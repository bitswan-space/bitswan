bspump.mongodb
==============

MongoDB database integration for BSPump.

.. automodule:: bspump.mongodb
   :members:
   :undoc-members:
   :show-inheritance:

MongoDBConnection
-----------------

Connection to MongoDB.

.. code-block:: python

    import bspump.mongodb

    connection = bspump.mongodb.MongoDBConnection(app, "MongoDBConnection")

**Configuration:**

.. code-block:: ini

    [connection:MongoDBConnection]
    uri=mongodb://localhost:27017
    database=mydb

**Options:**

- ``uri`` - MongoDB connection URI
- ``database`` - Default database name

**URI Examples:**

.. code-block:: ini

    # Local
    uri=mongodb://localhost:27017

    # With authentication
    uri=mongodb://user:password@localhost:27017/mydb?authSource=admin

    # Replica set
    uri=mongodb://host1:27017,host2:27017,host3:27017/mydb?replicaSet=rs0

MongoDBSource
-------------

Reads documents from MongoDB.

.. code-block:: python

    source = bspump.mongodb.MongoDBSource(
        app, pipeline,
        connection="MongoDBConnection"
    )

**Configuration:**

.. code-block:: ini

    [pipeline:MyPipeline:MongoDBSource]
    collection=events
    query={"status": "pending"}
    batch_size=100

MongoDBSink
-----------

Writes documents to MongoDB.

.. code-block:: python

    sink = bspump.mongodb.MongoDBSink(
        app, pipeline,
        connection="MongoDBConnection"
    )

**Configuration:**

.. code-block:: ini

    [pipeline:MyPipeline:MongoDBSink]
    collection=processed_events
    mode=insert

**Modes:**

- ``insert`` - Insert new documents
- ``upsert`` - Update or insert
- ``replace`` - Replace existing documents

MongoDBLookup
-------------

Lookup table backed by MongoDB.

.. code-block:: python

    lookup = bspump.mongodb.MongoDBLookup(
        app, "ProductLookup",
        connection="MongoDBConnection",
        config={
            "collection": "products",
            "key": "product_id"
        }
    )

Upsert Example
--------------

.. code-block:: python

    class UpsertProcessor(bspump.Processor):
        def process(self, context, event):
            # Set upsert key
            context["mongodb_upsert_key"] = {"_id": event["_id"]}
            return event

Example Pipeline
----------------

.. code-block:: python

    import bspump
    import bspump.mongodb
    import bspump.kafka

    class KafkaToMongoPipeline(bspump.Pipeline):
        def __init__(self, app, pipeline_id):
            super().__init__(app, pipeline_id)
            self.build(
                bspump.kafka.KafkaSource(app, self, connection="KafkaConnection"),
                DocumentProcessor(app, self),
                bspump.mongodb.MongoDBSink(app, self, connection="MongoDBConnection"),
            )
