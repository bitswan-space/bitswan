Scheduled Tasks
===============

This pattern demonstrates running periodic tasks using CronTrigger for
scheduled job execution.

Use Cases
---------

- Periodic data aggregation and reporting
- Scheduled cleanup tasks
- Regular health checks
- Batch processing at specific times
- Daily/weekly/monthly jobs

Architecture
------------

.. code-block:: text

    CronTrigger
    (Schedule: "0 * * * *")
          │
          ▼
    ┌───────────────────┐
    │  TriggerSource    │
    │  cycle() method   │
    └───────────────────┘
          │
          ▼
    ┌───────────────────┐
    │   Processors      │
    └───────────────────┘
          │
          ▼
    ┌───────────────────┐
    │      Sink         │
    └───────────────────┘

Jupyter Implementation
----------------------

.. code-block:: python

    from bspump.jupyter import *
    from bspump.abc.source import TriggerSource
    from bspump.trigger import CronTrigger
    from datetime import datetime

    class ScheduledSource(TriggerSource):
        async def cycle(self, *args, **kwargs):
            await self.Pipeline.ready()
            event = {
                "type": "scheduled_job",
                "triggered_at": datetime.now().isoformat(),
                "job_name": "hourly_report"
            }
            await self.Pipeline.process(event)

    auto_pipeline(
        source=lambda app, pipeline: ScheduledSource(app, pipeline).on(
            CronTrigger(app, "0 * * * *")  # Every hour
        ),
        sink=lambda app, pipeline: bspump.common.PPrintSink(app, pipeline),
        name="ScheduledPipeline",
    )

Process the scheduled event:

.. code-block:: python

    # Generate report data
    event["report_data"] = await generate_hourly_report()
    event["completed_at"] = datetime.now().isoformat()

Standalone Application
----------------------

.. code-block:: python

    import bspump
    import bspump.common
    from bspump.abc.source import TriggerSource
    from bspump.trigger import CronTrigger
    from datetime import datetime

    class DailyReportSource(TriggerSource):
        async def cycle(self, *args, **kwargs):
            await self.Pipeline.ready()

            # Generate daily report
            report = await self.generate_report()
            await self.Pipeline.process(report)

        async def generate_report(self):
            return {
                "type": "daily_report",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "metrics": {
                    "total_events": 12345,
                    "errors": 5,
                    "success_rate": 99.96
                }
            }

    class ReportProcessor(bspump.Processor):
        def process(self, context, event):
            # Format report for output
            event["formatted"] = f"Daily Report for {event['date']}"
            return event

    class ScheduledPipeline(bspump.Pipeline):
        def __init__(self, app, pipeline_id):
            super().__init__(app, pipeline_id)
            self.build(
                DailyReportSource(app, self).on(
                    CronTrigger(app, "0 0 * * *")  # Daily at midnight
                ),
                ReportProcessor(app, self),
                bspump.common.PPrintSink(app, self),
            )

    if __name__ == "__main__":
        app = bspump.BSPumpApplication()
        svc = app.get_service("bspump.PumpService")
        svc.add_pipeline(ScheduledPipeline(app, "ScheduledPipeline"))
        app.run()

Multiple Triggers
-----------------

Combine multiple triggers for flexibility:

.. code-block:: python

    from bspump.trigger import CronTrigger, PubSubTrigger

    source = MySource(app, pipeline).on(
        # Regular schedule
        CronTrigger(app, "0 * * * *"),
        # On-demand trigger via pub/sub
        PubSubTrigger(app, "run.scheduled.job")
    )

    # Trigger on-demand
    app.PubSub.publish("run.scheduled.job")

Batch Processing with Scheduled Source
--------------------------------------

Process multiple items in a single cycle:

.. code-block:: python

    class BatchProcessingSource(TriggerSource):
        async def cycle(self, *args, **kwargs):
            await self.Pipeline.ready()

            # Fetch batch of items to process
            items = await self.fetch_pending_items()

            for item in items:
                await self.Pipeline.process(item)

        async def fetch_pending_items(self):
            # Query database for pending items
            async with self.db_connection.acquire() as conn:
                return await conn.fetch(
                    "SELECT * FROM pending_items WHERE status = 'pending'"
                )

Cron Expression Examples
------------------------

.. code-block:: python

    # Every 10 minutes
    CronTrigger(app, "*/10 * * * *")

    # Every hour at minute 0
    CronTrigger(app, "0 * * * *")

    # Every day at midnight
    CronTrigger(app, "0 0 * * *")

    # Every Monday at 9 AM
    CronTrigger(app, "0 9 * * 1")

    # First of every month at midnight
    CronTrigger(app, "0 0 1 * *")

    # Weekdays at 6 PM
    CronTrigger(app, "0 18 * * 1-5")

Configuration
-------------

.. code-block:: ini

    [pipeline:ScheduledPipeline]
    # Pipeline-level configuration

Best Practices
--------------

1. **Idempotent operations**: Design jobs to be safely re-run
2. **Track execution**: Log start/end times and results
3. **Handle long-running jobs**: Use async for lengthy operations
4. **Avoid overlapping**: Ensure jobs complete before next trigger
5. **Monitor failures**: Alert on job failures
