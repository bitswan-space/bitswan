File Integration
================

BSPump provides file-based sources and sinks for processing CSV, JSON,
and line-based files.

Components
----------

- **FileLineSource**: Reads files line by line
- **FileCSVSource**: Reads CSV files
- **FileJSONSource**: Reads JSON files
- **FileLineSink**: Writes files line by line
- **FileCSVSink**: Writes CSV files

FileLineSource
--------------

Reads a file line by line.

.. code-block:: python

    import bspump.file

    source = bspump.file.FileLineSource(app, pipeline, config={
        "path": "/data/input.txt"
    })

Configuration:

.. code-block:: ini

    [pipeline:MyPipeline:FileLineSource]
    path=/data/input.txt
    # Encoding (optional)
    encoding=utf-8

FileCSVSource
-------------

Reads CSV files with automatic parsing.

.. code-block:: python

    import bspump.file

    source = bspump.file.FileCSVSource(app, pipeline, config={
        "path": "/data/input.csv"
    })

Configuration:

.. code-block:: ini

    [pipeline:MyPipeline:FileCSVSource]
    path=/data/input.csv
    # CSV options
    delimiter=,
    has_header=true

Each row becomes a dictionary with column names as keys.

FileJSONSource
--------------

Reads JSON files (one object per line or array).

.. code-block:: python

    import bspump.file

    source = bspump.file.FileJSONSource(app, pipeline, config={
        "path": "/data/input.json"
    })

Configuration:

.. code-block:: ini

    [pipeline:MyPipeline:FileJSONSource]
    path=/data/input.json

FileLineSink
------------

Writes events to a file, one per line.

.. code-block:: python

    import bspump.file

    sink = bspump.file.FileLineSink(app, pipeline, config={
        "path": "/data/output.txt"
    })

Configuration:

.. code-block:: ini

    [pipeline:MyPipeline:FileLineSink]
    path=/data/output.txt
    mode=w  # w for write, a for append

FileCSVSink
-----------

Writes events as CSV rows.

.. code-block:: python

    import bspump.file

    sink = bspump.file.FileCSVSink(app, pipeline, config={
        "path": "/data/output.csv"
    })

Configuration:

.. code-block:: ini

    [pipeline:MyPipeline:FileCSVSink]
    path=/data/output.csv
    delimiter=,
    # Columns to write (optional, defaults to all keys)
    columns=id,name,value

Complete Example
----------------

Process a CSV file and output results:

.. code-block:: python

    from bspump.jupyter import *
    import bspump.file

    auto_pipeline(
        source=lambda app, pipeline: bspump.file.FileCSVSource(
            app, pipeline, config={"path": "/data/input.csv"}
        ),
        sink=lambda app, pipeline: bspump.file.FileCSVSink(
            app, pipeline, config={"path": "/data/output.csv"}
        ),
        name="CSVProcessingPipeline",
    )

    # Process each row (event is a dict with column names as keys)
    event["processed"] = True
    event["value"] = float(event["value"]) * 2

Glob Patterns
-------------

Process multiple files using glob patterns:

.. code-block:: ini

    [pipeline:MyPipeline:FileLineSource]
    path=/data/logs/*.log

File Watching
-------------

Watch for new files in a directory:

.. code-block:: python

    import bspump.file

    source = bspump.file.FileWatchSource(app, pipeline, config={
        "path": "/data/incoming/",
        "pattern": "*.csv"
    })

Processing Large Files
----------------------

For large files, use streaming:

.. code-block:: python

    class StreamingSource(bspump.file.FileLineSource):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)
            # Process in chunks
            self.batch_size = 1000

Temporary Files
---------------

Write to temporary files and move on completion:

.. code-block:: python

    import bspump.file
    import shutil

    class SafeFileSink(bspump.file.FileLineSink):
        def __init__(self, app, pipeline, id=None, config=None):
            self.final_path = config.get("path")
            config["path"] = self.final_path + ".tmp"
            super().__init__(app, pipeline, id, config)

        async def on_completed(self):
            shutil.move(self.path, self.final_path)

Configuration Reference
-----------------------

**Source Options**

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Description
   * - path
     - (required)
     - File path or glob pattern
   * - encoding
     - utf-8
     - File encoding
   * - delimiter
     - , (CSV only)
     - CSV delimiter
   * - has_header
     - true (CSV only)
     - Whether CSV has header row

**Sink Options**

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Description
   * - path
     - (required)
     - Output file path
   * - mode
     - w
     - Write mode (w or a)
   * - encoding
     - utf-8
     - File encoding
