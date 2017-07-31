.. currentmodule:: sardana.pool.pooltriggergate

.. _sardana-triggergate-api:

=============================
Trigger/Gate API reference
=============================

The trigger/gate element represents synchronization devices like for example
the digital trigger and/or gate generators that are used to synchronize the
experimental channels.

A trigger/gate has a ``state``, and a ``index`` attributes. The state
indicates at any time if the trigger/gate is stopped, in alarm or moving.
The index, indicates the current trigger/gate index.

.. seealso::

    :ref:`sardana-triggergate-overview`
        the trigger/gate overview 

    :class:`~sardana.tango.pool.TriggerGate.TriggerGate`
        the trigger/gate tango device :term:`API`

..    :class:`~sardana.pool.pooltriggergate.PoolTriggerGate`
..        the trigger/gate class :term:`API`
