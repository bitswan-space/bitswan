Custom Components
=================

This guide covers building custom BSPump components: sources, processors,
sinks, and connections.

Custom Source
-------------

Create a source that generates or receives events:

.. code-block:: python

    import bspump
    import asyncio

    class MySource(bspump.Source):
        """
        Source that polls an external API.
        """

        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)
            self.url = self.Config.get("url")
            self.poll_interval = self.Config.getint("poll_interval", 60)

        async def main(self):
            """Main event loop for the source."""
            while True:
                try:
                    events = await self.fetch_events()
                    for event in events:
                        await self.Pipeline.ready()
                        await self.Pipeline.process(event)
                except Exception as e:
                    L.error(f"Error fetching events: {e}")

                await asyncio.sleep(self.poll_interval)

        async def fetch_events(self):
            """Override to implement event fetching."""
            raise NotImplementedError

Custom TriggerSource
--------------------

For trigger-based sources:

.. code-block:: python

    from bspump.abc.source import TriggerSource
    from bspump.trigger import CronTrigger

    class ScheduledSource(TriggerSource):
        """Source that runs on a schedule."""

        async def cycle(self, *args, **kwargs):
            """Called each time the trigger fires."""
            await self.Pipeline.ready()

            events = await self.generate_events()
            for event in events:
                await self.Pipeline.process(event)

        async def generate_events(self):
            return [{"timestamp": datetime.now().isoformat()}]

    # Usage
    source = ScheduledSource(app, pipeline).on(
        CronTrigger(app, "*/5 * * * *")
    )

Custom Processor
----------------

Transform, filter, or enrich events:

.. code-block:: python

    import bspump

    class EnrichmentProcessor(bspump.Processor):
        """Enriches events with external data."""

        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)
            self.lookup_url = self.Config.get("lookup_url")
            self.cache = {}

        async def process(self, context, event):
            """Process a single event."""
            key = event.get("key")

            # Check cache
            if key in self.cache:
                event["enrichment"] = self.cache[key]
            else:
                # Fetch and cache
                enrichment = await self.fetch_enrichment(key)
                self.cache[key] = enrichment
                event["enrichment"] = enrichment

            return event

        async def fetch_enrichment(self, key):
            """Fetch enrichment data."""
            # Implementation here
            pass

Custom Generator
----------------

Produce multiple events from one input:

.. code-block:: python

    import bspump

    class SplitGenerator(bspump.Generator):
        """Splits batch events into individual events."""

        async def generate(self, context, event, depth):
            """Generate multiple events from one input."""
            items = event.get("items", [])

            for item in items:
                # Inject each item as a separate event
                self.Pipeline.inject(context, item, depth)

Custom Sink
-----------

Output events to external systems:

.. code-block:: python

    import bspump
    import aiohttp

    class WebhookSink(bspump.Sink):
        """Sends events to a webhook endpoint."""

        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)
            self.url = self.Config.get("url")
            self.session = None

        async def process(self, context, event):
            """Process (output) a single event."""
            if self.session is None:
                self.session = aiohttp.ClientSession()

            try:
                async with self.session.post(
                    self.url,
                    json=event,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status >= 400:
                        L.error(f"Webhook failed: {response.status}")
            except Exception as e:
                L.error(f"Webhook error: {e}")
                raise

Custom Connection
-----------------

Create reusable connections:

.. code-block:: python

    import bspump

    class MyServiceConnection(bspump.Connection):
        """Connection to a custom service."""

        def __init__(self, app, connection_id, config=None):
            super().__init__(app, connection_id, config=config)
            self.client = None

        async def connect(self):
            """Establish connection."""
            self.client = await create_client(
                host=self.Config.get("host"),
                port=self.Config.getint("port"),
                auth_token=self.Config.get("auth_token")
            )

        async def disconnect(self):
            """Close connection."""
            if self.client:
                await self.client.close()
                self.client = None

        def acquire(self):
            """Get a connection from the pool."""
            return self.client

Configuration
-------------

Components automatically receive configuration:

.. code-block:: ini

    [pipeline:MyPipeline:MySource]
    url=https://api.example.com/events
    poll_interval=60

    [pipeline:MyPipeline:EnrichmentProcessor]
    lookup_url=https://api.example.com/lookup

    [pipeline:MyPipeline:WebhookSink]
    url=https://webhook.example.com/events

    [connection:MyServiceConnection]
    host=localhost
    port=8080
    auth_token=${SERVICE_TOKEN}

Best Practices
--------------

1. **Use async for I/O**: Always use async for network operations
2. **Handle errors gracefully**: Log errors and decide whether to retry or drop
3. **Respect backpressure**: Call ``await self.Pipeline.ready()`` before processing
4. **Configure through Config**: Use ``self.Config`` for all configuration
5. **Clean up resources**: Implement proper shutdown in ``__del__`` or shutdown handlers
6. **Add logging**: Use ``L`` logger for debugging and monitoring
