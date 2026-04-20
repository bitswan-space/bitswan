"""
CLI entry point for Spark job submission.

Compiles a BitSwan notebook and submits it as a Spark Structured Streaming job.

Usage:
    bitswan-spark examples/Kafka2Kafka/main.ipynb

    # With specific trigger mode
    bitswan-spark --trigger once examples/SqlToKafka/main.ipynb
    bitswan-spark --trigger "5 seconds" examples/Kafka2Kafka/main.ipynb

    # Submit to Spark cluster
    bitswan-spark --master spark://master:7077 examples/Kafka2Kafka/main.ipynb
"""

import argparse
import json
import logging
import os
import sys
import tempfile

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
L = logging.getLogger(__name__)


def compile_notebook(notebook_path: str, output_path: str) -> None:
    """Compile a Jupyter notebook to a Python module.

    Uses the same compilation logic as bspump.main but without running.

    Args:
        notebook_path: Path to the .ipynb file
        output_path: Path to write the compiled .py file
    """
    from bspump.main import NotebookCompiler

    with open(notebook_path) as f:
        notebook = json.load(f)

    compiler = NotebookCompiler()
    compiler.compile_notebook(notebook, out_path=output_path)
    L.info(f"Compiled notebook to {output_path}")


def setup_spark_environment(
    master: str = None,
    trigger: str = None,
    checkpoint_dir: str = None,
) -> None:
    """Set up the Spark runtime environment.

    Args:
        master: Spark master URL (e.g., spark://master:7077)
        trigger: Trigger mode (once, available_now, or processing time)
        checkpoint_dir: Directory for checkpoint data
    """
    # Always use spark runtime when running bitswan-spark
    os.environ["BITSWAN_RUNTIME"] = "spark"

    # Set Spark master if specified
    if master:
        os.environ["SPARK_MASTER"] = master
        L.info(f"Using Spark master at {master}")


def run_spark_job(
    notebook_path: str,
    config_path: str = None,
    master: str = None,
    trigger: str = None,
    checkpoint_dir: str = None,
) -> None:
    """Compile and run a notebook as a Spark Structured Streaming job.

    Args:
        notebook_path: Path to the .ipynb file
        config_path: Optional path to pipelines.conf (defaults to same dir as notebook)
        master: Spark master URL
        trigger: Trigger mode (once, available_now, or processing time)
        checkpoint_dir: Directory for checkpoint data
    """
    setup_spark_environment(master, trigger, checkpoint_dir)

    # Determine config path
    if config_path is None:
        notebook_dir = os.path.dirname(os.path.abspath(notebook_path))
        config_path = os.path.join(notebook_dir, "pipelines.conf")

    # Change to notebook directory so relative imports work
    notebook_dir = os.path.dirname(os.path.abspath(notebook_path))
    original_dir = os.getcwd()
    os.chdir(notebook_dir)

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            compiled_path = os.path.join(tmpdir, "spark_pipeline.py")
            compile_notebook(notebook_path, compiled_path)

            # Add temp dir to path so we can import the module
            sys.path.insert(0, tmpdir)

            # Import the Spark runtime and set up config path
            from bspump.spark.runtime import get_spark_runtime

            runtime = get_spark_runtime(config_path)

            # Configure trigger if specified
            if trigger or checkpoint_dir:
                runtime.set_trigger(
                    trigger=trigger or "1 second",
                    checkpoint_dir=checkpoint_dir or "/tmp/spark-checkpoint",
                )

            # Import the compiled module (this registers steps)
            L.info("Loading compiled pipeline...")
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "spark_pipeline", compiled_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Execute the Spark job
            L.info("Starting Spark streaming job...")
            query = runtime.execute()

            # Wait for termination (or process all available data if trigger=once)
            L.info("Awaiting termination...")
            runtime.await_termination(query)

    finally:
        os.chdir(original_dir)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run a BitSwan notebook as a Spark Structured Streaming job",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run locally with default trigger (continuous micro-batch)
  bitswan-spark examples/Kafka2Kafka/main.ipynb

  # Run with specific trigger mode
  bitswan-spark --trigger once examples/SqlToKafka/main.ipynb
  bitswan-spark --trigger "5 seconds" examples/Kafka2Kafka/main.ipynb
  bitswan-spark --trigger available_now examples/Batch/main.ipynb

  # Submit to Spark cluster
  bitswan-spark --master spark://master:7077 examples/Kafka2Kafka/main.ipynb

  # With explicit config file
  bitswan-spark -c /path/to/pipelines.conf notebook.ipynb

Environment Variables:
  SPARK_MASTER       Spark master URL - same as --master
  SPARK_LOG_LEVEL    Spark log level (default: WARN)
  SPARK_KAFKA_PACKAGES  Override Kafka package coordinates
        """,
    )

    parser.add_argument(
        "notebook",
        help="Path to the Jupyter notebook (.ipynb) to run",
    )
    parser.add_argument(
        "-m",
        "--master",
        metavar="URL",
        help="Spark master URL (e.g., spark://master:7077, local[*])",
    )
    parser.add_argument(
        "-t",
        "--trigger",
        metavar="MODE",
        help=(
            "Trigger mode: 'once' (process all available), "
            "'available_now' (process available then stop), "
            "or processing time like '1 second', '5 seconds'"
        ),
    )
    parser.add_argument(
        "--checkpoint-dir",
        metavar="PATH",
        help="Directory for checkpoint data (default: /tmp/spark-checkpoint)",
    )
    parser.add_argument(
        "-c",
        "--config",
        help="Path to pipelines.conf (default: same directory as notebook)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not os.path.exists(args.notebook):
        L.error(f"Notebook not found: {args.notebook}")
        sys.exit(1)

    # Use CLI arg or fall back to env var
    master = args.master or os.environ.get("SPARK_MASTER")

    try:
        run_spark_job(
            args.notebook,
            args.config,
            master,
            args.trigger,
            args.checkpoint_dir,
        )
    except ImportError as e:
        if "pyspark" in str(e).lower():
            L.error(
                "PySpark not installed. Install with: pip install pyspark"
            )
            sys.exit(1)
        raise
    except Exception as e:
        L.exception(f"Error running Spark job: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
