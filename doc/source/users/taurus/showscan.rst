.. _showscan_ui:

========
Showscan
========

Showscan is basically a simple HDF5 viewer application. It can be launched from
Spock using the :class:`~sardana.spock.magic.showscan` command. Without arguments,
it will show you the result of the last scan in a :term:`GUI`:

.. figure:: /_static/spock_snapshot02.png
    :height: 600

    Scan data viewer in action

:class:`~sardana.spock.magic.showscan` *scan_number* will display
data for the given scan number.

.. note::
	The :class:`~sardana.spock.magic.showscan` application can only read scans
	saved in the HDF5 format. Moreover, it opens the first file defined in
	:ref:`scanfile` environment variable, so if you use multiple files, make sure
	the HDF5 format one is the first one on list.

The scan files are saved on the Sardana server machine, however
:class:`~sardana.spock.magic.showscan` is running on the client one. If it's not
the same machine, you will need to share the scan files between machines, for
example with NFS.

.. note::
	If the path to the file on the server is different than on the client, you
	should use :ref:`directorymap` environment variable to map server paths	to
	client paths.
