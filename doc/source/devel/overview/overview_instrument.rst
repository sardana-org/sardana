.. currentmodule:: sardana.pool

.. _sardana-instrument-overview:

===================
Instrument overview
===================

An instrument in sardana is a group of sardana elements e.g. motors, counters.
Its general role is to group elements that are somehow related,
this relation reflects in most of the cases the element association
to a laboratory instrument.

Two features uses this information: nexus data storage and the
TaurusGUI panel population.

After creating a new instrument or changing an element from one instrument
to another, Pool, MacroServer and Spock must be restarted, otherwise the
changes will not have effect.


.. seealso::


    :class:`~sardana.pool.poolinstrument.PoolInstrument`
        the instrument class :term:`API`   
   
