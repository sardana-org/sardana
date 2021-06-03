.. currentmodule:: sardana.pool.poolmeasurementgroup

.. _sardana-measurementgroup-api:

================================
Measurement group API reference
================================

.. important::
    Measurement group :term:`API` was extended in SEP18_ but this is still
    not documented in this chapter. Please check the said SEP for more
    information about the additional :term:`API` or eventual changes.


The measurement group is a group element. It aggregates other elements like
experimental channels (counter/timer, 0D, 1D and 2D or external attribute e.g.
Tango_) and trigger/gates. The measurement group role is to execute acquisitions
using the aggregated elements.

A measurement group has a ``state`` attribute. The state indicates at any time
if the measurement group is stopped, in alarm or moving. The state is composed
from the states of all the elements involved in the measurement group. So, if
one of the involved element (experimental channel or trigger/gate) is in moving
or alarm state, the whole measurement group will be in that state.

The other measurement group's attributes are:

timer
    The name of the channel used as a timer.

integration time
    Integration time to be used in the acquisition operation.

monitor count
    Monitor count to be used in the acquisition operation.

acquisition mode
    Acquisition mode to be used in the acquisition operation, either Timer or
    Monitor.

latency time
    Latency time between two consecutive acquisitions in the same acquisition
    operation.

synch description
    Describes the acquisition operation synchronization. It is composed from
    the group(s) of equidistant acquisitions described by the following
    parameters:

    * initial point
    * initial delay
    * total interval
    * active interval 
    * number of repetitions

    These parameters can be expressed in different synchronization domains if
    necessary (time and/or position).

moveable
    Name of the master moveable.

    **Note:** This attribute has been included in Sardana on a provisional
    basis. Backwards incompatible changes (up to and including its removal)
    may occur if deemed necessary by the core developers.

software synchronizer initial domain
    Initial domain to be used by the software synchronizer.

    If the *initial* parameter is described redundantly in the
    synchronization description i.e. both in the *position* and in the
    *time* domains, then this attribute will specify the one that will be
    used by the software synchronizer.

    If the synchronization description does not contain value in this domain
    the software synchronizer will silently try to use the other one.

    **Note:** This attribute has been included in Sardana on a provisional
    basis. Backwards incompatible changes (up to and including its removal)
    may occur if deemed necessary by the core developers.


The available operations are:

start acquisition()
    Starts to acquire the measurement group.

    :meth:`~PoolMeasurementGroup.start_acquisition`

stop()
    stops the acquisition in an orderly fashion

abort()
    stops the acquisition as fast as possible

release()
    Release hung acquisition e.g. due to the hardware controller that
    got hung. You should first try stop/abort.



.. seealso::

    :ref:`sardana-measurementgroup-overview`
        the measurement group overview 

    :class:`~sardana.tango.pool.MeasurementGroup.MeasurementGroup`
        the measurement group tango device :term:`API`

..    :class:`~sardana.pool.poolmeasurementgroup.PoolMeasurementGroup`
..        the measurement group class :term:`API`

.. _Tango: http://www.tango-controls.org
.. _SEP18: http://www.sardana-controls.org/sep/?SEP18.md