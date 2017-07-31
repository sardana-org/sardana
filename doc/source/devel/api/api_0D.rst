.. currentmodule:: sardana.pool.poolzerodexpchannel

.. _sardana-0d-api:

=============================
0D channel API reference
=============================

The 0D experimental channel is used to access any kind of device which returns
a scalar value and which are not counter/timer.

A 0D has a ``state``, and a ``value`` attributes. The state indicates at any
time if the 0D is stopped, in alarm or moving. The value behaves exactly the
same as the accumulated value attribute.

The other attributes are:

accumulation
    Defines the computation type done on the values gathered during the
    acquisition. Three type of computation are supported:

    * Sum - the accumulation value attribute is the sum of all the data read
      during the acquisition. This is the default type.
    * Average - the accumulation value attribute is the average of all the data
      read during the acquisition.
    * Integral - the accumulation value attribute is a type of the integral of
      all the data read during the acquisition.

current value
    This is the current a.k.a. instant value of the experimental channel.
    If the current value attribute is read while the acquisition is in
    progress, it returns the last updated by the acquisition operation value
    (cache). When there is no acquisition in progress the current value read
    executes the hardware readout and returns an updated value.

accumulated value
    This is the result of the data acquisition after the computation defined by
    the accumulation attribute has been applied. This value is 0 until an
    acquisition has been started. After an acquisition, the attribute value
    stays unchanged until the next acquisition is started.

accumulation buffer
    This buffer is filled with the instant values read by the acquisition
    operation.

time buffer
    This buffer is filled with the timestamps of the instant values present in
    the accumulation buffer and it is also filled during the acquisition
    operation.

The available operations are:

start acquisition(integration time)
    starts to acquire the 0D with the given integration time

    :meth:`~Pool0DExpChannel.start_acquisition`

stop
    stops the 0D acquisition in an orderly fashion

abort
    stops the 0D acquisition as fast as possible

.. seealso::

    :ref:`sardana-0d-overview`
        the 0D experiment channel overview

    :class:`~sardana.tango.pool.ZeroDExpChannel.ZeroDExpChannel`
        the 0D experiment channel tango device :term:`API`

..    :class:`~sardana.pool.poolzerodexpchannel.Pool0DExpChannel`
..        the 0D experiment channel class :term:`API`
