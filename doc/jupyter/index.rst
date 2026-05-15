Jupyter Integration
===================

BSPump provides first-class Jupyter notebook integration for building
data pipelines interactively. Notebooks are compiled into production-ready
automations.

.. toctree::
   :maxdepth: 2

   notebook-structure
   auto-pipeline
   testing

Overview
--------

BSPump notebooks have a specific structure:

1. **Before auto_pipeline**: Imports, connections, lookups, helper functions, and test data
2. **The auto_pipeline cell**: Defines the source and sink (always in its own cell)
3. **After auto_pipeline**: Processing logic that runs for each event

.. code-block:: text

    ┌─────────────────────────────────────┐
    │  BEFORE auto_pipeline               │
    │  - Imports                          │
    │  - @register_connection             │
    │  - Helper functions                 │
    │  - Test event data                  │
    └─────────────────────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │  auto_pipeline(...)                 │
    │  - Defines source and sink          │
    │  - Always in its own cell           │
    └─────────────────────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │  AFTER auto_pipeline                │
    │  - Event processing logic           │
    │  - Becomes an async processor       │
    │  - Can use await                    │
    └─────────────────────────────────────┘

When deployed, the cells after ``auto_pipeline`` become a single async
processor in the pipeline. This allows you to:

- Quickly create single-step pipelines
- Interactively test computations with sample data
- Use regular Python without writing processor classes

Quick Start
-----------

Here's a minimal webhook-to-Kafka pipeline:

.. code-block:: python

    # Cell 1: Imports and connection
    from bspump.jupyter import *
    import bspump.http.web.source
    import bspump.kafka
    import json

    @register_connection
    def connection(app):
        return bspump.kafka.KafkaConnection(app, "KafkaConnection")

.. code-block:: python

    # Cell 2: auto_pipeline (always in its own cell)
    auto_pipeline(
        source=lambda app, pipeline: bspump.http.web.source.WebHookSource(
            app, pipeline,
            config={"port": 8080, "path": "/webhook"}
        ),
        sink=lambda app, pipeline: bspump.kafka.KafkaSink(
            app, pipeline, connection="KafkaConnection"
        ),
        name="Webhook2KafkaPipeline",
    )

.. code-block:: python

    # Cell 3: Processing logic (runs for each event)
    print("Received webhook")
    data = json.loads(event)
    data["processed"] = True
    event = json.dumps(data).encode("utf8")

Interactive Development
-----------------------

During development, define a test event before ``auto_pipeline`` to test
your processing logic:

.. code-block:: python

    # Test event for interactive development
    event = {
        "id": "test-123",
        "sender": "+1234567890",
        "recipient": "+0987654321",
    }
    event = json.dumps(event).encode("utf8")

Now you can run the cells after ``auto_pipeline`` to test your processing
logic with this sample data.
