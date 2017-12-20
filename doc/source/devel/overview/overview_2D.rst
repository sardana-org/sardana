.. currentmodule:: sardana.pool

.. _sardana-2d-overview:

=======================
2D channel overview
=======================

The 2D represents an experimental channel which acquisition result is an
image value. It is foreseen to interface with :term:`CCD` or photon-counting
array detectors.

The acquisition operation on a 2D channel is executed over the integration
time specified by the user. 2D channels can be controlled by either software
or hardware synchronization (:ref:`Trigger/Gate <sardana-triggergate-overview>`)
and multiple repetitions, also specified by the user are, are possible within
the same acquisition operation.

.. seealso::

    :ref:`sardana-2d-api`
        the 2D experiment channel :term:`API`

    :class:`~sardana.tango.pool.TwoDExpChannel.TwoDExpChannel`
        the 2D experiment channel tango device :term:`API`
