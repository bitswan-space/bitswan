"""
Unit tests for the Flink adapter infrastructure.

These tests verify the adapter system works correctly without
requiring a full PyFlink cluster or Kafka broker.
"""

import os
import sys
import tempfile
import unittest

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestFlinkConfig(unittest.TestCase):
    """Tests for FlinkConfig configuration loading."""

    def test_load_empty_config(self):
        """Test loading with no config file."""
        from bspump.flink.config import FlinkConfig

        config = FlinkConfig("/nonexistent/path.conf")
        self.assertEqual(config.connections, {})
        self.assertEqual(config.pipelines, {})

    def test_load_basic_config(self):
        """Test loading a basic config file."""
        from bspump.flink.config import FlinkConfig

        config_content = """
[connection:KafkaConnection]
bootstrap_servers=localhost:9092
security_protocol=PLAINTEXT

[pipeline:TestPipeline:KafkaSource]
topic=source-topic
group_id=test-group

[pipeline:TestPipeline:KafkaSink]
topic=sink-topic
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".conf", delete=False
        ) as f:
            f.write(config_content)
            config_path = f.name

        try:
            config = FlinkConfig(config_path)

            # Check connection
            self.assertIn("KafkaConnection", config.connections)
            self.assertEqual(
                config.connections["KafkaConnection"]["bootstrap_servers"],
                "localhost:9092",
            )

            # Check pipeline components
            source = config.get_source_config("TestPipeline")
            self.assertIsNotNone(source)
            self.assertEqual(source["topic"], "source-topic")

            sink = config.get_sink_config("TestPipeline")
            self.assertIsNotNone(sink)
            self.assertEqual(sink["topic"], "sink-topic")
        finally:
            os.unlink(config_path)

    def test_env_var_expansion(self):
        """Test environment variable expansion."""
        from bspump.flink.config import FlinkConfig

        os.environ["TEST_KAFKA_HOST"] = "kafka.example.com"
        os.environ["TEST_KAFKA_PORT"] = "9093"

        config_content = """
[connection:KafkaConnection]
bootstrap_servers=${TEST_KAFKA_HOST}:${TEST_KAFKA_PORT}
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".conf", delete=False
        ) as f:
            f.write(config_content)
            config_path = f.name

        try:
            config = FlinkConfig(config_path)
            self.assertEqual(
                config.connections["KafkaConnection"]["bootstrap_servers"],
                "kafka.example.com:9093",
            )
        finally:
            os.unlink(config_path)
            del os.environ["TEST_KAFKA_HOST"]
            del os.environ["TEST_KAFKA_PORT"]


class TestFlinkAdapters(unittest.TestCase):
    """Tests for the adapter registration system."""

    def test_adapter_registration(self):
        """Test registering custom adapters."""
        from bspump.flink.adapters import (
            FlinkSourceAdapter,
            FlinkSinkAdapter,
            register_source_adapter,
            register_sink_adapter,
            get_source_adapter,
            get_sink_adapter,
            FLINK_SOURCE_ADAPTERS,
            FLINK_SINK_ADAPTERS,
        )

        # Create test adapters
        class TestSourceAdapter(FlinkSourceAdapter):
            def create_source(self, env, conn_config, comp_config):
                return None

        class TestSinkAdapter(FlinkSinkAdapter):
            def add_sink(self, stream, conn_config, comp_config):
                pass

        # Register
        register_source_adapter("TestSource", TestSourceAdapter)
        register_sink_adapter("TestSink", TestSinkAdapter)

        # Verify registration
        self.assertIn("TestSource", FLINK_SOURCE_ADAPTERS)
        self.assertIn("TestSink", FLINK_SINK_ADAPTERS)

        # Verify retrieval
        self.assertEqual(get_source_adapter("TestSource"), TestSourceAdapter)
        self.assertEqual(get_sink_adapter("TestSink"), TestSinkAdapter)

    def test_builtin_kafka_adapters(self):
        """Test that Kafka adapters are registered by default."""
        from bspump.flink.adapters import (
            FLINK_SOURCE_ADAPTERS,
            FLINK_SINK_ADAPTERS,
        )

        # Import kafka module to trigger registration
        from bspump.flink import kafka  # noqa

        self.assertIn("KafkaSource", FLINK_SOURCE_ADAPTERS)
        self.assertIn("KafkaSink", FLINK_SINK_ADAPTERS)


class TestFlinkRuntime(unittest.TestCase):
    """Tests for FlinkRuntime step registration."""

    def test_register_step(self):
        """Test registering a step function."""
        from bspump.flink.runtime import FlinkRuntime

        runtime = FlinkRuntime()
        runtime.new_pipeline("TestPipeline")

        @runtime.register_step
        def my_step(event):
            return event.upper()

        self.assertEqual(len(runtime.pipelines["TestPipeline"].steps), 1)
        self.assertEqual(runtime.pipelines["TestPipeline"].steps[0].name, "my_step")
        self.assertFalse(runtime.pipelines["TestPipeline"].steps[0].is_generator)

    def test_register_async_step(self):
        """Test registering an async_step function."""
        from bspump.flink.runtime import FlinkRuntime

        runtime = FlinkRuntime()
        runtime.new_pipeline("TestPipeline")

        @runtime.register_async_step
        async def my_generator(inject, event):
            await inject(event)
            await inject(event)

        self.assertEqual(len(runtime.pipelines["TestPipeline"].steps), 1)
        self.assertEqual(
            runtime.pipelines["TestPipeline"].steps[0].name, "my_generator"
        )
        self.assertTrue(runtime.pipelines["TestPipeline"].steps[0].is_generator)

    def test_multiple_pipelines(self):
        """Test registering multiple pipelines."""
        from bspump.flink.runtime import FlinkRuntime

        runtime = FlinkRuntime()

        runtime.new_pipeline("Pipeline1")

        @runtime.register_step
        def step1(event):
            return event

        runtime.end_pipeline()

        runtime.new_pipeline("Pipeline2")

        @runtime.register_step
        def step2(event):
            return event

        runtime.end_pipeline()

        self.assertEqual(len(runtime.pipelines), 2)
        self.assertEqual(len(runtime.pipelines["Pipeline1"].steps), 1)
        self.assertEqual(len(runtime.pipelines["Pipeline2"].steps), 1)


class TestFlinkOperators(unittest.TestCase):
    """Tests for Flink operator wrappers."""

    def test_map_function_creation(self):
        """Test creating a map function from a step."""
        from bspump.flink.operators import create_map_function

        def my_step(event):
            if isinstance(event, bytes):
                return event.upper()
            return event

        map_fn = create_map_function(my_step)
        self.assertIsNotNone(map_fn.func_bytes)

    def test_flat_map_function_creation(self):
        """Test creating a flat_map function from an async_step."""
        from bspump.flink.operators import create_flat_map_function

        async def my_generator(inject, event):
            await inject(event)

        flat_map_fn = create_flat_map_function(my_generator)
        self.assertIsNotNone(flat_map_fn.func_bytes)

    def test_map_function_execution(self):
        """Test executing a map function."""
        import cloudpickle
        from bspump.flink.operators import BitSwanMapFunction

        def my_step(event):
            if isinstance(event, bytes):
                return event.upper()
            return str(event).upper().encode()

        func_bytes = cloudpickle.dumps(my_step)
        map_fn = BitSwanMapFunction(func_bytes)
        map_fn.open(None)

        result = map_fn.map((b"hello", {"key": "value"}))
        self.assertEqual(result[0], b"HELLO")
        self.assertEqual(result[1], {"key": "value"})

    def test_flat_map_function_execution(self):
        """Test executing a flat_map function."""
        import cloudpickle
        from bspump.flink.operators import BitSwanFlatMapFunction

        async def my_generator(inject, event):
            await inject(event)
            await inject(event + b"-copy")

        func_bytes = cloudpickle.dumps(my_generator)
        flat_map_fn = BitSwanFlatMapFunction(func_bytes)
        flat_map_fn.open(None)

        results = list(flat_map_fn.flat_map((b"test", {"k": "v"})))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][0], b"test")
        self.assertEqual(results[1][0], b"test-copy")


class TestRuntimeDetection(unittest.TestCase):
    """Tests for runtime detection."""

    def test_detect_flink_runtime(self):
        """Test detection with BITSWAN_RUNTIME=flink."""
        from bspump.flink.runtime import detect_runtime

        original = os.environ.get("BITSWAN_RUNTIME")
        try:
            os.environ["BITSWAN_RUNTIME"] = "flink"
            self.assertEqual(detect_runtime(), "flink")
        finally:
            if original:
                os.environ["BITSWAN_RUNTIME"] = original
            else:
                os.environ.pop("BITSWAN_RUNTIME", None)

    def test_detect_bspump_runtime(self):
        """Test detection with BITSWAN_RUNTIME=bspump."""
        from bspump.flink.runtime import detect_runtime

        original = os.environ.get("BITSWAN_RUNTIME")
        try:
            os.environ["BITSWAN_RUNTIME"] = "bspump"
            self.assertEqual(detect_runtime(), "bspump")
        finally:
            if original:
                os.environ["BITSWAN_RUNTIME"] = original
            else:
                os.environ.pop("BITSWAN_RUNTIME", None)


if __name__ == "__main__":
    unittest.main()
