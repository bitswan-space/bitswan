MQTT Integration
================

BSPump provides MQTT integration through ``bspump.mqtt``.

Installation
------------

.. code-block:: bash

    pip install aiomqtt

Components
----------

- **MQTTConnection**: Shared connection to MQTT broker
- **MQTTSource**: Subscribes to MQTT topics
- **MQTTSink**: Publishes to MQTT topics

MQTTConnection
--------------

.. code-block:: python

    import bspump.mqtt

    connection = bspump.mqtt.MQTTConnection(app, "MQTTConnection")

Configuration:

.. code-block:: ini

    [connection:MQTTConnection]
    host=localhost
    port=1883

    # Authentication (optional)
    username=user
    password=${MQTT_PASSWORD}

    # TLS (optional)
    # tls=true
    # ca_certs=/path/to/ca.pem

MQTTSource
----------

Subscribe to MQTT topics.

.. code-block:: python

    import bspump.mqtt

    source = bspump.mqtt.MQTTSource(
        app, pipeline,
        connection="MQTTConnection"
    )

Configuration:

.. code-block:: ini

    [pipeline:MyPipeline:MQTTSource]
    topic=sensors/#
    # Subscribe to multiple topics
    # topics=sensors/temperature,sensors/humidity

MQTTSink
--------

Publish messages to MQTT topics.

.. code-block:: python

    import bspump.mqtt

    sink = bspump.mqtt.MQTTSink(
        app, pipeline,
        connection="MQTTConnection"
    )

Configuration:

.. code-block:: ini

    [pipeline:MyPipeline:MQTTSink]
    topic=processed/sensors
    qos=1

Complete Example
----------------

.. code-block:: python

    from bspump.jupyter import *
    import bspump.mqtt
    import json

    @register_connection
    def mqtt_connection(app):
        return bspump.mqtt.MQTTConnection(app, "MQTTConnection")

    auto_pipeline(
        source=lambda app, pipeline: bspump.mqtt.MQTTSource(
            app, pipeline, connection="MQTTConnection"
        ),
        sink=lambda app, pipeline: bspump.mqtt.MQTTSink(
            app, pipeline, connection="MQTTConnection"
        ),
        name="MQTTProcessingPipeline",
    )

    # Process MQTT message
    data = json.loads(event.decode("utf-8"))
    data["processed"] = True
    event = json.dumps(data).encode("utf-8")

Topic Wildcards
---------------

MQTT supports wildcard subscriptions:

- ``+`` matches a single level: ``sensors/+/temperature``
- ``#`` matches multiple levels: ``sensors/#``

.. code-block:: ini

    [pipeline:MyPipeline:MQTTSource]
    # Match all sensor topics
    topic=sensors/#

Dynamic Topic Routing
---------------------

Route messages to different topics:

.. code-block:: python

    class TopicRouter(bspump.Processor):
        def process(self, context, event):
            sensor_type = event.get("sensor_type", "unknown")
            context["mqtt_topic"] = f"processed/{sensor_type}"
            return event

QoS Levels
----------

MQTT supports three Quality of Service levels:

- **QoS 0**: At most once (fire and forget)
- **QoS 1**: At least once (acknowledged delivery)
- **QoS 2**: Exactly once (guaranteed delivery)

.. code-block:: ini

    [pipeline:MyPipeline:MQTTSink]
    topic=alerts
    qos=2  # Exactly once for critical messages

Retained Messages
-----------------

Publish retained messages that persist on the broker:

.. code-block:: python

    class RetainProcessor(bspump.Processor):
        def process(self, context, event):
            context["mqtt_retain"] = True
            return event

MQTT Pipeline Inspection
------------------------

BSPump supports MQTT-based pipeline inspection. See :doc:`../advanced/mqtt-visibility`
for details on using MQTT topics to inspect running pipelines.

Configuration Reference
-----------------------

**Connection Options**

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Description
   * - host
     - localhost
     - MQTT broker host
   * - port
     - 1883
     - MQTT broker port
   * - username
     - (empty)
     - Authentication username
   * - password
     - (empty)
     - Authentication password
   * - tls
     - false
     - Enable TLS

**Source Options**

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Description
   * - topic
     - (required)
     - Topic to subscribe to
   * - qos
     - 0
     - Subscription QoS level

**Sink Options**

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Description
   * - topic
     - (required)
     - Topic to publish to
   * - qos
     - 0
     - Publish QoS level
   * - retain
     - false
     - Retain messages
