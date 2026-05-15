Integrations
============

BSPump provides integrations with many external systems. This section covers
the available connectors, sources, sinks, and configuration options.

.. toctree::
   :maxdepth: 2

   kafka
   http
   postgresql
   mongodb
   elasticsearch
   mqtt
   file

Overview
--------

.. list-table::
   :header-rows: 1

   * - Integration
     - Connection
     - Source
     - Sink
   * - :doc:`kafka`
     - Yes
     - Yes
     - Yes
   * - :doc:`http`
     - No
     - Yes (Webhook)
     - Yes (Client)
   * - :doc:`postgresql`
     - Yes
     - Yes
     - Yes
   * - :doc:`mongodb`
     - Yes
     - Yes
     - Yes
   * - :doc:`elasticsearch`
     - Yes
     - Yes
     - Yes
   * - :doc:`mqtt`
     - Yes
     - Yes
     - Yes
   * - :doc:`file`
     - No
     - Yes
     - Yes

Additional Integrations
-----------------------

BSPump also supports:

- **AMQP/RabbitMQ**: ``bspump.amqp``
- **InfluxDB**: ``bspump.influxdb``
- **MySQL**: ``bspump.mysql``
- **ODBC**: ``bspump.odbc``
- **FTP/SFTP**: ``bspump.ftp``, ``bspump.ssh``
- **Slack**: ``bspump.slack``
- **Google Drive**: ``bspump.googledrive``
- **LDAP**: ``bspump.ldap``
- **ZooKeeper**: ``bspump.zookeeper``

See the :doc:`../api/index` for complete documentation of all modules.
