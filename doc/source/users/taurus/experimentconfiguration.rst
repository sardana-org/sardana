.. currentmodule:: sardana.taurus.qt.qtgui.extra_sardana

.. _expconf_ui:


=======================================
Experiment Configuration user interface
=======================================

.. contents::

Experiment Configuration widget a.k.a. ``expconf`` is a complete interface to
define the experiment configuration. It consists of three main groups of
parameters organized in tabs:

* Measurement group
* Snapshot group
* Storage

The parameters may be modified in an arbitrary order, at any of the tabs, and
will be maintained as pending to apply until either applied or reset by the
user.

.. important::
  While editing configuration in the ``expconf`` widget, the experiment
  configuration on the server may have changed, for example, another
  ``expconf`` instance applied changes or a running macro changed it
  programmatically. This is notified to the user with a pop-up dialog
  offering the user to either keep the local version of the experiment
  configuration or to load the new configuration from the server. Be aware that
  the second option will **override all your local changes**. It is also
  possible to use the ``expconf`` widget in *slave* mode and automatically
  update on the server changes. You can enable/disable the "Auto update" mode
  from the context menu.


This widget is usually present in sardana-aware Taurus GUIs and is also invoked
by the ``expconf`` command in :ref:`Spock<sardana-spock>`.



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
* show/hide online plots for the current scan.

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

.. _expconf_ui_showplots:

View current scan plot(s)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Plots need to be configured previously as explained in the
:ref:`channel configuration <expconf_ui_measurementgroup_channel>`
(plot type and plot axes).
Running a scan will spawn a panel on taurusgui with the plot. The number of
panels that will spawn is defined in the
:ref:`channel configuration <expconf_ui_measurementgroup_channel>`.

If the configuration hasn't been changed, a new scan will overwrite the previous plots.

Plots can also be seen with spock's command ``showscan online``.

.. _expconf_ui_snapshot_group:

Snapshot group
~~~~~~~~~~~~~~

You can configure the snapshot group with the Experiment Configuration widget.
To do so, go to the **Snapshot Group** tab.

.. figure:: /_static/expconf-snapshot-group.png
   :width: 100%
   :figwidth: 100%
   :align: center

   Snapshot Group tab.

This tab provides the device tree browser for both Sardana elements and external
devices (currently only Tango is supported as an external source).
You can add elements to the snapshot group by just dragging them from the tree
browser and dropping them onto the list below.

.. note:: Settings in this tab alter :ref:`prescansnapshot` environment variable.

.. _expconf_ui_storage:

Storage
~~~~~~~

The ``expconf`` widget provides a way to configure the scan storage paths.
These settings are in the **Storage** tab.

.. figure:: /_static/expconf-storage.png
   :width: 100%
   :figwidth: 100%
   :align: center

   Storage configuration tab.

You can specify multiple files as a comma-separated list. Remeber that the path
you set is a path on Sardana server machine.

.. note:: Settings in this tab alter :ref:`scanfile`, :ref:`scandir` and :ref:`datacompressionrank`
  environment variables.
