.. _sardana-configuration-macroserver:

MacroServer
===========

Most probably your MacroServer will need to connect to one or more Device
Pools via the :ref:`sardana-macroserver-api-poolnames` attribute. This is
usually configured at the server creation time but can be also modified
later on. In case Sardana is used with Tango this configuration
is accessible via the ``PoolNames``
:class:`~sardana.tango.macroserver.MacroServer.MacroServer` device property.

You will certainly use the macro environment variables for changing macros
behavior at runtime. This environment is stored in a database configurable via
:ref:`sardana-macroserver-api-environmentdb` attribute. In case Sardana is
used with Tango this configuration is accessible via the ``EnvironmentDb``
:class:`~sardana.tango.macroserver.MacroServer.MacroServer` device property.

MacroServer is easily extendable by means of plugins of two types:
macros and recorders. MacroServer discovers them in directories
configurable via :ref:`sardana-macroserver-api-macropath` and
:ref:`sardana-macroserver-api-recorderpath` attributes. In case Sardana is
used with Tango this configuration is accessible via the ``MacroPath`` and
``RecorderPath`` :class:`~sardana.tango.macroserver.MacroServer.MacroServer`
device properties.

Your plugins may need to access to third party Python modules. One can
configure the directory where to look for them via
:ref:`sardana-macroserver-api-pythonpath` attribute. In case Sardana is
used with Tango this configuration is accessible via the ``PythonPath``
:class:`~sardana.tango.macroserver.MacroServer.MacroServer` device property.

Multiple macros can run concurrently in the MacroServer and the maximum number
of these threads is configurable via
:ref:`sardana-macroserver-api-maxparallelmacros` attribute. In case Sardana is
used with Tango this configuration is accessible via the ``MaxParallelMacros``
:class:`~sardana.tango.macroserver.MacroServer.MacroServer` device property
(default: 10).

Macros may report information to a file which is configurable via
:ref:`sardana-macroserver-api-logreportfilename` and
:ref:`sardana-macroserver-api-logreportformat`. In case Sardana is
used with Tango this configuration is accessible via the ``LogReportFilename``
and ``LogReportFormat``
:class:`~sardana.tango.macroserver.MacroServer.MacroServer` device properties.

MacroServer integrates natively with the
`Elastic Stack <http://www.elastic.co>`_ and may send logs to the a Logstash
instance. In case Sardana is used with Tango this configuration is
accessible via the ``LogstashHost`` and ``LogstashPort``
:class:`~sardana.tango.macroserver.MacroServer.MacroServer` device properties.
You can use the intermediate SQLite cache database configured with
``LogstashCacheDbPath`` property, however this is discouraged due to logging
performance problems.

You can debug the MacroServer at runtime using the Python remote
console - ``rconsole`` (part of the `rfoo <https://pypi.org/project/rfoo/>`_
project). First, you need to specify at which port the MacroServer will
accept connections. For that, simply set the ``RConsolePort``
:class:`~sardana.tango.macroserver.MacroServer.MacroServer` property.
Second, in order to open a connection to a MacroServer just type::

    $> rconsole -p <port>

The most convenient way to debug the MacroServer internals is to use the
`Tango Util <https://pytango.readthedocs.io/en/stable/server_api/util
.html#util>`_ singleton object. It is used to store Tango device server
process data and to provide the user with a set of utility methods.
For example, to access the MacroServer Sardana core object, in the rconsole
session, just type::

    >>> import tango
    >>> util = tango.Util.instance()
    >>> ms = util.get_device_by_name("<ms_device_name>").macro_server
