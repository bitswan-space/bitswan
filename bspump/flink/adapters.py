"""
Pluggable source/sink adapter system for Flink runtime.

Provides base classes and registry for custom source/sink adapters.
Users can add their own adapters by subclassing FlinkSourceAdapter
or FlinkSinkAdapter and registering them.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from pyflink.datastream import StreamExecutionEnvironment, DataStream


class FlinkSourceAdapter(ABC):
    """Base class for Flink source adapters.

    Implement this class to create custom source adapters for different
    data sources (files, HTTP, databases, etc.).

    Example:
        class FileSourceAdapter(FlinkSourceAdapter):
            def create_source(self, env, config):
                return env.read_text_file(config["path"]) \\
                          .map(lambda line: (line.encode(), {}))

        register_source_adapter("FileSource", FileSourceAdapter)
    """

    @abstractmethod
    def create_source(
        self,
        env: "StreamExecutionEnvironment",
        connection_config: Dict[str, Any],
        component_config: Dict[str, Any],
    ) -> "DataStream":
        """Create a DataStream from the source.

        Args:
            env: Flink StreamExecutionEnvironment
            connection_config: Connection settings from [connection:Name] section
            component_config: Component config from [pipeline:Name:Source] section

        Returns:
            DataStream of (event, context) tuples where:
            - event: bytes - the event data
            - context: dict - metadata (kafka_key, kafka_headers, etc.)
        """
        pass


class FlinkSinkAdapter(ABC):
    """Base class for Flink sink adapters.

    Implement this class to create custom sink adapters for different
    data destinations (files, HTTP, databases, etc.).

    Example:
        class FileSinkAdapter(FlinkSinkAdapter):
            def add_sink(self, stream, config):
                stream.map(lambda x: x[0].decode()) \\
                      .write_as_text(config["path"])

        register_sink_adapter("FileSink", FileSinkAdapter)
    """

    @abstractmethod
    def add_sink(
        self,
        stream: "DataStream",
        connection_config: Dict[str, Any],
        component_config: Dict[str, Any],
    ) -> None:
        """Add a sink to the DataStream.

        Args:
            stream: DataStream of (event, context) tuples where:
                   - event: bytes - the processed event data
                   - context: dict - metadata to preserve
            connection_config: Connection settings from [connection:Name] section
            component_config: Component config from [pipeline:Name:Sink] section
        """
        pass


# Registry for source adapters
# Maps adapter name (e.g., "KafkaSource") to adapter class
FLINK_SOURCE_ADAPTERS: Dict[str, Type[FlinkSourceAdapter]] = {}

# Registry for sink adapters
# Maps adapter name (e.g., "KafkaSink") to adapter class
FLINK_SINK_ADAPTERS: Dict[str, Type[FlinkSinkAdapter]] = {}


def register_source_adapter(
    name: str, adapter_class: Type[FlinkSourceAdapter]
) -> None:
    """Register a source adapter.

    Args:
        name: Adapter name (e.g., "FileSource", "HttpSource")
        adapter_class: Class implementing FlinkSourceAdapter
    """
    FLINK_SOURCE_ADAPTERS[name] = adapter_class


def register_sink_adapter(
    name: str, adapter_class: Type[FlinkSinkAdapter]
) -> None:
    """Register a sink adapter.

    Args:
        name: Adapter name (e.g., "FileSink", "DatabaseSink")
        adapter_class: Class implementing FlinkSinkAdapter
    """
    FLINK_SINK_ADAPTERS[name] = adapter_class


def get_source_adapter(name: str) -> Type[FlinkSourceAdapter]:
    """Get a registered source adapter by name.

    Args:
        name: Adapter name

    Returns:
        The adapter class

    Raises:
        KeyError: If adapter not found
    """
    if name not in FLINK_SOURCE_ADAPTERS:
        raise KeyError(
            f"Source adapter '{name}' not found. "
            f"Available: {list(FLINK_SOURCE_ADAPTERS.keys())}"
        )
    return FLINK_SOURCE_ADAPTERS[name]


def get_sink_adapter(name: str) -> Type[FlinkSinkAdapter]:
    """Get a registered sink adapter by name.

    Args:
        name: Adapter name

    Returns:
        The adapter class

    Raises:
        KeyError: If adapter not found
    """
    if name not in FLINK_SINK_ADAPTERS:
        raise KeyError(
            f"Sink adapter '{name}' not found. "
            f"Available: {list(FLINK_SINK_ADAPTERS.keys())}"
        )
    return FLINK_SINK_ADAPTERS[name]
