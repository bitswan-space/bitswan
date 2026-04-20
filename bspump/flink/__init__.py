"""
BitSwan Flink Runtime Adapter.

Run existing BitSwan stream pipelines on Apache Flink without modifying
pipeline code. The same @step, @async_step, and auto_pipeline() decorators
work unchanged.

Runtime Selection:
    Set BITSWAN_RUNTIME=flink environment variable to use Flink backend.

Example:
    BITSWAN_RUNTIME=flink bitswan-flink examples/Kafka2Kafka/main.ipynb

Architecture:
    - FlinkRuntime: Collects registered steps and builds Flink jobs
    - Adapters: Pluggable source/sink system (Kafka built-in)
    - Operators: Map @step to MapFunction, @async_step to FlatMapFunction
"""

from .runtime import (
    FlinkRuntime,
    get_flink_runtime,
    detect_runtime,
    _flink_runtime,
)
from .adapters import (
    FlinkSourceAdapter,
    FlinkSinkAdapter,
    register_source_adapter,
    register_sink_adapter,
    get_source_adapter,
    get_sink_adapter,
    FLINK_SOURCE_ADAPTERS,
    FLINK_SINK_ADAPTERS,
)
from .config import FlinkConfig
from .operators import (
    BitSwanMapFunction,
    BitSwanFlatMapFunction,
    create_map_function,
    create_flat_map_function,
)

# Import Kafka adapters to register them
from . import kafka  # noqa: F401

__all__ = [
    # Runtime
    "FlinkRuntime",
    "get_flink_runtime",
    "detect_runtime",
    "_flink_runtime",
    # Adapters
    "FlinkSourceAdapter",
    "FlinkSinkAdapter",
    "register_source_adapter",
    "register_sink_adapter",
    "get_source_adapter",
    "get_sink_adapter",
    "FLINK_SOURCE_ADAPTERS",
    "FLINK_SINK_ADAPTERS",
    # Config
    "FlinkConfig",
    # Operators
    "BitSwanMapFunction",
    "BitSwanFlatMapFunction",
    "create_map_function",
    "create_flat_map_function",
]
