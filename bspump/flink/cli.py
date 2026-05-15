"""
CLI entry point for Flink job submission.

Compiles a BitSwan notebook and submits it as a Flink job.

Usage:
    bitswan-flink examples/Kafka2Kafka/main.ipynb

    # With explicit Flink cluster
    bitswan-flink --flink-cluster jobmanager:8081 notebook.ipynb
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


def setup_flink_environment(flink_cluster: str = None) -> None:
    """Set up the Flink runtime environment.

    Args:
        flink_cluster: Flink JobManager address (host:port)
    """
    # Always use flink runtime when running bitswan-flink
    os.environ["BITSWAN_RUNTIME"] = "flink"

    # Set Flink cluster if specified
    if flink_cluster:
        os.environ["FLINK_JOBMANAGER"] = flink_cluster
        L.info(f"Using Flink cluster at {flink_cluster}")


def run_flink_job(
    notebook_path: str,
    config_path: str = None,
    flink_cluster: str = None,
) -> None:
    """Compile and run a notebook as a Flink job.

    Args:
        notebook_path: Path to the .ipynb file
        config_path: Optional path to pipelines.conf (defaults to same dir as notebook)
        flink_cluster: Flink JobManager address (host:port)
    """
    setup_flink_environment(flink_cluster)

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
  # Run locally (PyFlink mini-cluster)
  bitswan-flink examples/Kafka2Kafka/main.ipynb

  # Submit to Flink cluster
  bitswan-flink --flink-cluster jobmanager:8081 notebook.ipynb

  # With explicit config file
  bitswan-flink -c /path/to/pipelines.conf notebook.ipynb

Environment Variables:
  FLINK_JOBMANAGER  Flink JobManager address (host:port) - same as --flink-cluster
  FLINK_PARALLELISM Flink job parallelism (default: 1)
        """,
    )

    parser.add_argument(
        "notebook",
        help="Path to the Jupyter notebook (.ipynb) to run",
    )
    parser.add_argument(
        "-f",
        "--flink-cluster",
        metavar="HOST:PORT",
        help="Flink JobManager address (e.g., jobmanager:8081)",
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
    flink_cluster = args.flink_cluster or os.environ.get("FLINK_JOBMANAGER")

    try:
        run_flink_job(args.notebook, args.config, flink_cluster)
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
