bspump.analyzer
===============

Analyzers for aggregation, statistics, and streaming analysis.

.. automodule:: bspump.analyzer
   :members:
   :undoc-members:
   :show-inheritance:

Analyzer
--------

Base class for analyzers.

.. code-block:: python

    import bspump
    from bspump.analyzer import Analyzer

    class MyAnalyzer(Analyzer):
        def evaluate(self, context, event):
            # Analyze the event
            return event

TimeWindowAnalyzer
------------------

Aggregate events over fixed time windows.

.. code-block:: python

    from bspump.analyzer import TimeWindowAnalyzer

    class HourlyAnalyzer(TimeWindowAnalyzer):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(
                app, pipeline, id, config,
                window_size=3600,  # 1 hour
                resolution=60      # 1 minute
            )

        def evaluate(self, context, event):
            # Process each event
            return event

        def on_tick(self, tick):
            # Called each resolution period
            pass

SessionAnalyzer
---------------

Track user sessions.

.. code-block:: python

    from bspump.analyzer import SessionAnalyzer

    class UserSessionAnalyzer(SessionAnalyzer):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(
                app, pipeline, id, config,
                session_timeout=1800  # 30 minutes
            )

        def evaluate(self, context, event):
            user_id = event.get("user_id")
            session = self.get_session(user_id)
            if session is None:
                session = self.create_session(user_id, {})
            return event

        def on_session_end(self, session_id, session_data):
            # Called when session times out
            pass

GeoAnalyzer
-----------

Analyze geographic data.

.. code-block:: python

    class GeoAnalyzer(bspump.Analyzer):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)
            self.matrix = Matrix(app, "GeoMatrix", (360, 180))

        def evaluate(self, context, event):
            lat = int(event.get("lat", 0) + 90)
            lon = int(event.get("lon", 0) + 180)
            self.matrix[lat, lon] += 1
            return event

Aggregation Example
-------------------

.. code-block:: python

    class CountingAnalyzer(bspump.Analyzer):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)
            self.counts = {}

        def evaluate(self, context, event):
            key = event.get("type")
            self.counts[key] = self.counts.get(key, 0) + 1
            event["running_count"] = self.counts[key]
            return event

Statistics Example
------------------

.. code-block:: python

    class StatisticsAnalyzer(bspump.Analyzer):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)
            self.sum = 0
            self.count = 0

        def evaluate(self, context, event):
            value = event.get("value", 0)
            self.sum += value
            self.count += 1
            event["mean"] = self.sum / self.count
            return event

Using with Pipeline
-------------------

.. code-block:: python

    class AnalysisPipeline(bspump.Pipeline):
        def __init__(self, app, pipeline_id):
            super().__init__(app, pipeline_id)
            self.build(
                bspump.kafka.KafkaSource(app, self, connection="KafkaConnection"),
                TimeWindowAnalyzer(app, self),
                SessionAnalyzer(app, self),
                bspump.kafka.KafkaSink(app, self, connection="KafkaConnection"),
            )
