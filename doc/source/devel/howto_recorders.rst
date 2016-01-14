.. _sardana-writing-recorders:

=================
Writing recorders
=================

Overview
---------

Sardana macros may produce data and users are usually interested in storing
or visualizing it. Sardana delegates this work to the recorders.
A good example of the recorder usage are the scan macros developed with the
:ref:`sardana-macros-scanframework`. Recorders are in charge of writing data to
its destinations, for example a file, the Spock output or to plot it on a graph.

What is a recorder?
-------------------

Recorder class is a Sardana element managed by the MacroServer. It is
identified by its name, and is located in a recorder library - another Sardana
element which is also identified by its name. Recorders are developed as
Python classes, and recorder libraries are just Python modules aggregating these
classes.

Type of recorders
-----------------

Sardana defines some standard recorders e.g. the Spock output recorder or the 
SPEC file recorder. From the other hand users may define their custom recorders.
Sardana provides the following standard recorders (grouped by types):

* file [*]
    * FIO_FileRecorder
    * NXscan_FileRecorder
    * SPEC_FileRecorder

* shared memory [*]
    * SPSRecorder
    * ShmRecorder

* output
    * JsonRecorder [*]
    * OutputRecorder

[*] Scan Framework provides mechanisms to enable and select this recorders using
the environment variables.

Writing a custom recorder
-------------------------

.. todo:: document how to write custom recorders

Configuration
-------------

Custom recorders may be added to the Sardana system by placing the recorder
library module in a directory which is specified by the MacroServer
*RecorderPath* property. RecorderPath property may contain an ordered, 
colon-separated list of directories.
In case of overriding recorders by name or by file extension (in case of the
file recorders), recorders located in the first paths are of higher priority
than the ones from the last paths.

Three types of overriding may occur:

**By recorder library name**
   If Python modules with the same name are located in different directories, 
   the library located in the the higher priority directory will be loaded.

**By recorder name**
   If two recorder classes with the same name appear in two different modules,
   only the recorder from the library located in the higher
   priority module will be loaded. If both modules are located in the same
   directory, the behavior is undetermined.

**By file extension**
   If two different recorders supporting the same file extension appear in two 
   different modules, the one from the higher priority path will be used
   when selection is based on the extension (but both will be available for the
   selection by name). If both of these recorders' modules are located in the
   same directory, the system will assign a list of recorders to a given
   extension. Then the application is in charge of deciding which one to use.

As previously mentioned recorders are selectable by either the recorder name or
the extension. During the MacroServer startup the extension to recorder map is
generated while loading the recorder libraries. This dynamically created map
may be overridden by the custom map defined in the *sardanacustomsettings*
module (SCAN_RECORDER_MAP variable with a dictionary where key is the scan file
extension e.g. ".h5" and value is the recorder name e.g. "MyCustomRecorder",
where both keys and values are of type string).
