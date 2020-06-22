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

Instruments are created in the Pool and populated from the elements that want
to be added to it. Example how to configure Instruments from Spock::

  Pool_demo1_1.CreateInstrument(['/slit','NXcollimator'])
  mot01.instrument = '/slit'
  mot02.instrument = '/slit'
  gap01.instrument = '/slit'
  offset01.instrument = '/slit'
  Pool_demo1_1.CreateInstrument(['/mirror','NXmirror'])
  mot03.instrument = '/mirror'
  mot04.instrument = '/mirror'
  Pool_demo1_1.CreateInstrument(['/monitor','NXmonitor'])
  ct01.instrument = '/monitor'

  
.. seealso::


    :class:`~sardana.pool.poolinstrument.PoolInstrument`
        the instrument class :term:`API`   
   
