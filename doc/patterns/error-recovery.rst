Error Recovery
==============

This pattern demonstrates using Kafka for restart safety and building
resilient pipelines that recover from failures.

Use Cases
---------

- Guaranteed message delivery
- Pipeline restart without data loss
- Dead-letter queue for failed events
- Retry mechanisms for transient failures

Kafka for Restart Safety
------------------------

Kafka provides natural recovery through consumer offsets:

.. code-block:: text

    ┌─────────────┐
    │ KafkaSource │ ← Reads from last committed offset
    └─────────────┘
          │
          ▼
    ┌─────────────┐
    │ Processors  │ ← If crash here, message not committed
    └─────────────┘
          │
          ▼
    ┌─────────────┐
    │ KafkaSink   │ ← Commits offset after successful write
    └─────────────┘

On restart, processing resumes from the last committed offset.

Implementation
--------------

.. code-block:: python

    from bspump.jupyter import *
    import bspump.kafka

    @register_connection
    def kafka_connection(app):
        return bspump.kafka.KafkaConnection(app, "KafkaConnection")

    auto_pipeline(
        source=lambda app, pipeline: bspump.kafka.KafkaSource(
            app, pipeline,
            connection="KafkaConnection"
        ),
        sink=lambda app, pipeline: bspump.kafka.KafkaSink(
            app, pipeline,
            connection="KafkaConnection"
        ),
        name="RecoverablePipeline",
    )

Configuration for reliability:

.. code-block:: ini

    [connection:KafkaConnection]
    bootstrap_servers=kafka:9092
    group_id=reliable-consumer
    enable_auto_commit=false

    [pipeline:RecoverablePipeline:KafkaSink]
    topic=processed-events
    acks=all

Dead-Letter Queue Pattern
-------------------------

Route failed events to a separate topic:

.. code-block:: python

    import bspump
    import bspump.kafka
    import json

    class SafeProcessor(bspump.Processor):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)
            self.dlq_topic = "dead-letter-queue"

        def process(self, context, event):
            try:
                # Attempt processing
                data = json.loads(event.decode("utf-8"))
                data["processed"] = True
                return json.dumps(data).encode("utf-8")
            except Exception as e:
                # Send to dead-letter queue
                context["kafka_topic"] = self.dlq_topic
                context["error"] = str(e)
                return event

Retry with Exponential Backoff
------------------------------

Implement retry logic for transient failures:

.. code-block:: python

    import bspump
    import asyncio

    class RetryProcessor(bspump.Processor):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)
            self.max_retries = 3
            self.base_delay = 1.0

        async def process(self, context, event):
            for attempt in range(self.max_retries):
                try:
                    result = await self.risky_operation(event)
                    return result
                except TransientError as e:
                    if attempt < self.max_retries - 1:
                        delay = self.base_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
                    else:
                        raise

        async def risky_operation(self, event):
            # Operation that might fail
            pass

Circuit Breaker Pattern
-----------------------

Prevent cascading failures:

.. code-block:: python

    import bspump
    import time

    class CircuitBreakerProcessor(bspump.Processor):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)
            self.failure_count = 0
            self.failure_threshold = 5
            self.reset_timeout = 60
            self.last_failure_time = 0
            self.circuit_open = False

        def process(self, context, event):
            if self.circuit_open:
                if time.time() - self.last_failure_time > self.reset_timeout:
                    self.circuit_open = False
                    self.failure_count = 0
                else:
                    # Circuit is open, skip processing
                    context["circuit_breaker_triggered"] = True
                    return event

            try:
                result = self.do_processing(event)
                self.failure_count = 0
                return result
            except Exception:
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.failure_count >= self.failure_threshold:
                    self.circuit_open = True
                raise

Graceful Shutdown
-----------------

Handle shutdown signals properly:

.. code-block:: python

    import bspump
    import signal

    app = bspump.BSPumpApplication()

    def shutdown_handler(signum, frame):
        # Graceful shutdown
        app.stop()

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    app.run()

Configuration
-------------

.. code-block:: ini

    [connection:KafkaConnection]
    bootstrap_servers=kafka:9092
    group_id=reliable-consumer
    # Disable auto-commit for manual control
    enable_auto_commit=false
    # Ensure durability
    acks=all

    [pipeline:RecoverablePipeline:KafkaSource]
    topic=input-events
    # Start from earliest on new consumer group
    auto_offset_reset=earliest

    [pipeline:RecoverablePipeline:KafkaSink]
    topic=processed-events

Best Practices
--------------

1. **Use Kafka for persistence**: Leverage Kafka's replay capability
2. **Disable auto-commit**: Commit only after successful processing
3. **Implement dead-letter queues**: Don't lose failed events
4. **Design idempotent operations**: Handle reprocessing gracefully
5. **Monitor error rates**: Alert on elevated failure counts
6. **Test failure scenarios**: Verify recovery behavior
