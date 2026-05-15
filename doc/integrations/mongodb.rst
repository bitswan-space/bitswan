MongoDB Integration
===================

BSPump provides MongoDB integration through ``bspump.mongodb``.

Installation
------------

.. code-block:: bash

    pip install motor

Components
----------

- **MongoDBConnection**: Shared connection to MongoDB
- **MongoDBSource**: Reads documents from MongoDB collections
- **MongoDBSink**: Writes documents to MongoDB collections
- **MongoDBLookup**: Lookup table from MongoDB

MongoDBConnection
-----------------

.. code-block:: python

    import bspump.mongodb

    connection = bspump.mongodb.MongoDBConnection(app, "MongoDBConnection")

Configuration:

.. code-block:: ini

    [connection:MongoDBConnection]
    uri=mongodb://localhost:27017
    database=mydb

    # Authentication (optional)
    # uri=mongodb://user:password@localhost:27017/mydb?authSource=admin

    # Replica set (optional)
    # uri=mongodb://host1:27017,host2:27017,host3:27017/mydb?replicaSet=rs0

MongoDBSource
-------------

Read documents from a MongoDB collection.

.. code-block:: python

    import bspump.mongodb

    source = bspump.mongodb.MongoDBSource(
        app, pipeline,
        connection="MongoDBConnection"
    )

Configuration:

.. code-block:: ini

    [pipeline:MyPipeline:MongoDBSource]
    collection=events
    query={"status": "pending"}
    batch_size=100

MongoDBSink
-----------

Write documents to a MongoDB collection.

.. code-block:: python

    import bspump.mongodb

    sink = bspump.mongodb.MongoDBSink(
        app, pipeline,
        connection="MongoDBConnection"
    )

Configuration:

.. code-block:: ini

    [pipeline:MyPipeline:MongoDBSink]
    collection=processed_events
    # Insert mode: insert, upsert, replace
    mode=insert

MongoDBLookup
-------------

Use MongoDB for event enrichment.

.. code-block:: python

    import bspump.mongodb

    lookup = bspump.mongodb.MongoDBLookup(
        app, "ProductLookup",
        connection="MongoDBConnection",
        config={
            "collection": "products",
            "key": "product_id"
        }
    )

Complete Example
----------------

.. code-block:: python

    from bspump.jupyter import *
    import bspump.mongodb
    import bspump.kafka

    @register_connection
    def mongo_connection(app):
        return bspump.mongodb.MongoDBConnection(app, "MongoDBConnection")

    @register_connection
    def kafka_connection(app):
        return bspump.kafka.KafkaConnection(app, "KafkaConnection")

    auto_pipeline(
        source=lambda app, pipeline: bspump.kafka.KafkaSource(
            app, pipeline, connection="KafkaConnection"
        ),
        sink=lambda app, pipeline: bspump.mongodb.MongoDBSink(
            app, pipeline, connection="MongoDBConnection"
        ),
        name="KafkaToMongoPipeline",
    )

    # Transform event to MongoDB document
    import json
    data = json.loads(event.decode("utf-8"))
    event = {
        "_id": data.get("id"),
        "data": data,
        "created_at": datetime.now()
    }

Upsert Operations
-----------------

Update existing documents or insert new ones:

.. code-block:: python

    class UpsertProcessor(bspump.Processor):
        def process(self, context, event):
            # Set upsert key for the sink
            context["mongodb_upsert_key"] = {"_id": event["_id"]}
            return event

Configuration:

.. code-block:: ini

    [pipeline:MyPipeline:MongoDBSink]
    collection=events
    mode=upsert

Aggregation Pipeline
--------------------

Use MongoDB aggregation in a source:

.. code-block:: ini

    [pipeline:MyPipeline:MongoDBSource]
    collection=events
    pipeline=[{"$match": {"status": "active"}}, {"$group": {"_id": "$type", "count": {"$sum": 1}}}]

Configuration Reference
-----------------------

**Connection Options**

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Description
   * - uri
     - mongodb://localhost:27017
     - MongoDB connection URI
   * - database
     - test
     - Default database name

**Sink Options**

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Description
   * - collection
     - (required)
     - Target collection
   * - mode
     - insert
     - insert, upsert, or replace
