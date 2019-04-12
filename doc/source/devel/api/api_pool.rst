.. currentmodule:: sardana.pool.pool

.. _sardana-pool-api:

=========================
Pool API reference
=========================

The Pool is one of the most important elements in sardana.

This chapter explains the generic pool :term:`API` in the context of 
sardana. In sardana there are, in fact, two Pool :term:`API`\s. To 
better explain why, let's consider the case were sardana server is running 
as a Sardana Tango device server:

Every pool in sardana is represented in the sardana kernel as a
:class:`Pool`. The :class:`Pool` :term:`API` is not directly
accessible from outside the sardana server. This is a low level :term:`API`
that is only accessible to someone writing a server extension to sardana. At
the time of writing, the only available sardana server extension is Tango.

The second pool interface consists on the one provided by the server
extension, which is in this case the one provided by the Tango pool
device interface:
:class:`~sardana.tango.pool.Pool.Pool`. The Tango
pool interface tries to mimic the as closely as possible the
:class:`Pool` :term:`API`.

.. seealso:: 
    
    :ref:`sardana-pool-overview`
        the pool overview 

    :class:`~sardana.tango.pool.Pool.Pool`
        the pool tango device :term:`API`

Each pool has the following attributes:

.. _sardana-pool-api-poolpath:

pool path
----------
    Pool may load user macros and this are discoverable by scanning the
    file system directories configured in macro path.

.. _sardana-pool-api-pythonpath:

python path
-----------
    Macros may need to access to third party Python modules. When these are
    not available to the Python interpreter i.e. exported to the
    ``PYTHONPATH``, one can configure the file system directories where the
    Pool should look for these modules.