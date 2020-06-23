.. _sardana-configuration-pool:

Pool
====

Device Pool is easily extendable by means of controller plugins. Device Pool
discovers them in directories configurable via
:ref:`sardana-pool-api-poolpath` attribute. In case Sardana is used with
Tango this configuration is accessible via the ``PoolPath``
:class:`~sardana.tango.pool.Pool.Pool` device property.

Your controller plugins may need to access to third party Python modules. One
can configure the directory where to look for them via
:ref:`sardana-pool-api-pythonpath` attribute. In case Sardana is
used with Tango this configuration is accessible via the ``PythonPath``
:class:`~sardana.tango.pool.Pool.Pool` device property.

Device Pool integrates natively with the
`Elastic Stack <http://www.elastic.co>`_ and may send logs to the a Logstash
instance. In case Sardana is used with Tango this configuration is
accessible via the ``LogstashHost`` and ``LogstashPort``
:class:`~sardana.tango.pool.Pool.Pool` device properties.
You can use the intermediate SQLite cache database configured with
``LogstashCacheDbPath`` property, however this is discouraged due to logging
performance problems.


.. todo::
    Document RemoteLog, MotionLoop_SleepTime, MotionLoop_StatesPerPosition,
    AcqLoop_SleepTime, AcqLoop_StatesPerValue, DriftCorrection, InstrumentList
