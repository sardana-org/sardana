.. currentmodule:: sardana.pool.poolpseudomotor

.. _sardana-pseudomotor-api:

=============================
Pseudo motor API reference
=============================

A pseudo motor has a ``state``, and a ``position`` attributes. The state
indicates at any time if the pseudo motor is stopped, in alarm or moving. The
state is composed from the states of all the physical motors involved in the
pseudo motor. So, if one of the motors is in moving or alarm state, the whole
pseudo motor will be in that state. The position, indicates the current
position.

The other pseudo motor's attributes are:

drift correction
    Flag to enable/disable drift correction while calculating physical
    motor(s) position(s). When enabled, the write sibling(s) position(s) will
    be used, when disabled, the read sibiling(s) position(s) will be
    used instead. By default drift correction is enabled.

    :attr:`~PoolPseudoMotor.drift_correction`

siblings
    List of other psuedo motor objects that belongs to the same controller.

    :attr:`~PoolPseudoMotor.siblings`

The available operations are:

start move absolute
    Starts to move the pseudo motor to the given absolute position.

    :meth:`~PoolPseudoMotor.start_move`

stop
    Stops the pseudo motor motion, by stopping all the physical motors, in an
    orderly fashion.

abort
    Stops the pseudo motor motion, by stopping all the physical motors, as
    fast as possible (possibly without deceleration time and loss of position).


.. seealso::

    :ref:`sardana-pseudomotor-overview`
        the pseudo-motor overview

    :class:`~sardana.tango.pool.PseudoMotor.PseudoMotor`
        the pseudo-motor tango device :term:`API`

..    :class:`~sardana.pool.poolpseudomotor.PoolPseudoMotor`
..        the pseudo-motor class :term:`API`
