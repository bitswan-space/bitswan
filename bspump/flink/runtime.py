"""
Flink runtime for BitSwan pipelines.

FlinkRuntime tracks registered steps and builds PyFlink DataStream jobs
from BitSwan pipeline definitions.
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Dict, TYPE_CHECKING

from .config import FlinkConfig
from .adapters import get_source_adapter, get_sink_adapter

if TYPE_CHECKING:
    from pyflink.datastream import StreamExecutionEnvironment, DataStream

L = logging.getLogger(__name__)


@dataclass
class RegisteredStep:
    """A registered processor step."""

    name: str
    func: Callable
    is_generator: bool = False  # True for @async_step (one-to-many)


@dataclass
class FlinkPipeline:
    """A pipeline definition with source, processors, and sink."""

    name: str
    source_adapter: str = "KafkaSource"
    sink_adapter: str = "KafkaSink"
    steps: List[RegisteredStep] = field(default_factory=list)


class FlinkRuntime:
    """Runtime that builds and executes PyFlink DataStream jobs.

    This runtime collects registered @step and @async_step functions,
    then builds a Flink job that processes data through them.
    """

    def __init__(self, config_path: str = "pipelines.conf"):
        """Initialize the Flink runtime.

        Args:
            config_path: Path to pipelines.conf file
        """
        self.config = FlinkConfig(config_path)
        self.pipelines: Dict[str, FlinkPipeline] = {}
        self.current_pipeline: Optional[str] = None
        self._steps: List[RegisteredStep] = []
        self._env: Optional["StreamExecutionEnvironment"] = None

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
        self.pipelines[name] = FlinkPipeline(
            name=name,
            source_adapter=source_adapter,
            sink_adapter=sink_adapter,
        )
        self._steps = []

    def register_step(self, func: Callable[[Any], Any]) -> Callable:
        """Register a synchronous processor function.

        This is called by the @step decorator when BITSWAN_RUNTIME=flink.

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

        This is called by the @async_step decorator when BITSWAN_RUNTIME=flink.

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

    def _get_flink_env(self) -> "StreamExecutionEnvironment":
        """Get or create the Flink execution environment."""
        if self._env is None:
            from pyflink.datastream import StreamExecutionEnvironment

            # Check for remote cluster configuration
            jobmanager = os.environ.get("FLINK_JOBMANAGER")
            if jobmanager:
                # Parse host:port
                if ":" in jobmanager:
                    host, port = jobmanager.rsplit(":", 1)
                    port = int(port)
                else:
                    host = jobmanager
                    port = 8081  # Default Flink REST port

                L.info(f"Connecting to Flink cluster at {host}:{port}")
                self._env = StreamExecutionEnvironment.get_execution_environment()
                # Note: PyFlink uses REST API for remote submission
                # The cluster connection is handled at job submission time
            else:
                # Local execution (mini-cluster)
                self._env = StreamExecutionEnvironment.get_execution_environment()

            # Configure parallelism
            parallelism = int(os.environ.get("FLINK_PARALLELISM", "1"))
            self._env.set_parallelism(parallelism)

            # Add Kafka connector JARs if specified
            kafka_jars = os.environ.get("FLINK_KAFKA_JARS")
            if kafka_jars:
                self._env.add_jars(*kafka_jars.split(";"))
                L.info("Added Kafka JARs to Flink environment")

        return self._env

    def build_flink_job(
        self, pipeline_name: Optional[str] = None
    ) -> "DataStream":
        """Build a Flink DataStream job from registered steps.

        Args:
            pipeline_name: Name of pipeline to build (uses first if not specified)

        Returns:
            The final DataStream (before sink is added)
        """
        from .operators import create_map_function, create_flat_map_function

        env = self._get_flink_env()

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
        stream = source_adapter.create_source(env, connection_config, source_config)

        # Apply each step
        for step in pipeline.steps:
            if step.is_generator:
                # @async_step -> FlatMapFunction
                flat_map_fn = create_flat_map_function(step.func)
                stream = stream.flat_map(
                    flat_map_fn.flat_map,
                    output_type=None,  # Let Flink infer
                )
            else:
                # @step -> MapFunction
                map_fn = create_map_function(step.func)
                stream = stream.map(
                    map_fn.map,
                    output_type=None,  # Let Flink infer
                ).filter(lambda x: x is not None)

        return stream

    def execute(self, pipeline_name: Optional[str] = None) -> None:
        """Build and execute the Flink job.

        Args:
            pipeline_name: Name of pipeline to execute (uses first if not specified)
        """
        env = self._get_flink_env()

        # Get pipeline
        if pipeline_name is None:
            if not self.pipelines:
                raise RuntimeError("No pipelines registered")
            pipeline_name = list(self.pipelines.keys())[0]

        pipeline = self.pipelines.get(pipeline_name)
        if pipeline is None:
            raise RuntimeError(f"Pipeline '{pipeline_name}' not found")

        # Build the job
        stream = self.build_flink_job(pipeline_name)

        # Get sink adapter and config
        sink_adapter_cls = get_sink_adapter(pipeline.sink_adapter)
        sink_adapter = sink_adapter_cls()

        sink_connection_name = self.config.get_sink_connection_name(pipeline_name)
        connection_config = {}
        if sink_connection_name:
            connection_config = self.config.get_connection(sink_connection_name)

        sink_config = self.config.get_sink_config(pipeline_name) or {}

        # Add sink
        sink_adapter.add_sink(stream, connection_config, sink_config)

        # Execute
        job_name = f"BitSwan-{pipeline_name}"
        L.info(f"Executing Flink job: {job_name}")
        env.execute(job_name)


# Global runtime instance (created when BITSWAN_RUNTIME=flink)
_flink_runtime: Optional[FlinkRuntime] = None


def get_flink_runtime(config_path: str = "pipelines.conf") -> FlinkRuntime:
    """Get or create the global Flink runtime instance.

    Args:
        config_path: Path to pipelines.conf

    Returns:
        The FlinkRuntime instance
    """
    global _flink_runtime
    if _flink_runtime is None:
        _flink_runtime = FlinkRuntime(config_path)
    return _flink_runtime


def detect_runtime() -> str:
    """Detect which runtime to use.

    Checks BITSWAN_RUNTIME environment variable first,
    then falls back to auto-detection.

    Returns:
        "flink", "jupyter", or "bspump"
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
