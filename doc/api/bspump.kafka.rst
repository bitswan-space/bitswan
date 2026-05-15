bspump.kafka
============

Apache Kafka integration for BSPump.

.. automodule:: bspump.kafka
   :members:
   :undoc-members:
   :show-inheritance:

KafkaConnection
---------------

Shared connection to a Kafka cluster.

.. code-block:: python

    import bspump.kafka

    connection = bspump.kafka.KafkaConnection(app, "KafkaConnection")

**Configuration:**

.. code-block:: ini

    [connection:KafkaConnection]
    bootstrap_servers=kafka:9092
    security_protocol=PLAINTEXT
    group_id=my-consumer-group

**Options:**

- ``bootstrap_servers`` - Comma-separated list of brokers
- ``security_protocol`` - PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL
- ``group_id`` - Consumer group ID
- ``ssl_cafile`` - Path to CA certificate
- ``ssl_certfile`` - Path to client certificate
- ``ssl_keyfile`` - Path to client key
- ``sasl_mechanism`` - PLAIN, SCRAM-SHA-256, SCRAM-SHA-512
- ``sasl_plain_username`` - SASL username
- ``sasl_plain_password`` - SASL password

KafkaSource
-----------

Consumes messages from Kafka topics.

.. code-block:: python

    source = bspump.kafka.KafkaSource(
        app, pipeline,
        connection="KafkaConnection"
    )

**Configuration:**

.. code-block:: ini

    [pipeline:MyPipeline:KafkaSource]
    topic=input-topic
    auto_offset_reset=earliest
    max_poll_records=500

**Options:**

- ``topic`` - Single topic to consume
- ``topics`` - Comma-separated list of topics
- ``auto_offset_reset`` - earliest or latest
- ``max_poll_records`` - Maximum records per poll
- ``max_poll_interval_ms`` - Maximum time between polls

**Context Keys:**

The source adds these to the event context:

- ``kafka_topic`` - Source topic
- ``kafka_partition`` - Partition number
- ``kafka_offset`` - Message offset
- ``kafka_key`` - Message key
- ``kafka_timestamp`` - Message timestamp

KafkaSink
---------

Produces messages to Kafka topics.

.. code-block:: python

    sink = bspump.kafka.KafkaSink(
        app, pipeline,
        connection="KafkaConnection"
    )

**Configuration:**

.. code-block:: ini

    [pipeline:MyPipeline:KafkaSink]
    topic=output-topic
    acks=all

**Options:**

- ``topic`` - Target topic
- ``acks`` - Acknowledgment level (0, 1, all)
- ``batch_size`` - Batch size in bytes
- ``linger_ms`` - Time to wait for batch

**Dynamic Topic:**

Set the topic dynamically in a processor:

.. code-block:: python

    def process(self, context, event):
        context["kafka_topic"] = f"events-{event['type']}"
        return event

**Message Key:**

Set the message key for partitioning:

.. code-block:: python

    def process(self, context, event):
        context["kafka_key"] = event["user_id"].encode()
        return event

Example Pipeline
----------------

.. code-block:: python

    import bspump
    import bspump.kafka

    class KafkaProcessingPipeline(bspump.Pipeline):
        def __init__(self, app, pipeline_id):
            super().__init__(app, pipeline_id)
            self.build(
                bspump.kafka.KafkaSource(app, self, connection="KafkaConnection"),
                MyProcessor(app, self),
                bspump.kafka.KafkaSink(app, self, connection="KafkaConnection"),
            )

    app = bspump.BSPumpApplication()
    svc = app.get_service("bspump.PumpService")
    svc.add_connection(bspump.kafka.KafkaConnection(app, "KafkaConnection"))
    svc.add_pipeline(KafkaProcessingPipeline(app, "Pipeline"))
    app.run()
