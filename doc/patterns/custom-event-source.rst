Custom Event Source
===================

This pattern demonstrates building custom sources for polling external systems
or handling custom data ingestion scenarios.

Use Cases
---------

- Polling REST APIs for new data
- Integrating with proprietary systems
- Custom file watchers
- Database change data capture

Basic Custom Source
-------------------

A minimal custom source:

.. code-block:: python

    import bspump
    import asyncio

    class MyCustomSource(bspump.Source):
        async def main(self):
            while True:
                # Fetch data from external system
                events = await self.fetch_events()

                for event in events:
                    await self.Pipeline.ready()
                    await self.Pipeline.process(event)

                # Wait before next poll
                await asyncio.sleep(10)

        async def fetch_events(self):
            # Implement your data fetching logic
            return [{"id": 1, "data": "example"}]

Polling REST API
----------------

A source that polls a REST API:

.. code-block:: python

    import bspump
    import aiohttp
    import asyncio

    class RESTPollingSource(bspump.Source):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)
            self.url = self.Config.get("url")
            self.poll_interval = self.Config.getint("poll_interval", 60)
            self.session = None
            self.last_id = None

        async def main(self):
            async with aiohttp.ClientSession() as self.session:
                while True:
                    await self.poll()
                    await asyncio.sleep(self.poll_interval)

        async def poll(self):
            params = {}
            if self.last_id:
                params["since_id"] = self.last_id

            async with self.session.get(self.url, params=params) as response:
                data = await response.json()

                for item in data.get("items", []):
                    await self.Pipeline.ready()
                    await self.Pipeline.process(item)
                    self.last_id = item.get("id")

Using Thread Pools
------------------

For blocking operations, use a thread pool:

.. code-block:: python

    import bspump
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    class ThreadedSource(bspump.Source):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)
            self.executor = ThreadPoolExecutor(max_workers=4)

        async def main(self):
            loop = asyncio.get_event_loop()
            while True:
                # Run blocking operation in thread pool
                events = await loop.run_in_executor(
                    self.executor,
                    self.blocking_fetch
                )

                for event in events:
                    await self.Pipeline.ready()
                    await self.Pipeline.process(event)

                await asyncio.sleep(10)

        def blocking_fetch(self):
            # Blocking I/O operations here
            import requests
            response = requests.get("https://api.example.com/data")
            return response.json()

TriggerSource for Scheduled Polling
-----------------------------------

Use TriggerSource for cron-scheduled polling:

.. code-block:: python

    from bspump.abc.source import TriggerSource
    from bspump.trigger import CronTrigger

    class ScheduledPollingSource(TriggerSource):
        async def cycle(self, *args, **kwargs):
            # Called on each trigger
            events = await self.fetch_events()

            for event in events:
                await self.Pipeline.ready()
                await self.Pipeline.process(event)

        async def fetch_events(self):
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url) as response:
                    return await response.json()

    # Usage
    source = ScheduledPollingSource(app, pipeline).on(
        CronTrigger(app, "*/5 * * * *")  # Every 5 minutes
    )

Jupyter Implementation
----------------------

.. code-block:: python

    from bspump.jupyter import *
    from bspump.abc.source import TriggerSource
    from bspump.trigger import CronTrigger
    import aiohttp

    class APIPollingSource(TriggerSource):
        async def cycle(self, *args, **kwargs):
            await self.Pipeline.ready()

            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.example.com/events") as resp:
                    data = await resp.json()

            for event in data:
                await self.Pipeline.process(event)

    auto_pipeline(
        source=lambda app, pipeline: APIPollingSource(app, pipeline).on(
            CronTrigger(app, "*/5 * * * *")
        ),
        sink=lambda app, pipeline: bspump.common.PPrintSink(app, pipeline),
        name="PollingPipeline",
    )

Configuration
-------------

.. code-block:: ini

    [pipeline:PollingPipeline:RESTPollingSource]
    url=https://api.example.com/events
    poll_interval=60

Best Practices
--------------

1. **Handle rate limits**: Respect API rate limits with backoff
2. **Track state**: Remember last processed ID for incremental polling
3. **Use connection pooling**: Reuse HTTP sessions
4. **Handle failures**: Implement retry logic with exponential backoff
5. **Log progress**: Track metrics for monitoring
