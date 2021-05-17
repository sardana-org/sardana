.. currentmodule:: sardana.pool.controller

.. _sardana-2dcontroller-howto:

============================
How to write a 2D controller
============================

This chapter provides the necessary information to write a two dimensional (2D)
experimental channel controller in Sardana.

.. contents:: Table of contents
    :depth: 3
    :backlinks: entry

.. _sardana-2dcontroller-general-guide:

General guide
-------------

:ref:`2D experimental channels <sardana-2d-overview>`
together with :ref:`1D experimental channels <sardana-1d-overview>`
and :ref:`counter/timers <sardana-countertimer-overview>`
belong to the same family of *timerable* experimental channels.

To write a 2D controller class you can follow
the :ref:`sardana-countertimercontroller` guide keeping in mind
differences explained in continuation.

.. _sardana-2dcontroller-general-guide-shape:

Get 2D shape
~~~~~~~~~~~~

2D controller should provide a shape of the image which will be produced by
acquisition. The shape can be either static e.g. defined by the detector's
sensor size or dynamic e.g. depending on the detector's (or an intermediate
control software layer e.g. `LImA`_) configuration like :term:`RoI` or binning.

In any case you should provide the shape in the format of a two-element sequence
with horizontal and vertical dimensions using
the :meth:`~sardana.pool.controller.Controller.GetAxisPar` method.

Here is an example of the possible implementation of
:meth:`~sardana.pool.controller.Controller.GetAxisPar`:

.. code-block:: python

    class SpringfieldTwoDController(TwoDController):

        def GetAxisPar(self, axis, par):
            if par == "shape":
                return self.springfield.getShape(axis)

For backwards compatibility, in case of not implementing the ``shape`` axis
parameter, shape will be determined frm the ``MaxDimSize`` of the ``Value``
attribute, currently (4096, 4096).

.. _sardana-2dcontroller-differences-countertimer:

Differences with counter/timer controller
-----------------------------------------

Class definition
~~~~~~~~~~~~~~~~

:ref:`The basics of the counter/timer controller <sardana-countertimercontroller-howto-basics>`
chapter explains how to define the counter/timer controller class.
Here you need to simply inherit from the
`~sardana.pool.controller.TwoDController` class:

.. code-block:: python
    :emphasize-lines: 3

    from sardana.pool.controller import TwoDController

    class SpringfieldTwoDController(TwoDController):

       def __init__(self, inst, props, *args, **kwargs):
            super().__init__(inst, props, *args, **kwargs)

.. _sardana-2dcontroller-getvalue:

Get 2D value
~~~~~~~~~~~~

:ref:`Get counter value <sardana-countertimercontroller-howto-value>` chapter
explains how to read a counter/timer value
using the :meth:`~sardana.pool.controller.Readable.ReadOne` method.
Here you need to implement the same method but its return value
must be a two-dimensional `numpy.array` (or eventually
a `~sardana.sardanavalue.SardanaValue` object) containing an image instead
of a scalar value.

.. _sardana-2dcontroller-getvalues:

Get 2D values
~~~~~~~~~~~~~

:ref:`Get counter values <sardana-countertimercontroller-howto-external-synchronization-get-values>`
chapter explains how to read counter/timer values
using the :meth:`~sardana.pool.controller.Readable.ReadOne` method while
acquiring with external (hardware) synchronization.
Here you need to implement the same method but its return value
must be a sequence with two-dimensional `numpy.array` objects (or eventually
with :obj:`~sardana.sardanavalue.SardanaValue` objects) containing the images
instead of a scalar values.

Advanced topics
---------------

.. _sardana-2dcontroller-valuereferencing:

Working with value referencing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

2D experimental channels may produce big arrays of data at high
frame rate. Reading this data and storing it using sardana
is not always optimal. `SEP2`_ introduced data saving duality, optionally,
leaving the data storage at the responsibility of the detector
(or an intermediate software layer e.g. `LImA`_). In this case sardana
just deals with the reference to the data.

In order to announce the referencing capability the 2D controller must
additionally inherit from the `~sardana.pool.controller.Referable` class:

.. code-block:: python
    :emphasize-lines: 3

    from sardana.pool.controller import TwoDController, Referable

    class SpringfieldTwoDController(TwoDController, Referable):

        def __init__(self, inst, props, *args, **kwargs):
            super().__init__(inst, props, *args, **kwargs)

.. _sardana-2dcontroller-getvaluereference:

Get 2D value reference
""""""""""""""""""""""

To get the 2D value reference, sardana calls the
:meth:`~sardana.pool.controller.Referable.RefOne` method. This method
receives an axis as parameter and should return a URI (`str`)
pointing to the value.

Here is an example of the possible implementation of
:meth:`~sardana.pool.controller.Referable.RefOne`:

.. code-block:: python
    :emphasize-lines: 3

    class SpringfieldTwoDController(TwoDController):

        def RefOne(self, axis):
            value_ref = self.springfield.getValueRef(axis)
            return value_ref

.. _sardana-2dcontroller-getvaluesreferences:

Get 2D values references
""""""""""""""""""""""""

:ref:`Get counter values <sardana-countertimercontroller-howto-external-synchronization-get-values>`
chapter explains how to read counter/timer values
using the :meth:`~sardana.pool.controller.Readable.ReadOne` method while
acquiring with external (hardware) synchronization.
Here you need to implement the :meth:`~sardana.pool.controller.Referable.RefOne`
method and its return value must be a sequence with URIs (`str`)
pointing to the values.

.. _sardana-2dcontroller-configvaluereference:

Configure 2D value reference
""""""""""""""""""""""""""""

Two axis parameters: ``value_ref_pattern`` (`str`)
and ``value_ref_enabled`` (`bool`) are foreseen for configuring where to store
the values and whether to use the value referencing. Here you need to implement
the :meth:`~sardana.pool.controller.Controller.SetAxisPar` method.

Here is an example of the possible implementation of
:meth:`~sardana.pool.controller.Controller.SetAxisPar`:

.. code-block:: python

    class SpringfieldTwoDController(TwoDController):

        def SetAxisPar(self, axis, par, value):
            if par == "value_ref_pattern":
                self.springfield.setValueRefPattern(axis, value)
            elif par == "value_ref_enabled":
                self.springfield.setValueRefEnabled(axis, value)

.. hint::
    Use `Python Format String Syntax <https://docs.python.org/3/library/string.html#format-string-syntax>`_
    e.g. ``file:///tmp/sample1_{index:02d}`` to configure a dynamic value
    referencing using the acquisition index or any other parameter
    (acquisition index can be reset in the
    :ref:`per measurement preparation <sardana-countertimercontroller-per-measurement-preparation>`.
    phase)

When value referencing is used
""""""""""""""""""""""""""""""

Sardana will :ref:`sardana-2dcontroller-getvaluereference` when:

    - channel has referencing capability and it is enabled

Sardana will :ref:`sardana-2dcontroller-getvalue` when any of these
conditions applies:

    - channel does not have referencing capability
    - channel has referencing capability but it is disabled
    - there is a pseudo counter based on this channel

Hence, in some configurations, both methods may be used simultaneously.

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
