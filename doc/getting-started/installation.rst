Installation
============

Requirements
------------

BSPump requires Python 3.8 or higher. The framework is built on asyncio and
uses modern Python features for optimal performance.

Installing BSPump
-----------------

Install BSPump using pip:

.. code-block:: bash

    pip install bspump

For development installations with all optional dependencies:

.. code-block:: bash

    pip install bspump[dev]

Optional Dependencies
---------------------

BSPump supports various integrations that require additional packages:

**Kafka Integration**

.. code-block:: bash

    pip install aiokafka

**PostgreSQL Integration**

.. code-block:: bash

    pip install asyncpg

**MongoDB Integration**

.. code-block:: bash

    pip install motor

**Elasticsearch Integration**

.. code-block:: bash

    pip install elasticsearch[async]

**MQTT Integration**

.. code-block:: bash

    pip install aiomqtt

Verifying Installation
----------------------

Verify your installation by importing BSPump:

.. code-block:: python

    import bspump
    print(bspump.__version__)

You should see the version number printed without any errors.

Next Steps
----------

Once installed, proceed to the :doc:`quickstart` guide to build your first pipeline.
