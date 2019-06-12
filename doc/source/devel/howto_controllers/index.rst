.. currentmodule:: sardana.pool.controller

.. _sardana-controller-howto:

===================
Writing controllers
===================

This chapter provides the necessary information to write controllers in
sardana.

Before writing a new controller you should check the `controller plugin
register <https://sourceforge.net/p/sardana/controllers.git>`_.
There's a high chance that somebody already wrote the plugin for your hardware.

An overview of the pool controller concept can be found 
:ref:`here <sardana-controller-overview>`.

The complete controller :term:`API` can be found
:ref:`here <sardana-controller-api>`.

First, the common interface to all controller types is explained. After, a
detailed chapter will focus on each specific controller type:

.. toctree::
    :maxdepth: 1

    howto_controller
    howto_motorcontroller
    howto_countertimercontroller
    howto_0dcontroller
    howto_1dcontroller
    howto_2dcontroller
    howto_triggergatecontroller
    howto_ioregistercontroller
    howto_pseudomotorcontroller
    howto_pseudocountercontroller

.. seealso:: See the :ref:`sardana-adding-elements` section for information on
    how to add, configure and use controllers.

