.. currentmodule:: sardana.macroserver.macroserver

.. _sardana-macroserver-api:

=========================
MacroServer API reference
=========================

The MacroServer is one of the most important elements in sardana.

This chapter explains the generic macroserver :term:`API` in the context of 
sardana. In sardana there are, in fact, two MacroServer :term:`API`\s. To 
better explain why, let's consider the case were sardana server is running 
as a Sardana Tango device server:

Every macroserver in sardana is represented in the sardana kernel as a
:class:`MacroServer`. The :class:`MacroServer` :term:`API` is not directly
accessible from outside the sardana server. This is a low level :term:`API`
that is only accessible to someone writing a server extension to sardana. At
the time of writing, the only available sardana server extension is Tango.

The second macroserver interface consists on the one provided by the server
extension, which is in this case the one provided by the Tango macroserver
device interface:
:class:`~sardana.tango.macroserver.MacroServer.MacroServer`. The Tango
macroserver interface tries to mimic the as closely as possible the
:class:`MacroServer` :term:`API`.

.. seealso:: 
    
    :ref:`sardana-macroserver-overview`
        the macroserver overview 

    :class:`~sardana.tango.macroserver.MacroServer.MacroServer`
        the macroserver tango device :term:`API`

Each macroserver has the following attributes:

.. _sardana-macroserver-api-poolnames:

pool names
----------
    MacroServer may connect to none, one or many Device Pools. The advantage
    of connecting to device pools is the native access to the pool elements
    e.g. motors, experimental channels, etc. and their possible use in the
    macros. Most of the standard macros, for example scans, wants to
    interface with them. MacroServer listens to the device pool elements
    events so it is aware of new, modified and deleted elements.

.. _sardana-macroserver-api-environmentdb:

environment db
--------------
    Macro environment is stored in an external database. Currently it is
    implemented using the Python
    `shelve <https://docs.python.org/2.7/library/shelve.html#module-shelve>`_
    module. The shelve file is stored on the file system and by default it
    points to the OS temporary directory e.g. ``/tmp`` in case of Linux
    which may be transitory. It is highly recommended to change this location.
    
    Default value: ``/tmp/tango/<ds_exec_name>/<ds_inst_name>/macroserver.properties``

.. _sardana-macroserver-api-macropath:

macro path
----------
    MacroServer may load user macros and this are discoverable by scanning the
    file system directories configured in macro path.

.. _sardana-macroserver-api-recorderpath:

recorder path
-------------
    MacroServer may load user recorders and this are discoverable by scanning
    the file system directories configured in recorder path.

.. _sardana-macroserver-api-pythonpath:

python path
-----------
    Macros may need to access to third party Python modules. When these are
    not available to the Python interpreter i.e. exported to the
    ``PYTHONPATH``, one can configure the file system directories where the
    MacroServer should look for these modules.

.. _sardana-macroserver-api-maxparallelmacros:

max parallel macros
-------------------
    Multiple macros can run concurrently in the MacroServer on different
    Doors. The maximum number of these threads is configurable.
    
    Default value: 5

.. _sardana-macroserver-api-logreportfilename:

log report file name
--------------------
    Macros may report information to a file and its location is configurable.

.. _sardana-macroserver-api-logreportformat:

log report format
-----------------
    Macros may report information to a file and the format of this
    information is configurable. It uses the
    `Python logging format syntax <https://docs.python.org/2/library/logging.html#formatter-objects>`_.

    Defaul value: ``%(levelname)-8s %(asctime)s: %(message)s``
