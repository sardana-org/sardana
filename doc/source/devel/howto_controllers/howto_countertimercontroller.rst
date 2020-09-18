.. currentmodule:: sardana.pool.controller

.. _sardana-countertimercontroller-howto-basics:

=======================================
How to write a counter/timer controller
=======================================

.. important::
    Counter/timer controller :term:`API` was extended in SEP18_ but this is
    still not documented in this chapter. Please check the said SEP for more
    information about the additional :term:`API` or eventual changes.


The basics
----------

An example of a hypothetical *Springfield* counter/timer controller will be build
incrementally from scratch to aid in the explanation.

By now you should have read :ref:`the general controller basics <sardana-controller-api>` chapter. You should
be able to create a CounterTimerController with:

- a proper constructor,
- add and delete axis methods
- get axis state


.. code-block:: python

    import springfieldlib
		
    from sardana.pool.controller import CounterTimerController

    from sardana import State
		
    class SpringfieldCounterTimerController(CounterTimerController):

        def __init__(self, inst, props, *args, **kwargs):
            super(SpringfieldCounterTimerController, self).__init__(inst, props, *args, **kwargs)

            # initialize hardware communication
            self.springfield = springfieldlib.SpringfieldCounterHW()

            # do some initialization
            self._counters = {}

        def AddDevice(self, axis):
            self._counters[axis] = True 

        def DeleteDevice(self, axis):
            del self._counters[axis]

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

The examples use a :mod:`springfieldlib` module which emulates a counter/timer
hardware access library.

The :mod:`springfieldlib` can be downloaded from
:download:`here <springfieldlib.py>`.

The Springfield counter/timer controller can be downloaded from
:download:`here <sf_ct_ctrl.py>`.

The following code describes a minimal *Springfield* base counter/timer controller
which is able to return both the state and value of an individual counter as
well as to start an acquisition:

.. literalinclude:: sf_ct_ctrl.py
   :pyobject: SpringfieldBaseCounterTimerController

.. _sardana-countertimercontroller-howto-state:

Get counter state
~~~~~~~~~~~~~~~~~

To get the state of a counter, sardana calls the
:meth:`~sardana.pool.controller.Controller.StateOne` method. This method
receives an axis as parameter and should return either:

    - state (:obj:`~sardana.sardanadefs.State`) or
    - a sequence of two elements:
        - state (:obj:`~sardana.sardanadefs.State`)
        - status (:obj:`str`)

The state should be a member of :obj:`~sardana.sardanadefs.State` (For backward
compatibility reasons, it is also supported to return one of
:class:`PyTango.DevState`). The status could be any string.

.. _sardana-countertimercontroller-howto-load:

Load a counter
~~~~~~~~~~~~~~

To load a counter with either the integration time or the monitor counts,
sardana calls the :meth:`~sardana.pool.controller.Loadable.LoadOne` method.
This method receives axis, value and repetitions parameters. For the moment
let's focus on the first two of them.

Here is an example of the possible implementation of
:meth:`~sardana.pool.controller.Loadable.LoadOne`:

.. code-block:: python
    :emphasize-lines: 3

    class SpringfieldCounterTimerController(CounterTimerController):

        def LoadOne(self, axis, value, repetitions, latency):
            self.springfield.LoadChannel(axis, value)

.. _sardana-countertimercontroller-howto-value:

Get counter value
~~~~~~~~~~~~~~~~~

To get the counter value, sardana calls the
:meth:`~sardana.pool.controller.Readable.ReadOne` method. This method
receives an axis as parameter and should return a valid counter value. Sardana
notifies the pseudo counters about the new counter value so they can be updated
(see :ref:`sardana-pseudocounter-overview` for more details).

Here is an example of the possible implementation of
:meth:`~sardana.pool.controller.Readable.ReadOne`:

.. code-block:: python
    :emphasize-lines: 3

    class SpringfieldCounterTimerController(CounterTimerController):

        def ReadOne(self, axis):
            value = self.springfield.getValue(axis)
            return value

.. _sardana-countertimercontroller-howto-start:

Start a counter
~~~~~~~~~~~~~~~

When an order comes for sardana to start a counter, sardana will call the
:meth:`~sardana.pool.controller.Startable.StartOne` method. This method receives
an axis as parameter. The controller code should trigger the hardware acquisition.

Here is an example of the possible implementation of
:meth:`~sardana.pool.controller.Startable.StartOne`:

.. code-block:: python
    :emphasize-lines: 3

    class SpringfieldCounterTimerController(CounterTimerController):

        def StartOne(self, axis, value):
            self.springfield.StartChannel(axis)

As soon as :meth:`~sardana.pool.controller.Startable.StartOne` is invoked,
sardana expects the counter to be acquiring. It enters a high frequency acquisition
loop which asks for the counter state through calls to
:meth:`~sardana.pool.controller.Controller.StateOne`. It will keep the loop
running as long as the controller responds with ``State.Moving``.
If :meth:`~sardana.pool.controller.Controller.StateOne` raises an exception
or returns something other than ``State.Moving``, sardana will assume the counter
is stopped and exit the acquisition loop.

For an acquisition to work properly, it is therefore, **very important** that
:meth:`~sardana.pool.controller.Controller.StateOne` responds correctly.

.. _sardana-countertimercontroller-howto-stop:

Stop a counter
~~~~~~~~~~~~~~

It is possible to stop a counter when it is acquiring. When sardana is ordered to
stop a counter acquisition, it invokes the :meth:`~sardana.pool.controller.Stopable.StopOne`
method. This method receives an axis parameter. The controller should make
sure the desired counter is *gracefully* stopped.

Here is an example of the possible implementation of
:meth:`~sardana.pool.controller.Stopable.StopOne`:

.. code-block:: python
    :emphasize-lines: 3

    class SpringfieldCounterTImerController(CounterTimerController):

        def StopOne(self, axis):
            self.springfield.StopChannel(axis)

.. _sardana-countertimercontroller-howto-abort:

Abort a counter
~~~~~~~~~~~~~~~

In an emergency situation, it is desirable to abort an acquisition
*as fast as possible*. When sardana is ordered to abort a counter acquisition,
it invokes the :meth:`~sardana.pool.controller.Stopable.AbortOne`
method. This method receives an axis parameter. The controller should make
sure the desired counter is stopped as fast as it can be done.

Here is an example of the possible implementation of
:meth:`~sardana.pool.controller.Stopable.AbortOne`:

.. code-block:: python
    :emphasize-lines: 3

    class SpringfieldCounterTimerController(CounterTimerController):

        def AbortOne(self, axis):
            self.springfield.AbortChannel(axis)

.. _sardana-countertimercontroller-howto-timermonitor:

Timer and monitor roles
-----------------------

Usually counters can work in either of two modes: timer or monitor. In both of
them, one counter in a group is assigned a special role to control when
the rest of them should stop counting. The stopping condition is based on the
integration time in case of the timer or on the monitor counts in case of the
monitor. The assignment of this special role is based on the measurement group
:ref:`sardana-measurementgroup-overview-configuration`. The controller receives
this configuration (axis number) via the controller parameter ``timer``
and ``monitor``. The currently used acquisition mode is set via the controller
parameter ``acquisition_mode``.

Controller may announce its default timer axis with the
:obj:`~sardana.pool.controller.Loadable.default_timer` class attribute.

.. _sardana-countertimercontroller-howto-advanced:

Advanced topics
---------------

.. _sardana-countertimercontroller-howto-timestamp-value:

Timestamp a counter value
~~~~~~~~~~~~~~~~~~~~~~~~~

When you read the value of a counter from the hardware sometimes it is
necessary to associate a timestamp with that value so you can track the
value of a counter in time.

If sardana is executed as a Tango device server, reading the value
attribute from the counter device triggers the execution of your controller's
:meth:`~sardana.pool.controller.Readable.ReadOne` method. Tango responds with
the value your controller returns from the call to
:meth:`~sardana.pool.controller.Readable.ReadOne` and automatically assigns
a timestamp. However this timestamp has a certain delay since the time the
value was actually read from hardware and the time Tango generates the timestamp.

To avoid this, sardana supports returning in
:meth:`~sardana.pool.controller.Readable.ReadOne` an object that contains both
the value and the timestamp instead of the usual :class:`numbers.Number`.
The object must be an instance of :class:`~sardana.sardanavalue.SardanaValue`.

Here is an example of associating a timestamp in
:meth:`~sardana.pool.controller.Readable.ReadOne`:

.. code-block:: python

    import time
    from sardana.pool.controller import SardanaValue

    class SpringfieldCounterTimerController(CounterTimerController):

       def ReadOne(self, axis):
           return SardanaValue(value=self.springfield.getValue(axis),
                               timestamp=time.time())

If your controller communicates with a Tango device, Sardana also supports
returning a :class:`~PyTango.DeviceAttribute` object. Sardana will use this
object's value and timestamp. Example:

.. code-block:: python

    class TangoCounterTimerController(CounterTimerController):

       def ReadOne(self, axis):
           return self.device.read_attribute("value")

.. _sardana-countertimercontroller-howto-mutliple-acquisition:

Multiple acquisition synchronization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This chapter describes an extended :term:`API` that allows you to better
synchronize acquisitions involving more than one counter, as well as optimize
hardware communication (in case the hardware interface also supports this).

Often it is the case that the experiment/procedure the user runs requires to
acquire more than one counter at the same time
(see :ref:`sardana-measurementgroup-overview`).
Imagine that the user requires counter at axis 1 and counter at axis 2 to be
acquired.
Your controller will receive two consecutive calls to
:meth:`~sardana.pool.controller.Startable.StartOne`:

.. code-block:: python

    StartOne(1)
    StartOne(2)

and each StartOne will probably connect to the hardware (through serial line,
socket, Tango_ or EPICS_) and ask the counter to be started.
This will do the job but, there will be a slight desynchronization between the
two counters because hardware call of counter 1 will be done before hardware call
to counter 2.

Sardana provides an extended *start acquisition* which gives you the possibility
to improve the synchronization (and probably reduce communications) but your
hardware controller must somehow support this feature as well.

The complete start acquisition :term:`API` consists of four methods:

    - :meth:`~sardana.pool.controller.Startable.PreStartAll`
    - :meth:`~sardana.pool.controller.Startable.PreStartOne`
    - :meth:`~sardana.pool.controller.Startable.StartOne`
    - :meth:`~sardana.pool.controller.Startable.StartAll`

Except for :meth:`~sardana.pool.controller.Startable.StartOne`, the
implementation of all other start methods is optional and their default
implementation does nothing (:meth:`~sardana.pool.controller.Startable.PreStartOne`
actually returns ``True``).

So, actually, the algorithm for counter acquisition start in sardana is::

    /FOR/ Each controller(s) implied in the acquisition
        - Call PreStartAll()
    /END FOR/

    /FOR/ Each controller(s) implied in the acquisition
        /FOR/ Each counter(s) implied in the acquisition
            - ret = PreStartOne(counter to acquire, new position)
            - /IF/ ret is not true
                /RAISE/ Cannot start. Counter PreStartOne returns False
            - /END IF/
            - Call StartOne(counter to acquire, new position)
        /END FOR/
    /END FOR/

    /FOR/ Each controller(s) implied in the acquisition
        - Call StartAll()
    /END FOR/

The controllers over which we iterate in the above pseudo code are organized
so the master timer/monitor controller is the last one to be called. Similar order of
iteration applies to the counters of a given controller, so the timer/monitor
is the last one to be called.

You can assign the master controller role with the order of the controllers
in the measurement group. There is one master per each of the following
synchronization modes: :attr:`~sardana.pool.pooldefs.AcqSynch.SoftwareTrigger`
and :attr:`~sardana.pool.pooldefs.AcqSynch.SoftwareStart`. This order must be
set within the measurement group :ref:`sardana-measurementgroup-overview-configuration`.

So, for the example above where we acquire two counters, the complete sequence of
calls to the controller is:

.. code-block:: python

    PreStartAll()

    if not PreStartOne(1):
        raise Exception("Cannot start. Counter(1) PreStartOne returns False")
    if not PreStartOne(2):
        raise Exception("Cannot start. Counter(2) PreStartOne returns False")

    StartOne(1)
    StartOne(2)

    StartAll()

Sardana assures that the above sequence is never interrupted by other calls,
like a call from a different user to get counter state.
    
Suppose the springfield library tells us in the documentation that:

    ... to acquire multiple counters at the same time use::

        startCounters(seq<axis>)

    Example::

        startCounters([1, 2])

We can modify our counter controller to take profit of this hardware feature:

.. code-block:: python

    class SpringfieldCounterTimerController(MotorController):

        def PreStartAll(self):
            # clear the local acquisition information dictionary
            self._counters_info = []

        def StartOne(self, axis):
            # store information about this axis motion
            self._counters_info.append(axis)

        def StartAll(self):
            self.springfield.startCounters(self._counters_info)

Hardware synchronization
~~~~~~~~~~~~~~~~~~~~~~~~

The synchronization achieved in :ref:`sardana-countertimercontroller-howto-mutliple-acquisition`
may not be enough when it comes to acquiring with multiple controllers at the
same time or to executing multiple acquisitions in a row.
Some of the controllers can be synchronized on an external hardware
event and in this case several important aspects needs to be taken into account.

Synchronization type
""""""""""""""""""""

First of all the controller needs to know which type of synchronization will
be used. This is assigned on the measurement group
:ref:`sardana-measurementgroup-overview-configuration` level. The controller
receives one of the :class:`~sardana.pool.pooldefs.AcqSynch` values via the
controller parameter ``synchronization``.

The selected mode will change the behavior of the counter after the
:meth:`~sardana.pool.controller.Startable.StartOne` is invoked. In case one of
the software modes was selected, the counter will immediately start acquiring.
In case one of the hardware modes was selected, the counter will immediately
get armed for the hardware events, and will wait with the acquisition until they
occur.

Here is an example of the possible implementation of 
:meth:`~sardana.pool.controller.Controller.SetCtrlPar`:

.. code-block:: python
    :emphasize-lines: 3

    from sardana.pool import AcqSynch

    class SpringfieldCounterTimerController(CounterTimerController):

        SynchMap = {
            AcqSynch.SoftwareTrigger : 1,
            AcqSynch.SoftwareGate : 2,
            AcqSynch.HardwareTrigger: 3,
            AcqSynch.HardwareGate: 4
        }

        def SetCtrlPar(self, name, value):
            super(SpringfieldMotorController, self).SetCtrlPar(name, value)
            synchronization = SynchMap[value]
            if name == "synchronization":
                self.springfield.SetSynchronization(synchronization)


Multiple acquisitions
"""""""""""""""""""""

It is a very common scenario to execute multiple hardware synchronized
acquisitions in a row. One example of this type of measurements are the
:ref:`sardana-users-scan-continuous`. The controller receives the number of
acquisitions via the third argument of the
:meth:`~sardana.pool.controller.Loadable.LoadOne` method.

Here is an example of the possible implementation of
:meth:`~sardana.pool.controller.Loadable.LoadOne`:

.. code-block:: python
    :emphasize-lines: 3

    class SpringfieldCounterTimerController(CounterTimerController):

        def LoadOne(self, axis, value, repetitions, latency):
            self.springfield.LoadChannel(axis, value)
            self.springfield.SetRepetitions(repetitions)
            return value

Get counter values
""""""""""""""""""

During the hardware synchronized acquisitions the counter values are usually
stored in the hardware buffers. Sardana enters a high frequency acquisition loop
after the :meth:`~sardana.pool.controller.Startable.StartOne` is invoked
which, apart of asking for the counter state through calls to the
:meth:`~sardana.pool.controller.Controller.StateOne` method, will try to retrieve
the counter values using the :meth:`~sardana.pool.controller.Readable.ReadOne` method.
It will keep the loop running as long as the controller responds with ``State.Moving``.
Sardana executes one extra readout after the state has changed in order to retrieve
the final counter values.

The :meth:`~sardana.pool.controller.Readable.ReadOne` method is used indifferently
of the selected synchronization but its return values should depend on it and
can be:

     - a single counter value: either :class:`float` or :obj:`~sardana.sardanavalue.SardanaValue`
       in case of the :attr:`~sardana.pool.pooldefs.AcqSynch.SoftwareTrigger` or
       :attr:`~sardana.pool.pooldefs.AcqSynch.SoftwareGate` synchronization

     - a sequence of counter values: either :class:`float` or :obj:`~sardana.sardanavalue.SardanaValue`
       in case of the :attr:`~sardana.pool.pooldefs.AcqSynch.HardwareTrigger` or
       :attr:`~sardana.pool.pooldefs.AcqSynch.HardwareGate` synchronization

Sardana assumes that the counter values are returned in the order of acquisition
and that there are no gaps in between them.

.. todo:: document how to skip the readouts while acquiring


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
.. _SEP18: http://www.sardana-controls.org/sep/?SEP18.md
