from ..abc.source import TriggerSource


class CronSource(TriggerSource):
    """
    A simplified source for cron-triggered pipelines.

    Usage:
        auto_pipeline(
            source=lambda app, pipeline: CronSource(
                app, pipeline,
                config={"when": "*/10 * * * *"}
            ),
            sink=lambda app, pipeline: PPrintSink(app, pipeline),
        )

    Config:
        when (str): Cron expression (e.g., "0 9 * * *" for daily at 9 AM)
        init_time (datetime, optional): Initial time for cron calculation (naive)
    """

    def __init__(self, app, pipeline, id=None, config=None):
        super().__init__(app, pipeline, id=id, config=config)

        cron_string = self.Config.get("when")
        if not cron_string:
            raise ValueError(
                "CronSource requires 'when' config parameter with cron expression"
            )

        init_time = self.Config.get("init_time")
        if init_time is None:
            from datetime import datetime

            init_time = datetime.now()  # naive for backward compatibility

        from ..trigger import CronTrigger

        cron_trigger = CronTrigger(app, cron_string, init_time, id=f"{self.Id}_cron")
        self.on(cron_trigger)

    async def cycle(self, *args, **kwargs):
        await self.Pipeline.ready()
        from datetime import datetime

        now = datetime.now()  # naive
        event = {
            "cron_triggered": now.isoformat(),
            "trigger_id": self.Id,
            "timestamp": now.timestamp(),
        }
        await self.Pipeline.process(event)
