"""
BitSwan Spark Runtime Adapter.

Run existing BitSwan stream pipelines on Apache Spark Structured Streaming
without modifying pipeline code. The same @step, @async_step, and
auto_pipeline() decorators work unchanged.

Runtime Selection:
    Set BITSWAN_RUNTIME=spark environment variable to use Spark backend.

Example:
    BITSWAN_RUNTIME=spark bitswan-spark examples/Kafka2Kafka/main.ipynb

Architecture:
    - SparkRuntime: Collects registered steps and builds Spark jobs
    - Adapters: Pluggable source/sink system (Kafka built-in)
    - Operators: Map @step to UDF, @async_step to UDF with explode()
"""

from .runtime import (
    SparkRuntime,
    get_spark_runtime,
    detect_runtime,
    _spark_runtime,
)
from .adapters import (
    SparkSourceAdapter,
    SparkSinkAdapter,
    register_source_adapter,
    register_sink_adapter,
    get_source_adapter,
    get_sink_adapter,
    SPARK_SOURCE_ADAPTERS,
    SPARK_SINK_ADAPTERS,
)
from .config import SparkConfig
from .operators import (
    create_map_udf,
    create_flatmap_udf,
)

# Import Kafka adapters to register them
from . import kafka  # noqa: F401

__all__ = [
    # Runtime
    "SparkRuntime",
    "get_spark_runtime",
    "detect_runtime",
    "_spark_runtime",
    # Adapters
    "SparkSourceAdapter",
    "SparkSinkAdapter",
    "register_source_adapter",
    "register_sink_adapter",
    "get_source_adapter",
    "get_sink_adapter",
    "SPARK_SOURCE_ADAPTERS",
    "SPARK_SINK_ADAPTERS",
    # Config
    "SparkConfig",
    # Operators
    "create_map_udf",
    "create_flatmap_udf",
]
