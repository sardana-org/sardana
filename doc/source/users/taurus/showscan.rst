.. _showscan_ui:

========
Showscan
========

Sardana provides widgets for plotting scans either *online* or *offline*.
Currently there are two different widgets for providing these features.
These widgets can be used in your GUI or
:ref:`launched from spock <sardana-spock-showscan>`.

---------------
Showscan online
---------------

Showscan online is a simplified Taurus application which provides live scan
plots. The number of plots and their configuration depends on the
:ref:`measurement group plotting configuration <expconf_ui_measurementgroup>`.

When started it gets populated with empty plots of the
:ref:`active measurement group <activemntgrp>`. As soon as you start
scanning the curves and the legend will start to appear. Even if you change
the active measurement group or you change the plotting configuration the
plots will not get recreated until you start another scan. The purpose of this
behavior is to keep the plotted data available for inspection after the scan
execution.

.. figure:: /_static/showscan-online.png
    :height: 600

    Showscan online plotting two physical counters against the point
    number and a pseudo counter against the moveable.

----------------
Showscan offline
----------------

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
	saved in the HDF5 format.

The scan files are saved on the Sardana server machine, however
:class:`~sardana.spock.magic.showscan` is running on the client one. If it's not
the same machine, you will need to share the scan files between machines, for
example with NFS.

.. note::
	If the path to the file on the server is different than on the client, you
	should use :ref:`directorymap` environment variable to map server paths	to
	client paths.
