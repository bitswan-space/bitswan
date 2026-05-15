Pipeline
========

A Pipeline is the core abstraction in BSPump. It defines how events flow
from a source, through processors, to a sink.

Basic Pipeline Structure
------------------------

Every pipeline consists of:

- Exactly one **Source** (first component)
- Zero or more **Processors** (middle components)
- Exactly one **Sink** (last component)

.. code-block:: python

    import bspump

    class MyPipeline(bspump.Pipeline):
        def __init__(self, app, pipeline_id):
            super().__init__(app, pipeline_id)
            self.build(
                MySource(app, self),
                ProcessorA(app, self),
                ProcessorB(app, self),
                MySink(app, self),
            )

Pipeline Lifecycle
------------------

Pipelines go through several lifecycle states:

1. **Created**: Pipeline is instantiated but not started
2. **Ready**: Pipeline is ready to process events
3. **Running**: Actively processing events
4. **Throttled**: Temporarily paused due to backpressure
5. **Stopped**: Pipeline has been shut down

Pipeline Methods
----------------

.. py:method:: Pipeline.build(*components)

    Builds the pipeline with the specified components.

    :param components: Source, Processors, and Sink in order

.. py:method:: Pipeline.ready()

    Coroutine that resolves when the pipeline is ready to process.

    .. code-block:: python

        async def cycle(self):
            await self.Pipeline.ready()
            # Pipeline is now ready

.. py:method:: Pipeline.process(event, context=None)

    Processes an event through the pipeline.

    :param event: The event to process
    :param context: Optional context dictionary

Throttling and Backpressure
---------------------------

BSPump implements backpressure through throttling. When a sink or processor
cannot keep up with the event rate, the pipeline throttles:

.. code-block:: python

    class SlowProcessor(bspump.Processor):
        def process(self, context, event):
            # This might cause throttling if too slow
            time.sleep(0.1)
            return event

The source is automatically paused when the pipeline is throttled.

Pipeline Configuration
----------------------

Pipelines can be configured via the ``pipelines.conf`` file:

.. code-block:: ini

    [pipeline:MyPipeline]
    # Pipeline-specific settings

See :doc:`../configuration/pipelines-conf` for detailed configuration options.

Working with Multiple Pipelines
-------------------------------

An application can run multiple pipelines simultaneously:

.. code-block:: python

    app = bspump.BSPumpApplication()
    svc = app.get_service("bspump.PumpService")

    svc.add_pipeline(PipelineA(app, "PipelineA"))
    svc.add_pipeline(PipelineB(app, "PipelineB"))
    svc.add_pipeline(PipelineC(app, "PipelineC"))

    app.run()

Each pipeline operates independently with its own event stream.
