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

The available operations are:

start acquisition(integration time)
    starts to acquire the 2D with the given integration time

    :meth:`~PoolCounterTimer.start_acquisition`

stop
    stops the 2D acquisition in an orderly fashion

abort
    stops the 2D acquisition as fast as possible

.. seealso::

    :ref:`sardana-2d-overview`
        the 2D experiment channel overview

    :class:`~sardana.tango.pool.TwoDExpChannel.TwoDExpChannel`
        the 2D experiment channel tango device :term:`API`

..    :class:`~sardana.pool.pooltwodexpchannel.Pool2DExpChannel`
..        the 2D experiment channel class :term:`API`
