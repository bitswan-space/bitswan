bspump.mqtt
===========

MQTT integration for BSPump.

.. automodule:: bspump.mqtt
   :members:
   :undoc-members:
   :show-inheritance:

MQTTConnection
--------------

Connection to MQTT broker.

.. code-block:: python

    import bspump.mqtt

    connection = bspump.mqtt.MQTTConnection(app, "MQTTConnection")

**Configuration:**

.. code-block:: ini

    [connection:MQTTConnection]
    host=localhost
    port=1883
    username=user
    password=${MQTT_PASSWORD}

**Options:**

- ``host`` - MQTT broker host
- ``port`` - MQTT broker port (default: 1883)
- ``username`` - Authentication username
- ``password`` - Authentication password
- ``tls`` - Enable TLS (true/false)
- ``ca_certs`` - Path to CA certificate

MQTTSource
----------

Subscribes to MQTT topics.

.. code-block:: python

    source = bspump.mqtt.MQTTSource(
        app, pipeline,
        connection="MQTTConnection"
    )

**Configuration:**

.. code-block:: ini

    [pipeline:MyPipeline:MQTTSource]
    topic=sensors/#
    qos=1

**Options:**

- ``topic`` - Topic to subscribe to
- ``topics`` - Comma-separated list of topics
- ``qos`` - Quality of Service (0, 1, 2)

**Wildcards:**

- ``+`` - Single level: ``sensors/+/temperature``
- ``#`` - Multi level: ``sensors/#``

MQTTSink
--------

Publishes messages to MQTT topics.

.. code-block:: python

    sink = bspump.mqtt.MQTTSink(
        app, pipeline,
        connection="MQTTConnection"
    )

**Configuration:**

.. code-block:: ini

    [pipeline:MyPipeline:MQTTSink]
    topic=processed/sensors
    qos=1
    retain=false

**Options:**

- ``topic`` - Topic to publish to
- ``qos`` - Quality of Service (0, 1, 2)
- ``retain`` - Retain messages (true/false)

Dynamic Topic
-------------

.. code-block:: python

    class TopicRouter(bspump.Processor):
        def process(self, context, event):
            context["mqtt_topic"] = f"sensors/{event['sensor_id']}"
            return event

Retained Messages
-----------------

.. code-block:: python

    class RetainProcessor(bspump.Processor):
        def process(self, context, event):
            context["mqtt_retain"] = True
            return event

Example Pipeline
----------------

.. code-block:: python

    import bspump
    import bspump.mqtt

    class MQTTProcessingPipeline(bspump.Pipeline):
        def __init__(self, app, pipeline_id):
            super().__init__(app, pipeline_id)
            self.build(
                bspump.mqtt.MQTTSource(app, self, connection="MQTTConnection"),
                ParseProcessor(app, self),
                bspump.mqtt.MQTTSink(app, self, connection="MQTTConnection"),
            )
