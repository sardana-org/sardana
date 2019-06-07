.. _sardana-acquisition:

===========
Acquisition
===========

Sardana provides advanced solutions for data acqusition. In the data acquisition
process controlled by sardana there is always involved at least one experimental channel.

Two different ways of acquisition exists in Sardana :ref:`sardana-acquisition-expchannel`
and :ref:`sardana-acquisition-measgrp`.

.. _sardana-acquisition-expchannel:

Experimental channel acquisition
--------------------------------

Counter/Timer and 1D and 2D experimental channels can acquire data on its own, without being included in an measurement group.
This can be important for testing purposes or for implementation of own measurement procedures.
The relevant :term:`API` for this feature ist:

- Timer, with three special values:
  
  - __default: Default timer for the controller in use, defined in the controller plugin as a class member. If the element belonging to this axis is not defined in the controller, resetting the controller's timer to the default one raises an exception.
  - __self: the own channel is its timer.
  - None: disable the single acquisition.
 
  Timer and channel have to belong to the same controller.
    
- IntegrationTime
  
- Start

The single acquisition of these channels can be also done with the macro
:class:`~sardana.macroserver.macros.standard.ct`, giving the name of the channel as last argument.

.. _sardana-acquisition-measgrp:

Measurement group acquisition
-----------------------------

Measurement group acquisition allows much more complex measurement processes than
the :ref:`sardana-acquisition-expchannel`. These could be, for example, multiple
channel, multiple repetitions or hardware synchronized acquisitions.

.. important::
   Sardana does not allow that the elements involved in one operation are used in
   another one simultaneously. This rule applies to the data acqusition operations as well.
   For example, if you try to use a channel or synchronizer element that is
   participating in another acquisition sardana will raise an error.
   So elements can not participate concurrently in two
   :ref:`measurement group acquisitions <sardana-acquisition-measgrp>` neither in
   :ref:`experimental channel acquisition <sardana-acquisition-expchannel>`.

Other acquisition features:

* synchronized start of multiple axes acquisition
* hardware/software synchronized acquisition
* measurement preparation
