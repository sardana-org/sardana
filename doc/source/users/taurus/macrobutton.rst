MacroButton User’s Interface
-----------------------------

Sardana provides a button widget to operate a macro.
As all Taurus widget it needs a model, in that case must be a valid door.
This widget also needs the set a macro and its parameters in case it has.

The :class:`~sardana.taurus.qt.qtgui.extra_macroexecutor.macrobutton.MacroButton`
can execute/pause/abort the configured macro.

Once you clicking in the button, if it is possible the macro will be run.
On the bottom of the widget there is a progress bar that shows an
estimated evolution of a macro (in %)

.. image:: /_static//macrobutton.png
    :align: center


If you clicking again in the button, when a macro is still running a dialog box
will be showed to allow you to choose abort the current macro.
If the executed macro implements pausedPoints the macro will be paused till you
took the decision (resume or abort).


.. image:: /_static//macrobutton_abort.png
    :align: center
