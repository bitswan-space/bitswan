PostgreSQL Integration
======================

BSPump provides PostgreSQL integration through ``bspump.postgresql``.

Installation
------------

.. code-block:: bash

    pip install asyncpg

Components
----------

- **PostgreSQLConnection**: Shared connection pool
- **PostgreSQLSource**: Queries data from PostgreSQL
- **PostgreSQLSink**: Writes data to PostgreSQL
- **PostgreSQLLookup**: Lookup table from PostgreSQL

PostgreSQLConnection
--------------------

.. code-block:: python

    import bspump.postgresql

    connection = bspump.postgresql.PostgreSQLConnection(app, "PostgreSQLConnection")

Configuration:

.. code-block:: ini

    [connection:PostgreSQLConnection]
    host=localhost
    port=5432
    database=mydb
    user=postgres
    password=${POSTGRES_PASSWORD}

    # Connection pool settings
    min_size=1
    max_size=10

PostgreSQLSource
----------------

Query data from PostgreSQL tables.

.. code-block:: python

    import bspump.postgresql

    source = bspump.postgresql.PostgreSQLSource(
        app, pipeline,
        connection="PostgreSQLConnection"
    )

Configuration:

.. code-block:: ini

    [pipeline:MyPipeline:PostgreSQLSource]
    query=SELECT * FROM events WHERE processed = false
    batch_size=100

PostgreSQLSink
--------------

Write events to PostgreSQL.

.. code-block:: python

    import bspump.postgresql

    sink = bspump.postgresql.PostgreSQLSink(
        app, pipeline,
        connection="PostgreSQLConnection"
    )

Configuration:

.. code-block:: ini

    [pipeline:MyPipeline:PostgreSQLSink]
    table=processed_events
    # Columns to insert (optional, defaults to all event keys)
    columns=id,data,created_at

PostgreSQLLookup
----------------

Use PostgreSQL data for event enrichment.

.. code-block:: python

    import bspump.postgresql

    lookup = bspump.postgresql.PostgreSQLLookup(
        app, "UserLookup",
        connection="PostgreSQLConnection",
        config={
            "query": "SELECT id, name, email FROM users",
            "key": "id"
        }
    )

Usage in a processor:

.. code-block:: python

    class EnrichProcessor(bspump.Processor):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)
            svc = app.get_service("bspump.PumpService")
            self.user_lookup = svc.locate_lookup("UserLookup")

        def process(self, context, event):
            user_id = event.get("user_id")
            user = self.user_lookup.get(user_id)
            if user:
                event["user_name"] = user["name"]
            return event

Complete Example
----------------

.. code-block:: python

    from bspump.jupyter import *
    import bspump.postgresql
    import bspump.kafka

    @register_connection
    def pg_connection(app):
        return bspump.postgresql.PostgreSQLConnection(app, "PostgreSQLConnection")

    @register_connection
    def kafka_connection(app):
        return bspump.kafka.KafkaConnection(app, "KafkaConnection")

    auto_pipeline(
        source=lambda app, pipeline: bspump.kafka.KafkaSource(
            app, pipeline, connection="KafkaConnection"
        ),
        sink=lambda app, pipeline: bspump.postgresql.PostgreSQLSink(
            app, pipeline, connection="PostgreSQLConnection"
        ),
        name="KafkaToPostgresPipeline",
    )

    # Transform Kafka message to database row
    import json
    data = json.loads(event.decode("utf-8"))
    event = {
        "id": data["id"],
        "payload": json.dumps(data),
        "created_at": datetime.now()
    }

Raw Query Execution
-------------------

Execute custom queries in processors:

.. code-block:: python

    class QueryProcessor(bspump.Processor):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)
            svc = app.get_service("bspump.PumpService")
            self.connection = svc.locate_connection("PostgreSQLConnection")

        async def process(self, context, event):
            async with self.connection.acquire() as conn:
                result = await conn.fetch(
                    "SELECT * FROM related WHERE parent_id = $1",
                    event["id"]
                )
                event["related"] = [dict(r) for r in result]
            return event

Configuration Reference
-----------------------

**Connection Options**

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Description
   * - host
     - localhost
     - Database host
   * - port
     - 5432
     - Database port
   * - database
     - postgres
     - Database name
   * - user
     - postgres
     - Username
   * - password
     - (empty)
     - Password
   * - min_size
     - 1
     - Minimum pool connections
   * - max_size
     - 10
     - Maximum pool connections
