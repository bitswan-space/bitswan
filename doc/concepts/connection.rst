Connection
==========

Connections are shared, reusable connections to external systems. They manage
connection pooling, reconnection, and configuration for databases, message
queues, and other services.

Why Use Connections?
--------------------

- **Reusability**: Share a single connection across multiple pipelines
- **Resource Efficiency**: Connection pooling reduces overhead
- **Centralized Configuration**: Configure once, use everywhere
- **Lifecycle Management**: Automatic connection and reconnection handling

Creating a Connection
---------------------

Connections are registered with the application:

.. code-block:: python

    import bspump
    import bspump.kafka

    app = bspump.BSPumpApplication()
    svc = app.get_service("bspump.PumpService")

    # Create and register a Kafka connection
    svc.add_connection(
        bspump.kafka.KafkaConnection(app, "KafkaConnection")
    )

Using Connections in Pipelines
------------------------------

Reference connections by their ID:

.. code-block:: python

    class MyPipeline(bspump.Pipeline):
        def __init__(self, app, pipeline_id):
            super().__init__(app, pipeline_id)
            self.build(
                bspump.kafka.KafkaSource(
                    app, self,
                    connection="KafkaConnection"  # Reference by ID
                ),
                bspump.kafka.KafkaSink(
                    app, self,
                    connection="KafkaConnection"  # Same connection
                ),
            )

Jupyter Connection Registration
-------------------------------

In Jupyter notebooks, use the ``@register_connection`` decorator:

.. code-block:: python

    from bspump.jupyter import *
    import bspump.kafka

    @register_connection
    def kafka_connection(app):
        return bspump.kafka.KafkaConnection(app, "KafkaConnection")

Built-in Connections
--------------------

**Kafka**

.. code-block:: python

    import bspump.kafka

    connection = bspump.kafka.KafkaConnection(app, "KafkaConnection")

**PostgreSQL**

.. code-block:: python

    import bspump.postgresql

    connection = bspump.postgresql.PostgreSQLConnection(app, "PostgreSQLConnection")

**MongoDB**

.. code-block:: python

    import bspump.mongodb

    connection = bspump.mongodb.MongoDBConnection(app, "MongoDBConnection")

**Elasticsearch**

.. code-block:: python

    import bspump.elasticsearch

    connection = bspump.elasticsearch.ElasticSearchConnection(app, "ESConnection")

**MQTT**

.. code-block:: python

    import bspump.mqtt

    connection = bspump.mqtt.MQTTConnection(app, "MQTTConnection")

Connection Configuration
------------------------

Connections are configured via the ``pipelines.conf`` file:

.. code-block:: ini

    [connection:KafkaConnection]
    bootstrap_servers=kafka:9092
    security_protocol=PLAINTEXT

    [connection:PostgreSQLConnection]
    host=localhost
    port=5432
    database=mydb
    user=postgres
    password=${POSTGRES_PASSWORD}

Environment variables can be referenced using ``${VAR_NAME}`` syntax.

See :doc:`../configuration/pipelines-conf` for detailed configuration options.

Connection Lifecycle
--------------------

Connections handle their lifecycle automatically:

1. **Initialization**: Connection is created and configured
2. **Connection**: Establishes connection to the external system
3. **Ready**: Connection is available for use
4. **Reconnection**: Automatic reconnection on failure
5. **Shutdown**: Graceful disconnection on application stop

Custom Connections
------------------

Create custom connections by extending the base class:

.. code-block:: python

    import bspump

    class MyConnection(bspump.Connection):
        def __init__(self, app, connection_id, config=None):
            super().__init__(app, connection_id, config=config)
            self.client = None

        async def connect(self):
            self.client = await create_client(
                host=self.Config.get("host"),
                port=self.Config.getint("port")
            )

        async def disconnect(self):
            if self.client:
                await self.client.close()
