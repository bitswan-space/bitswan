bspump.common
=============

Common utilities, processors, and sinks for general use.

.. automodule:: bspump.common
   :members:
   :undoc-members:
   :show-inheritance:

Sinks
-----

PPrintSink
^^^^^^^^^^

Pretty-prints events to console. Useful for debugging.

.. code-block:: python

    import bspump.common

    sink = bspump.common.PPrintSink(app, pipeline)

NullSink
^^^^^^^^

Discards all events. Useful for testing or when output is handled elsewhere.

.. code-block:: python

    sink = bspump.common.NullSink(app, pipeline)

Processors
----------

JsonBytesToDictParser
^^^^^^^^^^^^^^^^^^^^^

Parses JSON bytes to Python dictionary.

.. code-block:: python

    processor = bspump.common.JsonBytesToDictParser(app, pipeline)

    # Input: b'{"key": "value"}'
    # Output: {"key": "value"}

DictToJsonBytesParser
^^^^^^^^^^^^^^^^^^^^^

Converts Python dictionary to JSON bytes.

.. code-block:: python

    processor = bspump.common.DictToJsonBytesParser(app, pipeline)

    # Input: {"key": "value"}
    # Output: b'{"key": "value"}'

MappingProcessor
^^^^^^^^^^^^^^^^

Maps/renames event keys.

.. code-block:: python

    processor = bspump.common.MappingProcessor(app, pipeline, mapping={
        "old_key": "new_key",
        "source_field": "dest_field"
    })

StdJsonToDictParser
^^^^^^^^^^^^^^^^^^^

Standard JSON parsing with error handling.

.. code-block:: python

    processor = bspump.common.StdJsonToDictParser(app, pipeline)

StdDictToJsonParser
^^^^^^^^^^^^^^^^^^^

Standard dictionary to JSON conversion.

.. code-block:: python

    processor = bspump.common.StdDictToJsonParser(app, pipeline)

StringToBytesParser
^^^^^^^^^^^^^^^^^^^

Converts string to bytes.

.. code-block:: python

    processor = bspump.common.StringToBytesParser(app, pipeline)

BytesToStringParser
^^^^^^^^^^^^^^^^^^^

Converts bytes to string.

.. code-block:: python

    processor = bspump.common.BytesToStringParser(app, pipeline)

RoutingProcessor
^^^^^^^^^^^^^^^^

Routes events to different pipelines.

.. code-block:: python

    processor = bspump.common.RoutingProcessor(app, pipeline, routing={
        "type_a": "PipelineA",
        "type_b": "PipelineB"
    })

FilterProcessor
^^^^^^^^^^^^^^^

Filters events based on a condition.

.. code-block:: python

    class MyFilter(bspump.common.FilterProcessor):
        def filter(self, context, event):
            return event.get("valid", False)

TeeProcessor
^^^^^^^^^^^^

Duplicates events to another pipeline.

.. code-block:: python

    processor = bspump.common.TeeProcessor(app, pipeline, target_pipeline_id="AuditPipeline")

Utility Functions
-----------------

These utilities are commonly used in pipelines:

- JSON parsing and serialization
- String/bytes conversion
- Event routing and filtering
- Debug output
