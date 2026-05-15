Webhook to Kafka
================

This pattern demonstrates receiving HTTP webhooks and forwarding them to Kafka
for reliable, scalable event processing.

Use Cases
---------

- Receiving payment notifications from payment providers
- Ingesting alerts from monitoring systems
- Collecting data from third-party APIs with webhook support
- Building event-driven integrations

Architecture
------------

.. code-block:: text

    External Service
          │
          ▼
    ┌───────────────┐
    │ WebHookSource │ HTTP POST /webhook
    └───────────────┘
          │
          ▼
    ┌───────────────┐
    │  Processors   │ Validate, transform
    └───────────────┘
          │
          ▼
    ┌───────────────┐
    │  KafkaSink    │ → Kafka topic
    └───────────────┘

Jupyter Implementation
----------------------

.. code-block:: python

    from bspump.jupyter import *
    import bspump.kafka
    import bspump.http.web

    @register_connection
    def kafka_connection(app):
        return bspump.kafka.KafkaConnection(app, "KafkaConnection")

    auto_pipeline(
        source=lambda app, pipeline: bspump.http.web.WebHookSource(
            app, pipeline,
            config={"port": 8080, "path": "/webhook"}
        ),
        sink=lambda app, pipeline: bspump.kafka.KafkaSink(
            app, pipeline, connection="KafkaConnection"
        ),
        name="Webhook2KafkaPipeline",
    )

In subsequent cells, process the incoming webhook data:

.. code-block:: python

    import json

    # Parse and validate the webhook payload
    try:
        data = json.loads(event.decode("utf-8"))
    except json.JSONDecodeError:
        event = None  # Drop invalid JSON

.. code-block:: python

    # Add metadata
    if event:
        event["received_at"] = datetime.now().isoformat()
        event["source"] = "webhook"
        event = json.dumps(event).encode("utf-8")

Standalone Application
----------------------

.. code-block:: python

    import bspump
    import bspump.kafka
    import bspump.http.web
    import bspump.common
    import json

    class ValidateProcessor(bspump.Processor):
        def process(self, context, event):
            try:
                data = json.loads(event.decode("utf-8"))
                return data
            except (json.JSONDecodeError, UnicodeDecodeError):
                return None  # Drop invalid events

    class EnrichProcessor(bspump.Processor):
        def process(self, context, event):
            event["received_at"] = datetime.now().isoformat()
            event["source"] = "webhook"
            return json.dumps(event).encode("utf-8")

    class WebhookToKafkaPipeline(bspump.Pipeline):
        def __init__(self, app, pipeline_id):
            super().__init__(app, pipeline_id)
            self.build(
                bspump.http.web.WebHookSource(app, self, config={
                    "port": 8080,
                    "path": "/webhook"
                }),
                ValidateProcessor(app, self),
                EnrichProcessor(app, self),
                bspump.kafka.KafkaSink(app, self, connection="KafkaConnection"),
            )

    if __name__ == "__main__":
        app = bspump.BSPumpApplication()
        svc = app.get_service("bspump.PumpService")

        svc.add_connection(
            bspump.kafka.KafkaConnection(app, "KafkaConnection")
        )
        svc.add_pipeline(WebhookToKafkaPipeline(app, "WebhookToKafkaPipeline"))

        app.run()

Configuration
-------------

Configure via ``pipelines.conf``:

.. code-block:: ini

    [connection:KafkaConnection]
    bootstrap_servers=kafka:9092

    [pipeline:WebhookToKafkaPipeline:WebHookSource]
    port=8080
    path=/webhook

    [pipeline:WebhookToKafkaPipeline:KafkaSink]
    topic=incoming-webhooks

Best Practices
--------------

1. **Validate incoming data**: Always validate webhook payloads before processing
2. **Add metadata**: Include timestamps and source information
3. **Use Kafka for durability**: Kafka provides replay and failure recovery
4. **Implement authentication**: Secure webhook endpoints with signatures/tokens
5. **Handle duplicates**: Design downstream consumers to be idempotent
