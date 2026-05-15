Configuration
=============

BSPump uses a layered configuration system supporting configuration files,
environment variables, and programmatic configuration.

.. toctree::
   :maxdepth: 2

   pipelines-conf
   secrets

Configuration Sources
---------------------

BSPump loads configuration from multiple sources in order of precedence:

1. **Command-line arguments**: Highest priority
2. **Environment variables**: ``BSPUMP_*`` prefix
3. **Configuration files**: ``pipelines.conf``, ``*.conf``
4. **Default values**: Built into components

Configuration File Format
-------------------------

BSPump uses INI-style configuration files:

.. code-block:: ini

    [section:name]
    key=value
    another_key=another value

    # Comments start with #
    ; Or with semicolon

Section Naming
--------------

Sections follow naming patterns:

- ``[connection:ConnectionId]`` - Connection configuration
- ``[pipeline:PipelineName]`` - Pipeline-level configuration
- ``[pipeline:PipelineName:ComponentId]`` - Component configuration
- ``[lookup:LookupId]`` - Lookup configuration

Example:

.. code-block:: ini

    [connection:KafkaConnection]
    bootstrap_servers=kafka:9092

    [pipeline:MyPipeline]
    max_concurrent=10

    [pipeline:MyPipeline:KafkaSource]
    topic=input-events

    [lookup:UserLookup]
    path=/data/users.json

Environment Variable Substitution
---------------------------------

Use ``${VAR}`` syntax for environment variables:

.. code-block:: ini

    [connection:PostgreSQLConnection]
    host=${POSTGRES_HOST}
    password=${POSTGRES_PASSWORD}

Default values:

.. code-block:: ini

    [connection:PostgreSQLConnection]
    host=${POSTGRES_HOST:-localhost}
    port=${POSTGRES_PORT:-5432}

Loading Configuration
---------------------

Specify configuration files at startup:

.. code-block:: bash

    python app.py -c pipelines.conf -c secrets.conf

Or in code:

.. code-block:: python

    app = bspump.BSPumpApplication()
    app.Config.read("pipelines.conf")

Accessing Configuration
-----------------------

Access configuration in components:

.. code-block:: python

    class MyProcessor(bspump.Processor):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)

            # Access configuration
            self.threshold = self.Config.getint("threshold", 100)
            self.enabled = self.Config.getboolean("enabled", True)
            self.rate = self.Config.getfloat("rate", 1.0)

Configuration Methods
---------------------

.. py:method:: Config.get(key, default=None)

   Get a string value.

.. py:method:: Config.getint(key, default=0)

   Get an integer value.

.. py:method:: Config.getfloat(key, default=0.0)

   Get a float value.

.. py:method:: Config.getboolean(key, default=False)

   Get a boolean value (true/false, yes/no, 1/0).
