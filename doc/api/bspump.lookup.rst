bspump.lookup
=============

Lookup tables for data enrichment.

.. automodule:: bspump.lookup
   :members:
   :undoc-members:
   :show-inheritance:

Base Classes
------------

Lookup
^^^^^^

Base class for all lookups.

.. code-block:: python

    import bspump

    class MyLookup(bspump.Lookup):
        def get(self, key):
            return self.data.get(key)

DictionaryLookup
^^^^^^^^^^^^^^^^

Simple dictionary-based lookup.

.. code-block:: python

    lookup = bspump.DictionaryLookup(app, "StatusLookup", {
        "1": "active",
        "2": "inactive",
        "3": "pending"
    })

MappingLookup
^^^^^^^^^^^^^

Lookup with set/get operations.

.. code-block:: python

    lookup = bspump.MappingLookup(app, "MappingLookup")
    lookup.set("key1", {"field": "value"})
    lookup.set("key2", {"field": "other"})

File-based Lookups
------------------

JSONLookup
^^^^^^^^^^

Load lookup data from JSON file.

.. code-block:: python

    import bspump.lookup

    lookup = bspump.lookup.JSONLookup(app, "JSONLookup", config={
        "path": "/data/lookup.json"
    })

CSVLookup
^^^^^^^^^

Load lookup data from CSV file.

.. code-block:: python

    lookup = bspump.lookup.CSVLookup(app, "CSVLookup", config={
        "path": "/data/lookup.csv",
        "key_column": "id"
    })

Using Lookups
-------------

Access lookups in processors:

.. code-block:: python

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

Registering Lookups
-------------------

.. code-block:: python

    app = bspump.BSPumpApplication()
    svc = app.get_service("bspump.PumpService")

    lookup = bspump.DictionaryLookup(app, "StatusLookup", {
        "1": "active",
        "2": "inactive"
    })
    svc.add_lookup(lookup)

Jupyter Registration
--------------------

.. code-block:: python

    from bspump.jupyter import register_lookup

    @register_lookup
    def user_lookup(app):
        return bspump.DictionaryLookup(app, "UserLookup", {
            "u1": {"name": "Alice"},
            "u2": {"name": "Bob"}
        })

Configuration
-------------

.. code-block:: ini

    [lookup:JSONLookup]
    path=/data/lookup.json
    reload_interval=3600

Custom Lookups
--------------

.. code-block:: python

    class RedisLookup(bspump.Lookup):
        def __init__(self, app, lookup_id, redis_client):
            super().__init__(app, lookup_id)
            self.redis = redis_client

        def get(self, key):
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None

        def set(self, key, value):
            self.redis.set(key, json.dumps(value))
