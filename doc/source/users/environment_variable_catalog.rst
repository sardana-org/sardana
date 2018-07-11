.. _environment-variable-catalog:

============================
Environment Variable Catalog
============================

This is the catalog of the available environment variables that can be used in
Sardana.

.. toctree::
    :maxdepth: 3

    environment_variable_catalog.rst

.. todo:: Add the scope of each environment variable
          (spock, macroserver, pool ...)

.. todo:: Add examples ... ??

.. _diffractometer-env-vars:

Diffractometer Environment Variables
------------------------------------

.. _diffracdevice:

DiffracDevice
~~~~~~~~~~~~~
*Mandatory, set by user*

This environment variable is used to define the name of the diffractometer device.
At this moment, this name is supporting only tango device names and it should
be pointing to the Sardana controller of the class HklPseudoMotorCtrl that will
be used by the hkl macros.

.. _psi:

Psi
~~~
*Not mandatory, set by user*

Environment variable to specify the *psi* device. This device must be the
tango device server corresponding Sardana PseudoMotor steering the movement
of the azimuthal angle.

.. _q:

Q
~
*Mandatory, set by macro wh*

This environment variable is set by the macro *wh* and it correspond to the
Q vector.

.. todo:: Add the reference to the wh macro.

.. _intern-env-vars:

Intern
------

.. _viewoptions:

_ViewOptions
~~~~~~~~~~~~
*Not mandatory, set by user*

.. _macro-logging-env-vars:

Macro Logging Environment Variables
-----------------------------------

.. _logmacro:

LogMacro
~~~~~~~~
*Not mandatory, set by user*

If true macro logging on, if false or not set macro logging off.

.. _logmacrodir:

LogMacroDir
~~~~~~~~~~~
*Not mandatory, set by user or to default value: \tmp, by macro*

Directory to save the macro logging file.

.. _logmacromode:

LogMacroMode
~~~~~~~~~~~~
*Not mandatory, set by user or to default value: 0, by macro*

Number of backup files to be saved.

.. _logmacroformat:

LogMacroFormat
~~~~~~~~~~~~~~
*Not mandatory, set by user or to default value by macro*

Line file format.

.. _motion-env-vars:

Motion Environment Variables
----------------------------

.. _motiondecoupled:

MotionDecoupled
~~~~~~~~~~~~~~~
*Not mandatory, set by user*

.. _scan-env-vars:

Scan Environment Variables
--------------------------

Following variables are supported:

.. _activemntgrp:

ActiveMntGrp
~~~~~~~~~~~~
*Mandatory, set by user*

Environment variable to define the measurement group that will be
used when running a scan.

.. seealso:: For further information regarding measurement groups, please read
             the following document:
             :ref:`Measurement Group Overview <sardana-measurementgroup-overview>`

.. _applyextraploation:

ApplyExtrapolation
~~~~~~~~~~~~~~~~~~
*Not mandatory, set by user*

Enable/disable the extrapolation method to fill the missing parts of the
very first scan records in case the software synchronized acquisition could
not follow the pace. Can be used only with the continuous acquisition
macros e.g. *ct* type of continuous scans or timescan. Its value is of
boolean type.

.. note::
    The ApplyExtrapolation environment variable has been included in
    Sardana on a provisional basis. Backwards incompatible changes
    (up to and including removal of this variable) may occur if deemed
    necessary by the core developers.

.. _applyinterpolation:

ApplyInterpolation
~~~~~~~~~~~~~~~~~~
*Not mandatory, set by user*

Enable/disable the `zero order hold`_ a.k.a. "constant interpolation"
method to fill the missing parts of the scan records in case the software
synchronized acquisition could not follow the pace. Can be used only
with the continuous acquisition macros *ct* type of continuous scans or
timescan. Its value is of boolean type.

.. note::
    The ApplyInterpolation environment variable has been included in
    Sardana on a provisional basis with SEP6_. Backwards incompatible
    changes (up to and including removal of this variable) may occur if
    deemed necessary by the core developers.

.. _directorymap:

DirectoryMap
~~~~~~~~~~~~
*Not mandatory, set by user*

In case that the server and the client do not run on the same host, the scan
data may be easily shared between them using the NFS. Since some of the
tools e.g. showscan rely on the scan data file the DirectoryMap may help in
overcoming the shared directory naming issues between the hosts.

Its value is a dictionary with keys pointing to the server side directory
and values to the client side directory/ies (string or list of strings).

.. todo::
    Add an example here.

.. _extracolumns:

ExtraColumns
~~~~~~~~~~~~
    *Not mandatory, set by user*

.. _jsonrecorder:

JsonRecorder
~~~~~~~~~~~~
    *Not mandatory, set by user*

.. _outputcols:

OutputCols
~~~~~~~~~~
    *Not mandatory, set by user*

.. _prescansnapshot:

PreScanSnapshot
~~~~~~~~~~~~~~~
    *Not mandatory, set by user*

.. _sampleinfo:

SampleInfo
~~~~~~~~~~
    *Not mandatory, set by user*


.. _scandir:

ScanDir
~~~~~~~
*Mandatory if file wants to be saved, set by user*

Its value is of string type and indicates an absolute path to the directory
where scan data will be stored.

.. _scanfile:

ScanFile
~~~~~~~~
*Mandatory if file wants to be saved, set by user*

Its value may be either of type string or of list of strings. In the second
case data will be duplicated in multiple files (different file formats may
be used). Recorder class is implicitly selected based on the file extension.
For example "myexperiment.spec" will by default store data in SPEC
compatible format.
    
.. seealso:: More about the extension to recorder map in
             :ref:`sardana-writing-recorders`).

.. _scanrecorder:

ScanRecorder
~~~~~~~~~~~~
*Not mandatory, set by user*

Its value may be either of type string or of list of strings. If
ScanRecorder variable is defined, it explicitly indicates which recorder
class should be used and for which file defined by ScanFile (based on the 
order).

Example 1:

::

    ScanFile = myexperiment.spec
    ScanRecorder = FIO_FileRecorder

    FIO_FileRecorder will write myexperiment.spec file.

Example 2:

::

    ScanFile = myexperiment.spec, myexperiment.h5
    ScanRecorder = FIO_FileRecorder

    FIO_FileRecorder will write myexperiment.spec file and
    NXscan_FileRecorder will write the myexpriment.h5. The selection of the
    second recorder is based on the extension.

.. _sharedmemory:

SharedMemory
~~~~~~~~~~~~
*Not mandatory, set by user*

Its value is of string type and it indicates which shared memory recorder should
be used during the scan e.g. "sps" will use SPSRecorder (sps Python module
must be installed on the PC where the MacroServer runs).

.. seealso:: For more information about the implementation details of the scan
             macros in Sardana, see 
             :ref:`scan framework <sardana-macros-scanframework>`

.. _sourceinfo:

SourceInfo
~~~~~~~~~~
*Not mandatory, set by user*