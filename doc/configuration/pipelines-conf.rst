pipelines.conf
==============

The ``pipelines.conf`` file is the primary configuration file for BSPump
applications. It configures connections, pipelines, and components.

File Location
-------------

BSPump looks for ``pipelines.conf`` in:

1. Current working directory
2. Path specified via ``-c`` command-line argument
3. ``/etc/bspump/pipelines.conf``

Basic Structure
---------------

.. code-block:: ini

    # Connection configuration
    [connection:KafkaConnection]
    bootstrap_servers=kafka:9092

    # Pipeline configuration
    [pipeline:MyPipeline]
    max_concurrent=10

    # Component configuration
    [pipeline:MyPipeline:KafkaSource]
    topic=input-events

    [pipeline:MyPipeline:KafkaSink]
    topic=output-events

Connection Configuration
------------------------

Connections are configured with ``[connection:ID]`` sections.

**Kafka**

.. code-block:: ini

    [connection:KafkaConnection]
    bootstrap_servers=kafka1:9092,kafka2:9092
    security_protocol=PLAINTEXT
    group_id=my-consumer-group

    # SSL
    # security_protocol=SSL
    # ssl_cafile=/path/to/ca.pem
    # ssl_certfile=/path/to/cert.pem
    # ssl_keyfile=/path/to/key.pem

    # SASL
    # security_protocol=SASL_SSL
    # sasl_mechanism=PLAIN
    # sasl_plain_username=${KAFKA_USER}
    # sasl_plain_password=${KAFKA_PASSWORD}

**PostgreSQL**

.. code-block:: ini

    [connection:PostgreSQLConnection]
    host=localhost
    port=5432
    database=mydb
    user=postgres
    password=${POSTGRES_PASSWORD}
    min_size=1
    max_size=10

**MongoDB**

.. code-block:: ini

    [connection:MongoDBConnection]
    uri=mongodb://localhost:27017
    database=mydb

**Elasticsearch**

.. code-block:: ini

    [connection:ElasticSearchConnection]
    url=http://localhost:9200

**MQTT**

.. code-block:: ini

    [connection:MQTTConnection]
    host=localhost
    port=1883
    username=${MQTT_USER}
    password=${MQTT_PASSWORD}

Pipeline Configuration
----------------------

Pipelines are configured with ``[pipeline:Name]`` sections.

.. code-block:: ini

    [pipeline:ProcessingPipeline]
    # Maximum concurrent events
    max_concurrent=100

    # Pipeline timeout in seconds
    timeout=60

Source Configuration
--------------------

Sources are configured with ``[pipeline:Name:SourceId]`` sections.

**Kafka Source**

.. code-block:: ini

    [pipeline:MyPipeline:KafkaSource]
    topic=input-events
    # Or multiple topics
    # topics=topic1,topic2

    auto_offset_reset=earliest
    max_poll_records=500
    max_poll_interval_ms=300000

**WebHook Source**

.. code-block:: ini

    [pipeline:MyPipeline:WebHookSource]
    path=/webhook
    port=8080
    host=0.0.0.0

**File Source**

.. code-block:: ini

    [pipeline:MyPipeline:FileLineSource]
    path=/data/input.txt
    encoding=utf-8

Processor Configuration
-----------------------

Processors are configured with ``[pipeline:Name:ProcessorId]`` sections.

.. code-block:: ini

    [pipeline:MyPipeline:FilterProcessor]
    threshold=100
    enabled=true

Sink Configuration
------------------

Sinks are configured with ``[pipeline:Name:SinkId]`` sections.

**Kafka Sink**

.. code-block:: ini

    [pipeline:MyPipeline:KafkaSink]
    topic=output-events
    acks=all
    batch_size=16384
    linger_ms=0

**Elasticsearch Sink**

.. code-block:: ini

    [pipeline:MyPipeline:ElasticSearchSink]
    index=events-%Y-%m-%d
    bulk_size=500
    bulk_timeout=5.0

**PostgreSQL Sink**

.. code-block:: ini

    [pipeline:MyPipeline:PostgreSQLSink]
    table=events
    columns=id,data,created_at

**File Sink**

.. code-block:: ini

    [pipeline:MyPipeline:FileLineSink]
    path=/data/output.txt
    mode=a

Lookup Configuration
--------------------

Lookups are configured with ``[lookup:ID]`` sections.

.. code-block:: ini

    [lookup:UserLookup]
    path=/data/users.json
    reload_interval=3600

Environment Variables
---------------------

Reference environment variables with ``${VAR}`` syntax:

.. code-block:: ini

    [connection:PostgreSQLConnection]
    password=${POSTGRES_PASSWORD}

With defaults:

.. code-block:: ini

    [connection:PostgreSQLConnection]
    host=${POSTGRES_HOST:-localhost}
    port=${POSTGRES_PORT:-5432}

Complete Example
----------------

.. code-block:: ini

    # pipelines.conf

    # Kafka connection
    [connection:KafkaConnection]
    bootstrap_servers=${KAFKA_BOOTSTRAP_SERVERS:-kafka:9092}
    group_id=processing-group

    # PostgreSQL connection
    [connection:PostgreSQLConnection]
    host=${POSTGRES_HOST:-localhost}
    port=5432
    database=events
    user=postgres
    password=${POSTGRES_PASSWORD}

    # Main processing pipeline
    [pipeline:ProcessingPipeline]
    max_concurrent=100

    [pipeline:ProcessingPipeline:KafkaSource]
    topic=raw-events
    auto_offset_reset=earliest

    [pipeline:ProcessingPipeline:KafkaSink]
    topic=processed-events
    acks=all

    # Archival pipeline
    [pipeline:ArchivalPipeline]

    [pipeline:ArchivalPipeline:KafkaSource]
    topic=processed-events

    [pipeline:ArchivalPipeline:ElasticSearchSink]
    index=events-%Y-%m-%d
    bulk_size=1000

    # User lookup
    [lookup:UserLookup]
    path=/data/users.json

Best Practices
--------------

1. **Use environment variables for secrets**: Never commit passwords
2. **Provide sensible defaults**: Use ``${VAR:-default}`` syntax
3. **Separate concerns**: Use multiple config files if needed
4. **Document configuration**: Add comments explaining options
5. **Validate on startup**: Check required configuration exists
