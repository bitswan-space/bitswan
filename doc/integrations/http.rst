HTTP Integration
================

BSPump provides HTTP capabilities through webhook sources and HTTP client sinks.

Components
----------

- **WebHookSource**: Receives HTTP POST requests (``bspump.http.web``)
- **HTTPClientSink**: Sends HTTP requests (``bspump.http.client``)

WebHookSource
-------------

Receives incoming HTTP webhooks.

.. code-block:: python

    import bspump.http.web

    source = bspump.http.web.WebHookSource(
        app, pipeline,
        config={"path": "/webhook", "port": 8080}
    )

Configuration:

.. code-block:: ini

    [pipeline:MyPipeline:WebHookSource]
    path=/webhook
    port=8080
    host=0.0.0.0

Multiple Endpoints
------------------

Create multiple webhook endpoints:

.. code-block:: python

    class Pipeline1(bspump.Pipeline):
        def __init__(self, app, pipeline_id):
            super().__init__(app, pipeline_id)
            self.build(
                bspump.http.web.WebHookSource(app, self, config={
                    "path": "/api/v1/events",
                    "port": 8080
                }),
                MySink(app, self),
            )

    class Pipeline2(bspump.Pipeline):
        def __init__(self, app, pipeline_id):
            super().__init__(app, pipeline_id)
            self.build(
                bspump.http.web.WebHookSource(app, self, config={
                    "path": "/api/v1/notifications",
                    "port": 8080
                }),
                MySink(app, self),
            )

HTTPClientSink
--------------

Sends events to HTTP endpoints.

.. code-block:: python

    import bspump.http.client

    sink = bspump.http.client.HTTPClientSink(
        app, pipeline,
        config={"url": "https://api.example.com/events"}
    )

Configuration:

.. code-block:: ini

    [pipeline:MyPipeline:HTTPClientSink]
    url=https://api.example.com/events
    method=POST
    timeout=30

    # Headers (optional)
    headers={"Content-Type": "application/json", "Authorization": "Bearer ${API_TOKEN}"}

Webhook Validation
------------------

Validate incoming webhooks:

.. code-block:: python

    import hmac
    import hashlib

    class WebhookValidator(bspump.Processor):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)
            self.secret = os.environ.get("WEBHOOK_SECRET")

        def process(self, context, event):
            signature = context.get("headers", {}).get("X-Signature")
            if not self.verify_signature(event, signature):
                return None  # Drop invalid requests
            return event

        def verify_signature(self, payload, signature):
            expected = hmac.new(
                self.secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected, signature)

Complete Webhook Example
------------------------

.. code-block:: python

    from bspump.jupyter import *
    import bspump.http.web
    import bspump.kafka
    import json

    @register_connection
    def kafka_connection(app):
        return bspump.kafka.KafkaConnection(app, "KafkaConnection")

    auto_pipeline(
        source=lambda app, pipeline: bspump.http.web.WebHookSource(
            app, pipeline,
            config={"path": "/webhook", "port": 8080}
        ),
        sink=lambda app, pipeline: bspump.kafka.KafkaSink(
            app, pipeline, connection="KafkaConnection"
        ),
        name="WebhookPipeline",
    )

    # Parse incoming JSON
    event = json.loads(event.decode("utf-8"))

    # Add metadata
    event["received_at"] = datetime.now().isoformat()

    # Serialize
    event = json.dumps(event).encode("utf-8")

HTTP Client for Data Fetching
-----------------------------

Use aiohttp for fetching data in processors:

.. code-block:: python

    import bspump
    import aiohttp

    class EnrichmentProcessor(bspump.Processor):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)
            self.session = None

        async def process(self, context, event):
            if self.session is None:
                self.session = aiohttp.ClientSession()

            user_id = event.get("user_id")
            async with self.session.get(f"https://api.example.com/users/{user_id}") as resp:
                user_data = await resp.json()
                event["user"] = user_data

            return event

Configuration Reference
-----------------------

**WebHookSource Options**

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Description
   * - path
     - /
     - URL path for the webhook endpoint
   * - port
     - 8080
     - HTTP port to listen on
   * - host
     - 0.0.0.0
     - Host to bind to

**HTTPClientSink Options**

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Description
   * - url
     - (required)
     - Target URL
   * - method
     - POST
     - HTTP method
   * - timeout
     - 30
     - Request timeout in seconds
