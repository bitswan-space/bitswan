"""
End-to-end integration test harness for the Kafka2Kafka example.

This module provides a comprehensive test harness that:
1. Spins up a real Kafka broker using testcontainers
2. Creates source and sink topics
3. Runs the kafka2kafka pipeline (uppercase + reverse transformation)
4. Produces test messages to the source topic
5. Consumes messages from the sink topic
6. Verifies the transformations were applied correctly

Usage:
    pytest test/kafka/test_kafka2kafka_e2e.py -v

Requirements:
    pip install testcontainers[kafka] pytest pytest-asyncio

Environment variables (optional, for using external Kafka):
    KAFKA_BOOTSTRAP_SERVERS: Bootstrap servers (e.g., "localhost:9092")
    KAFKA_USE_EXTERNAL: Set to "true" to use external Kafka instead of testcontainers
"""

import asyncio
import json
import logging
import os
import signal
import time
import unittest
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from unittest.mock import patch

import confluent_kafka
from confluent_kafka.admin import AdminClient, NewTopic

# BitSwan imports
import bspump
import bspump.kafka
from bspump.asab.abc.singleton import Singleton

L = logging.getLogger(__name__)


# ============================================================================
# Kafka Test Infrastructure
# ============================================================================


class KafkaTestCluster:
    """
    Manages a Kafka test cluster, either via testcontainers or external connection.
    """

    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        use_testcontainers: bool = True,
    ):
        self.bootstrap_servers = bootstrap_servers
        self.use_testcontainers = use_testcontainers
        self._container = None
        self._admin_client = None

    def start(self) -> str:
        """Start the Kafka cluster and return bootstrap servers."""
        if self.bootstrap_servers:
            L.info(f"Using external Kafka at {self.bootstrap_servers}")
            return self.bootstrap_servers

        if self.use_testcontainers:
            return self._start_testcontainers()

        raise ValueError("No Kafka bootstrap servers configured")

    def _start_testcontainers(self) -> str:
        """Start Kafka using testcontainers."""
        try:
            from testcontainers.kafka import KafkaContainer
        except ImportError:
            raise ImportError(
                "testcontainers[kafka] is required for integration tests. "
                "Install with: pip install testcontainers[kafka]"
            )

        L.info("Starting Kafka container via testcontainers...")
        self._container = KafkaContainer()
        self._container.start()

        self.bootstrap_servers = self._container.get_bootstrap_server()
        L.info(f"Kafka container started at {self.bootstrap_servers}")
        return self.bootstrap_servers

    def stop(self):
        """Stop the Kafka cluster."""
        if self._admin_client:
            self._admin_client = None

        if self._container:
            L.info("Stopping Kafka container...")
            self._container.stop()
            self._container = None

    def get_admin_client(self) -> AdminClient:
        """Get or create an AdminClient for topic management."""
        if self._admin_client is None:
            self._admin_client = AdminClient(
                {"bootstrap.servers": self.bootstrap_servers}
            )
        return self._admin_client

    def create_topics(
        self,
        topics: List[str],
        num_partitions: int = 1,
        replication_factor: int = 1,
        timeout: float = 30.0,
    ):
        """Create Kafka topics."""
        admin = self.get_admin_client()

        new_topics = [
            NewTopic(topic, num_partitions=num_partitions, replication_factor=replication_factor)
            for topic in topics
        ]

        futures = admin.create_topics(new_topics)

        for topic, future in futures.items():
            try:
                future.result(timeout=timeout)
                L.info(f"Created topic: {topic}")
            except Exception as e:
                # Topic may already exist
                if "already exists" in str(e).lower():
                    L.info(f"Topic already exists: {topic}")
                else:
                    raise

    def delete_topics(self, topics: List[str], timeout: float = 30.0):
        """Delete Kafka topics."""
        admin = self.get_admin_client()
        futures = admin.delete_topics(topics)

        for topic, future in futures.items():
            try:
                future.result(timeout=timeout)
                L.info(f"Deleted topic: {topic}")
            except Exception as e:
                L.warning(f"Failed to delete topic {topic}: {e}")

    def wait_for_kafka_ready(self, timeout: float = 60.0):
        """Wait for Kafka to be ready to accept connections."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                admin = self.get_admin_client()
                # Try to list topics as a health check
                admin.list_topics(timeout=5.0)
                L.info("Kafka is ready")
                return
            except Exception as e:
                L.debug(f"Waiting for Kafka... ({e})")
                time.sleep(1.0)

        raise TimeoutError(f"Kafka not ready after {timeout}s")


# ============================================================================
# Test Producers and Consumers
# ============================================================================


class KafkaTestProducer:
    """A simple Kafka producer for sending test messages."""

    def __init__(self, bootstrap_servers: str, topic: str):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self._producer = None

    def start(self):
        """Initialize the producer."""
        self._producer = confluent_kafka.Producer(
            {
                "bootstrap.servers": self.bootstrap_servers,
                "acks": "all",
            }
        )

    def send(self, messages: List[bytes], flush: bool = True):
        """Send messages to the topic."""
        for msg in messages:
            self._producer.produce(self.topic, value=msg)
            L.debug(f"Sent message to {self.topic}: {msg}")

        if flush:
            self._producer.flush(timeout=10.0)

    def stop(self):
        """Flush and close the producer."""
        if self._producer:
            self._producer.flush(timeout=10.0)
            self._producer = None


class KafkaTestConsumer:
    """A simple Kafka consumer for receiving test messages."""

    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        group_id: str = "test-consumer-group",
    ):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self._consumer = None

    def start(self):
        """Initialize the consumer."""
        self._consumer = confluent_kafka.Consumer(
            {
                "bootstrap.servers": self.bootstrap_servers,
                "group.id": self.group_id,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": "true",
            }
        )
        self._consumer.subscribe([self.topic])

    def consume(
        self,
        expected_count: int,
        timeout: float = 30.0,
    ) -> List[bytes]:
        """
        Consume messages from the topic.

        Args:
            expected_count: Number of messages to wait for
            timeout: Maximum time to wait in seconds

        Returns:
            List of message values (bytes)
        """
        messages = []
        start_time = time.time()

        while len(messages) < expected_count:
            if time.time() - start_time > timeout:
                L.warning(
                    f"Timeout waiting for messages. Got {len(messages)}/{expected_count}"
                )
                break

            msg = self._consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                L.error(f"Consumer error: {msg.error()}")
                continue

            messages.append(msg.value())
            L.debug(f"Received message from {self.topic}: {msg.value()}")

        return messages

    def stop(self):
        """Close the consumer."""
        if self._consumer:
            self._consumer.close()
            self._consumer = None


# ============================================================================
# Test Harness
# ============================================================================


class Kafka2KafkaTestHarness:
    """
    Test harness for running end-to-end Kafka2Kafka integration tests.

    This harness manages:
    - Kafka cluster (via testcontainers or external)
    - Topic creation/deletion
    - Test producers and consumers
    - BSPump application lifecycle
    """

    def __init__(
        self,
        source_topic: str = "test-source",
        sink_topic: str = "test-sink",
        consumer_group: str = "test-pipeline-consumer",
        bootstrap_servers: Optional[str] = None,
        use_testcontainers: bool = True,
    ):
        self.source_topic = source_topic
        self.sink_topic = sink_topic
        self.consumer_group = consumer_group

        # Check for environment variable overrides
        env_bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS")
        env_use_external = os.environ.get("KAFKA_USE_EXTERNAL", "").lower() == "true"

        if env_bootstrap:
            bootstrap_servers = env_bootstrap
            use_testcontainers = False
        elif env_use_external:
            use_testcontainers = False

        self.kafka_cluster = KafkaTestCluster(
            bootstrap_servers=bootstrap_servers,
            use_testcontainers=use_testcontainers,
        )

        self.producer: Optional[KafkaTestProducer] = None
        self.consumer: Optional[KafkaTestConsumer] = None
        self.app: Optional[bspump.BSPumpApplication] = None
        self._app_task: Optional[asyncio.Task] = None

    def setup(self):
        """Set up the test environment."""
        # Start Kafka
        self.bootstrap_servers = self.kafka_cluster.start()
        self.kafka_cluster.wait_for_kafka_ready()

        # Create topics
        self.kafka_cluster.create_topics([self.source_topic, self.sink_topic])

        # Allow topics to be ready
        time.sleep(2.0)

        # Set up producer and consumer
        self.producer = KafkaTestProducer(self.bootstrap_servers, self.source_topic)
        self.producer.start()

        self.consumer = KafkaTestConsumer(
            self.bootstrap_servers,
            self.sink_topic,
            group_id="test-sink-consumer",
        )
        self.consumer.start()

    def run_pipeline_async(self, duration: float = 10.0):
        """Run the pipeline for a specified duration using subprocess."""
        import subprocess
        import sys
        import textwrap

        # Create a Python script to run the pipeline
        script = textwrap.dedent(f'''
            import sys
            import signal
            import bspump
            import bspump.kafka
            import json

            class JsonDecodeProcessor(bspump.Processor):
                def process(self, context, event):
                    return json.loads(event.decode("utf-8"))

            class UppercaseProcessor(bspump.Processor):
                def process(self, context, event):
                    if "foo" in event:
                        event["foo"] = event["foo"].upper()
                    return event

            class ReverseProcessor(bspump.Processor):
                def process(self, context, event):
                    if "foo" in event:
                        event["foo"] = "".join(reversed(list(event["foo"])))
                    return event

            class JsonEncodeProcessor(bspump.Processor):
                def process(self, context, event):
                    return json.dumps(event).encode("utf-8")

            class Kafka2KafkaPipeline(bspump.Pipeline):
                def __init__(self, app):
                    super().__init__(app, "Kafka2KafkaPipeline")
                    self.build(
                        bspump.kafka.KafkaSource(
                            app, self, connection="KafkaConnection",
                            config={{
                                "topic": "{self.source_topic}",
                                "group.id": "{self.consumer_group}",
                                "auto.offset.reset": "earliest",
                            }},
                        ),
                        JsonDecodeProcessor(app, self),
                        UppercaseProcessor(app, self),
                        ReverseProcessor(app, self),
                        JsonEncodeProcessor(app, self),
                        bspump.kafka.KafkaSink(
                            app, self, connection="KafkaConnection",
                            config={{"topic": "{self.sink_topic}"}},
                        ),
                    )

            if __name__ == "__main__":
                app = bspump.BSPumpApplication(args=[])
                svc = app.get_service("bspump.PumpService")
                svc.add_connection(
                    bspump.kafka.KafkaConnection(
                        app, "KafkaConnection",
                        config={{"bootstrap_servers": "{self.bootstrap_servers}"}},
                    )
                )
                svc.add_pipeline(Kafka2KafkaPipeline(app))
                app.run()
        ''')

        # Start the pipeline process
        self._pipeline_process = subprocess.Popen(
            [sys.executable, "-c", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Let it run for the duration
        time.sleep(duration)

        # Stop the pipeline
        self._pipeline_process.terminate()
        try:
            self._pipeline_process.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            self._pipeline_process.kill()
            self._pipeline_process.wait()

    def send_test_messages(self, messages: List[Dict[str, Any]]):
        """Send test messages to the source topic."""
        encoded = [json.dumps(msg).encode("utf-8") for msg in messages]
        self.producer.send(encoded)

    def receive_messages(
        self,
        expected_count: int,
        timeout: float = 30.0,
    ) -> List[Dict[str, Any]]:
        """Receive messages from the sink topic."""
        raw_messages = self.consumer.consume(expected_count, timeout)
        return [json.loads(msg.decode("utf-8")) for msg in raw_messages]

    def teardown(self):
        """Tear down the test environment."""
        if self.producer:
            self.producer.stop()

        if self.consumer:
            self.consumer.stop()

        if self.app:
            try:
                Singleton.delete(self.app.__class__)
            except Exception:
                pass
            self.app = None

        # Clean up topics
        try:
            self.kafka_cluster.delete_topics([self.source_topic, self.sink_topic])
        except Exception as e:
            L.warning(f"Failed to delete topics: {e}")

        self.kafka_cluster.stop()

    @contextmanager
    def context(self):
        """Context manager for the test harness."""
        try:
            self.setup()
            yield self
        finally:
            self.teardown()


# ============================================================================
# Test Cases
# ============================================================================


class TestKafka2KafkaE2E(unittest.TestCase):
    """End-to-end integration tests for Kafka2Kafka pipeline."""

    @classmethod
    def setUpClass(cls):
        """Set up logging for tests."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def test_single_message_transformation(self):
        """Test that a single message is correctly transformed."""
        harness = Kafka2KafkaTestHarness(
            source_topic="test-e2e-source-single",
            sink_topic="test-e2e-sink-single",
        )

        with harness.context():
            # Send test message
            test_messages = [{"foo": "bar"}]
            harness.send_test_messages(test_messages)

            # Run pipeline
            harness.run_pipeline_async(duration=5.0)

            # Receive and verify
            received = harness.receive_messages(expected_count=1, timeout=10.0)

            self.assertEqual(len(received), 1)
            # bar -> BAR -> RAB
            self.assertEqual(received[0]["foo"], "RAB")

    def test_multiple_messages_transformation(self):
        """Test that multiple messages are correctly transformed."""
        harness = Kafka2KafkaTestHarness(
            source_topic="test-e2e-source-multi",
            sink_topic="test-e2e-sink-multi",
        )

        with harness.context():
            # Send test messages
            test_messages = [
                {"foo": "bap"},
                {"foo": "baz"},
                {"foo": "hello"},
            ]
            harness.send_test_messages(test_messages)

            # Run pipeline
            harness.run_pipeline_async(duration=5.0)

            # Receive and verify
            received = harness.receive_messages(expected_count=3, timeout=15.0)

            self.assertEqual(len(received), 3)

            # Verify transformations (order may vary)
            expected_values = {"PAB", "ZAB", "OLLEH"}  # uppercase + reversed
            actual_values = {msg["foo"] for msg in received}
            self.assertEqual(actual_values, expected_values)

    def test_empty_string_transformation(self):
        """Test transformation of empty strings."""
        harness = Kafka2KafkaTestHarness(
            source_topic="test-e2e-source-empty",
            sink_topic="test-e2e-sink-empty",
        )

        with harness.context():
            test_messages = [{"foo": ""}]
            harness.send_test_messages(test_messages)

            harness.run_pipeline_async(duration=5.0)

            received = harness.receive_messages(expected_count=1, timeout=10.0)

            self.assertEqual(len(received), 1)
            self.assertEqual(received[0]["foo"], "")

    def test_special_characters_transformation(self):
        """Test transformation of strings with special characters."""
        harness = Kafka2KafkaTestHarness(
            source_topic="test-e2e-source-special",
            sink_topic="test-e2e-sink-special",
        )

        with harness.context():
            test_messages = [{"foo": "hello123"}]
            harness.send_test_messages(test_messages)

            harness.run_pipeline_async(duration=5.0)

            received = harness.receive_messages(expected_count=1, timeout=10.0)

            self.assertEqual(len(received), 1)
            # hello123 -> HELLO123 -> 321OLLEH
            self.assertEqual(received[0]["foo"], "321OLLEH")

    def test_unicode_transformation(self):
        """Test transformation of unicode strings."""
        harness = Kafka2KafkaTestHarness(
            source_topic="test-e2e-source-unicode",
            sink_topic="test-e2e-sink-unicode",
        )

        with harness.context():
            test_messages = [{"foo": "cafe"}]  # ASCII for predictable uppercase
            harness.send_test_messages(test_messages)

            harness.run_pipeline_async(duration=5.0)

            received = harness.receive_messages(expected_count=1, timeout=10.0)

            self.assertEqual(len(received), 1)
            # cafe -> CAFE -> EFAC
            self.assertEqual(received[0]["foo"], "EFAC")

    def test_preserves_additional_fields(self):
        """Test that additional fields in the message are preserved."""
        harness = Kafka2KafkaTestHarness(
            source_topic="test-e2e-source-preserve",
            sink_topic="test-e2e-sink-preserve",
        )

        with harness.context():
            test_messages = [
                {"foo": "test", "bar": "unchanged", "count": 42}
            ]
            harness.send_test_messages(test_messages)

            harness.run_pipeline_async(duration=5.0)

            received = harness.receive_messages(expected_count=1, timeout=10.0)

            self.assertEqual(len(received), 1)
            self.assertEqual(received[0]["foo"], "TSET")  # TEST -> TSET
            self.assertEqual(received[0]["bar"], "unchanged")
            self.assertEqual(received[0]["count"], 42)


# ============================================================================
# Standalone test runner for quick validation
# ============================================================================


def run_quick_test():
    """
    Run a quick standalone test to validate the harness works.
    This can be run directly without pytest.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("=" * 60)
    print("Kafka2Kafka E2E Integration Test")
    print("=" * 60)

    harness = Kafka2KafkaTestHarness(
        source_topic="quick-test-source",
        sink_topic="quick-test-sink",
    )

    try:
        print("\n[1/5] Setting up test environment...")
        harness.setup()
        print("      Done!")

        print("\n[2/5] Sending test messages...")
        test_messages = [
            {"foo": "bap"},
            {"foo": "baz"},
        ]
        harness.send_test_messages(test_messages)
        print(f"      Sent {len(test_messages)} messages")

        print("\n[3/5] Running pipeline...")
        harness.run_pipeline_async(duration=5.0)
        print("      Done!")

        print("\n[4/5] Receiving transformed messages...")
        received = harness.receive_messages(expected_count=2, timeout=15.0)
        print(f"      Received {len(received)} messages")

        print("\n[5/5] Verifying results...")
        expected = {"PAB", "ZAB"}  # uppercase + reversed
        actual = {msg["foo"] for msg in received}

        if actual == expected:
            print("      SUCCESS! All transformations correct.")
            print(f"      Expected: {expected}")
            print(f"      Actual:   {actual}")
        else:
            print("      FAILURE! Transformation mismatch.")
            print(f"      Expected: {expected}")
            print(f"      Actual:   {actual}")
            return 1

    except Exception as e:
        print(f"\n      ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        print("\n[Cleanup] Tearing down test environment...")
        harness.teardown()
        print("          Done!")

    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(run_quick_test())
