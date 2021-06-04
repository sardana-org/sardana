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

The other attributes are:

timer
    name of the timer channel (proceeding from the same controller) to be used
    when the channel is acquired independently

    special values:

    * __default - controller's default timer
    * __self - the same channel acts like a timer
    * None - independent acquisition is disabled

integration time
    integration time (in seconds) to be used when the channel is acquired
    independently

The available operations are:

start acquisition
    starts to acquire the counter/timer

    :meth:`~sardana.pool.poolbasechannel.PoolTimerableChannel.start_acquisition`

stop
    stops the counter/timer acquisition in an orderly fashion

abort
    stops the counter/timer acquisition as fast as possible

release
    Release hung acquisition e.g. due to the hardware controller that
    got hung. You should first try stop/abort.

.. seealso::

    :ref:`sardana-countertimer-overview`
        the counter/timer overview

    :class:`~sardana.tango.pool.CTExpChannel.CTExpChannel`
        the counter/timer tango device :term:`API`

..    :class:`~sardana.pool.poolcountertimer.PoolCounterTimer`
..        the counter/timer class :term:`API`
