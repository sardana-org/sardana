.. currentmodule:: sardana.pool.poolonedexpchannel

.. _sardana-1d-api:

=============================
1D channel API reference
=============================

A 1D represents an experimental channel which acquisition result is a spectrum
value.

A 1D has a ``state``, and a ``value`` attributes. The state indicates at any
time if the 1D is stopped, in alarm or moving. The value, indicates the
current 1D value.

The other attributes are:

data source
    Unique identifier for the 1D data (value attribute)

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
    starts to acquire the 1D

    :meth:`~PoolCounterTimer.start_acquisition`

stop
    stops the 1D acquisition in an orderly fashion

abort
    stops the 1D acquisition as fast as possible

release
    Release hung acquisition e.g. due to the hardware controller that
    got hung. You should first try stop/abort.

.. seealso::

    :ref:`sardana-1d-overview`
        the 1D experiment channel overview

    :class:`~sardana.tango.pool.OneDExpChannel.OneDExpChannel`
        the 1D experiment channel tango device :term:`API`

..    :class:`~sardana.pool.poolonedexpchannel.Pool1DExpChannel`
..        the 1D experiment channel class :term:`API`
