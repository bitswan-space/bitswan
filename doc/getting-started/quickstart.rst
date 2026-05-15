Quickstart
==========

This guide will help you build your first BSPump pipeline in 5 minutes.

Your First Pipeline
-------------------

Let's create a simple pipeline that generates random data and prints it.

.. code-block:: python

    import bspump
    import bspump.common
    import bspump.random

    class MyPipeline(bspump.Pipeline):
        def __init__(self, app, pipeline_id):
            super().__init__(app, pipeline_id)
            self.build(
                bspump.random.RandomSource(app, self, choice=['A', 'B', 'C']),
                bspump.common.PPrintSink(app, self),
            )

    if __name__ == '__main__':
        app = bspump.BSPumpApplication()
        svc = app.get_service("bspump.PumpService")
        svc.add_pipeline(MyPipeline(app, "MyPipeline"))
        app.run()

Understanding the Pipeline
--------------------------

Let's break down what's happening:

1. **BSPumpApplication**: The application container that manages the event loop and services.

2. **Pipeline**: A chain of components that process events. Each pipeline has:
   - One **Source**: Generates or receives events
   - Zero or more **Processors**: Transform events
   - One **Sink**: Outputs events

3. **RandomSource**: Generates random events from the provided choices.

4. **PPrintSink**: Pretty-prints events to the console.

Adding a Processor
------------------

Let's add a processor to transform the events:

.. code-block:: python

    import bspump
    import bspump.common
    import bspump.random

    class TransformProcessor(bspump.Processor):
        def process(self, context, event):
            return {"original": event, "transformed": True}

    class MyPipeline(bspump.Pipeline):
        def __init__(self, app, pipeline_id):
            super().__init__(app, pipeline_id)
            self.build(
                bspump.random.RandomSource(app, self, choice=['A', 'B', 'C']),
                TransformProcessor(app, self),
                bspump.common.PPrintSink(app, self),
            )

Using Jupyter Notebooks
-----------------------

BSPump integrates seamlessly with Jupyter notebooks for interactive development:

.. code-block:: python

    from bspump.jupyter import *
    import bspump.common

    auto_pipeline(
        source=lambda app, pipeline: bspump.random.RandomSource(
            app, pipeline, choice=['A', 'B', 'C']
        ),
        sink=lambda app, pipeline: bspump.common.PPrintSink(app, pipeline),
        name="QuickstartPipeline",
    )

In subsequent notebook cells, you can process events:

.. code-block:: python

    # This cell processes each event
    event = {"original": event, "transformed": True}

Next Steps
----------

- Learn about :doc:`../concepts/index` to understand the architecture
- Explore :doc:`../patterns/index` for common use cases
- See :doc:`../integrations/index` for connecting to external systems
