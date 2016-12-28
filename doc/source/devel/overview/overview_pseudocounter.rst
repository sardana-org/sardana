.. currentmodule:: sardana.pool

.. _sardana-pseudocounter-overview:

=======================
Pseudo counter overview
=======================

Pseudo counter acts like an abstraction layer for a counter or a set of
counters allowing the user to see the experiment results by means of an
interface which is more meaningful to him.

One example of a pseudo counter is
:class:`~sardana.pool.poolcontrollers.IoverI0` useful for normalizing the
measurement results in order to make them comparable.

In order to translate the counter values into the pseudo counter values,
calculations have to be performed. The device pool provides
:class:`~sardana.pool.controller.PseudoCounterController` class that can be
overwritten to provide new calculations.

The pseudo counter value gets updated automatically every time one of its
counters value gets updated e.g. when the acquisition is in progress.

Each pseudo counter is represented by a Tango_ device whose interface allows to
obtain a calculation result (scalar value).

.. seealso::

    :ref:`sardana-pseudocounter-api`
        the pseudo counter :term:`API`

    :class:`~sardana.tango.pool.PseudoCounter.PseudoCounter`
        the pseudo counter tango device :term:`API`

.. _Tango: http://www.tango-controls.org