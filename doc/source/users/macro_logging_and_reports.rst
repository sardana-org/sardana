.. highlight:: python
   :linenothreshold: 5
   
.. currentmodule:: sardana.macroserver.macros.logging_and_reports

.. _sardana-macros-logging-and-reports:

=========================
Macro Logging and Reports
=========================

The MacroServer allows to write into a log file
:ref:`log messages <sardana-macro-logging>` from the macros
as well as additional log entries that enclose each macro
execution, e.g. when it starts and when it ends.

This log feature is controlled via
:ref:`environment variables <macro-logging-env-vars>`,
allowing the activation/deactivation and the setting of
the number of backup files, log directory and file names
and output format.

Additional filters to this log messages can be applied with
:data:`~sardana.sardanacustomsettings.LOG_MACRO_FILTER`.

The macro :class:`~sardana.macroserver.macros.standard.logmacro` activate/deactivate the macro logging.

:ref:`Report messages <sardana-macro-reporting>` can be sent by the macros to a report file.
This report feature is controlled by the :ref:`MacroServer configuration <sardana-configuration-macroserver>`.
