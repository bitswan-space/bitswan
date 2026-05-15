bspump.postgresql
=================

PostgreSQL database integration for BSPump.

.. automodule:: bspump.postgresql
   :members:
   :undoc-members:
   :show-inheritance:

PostgreSQLConnection
--------------------

Connection pool to PostgreSQL database.

.. code-block:: python

    import bspump.postgresql

    connection = bspump.postgresql.PostgreSQLConnection(app, "PostgreSQLConnection")

**Configuration:**

.. code-block:: ini

    [connection:PostgreSQLConnection]
    host=localhost
    port=5432
    database=mydb
    user=postgres
    password=${POSTGRES_PASSWORD}
    min_size=1
    max_size=10

**Options:**

- ``host`` - Database host
- ``port`` - Database port (default: 5432)
- ``database`` - Database name
- ``user`` - Username
- ``password`` - Password
- ``min_size`` - Minimum pool connections
- ``max_size`` - Maximum pool connections

PostgreSQLSource
----------------

Queries data from PostgreSQL.

.. code-block:: python

    source = bspump.postgresql.PostgreSQLSource(
        app, pipeline,
        connection="PostgreSQLConnection"
    )

**Configuration:**

.. code-block:: ini

    [pipeline:MyPipeline:PostgreSQLSource]
    query=SELECT * FROM events WHERE processed = false
    batch_size=100

PostgreSQLSink
--------------

Writes events to PostgreSQL.

.. code-block:: python

    sink = bspump.postgresql.PostgreSQLSink(
        app, pipeline,
        connection="PostgreSQLConnection"
    )

**Configuration:**

.. code-block:: ini

    [pipeline:MyPipeline:PostgreSQLSink]
    table=events
    columns=id,data,created_at

PostgreSQLLookup
----------------

Lookup table backed by PostgreSQL.

.. code-block:: python

    lookup = bspump.postgresql.PostgreSQLLookup(
        app, "UserLookup",
        connection="PostgreSQLConnection",
        config={
            "query": "SELECT id, name FROM users",
            "key": "id"
        }
    )

Using Connection Directly
-------------------------

Execute custom queries in processors:

.. code-block:: python

    class QueryProcessor(bspump.Processor):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)
            svc = app.get_service("bspump.PumpService")
            self.connection = svc.locate_connection("PostgreSQLConnection")

        async def process(self, context, event):
            async with self.connection.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM related WHERE id = $1",
                    event["id"]
                )
                event["related"] = [dict(r) for r in rows]
            return event

Example Pipeline
----------------

.. code-block:: python

    import bspump
    import bspump.postgresql
    import bspump.kafka

    class KafkaToPostgresPipeline(bspump.Pipeline):
        def __init__(self, app, pipeline_id):
            super().__init__(app, pipeline_id)
            self.build(
                bspump.kafka.KafkaSource(app, self, connection="KafkaConnection"),
                TransformProcessor(app, self),
                bspump.postgresql.PostgreSQLSink(app, self, connection="PostgreSQLConnection"),
            )
