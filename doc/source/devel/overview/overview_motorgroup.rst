.. _sardana-motorgroup-overview:

.. currentmodule:: sardana.pool

===================
MotorGroup overview
===================

Whenever a move with more than one motor (or moveable element in general) is
requested, a MotorGroup object containing all elements involved in the movement
is silently created.

The motor group will not be removed automatically after the operation finishes.
This allows reuse of the groups by subsequent operation involving the same set
of moveables. You can however freely remove them manually with no adverse
effects.

The *motor group* object is also exposed as a Tango_ device, by default using
the :code:`mg/<pool name>/_mg_ms_<pid>_<num>` where :code:`pool name` is the
alias or instance name of the Pool hosting the MotorGroup, :code:`pid` is a PID
of the MacroServer that created the MotorGroup, and :code:`num` is just a
sequential counter.

.. seealso::

    :class:`~sardana.tango.pool.MotorGroup.MotorGroup`
        the motor group tango device :term:`API`

    :class:`~sardana.pool.poolmotorgroup.PoolMotorGroup`
        the motor group internal class :term:`API`

.. _Tango: http://www.tango-controls.org/
