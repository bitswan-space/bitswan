Testing and Development
=======================

BSPump notebooks support interactive testing during development.

Interactive Testing
-------------------

Define test events before ``auto_pipeline`` to test your processing logic:

.. code-block:: python

    # Imports and connections
    from bspump.jupyter import *
    import bspump.kafka
    import json

    @register_connection
    def connection(app):
        return bspump.kafka.KafkaConnection(app, "KafkaConnection")

    # TEST EVENT - Define sample data for development
    event = json.dumps({
        "id": "test-123",
        "sender": "+1234567890",
        "recipient": "+0987654321",
        "subject": "Test Fax"
    }).encode("utf8")

.. code-block:: python

    auto_pipeline(
        source=lambda app, pipeline: bspump.kafka.KafkaSource(
            app, pipeline, connection="KafkaConnection"
        ),
        sink=lambda app, pipeline: bspump.kafka.KafkaSink(
            app, pipeline, connection="KafkaConnection"
        ),
        name="TestPipeline",
    )

.. code-block:: python

    # Processing - test with the sample event above
    data = json.loads(event.decode("utf8"))
    print(f"Processing: {data}")

    data["processed"] = True
    event = json.dumps(data).encode("utf8")

Now you can run the processing cells to test with your sample data.

Ignore Cells
------------

Cells that should not be deployed can be marked with ``#ignore``:

.. code-block:: python

    #ignore
    import os
    os.chdir("/home/coder/workspace/my-pipeline")

.. code-block:: python

    #ignore
    # Install development dependencies
    import sys
    !{sys.executable} -m pip install some-package

.. code-block:: python

    #ignore
    # Load secrets for local development
    from dotenv import load_dotenv
    load_dotenv("../secrets/dev")

These cells run in Jupyter but are excluded from the deployed automation.

Loading Secrets Locally
-----------------------

For local development, load secrets manually:

.. code-block:: python

    #ignore
    from dotenv import load_dotenv
    import os

    # Load multiple secret groups
    groups = ["kafka", "api", "discord"]
    for group in groups:
        secrets_path = os.path.join(
            os.environ.get("BITSWAN_GITOPS_DIR", ".."),
            "secrets",
            group
        )
        if os.path.exists(secrets_path):
            load_dotenv(secrets_path)

In production, secrets are loaded automatically based on ``automation.toml``.

Debugging Output
----------------

Use ``print()`` for debugging - output appears in Jupyter and in logs:

.. code-block:: python

    data = json.loads(event.decode("utf8"))
    print(f"Received event: {data['id']}")
    print(f"Sender: {data['sender']}")
    print(f"Recipient: {data['recipient']}")

    # Processing...
    data["processed"] = True
    print(f"Processed successfully")

    event = json.dumps(data).encode("utf8")

Using PPrintSink for Development
--------------------------------

For scheduled tasks or debugging, use ``PPrintSink`` to see output:

.. code-block:: python

    auto_pipeline(
        source=lambda app, pipeline: ScheduledSource(app, pipeline).on(
            CronTrigger(app, "*/5 * * * *")
        ),
        sink=lambda app, pipeline: bspump.common.PPrintSink(app, pipeline),
        name="DebugPipeline",
    )

Error Handling
--------------

Handle errors gracefully in your processing:

.. code-block:: python

    import json

    try:
        data = json.loads(event.decode("utf8"))
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        event = None  # Drop invalid events

.. code-block:: python

    # Continue only if event wasn't dropped
    if event is None:
        pass  # Skip remaining processing
    else:
        # Process valid event
        data["validated"] = True
        event = json.dumps(data).encode("utf8")

For critical errors that should alert operators:

.. code-block:: python

    import requests
    import os

    def send_alert(message):
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        requests.post(webhook_url, json={"content": message})

    try:
        result = risky_operation(data)
    except Exception as e:
        send_alert(f"Pipeline error: {e}")
        event = None  # Drop event after alerting

Testing Async Operations
------------------------

Async operations work directly in notebook cells:

.. code-block:: python

    import aiohttp

    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.example.com/status") as response:
            status = await response.json()
            print(f"API Status: {status}")

    event["api_status"] = status

You can also use ``await`` directly:

.. code-block:: python

    import asyncio

    # Wait before processing (e.g., for rate limiting)
    if data.get("requeue"):
        await asyncio.sleep(60 * 5)  # Wait 5 minutes

    # Continue processing
    event = json.dumps(data).encode("utf8")
