.. _sardana-door-overview:

=============
Door overview
=============

*Door* is an entry point to the MacroServer. Door exposes an interface
to run macros and interact with macro currently being run.

A single Macro Server can have many active Doors at the same time but
a Door can only run one macro at a time. Each Door is exposed on the
sardana server as a Tango_ device.

Exist a possibility to define :ref:`macro environment <macro-environment>`
applied at the door level i.e. not visible on other doors.

.. _Tango: http://www.tango-controls.org/
