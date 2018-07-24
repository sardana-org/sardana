.. highlight:: python
   :linenothreshold: 5
   
.. currentmodule:: sardana.macroserver.macros.logging


.. _sardana-macros-logging:

=============
Macro Logging
=============

The MacroServer allows to write into a log file messages from the class responsible for
running the macros together with the :ref:`log messages <sardana-macro-logging>` coming
from the macro itself.

This log feature is controlled via :ref:`environment variables <macro-logging-env-vars>`,
that allows the activation/deactivation and the setting of the number of backup files,
log directory and file names, output format and customized filters.

The macro :class:`~sardana.macroserver.macros.standard.logmacro` controls this feature.
