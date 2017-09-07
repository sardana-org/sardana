.. currentmodule:: sardana.pool

.. _sardana-triggergate-overview:

=======================
Trigger/gate overview
=======================

The trigger/gate represents synchronization devices like for example the
digital trigger and/or gate generators. Their main role is to synchronize
acquisition of the experimental channels.

Trigger or gate characteristics could be described in either the time and/or
the position configuration domains.

In the time domain, elements are configured in time units (seconds) and
generation of the synchronization signals is based on passing time.

The concept of position domain is based on the relation between
the trigger/gate and the moveable element. In the position domain,
elements are configured in distance units of the moveable element configured as
the feedback source (this could be mm, mrad, degrees, etc.). In this case
generation of the synchronization signals is based on receiving updates from
the source.

.. seealso::

    :ref:`sardana-triggergate-api`
        the trigger/gate :term:`API` 

    :class:`~sardana.tango.pool.TriggerGate.TriggerGate`
        the trigger/gate tango device :term:`API`
