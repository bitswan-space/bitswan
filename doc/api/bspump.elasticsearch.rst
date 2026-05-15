bspump.elasticsearch
====================

Elasticsearch integration for BSPump.

.. automodule:: bspump.elasticsearch
   :members:
   :undoc-members:
   :show-inheritance:

ElasticSearchConnection
-----------------------

Connection to Elasticsearch cluster.

.. code-block:: python

    import bspump.elasticsearch

    connection = bspump.elasticsearch.ElasticSearchConnection(
        app, "ElasticSearchConnection"
    )

**Configuration:**

.. code-block:: ini

    [connection:ElasticSearchConnection]
    url=http://localhost:9200

**Options:**

- ``url`` - Elasticsearch URL(s), comma-separated for multiple nodes

**URL Examples:**

.. code-block:: ini

    # Single node
    url=http://localhost:9200

    # With authentication
    url=https://user:password@localhost:9200

    # Multiple nodes
    url=http://node1:9200,http://node2:9200,http://node3:9200

ElasticSearchSource
-------------------

Queries documents from Elasticsearch.

.. code-block:: python

    source = bspump.elasticsearch.ElasticSearchSource(
        app, pipeline,
        connection="ElasticSearchConnection"
    )

**Configuration:**

.. code-block:: ini

    [pipeline:MyPipeline:ElasticSearchSource]
    index=events
    query={"match_all": {}}
    scroll=5m
    size=1000

ElasticSearchSink
-----------------

Indexes documents to Elasticsearch.

.. code-block:: python

    sink = bspump.elasticsearch.ElasticSearchSink(
        app, pipeline,
        connection="ElasticSearchConnection"
    )

**Configuration:**

.. code-block:: ini

    [pipeline:MyPipeline:ElasticSearchSink]
    index=events
    bulk_size=500
    bulk_timeout=5.0

**Time-Based Indices:**

.. code-block:: ini

    index=events-%Y-%m-%d

Dynamic Index Routing
---------------------

.. code-block:: python

    class IndexRouter(bspump.Processor):
        def process(self, context, event):
            context["elasticsearch_index"] = f"events-{event['type']}"
            return event

Document ID
-----------

Set the document ID:

.. code-block:: python

    class DocumentProcessor(bspump.Processor):
        def process(self, context, event):
            # Event dict can include _id for document ID
            event["_id"] = event.pop("id")
            return event

Example Pipeline
----------------

.. code-block:: python

    import bspump
    import bspump.elasticsearch
    import bspump.kafka

    class KafkaToElasticPipeline(bspump.Pipeline):
        def __init__(self, app, pipeline_id):
            super().__init__(app, pipeline_id)
            self.build(
                bspump.kafka.KafkaSource(app, self, connection="KafkaConnection"),
                TimestampProcessor(app, self),
                bspump.elasticsearch.ElasticSearchSink(
                    app, self, connection="ElasticSearchConnection"
                ),
            )
