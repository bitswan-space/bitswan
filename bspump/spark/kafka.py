"""
Built-in Kafka adapters for Spark runtime.

Provides KafkaSourceAdapter and KafkaSinkAdapter that integrate
with Spark Structured Streaming's Kafka connector.
"""

import logging
from typing import Any, Dict, TYPE_CHECKING

from .adapters import (
    SparkSourceAdapter,
    SparkSinkAdapter,
    register_source_adapter,
    register_sink_adapter,
)

if TYPE_CHECKING:
    from pyspark.sql import SparkSession, DataFrame
    from pyspark.sql.streaming import StreamingQuery

L = logging.getLogger(__name__)


class KafkaSourceAdapter(SparkSourceAdapter):
    """Spark Structured Streaming Kafka source adapter.

    Creates a streaming DataFrame from a Kafka topic with a 'value' column
    containing event strings.

    Configuration from pipelines.conf:
        [connection:KafkaConnection]
        bootstrap_servers = kafka:9092

        [pipeline:MyPipeline:KafkaSource]
        topic = source-topic
        group_id = my-consumer-group
    """

    def create_source(
        self,
        spark: "SparkSession",
        connection_config: Dict[str, Any],
        component_config: Dict[str, Any],
    ) -> "DataFrame":
        """Create a Kafka source streaming DataFrame.

        Args:
            spark: SparkSession instance
            connection_config: Connection settings (bootstrap_servers, etc.)
            component_config: Source config (topic, group_id, etc.)

        Returns:
            Streaming DataFrame with 'value' column containing event strings
        """
        bootstrap_servers = connection_config.get(
            "bootstrap_servers", "localhost:9092"
        )
        topic = component_config.get("topic", "unconfigured")
        group_id = component_config.get("group_id", "bspump-spark")
        starting_offsets = component_config.get("starting_offsets", "earliest")

        L.info(f"Creating Kafka source: {topic} from {bootstrap_servers}")

        # Build Kafka source
        reader = (
            spark.readStream
            .format("kafka")
            .option("kafka.bootstrap.servers", bootstrap_servers)
            .option("subscribe", topic)
            .option("startingOffsets", starting_offsets)
            .option("kafka.group.id", group_id)
        )

        # Add optional security settings
        if "security_protocol" in connection_config:
            reader = reader.option(
                "kafka.security.protocol",
                connection_config["security_protocol"]
            )
        if "sasl_mechanism" in connection_config:
            reader = reader.option(
                "kafka.sasl.mechanism",
                connection_config["sasl_mechanism"]
            )
        if "sasl_username" in connection_config:
            jaas_config = (
                "org.apache.kafka.common.security.plain.PlainLoginModule required "
                f"username=\"{connection_config['sasl_username']}\" "
                f"password=\"{connection_config.get('sasl_password', '')}\";"
            )
            reader = reader.option("kafka.sasl.jaas.config", jaas_config)

        # Load and extract value as string
        df = reader.load().selectExpr("CAST(value AS STRING) as value")

        return df


class KafkaSinkAdapter(SparkSinkAdapter):
    """Spark Structured Streaming Kafka sink adapter.

    Writes a streaming DataFrame with 'value' column to a Kafka topic.

    Configuration from pipelines.conf:
        [connection:KafkaConnection]
        bootstrap_servers = kafka:9092

        [pipeline:MyPipeline:KafkaSink]
        topic = sink-topic
    """

    def add_sink(
        self,
        df: "DataFrame",
        connection_config: Dict[str, Any],
        component_config: Dict[str, Any],
        trigger_config: Dict[str, Any],
    ) -> "StreamingQuery":
        """Add Kafka sink to the streaming DataFrame.

        Args:
            df: Streaming DataFrame with 'value' column
            connection_config: Connection settings (bootstrap_servers, etc.)
            component_config: Sink config (topic, etc.)
            trigger_config: Trigger configuration (trigger mode, checkpoint dir)

        Returns:
            StreamingQuery handle for the running query
        """
        bootstrap_servers = connection_config.get(
            "bootstrap_servers", "localhost:9092"
        )
        topic = component_config.get("topic", "unconfigured")
        checkpoint_dir = trigger_config.get(
            "checkpoint_dir", "/tmp/spark-checkpoint"
        )

        L.info(f"Creating Kafka sink: {topic} to {bootstrap_servers}")

        # Get trigger settings
        trigger = self._get_trigger(trigger_config)

        # Build write stream
        writer = (
            df.selectExpr("CAST(value AS STRING) as value")
            .writeStream
            .format("kafka")
            .option("kafka.bootstrap.servers", bootstrap_servers)
            .option("topic", topic)
            .option("checkpointLocation", checkpoint_dir)
        )

        # Add optional security settings
        if "security_protocol" in connection_config:
            writer = writer.option(
                "kafka.security.protocol",
                connection_config["security_protocol"]
            )
        if "sasl_mechanism" in connection_config:
            writer = writer.option(
                "kafka.sasl.mechanism",
                connection_config["sasl_mechanism"]
            )
        if "sasl_username" in connection_config:
            jaas_config = (
                "org.apache.kafka.common.security.plain.PlainLoginModule required "
                f"username=\"{connection_config['sasl_username']}\" "
                f"password=\"{connection_config.get('sasl_password', '')}\";"
            )
            writer = writer.option("kafka.sasl.jaas.config", jaas_config)

        # Apply trigger and start
        return writer.trigger(**trigger).start()

    def _get_trigger(self, trigger_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert trigger configuration to Spark trigger kwargs.

        Args:
            trigger_config: Trigger configuration dict

        Returns:
            Dict suitable for .trigger(**kwargs)
        """
        trigger = trigger_config.get("trigger", "1 second")

        if trigger == "once":
            return {"once": True}
        elif trigger == "available_now":
            return {"availableNow": True}
        elif trigger == "continuous":
            # Continuous processing mode (experimental in Spark)
            interval = trigger_config.get("interval", "1 second")
            return {"continuous": interval}
        else:
            # Default: processingTime trigger
            return {"processingTime": trigger}


# Register adapters on module import
register_source_adapter("KafkaSource", KafkaSourceAdapter)
register_sink_adapter("KafkaSink", KafkaSinkAdapter)
