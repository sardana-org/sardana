.. _sardana-users-motion:

======
Motion
======

Sardana provides advanced solutions for motion. By motion we understand
a controlled process of changing any set point, which could be, a physical motor's position,
temperature set point of a tempertaure controller or a voltage of a power supplier, etc.

In this chapter we just want to list all the features related to motion
and eventually point you to more detailed information. It is not necessary to
understand them if you follow the order of this documentation guide - you will
step by them sooner or later.

We call a sardana element involved in the motion process a :ref:`motor <sardana-motor-overview>`.
Motors can be intergrated into sardana by means of :ref:`MotorController <sardana-motorcontroller-howto-basics>`
plugin classes.

Some times you need to control the motion by means of an interface which
is more meaningful to you, for example, your physical motor acts on a
linear to angular translation and you would like to act on the motor in the
angular dimension. This is solved in sardana by a :ref:`pseudo motor <sardana-pseudomotor-overview>`.
Pseudo motors calculations can be intergrated into sardana by means of :ref:`PseudoMotorController <sardana-pseudomotorcontroller-howto-basics>` plugin classes.

Other motion features:

* :term:`user position` to/from :term:`dial position` conversion
* :ref:`synchronized start of multiple axes motion <sardana-motorcontroller-howto-mutiple-motion>`
* emergency break
* physical motor backlash correction
* :ref:`pseudo motor drift correction <sardana-pseudomotor-api-driftcorrection>`
