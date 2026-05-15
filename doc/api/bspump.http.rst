bspump.http
===========

HTTP integration for BSPump, including webhook sources and HTTP client sinks.

bspump.http.web
---------------

Web/webhook components.

.. automodule:: bspump.http.web
   :members:
   :undoc-members:
   :show-inheritance:

WebHookSource
^^^^^^^^^^^^^

Receives HTTP POST requests as events.

.. code-block:: python

    import bspump.http.web

    source = bspump.http.web.WebHookSource(
        app, pipeline,
        config={"path": "/webhook", "port": 8080}
    )

**Configuration:**

.. code-block:: ini

    [pipeline:MyPipeline:WebHookSource]
    path=/webhook
    port=8080
    host=0.0.0.0

**Options:**

- ``path`` - URL path for the endpoint
- ``port`` - HTTP port to listen on
- ``host`` - Host to bind to

**Context Keys:**

The source adds these to the event context:

- ``http_method`` - HTTP method (POST)
- ``http_path`` - Request path
- ``http_query`` - Query parameters
- ``headers`` - Request headers
- ``remote_addr`` - Client IP address

bspump.http.client
------------------

HTTP client components.

.. automodule:: bspump.http.client
   :members:
   :undoc-members:
   :show-inheritance:

HTTPClientSink
^^^^^^^^^^^^^^

Sends events to HTTP endpoints.

.. code-block:: python

    import bspump.http.client

    sink = bspump.http.client.HTTPClientSink(
        app, pipeline,
        config={"url": "https://api.example.com/events"}
    )

**Configuration:**

.. code-block:: ini

    [pipeline:MyPipeline:HTTPClientSink]
    url=https://api.example.com/events
    method=POST
    timeout=30

**Options:**

- ``url`` - Target URL
- ``method`` - HTTP method (POST, PUT, etc.)
- ``timeout`` - Request timeout in seconds
- ``headers`` - JSON object of headers

**Dynamic URL:**

Set the URL dynamically:

.. code-block:: python

    def process(self, context, event):
        context["http_url"] = f"https://api.example.com/users/{event['id']}"
        return event

Example Pipeline
----------------

Webhook to HTTP forwarding:

.. code-block:: python

    import bspump
    import bspump.http.web
    import bspump.http.client

    class ForwardingPipeline(bspump.Pipeline):
        def __init__(self, app, pipeline_id):
            super().__init__(app, pipeline_id)
            self.build(
                bspump.http.web.WebHookSource(app, self, config={
                    "path": "/webhook",
                    "port": 8080
                }),
                TransformProcessor(app, self),
                bspump.http.client.HTTPClientSink(app, self, config={
                    "url": "https://api.example.com/events"
                }),
            )
