Core Concepts
=============

BSPump is built around a composable architecture where data flows through
pipelines consisting of sources, processors, and sinks. Understanding these
core concepts is essential for building effective data pipelines.

.. toctree::
   :maxdepth: 2

   pipeline
   source
   processor
   sink
   connection
   lookup
   trigger

Architecture Overview
---------------------

.. code-block:: text

    ┌─────────────────────────────────────────────────────────────┐
    │                        Application                          │
    │  ┌───────────────────────────────────────────────────────┐  │
    │  │                      Pipeline                         │  │
    │  │                                                       │  │
    │  │   ┌────────┐   ┌───────────┐   ┌───────────┐   ┌────┐ │  │
    │  │   │ Source │──▶│ Processor │──▶│ Processor │──▶│Sink│ │  │
    │  │   └────────┘   └───────────┘   └───────────┘   └────┘ │  │
    │  │                                                       │  │
    │  └───────────────────────────────────────────────────────┘  │
    │                                                             │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
    │  │ Connection  │  │   Lookup    │  │   Trigger   │          │
    │  └─────────────┘  └─────────────┘  └─────────────┘          │
    └─────────────────────────────────────────────────────────────┘

Key Components
--------------

**Pipeline**
    The core abstraction that chains components together. Events flow from
    source through processors to the sink.

**Source**
    Entry point for data. Sources can pull data (polling) or receive data
    (push-based like webhooks). See :doc:`source`.

**Processor**
    Transforms, filters, or enriches events. Multiple processors can be
    chained together. See :doc:`processor`.

**Sink**
    Exit point for data. Sinks write events to external systems, files,
    or other destinations. See :doc:`sink`.

**Connection**
    Shared, reusable connections to external systems (databases, message
    queues, etc.). See :doc:`connection`.

**Lookup**
    Data enrichment tables that can be used to add context to events.
    See :doc:`lookup`.

**Trigger**
    Controls when sources produce events (cron schedules, pub/sub, etc.).
    See :doc:`trigger`.

Event Flow
----------

Events flow through the pipeline in a linear fashion:

1. **Source** generates or receives an event
2. Event passes through each **Processor** in order
3. Each processor can transform, filter, or split the event
4. **Sink** receives the final event and outputs it

Events can be any Python object, but are commonly:

- Bytes (raw data)
- Dictionaries (structured data)
- Dataclasses or typed objects

Async-First Design
------------------

BSPump is built on Python's asyncio, enabling:

- Non-blocking I/O operations
- High concurrency with minimal threads
- Efficient handling of many simultaneous connections
- Natural integration with async libraries
