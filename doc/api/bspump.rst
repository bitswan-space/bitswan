bspump
======

The main BSPump module containing the core application framework.

.. automodule:: bspump
   :members:
   :undoc-members:
   :show-inheritance:

BSPumpApplication
-----------------

.. autoclass:: bspump.BSPumpApplication
   :members:
   :undoc-members:
   :show-inheritance:

The main application class that manages the event loop, services, and
component lifecycle.

**Example:**

.. code-block:: python

    import bspump

    app = bspump.BSPumpApplication()
    svc = app.get_service("bspump.PumpService")
    svc.add_pipeline(MyPipeline(app, "MyPipeline"))
    app.run()

BSPumpService
-------------

.. autoclass:: bspump.BSPumpService
   :members:
   :undoc-members:
   :show-inheritance:

Service that manages pipelines, connections, and lookups.

**Methods:**

- ``add_pipeline(pipeline)`` - Register a pipeline
- ``add_connection(connection)`` - Register a connection
- ``add_lookup(lookup)`` - Register a lookup
- ``locate_connection(connection_id)`` - Get a connection by ID
- ``locate_lookup(lookup_id)`` - Get a lookup by ID

Pipeline
--------

.. autoclass:: bspump.Pipeline
   :members:
   :undoc-members:
   :show-inheritance:

The core pipeline class that chains sources, processors, and sinks.

**Example:**

.. code-block:: python

    class MyPipeline(bspump.Pipeline):
        def __init__(self, app, pipeline_id):
            super().__init__(app, pipeline_id)
            self.build(
                MySource(app, self),
                MyProcessor(app, self),
                MySink(app, self),
            )

PumpBuilder
-----------

.. autoclass:: bspump.PumpBuilder
   :members:
   :undoc-members:
   :show-inheritance:

Utility for building pipelines programmatically.

Source
------

.. autoclass:: bspump.Source
   :members:
   :undoc-members:
   :show-inheritance:

Base class for event sources.

TriggerSource
-------------

.. autoclass:: bspump.TriggerSource
   :members:
   :undoc-members:
   :show-inheritance:

Base class for trigger-activated sources.

Processor
---------

.. autoclass:: bspump.Processor
   :members:
   :undoc-members:
   :show-inheritance:

Base class for event processors.

Generator
---------

.. autoclass:: bspump.Generator
   :members:
   :undoc-members:
   :show-inheritance:

Base class for generators that produce multiple events.

Sink
----

.. autoclass:: bspump.Sink
   :members:
   :undoc-members:
   :show-inheritance:

Base class for event sinks.

Connection
----------

.. autoclass:: bspump.Connection
   :members:
   :undoc-members:
   :show-inheritance:

Base class for shared connections.

Lookup
------

.. autoclass:: bspump.Lookup
   :members:
   :undoc-members:
   :show-inheritance:

Base class for lookup tables.

DictionaryLookup
----------------

.. autoclass:: bspump.DictionaryLookup
   :members:
   :undoc-members:
   :show-inheritance:

Simple dictionary-based lookup.

MappingLookup
-------------

.. autoclass:: bspump.MappingLookup
   :members:
   :undoc-members:
   :show-inheritance:

Mapping-based lookup with set/get operations.

ProcessingError
---------------

.. autoclass:: bspump.ProcessingError
   :members:
   :undoc-members:
   :show-inheritance:

Exception raised during event processing.

Analyzer
--------

.. autoclass:: bspump.Analyzer
   :members:
   :undoc-members:
   :show-inheritance:

Base class for analyzers.

Matrix
------

.. autoclass:: bspump.Matrix
   :members:
   :undoc-members:
   :show-inheritance:

Matrix data structure for multi-dimensional analysis.
