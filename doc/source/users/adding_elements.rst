.. _sardana-adding-elements:

====================
Adding real elements
====================

To use your hardware with Sardana you will need to create corresponding elements
first. Each Sardana element uses the controller instance for hardware
communication.

Controllers
===========

To create the controller you can use
:class:`~sardana.macroserver.macros.expert.defctrl` macro::

  defctrl <class> <name> <roles/properties>

The ``<class>`` parameter is a class name for your controller to use and
``<name>`` is the name of the controller instance.

Roles are used to connect the Pseudo controllers with other Sardana elements and
should be specified in the following format: ``role=value``.
Properties are used for controller configuration and use different syntax:
``property value``.
You can specify multiple roles and properties, however when using both, roles
should be supplied before properties.

Examples::

  defctrl DummyMotorController motctrl01
  defctrl IcepapController ipap01 Host 10.0.0.30 Port 5000
  defctrl Slit s0ctrl sl2t=mot01 sl2b=mot02 Gap=s0gap Offset=s0off

Controller axes
===============

Each Sardana element that serves as the interface for hardware is a controller
axis. For example, single motor controller can have multiple axes corresponding
to multiple motors.

With the :class:`~sardana.macroserver.macros.expert.defelem` macro you can
create any type of controller axis::

  defelem <name> <controller> <axis>

``<name>`` is the element name, ``<controller>`` is the controller instance on
which the element should be created and ``<axis>`` is the controller axis number.
The ``<axis>`` default value is ``-1`` which adds the element as first available
axis.

Example::

  defelem mot01 motctrl01 1

The exception are the Pseudo controllers that use pseudo roles instead of the
axes. As roles are specified during controller creation, elements are created
together with the controller instance, and it's not possible to use the
:class:`~sardana.macroserver.macros.expert.defelem` macro with Pseudo controllers.

Motors
======

For creating motors you can use :class:`~sardana.macroserver.macros.expert.defm`
macro instead of :class:`~sardana.macroserver.macros.expert.defelem`.
Its invocation is the same, it's just a shortcut.

Example::

  defm mot02 motctrl01 2

Measurement groups
==================

To create a measurement group use :class:`~sardana.macroserver.macros.expert.defmeas`
macro::

  defmeas <name> <channel_list>

This macro takes the name for the new meaasurement group and the list of
experimetal channels as its arguments. The first channel must be a Sardana internal
channel and at least one of the channels must be a Counter/Timer.

Example::

  defmeas mntgrp01 ct01 ct02 ct03 ct04

Removing elements
=================

Each element can be removed using macro corresponding to the element type.
For controllers use :class:`~sardana.macroserver.macros.expert.udefctrl`.
For controller axes use :class:`~sardana.macroserver.macros.expert.udefelem`.
For measurement groups use :class:`~sardana.macroserver.macros.expert.udefmeas`.

Each of these macros takes the list of element names as the argument.

Remember that you cannot remove controllers with elements, so you must remove the
elements prior to removing the controller.

Useful lists
============

To create a controller it's useful to know which controller classes are available.
To do this use :class:`~sardana.macroserver.macros.lists.lsctrllib` macro.
To see the created controllers use :class:`~sardana.macroserver.macros.lists.lsctrl`.
For lists of motors and experimental channels use :class:`~sardana.macroserver.macros.lists.lsm`
and :class:`~sardana.macroserver.macros.lists.lsexp` respectively.
You can display all measurement groups with :class:`~sardana.macroserver.macros.lists.lsmeas`
macro.

Each of these macros accepts regexp filter as the optional argument.

.. seealso:: The path Sardana uses for loading controller classes can be configured.
             See the Configuration section for details.

.. TODO: Create proper link to the configuration description when it's ready
