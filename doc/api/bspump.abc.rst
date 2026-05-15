bspump.abc
==========

Abstract base classes for BSPump components.

.. automodule:: bspump.abc
   :members:
   :undoc-members:
   :show-inheritance:

Source
------

.. automodule:: bspump.abc.source
   :members:
   :undoc-members:
   :show-inheritance:

**Source**

Base class for continuous event sources.

.. code-block:: python

    class MySource(bspump.Source):
        async def main(self):
            while True:
                event = await self.get_event()
                await self.Pipeline.ready()
                await self.Pipeline.process(event)

**TriggerSource**

Base class for trigger-activated sources.

.. code-block:: python

    from bspump.abc.source import TriggerSource

    class MyTriggerSource(TriggerSource):
        async def cycle(self, *args, **kwargs):
            await self.Pipeline.ready()
            event = self.generate_event()
            await self.Pipeline.process(event)

Processor
---------

.. automodule:: bspump.abc.processor
   :members:
   :undoc-members:
   :show-inheritance:

**Processor**

Base class for event processors.

.. code-block:: python

    class MyProcessor(bspump.Processor):
        def process(self, context, event):
            # Transform event
            event["processed"] = True
            return event

        # Or async:
        async def process(self, context, event):
            result = await self.async_operation(event)
            event["result"] = result
            return event

Sink
----

.. automodule:: bspump.abc.sink
   :members:
   :undoc-members:
   :show-inheritance:

**Sink**

Base class for event sinks.

.. code-block:: python

    class MySink(bspump.Sink):
        def process(self, context, event):
            self.output(event)

        # Or async:
        async def process(self, context, event):
            await self.async_output(event)

Generator
---------

.. automodule:: bspump.abc.generator
   :members:
   :undoc-members:
   :show-inheritance:

**Generator**

Base class for 1-to-many event generation.

.. code-block:: python

    class MyGenerator(bspump.Generator):
        async def generate(self, context, event, depth):
            for item in event["items"]:
                self.Pipeline.inject(context, item, depth)

Connection
----------

.. automodule:: bspump.abc.connection
   :members:
   :undoc-members:
   :show-inheritance:

**Connection**

Base class for shared connections.

.. code-block:: python

    class MyConnection(bspump.Connection):
        async def connect(self):
            self.client = await create_client()

        async def disconnect(self):
            await self.client.close()

Lookup
------

.. automodule:: bspump.abc.lookup
   :members:
   :undoc-members:
   :show-inheritance:

**Lookup**

Base class for lookup tables.

.. code-block:: python

    class MyLookup(bspump.Lookup):
        def get(self, key):
            return self.data.get(key)

        def set(self, key, value):
            self.data[key] = value

Anomaly
-------

.. automodule:: bspump.abc.anomaly
   :members:
   :undoc-members:
   :show-inheritance:

**Anomaly**

Base class for anomaly detection.
