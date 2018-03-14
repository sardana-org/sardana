	Title: Continuous Scan Implementation
	SEP: 6
	State: ACCEPTED
	Date: 2013-07-29
	Drivers: Zbigniew Reszela <zreszela@cells.es>
	URL: http://www.sardana-controls.org/sep/?SEP6.md
	License: http://www.jclark.com/xml/copying.txt
	Abstract:
	 Generic Scan Framework requires extension for a new type of scans: continuous scans.
	 Various types of synchronization between moveable and acquisition elements exists:
	 software (so called best effort) and hardware (either position or time driven).
	 The challenge of this SEP is to achieve the maximum generalization and transparency 
	 level between all types of continuous scans (and probably step scans as well). This 
	 design and implementation will require enhancement of the already existing elements of 
	 Sardana: controllers, moveables, experimental channels and measurement group and 
	 probably definition of new elements e.g. triggers. A proof of concept work was already 
	 done at ALBA, and it could be used as a base for the further design and development.


Current situation
=================
In the present situation, step scans can be executed using the software synchronization mode. The software-synchronized continuous scans are already implemented in Sardana as well and are described [here](http://www.sardana-controls.org/en/latest/users/scan.html#continuous-scans). As a proof-of-concept, very limited scan macros that abstracts some specifics of the totally hardware-synchronized systems were added to Sardana in 2013. They require generalization and this SEP aims to provide it.

Specification
==========

Contents
-------------

- Transparency
- Generic Scan Framework
- Measurement Group
- Trigger/Gate
- Experimental Channel
- Data collection, merging and storage
- Data transfer
- Motion


Transparency
-------------------

Sardana scans can be executed in the following modes: step, continuous and hybrid. The main difference between them is how the motion and the acquisition phases are executed. The step scans execute motion and acquisition sequentially, accelerating and decelerating the moveables in between each scan point. The acquisition phase is executed while the moveables are stopped. The continuous scans execute all the acquisitions simultanously to the motion of the moveables from the scan start to the end positions. Acquisitions are synchronized to be executed on the scan intervals commanded by the user. In the hybrid scans motion to each scan point is acompanied with the acquisition from the previous scan point, so the acquisition is also executed while moveables are moving, however they stop in between each scan point.

A step scan can be executed with one of the standard macros e.g. ascan, d2scan, mesh. While the continuous scans developed in this SEP can be executed with their equivalents terminated with *ct* suffix. Basic parameters of the continuous scans are the same as in the step scans and continuous scans add an extra optional parameter latency_time. Also the scan records comprise the same fields as in the step scan. The only difference in the continuous scan records is that the: motor positions and the delta times are filled with the nominal values instead of the real ones. The measurement group configuration should allow to scan in step and continuous modes without the need to reconfigure any parameters, of course if the hardware allows that. For the reference, a different type of the continuous scans, terminated with *c* suffix, is also present in Sardana.

Example of a continuous scan - the absolute equidistant continuous scan:

    ascanct <motor> <start_pos> <final_pos> <nr_interv> <integ_time> <latency_time>

Generic Scan Framework (GSF)
------------------------------------

GSF and its components have basically 3 roles:

* It uses the input parameters of the scan together with the already present configuration of the involved in the scan elements and transforms it into more specific parameters. These parameters are set to the involved elements in the process of preparation to scanning: e.g. move motors to the correct positions, set synchronization specification to the Measurement Group
* Control the scan flow e.g. starts in the correct sequence the involved elements
* Receive the data chunks, compose the scan records and perform the interpolation if necessary, finally passing all the data to the recorders.

User inputs:

* moveable(s)
* start position(s)
* end position(s)
* number of intervals
* integration time
* latency time (optional) - It may be especially useful for acquisitions involving the software synchronized channels. The software overhead may cause acquisitions to be skipped if the previous acquisition is still in progress while the new synchronization event arrives. The *latency time* parameter, by default, has zero value.

Other inputs:

* acceleration times(s), deceleration time(s) and base rate(s) obtained from the Motor(s)
* latency time obtained from the MeasurementGroup

Calculation outputs:

* pre-start and post-end position(s)
* common acceleration and deceleration time
* velocitie(s)
* master (reference) moveable
* synchronization specification

Formulas:

* pre-start, post-end positions, acceleration time, deceleration time and velocity - see Motion chapter
* Synchronization structure (this example describes an equidistant scan of a single physical motor):
* The maximum of the user input latency time and the active measurement group latency time is used.

Parameter | Time | Position
---------- | ---------- | ------ 
Offset | acceleration time | velocity * acceleration time / 2
Initial | None | start position
Active | integration time | integration time * velocity
Total | integration time + latency time | end - start / number of intervals

Repeats = number of intervals + 1

Measurement Group (MG)
-----------------------------
MeasurementGroup is a group element. It aggregates other elements of types ExpChannel (these are CounterTimer, 0D, 1D and 2D ExperimentalChannels) and TriggerGate. The MeasurementGroup's role is to execute acquisitions using the aggregated elements.

The acquisition is synchronized by the TriggerGate elements or by the software synchronizer. The hardware synchronized ExpChannel controllers  are configured with the number of acquisitions to be executed while the software synchronized do not know a priori the number of acqusitions.

Latency time is a new attribute of the measurement group and it introduces an extra dead time in between two consecutive acquisitions. Its value corresponds to the maximum latency time of all the ExpChannel controllers present in the measurement group. It may be especially useful for acquisitions involving software synchronized channels. The software overhead may cause acquisitions to be skipped if the previous acquisition is still in progress while the new synchronization event arrives. The *latency time* parameter, by default, has zero value.

On the MeasurementGroup creation, the software synchronizer is assigned by default to the newly added ExperimentalChannel controllers, so the MeasurementGroup could start measuring without any additional configurations. 

The configuration parameters:

- **Configuration** (type: dictionary) - stores static configuration e.g. which synchronizer is associated to which ExperimentalChannel controller and which synchronization type is used (Trigger or Gate)
- **Synchronization** (type: list of dictionaries) - express the measurement synchronization, it is composed from the groups of equidistant acquisitions described by: the initial point and delay, total and active intervals and the number of repetitions, these information can be expressed in different synchronization domains if necessary (time and/or position) 
- **LatencyTime** (type: float, unit: seconds, access: read only): latency time between two consecutive acquisitions
- **Moveable** (type: string) - full name of the master moveable element

Format of the configuration parameter:

~~~~
dict <str, obj=""> with (at least) keys:
      - 'timer' : the MG master timer channel name / id
      - 'monitor' : the MG master monitor channel name / id
      - 'controllers' : dict <Controller, dict=""> with one entry per controller:
          - ctrl_object : dict<str, dict=""> with (at least) keys:
              - 'timer' : the timer channel name / id
              - 'monitor' : the monitor channel name / id
              - 'synchronization' : 'Trigger' / 'Gate'
              - 'synchronizer': the TriggerGate name / id or 'software' to indicate software synchronizer
              - 'channels' where value is a dict<str, obj=""> with (at least) keys:
                      - ...
~~~~

The configuration parameter had changed during the SEP6 developments. First of all the [feature request #372](https://sourceforge.net/p/sardana/tickets/372/) was developed and the units level disappeared from the configuration. Furthermore the controller parameters _trigger_type_ was renamed to _synchronization_. In both cases one-way backwards compatibility was maintained. That means that the measurement groups created with the previous versions of Sardana are functional. Once their configuration gets saved again (either after modification or simply by re-applying), the configuration is no more reverse compatible. **IMPORTANT: when deploying the SEP6 consider back-up of the measurement groups configurations in case you would need to rollback**

Format of the synchronization parameter:

~~~~
list of dicts <SynchParam, obj> with the following keys:
      - SynchParam.Delay : dict <SynchDomain, float> initial delay (relative to start) expressed in Time and Position* domain
      - SynchParam.Initial : dict <SynchDomain, float> initial point (absolute) expressed in Time and Position* domain
      - SynchParam.Active : dict <SynchDomain, float> active interval (with sign indicating direction) expressed in Time (and Position domain) or Monitor domain
      - SynchParam.Total': dict <SynchDomain, float> total interval (with sign indicating direction) expressed in Time and Position* domain
      - SynchParam.Repeats: <long> - how many times the group has to be repeated
* Position domain is optional - lack of it implicitly forces synchronization in the Time domain e.g. timescan
~~~~

Trigger/Gate
----------------

TriggerGate is a new Sardana element type and it represents devices with trigger and/or gate generation capabilities. Their main role is to synchronize acquisition of the ExpChannel. Trigger or gate characteristics could be described in either time and/or position configuration domains. In the time domain, elements are configured in time units (seconds) and generation of the synchronization signals is based on passing time. The concept of position domain is based on the relation between the TriggerGate and the Moveable element. In the position domain, elements are configured in distance units of the Moveable element configured as the feedback source (this could be mm, mrad, degrees, etc.). In this case generation of the synchronization signals is based on receiving updates from the source.

Each ExpChannel controller can have one TriggerGate element associated to it. Its role is to control at which moment each single measurement has to start in case of trigger or start and stop in case of gate.

The allowed states for TriggerGate element are:

- On - the element is ready to generate synchronization signals
- Moving - the element is currently generating synchronization signals
- Fault - the device is faulty

**Tango interface**

Each TriggerGate element is represented in the Tango world by one device of TriggerGate Tango class. They implement State and Status Tango attributes.

**TriggerGate controller (plug-in)**

A custom TriggerGate controller must inherit from the TriggerGateController class. The dynamic configuration is accessed via the Synch methods. This configuration has the same format as the MeasurementGroup Synchronization parameter.

TriggerGateController API (**bold** are mandatory):

- AddDevice
- DeleteDevice
- PreStateAll
- PreStateOne
- StateAll
- **StateOne**
- PreStartOne
- PreStartAll
- **StartOne**
- StartAll
- StopOne
- StopAll
- **AbortOne**
- AbortAll
- PreSynchOne
- PreSynchAll
- **SynchOne**
- SynchAll
- SetAxisPar and GetAxisPar

In case that the sychronization description contains information in both domains (position and time), the Synch methods should configure the trigger on position and only if not supported by the hardware on time. Similarly the gate duration should be configured on time and only if not supported by the hardware on position. This are only the recommendations to the controllers developers. In some special cases it may be needed to ignore this recommendation. In this case an extra axis attributes could be defined in the controller to control the domain selection.

Sardana provides one TriggerGate controllers DummyTriggerGateController which does not synchronize acquisition and just provides dummy behavior. DummyTriggerGateController imitate the behavior of the hardware with trigger and/or gate signal generation capabilities. It emulates the state machine: changes state from On to Moving on start and from Moving to On based on the configuration parameters or when stopped.

Software synchronizer resides in the core of Sardana and generates software events of type: *active* and *passive*. The acquisition action listens to these events and start or start and stop the acquisition process when they arrive.
In case the MeasurementGroup Synchronization contains position domain characteristics the software synchronizer is added as a listener to the moveable's position attribute. Then the generation of the synchronization events is based on these updates.

**Pool Synchronization action**

PoolSynchronization is the Pool's action in charge of the control of the TriggerGate elements during the generation, which usually take place in the MeasurementGroup acquisition process.

Its **start_action** method executes the following:

- load dynamic configuration to the hardware by calling Synch methods
    - for each controller implied in the generation call PreSynchAll
    - for each axis implied in the generation call PreSynchOne and SynchOne
    - for each controller implied in the generation call SynchAll
- in case the software synchronizer is in use, add the acquisition action as the listener of the software synchronzier
- in case the position domain synchronization is in use it adds the software synchronizer as the listener of the moveable's position updates
- start the involved axes
    - for each controller implied in the generation call PreStartAll
    - for each axis implied in the generation call PreStartOne and StartOne
    - for each controller implied in the generation call StartAll
- for each TriggerGate element implied in the generation set state to Moving

Its **action_loop** method executes the following:

- while there is at least one axis in Moving state:
    - for each controller implied in the generation call PreStateAll
    - for each axis implied in the generation call PreStartOne
    - for each controller implied in the generation call StartAll
    - for each axis implied in the generation call StartOne
    - wait some time
- for each TriggerGate element implied in the generation set state to On

The action_loop waits some time between interrogating controllers for their states. The wait time by default is 0.01 [s].

ExpChannel
-----------------------------

When hardware TriggerGate is associated to the ExpChannel controller, the second one must know how many acquisitions has to be performed. In case of synchronization with triggering signals the controller must also know the integration time. Both of this parameters are configured on the controller level and not the channel level. During the acquisition process hardware synchronized channels may not report data until the end of the acquisition or report data in blocks.

**ExpChannel controller (plug-in)**

Configuration parameters implemented as controller parameters: SetCtrlPar and GetCtrlPar:

- **synchronization** (type: enumeration, options: SoftwareTrigger|SoftwareGate|HardwareTrigger|HardwareGate) - how acquisition will be started or started and stopped
- **timer** (type: integer) - correspnds to the axis number of the timer assigned to this controller *
- **monitor** (type: monitor) - corresponds to the axis number of the monitor assigned to this controller *
- **acquisition_mode** (type: enumeration, options: Timer|Monitor) - corresponds to the selected acquisition mode * 

Configuration parameters pass in LoadOne method:

- **value** (type: float, unit: seconds or counts) - integration time or monitor counts of each single acquisition
- **repetitions** (type: long) - number of single acquisitions executed after the start (it is always 1 for software synchronized acquisition)

Defines static characteristics of the hardware, implemented as controller parameters: GetCtrlPar

- **latency_time** (type: float, unit: seconds) - time required to prepare the hardware for the next hardware trigger or gate 

The *Read* methods usually implement the data retrieval from the device and return the acquired data. The same method is foreseen for software and hardware synchronized acquisitions, both by trigger and gate. In case that access to the data in a device differenciate between the synchronization mode, the *Read* methods would need to implement different cases based on the confiugured synchronization. 
ReadOne method may return data in blocks corresponding to multiple acquisitions or just single values. The following return values are allowed:

* float
* sequence of float e.g. list of floats
* SardanaValue
* sequence of SardanaValue e.g. list of SardanaValues

**Acquisition actions**

Several sub-acquisition actions may participate in the global acquisition, what depends on the involved experimental channels and their synchronization mode. These includes:

* HardwareSynchronizedAcquisition
* SoftwareSynchronizedAcquisition
* 0DAcquisition

**HardwareSynchronizedAcquisition** acts on the ExpChannel synchronized by the hardware TriggerGate controller. 
Their synchronization mode whether trigger or gate does not affect flow of the action.

Prior to the action execution the following parameters are loaded to the involved controllers:

- synchronization
- timer
- monitor
- acquisition_mode

Its **start_action** method executes the following:

- load the involved timer/monitors with integration time/mnitor counts and repetitions
    - for each controller implied in the acquistion call PreLoadAll
    - for the timer/monitor axis implied in the acquisition call PreLoadOne and LoadOne
    - for each controller implied in the acquisition call LoadAll
- start the involved axes
    - for each controller implied in the acquistion call PreStartAll
    - for each axis implied in the acquisition call PreStartOne and StartOne
    - for each controller implied in the acquisition call StartAll
- for each ExpChannel implied in the acquisition set state to Moving

Its **action_loop** method executes the following:

- while there is at least one axis in Moving state:
    - for each controller implied in the acquisition call PreStateAll
    - for each axis implied in the acquisition call PreStartOne
    - for each controller implied in the acquisition call StartAll
    - for each axis implied in the acquisition call StartOne
    - wait some time
    - every certain number of iterations read new data:
        - for each controller implied in the acquisition call PreReadAll
        - for each axis implied in the acquisition call PreReadOne
        - for each controller implied in the acquisition call ReadAll
        - for each axis implied in the acquisition call ReadOne
- for each controller implied in the acquisition call PreReadAll
- for each axis implied in the acquisition call PreReadOne
- for each controller implied in the acquisition call ReadAll
- for each axis implied in the acquisition call ReadOne
- for each ExpChannel implied in the acquisition set state to On

The action_loop waits some time between interrogating controllers for their states. The wait time by default is 0.01 [s] and is configurable with the AcqLoop_SleepTime property (unit: milliseconds) of the Pool Tango Device.
The action_loop reads new data every certain number of state readout iterations. This number is by default 10 and is configurable with the AcqLoop_StatesPerValue property of the PoolTangoDevice. 

**SoftwareSynchronizedAcquisition** acts on the ExpChannels synchronized by the software synchronizer. This action is launched on the active event comming from the software synchronizer, and lasts until all the ExpChannel terminates their acquisitions.
This action assigns index to the acquired data (returned by the ReadOne). The index originates from the events generated by the software synchronizer. 

Prior to the action execution load parameters to the involved controllers:

- synchronization
- timer
- monitor
- acquisition_mode

Its **start_action** method executes the following:

- load the involved timer/monitors with integration time/mnitor counts and repetitions
    - for each controller implied in the acquistion call PreLoadAll
    - for the timer/monitor axis implied in the acquisition call PreLoadOne and LoadOne
    - for each controller implied in the acquisition call LoadAll
- start the involved axes
    - for each controller implied in the acquisition call PreStartAll
    - for each axis implied in the acquisition call PreStartOne and StartOne
    - for each controller implied in the acquisition call StartAll
- for each ExpChannel implied in the acquisition set state to Moving

Its **action_loop** method executes the following:

- while there is at least one axis in Moving state:
    - for each controller implied in the acquisition call PreStateAll
    - for each axis implied in the acquisition call PreStateOne
    - for each controller implied in the acquisition call StateAll
    - for each axis implied in the acquisition call StateOne
    - wait some time
- read data 
    - for each controller implied in the acquisition call PreReadAll
    - for each axis implied in the acquisition call PreReadOne
    - for each controller implied in the acquisition call ReadAll
    - for each axis implied in the acquisition call ReadOne
- for each ExpChannel implied in the acquisition set state to On

The action_loop waits some time between interrogating controllers for their states. The wait time by default is 0.01 [s] and is configurable with the AcqLoop_SleepTime property (unit: milliseconds) of the Pool Tango Device.
The action_loop reads new data every certain number of state readout iterations. This number is by default 10 and is configurable with the AcqLoop_StatesPerValue property of the PoolTangoDevice.

**0DAcquisition** was not changed in this SEP, it is slave to the SoftwareSynchronizedAcquisition.

**IMPORTANT:** SEP6 sacrify intermediate events with the CTExpChannel count updates. It could be readded in the future. 

Data merging
-----------------------------------------------
Every value acquired or read during the continuous scan execution is stamped with an absolute time and the acquisition index. The experimental channels synchronized by hardware (gate or trigger) provide the core part of each scan record.
The software synchronized channels does not guarantee to provide data for each scan record. The RecordList class, part of the GSF, applies the [zero order hold](http://en.wikipedia.org/wiki/Zero-order_hold) ("constant interpolation") method to fill the missing part of the records. Different interpolation methods could be available to the user end executed as a post-scan processing, however implementation of them is out of scope of this SEP.

Data transfer
-------------

The data collected by the MG needs to be transferred back to to the GSF for proper organization of scan records, using indexes by the RecordList, and storage by the Data Handler and its servants - recorders. Data are passed with the Tango change events of the Data attribute of the Experimental Channels. 

Motion
------

This SEP will deal only with the linear motion. Any combination of Sardana motors and pseudomotors could be used as a scan moveable. The following attributes: acceleration time, velocity and deceleration time are configured, so all the motors reach and leave the constant velocity region at the same time. 

**pre-start position** - is calculated for each motor separately: 
- start position - (velocity * acceleration time) / 2 (scanning in positive direction)
- start position + (velocity * acceleration time) / 2 (scanning in negative direction)

**acceleration time** - is common to all the motors and is determine by the slower accelerating motor involved in the scan.

**velocity** - is calculated for each motor separately from the following parameters: the scan range = abs(end position - start position) and the scan time. The scan time is equal to number of intervals * (integration time + latency time).

**deceleration time** - is common to all the motors and is determine by the slower decelerating motor involved in the scan. 

**post-end position** - is calculated for each motor separately: 
- end position + (velocity * integration time) + (velocity * deceleration time) / 2 (scanning in positive direction)
- end position - (velocity * integration time) - (velocity * deceleration time) / 2 (scanning in negative direction

Some scans require execution of multiple sub-scans e.g. mesh. In this case a sequence of sub-scans will be executed in a loop, substituting the "Move to end position" action with a "Move to pre-start position" (of the next sub-scan). 
 
![motion diagram](res/sep6_motion.bmp)

More about the motion control could be found in [1](http://accelconf.web.cern.ch/AccelConf/ICALEPCS2013/papers/wecoaab03.pdf).

Out of scope of SEP6
=================

* support software Gate synchronization
* support of different trigger types: pre-, mid- or post-triggers
* ascanct does not support
    * pseudocounters 
    * 0D ExpChannel
    * 1D ExpChannel
    * 2D ExpChannel
    * external channels (Tango attributes)
* merge ascanc and ascanct into one macro
* make the overshoot correction optional
* make interpolated data easily distinguishable from the real data

References
=========
1. [WECOAAB03, "Synchronization of Motion and Detectors and Continuous Scans as the Standard Data Acquisition Technique", D.F.C. Fernández-Carreiras et al.](http://accelconf.web.cern.ch/AccelConf/ICALEPCS2013/papers/wecoaab03.pdf)

Changes
=======

- 2016-11-30 [mrosanes](https://github.com/sagiss) Migrate SEP6 from SF wiki to independent markdown language file.
- 2017-01-01 [reszelaz](https://github.com/reszelaz) Remove last pending TODOs and fix the scope in order to open for final discussions.
- 2017-04-03 [reszelaz](https://github.com/reszelaz) Accept SEP6 after positive votes from DESY, MAXIV, SOLARIS and ALBA.
- 2017-05-25 [reszelaz](https://github.com/reszelaz) Correction: reflect 0D non-support in ascanct (Out of scope of SEP6 section).




