.. currentmodule:: sardana.pool

.. _sardana-measurementgroup-overview:

==========================
Measurement group overview
==========================

The measurement group interface allows the user to access several data
acquisition channels at the same time. The measurement group is the key
interface to be used when acquiring the data. The Pool can have several
measurement groups and use them simultaneously. When creating a measurement
group, the user compose it from: 

* :ref:`Counter/Timer <sardana-countertimer-overview>`
* :ref:`0D <sardana-0d-overview>`
* :ref:`1D <sardana-1d-overview>`
* :ref:`2D <sardana-2d-overview>`
* :ref:`Pseudo Counter <sardana-pseudocounter-overview>`
* external attribute e.g. Tango_

It is not possible to have several times the same channel in a measurement group.

.. _sardana-measurementgroup-overview-configuration:

Configuration
-------------

In order to properly use the measurement group, each of the timerable
controllers (Counter/Timer, 1D or 2D) needs to be assigned one of its channels
as the timer or the monitor. The first timer or monitor becomes the master one
for the whole measurement group.

By default, the data acquisition channels are synchronized by software,
meaning that the acquisition will be commanded to start (or start and stop)
with the software precission. In order to achieve a better synchonization the
hardware triggerring (or gating) can be used by configuring a
:ref:`Trigger/Gate <sardana-triggergate-overview>` as the controller's
synchronizer.

The measurement group configuration can by modified with the
:ref:`expconf widget <expconf_ui>`.

.. seealso::

    :ref:`sardana-measurementgroup-api`
        the measuremenent group :term:`API` 

    :class:`~sardana.tango.pool.MeasurementGroup.MeasurementGroup`
        the measurement group tango device :term:`API`

    :class:`~sardana.pool.poolmeasurementgroup.PoolMeasurementGroup`
        the measurement group class :term:`API`

.. _Tango: http://www.tango-controls.org
