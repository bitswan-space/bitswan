Analyzers
=========

BSPump provides analyzers for time-window aggregation, statistics, and
anomaly detection over streaming data.

Overview
--------

Analyzers are specialized processors that maintain state across events
and can perform complex aggregations.

TimeWindowAnalyzer
------------------

Aggregate events over fixed time windows:

.. code-block:: python

    import bspump
    from bspump.analyzer import TimeWindowAnalyzer

    class HourlyCountAnalyzer(TimeWindowAnalyzer):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(
                app, pipeline, id, config,
                window_size=3600,  # 1 hour in seconds
                resolution=60     # 1 minute resolution
            )
            self.counts = {}

        def evaluate(self, context, event):
            event_type = event.get("type")
            self.counts[event_type] = self.counts.get(event_type, 0) + 1
            return event

        def on_tick(self, tick):
            # Called each resolution period
            for event_type, count in self.counts.items():
                print(f"{event_type}: {count} events")
            self.counts.clear()

SessionAnalyzer
---------------

Track user sessions:

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
                # New session
                session = self.create_session(user_id, {
                    "start_time": event.get("timestamp"),
                    "events": []
                })

            session["events"].append(event)
            return event

        def on_session_end(self, session_id, session_data):
            # Called when session times out
            duration = len(session_data["events"])
            print(f"Session {session_id} ended with {duration} events")

Matrix Analyzer
---------------

Use matrices for multi-dimensional analysis:

.. code-block:: python

    import bspump
    from bspump.matrix import Matrix

    class GeoAnalyzer(bspump.Analyzer):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)
            # 360x180 matrix for lat/lon buckets
            self.matrix = Matrix(app, "GeoMatrix", (360, 180))

        def evaluate(self, context, event):
            lat = int(event.get("latitude", 0) + 90)
            lon = int(event.get("longitude", 0) + 180)
            self.matrix[lat, lon] += 1
            return event

Anomaly Detection
-----------------

Detect anomalies in event streams:

.. code-block:: python

    from bspump.anomaly import Anomaly

    class RateAnomalyDetector(bspump.Analyzer):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)
            self.window = []
            self.window_size = 100

        def evaluate(self, context, event):
            value = event.get("value", 0)
            self.window.append(value)

            if len(self.window) > self.window_size:
                self.window.pop(0)

            if len(self.window) >= self.window_size:
                mean = sum(self.window) / len(self.window)
                std = (sum((x - mean) ** 2 for x in self.window) / len(self.window)) ** 0.5

                if abs(value - mean) > 3 * std:
                    event["anomaly"] = True
                    event["anomaly_score"] = abs(value - mean) / std

            return event

Aggregation Pipeline
--------------------

Build aggregation pipelines:

.. code-block:: python

    class AggregationPipeline(bspump.Pipeline):
        def __init__(self, app, pipeline_id):
            super().__init__(app, pipeline_id)
            self.build(
                bspump.kafka.KafkaSource(app, self, connection="KafkaConnection"),
                HourlyCountAnalyzer(app, self),
                UserSessionAnalyzer(app, self),
                RateAnomalyDetector(app, self),
                bspump.kafka.KafkaSink(app, self, connection="KafkaConnection"),
            )

State Persistence
-----------------

Persist analyzer state for recovery:

.. code-block:: python

    from bspump.matrix import PersistentMatrix

    class PersistentAnalyzer(bspump.Analyzer):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)
            self.matrix = PersistentMatrix(
                app, "PersistentMatrix",
                path="/data/matrix.dat",
                shape=(1000, 1000)
            )

The matrix state is automatically saved and restored on restart.

Configuration
-------------

Configure analyzers in ``pipelines.conf``:

.. code-block:: ini

    [pipeline:AnalysisPipeline:TimeWindowAnalyzer]
    window_size=3600
    resolution=60

    [pipeline:AnalysisPipeline:SessionAnalyzer]
    session_timeout=1800
