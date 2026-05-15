bspump.jupyter
==============

Jupyter notebook integration for interactive pipeline development.

.. automodule:: bspump.jupyter
   :members:
   :undoc-members:
   :show-inheritance:

Core Functions
--------------

auto_pipeline
^^^^^^^^^^^^^

Create a pipeline with automatic cell-based processing.

.. code-block:: python

    from bspump.jupyter import auto_pipeline

    auto_pipeline(
        source=lambda app, pipeline: MySource(app, pipeline),
        sink=lambda app, pipeline: MySink(app, pipeline),
        name="MyPipeline",
        processors=[
            lambda app, pipeline: MyProcessor(app, pipeline)
        ]
    )

**Parameters:**

- ``source`` - Lambda returning a Source instance
- ``sink`` - Lambda returning a Sink instance
- ``name`` - Pipeline name
- ``processors`` - Optional list of processor lambdas

Decorators
----------

register_connection
^^^^^^^^^^^^^^^^^^^

Register a connection factory.

.. code-block:: python

    from bspump.jupyter import register_connection

    @register_connection
    def kafka_connection(app):
        return bspump.kafka.KafkaConnection(app, "KafkaConnection")

register_lookup
^^^^^^^^^^^^^^^

Register a lookup factory.

.. code-block:: python

    from bspump.jupyter import register_lookup

    @register_lookup
    def user_lookup(app):
        return bspump.DictionaryLookup(app, "UserLookup", {})

register_app_post_init
^^^^^^^^^^^^^^^^^^^^^^

Register a callback for after app initialization.

.. code-block:: python

    from bspump.jupyter import register_app_post_init

    @register_app_post_init
    def setup(app):
        # Custom initialization
        pass

Pipeline Building
-----------------

new_pipeline
^^^^^^^^^^^^

Start building a pipeline.

.. code-block:: python

    from bspump.jupyter import new_pipeline

    new_pipeline("MyPipeline")

register_source
^^^^^^^^^^^^^^^

Register the pipeline source.

.. code-block:: python

    from bspump.jupyter import register_source

    @register_source
    def source(app, pipeline):
        return MySource(app, pipeline)

register_processor
^^^^^^^^^^^^^^^^^^

Register a processor.

.. code-block:: python

    from bspump.jupyter import register_processor

    @register_processor
    def processor(app, pipeline):
        return MyProcessor(app, pipeline)

register_sink
^^^^^^^^^^^^^

Register the pipeline sink.

.. code-block:: python

    from bspump.jupyter import register_sink

    @register_sink
    def sink(app, pipeline):
        return MySink(app, pipeline)

end_pipeline
^^^^^^^^^^^^

Finalize pipeline building.

.. code-block:: python

    from bspump.jupyter import end_pipeline

    end_pipeline()

Testing
-------

bitswan_test_mode
^^^^^^^^^^^^^^^^^

Enable/disable test mode.

.. code-block:: python

    from bspump.jupyter import bitswan_test_mode

    bitswan_test_mode(enabled=True)

add_test_probe
^^^^^^^^^^^^^^

Add a test probe at a specific point.

.. code-block:: python

    from bspump.jupyter import add_test_probe

    add_test_probe("after_transform")

bitswan_test_probes
^^^^^^^^^^^^^^^^^^^

Dictionary of test probe results.

.. code-block:: python

    from bspump.jupyter import bitswan_test_probes

    results = bitswan_test_probes.get("after_transform", [])

bitswan_tested_pipelines
^^^^^^^^^^^^^^^^^^^^^^^^

Dictionary of tested pipeline results.

.. code-block:: python

    from bspump.jupyter import bitswan_tested_pipelines

    results = bitswan_tested_pipelines.get("MyPipeline")

Sampling
--------

sample_events
^^^^^^^^^^^^^

Configure sample event collection.

.. code-block:: python

    from bspump.jupyter import sample_events

    sample_events(count=10)

retrieve_sample_events
^^^^^^^^^^^^^^^^^^^^^^

Retrieve collected sample events.

.. code-block:: python

    from bspump.jupyter import retrieve_sample_events

    samples = retrieve_sample_events()

Deployment
----------

deploy
^^^^^^

Deploy the notebook as a standalone automation.

.. code-block:: python

    from bspump.jupyter import deploy

    deploy()

Application Access
------------------

App
^^^

Access to the BSPump application instance.

.. code-block:: python

    from bspump.jupyter import App

    svc = App.get_service("bspump.PumpService")
    lookup = svc.locate_lookup("MyLookup")

Cell Processing
---------------

step
^^^^

Process a single step (for explicit control).

.. code-block:: python

    from bspump.jupyter import step

    @step
    def process_step(event):
        event["processed"] = True
        return event

async_step
^^^^^^^^^^

Async version of step.

.. code-block:: python

    from bspump.jupyter import async_step

    @async_step
    async def async_process_step(event):
        result = await fetch_data(event["id"])
        event["data"] = result
        return event
