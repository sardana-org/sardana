.. currentmodule:: sardana.pool.controller

.. _sardana-0dcontroller-howto-basics:

============================
How to write a 0D controller
============================

.. todo:: complete 0D controller howto

Get 0D state
~~~~~~~~~~~~~~~

To get the state of a 0D, sardana calls the
:meth:`~sardana.pool.controller.Controller.StateOne` method. During the
acquisition loop this method is called only once when it is about to
exit. This method receives an axis as parameter and should return either:

    - state (:obj:`~sardana.sardanadefs.State`) or
    - a sequence of two elements:
        - state (:obj:`~sardana.sardanadefs.State`)
        - status (:obj:`str`)

The state should be a member of :obj:`~sardana.sardanadefs.State` (For backward
compatibility reasons, it is also supported to return one of
:class:`PyTango.DevState`). The status could be any string.

If you don't return a status, sardana will compose a status string with:

    <axis name> is in <state name>

The controller could return on of the four states **On**, **Alarm**, **Fault**
or **Unknown**. Apart of that sardana could set **Moving** or **Fault** state
to the 0D. The Moving state is set during the acquisition loop to indicate that
it is acquiring data. The Fault state is set when the controller software is
not available (impossible to load it).
The controller should return Fault if a fault is reported from the hardware
controller or if the controller software returns an unforeseen state.
The controller should return Unknown state if an exception occurs during the
communication between the pool and the hardware controller.

        
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
