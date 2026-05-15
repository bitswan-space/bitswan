Common Patterns
===============

This section covers common patterns for building data pipelines with BSPump.
These patterns are based on real-world usage in production environments.

.. toctree::
   :maxdepth: 2

   webhook-to-kafka
   kafka-processing
   custom-event-source
   scheduled-tasks
   error-recovery

Overview
--------

The patterns in this section demonstrate:

- **Webhook to Kafka**: Receiving HTTP webhooks and forwarding to Kafka
- **Kafka Processing**: Consuming, processing, and producing to Kafka
- **Custom Event Source**: Building custom sources with thread pools
- **Scheduled Tasks**: Running periodic jobs with CronTrigger
- **Error Recovery**: Using Kafka for restart safety

Each pattern includes complete, runnable code examples.

Pattern Selection Guide
-----------------------

.. list-table::
   :header-rows: 1

   * - Use Case
     - Pattern
   * - Receive external HTTP data
     - :doc:`webhook-to-kafka`
   * - Transform streaming data
     - :doc:`kafka-processing`
   * - Poll external systems
     - :doc:`custom-event-source`
   * - Run periodic jobs
     - :doc:`scheduled-tasks`
   * - Handle failures gracefully
     - :doc:`error-recovery`
