.. _sardana-configuration-server:

Sardana server configuration
============================

Sardana system can
:ref:`run as one or many Tango device servers<sardana-getting-started-running-server>`.
Tango device servers listens on a TCP port for the CORBA requests. Usually
it is fine to use the randomly assigned port (default behavior) but sometimes
it may be necessary to use a fixed port number. For example, when the server
needs to be accessed from another isolated network and we want to open
connections only for the given ports.

There are three possibilities to assign the port explicitly (the order
indicates the precedence):

- using OS environment variable ``ORBendPoint`` e.g.

.. code-block:: bash

    $ export ORBendPoint=28366
    $ Pool demo1 -ORBendPoint 28366

- using Tango device server command line argument ``-ORBendPoint``

.. code-block:: bash

    $ Pool demo1 -ORBendPoint 28366

- using Tango DB free property with object name: ``ORBendPoint`` and property
  name: ``<server_name>/<instance_name>``)

.. code-block:: python

    import tango
    db = tango.Database()
    db.put_property("ORBendPoint", {"Pool/demo1": 28366})

.. note::

    Due to a bug, when Sardana is used with Tango versions prior to 8.0.5,
    the command line arguments takes precedence over the environment variables.
