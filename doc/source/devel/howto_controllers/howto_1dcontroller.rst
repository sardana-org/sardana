.. currentmodule:: sardana.pool.controller

.. _sardana-1dcontroller-howto-basics:

============================
How to write a 1D controller
============================

The basics
----------

This chapter provides the necessary information to write a one dimensional (1D)
experimental channel controller in Sardana.

.. contents:: Table of contents
    :depth: 3
    :backlinks: entry

.. _sardana-1dcontroller-general-guide:

General guide
-------------

:ref:`1D experimental channels <sardana-1d-overview>`
together with :ref:`2D experimental channels <sardana-2d-overview>`
and :ref:`counter/timers <sardana-countertimer-overview>`
belong to the same family of *timerable* experimental channels.

To write a 1D controller class you can follow
the :ref:`sardana-countertimercontroller` guide keeping in mind
differences explained in continuation.

.. _sardana-1dcontroller-differences-countertimer:

Differences with counter/timer controller
-----------------------------------------

Class definition
~~~~~~~~~~~~~~~~

:ref:`The basics of the counter/timer controller <sardana-countertimercontroller-howto-basics>`
chapter explains how to define the counter/timer controller class.
Here you need to simply inherit from the
`~sardana.pool.controller.OneDController` class:

.. code-block:: python
    :emphasize-lines: 3

    from sardana.pool.controller import OneDController

    class SpringfieldOneDController(OneDController):

       def __init__(self, inst, props, *args, **kwargs):
            super().__init__(inst, props, *args, **kwargs)

.. _sardana-1dcontroller-getvalue:

Get 1D value
~~~~~~~~~~~~

:ref:`Get counter value <sardana-countertimercontroller-howto-value>` chapter
explains how to read a counter/timer value
using the :meth:`~sardana.pool.controller.Readable.ReadOne` method.
Here you need to implement the same method but its return value
must be a one-dimensional `numpy.array` (or eventually
a `~sardana.sardanavalue.SardanaValue` object) containing the spectrum instead
of a scalar value.

.. _sardana-1dcontroller-getvalues:

Get 1D values
~~~~~~~~~~~~~

:ref:`Get counter values <sardana-countertimercontroller-howto-external-synchronization-get-values>`
chapter explains how to read counter/timer values
using the :meth:`~sardana.pool.controller.Readable.ReadOne` method while
acquiring with external (hardware) synchronization.
Here you need to implement the same method but its return value
must be a sequence with one-dimensional `numpy.array` objects (or eventually
with :obj:`~sardana.sardanavalue.SardanaValue` objects) containing spectrums
instead of scalar values.

Advanced topics
---------------

.. _sardana-1dcontroller-valuereferencing:

Working with value referencing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1D experimental channels may produce significant arrays of data at high
frame rate. Reading this data and storing it using sardana
is not always optimal. `SEP2`_ introduced data saving duality, optionally,
leaving the data storage at the responsibility of the detector
(or an intermediate software layer e.g. `LImA`_). In this case sardana
just deals with the reference to the data.

Please refer to :ref:`sardana-2dcontroller-valuereferencing` chapter from
:ref:`sardana-2dcontroller-howto` in order to implement this feature for 1D
controller.

.. _ALBA: http://www.cells.es/
.. _ANKA: http://http://ankaweb.fzk.de/
.. _ELETTRA: http://http://www.elettra.trieste.it/
.. _ESRF: http://www.esrf.eu/
.. _FRMII: http://www.frm2.tum.de/en/index.html
.. _HASYLAB: http://hasylab.desy.de/
.. _MAX-lab: http://www.maxlab.lu.se/maxlab/max4/index.html
.. _SOLEIL: http://www.synchrotron-soleil.fr/

.. _Tango: http://www.tango-controls.org/
.. _Taco: http://www.esrf.eu/Infrastructure/Computing/TACO/
.. _PyTango: http://packages.python.org/PyTango/
.. _Taurus: http://packages.python.org/taurus/
.. _QTango: http://www.tango-controls.org/download/index_html#qtango3
.. _Qt: http://qt.nokia.com/products/
.. _PyQt: http://www.riverbankcomputing.co.uk/software/pyqt/
.. _PyQwt: http://pyqwt.sourceforge.net/
.. _Python: http://www.python.org/
.. _IPython: http://ipython.org/
.. _ATK: http://www.tango-controls.org/Documents/gui/atk/tango-application-toolkit
.. _Qub: http://www.blissgarden.org/projects/qub/
.. _numpy: http://numpy.scipy.org/
.. _SPEC: http://www.certif.com/
.. _EPICS: http://www.aps.anl.gov/epics/
.. _SEP2: http://www.sardana-controls.org/sep/?SEP2.md
.. _LImA: https://lima1.readthedocs.io/en/latest/
