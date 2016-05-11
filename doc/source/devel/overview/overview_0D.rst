.. currentmodule:: sardana.pool

.. _sardana-0d-overview:

=======================
0D channel overview
=======================

The ZeroDExpChannel is used to access any kind of device which returns a scalar
value and which are not counter or timer. Very often (but not always), this is
a commercial measurement equipment connected to a GPIB bus. In order to have as
precise as possible measurement, an acquisition loop is implemented for the
ZeroDExpChannel device. This acquisition loop will simply read the data from
the hardware as fast as it can (only “sleeping” 10 mS between each reading) and
a computation is done on the resulting data set to return only one value.
Three types of computation are foreseen. The user selects which one he needs
with an attribute. The time during which this acquisition loop will get data is
controlled by the counters & timers present in the measurement group - when all
of them finish acquiring the ZeroD acquisition action will also stop.

.. seealso::

    :ref:`sardana-0d-api`
        the 0D experiment channel :term:`API` 

    :class:`~sardana.tango.pool.ZeroDExpChannel.ZeroDExpChannel`
        the 0D experiment channel tango device :term:`API`
