.. currentmodule:: sardana.pool.pooltwodexpchannel

.. _sardana-2d-api:

=============================
2D channel API reference
=============================

A 2D represents an experimental channel which acquisition result is a image
value.

A 2D has a ``state``, and a ``value`` attributes. The state indicates at any
time if the 2D is stopped, in alarm or moving. The value, indicates the
current 2D value.

The other attributes are:

data source
    Unique identifier for the 2D data (value attribute)

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
    starts to acquire the 2Ds

    :meth:`~PoolCounterTimer.start_acquisition`

stop
    stops the 2D acquisition in an orderly fashion

abort
    stops the 2D acquisition as fast as possible

release
    Release hung acquisition e.g. due to the hardware controller that
    got hung. You should first try stop/abort.

.. seealso::

    :ref:`sardana-2d-overview`
        the 2D experiment channel overview

    :class:`~sardana.tango.pool.TwoDExpChannel.TwoDExpChannel`
        the 2D experiment channel tango device :term:`API`

..    :class:`~sardana.pool.pooltwodexpchannel.Pool2DExpChannel`
..        the 2D experiment channel class :term:`API`
