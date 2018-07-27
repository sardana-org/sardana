.. currentmodule:: sardana.pool

.. _sardana-pseudomotor-overview:

=======================
Pseudo motor overview
=======================

The pseudo motor interface acts like an abstraction layer for a motor
or a set of motors allowing the user to control the experiment by
means of an interface which is more meaningful to him(her).

One of the most basic examples is the control of a slit. The slit has two blades
with one motor each. Usually the user doesn't want to control the experiment by
directly handling these two motor positions since they have little meaning from
the experiments perspective. Instead, it would be more useful for the user to
control the experiment by means of changing the gap and offset values. In the
:class:`~sardana.pool.poolcontrollers.Slit` controller, pseudo motors gap and
offset will provide the necessary interface for controlling the experiments
gap and offset values respectively.

.. figure:: /_static/slits.gif
    :align: center

    An animation [#]_ representing a system of slits composed from horizontal
    blades (left and right) an vertical blades (top and bottom).

In order to translate the motor positions into the pseudo motor positions and
vice versa, calculations have to be performed. The device pool provides
:class:`~sardana.pool.controller.PseudoMotorController` class that can be
overwritten to provide new calculations.

The pseudo motor position gets updated automatically every time one of its
motors position gets updated e.g. when the motion is in progress.

The pseudo motor object is also exposed as a Tango_ device.

.. seealso::

    :ref:`sardana-pseudomotor-api`
        the pseudo motor :term:`API`

    :class:`~sardana.tango.pool.PseudoMotor.PseudoMotor`
        the pseudo motor tango device :term:`API`

.. rubric:: Footnotes

.. [#] We would like to thank Dominique Heinis for sharing his expertise in
       blender.

.. _Tango: http://www.tango-controls.org/
