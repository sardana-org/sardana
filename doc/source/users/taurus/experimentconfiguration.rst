.. currentmodule:: sardana.taurus.qt.qtgui.extra_sardana

.. _expconf_ui:


=======================================
Experiment Configuration user interface
=======================================

.. contents::

Experiment Configuration widget a.k.a. expconf is a complete interface to
define all the experiment configuration. It consists of three main groups of
parameters organized in tabs:

* Measurement group
* Snapshot group
* Storage

The parameters may be modified in an arbitrary order, at any of the tabs, and
will be maintained as pending to apply until either applied or reset by the
user.

.. _expconf_ui_measurementgroup:

Measurement group configuration
-------------------------------

In the measurement group tab the user can:

* create or remove a measurement group
* select the active measurement group
* add or remove channels of the measurement group
* reorganize the order of the channels in the measurement group
* change configuration of a particular channel (or its controller) in the
  selected measurement group

.. figure:: /_static/expconf01.png
   :width: 100%
   :figwidth: 100%
   :align: center

   Measurement group tab of the expconf widget with the `mntgrp` configuration.

.. _expconf_ui_measurementgroup_channel:

Experimental channel configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the measurement group table the user can modify the following parameters of
a given channel or its controller:

* enabled - include or exclude (True or False) the channel in the acquisition
  process.
* output - whether the channel acquisition results should be printed, for example,
  by the output recorder during the scan. Can be either True or False.
* shape - shape of the data 
* data type - type of the data
* plot type - select the online scan plot type for the channel. Can have one
  of the following values:
  - No - no plot
  - Spectrum - suitable for scalar values
  - Image - suitable for spectrum values
* plot axes - select the abscissa (x axis) of the plot. Can be either
  - <idx> - scan index (point number)
  - <mov> - master moveable (in case of a2scan - the first motor) used in the scan
  - any of the scalar experimental channels used in the measurement group
* timer - channel to be used as timer. Timer controls the acqusition in terms of the
  integration time. Applies on the controller level.
* monitor - channel to be used as monitor. Monitor controls the acquisition in
  terms of the monitor counts. Applies on the controller level.
* synchronizer - the element that will synchronize the channel's
  acquisition. Can be either a :ref:`Trigger/Gate <sardana-triggergate-overview>`
  element or the *software* synchronizer. Configurable only for the timerable
  controllers. Applies on the controller level.
* synchronization - the synchronization type. Can be either *Trigger* or *Gate*.
  Configurable only for the timerable controllers. Applies on the controller level.
* conditioning - expression to evaluate on the data before displaying it
* normalization - normalization mode for the data
* nexus path - location of the data of this channel withing the NeXus tree
