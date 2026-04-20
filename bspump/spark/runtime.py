"""
Spark runtime for BitSwan pipelines.

SparkRuntime tracks registered steps and builds Spark Structured Streaming
jobs from BitSwan pipeline definitions.
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Dict, TYPE_CHECKING

from .config import SparkConfig
from .adapters import get_source_adapter, get_sink_adapter

if TYPE_CHECKING:
    from pyspark.sql import SparkSession, DataFrame
    from pyspark.sql.streaming import StreamingQuery

L = logging.getLogger(__name__)


@dataclass
class RegisteredStep:
    """A registered processor step."""

    name: str
    func: Callable
    is_generator: bool = False  # True for @async_step (one-to-many)


@dataclass
class SparkPipeline:
    """A pipeline definition with source, processors, and sink."""

    name: str
    source_adapter: str = "KafkaSource"
    sink_adapter: str = "KafkaSink"
    steps: List[RegisteredStep] = field(default_factory=list)


class SparkRuntime:
    """Runtime that builds and executes Spark Structured Streaming jobs.

    This runtime collects registered @step and @async_step functions,
    then builds a Spark job that processes data through them.
    """

    def __init__(self, config_path: str = "pipelines.conf"):
        """Initialize the Spark runtime.

        Args:
            config_path: Path to pipelines.conf file
        """
        self.config = SparkConfig(config_path)
        self.pipelines: Dict[str, SparkPipeline] = {}
        self.current_pipeline: Optional[str] = None
        self._steps: List[RegisteredStep] = []
        self._spark: Optional["SparkSession"] = None
        self._trigger_config: Dict[str, Any] = {
            "trigger": "1 second",
            "checkpoint_dir": "/tmp/spark-checkpoint",
        }

    def set_trigger(
        self,
        trigger: str = "1 second",
        checkpoint_dir: str = "/tmp/spark-checkpoint",
    ) -> None:
        """Configure trigger settings for streaming queries.

        Args:
            trigger: Trigger mode - "once", "available_now", or processing time
                     like "1 second", "5 seconds", "1 minute"
            checkpoint_dir: Directory for checkpoint data
        """
        self._trigger_config = {
            "trigger": trigger,
            "checkpoint_dir": checkpoint_dir,
        }

    def new_pipeline(
        self,
        name: str,
        source_adapter: str = "KafkaSource",
        sink_adapter: str = "KafkaSink",
    ) -> None:
        """Create a new pipeline.

        Args:
            name: Pipeline name
            source_adapter: Name of the source adapter to use
            sink_adapter: Name of the sink adapter to use
        """
        self.current_pipeline = name
        self.pipelines[name] = SparkPipeline(
            name=name,
            source_adapter=source_adapter,
            sink_adapter=sink_adapter,
        )
        self._steps = []

    def register_step(self, func: Callable[[Any], Any]) -> Callable:
        """Register a synchronous processor function.

        This is called by the @step decorator when BITSWAN_RUNTIME=spark.

        Args:
            func: The decorated function

        Returns:
            The original function (unchanged)
        """
        step = RegisteredStep(
            name=func.__name__,
            func=func,
            is_generator=False,
        )
        self._steps.append(step)

        if self.current_pipeline and self.current_pipeline in self.pipelines:
            self.pipelines[self.current_pipeline].steps.append(step)

        L.debug(f"Registered step: {func.__name__}")
        return func

    def register_async_step(
        self, func: Callable[[Callable, Any], None]
    ) -> Callable:
        """Register an async generator function.

        This is called by the @async_step decorator when BITSWAN_RUNTIME=spark.

        Args:
            func: The decorated async function with signature (inject, event) -> None

        Returns:
            The original function (unchanged)
        """
        step = RegisteredStep(
            name=func.__name__,
            func=func,
            is_generator=True,
        )
        self._steps.append(step)

        if self.current_pipeline and self.current_pipeline in self.pipelines:
            self.pipelines[self.current_pipeline].steps.append(step)

        L.debug(f"Registered async_step: {func.__name__}")
        return func

    def end_pipeline(self) -> None:
        """Finalize the current pipeline definition."""
        if self.current_pipeline:
            pipeline = self.pipelines.get(self.current_pipeline)
            if pipeline:
                pipeline.steps = list(self._steps)
            L.debug(
                f"Finalized pipeline {self.current_pipeline} "
                f"with {len(self._steps)} steps"
            )
        self._steps = []

    def _get_spark_session(self) -> "SparkSession":
        """Get or create the SparkSession."""
        if self._spark is None:
            from pyspark.sql import SparkSession

            # Check for remote cluster configuration
            master = os.environ.get("SPARK_MASTER")

            builder = SparkSession.builder.appName("BitSwan")

            if master:
                L.info(f"Connecting to Spark cluster at {master}")
                builder = builder.master(master)
            else:
                # Local execution
                builder = builder.master("local[*]")

            # Add Kafka package if needed
            kafka_packages = os.environ.get("SPARK_KAFKA_PACKAGES")
            if kafka_packages:
                builder = builder.config(
                    "spark.jars.packages", kafka_packages
                )
            else:
                # Default Kafka package for Spark 3.5
                builder = builder.config(
                    "spark.jars.packages",
                    "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0"
                )

            self._spark = builder.getOrCreate()

            # Set log level
            self._spark.sparkContext.setLogLevel(
                os.environ.get("SPARK_LOG_LEVEL", "WARN")
            )

        return self._spark

    def build_spark_job(
        self, pipeline_name: Optional[str] = None
    ) -> "DataFrame":
        """Build a Spark streaming DataFrame job from registered steps.

        Args:
            pipeline_name: Name of pipeline to build (uses first if not specified)

        Returns:
            The final streaming DataFrame (before sink is added)
        """
        from pyspark.sql.functions import col, explode

        from .operators import create_map_udf, create_flatmap_udf

        spark = self._get_spark_session()

        # Get pipeline
        if pipeline_name is None:
            if not self.pipelines:
                raise RuntimeError("No pipelines registered")
            pipeline_name = list(self.pipelines.keys())[0]

        pipeline = self.pipelines.get(pipeline_name)
        if pipeline is None:
            raise RuntimeError(f"Pipeline '{pipeline_name}' not found")

        # Get source adapter and config
        source_adapter_cls = get_source_adapter(pipeline.source_adapter)
        source_adapter = source_adapter_cls()

        source_connection_name = self.config.get_source_connection_name(
            pipeline_name
        )
        connection_config = {}
        if source_connection_name:
            connection_config = self.config.get_connection(source_connection_name)

        source_config = self.config.get_source_config(pipeline_name) or {}

        # Create source stream
        df = source_adapter.create_source(spark, connection_config, source_config)

        # Apply each step
        for step in pipeline.steps:
            if step.is_generator:
                # @async_step -> UDF with explode
                flatmap_udf = create_flatmap_udf(step.func)
                df = df.withColumn("value", explode(flatmap_udf(col("value"))))
            else:
                # @step -> UDF
                map_udf = create_map_udf(step.func)
                df = df.withColumn("value", map_udf(col("value")))
                # Filter out nulls (filtered events)
                df = df.filter(col("value").isNotNull())

        return df

    def execute(self, pipeline_name: Optional[str] = None) -> "StreamingQuery":
        """Build and execute the Spark streaming job.

        Args:
            pipeline_name: Name of pipeline to execute (uses first if not specified)

        Returns:
            StreamingQuery handle for the running query
        """
        # Get pipeline
        if pipeline_name is None:
            if not self.pipelines:
                raise RuntimeError("No pipelines registered")
            pipeline_name = list(self.pipelines.keys())[0]

        pipeline = self.pipelines.get(pipeline_name)
        if pipeline is None:
            raise RuntimeError(f"Pipeline '{pipeline_name}' not found")

        # Build the job
        df = self.build_spark_job(pipeline_name)

        # Get sink adapter and config
        sink_adapter_cls = get_sink_adapter(pipeline.sink_adapter)
        sink_adapter = sink_adapter_cls()

        sink_connection_name = self.config.get_sink_connection_name(pipeline_name)
        connection_config = {}
        if sink_connection_name:
            connection_config = self.config.get_connection(sink_connection_name)

        sink_config = self.config.get_sink_config(pipeline_name) or {}

        # Add sink and start
        job_name = f"BitSwan-{pipeline_name}"
        L.info(f"Starting Spark streaming job: {job_name}")

        query = sink_adapter.add_sink(
            df, connection_config, sink_config, self._trigger_config
        )

        return query

    def await_termination(self, query: "StreamingQuery" = None) -> None:
        """Wait for streaming query to terminate.

        Args:
            query: StreamingQuery to wait for. If None, waits for all queries.
        """
        spark = self._get_spark_session()

        if query:
            query.awaitTermination()
        else:
            spark.streams.awaitAnyTermination()


# Global runtime instance (created when BITSWAN_RUNTIME=spark)
_spark_runtime: Optional[SparkRuntime] = None


def get_spark_runtime(config_path: str = "pipelines.conf") -> SparkRuntime:
    """Get or create the global Spark runtime instance.

    Args:
        config_path: Path to pipelines.conf

    Returns:
        The SparkRuntime instance
    """
    global _spark_runtime
    if _spark_runtime is None:
        _spark_runtime = SparkRuntime(config_path)
    return _spark_runtime


def detect_runtime() -> str:
    """Detect which runtime to use.

    Checks BITSWAN_RUNTIME environment variable first,
    then falls back to auto-detection.

    Returns:
        "spark", "flink", "jupyter", or "bspump"
    """
    runtime = os.environ.get("BITSWAN_RUNTIME")
    if runtime:
        return runtime.lower()

    # Auto-detect Jupyter environment
    try:
        from IPython import get_ipython

        if "IPKernelApp" in get_ipython().config:
            return "jupyter"
        if "VSCODE_PID" in os.environ:
            return "jupyter"
    except Exception:
        pass

    return "bspump"
