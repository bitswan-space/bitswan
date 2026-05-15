Notebook Structure
==================

BSPump notebooks follow a specific three-part structure that maps directly
to how pipelines work in production.

The Three Sections
------------------

**1. Before auto_pipeline**

This section contains setup code:

- Imports
- Connection registrations (``@register_connection``)
- Lookup registrations (``@register_lookup``)
- Helper functions and classes
- Test event data for interactive development

**2. The auto_pipeline Cell**

This cell defines the pipeline's source and sink. It must be in its own
cell because it marks the boundary between setup and processing.

**3. After auto_pipeline**

Everything after ``auto_pipeline`` becomes processing logic. When deployed,
these cells are compiled into a single async processor. You can:

- Transform the ``event`` variable
- Set ``event = None`` to drop events
- Use ``await`` for async operations
- Call helper functions defined before ``auto_pipeline``

Complete Example: Webhook to Kafka
----------------------------------

.. code-block:: python

    # ============================================
    # BEFORE auto_pipeline: Setup
    # ============================================

    from bspump.jupyter import *
    import bspump.http.web.source
    import bspump.kafka
    import json
    import os

    @register_connection
    def connection(app):
        return bspump.kafka.KafkaConnection(app, "KafkaConnection")

    # Helper function (available in processing cells)
    def validate_request(data):
        required = ["sender", "recipient"]
        return all(k in data for k in required)

    # Test event for interactive development
    event = json.dumps({
        "sender": "+1234567890",
        "recipient": "+0987654321",
        "subject": "Test Fax"
    }).encode("utf8")

.. code-block:: python

    # ============================================
    # auto_pipeline cell (always standalone)
    # ============================================

    auto_pipeline(
        source=lambda app, pipeline: bspump.http.web.source.WebHookSource(
            app, pipeline,
            config={
                "port": 8080,
                "path": "/",
                "secret_qparam": os.environ.get("API_SECRET"),
            }
        ),
        sink=lambda app, pipeline: bspump.kafka.KafkaSink(
            app, pipeline, connection="KafkaConnection"
        ),
        name="Webhook2KafkaPipeline",
    )

.. code-block:: python

    # ============================================
    # AFTER auto_pipeline: Processing
    # ============================================

    print("Queuing request")
    request = json.loads(event)

    # Validate the request
    if not validate_request(request):
        print("Invalid request, dropping")
        event = None
    else:
        print(f"Processing request for {request['recipient']}")

.. code-block:: python

    # Additional processing cell (also becomes part of the processor)
    if event:
        request["queued_at"] = datetime.now().isoformat()
        event = json.dumps(request).encode("utf8")

Complete Example: Kafka Processing
----------------------------------

.. code-block:: python

    # Setup
    from bspump.jupyter import *
    import bspump.kafka
    import json
    import aiohttp

    @register_connection
    def connection(app):
        return bspump.kafka.KafkaConnection(app, "KafkaConnection")

    api_token = os.getenv("API_TOKEN")
    api_endpoint = "https://api.example.com/process"

    # Test event
    event = json.dumps({
        "id": "fax-123",
        "status": "pending"
    }).encode("utf8")

.. code-block:: python

    auto_pipeline(
        source=lambda app, pipeline: bspump.kafka.KafkaSource(
            app, pipeline, connection="KafkaConnection"
        ),
        sink=lambda app, pipeline: bspump.kafka.KafkaSink(
            app, pipeline, connection="KafkaConnection"
        ),
        name="ProcessingPipeline",
    )

.. code-block:: python

    # Parse the event
    event = json.loads(event.decode("utf8"))
    print(f"Processing event: {event['id']}")

.. code-block:: python

    # Call external API (async is supported)
    async with aiohttp.ClientSession() as session:
        async with session.post(
            api_endpoint,
            headers={"Authorization": f"Bearer {api_token}"},
            json=event
        ) as response:
            result = await response.json()
            event["api_result"] = result

.. code-block:: python

    # Serialize for output
    event = json.dumps(event).encode("utf8")

Complete Example: Cron Scheduled Task
-------------------------------------

.. code-block:: python

    # Setup
    from bspump.jupyter import *
    from bspump.trigger import CronTrigger
    from bspump.abc.source import TriggerSource
    import bspump.common
    from datetime import datetime, timezone
    import requests
    import os

    api_token = os.getenv("API_TOKEN")

    class ScheduledSource(TriggerSource):
        async def cycle(self, *args, **kwargs):
            await self.Pipeline.ready()
            event = {"triggered_at": datetime.now(timezone.utc)}
            await self.Pipeline.process(event)

    # Test event for development
    event = {"triggered_at": datetime.now(timezone.utc)}

.. code-block:: python

    auto_pipeline(
        source=lambda app, pipeline: ScheduledSource(app, pipeline).on(
            CronTrigger(app, "*/15 * * * *")  # Every 15 minutes
        ),
        sink=lambda app, pipeline: bspump.common.PPrintSink(app, pipeline),
        name="ScheduledCheckPipeline",
    )

.. code-block:: python

    # Processing: Check system status
    print(f"Running scheduled check at {event['triggered_at']}")

    response = requests.get(
        "https://api.example.com/status",
        headers={"Authorization": f"Bearer {api_token}"}
    )
    event["status"] = response.json()

    if event["status"].get("error"):
        # Send alert
        requests.post(
            os.getenv("ALERT_WEBHOOK_URL"),
            json={"message": f"Error detected: {event['status']['error']}"}
        )

Complete Example: Custom Event Source
-------------------------------------

For integrating with systems that don't have built-in sources:

.. code-block:: python

    # Setup
    from bspump.jupyter import *
    from bspump.abc.source import Source
    import bspump.kafka
    import json
    import os
    import asyncio
    import concurrent.futures
    import greenswitch  # FreeSWITCH library

    @register_connection
    def connection(app):
        return bspump.kafka.KafkaConnection(app, "KafkaConnection")

    class FreeSwitchSource(Source):
        """Custom source for FreeSWITCH events."""

        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id=id, config=config)
            self.App = app
            self.Loop = app.Loop
            self.Running = False
            self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        async def main(self):
            host = os.environ.get("FREESWITCH_HOST", "freeswitch")
            port = 8021
            password = os.environ["FREESWITCH_PASSWORD"]

            self.Running = True
            await self.Loop.run_in_executor(
                self._executor,
                self._run_client, host, port, password
            )

        def _run_client(self, host, port, password):
            import gevent

            while self.Running:
                try:
                    client = greenswitch.InboundESL(host=host, port=port, password=password)
                    client.connect()

                    # Subscribe to events
                    client.register_handle("spandsp::txfaxresult", self._handle_event)
                    client.send("EVENTS PLAIN CUSTOM spandsp::txfaxresult")

                    while self.Running:
                        gevent.sleep(1)
                        client.send("LINGER")
                except Exception as e:
                    print(f"Connection error: {e}")
                    gevent.sleep(5)

        def _handle_event(self, event):
            event_data = dict(event.headers)
            asyncio.run_coroutine_threadsafe(
                self._process_event(event_data),
                self.Loop
            )

        async def _process_event(self, event_data):
            await self.process(event_data, {})

    # Test event
    event = {"Event-Name": "CUSTOM", "fax_result": "success"}

.. code-block:: python

    auto_pipeline(
        source=lambda app, pipeline: FreeSwitchSource(app, pipeline),
        sink=lambda app, pipeline: bspump.kafka.KafkaSink(
            app, pipeline, connection="KafkaConnection"
        ),
        name="FreeSwitch2KafkaPipeline",
    )

.. code-block:: python

    # Process FreeSWITCH events
    print("Received FreeSWITCH event")
    print(event)
    event = json.dumps(event).encode("utf8")

Key Points
----------

1. **auto_pipeline always in its own cell**: This is required for the compilation to work correctly.

2. **Test events before auto_pipeline**: Define sample events to test your processing logic interactively.

3. **Processing cells support await**: The cells after ``auto_pipeline`` are compiled into an async function.

4. **Helper functions before auto_pipeline**: Define reusable functions in the setup section.

5. **Control event flow with exceptions**: Use ``raise SkipEvent()`` to drop events or ``raise FinalizeEvent(event)`` to send to sink immediately.

Event Flow Control
------------------

BSPump provides special exceptions for cleaner event flow control:

**SkipEvent** - Drop an event without further processing:

.. code-block:: python

    from bspump.jupyter import SkipEvent

    if event.get("type") == "spam":
        raise SkipEvent()  # Event is dropped, no output to sink

    event["processed"] = True

**FinalizeEvent** - Send event to sink immediately, skip remaining cells:

.. code-block:: python

    from bspump.jupyter import FinalizeEvent

    if event.get("cached"):
        raise FinalizeEvent(event)  # Sent to sink now

    # This only runs for non-cached events
    event["result"] = expensive_computation(event)
