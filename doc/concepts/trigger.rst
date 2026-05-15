Trigger
=======

Triggers control when TriggerSources produce events. They enable scheduled
execution, pub/sub patterns, and other event-driven architectures.

What are Triggers?
------------------

Triggers are used with ``TriggerSource`` to define when the source's
``cycle()`` method should be called. Common use cases:

- Running tasks on a schedule (cron)
- Responding to external events (pub/sub)
- Periodic polling

Using Triggers
--------------

Attach triggers to a TriggerSource:

.. code-block:: python

    from bspump.abc.source import TriggerSource
    from bspump.trigger import CronTrigger

    class MySource(TriggerSource):
        async def cycle(self, *args, **kwargs):
            await self.Pipeline.ready()
            event = {"timestamp": datetime.now().isoformat()}
            await self.Pipeline.process(event)

    # Attach a cron trigger
    source = MySource(app, pipeline).on(
        CronTrigger(app, "*/5 * * * *")  # Every 5 minutes
    )

Built-in Triggers
-----------------

**CronTrigger**

Schedule-based triggers using cron expressions:

.. code-block:: python

    from bspump.trigger import CronTrigger

    # Every 5 minutes
    trigger = CronTrigger(app, "*/5 * * * *")

    # Every hour at minute 0
    trigger = CronTrigger(app, "0 * * * *")

    # Every day at midnight
    trigger = CronTrigger(app, "0 0 * * *")

    # Every Monday at 9 AM
    trigger = CronTrigger(app, "0 9 * * 1")

**PubSubTrigger**

Event-driven triggers using internal pub/sub:

.. code-block:: python

    from bspump.trigger import PubSubTrigger

    trigger = PubSubTrigger(app, "my.event.topic")

    # Fire the trigger from elsewhere
    app.PubSub.publish("my.event.topic", data={"key": "value"})

**PeriodicTrigger**

Simple interval-based triggers:

.. code-block:: python

    from bspump.trigger import PeriodicTrigger

    # Every 10 seconds
    trigger = PeriodicTrigger(app, 10)

**OpportunisticTrigger**

Fires when the application has idle time:

.. code-block:: python

    from bspump.trigger import OpportunisticTrigger

    trigger = OpportunisticTrigger(app)

Multiple Triggers
-----------------

A source can have multiple triggers:

.. code-block:: python

    source = MySource(app, pipeline).on(
        CronTrigger(app, "0 * * * *"),    # Every hour
        PubSubTrigger(app, "force.run")   # On-demand
    )

The source's ``cycle()`` method runs when any trigger fires.

Trigger with Arguments
----------------------

Triggers can pass arguments to the ``cycle()`` method:

.. code-block:: python

    class MySource(TriggerSource):
        async def cycle(self, trigger_name=None, **kwargs):
            await self.Pipeline.ready()
            event = {
                "trigger": trigger_name,
                "timestamp": datetime.now().isoformat()
            }
            await self.Pipeline.process(event)

Cron Expression Reference
-------------------------

Cron expressions have 5 fields:

.. code-block:: text

    ┌───────────── minute (0 - 59)
    │ ┌───────────── hour (0 - 23)
    │ │ ┌───────────── day of month (1 - 31)
    │ │ │ ┌───────────── month (1 - 12)
    │ │ │ │ ┌───────────── day of week (0 - 6, Sunday = 0)
    │ │ │ │ │
    * * * * *

Special characters:

- ``*`` - any value
- ``*/n`` - every n units
- ``n,m`` - specific values
- ``n-m`` - range of values

Examples:

- ``*/15 * * * *`` - every 15 minutes
- ``0 9-17 * * 1-5`` - hourly, 9 AM to 5 PM, Monday through Friday
- ``0 0 1 * *`` - midnight on the first of each month

Custom Triggers
---------------

Create custom triggers by extending the base class:

.. code-block:: python

    import bspump.trigger

    class WebhookTrigger(bspump.trigger.Trigger):
        def __init__(self, app, webhook_path):
            super().__init__(app)
            self.webhook_path = webhook_path
            # Set up webhook handler

        async def handle_webhook(self, request):
            # Fire the trigger
            await self.fire()
