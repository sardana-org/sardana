.. currentmodule:: sardana.taurus.qt.qtgui.extra_sardana

.. _sardanaeditor_ui:


==========================
Sardana Editor's interface
==========================

.. contents::

Sardana editor is an :term:`IDE` for developing sardana plugins such as
:ref:`macros <sardana-macro-howto>` or :ref:`controllers <sardana-controller-howto>`.
It is based on the `Spyder <https://www.spyder-ide.org/>`_ project.

.. image:: /_static/sardanaeditor.png

Some features of the sardana editor are:

* plugins modules navigation
* reload of the plugin code on the server

At the time of writing this document there is no script to directly start the editor
but you can launch it with the following command specifying the door to which you
want to connect::

    python -m sardana.taurus.qt.qtgui.extra_sardana.sardanaeditor <door_name>
    
.. warning::
    Sardana editor is still under development. If you find a bug please check the
    `project issues <www.github.com/sardana-org/sardana/issues>`_ if it was already
    reported and if not report it or directly propose a fix.

 
