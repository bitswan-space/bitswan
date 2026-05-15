Processor
=========

Processors transform, filter, enrich, or route events as they flow through
a pipeline. They sit between the source and sink.

Basic Processor
---------------

A processor implements the ``process`` method:

.. code-block:: python

    import bspump

    class MyProcessor(bspump.Processor):
        def process(self, context, event):
            # Transform the event
            event["processed"] = True
            return event

The ``process`` method receives:

- **context**: A dictionary with metadata about the event
- **event**: The event to process

It must return:

- The transformed event
- ``None`` to drop the event (filter it out)

Filtering Events
----------------

Return ``None`` to filter out events:

.. code-block:: python

    class FilterProcessor(bspump.Processor):
        def process(self, context, event):
            if event.get("type") == "spam":
                return None  # Drop spam events
            return event

Async Processors
----------------

For I/O-bound operations, use async processors:

.. code-block:: python

    class AsyncProcessor(bspump.Processor):
        async def process(self, context, event):
            # Async operations are supported
            result = await self.fetch_enrichment_data(event["id"])
            event["enriched"] = result
            return event

Generator (1-to-Many)
---------------------

When you need to produce multiple events from a single input:

.. code-block:: python

    import bspump

    class SplitGenerator(bspump.Generator):
        async def generate(self, context, event, depth):
            # Split a batch into individual events
            for item in event["items"]:
                self.Pipeline.inject(context, item, depth)

Built-in Processors
-------------------

BSPump includes many utility processors:

**JSON Parsing**

.. code-block:: python

    import bspump.common

    # Parse JSON bytes to dict
    processor = bspump.common.JsonBytesToDictParser(app, pipeline)

    # Convert dict to JSON bytes
    processor = bspump.common.DictToJsonBytesParser(app, pipeline)

**Mapping and Transformation**

.. code-block:: python

    # Apply a function to each event
    processor = bspump.common.MappingProcessor(app, pipeline, mapping={
        "old_key": "new_key"
    })

**Routing**

.. code-block:: python

    # Route events to different pipelines
    processor = bspump.common.RouterProcessor(app, pipeline, routing={
        "type_a": "PipelineA",
        "type_b": "PipelineB"
    })

Processor Chains
----------------

Processors are chained together in the pipeline:

.. code-block:: python

    class MyPipeline(bspump.Pipeline):
        def __init__(self, app, pipeline_id):
            super().__init__(app, pipeline_id)
            self.build(
                MySource(app, self),
                ValidateProcessor(app, self),      # Step 1
                EnrichProcessor(app, self),        # Step 2
                TransformProcessor(app, self),    # Step 3
                MySink(app, self),
            )

Events flow through processors in order.

Error Handling
--------------

Handle errors gracefully in processors:

.. code-block:: python

    class SafeProcessor(bspump.Processor):
        def process(self, context, event):
            try:
                return self.risky_transform(event)
            except Exception as e:
                L.error(f"Processing error: {e}")
                # Either return None to drop, or return original
                return None

For recoverable errors, consider routing failed events to a dead-letter queue.
