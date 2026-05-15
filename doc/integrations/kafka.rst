Kafka Integration
=================

BSPump provides comprehensive Kafka integration through ``bspump.kafka``.

Installation
------------

.. code-block:: bash

    pip install aiokafka

Components
----------

- **KafkaConnection**: Shared connection to Kafka cluster
- **KafkaSource**: Consumes messages from Kafka topics
- **KafkaSink**: Produces messages to Kafka topics

KafkaConnection
---------------

.. code-block:: python

    import bspump.kafka

    connection = bspump.kafka.KafkaConnection(app, "KafkaConnection")

Configuration:

.. code-block:: ini

    [connection:KafkaConnection]
    bootstrap_servers=kafka1:9092,kafka2:9092,kafka3:9092
    security_protocol=PLAINTEXT
    group_id=my-consumer-group

    # SSL configuration (optional)
    # security_protocol=SSL
    # ssl_cafile=/path/to/ca.pem
    # ssl_certfile=/path/to/cert.pem
    # ssl_keyfile=/path/to/key.pem

    # SASL configuration (optional)
    # security_protocol=SASL_SSL
    # sasl_mechanism=PLAIN
    # sasl_plain_username=user
    # sasl_plain_password=${KAFKA_PASSWORD}

KafkaSource
-----------

Consumes messages from one or more Kafka topics.

.. code-block:: python

    import bspump.kafka

    source = bspump.kafka.KafkaSource(
        app, pipeline,
        connection="KafkaConnection"
    )

Configuration:

.. code-block:: ini

    [pipeline:MyPipeline:KafkaSource]
    topic=my-topic
    # Or multiple topics
    # topics=topic1,topic2,topic3

    # Consumer settings
    auto_offset_reset=earliest
    # Options: earliest, latest

    # Batch settings
    max_poll_records=500
    max_poll_interval_ms=300000

KafkaSink
---------

Produces messages to a Kafka topic.

.. code-block:: python

    import bspump.kafka

    sink = bspump.kafka.KafkaSink(
        app, pipeline,
        connection="KafkaConnection"
    )

Configuration:

.. code-block:: ini

    [pipeline:MyPipeline:KafkaSink]
    topic=output-topic

    # Producer settings
    acks=all
    # Options: 0, 1, all

    # Batching
    batch_size=16384
    linger_ms=0

Dynamic Topic Routing
---------------------

Set the topic dynamically in a processor:

.. code-block:: python

    class RouterProcessor(bspump.Processor):
        def process(self, context, event):
            event_type = event.get("type", "default")
            context["kafka_topic"] = f"events-{event_type}"
            return event

Message Keys
------------

Set a message key for partitioning:

.. code-block:: python

    class KeyProcessor(bspump.Processor):
        def process(self, context, event):
            # Events with the same key go to the same partition
            context["kafka_key"] = event.get("user_id", "").encode()
            return event

Complete Example
----------------

.. code-block:: python

    from bspump.jupyter import *
    import bspump.kafka
    import json

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
        name="KafkaPipeline",
    )

    # Process events
    event = json.loads(event.decode("utf-8"))
    event["processed"] = True
    event = json.dumps(event).encode("utf-8")

Configuration Reference
-----------------------

**Connection Options**

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Description
   * - bootstrap_servers
     - localhost:9092
     - Comma-separated list of brokers
   * - security_protocol
     - PLAINTEXT
     - PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL
   * - group_id
     - bspump
     - Consumer group ID

**Source Options**

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Description
   * - topic
     - (required)
     - Topic to consume from
   * - auto_offset_reset
     - latest
     - Where to start: earliest or latest
   * - max_poll_records
     - 500
     - Max records per poll

**Sink Options**

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Description
   * - topic
     - (required)
     - Topic to produce to
   * - acks
     - 1
     - Acknowledgment level: 0, 1, or all
