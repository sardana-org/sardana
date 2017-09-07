.. currentmodule:: sardana.pool

.. _sardana-countertimer-overview:

=======================
Counter/timer overview
=======================

The counter/timer is one of the most used elements in Sardana. A counter/timer
represents an experimental channel which acquisition result is a scalar value.
As indicates its name it is foreseen to interface hardware couters or timers
but it also fits well with other hardware like :term:`ADC` or electrometer.

The acquisition operation on a counter/timer is executed over the integration
time specified by the user. Counter/timer can be controlled by either software
or hardware synchronization (:ref:`Trigger/Gate <sardana-triggergate-overview>`)
and multiple repetitions, also specified by the user are, are possible within
the same acquisition operation.

.. seealso::

    :ref:`sardana-countertimer-api`
        the counter/timer :term:`API`

    :class:`~sardana.tango.pool.CTExpChannel.CTExpChannel`
        the counter/timer tango device :term:`API`
