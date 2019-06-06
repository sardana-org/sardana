.. _sardana-acquisition:

============
Acquisition
============

Measurement group simultaneous usage
-------------------------------------
Sardana does not allow that the elements involved in an acquisition action can
be used in another aone. If you try to use a channel or a
synchronizer element that is participating in another acquisition,
Sardana will raise an error.

So elements can not participate concurrently in two measurement groups:ref:`sardana-measurementgroup-overview`
neither in a single channel acquisition.



