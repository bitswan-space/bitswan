auto_pipeline Reference
=======================

The ``auto_pipeline`` function creates a pipeline where notebook cells
after the call become the processing logic.

Function Signature
------------------

.. code-block:: python

    auto_pipeline(
        source,      # Lambda returning a Source
        sink,        # Lambda returning a Sink
        name,        # Pipeline name (string)
        processors=None  # Optional list of explicit processors
    )

Parameters
----------

**source** (required)
    A lambda function that receives ``(app, pipeline)`` and returns a Source instance.

    .. code-block:: python

        source=lambda app, pipeline: bspump.kafka.KafkaSource(
            app, pipeline, connection="KafkaConnection"
        )

**sink** (required)
    A lambda function that receives ``(app, pipeline)`` and returns a Sink instance.

    .. code-block:: python

        sink=lambda app, pipeline: bspump.kafka.KafkaSink(
            app, pipeline, connection="KafkaConnection"
        )

**name** (required)
    A string identifier for the pipeline.

    .. code-block:: python

        name="MyProcessingPipeline"

**processors** (optional)
    A list of lambdas returning explicit Processor instances. These run
    before the notebook cell processing.

    .. code-block:: python

        processors=[
            lambda app, pipeline: MyProcessor(app, pipeline)
        ]

Common Source Patterns
----------------------

**Kafka Source**

.. code-block:: python

    auto_pipeline(
        source=lambda app, pipeline: bspump.kafka.KafkaSource(
            app, pipeline, connection="KafkaConnection"
        ),
        ...
    )

**HTTP Webhook Source**

.. code-block:: python

    auto_pipeline(
        source=lambda app, pipeline: bspump.http.web.source.WebHookSource(
            app, pipeline,
            config={
                "port": 8080,
                "path": "/webhook",
                "secret_qparam": os.environ.get("WEBHOOK_SECRET"),
            }
        ),
        ...
    )

**Cron Trigger Source**

.. code-block:: python

    from bspump.abc.source import TriggerSource
    from bspump.trigger import CronTrigger
    from datetime import datetime

    class ScheduledSource(TriggerSource):
        async def cycle(self, *args, **kwargs):
            await self.Pipeline.ready()
            await self.Pipeline.process({"triggered_at": datetime.now()})

    auto_pipeline(
        source=lambda app, pipeline: ScheduledSource(app, pipeline).on(
            CronTrigger(app, "*/15 * * * *")  # Every 15 minutes
        ),
        ...
    )

Common Sink Patterns
--------------------

**Kafka Sink**

.. code-block:: python

    auto_pipeline(
        ...
        sink=lambda app, pipeline: bspump.kafka.KafkaSink(
            app, pipeline, connection="KafkaConnection"
        ),
    )

**PPrint Sink (for debugging/scheduled tasks)**

.. code-block:: python

    auto_pipeline(
        ...
        sink=lambda app, pipeline: bspump.common.PPrintSink(app, pipeline),
    )

**Null Sink (for tasks with side effects only)**

.. code-block:: python

    auto_pipeline(
        ...
        sink=lambda app, pipeline: bspump.common.NullSink(app, pipeline),
    )

Connection Registration
-----------------------

Register connections before ``auto_pipeline`` using the ``@register_connection`` decorator:

.. code-block:: python

    from bspump.jupyter import *
    import bspump.kafka

    @register_connection
    def kafka_connection(app):
        return bspump.kafka.KafkaConnection(app, "KafkaConnection")

Multiple connections:

.. code-block:: python

    @register_connection
    def kafka_connection(app):
        return bspump.kafka.KafkaConnection(app, "KafkaConnection")

    @register_connection
    def postgres_connection(app):
        return bspump.postgresql.PostgreSQLConnection(app, "PostgreSQLConnection")

Processing After auto_pipeline
------------------------------

Cells after ``auto_pipeline`` process each event. The ``event`` variable
contains the incoming data.

**Basic transformation:**

.. code-block:: python

    import json

    # Parse JSON
    event = json.loads(event.decode("utf8"))

    # Transform
    event["processed"] = True

    # Serialize back
    event = json.dumps(event).encode("utf8")

**Filtering (drop events):**

.. code-block:: python

    data = json.loads(event.decode("utf8"))

    if data.get("type") == "spam":
        event = None  # Drop this event
    else:
        event = json.dumps(data).encode("utf8")

**Async operations:**

.. code-block:: python

    import aiohttp

    data = json.loads(event.decode("utf8"))

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, json=data) as response:
            result = await response.json()
            data["api_result"] = result

    event = json.dumps(data).encode("utf8")

**Multiple cells:**

Each cell runs in sequence. The ``event`` variable persists between cells:

.. code-block:: python

    # Cell 1: Parse
    event = json.loads(event.decode("utf8"))

.. code-block:: python

    # Cell 2: Validate
    if "id" not in event:
        raise ValueError("Missing id")

.. code-block:: python

    # Cell 3: Transform
    event["validated"] = True

.. code-block:: python

    # Cell 4: Serialize
    event = json.dumps(event).encode("utf8")

Environment Variables
---------------------

Access secrets via environment variables:

.. code-block:: python

    import os

    api_token = os.getenv("API_TOKEN")
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

See :doc:`../configuration/secrets` for configuring secrets in BitSwan.
