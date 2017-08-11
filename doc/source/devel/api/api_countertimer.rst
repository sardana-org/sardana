.. currentmodule:: sardana.pool.poolcountertimer

.. _sardana-countertimer-api:

=============================
Counter/Timer API reference
=============================

The counter/timer is one of the most used elements in sardana. A counter/timer
represents an experimental channel which acquisition result is a scalar value.

A counter/timer has a ``state``, and a ``value`` attributes. The state
indicates at any time if the counter/timer is stopped, in alarm or moving.
The value, indicates the current counter/timer value.

The available operations are:

start acquisition(integration time)
    starts to acquire the counter/timer with the given integration time

    :meth:`~PoolCounterTimer.start_acquisition`

stop
    stops the counter/timer acquisition in an orderly fashion

abort
    stops the counter/timer acquisition as fast as possible

.. seealso::

    :ref:`sardana-countertimer-overview`
        the counter/timer overview

    :class:`~sardana.tango.pool.CTExpChannel.CTExpChannel`
        the counter/timer tango device :term:`API`

..    :class:`~sardana.pool.poolcountertimer.PoolCounterTimer`
..        the counter/timer class :term:`API`
