"""
Pytest fixtures for Kafka integration tests.

This module provides shared fixtures for Kafka testing, including:
- Kafka cluster management (testcontainers or external)
- Topic creation/cleanup
- Producer and consumer utilities
"""

import logging
import os
import pytest
import time
from typing import Generator, Optional

# Try to import testcontainers
try:
    from testcontainers.kafka import KafkaContainer
    TESTCONTAINERS_AVAILABLE = True
except ImportError:
    TESTCONTAINERS_AVAILABLE = False


L = logging.getLogger(__name__)


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "kafka: mark test as requiring a Kafka broker",
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow-running",
    )


def pytest_collection_modifyitems(config, items):
    """Skip Kafka tests if testcontainers not available and no external Kafka."""
    external_kafka = os.environ.get("KAFKA_BOOTSTRAP_SERVERS")

    if TESTCONTAINERS_AVAILABLE or external_kafka:
        return

    skip_kafka = pytest.mark.skip(
        reason="testcontainers[kafka] not installed and KAFKA_BOOTSTRAP_SERVERS not set"
    )

    for item in items:
        if "kafka" in item.keywords:
            item.add_marker(skip_kafka)


@pytest.fixture(scope="session")
def kafka_bootstrap_servers() -> Generator[str, None, None]:
    """
    Provide Kafka bootstrap servers for tests.

    Uses testcontainers if available, otherwise falls back to
    KAFKA_BOOTSTRAP_SERVERS environment variable.
    """
    external = os.environ.get("KAFKA_BOOTSTRAP_SERVERS")

    if external:
        L.info(f"Using external Kafka at {external}")
        yield external
        return

    if not TESTCONTAINERS_AVAILABLE:
        pytest.skip("testcontainers[kafka] not installed")

    L.info("Starting Kafka container...")
    container = KafkaContainer()
    container.start()

    bootstrap_servers = container.get_bootstrap_server()
    L.info(f"Kafka container started at {bootstrap_servers}")

    # Wait for Kafka to be ready
    _wait_for_kafka(bootstrap_servers)

    try:
        yield bootstrap_servers
    finally:
        L.info("Stopping Kafka container...")
        container.stop()


def _wait_for_kafka(bootstrap_servers: str, timeout: float = 60.0):
    """Wait for Kafka to be ready."""
    from confluent_kafka.admin import AdminClient

    start = time.time()
    while time.time() - start < timeout:
        try:
            admin = AdminClient({"bootstrap.servers": bootstrap_servers})
            admin.list_topics(timeout=5.0)
            L.info("Kafka is ready")
            return
        except Exception as e:
            L.debug(f"Waiting for Kafka: {e}")
            time.sleep(1.0)

    raise TimeoutError(f"Kafka not ready after {timeout}s")


@pytest.fixture
def kafka_admin_client(kafka_bootstrap_servers):
    """Provide a Kafka AdminClient."""
    from confluent_kafka.admin import AdminClient

    return AdminClient({"bootstrap.servers": kafka_bootstrap_servers})


@pytest.fixture
def create_topics(kafka_admin_client):
    """
    Factory fixture to create Kafka topics.

    Usage:
        def test_something(create_topics):
            topics = create_topics(["topic1", "topic2"])
            # topics will be cleaned up after test
    """
    from confluent_kafka.admin import NewTopic

    created_topics = []

    def _create(topic_names: list, num_partitions: int = 1):
        new_topics = [
            NewTopic(name, num_partitions=num_partitions, replication_factor=1)
            for name in topic_names
        ]

        futures = kafka_admin_client.create_topics(new_topics)
        for topic, future in futures.items():
            try:
                future.result(timeout=30.0)
                created_topics.append(topic)
                L.info(f"Created topic: {topic}")
            except Exception as e:
                if "already exists" not in str(e).lower():
                    raise

        # Give topics time to be ready
        time.sleep(1.0)
        return topic_names

    yield _create

    # Cleanup
    if created_topics:
        futures = kafka_admin_client.delete_topics(created_topics)
        for topic, future in futures.items():
            try:
                future.result(timeout=10.0)
                L.info(f"Deleted topic: {topic}")
            except Exception as e:
                L.warning(f"Failed to delete topic {topic}: {e}")


@pytest.fixture
def kafka_producer(kafka_bootstrap_servers):
    """Provide a Kafka producer."""
    import confluent_kafka

    producer = confluent_kafka.Producer({
        "bootstrap.servers": kafka_bootstrap_servers,
        "acks": "all",
    })

    yield producer

    producer.flush(timeout=10.0)


@pytest.fixture
def kafka_consumer_factory(kafka_bootstrap_servers):
    """
    Factory fixture to create Kafka consumers.

    Usage:
        def test_something(kafka_consumer_factory):
            consumer = kafka_consumer_factory("my-topic", "my-group")
    """
    import confluent_kafka

    consumers = []

    def _create(topic: str, group_id: str):
        consumer = confluent_kafka.Consumer({
            "bootstrap.servers": kafka_bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": "true",
        })
        consumer.subscribe([topic])
        consumers.append(consumer)
        return consumer

    yield _create

    for consumer in consumers:
        try:
            consumer.close()
        except Exception:
            pass
