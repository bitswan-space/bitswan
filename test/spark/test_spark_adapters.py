"""
Unit tests for the Spark adapter infrastructure.

These tests verify the adapter system works correctly without
requiring a full PySpark cluster or Kafka broker.
"""

import os
import sys
import tempfile
import unittest

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestSparkConfig(unittest.TestCase):
    """Tests for SparkConfig configuration loading."""

    def test_load_empty_config(self):
        """Test loading with no config file."""
        from bspump.spark.config import SparkConfig

        config = SparkConfig("/nonexistent/path.conf")
        self.assertEqual(config.connections, {})
        self.assertEqual(config.pipelines, {})

    def test_load_basic_config(self):
        """Test loading a basic config file."""
        from bspump.spark.config import SparkConfig

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
            config = SparkConfig(config_path)

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
        from bspump.spark.config import SparkConfig

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
            config = SparkConfig(config_path)
            self.assertEqual(
                config.connections["KafkaConnection"]["bootstrap_servers"],
                "kafka.example.com:9093",
            )
        finally:
            os.unlink(config_path)
            del os.environ["TEST_KAFKA_HOST"]
            del os.environ["TEST_KAFKA_PORT"]


class TestSparkAdapters(unittest.TestCase):
    """Tests for the adapter registration system."""

    def test_adapter_registration(self):
        """Test registering custom adapters."""
        from bspump.spark.adapters import (
            SparkSourceAdapter,
            SparkSinkAdapter,
            register_source_adapter,
            register_sink_adapter,
            get_source_adapter,
            get_sink_adapter,
            SPARK_SOURCE_ADAPTERS,
            SPARK_SINK_ADAPTERS,
        )

        # Create test adapters
        class TestSourceAdapter(SparkSourceAdapter):
            def create_source(self, spark, conn_config, comp_config):
                return None

        class TestSinkAdapter(SparkSinkAdapter):
            def add_sink(self, df, conn_config, comp_config, trigger_config):
                return None

        # Register
        register_source_adapter("TestSource", TestSourceAdapter)
        register_sink_adapter("TestSink", TestSinkAdapter)

        # Verify registration
        self.assertIn("TestSource", SPARK_SOURCE_ADAPTERS)
        self.assertIn("TestSink", SPARK_SINK_ADAPTERS)

        # Verify retrieval
        self.assertEqual(get_source_adapter("TestSource"), TestSourceAdapter)
        self.assertEqual(get_sink_adapter("TestSink"), TestSinkAdapter)

    def test_builtin_kafka_adapters(self):
        """Test that Kafka adapters are registered by default."""
        from bspump.spark.adapters import (
            SPARK_SOURCE_ADAPTERS,
            SPARK_SINK_ADAPTERS,
        )

        # Import kafka module to trigger registration
        from bspump.spark import kafka  # noqa

        self.assertIn("KafkaSource", SPARK_SOURCE_ADAPTERS)
        self.assertIn("KafkaSink", SPARK_SINK_ADAPTERS)


class TestSparkRuntime(unittest.TestCase):
    """Tests for SparkRuntime step registration."""

    def test_register_step(self):
        """Test registering a step function."""
        from bspump.spark.runtime import SparkRuntime

        runtime = SparkRuntime()
        runtime.new_pipeline("TestPipeline")

        @runtime.register_step
        def my_step(event):
            return event.upper()

        self.assertEqual(len(runtime.pipelines["TestPipeline"].steps), 1)
        self.assertEqual(runtime.pipelines["TestPipeline"].steps[0].name, "my_step")
        self.assertFalse(runtime.pipelines["TestPipeline"].steps[0].is_generator)

    def test_register_async_step(self):
        """Test registering an async_step function."""
        from bspump.spark.runtime import SparkRuntime

        runtime = SparkRuntime()
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
        from bspump.spark.runtime import SparkRuntime

        runtime = SparkRuntime()

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

    def test_set_trigger(self):
        """Test setting trigger configuration."""
        from bspump.spark.runtime import SparkRuntime

        runtime = SparkRuntime()

        # Default trigger
        self.assertEqual(runtime._trigger_config["trigger"], "1 second")

        # Set custom trigger
        runtime.set_trigger(trigger="once", checkpoint_dir="/custom/checkpoint")
        self.assertEqual(runtime._trigger_config["trigger"], "once")
        self.assertEqual(
            runtime._trigger_config["checkpoint_dir"], "/custom/checkpoint"
        )


class TestSparkOperators(unittest.TestCase):
    """Tests for Spark operator wrappers."""

    def test_map_function_creation(self):
        """Test creating a map function from a step."""
        import cloudpickle
        from bspump.spark.operators import BitSwanMapFunction

        def my_step(event):
            if isinstance(event, bytes):
                return event.upper()
            return event

        func_bytes = cloudpickle.dumps(my_step)
        map_fn = BitSwanMapFunction(func_bytes)
        self.assertIsNotNone(map_fn.func_bytes)

    def test_flat_map_function_creation(self):
        """Test creating a flat_map function from an async_step."""
        import cloudpickle
        from bspump.spark.operators import BitSwanFlatMapFunction

        async def my_generator(inject, event):
            await inject(event)

        func_bytes = cloudpickle.dumps(my_generator)
        flat_map_fn = BitSwanFlatMapFunction(func_bytes)
        self.assertIsNotNone(flat_map_fn.func_bytes)

    def test_map_function_execution(self):
        """Test executing a map function."""
        import cloudpickle
        from bspump.spark.operators import BitSwanMapFunction

        def my_step(event):
            if isinstance(event, bytes):
                return event.upper()
            return str(event).upper().encode()

        func_bytes = cloudpickle.dumps(my_step)
        map_fn = BitSwanMapFunction(func_bytes)
        map_fn.open(None)

        result = map_fn.map("hello")
        self.assertEqual(result, "HELLO")

    def test_flat_map_function_execution(self):
        """Test executing a flat_map function."""
        import cloudpickle
        from bspump.spark.operators import BitSwanFlatMapFunction

        async def my_generator(inject, event):
            await inject(event)
            await inject(event + b"-copy")

        func_bytes = cloudpickle.dumps(my_generator)
        flat_map_fn = BitSwanFlatMapFunction(func_bytes)
        flat_map_fn.open(None)

        results = flat_map_fn.flat_map("test")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], "test")
        self.assertEqual(results[1], "test-copy")

    def test_map_function_with_json(self):
        """Test map function handling JSON data."""
        import json
        import cloudpickle
        from bspump.spark.operators import BitSwanMapFunction

        def transform_json(event):
            data = json.loads(event.decode())
            data["foo"] = data["foo"].upper()
            return json.dumps(data).encode()

        func_bytes = cloudpickle.dumps(transform_json)
        map_fn = BitSwanMapFunction(func_bytes)
        map_fn.open(None)

        result = map_fn.map('{"foo": "bar"}')
        self.assertEqual(json.loads(result), {"foo": "BAR"})

    def test_map_function_returns_none(self):
        """Test map function that filters events."""
        import cloudpickle
        from bspump.spark.operators import BitSwanMapFunction

        def filter_fn(event):
            if b"skip" in event:
                return None
            return event

        func_bytes = cloudpickle.dumps(filter_fn)
        map_fn = BitSwanMapFunction(func_bytes)
        map_fn.open(None)

        # Should return None for filtered event
        result = map_fn.map("skip this")
        self.assertIsNone(result)

        # Should pass through normal event
        result = map_fn.map("keep this")
        self.assertEqual(result, "keep this")


class TestRuntimeDetection(unittest.TestCase):
    """Tests for runtime detection."""

    def test_detect_spark_runtime(self):
        """Test detection with BITSWAN_RUNTIME=spark."""
        from bspump.spark.runtime import detect_runtime

        original = os.environ.get("BITSWAN_RUNTIME")
        try:
            os.environ["BITSWAN_RUNTIME"] = "spark"
            self.assertEqual(detect_runtime(), "spark")
        finally:
            if original:
                os.environ["BITSWAN_RUNTIME"] = original
            else:
                os.environ.pop("BITSWAN_RUNTIME", None)

    def test_detect_bspump_runtime(self):
        """Test detection with BITSWAN_RUNTIME=bspump."""
        from bspump.spark.runtime import detect_runtime

        original = os.environ.get("BITSWAN_RUNTIME")
        try:
            os.environ["BITSWAN_RUNTIME"] = "bspump"
            self.assertEqual(detect_runtime(), "bspump")
        finally:
            if original:
                os.environ["BITSWAN_RUNTIME"] = original
            else:
                os.environ.pop("BITSWAN_RUNTIME", None)


class TestKafkaSinkTrigger(unittest.TestCase):
    """Tests for Kafka sink trigger configuration."""

    def test_trigger_once(self):
        """Test 'once' trigger mode."""
        from bspump.spark.kafka import KafkaSinkAdapter

        adapter = KafkaSinkAdapter()
        trigger = adapter._get_trigger({"trigger": "once"})
        self.assertEqual(trigger, {"once": True})

    def test_trigger_available_now(self):
        """Test 'available_now' trigger mode."""
        from bspump.spark.kafka import KafkaSinkAdapter

        adapter = KafkaSinkAdapter()
        trigger = adapter._get_trigger({"trigger": "available_now"})
        self.assertEqual(trigger, {"availableNow": True})

    def test_trigger_processing_time(self):
        """Test processing time trigger mode."""
        from bspump.spark.kafka import KafkaSinkAdapter

        adapter = KafkaSinkAdapter()
        trigger = adapter._get_trigger({"trigger": "5 seconds"})
        self.assertEqual(trigger, {"processingTime": "5 seconds"})

    def test_trigger_default(self):
        """Test default trigger mode."""
        from bspump.spark.kafka import KafkaSinkAdapter

        adapter = KafkaSinkAdapter()
        trigger = adapter._get_trigger({})
        self.assertEqual(trigger, {"processingTime": "1 second"})


if __name__ == "__main__":
    unittest.main()
