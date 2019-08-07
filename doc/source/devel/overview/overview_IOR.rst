.. currentmodule:: sardana.pool

.. _sardana-ior-overview:

=======================
I/O register overview
=======================

The IOR is a generic element which allows to write/read from a given hardware
register a value. This value type may be one of: :class:`int`,
:class:`float`, :class:`bool` but the hardware usually expects a fixed type
for a given register.

In contrary to the writing of the :ref:`motor's <sardana-motor-overview>`
position attribute the writing of the IOR's value attribute is an instant
operation.

The IOR has a very wide range of applications, for example it can serve to
control the :term:`PLC` registers.

.. seealso::

    :ref:`sardana-ior-api`
        the I/O register :term:`API` 

    :class:`~sardana.tango.pool.IORegister.IORegister`
        the I/O register tango device :term:`API`
