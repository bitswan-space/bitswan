API Reference
=============

This section provides comprehensive API documentation for all BSPump modules.

.. toctree::
   :maxdepth: 2

   bspump
   bspump.abc
   bspump.common
   bspump.kafka
   bspump.http
   bspump.postgresql
   bspump.mongodb
   bspump.elasticsearch
   bspump.mqtt
   bspump.file
   bspump.trigger
   bspump.lookup
   bspump.analyzer
   bspump.matrix
   bspump.jupyter

Core Modules
------------

.. list-table::
   :header-rows: 1

   * - Module
     - Description
   * - :doc:`bspump`
     - Main module with Application, Pipeline, Service
   * - :doc:`bspump.abc`
     - Abstract base classes: Source, Processor, Sink, Connection
   * - :doc:`bspump.common`
     - Common utilities and processors
   * - :doc:`bspump.trigger`
     - Triggers: CronTrigger, PubSubTrigger, etc.
   * - :doc:`bspump.lookup`
     - Lookup tables for data enrichment
   * - :doc:`bspump.analyzer`
     - Analyzers for aggregation and statistics
   * - :doc:`bspump.matrix`
     - Matrix data structures
   * - :doc:`bspump.jupyter`
     - Jupyter notebook integration

Integration Modules
-------------------

.. list-table::
   :header-rows: 1

   * - Module
     - Description
   * - :doc:`bspump.kafka`
     - Apache Kafka integration
   * - :doc:`bspump.http`
     - HTTP webhook and client
   * - :doc:`bspump.postgresql`
     - PostgreSQL database
   * - :doc:`bspump.mongodb`
     - MongoDB database
   * - :doc:`bspump.elasticsearch`
     - Elasticsearch
   * - :doc:`bspump.mqtt`
     - MQTT messaging
   * - :doc:`bspump.file`
     - File-based sources and sinks

Additional Modules
------------------

BSPump also includes these modules (see source code for details):

- ``bspump.amqp`` - AMQP/RabbitMQ integration
- ``bspump.influxdb`` - InfluxDB time-series database
- ``bspump.mysql`` - MySQL database
- ``bspump.odbc`` - ODBC database connections
- ``bspump.ftp`` - FTP file transfer
- ``bspump.ssh`` - SSH/SFTP connections
- ``bspump.slack`` - Slack integration
- ``bspump.googledrive`` - Google Drive integration
- ``bspump.ldap`` - LDAP directory services
- ``bspump.zookeeper`` - Apache ZooKeeper
- ``bspump.crypto`` - Cryptographic processors
- ``bspump.declarative`` - Declarative expressions
- ``bspump.aggregation`` - Aggregation utilities
- ``bspump.anomaly`` - Anomaly detection
- ``bspump.cache`` - Caching utilities
- ``bspump.filter`` - Filtering processors
- ``bspump.integrity`` - Data integrity checks
- ``bspump.random`` - Random data generation
- ``bspump.socket`` - Socket-based communication
- ``bspump.subprocess`` - Subprocess management
- ``bspump.timeseries`` - Time-series utilities
- ``bspump.parquet`` - Parquet file support
- ``bspump.avro`` - Avro serialization
