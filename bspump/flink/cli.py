"""
CLI entry point for Flink job submission.

Compiles a BitSwan notebook and submits it as a Flink job.

Usage:
    BITSWAN_RUNTIME=flink bitswan-flink examples/Kafka2Kafka/main.ipynb

Or with environment variables:
    BITSWAN_RUNTIME=flink \\
    FLINK_JOBMANAGER=jobmanager:8081 \\
    bitswan-flink examples/Kafka2Kafka/main.ipynb
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


def setup_flink_environment() -> None:
    """Set up the Flink runtime environment."""
    # Ensure BITSWAN_RUNTIME is set
    os.environ.setdefault("BITSWAN_RUNTIME", "flink")

    # Set default Flink configuration
    if "FLINK_HOME" not in os.environ:
        L.warning("FLINK_HOME not set, using system PyFlink")


def run_flink_job(notebook_path: str, config_path: str = None) -> None:
    """Compile and run a notebook as a Flink job.

    Args:
        notebook_path: Path to the .ipynb file
        config_path: Optional path to pipelines.conf (defaults to same dir as notebook)
    """
    setup_flink_environment()

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
            compiled_path = os.path.join(tmpdir, "flink_pipeline.py")
            compile_notebook(notebook_path, compiled_path)

            # Add temp dir to path so we can import the module
            sys.path.insert(0, tmpdir)

            # Import the Flink runtime and set up config path
            from bspump.flink.runtime import get_flink_runtime

            runtime = get_flink_runtime(config_path)

            # Import the compiled module (this registers steps)
            L.info("Loading compiled pipeline...")
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "flink_pipeline", compiled_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Execute the Flink job
            L.info("Submitting Flink job...")
            runtime.execute()

    finally:
        os.chdir(original_dir)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run a BitSwan notebook as a Flink job",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with Flink runtime
  BITSWAN_RUNTIME=flink bitswan-flink examples/Kafka2Kafka/main.ipynb

  # With explicit config file
  bitswan-flink examples/Kafka2Kafka/main.ipynb -c /path/to/pipelines.conf

  # With Flink cluster
  FLINK_JOBMANAGER=jobmanager:8081 bitswan-flink notebook.ipynb

Environment Variables:
  BITSWAN_RUNTIME   Runtime to use (flink, bspump, jupyter)
  FLINK_HOME        Path to Flink installation
  FLINK_JOBMANAGER  Flink JobManager address (host:port)
  FLINK_PARALLELISM Flink job parallelism (default: 1)
        """,
    )

    parser.add_argument(
        "notebook",
        help="Path to the Jupyter notebook (.ipynb) to run",
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

    try:
        run_flink_job(args.notebook, args.config)
    except ImportError as e:
        if "pyflink" in str(e).lower():
            L.error(
                "PyFlink not installed. Install with: pip install apache-flink"
            )
            sys.exit(1)
        raise
    except Exception as e:
        L.exception(f"Error running Flink job: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
