"""
Pluggable source/sink adapter system for Spark runtime.

Provides base classes and registry for custom source/sink adapters.
Users can add their own adapters by subclassing SparkSourceAdapter
or SparkSinkAdapter and registering them.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import SparkSession, DataFrame
    from pyspark.sql.streaming import StreamingQuery


class SparkSourceAdapter(ABC):
    """Base class for Spark source adapters.

    Implement this class to create custom source adapters for different
    data sources (files, HTTP, databases, etc.).

    Example:
        class FileSourceAdapter(SparkSourceAdapter):
            def create_source(self, spark, conn_config, comp_config):
                return (spark.readStream
                    .format("text")
                    .load(comp_config["path"])
                    .selectExpr("CAST(value AS STRING) as value"))

        register_source_adapter("FileSource", FileSourceAdapter)
    """

    @abstractmethod
    def create_source(
        self,
        spark: "SparkSession",
        connection_config: Dict[str, Any],
        component_config: Dict[str, Any],
    ) -> "DataFrame":
        """Create a streaming DataFrame from the source.

        Args:
            spark: SparkSession instance
            connection_config: Connection settings from [connection:Name] section
            component_config: Component config from [pipeline:Name:Source] section

        Returns:
            Streaming DataFrame with a 'value' column containing event strings
        """
        pass


class SparkSinkAdapter(ABC):
    """Base class for Spark sink adapters.

    Implement this class to create custom sink adapters for different
    data destinations (files, HTTP, databases, etc.).

    Example:
        class FileSinkAdapter(SparkSinkAdapter):
            def add_sink(self, df, conn_config, comp_config, trigger_config):
                return (df.writeStream
                    .format("text")
                    .option("path", comp_config["path"])
                    .option("checkpointLocation", "/tmp/checkpoint")
                    .start())

        register_sink_adapter("FileSink", FileSinkAdapter)
    """

    @abstractmethod
    def add_sink(
        self,
        df: "DataFrame",
        connection_config: Dict[str, Any],
        component_config: Dict[str, Any],
        trigger_config: Dict[str, Any],
    ) -> "StreamingQuery":
        """Add a streaming sink to the DataFrame.

        Args:
            df: Streaming DataFrame with a 'value' column
            connection_config: Connection settings from [connection:Name] section
            component_config: Component config from [pipeline:Name:Sink] section
            trigger_config: Trigger configuration (trigger mode, checkpoint dir)

        Returns:
            StreamingQuery handle for the running query
        """
        pass


# Registry for source adapters
# Maps adapter name (e.g., "KafkaSource") to adapter class
SPARK_SOURCE_ADAPTERS: Dict[str, Type[SparkSourceAdapter]] = {}

# Registry for sink adapters
# Maps adapter name (e.g., "KafkaSink") to adapter class
SPARK_SINK_ADAPTERS: Dict[str, Type[SparkSinkAdapter]] = {}


def register_source_adapter(
    name: str, adapter_class: Type[SparkSourceAdapter]
) -> None:
    """Register a source adapter.

    Args:
        name: Adapter name (e.g., "FileSource", "HttpSource")
        adapter_class: Class implementing SparkSourceAdapter
    """
    SPARK_SOURCE_ADAPTERS[name] = adapter_class


def register_sink_adapter(
    name: str, adapter_class: Type[SparkSinkAdapter]
) -> None:
    """Register a sink adapter.

    Args:
        name: Adapter name (e.g., "FileSink", "DatabaseSink")
        adapter_class: Class implementing SparkSinkAdapter
    """
    SPARK_SINK_ADAPTERS[name] = adapter_class


def get_source_adapter(name: str) -> Type[SparkSourceAdapter]:
    """Get a registered source adapter by name.

    Args:
        name: Adapter name

    Returns:
        The adapter class

    Raises:
        KeyError: If adapter not found
    """
    if name not in SPARK_SOURCE_ADAPTERS:
        raise KeyError(
            f"Source adapter '{name}' not found. "
            f"Available: {list(SPARK_SOURCE_ADAPTERS.keys())}"
        )
    return SPARK_SOURCE_ADAPTERS[name]


def get_sink_adapter(name: str) -> Type[SparkSinkAdapter]:
    """Get a registered sink adapter by name.

    Args:
        name: Adapter name

    Returns:
        The adapter class

    Raises:
        KeyError: If adapter not found
    """
    if name not in SPARK_SINK_ADAPTERS:
        raise KeyError(
            f"Sink adapter '{name}' not found. "
            f"Available: {list(SPARK_SINK_ADAPTERS.keys())}"
        )
    return SPARK_SINK_ADAPTERS[name]
