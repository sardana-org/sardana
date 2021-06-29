.. _qtspock:

QtSpock
-------

.. note::
        The QtSpock widget has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including its removal) may occur if
        deemed necessary by the core developers.

Sardana provides `qtconsole  <https://qtconsole.readthedocs.io>`_-based widget to
run :ref:`sardana-spock`.

.. image:: /_static/qtspock.png
    :align: center

It provides most of the Spock features and can be launched either
as a standalone application

.. code-block:: console

    python3 -m sardana.taurus.qt.qtgui.extra_sardana.qtspock

or embedded in the :ref:`taurusgui_ui`: (when :ref:`panelcreation` use:
`sardana.taurus.qt.qtgui.extra_sardana.qtspock` module and
`~sardana.taurus.qt.qtgui.extra_sardana.qtspock.QtSpockWidget`
class).

QtSpock requires a spock profile *spockdoor* to be created and upgraded
beforehand (use ``spock`` command to create/upgrade profile).

Below you can find a list of features still not supported by QtSpock:

* block update macros e.g. `~sardana.macroserver.macros.standard.umv` are not
  updated in block but their output is simply appended
* `~sardana.spock.magic.edmac` magic command
