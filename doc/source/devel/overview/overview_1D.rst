.. currentmodule:: sardana.pool

.. _sardana-1d-overview:

=======================
1D channel overview
=======================

The 1D represents an experimental channel which acquisition result is a
spectrum value. It is foreseen to interface with :term:`MCA` or position
sensitive detectors.

The acquisition operation on a 1D channel is executed over the integration
time specified by the user. 1D channels can be controlled by either software
or hardware synchronization (:ref:`Trigger/Gate <sardana-triggergate-overview>`)
and multiple repetitions, also specified by the user are, are possible within
the same acquisition operation.

.. seealso::

    :ref:`sardana-1d-api`
        the 1D experiment channel :term:`API` 

    :class:`~sardana.tango.pool.OneDExpChannel.OneDExpChannel`
        the 1D experiment channel tango device :term:`API`
