Lookup
======

Lookups provide data enrichment capabilities. They allow you to add context
to events by looking up related data from various sources.

What are Lookups?
-----------------

Lookups are key-value stores that can be:

- Loaded from files (JSON, CSV)
- Populated from databases
- Built dynamically at runtime
- Shared across pipelines

Using Lookups
-------------

Access lookups in processors:

.. code-block:: python

    import bspump

    class EnrichProcessor(bspump.Processor):
        def __init__(self, app, pipeline, id=None, config=None):
            super().__init__(app, pipeline, id, config)
            svc = app.get_service("bspump.PumpService")
            self.lookup = svc.locate_lookup("UserLookup")

        def process(self, context, event):
            user_id = event.get("user_id")
            user_info = self.lookup.get(user_id)
            if user_info:
                event["user_name"] = user_info.get("name")
            return event

Built-in Lookup Types
---------------------

**DictionaryLookup**

Simple in-memory key-value lookup:

.. code-block:: python

    import bspump

    lookup = bspump.DictionaryLookup(app, "StatusLookup", {
        "1": "active",
        "2": "inactive",
        "3": "pending"
    })

**MappingLookup**

For more complex mapping scenarios:

.. code-block:: python

    import bspump

    lookup = bspump.MappingLookup(app, "MappingLookup")
    lookup.set("key1", {"field": "value"})

Loading from Files
------------------

Load lookup data from external files:

.. code-block:: python

    import bspump.lookup

    # Load from JSON file
    lookup = bspump.lookup.JSONLookup(app, "JSONLookup", config={
        "path": "/data/lookup.json"
    })

    # Load from CSV file
    lookup = bspump.lookup.CSVLookup(app, "CSVLookup", config={
        "path": "/data/lookup.csv",
        "key_column": "id"
    })

Database-backed Lookups
-----------------------

Lookups can be populated from databases:

.. code-block:: python

    import bspump.postgresql

    lookup = bspump.postgresql.PostgreSQLLookup(
        app, "PostgreSQLLookup",
        connection="PostgreSQLConnection",
        config={
            "query": "SELECT id, name, email FROM users",
            "key": "id"
        }
    )

Registering Lookups
-------------------

Register lookups with the application:

.. code-block:: python

    app = bspump.BSPumpApplication()
    svc = app.get_service("bspump.PumpService")

    lookup = bspump.DictionaryLookup(app, "StatusLookup", {
        "1": "active",
        "2": "inactive"
    })
    svc.add_lookup(lookup)

Jupyter Lookup Registration
---------------------------

In Jupyter notebooks:

.. code-block:: python

    from bspump.jupyter import *

    @register_lookup
    def status_lookup(app):
        return bspump.DictionaryLookup(app, "StatusLookup", {
            "1": "active",
            "2": "inactive"
        })

Lookup Updates
--------------

Lookups can be updated at runtime:

.. code-block:: python

    class DynamicLookup(bspump.MappingLookup):
        async def load(self):
            # Reload data periodically
            data = await self.fetch_latest_data()
            self.clear()
            for key, value in data.items():
                self.set(key, value)

Lookup Configuration
--------------------

Configure lookups in ``pipelines.conf``:

.. code-block:: ini

    [lookup:StatusLookup]
    path=/data/status.json
    reload_interval=3600

Custom Lookups
--------------

Create custom lookups for specialized needs:

.. code-block:: python

    import bspump

    class RedisLookup(bspump.Lookup):
        def __init__(self, app, lookup_id, redis_connection):
            super().__init__(app, lookup_id)
            self.redis = redis_connection

        def get(self, key):
            return self.redis.get(key)

        def set(self, key, value):
            self.redis.set(key, value)
