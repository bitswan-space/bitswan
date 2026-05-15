"""
Built-in Kafka adapters for Flink runtime.

Provides KafkaSourceAdapter and KafkaSinkAdapter that integrate
with PyFlink's Kafka connectors.
"""

import json
import logging
from typing import Any, Dict, TYPE_CHECKING

from .adapters import (
    FlinkSourceAdapter,
    FlinkSinkAdapter,
    register_source_adapter,
    register_sink_adapter,
)

if TYPE_CHECKING:
    from pyflink.datastream import StreamExecutionEnvironment, DataStream

L = logging.getLogger(__name__)


class KafkaSourceAdapter(FlinkSourceAdapter):
    """PyFlink Kafka source adapter.

    Creates a DataStream from a Kafka topic, producing (event, context) tuples
    where context preserves Kafka metadata.

    Configuration from pipelines.conf:
        [connection:KafkaConnection]
        bootstrap_servers = kafka:9092

        [pipeline:MyPipeline:KafkaSource]
        topic = source-topic
        group_id = my-consumer-group
    """

    def create_source(
        self,
        env: "StreamExecutionEnvironment",
        connection_config: Dict[str, Any],
        component_config: Dict[str, Any],
    ) -> "DataStream":
        """Create a Kafka source DataStream.

        Args:
            env: Flink StreamExecutionEnvironment
            connection_config: Connection settings (bootstrap_servers, etc.)
            component_config: Source config (topic, group_id, etc.)

        Returns:
            DataStream of (event_bytes, context_dict) tuples
        """
        from pyflink.datastream.connectors.kafka import (
            KafkaSource,
            KafkaOffsetsInitializer,
        )
        from pyflink.common.serialization import SimpleStringSchema
        from pyflink.common import WatermarkStrategy

        bootstrap_servers = connection_config.get(
            "bootstrap_servers", "localhost:9092"
        )
        topic = component_config.get("topic", "unconfigured")
        group_id = component_config.get("group_id", "bspump-flink")

        # Build Kafka source
        kafka_source_builder = (
            KafkaSource.builder()
            .set_bootstrap_servers(bootstrap_servers)
            .set_topics(topic)
            .set_group_id(group_id)
            .set_starting_offsets(KafkaOffsetsInitializer.earliest())
            .set_value_only_deserializer(SimpleStringSchema())
        )

        # Add optional security settings
        if "security_protocol" in connection_config:
            kafka_source_builder.set_property(
                "security.protocol", connection_config["security_protocol"]
            )
        if "sasl_mechanism" in connection_config:
            kafka_source_builder.set_property(
                "sasl.mechanism", connection_config["sasl_mechanism"]
            )
        if "sasl_username" in connection_config:
            kafka_source_builder.set_property(
                "sasl.jaas.config",
                f"org.apache.kafka.common.security.plain.PlainLoginModule required "
                f"username=\"{connection_config['sasl_username']}\" "
                f"password=\"{connection_config.get('sasl_password', '')}\";",
            )

        kafka_source = kafka_source_builder.build()

        # Create stream and transform to (event, context) tuples
        stream = env.from_source(
            kafka_source,
            WatermarkStrategy.no_watermarks(),
            f"KafkaSource-{topic}",
        )

        # Transform string messages to (bytes, context) tuples
        def to_event_context(value: str) -> tuple:
            return (
                value.encode("utf-8") if isinstance(value, str) else value,
                {
                    "_kafka_topic": topic,
                    "kafka_key": None,
                    "kafka_headers": None,
                },
            )

        return stream.map(to_event_context)


class KafkaSinkAdapter(FlinkSinkAdapter):
    """PyFlink Kafka sink adapter.

    Writes (event, context) tuples to a Kafka topic.

    Configuration from pipelines.conf:
        [connection:KafkaConnection]
        bootstrap_servers = kafka:9092

        [pipeline:MyPipeline:KafkaSink]
        topic = sink-topic
    """

    def add_sink(
        self,
        stream: "DataStream",
        connection_config: Dict[str, Any],
        component_config: Dict[str, Any],
    ) -> None:
        """Add Kafka sink to the DataStream.

        Args:
            stream: DataStream of (event_bytes, context_dict) tuples
            connection_config: Connection settings (bootstrap_servers, etc.)
            component_config: Sink config (topic, etc.)
        """
        from pyflink.datastream.connectors.kafka import (
            KafkaSink as PyFlinkKafkaSink,
            KafkaRecordSerializationSchema,
        )
        from pyflink.common.serialization import SimpleStringSchema

        bootstrap_servers = connection_config.get(
            "bootstrap_servers", "localhost:9092"
        )
        topic = component_config.get("topic", "unconfigured")

        # Build serialization schema
        serialization_schema = (
            KafkaRecordSerializationSchema.builder()
            .set_topic(topic)
            .set_value_serialization_schema(SimpleStringSchema())
            .build()
        )

        # Build Kafka sink
        kafka_sink_builder = (
            PyFlinkKafkaSink.builder()
            .set_bootstrap_servers(bootstrap_servers)
            .set_record_serializer(serialization_schema)
        )

        # Add optional security settings
        if "security_protocol" in connection_config:
            kafka_sink_builder.set_property(
                "security.protocol", connection_config["security_protocol"]
            )
        if "sasl_mechanism" in connection_config:
            kafka_sink_builder.set_property(
                "sasl.mechanism", connection_config["sasl_mechanism"]
            )
        if "sasl_username" in connection_config:
            kafka_sink_builder.set_property(
                "sasl.jaas.config",
                f"org.apache.kafka.common.security.plain.PlainLoginModule required "
                f"username=\"{connection_config['sasl_username']}\" "
                f"password=\"{connection_config.get('sasl_password', '')}\";",
            )

        kafka_sink = kafka_sink_builder.build()

        # Extract event bytes from (event, context) tuples and convert to string
        def extract_event(value: tuple) -> str:
            event, context = value
            if isinstance(event, bytes):
                return event.decode("utf-8")
            elif isinstance(event, dict):
                return json.dumps(event)
            return str(event)

        stream.map(extract_event).sink_to(kafka_sink)


# Register adapters on module import
register_source_adapter("KafkaSource", KafkaSourceAdapter)
register_sink_adapter("KafkaSink", KafkaSinkAdapter)
