.. currentmodule:: sardana.pool.controller

.. _sardana-triggergatecontroller-howto-basics:

=======================================
How to write a trigger/gate controller
=======================================

The basics
----------

An example of a hypothetical *Springfield* trigger/gate controller will be build
incrementally from scratch to aid in the explanation.

By now you should have read the general controller basics chapter. You should
be able to create a TriggerGateController with:

- a proper constructor
- add and delete axis methods
- get axis state


.. code-block:: python

    import springfieldlib

    from sardana.pool.controller import TriggerGateController

    class SpringfieldTriggerGateController(TriggerGateController):

        def __init__(self, inst, props, *args, **kwargs):
            super(SpringfieldTriggerGateController, self).__init__(inst, props, *args, **kwargs)

            # initialize hardware communication
            self.springfield = springfieldlib.SpringfieldTriggerHW()

            # do some initialization
            self._triggers = {}

        def AddDevice(self, axis):
            self._triggers[axis] = True 

        def DeleteDevice(self, axis):
            del self._triggers[axis]

        StateMap = {
            1 : State.On,
            2 : State.Moving,
            3 : State.Fault,
        }

        def StateOne(self, axis):
            springfield = self.springfield
            state = self.StateMap[ springfield.getState(axis) ]
            status = springfield.getStatus(axis)
            return state, status

The examples use a :mod:`springfieldlib` module which emulates a trigger/gate
hardware access library.

The :mod:`springfieldlib` can be downloaded from
:download:`here <springfieldlib.py>`.

The Springfield trigger/gate controller can be downloaded from
:download:`here <sf_tg_ctrl.py>`.

The following code describes a minimal *Springfield* base trigger/gate controller
which is able to return the state of an individual trigger as well as to start
a synchronization:

.. literalinclude:: sf_tg_ctrl.py
   :pyobject: SpringfieldBaseTriggerGateController

.. _sardana-triggergatecontroller-howto-state:

Get trigger state
~~~~~~~~~~~~~~~~~

To get the state of a trigger, sardana calls the
:meth:`~sardana.pool.controller.Controller.StateOne` method. This method
receives an axis as parameter and should return either:

    - state (:obj:`~sardana.sardanadefs.State`) or
    - a sequence of two elements:
        - state (:obj:`~sardana.sardanadefs.State`)
        - status (:obj:`str`)

The state should be a member of :obj:`~sardana.sardanadefs.State` (For backward
compatibility reasons, it is also supported to return one of
:class:`PyTango.DevState`). The status could be any string.

.. _sardana-TriggerGateController-howto-load:

Load synchronization description
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To load a trigger with the synchronization description
sardana calls the :meth:`~sardana.pool.controller.Synchronizer.SynchOne` method.
This method receives axis and synchronization parameters.

Here is an example of the possible implementation of
:meth:`~sardana.pool.controller.Synchronizer.SynchOne`:

.. code-block:: python
    :emphasize-lines: 3

    class SpringfieldTriggerGateController(TriggerGateController):

        def SynchOne(self, axis, synchronization):
            self.springfield.SynchChannel(axis, synchronization)

.. _sardana-triggergatecontroller-howto-synchronization:

Synchronization description
###########################

Synchronization is a data structure following a special convention. It is
composed from the groups of equidistant intervals described by: the initial
point and delay, total and active intervals and the number of repetitions.
These information can be expressed in different synchronization domains if
necessary: time and/or position.

.. figure:: /_static/synchronization_description.png
  :align: center
  :width: 680

  This sketch depicts parameters describing a group.

Sardana defines two enumeration classes to help in manipulations of the
synchronization description. The :class:`~sardana.pool.pooldefs.SynchParam` defines the
parameters used to describe a group. The :class:`~sardana.pool.pooldefs.SynchDomain`
defines the possible domains in which a parameter may be expressed.

The following code demonstrates creation of a synchronization description
expressed in time and position domains (moveable's velocity = 10 units/second
and acceleration time = 0.1 second). It will generate 10 synchronization pulses
of length 0.1 second equally spaced on a distance of 100 units.

.. code-block:: python

    from sardana.pool import SynchParam, SynchDomain

    synchronization = [
        {
            SynchParam.Delay:   {SynchDomain.Time: 0.1, SynchDomain.Position: 0.5},
            SynchParam.Initial: {SynchDomain.Time: None, SynchDomain.Position: 0},
            SynchParam.Active:  {SynchDomain.Time: 0.1, SynchDomain.Position: 1},
            SynchParam.Total:   {SynchDomain.Time: 1, SynchDomain.Position: 10},
            SynchParam.Repeats: 10,
        }
    ]


.. _sardana-TriggerGateController-howto-start:

Start a trigger
~~~~~~~~~~~~~~~

When an order comes for sardana to start a trigger, sardana will call the
:meth:`~sardana.pool.controller.Startable.StartOne` method. This method receives
an axis as parameter. The controller code should trigger the hardware acquisition.

Here is an example of the possible implementation of
:meth:`~sardana.pool.controller.Startable.StartOne`:

.. code-block:: python
    :emphasize-lines: 3

    class SpringfieldTriggerGateController(TriggerGateController):

        def StartOne(self, axis):
            self.springfield.StartChannel(axis)

As soon as :meth:`~sardana.pool.controller.Startable.StartOne` is invoked,
sardana expects the trigger to be running. It enters a high frequency
synchronization loop which asks for the trigger state through calls to
:meth:`~sardana.pool.controller.Controller.StateOne`. It will keep the loop
running as long as the controller responds with ``State.Moving``.
If :meth:`~sardana.pool.controller.Controller.StateOne` raises an exception
or returns something other than ``State.Moving``, sardana will assume the trigger
is stopped and exit the synchronization loop.

For an synchronization to work properly, it is therefore, **very important** that
:meth:`~sardana.pool.controller.Controller.StateOne` responds correctly.

.. _sardana-triggergatecontroller-howto-stop:

Stop a trigger
~~~~~~~~~~~~~~

It is possible to stop a trigger when it is running. When sardana is ordered to
stop a trigger synchronization, it invokes the
:meth:`~sardana.pool.controller.Stopable.StopOne` method. This method receives
an axis parameter. The controller should make sure the desired trigger is
*gracefully* stopped.

Here is an example of the possible implementation of
:meth:`~sardana.pool.controller.Stopable.StopOne`:

.. code-block:: python
    :emphasize-lines: 3

    class SpringfieldTriggerGateController(TriggerGateController):

        def StopOne(self, axis):
            self.springfield.StopChannel(axis)

.. _sardana-triggergatecontroller-howto-abort:

Abort a trigger
~~~~~~~~~~~~~~~

In an emergency situation, it is desirable to abort a synchronization
*as fast as possible*. When sardana is ordered to abort a trigger synchronization,
it invokes the :meth:`~sardana.pool.controller.Stopable.AbortOne`
method. This method receives an axis parameter. The controller should make
sure the desired trigger is stopped as fast as it can be done.

Here is an example of the possible implementation of
:meth:`~sardana.pool.controller.Stopable.AbortOne`:

.. code-block:: python
    :emphasize-lines: 3

    class SpringfieldTriggerGateController(TriggerGateController):

        def AbortOne(self, axis):
            self.springfield.AbortChannel(axis)


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
