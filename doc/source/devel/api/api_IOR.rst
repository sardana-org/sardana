.. currentmodule:: sardana.pool.poolioregister

.. _sardana-ior-api:

=============================
I/O register API reference
=============================

The IOR is a generic element which allows to write/read from a given hardware
register a value. This value type may be one of: :class:`int`, :class:`float`,
:class:`bool`.

An IOR has a ``state``, and a ``value`` attributes. The state
indicates at any time if the IOR is stopped, in alarm or moving.
The value, indicates the current IOR value.

The available operations are:

write register(value)
    executes write operation on the IOR with the given value

    :meth:`~PoolIORegister.write_register`

.. seealso::

    :ref:`sardana-ior-overview`
        the I/O register overview

    :class:`~sardana.tango.pool.IORegister.IORegister`
        the I/O register tango device :term:`API`

..    :class:`~sardana.pool.poolioregister.PoolIORegister`
..        the I/O register class :term:`API`
