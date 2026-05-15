bspump.trigger
==============

Triggers for controlling when TriggerSources produce events.

.. automodule:: bspump.trigger
   :members:
   :undoc-members:
   :show-inheritance:

CronTrigger
-----------

Schedule-based triggers using cron expressions.

.. code-block:: python

    from bspump.trigger import CronTrigger

    trigger = CronTrigger(app, "*/5 * * * *")  # Every 5 minutes

**Cron Expression Format:**

.. code-block:: text

    ┌───────────── minute (0 - 59)
    │ ┌───────────── hour (0 - 23)
    │ │ ┌───────────── day of month (1 - 31)
    │ │ │ ┌───────────── month (1 - 12)
    │ │ │ │ ┌───────────── day of week (0 - 6, Sunday = 0)
    │ │ │ │ │
    * * * * *

**Examples:**

.. code-block:: python

    CronTrigger(app, "*/10 * * * *")     # Every 10 minutes
    CronTrigger(app, "0 * * * *")        # Every hour
    CronTrigger(app, "0 0 * * *")        # Daily at midnight
    CronTrigger(app, "0 9 * * 1")        # Monday at 9 AM
    CronTrigger(app, "0 0 1 * *")        # First of each month
    CronTrigger(app, "0 18 * * 1-5")     # Weekdays at 6 PM

PubSubTrigger
-------------

Event-driven triggers using internal pub/sub.

.. code-block:: python

    from bspump.trigger import PubSubTrigger

    trigger = PubSubTrigger(app, "my.event.topic")

    # Fire the trigger from elsewhere
    app.PubSub.publish("my.event.topic", data={"key": "value"})

PeriodicTrigger
---------------

Simple interval-based triggers.

.. code-block:: python

    from bspump.trigger import PeriodicTrigger

    trigger = PeriodicTrigger(app, 10)  # Every 10 seconds

OpportunisticTrigger
--------------------

Fires when the application has idle time.

.. code-block:: python

    from bspump.trigger import OpportunisticTrigger

    trigger = OpportunisticTrigger(app)

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

    source = MySource(app, pipeline).on(
        CronTrigger(app, "*/5 * * * *")
    )

Multiple Triggers
-----------------

A source can have multiple triggers:

.. code-block:: python

    source = MySource(app, pipeline).on(
        CronTrigger(app, "0 * * * *"),     # Every hour
        PubSubTrigger(app, "force.run")    # On-demand
    )

The source's ``cycle()`` method runs when any trigger fires.

Custom Triggers
---------------

Create custom triggers:

.. code-block:: python

    from bspump.trigger import Trigger

    class WebhookTrigger(Trigger):
        def __init__(self, app, path):
            super().__init__(app)
            self.path = path
            # Set up webhook handler

        async def handle_webhook(self, request):
            await self.fire()
