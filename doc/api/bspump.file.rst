bspump.file
===========

File-based sources and sinks for BSPump.

.. automodule:: bspump.file
   :members:
   :undoc-members:
   :show-inheritance:

Sources
-------

FileLineSource
^^^^^^^^^^^^^^

Reads files line by line.

.. code-block:: python

    import bspump.file

    source = bspump.file.FileLineSource(app, pipeline, config={
        "path": "/data/input.txt"
    })

**Configuration:**

.. code-block:: ini

    [pipeline:MyPipeline:FileLineSource]
    path=/data/input.txt
    encoding=utf-8

FileCSVSource
^^^^^^^^^^^^^

Reads CSV files with automatic parsing.

.. code-block:: python

    source = bspump.file.FileCSVSource(app, pipeline, config={
        "path": "/data/input.csv"
    })

**Configuration:**

.. code-block:: ini

    [pipeline:MyPipeline:FileCSVSource]
    path=/data/input.csv
    delimiter=,
    has_header=true

Each row becomes a dictionary with column names as keys.

FileJSONSource
^^^^^^^^^^^^^^

Reads JSON files.

.. code-block:: python

    source = bspump.file.FileJSONSource(app, pipeline, config={
        "path": "/data/input.json"
    })

Sinks
-----

FileLineSink
^^^^^^^^^^^^

Writes events as lines to a file.

.. code-block:: python

    sink = bspump.file.FileLineSink(app, pipeline, config={
        "path": "/data/output.txt"
    })

**Configuration:**

.. code-block:: ini

    [pipeline:MyPipeline:FileLineSink]
    path=/data/output.txt
    mode=w

**Modes:**

- ``w`` - Write (overwrite)
- ``a`` - Append

FileCSVSink
^^^^^^^^^^^

Writes events as CSV rows.

.. code-block:: python

    sink = bspump.file.FileCSVSink(app, pipeline, config={
        "path": "/data/output.csv"
    })

**Configuration:**

.. code-block:: ini

    [pipeline:MyPipeline:FileCSVSink]
    path=/data/output.csv
    columns=id,name,value
    delimiter=,

Glob Patterns
-------------

Process multiple files:

.. code-block:: ini

    [pipeline:MyPipeline:FileLineSource]
    path=/data/logs/*.log

Configuration Options
---------------------

**Common Source Options:**

- ``path`` - File path or glob pattern
- ``encoding`` - File encoding (default: utf-8)

**CSV Options:**

- ``delimiter`` - Field delimiter (default: ,)
- ``has_header`` - Whether file has header row (default: true)

**Sink Options:**

- ``path`` - Output file path
- ``mode`` - Write mode (w or a)
- ``encoding`` - File encoding (default: utf-8)

Example Pipeline
----------------

.. code-block:: python

    import bspump
    import bspump.file

    class CSVProcessingPipeline(bspump.Pipeline):
        def __init__(self, app, pipeline_id):
            super().__init__(app, pipeline_id)
            self.build(
                bspump.file.FileCSVSource(app, self, config={
                    "path": "/data/input.csv"
                }),
                TransformProcessor(app, self),
                bspump.file.FileCSVSink(app, self, config={
                    "path": "/data/output.csv"
                }),
            )
