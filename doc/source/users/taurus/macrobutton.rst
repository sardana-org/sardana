.. _macrobutton:

MacroButton User’s Interface
-----------------------------

Sardana provides a button widget to operate a macro execution.
As all Taurus widget it needs a model, in that case the model points to a Door device.
This widget also needs the set the macro macro and its parameters in case it has.

The :class:`~sardana.taurus.qt.qtgui.extra_macroexecutor.macrobutton.MacroButton`
can execute/pause/abort the configured macro.

Once you clicking in the button, if it is possible the macro will be run.
On the bottom of the widget there is a progress bar that shows an
estimated progress of a macro (in %)

.. image:: /_static//macrobutton.png
    :align: center


If you click again on the button, when a macro is still running a dialog box
will be showed to allow you to choose to abort the current macro.
If the executed macro implements pause points the macro will be paused utill you
take the decision (resume or abort).

.. image:: /_static//macrobutton_abort.png
    :align: center
