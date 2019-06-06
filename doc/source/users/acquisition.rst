.. _sardana-acquisition:

============
Acquisition
============

Measurement group simultaneous usage
-------------------------------------
Sardana does not allow that the elements involved in an acquisition action can
be used in another one. If you try to use a channel or a synchronizer element
that is participating in another acquisition, Sardana will raise an error.

So elements can not participate concurrently in two measurement group
(:ref:`sardana-measurementgroup-overview`) nor single channel acquisitions.
