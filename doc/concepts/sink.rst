Sink
====

Sinks are the exit points of a pipeline. They receive processed events and
write them to external systems, files, or other destinations.

Basic Sink
----------

A sink implements the ``process`` method:

.. code-block:: python

    import bspump

    class MySink(bspump.Sink):
        def process(self, context, event):
            # Write event to destination
            self.write_to_database(event)

Async Sinks
-----------

For I/O-bound operations, use async sinks:

.. code-block:: python

    class AsyncSink(bspump.Sink):
        async def process(self, context, event):
            await self.async_write(event)

Built-in Sinks
--------------

BSPump includes many built-in sinks:

**Debug/Development**

.. code-block:: python

    import bspump.common

    # Pretty print events to console
    sink = bspump.common.PPrintSink(app, pipeline)

    # Null sink (discard events)
    sink = bspump.common.NullSink(app, pipeline)

**Kafka**

.. code-block:: python

    import bspump.kafka

    sink = bspump.kafka.KafkaSink(
        app, pipeline,
        connection="KafkaConnection"
    )

**HTTP**

.. code-block:: python

    import bspump.http.client

    sink = bspump.http.client.HTTPClientSink(
        app, pipeline,
        config={"url": "https://api.example.com/events"}
    )

**File Output**

.. code-block:: python

    import bspump.file

    # Line-by-line output
    sink = bspump.file.FileLineSink(app, pipeline, config={
        "path": "/data/output.txt"
    })

See :doc:`../integrations/index` for the full list of available sinks.

Batching
--------

Some sinks support batching for efficiency:

.. code-block:: python

    sink = bspump.kafka.KafkaSink(
        app, pipeline,
        connection="KafkaConnection",
        config={
            "batch_size": 100,
            "batch_timeout": 1.0  # seconds
        }
    )

The sink will accumulate events and write them in batches.

Backpressure
------------

Sinks can signal backpressure to the pipeline when they cannot keep up:

.. code-block:: python

    class SlowSink(bspump.Sink):
        async def process(self, context, event):
            # If the destination is slow, this creates backpressure
            await self.slow_write(event)

When backpressure occurs, the pipeline throttles the source.

Error Handling
--------------

Handle sink errors appropriately:

.. code-block:: python

    class ResilientSink(bspump.Sink):
        async def process(self, context, event):
            for attempt in range(3):
                try:
                    await self.write(event)
                    return
                except ConnectionError:
                    await asyncio.sleep(1 * attempt)

            # After retries, handle failure
            await self.send_to_dead_letter_queue(event)

Multiple Outputs
----------------

To send events to multiple destinations, use a routing processor
or multiple pipelines sharing a source.

Sink Configuration
------------------

Sinks can be configured via ``pipelines.conf``:

.. code-block:: ini

    [pipeline:MyPipeline:MySink]
    url=https://api.example.com/events
    batch_size=100
    timeout=30
