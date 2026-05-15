Elasticsearch Integration
=========================

BSPump provides Elasticsearch integration through ``bspump.elasticsearch``.

Installation
------------

.. code-block:: bash

    pip install elasticsearch[async]

Components
----------

- **ElasticSearchConnection**: Shared connection to Elasticsearch
- **ElasticSearchSource**: Reads documents from Elasticsearch
- **ElasticSearchSink**: Writes documents to Elasticsearch

ElasticSearchConnection
-----------------------

.. code-block:: python

    import bspump.elasticsearch

    connection = bspump.elasticsearch.ElasticSearchConnection(
        app, "ElasticSearchConnection"
    )

Configuration:

.. code-block:: ini

    [connection:ElasticSearchConnection]
    url=http://localhost:9200

    # Authentication (optional)
    # url=https://user:password@localhost:9200

    # Multiple nodes
    # url=http://node1:9200,http://node2:9200,http://node3:9200

ElasticSearchSink
-----------------

Index documents to Elasticsearch.

.. code-block:: python

    import bspump.elasticsearch

    sink = bspump.elasticsearch.ElasticSearchSink(
        app, pipeline,
        connection="ElasticSearchConnection"
    )

Configuration:

.. code-block:: ini

    [pipeline:MyPipeline:ElasticSearchSink]
    index=events
    # Time-based index pattern (optional)
    # index=events-%Y-%m-%d
    # Bulk settings
    bulk_size=500
    bulk_timeout=5.0

ElasticSearchSource
-------------------

Query documents from Elasticsearch.

.. code-block:: python

    import bspump.elasticsearch

    source = bspump.elasticsearch.ElasticSearchSource(
        app, pipeline,
        connection="ElasticSearchConnection"
    )

Configuration:

.. code-block:: ini

    [pipeline:MyPipeline:ElasticSearchSource]
    index=events
    query={"match_all": {}}
    scroll=5m
    size=1000

Complete Example
----------------

.. code-block:: python

    from bspump.jupyter import *
    import bspump.elasticsearch
    import bspump.kafka
    import json

    @register_connection
    def es_connection(app):
        return bspump.elasticsearch.ElasticSearchConnection(
            app, "ElasticSearchConnection"
        )

    @register_connection
    def kafka_connection(app):
        return bspump.kafka.KafkaConnection(app, "KafkaConnection")

    auto_pipeline(
        source=lambda app, pipeline: bspump.kafka.KafkaSource(
            app, pipeline, connection="KafkaConnection"
        ),
        sink=lambda app, pipeline: bspump.elasticsearch.ElasticSearchSink(
            app, pipeline, connection="ElasticSearchConnection"
        ),
        name="KafkaToElasticPipeline",
    )

    # Prepare document for indexing
    data = json.loads(event.decode("utf-8"))
    event = {
        "_id": data.get("id"),  # Document ID
        "@timestamp": datetime.now().isoformat(),
        **data
    }

Time-Based Indices
------------------

Create daily indices for time-series data:

.. code-block:: ini

    [pipeline:MyPipeline:ElasticSearchSink]
    index=logs-%Y-%m-%d

The index name is formatted with the current date.

Dynamic Index Routing
---------------------

Route events to different indices:

.. code-block:: python

    class IndexRouter(bspump.Processor):
        def process(self, context, event):
            event_type = event.get("type", "default")
            context["elasticsearch_index"] = f"events-{event_type}"
            return event

Bulk Operations
---------------

Configure bulk indexing for performance:

.. code-block:: ini

    [pipeline:MyPipeline:ElasticSearchSink]
    index=events
    bulk_size=1000      # Documents per bulk request
    bulk_timeout=10.0   # Timeout for bulk operations

Configuration Reference
-----------------------

**Connection Options**

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Description
   * - url
     - http://localhost:9200
     - Elasticsearch URL(s)

**Sink Options**

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Description
   * - index
     - (required)
     - Index name or pattern
   * - bulk_size
     - 500
     - Documents per bulk request
   * - bulk_timeout
     - 5.0
     - Bulk timeout in seconds

**Source Options**

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Description
   * - index
     - (required)
     - Index to query
   * - query
     - {"match_all": {}}
     - Elasticsearch query DSL
   * - scroll
     - 5m
     - Scroll timeout
   * - size
     - 1000
     - Documents per scroll request
