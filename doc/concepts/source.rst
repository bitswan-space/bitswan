Source
======

Sources are the entry points for data into a pipeline. They either generate
events internally or receive them from external systems.

Source Types
------------

BSPump provides two base source classes:

**Source**
    Base class for sources that continuously produce events (like Kafka consumers).

**TriggerSource**
    Base class for sources that produce events on a trigger (like cron jobs).

Basic Source
------------

A simple source that produces events:

.. code-block:: python

    import bspump

    class MySource(bspump.Source):
        async def main(self):
            while True:
                event = await self.get_event_from_somewhere()
                await self.Pipeline.ready()
                await self.Pipeline.process(event)

TriggerSource
-------------

For sources that should run on a schedule or trigger:

.. code-block:: python

    import bspump
    from bspump.abc.source import TriggerSource
    from bspump.trigger import CronTrigger

    class ScheduledSource(TriggerSource):
        async def cycle(self, *args, **kwargs):
            await self.Pipeline.ready()
            event = {"timestamp": datetime.now().isoformat()}
            await self.Pipeline.process(event)

    # Use with a trigger
    source = ScheduledSource(app, pipeline).on(
        CronTrigger(app, "*/5 * * * *")  # Every 5 minutes
    )

Built-in Sources
----------------

BSPump includes many built-in sources:

**Kafka**

.. code-block:: python

    import bspump.kafka

    source = bspump.kafka.KafkaSource(
        app, pipeline,
        connection="KafkaConnection"
    )

**HTTP Webhook**

.. code-block:: python

    import bspump.http.web

    source = bspump.http.web.WebHookSource(
        app, pipeline,
        config={"path": "/webhook", "port": 8080}
    )

**File Sources**

.. code-block:: python

    import bspump.file

    # Line-by-line file reading
    source = bspump.file.FileLineSource(app, pipeline, config={
        "path": "/data/input.txt"
    })

    # CSV file reading
    source = bspump.file.FileCSVSource(app, pipeline, config={
        "path": "/data/input.csv"
    })

See :doc:`../integrations/index` for the full list of available sources.

Source Configuration
--------------------

Sources can be configured via:

1. Constructor parameters
2. Configuration file (``pipelines.conf``)

.. code-block:: ini

    [pipeline:MyPipeline:MySource]
    path=/data/input.txt
    batch_size=100

Context
-------

Sources can attach context to events, which is passed through the pipeline:

.. code-block:: python

    async def main(self):
        context = {"source": "my_source", "timestamp": time.time()}
        await self.Pipeline.process(event, context=context)

The context can be accessed in processors:

.. code-block:: python

    def process(self, context, event):
        source = context.get("source")
        return event
