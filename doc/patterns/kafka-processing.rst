Kafka Processing Pipeline
=========================

This pattern demonstrates consuming from Kafka, processing events, and
producing to another Kafka topic.

Use Cases
---------

- Data transformation and enrichment
- Filtering and routing events
- Stream processing and aggregation
- Event-driven microservices

Architecture
------------

.. code-block:: text

    Kafka Input Topic
          │
          ▼
    ┌───────────────┐
    │  KafkaSource  │
    └───────────────┘
          │
          ▼
    ┌───────────────┐
    │  Processors   │ Transform, filter, enrich
    └───────────────┘
          │
          ▼
    ┌───────────────┐
    │  KafkaSink    │
    └───────────────┘
          │
          ▼
    Kafka Output Topic

Jupyter Implementation
----------------------

.. code-block:: python

    from bspump.jupyter import *
    import bspump.kafka

    @register_connection
    def kafka_connection(app):
        return bspump.kafka.KafkaConnection(app, "KafkaConnection")

    auto_pipeline(
        source=lambda app, pipeline: bspump.kafka.KafkaSource(
            app, pipeline, connection="KafkaConnection"
        ),
        sink=lambda app, pipeline: bspump.kafka.KafkaSink(
            app, pipeline, connection="KafkaConnection"
        ),
        name="ProcessingPipeline",
    )

Process events in notebook cells:

.. code-block:: python

    import json

    # Parse JSON event
    event = json.loads(event.decode("utf-8"))

.. code-block:: python

    # Transform the event
    event["processed"] = True
    event["processed_at"] = datetime.now().isoformat()

    # Filter: drop events missing required fields
    if "user_id" not in event:
        event = None

.. code-block:: python

    # Serialize back to JSON bytes
    if event:
        event = json.dumps(event).encode("utf-8")

Standalone Application
----------------------

.. code-block:: python

    import bspump
    import bspump.kafka
    import json
    from datetime import datetime

    class JsonParser(bspump.Processor):
        def process(self, context, event):
            try:
                return json.loads(event.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return None

    class TransformProcessor(bspump.Processor):
        def process(self, context, event):
            event["processed"] = True
            event["processed_at"] = datetime.now().isoformat()
            return event

    class FilterProcessor(bspump.Processor):
        def process(self, context, event):
            if "user_id" not in event:
                return None
            return event

    class JsonSerializer(bspump.Processor):
        def process(self, context, event):
            return json.dumps(event).encode("utf-8")

    class KafkaProcessingPipeline(bspump.Pipeline):
        def __init__(self, app, pipeline_id):
            super().__init__(app, pipeline_id)
            self.build(
                bspump.kafka.KafkaSource(app, self, connection="KafkaConnection"),
                JsonParser(app, self),
                TransformProcessor(app, self),
                FilterProcessor(app, self),
                JsonSerializer(app, self),
                bspump.kafka.KafkaSink(app, self, connection="KafkaConnection"),
            )

    if __name__ == "__main__":
        app = bspump.BSPumpApplication()
        svc = app.get_service("bspump.PumpService")

        svc.add_connection(
            bspump.kafka.KafkaConnection(app, "KafkaConnection")
        )
        svc.add_pipeline(KafkaProcessingPipeline(app, "KafkaProcessingPipeline"))

        app.run()

Configuration
-------------

.. code-block:: ini

    [connection:KafkaConnection]
    bootstrap_servers=kafka:9092
    group_id=my-consumer-group

    [pipeline:KafkaProcessingPipeline:KafkaSource]
    topic=input-topic
    auto_offset_reset=earliest

    [pipeline:KafkaProcessingPipeline:KafkaSink]
    topic=output-topic

Multiple Output Topics
----------------------

Route events to different topics based on content:

.. code-block:: python

    class RoutingProcessor(bspump.Processor):
        def process(self, context, event):
            # Set the output topic based on event type
            event_type = event.get("type", "default")
            context["kafka_topic"] = f"events-{event_type}"
            return event

Consumer Groups
---------------

Multiple instances of the same pipeline share a consumer group for
horizontal scaling:

.. code-block:: ini

    [connection:KafkaConnection]
    group_id=processing-group

Kafka automatically distributes partitions among group members.

Best Practices
--------------

1. **Use consumer groups**: Enable horizontal scaling
2. **Commit offsets after processing**: Ensure at-least-once delivery
3. **Handle poison messages**: Use dead-letter queues for unprocessable events
4. **Monitor lag**: Track consumer lag for performance monitoring
5. **Design idempotent processors**: Handle duplicate deliveries gracefully
