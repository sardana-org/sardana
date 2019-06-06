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
