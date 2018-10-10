    Title: Extend acquisition and synchronization concepts for SEP2 needs.
    SEP: 18
    State: DRAFT
    Reason:
     New acquisition and synchronization concepts are necessary in order to
      properly integrate 1D and 2D experimental channels in Sardana (SEP2).
    Date: 2018-05-30
    Drivers: Zbigniew Reszela <zreszela@cells>             
    URL: https://github.com/reszelaz/sardana/blob/sep18/doc/source/sep/SEP18.md
    License: http://www.jclark.com/xml/copying.txt
    Abstract:
     SEP6 defined some acquisition and synchronization concepts for the needs
     of the continuous scan. When working on the 1D and 2D experimental 
     channels integration we see that more concepts are necessary. This SEP 
     introduces them.

Terminology
-----------

* Measurement - a measurement process that may, but not necessarily, involve 
multiple acquisitions e.g. measurement group count, continuous scan, step scan.
* Acquisition - a single acquisition e.g. over an integration time, which is a 
part of a measurement

Current Limitations
-------------------

* The Software and Hardware synchronization types terminology is not self 
descriptive. Internal and External terminology describes better these types.
* Some hardware or even the Lima library allows some synchronization modes 
that are not foreseen in Sardana and are necessary.
* Some experimental channels could benefit from preparing them for multiple 
acquisitions before the measurement e.g. software synchronized continuous 
scan or step scan.

Objectives
----------

Overcome the above limitations.

Design
------
1. Use of the measurement group will change:
    * From now on, in order to start the measurement group, it is mandatory
    to prepare it.
    * The measurement group is prepared for a number of starts. The 
    preparation will expire whenever all starts gets called or in case of 
    stop/abort. Afterwards measurement group requires another preparation. 
    **IMPORTANT**: Whenever we drop backwards compatibility explained in the 
    following point starting of the measurement group without prior
    preparation will be considered as wrong usage and will cause exception.
    This will break step scans with attached hooks which measure with the
    same measurement group as used by the scan.
    * Direct start of the measurement group (after prior configuration of
    the integration time or synchronization) will be supported as backwards
    compatibility and the corresponding warning will be logged.
2. Allow different types of preparation of channels - this still depends on
the option selected in the implementation of controllers. The following
assumes option 1.
    * Per measurement preparation with number of starts = n e.g.
    Prepare(One|All) or a controller parameter
    * Per acquisition preparation with repetitions = n e.g. Load(One|All)
3. Extend AcqSynch with two new options:
    * SoftwareStart (which means internal start)
    * HardwareStart (which means external start)
4. Extend AcqSynchType with one new option (supported from expconf):
    * Start
5. Modify acquisition actions (and synchronization action if necessary) so
they support the new concepts added in points 2 and 3.
6. *Extend Generic Scan Framework* (GSF), more precisely scan in step mode
with measurement preparation (number of starts = n) if possible i.e. scan
macro knows beforehand the number of points.
7. Document well that:
    * Software(Trigger|Gate) are synonyms to Internal (Trigger|Gate).
    Internal means that Sardana will synchronize the acquisitions.
    * Hardware(Trigger|Gate) are synonyms to External(Trigger|Gate).
    External means that an external to Sardana object (could be hardware)
    will synchronize the acquisitions.

Implementation
--------------

### GSF

* `SScan` (step scan) implemented according to the following pseudo code:
    * If number of points is known:
        * `prepare(synchronization, starts=n)` where synchronization
        contains the integration time and n means number of scan points
        * `for step in range(n): count_raw()`
    * If number of points is unknown:
        * `while new_step: count()`
* `CTScan` (continuous scan) does not require changes, it simply calls 
`count_continuous`

### Measurement Group

Measurement group is extended by the *prepare* command (with no arguments)
*number of starts* attribute. The use of the attribute is optional and 
it indicates how many times measurement group will be started, with the 
*start* command, to measure according to the synchronization description or 
integration time. When it is not used number of starts of 1 will be assumed.

1. Measurement group - Tango device class
    * Add `Prepare` command.
    * Add `NrOfStarts` (`DevLong`) attribute.
2. Measurement group - core class
    * Add `prepare()` method.
    * Add `nr_of_starts` property. 
3. Backwards compatibility for using just the integration time attribute with
the start command (without calling prepare command in-between) will be
solved in the following way: start command will internally call the prepare.
4. Measurement group - Taurus extension
    * Add `prepare()` method which simply maps to `Prepare` Tango command
    * Add `count_raw` method according to the following pseudo code:
        * `start()`
        * `waitFinish()`
    * Implement `count(integration_time)` method according to the following 
    pseudo 
    code:
        * set `integration_time`
        * set `nr_of_starts=1`
        * `prepare()`
        * `count_raw()`
    * Implement `count_continuous` (previous `measure`) method according to
    the following pseudo code:
        * `prepare()` where synchronization may
        contain the continuous acquisition description
        * `subscribeValueBuffer()`
        * `count_raw()`
        * `unsubscribeValueBuffer()`

### Software synchronizer

* Add `start` and `end` events. Start is emitted before the first `active`
event and end is emitted after the last `passive` event. 

### Acquisition actions

* Add `PoolAcquisitionSoftwareStart` action that will start channels on
software synchronizer `start` event.
* `PoolAcquisitionSoftware` will stop channels on software synchronizer
`end` event. TODO: decide if we wait for the acquisition in progress
until it finises or we stop immediatelly (finish hook could be used if
we choose to wait).

### Controllers

C/T, 1D and 2D controllers (plugins) API is extended. TODO: Choose between
the following options:

#### Option 1

* Add `Preparable` interface with
`PrepareOne(axis, integ_time, repeats, latency_time, starts)` TODO: or
directly add it to the Loadable interface
* Make C/T, 1D and 2D controllers inherit from this interface
* Add extra argument to `LoadOne`, etc. methods of the `Loadable` interface
`latency_time`: `LoadOne(axis, integ_time, repeats, latency_time)`

This option maintains backwards compatibility.

The following examples demonstrates the sequence of calls (only the ones
relevant to the SEP18) of one channel (axis 1) involved in the given
acquisition. This channel is at the same time the timer.

* **step scan** 5 acquisitions x 0.1 s of integration time
```python
PrepareOne(1, 0.1, 1, 0, 5)
for acquisition in range(5):
    LoadOne(1, 0.1, 1, 0)
    StartOne(1)
```

* **continuous scan (hw trigger)** 5 acquisitions x 0.1 s of integration
time and 0.05 s of latency time
```python
PrepareOne(1, 0.1, 5, 0.05, 1)  # latency time can be ignored
LoadOne(1, 0.1, 5, 0.05)  # latency time can be ignored
StartOne(1)
```

* **continuous scan (sw trigger)** 5 acquisitions x 0.1 s of integration
time and 0.05 s of latency time
```python
PrepareOne(1, 0.1, 1, 0.05, 5)  # latency time can be ignored
for trigger in range(5):
    LoadOne(1, 0.1, 1, 0.05)  # latency time can be ignored
    StartOne(1)
```

* **continuous scan (hw gate)** 5 acquisitions x 0.1 s of integration
time and 0.05 s of latency time
```python
PrepareOne(1, 0.1, 5, 0.05, 1)  # integration time and latency time can be ignored
LoadOne(1, 0.1, 5, 0.05)  # integration time and latency time can be ignored
StartOne(1)
```

* **continuous scan (sw gate)** 5 acquisitions x 0.1 s of integration
time and 0.05 s of latency time
```python
PrepareOne(1, 0.1, 1, 0.05, 5)
for gate in range(5):
    LoadOne(1, 0.1, 1, 0.05)  # integration time and latency time can be ignored
    StartOne(1)
```
* **continuous scan (hw start)** 5 acquisitions x 0.1 s of integration
time and 0.05 s of latency time
```python
PrepareOne(1, 0.1, 5, 0.05, 1)
LoadOne(1, 0.1, 5, 0.05)
StartOne(1)
```

* **continuous scan (sw start)** 5 acquisitions x 0.1 s of integration
time and 0.05 s of latency time
```python
PrepareOne(1, 0.1, 5, 0.05, 1)
LoadOne(1, 0.1, 5, 0.05)
StartOne(1)
```

#### Option 2

* Add extra arguments to `LoadOne`, etc. methods of the `Loadable` interface
`latency_time` and `starts` and switch the order of arguments so the API is:
`LoadOne(axis, integ_time, latency_time, repeats, starts)`.
* Make the `LoadOne`, etc. be called only once per measurement, in the
measurement group prepare command.

This option **breaks** backwards compatibility.

The following examples demonstrates the sequence of calls (only the ones
relevant to the SEP18) of one channel (axis 1) involved in the given
acquisition. This channel is at the same time the timer.

* **step scan** 5 acquisitions x 0.1 s of integration time
```python
LoadOne(1, 0.1, 0, 1, 5)
for acquisition in range(5):
    StartOne(1)
```

* **continuous scan (hw trigger)** 5 acquisitions x 0.1 s of integration
time and 0.05 s of latency time
```python
LoadOne(1, 0.1, 0.05, 5, 1)  # latency time can be ignored
StartOne(1)
```

* **continuous scan (sw trigger)**
```python
LoadOne(1, 0.1, 0.05, 1, 5)  # latency time can be ignored
for trigger in range(5):
    StartOne(1)
```

* **continuous scan (hw gate)**
```python
LoadOne(1, 0.1, 0.05, 5, 1)  # integration time and latency time can be ignored
StartOne(1)
```

* **continuous scan (sw gate)**
```python
LoadOne(1, 0.1, 0.05, 1, 5)  # integration time and latency time can be ignored
for gate in range(5):
    StartOne(1)
```

* **continuous scan (hw start)**
```python
LoadOne(1, 0.1, 0.05, 5, 1)
StartOne(1)
```

* **continuous scan (sw start)**
```python
LoadOne(1, 0.1, 0.05, 5, 1)
StartOne(1)
```

#### Option 3

The same as option 2 but maintaining the backwards compatibility in the 
following way:
* Acquisition actions will call the `LoadOne`, etc. methods depending on the
controllers implementations (more precisely using the `inspect.getargspec`
and counting the number of arguments). This will require much more complicated
acquisition actions.

### Dummy C/T controller
Implement `SoftwareStart` and `HardwareStart` in the
`DummyCounterTimerController` - minimal implementation.
