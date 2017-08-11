.. currentmodule:: sardana.pool.poolpseudocounter

.. _sardana-pseudocounter-api:

=============================
Pseudo counter API reference
=============================

A pseudo counter has a ``state``, and a ``value`` attributes. The state
indicates at any time if the psuedo counter is stopped, in alarm or moving. The
state is composed from the states of all the physical counters involved in the
pseudo counter. So, if one of the counters is in moving or alarm state, the
whole pseudo counter will be in that state. The value, indicates the current
value.

The other pseudo counter's attributes are:

siblings
    List of other psuedo counter objects that belongs to the same controller.

    :attr:`~PoolPseudoCounter.siblings`

The available operations are:

start acquisition(integration time)
    starts to acquire the pseudo counter with the given integration time

    :meth:`~PoolPseudoCounter.start_acquisition`

stop
    stops the pseudo counter acquisition in an orderly fashion

abort
    stops the pseudo counter acquisition as fast as possible

.. seealso::

    :ref:`sardana-pseudocounter-overview`
        the pseudo-counter overview 

    :class:`~sardana.tango.pool.PseudoCounter.PseudoCounter`
        the pseudo-counter tango device :term:`API`

..    :class:`~sardana.pool.poolpseudocounter.PoolPseudoCounter`
..        the pseudo-counter class :term:`API`
