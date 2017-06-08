    Title: Ongoing acquisition formalization and implementation
    SEP: 17
    State: DRAFT
    Date: 2017-06-08
    Drivers: Zbigniew Reszela <zreszela@cells.es>
    URL: http://www.sardana-controls.org/sep/?SEP17.md
    License: http://www.jclark.com/xml/copying.txt
    Abstract:
     This SEP aims to formalize the ongoing acqiuisition of experimental
     channels and implements the missing aspects of this feature.

# Motivation

It is very common that the data acquisition hardware, apart of the capability
to execute a controlled and synchronized acquisition, is able to perform an
ongoing acquisition e.g. continuous sampling of an ADC, a live video of a CCD
camera, etc. Having two different control applications to deal with this two
use cases (synchronized and ongoing acquisition) introduces an extra complexity
to the end user in terms of learning the application, memorizing different
channel's identifier and configuring the channel.

Since the SEP6 has formalized the synchronized acquisition this SEP formalizes
the ongoing acquisition.

# Current situation

All experimental channels have the `Value` and the `ValueBuffer` (on the Tango
layer currently called `Data`) attributes. The `ValueBuffer` attribute provides
a way of buffering values for their eventual use in the pseudo counters
calculations and their later transfer (after a prior trigger index assignment)
in a synchronized acquisition.

The rest of this section refers to the `Value` attribute.

## CT

The software synchronized acquisition, performs the intermediate hardware readouts of the
channels while acquiring and one more hardware readout when the acquisition has
already finished. The intermediate readouts were temporary removed from the
implementation with the SEP6 and we should reintroduce them ASAP.

If the `Value` attribute is read while the acquisition is in progress,
it returns the last updated by the acquisition action value (cache). In case
of the software synchronized acquisition this means an intermediate value
corresponding to the current acquisition index and in case of the hardware
synchronized acquisition the value corresponding to the most recently
reported acquisition index. 

When there is no acquisition in progress the `Value` attribute read executes
the hardware readout and returns an updated value.

## 0D

Apart of the `Value` attribute it also has the `CurrentValue` attribute.
The `Value` attribute provides the result of the accumulation operation
executed on the accumulation buffer.

Everytime the `Value` attribute is read, the operation is performed on
what is in the buffer at that moment. So the same calculations are unneceserily
repeated if the `Value` attribute is read multiple times after the acquisition.
The accumulation buffer is filled gradually by the acquisition action with
the hardware readout results, which by the same time fills the cache of the
`CurrentValue` attribute.

If the `CurrentValue` attribute is read while the acquisition is in progress,
it returns the last updated by the acquisition action value (cache).

When there is no acquisition in progress the `CurrentValue` read executes
the hardware readout and returns an updated value.

## 1D and 2D

The software acquisition action performs the hardware readout of the channels
only once at the end of the acquisition.

If the `Value` attribute is read while the acquisition is in progress,
it returns the last updated by the acquisition action value (cache). Since no
intermediate hardware readouts are done during the software synchronized
acquisition this means a value that corresponds to the previous acquisition.
In case of the hardware synchronized acquisitions this means a value that
corresponds to the most recently reported acquisition index.

When there is no acquisition in progress the `Value` attribute read executes
the hardware readout and returns an updated value.

## PseudoCounter

If the `Value` attribute is read while any of the underneath physical channels
is acquiring, it returns the result of the calculation based on the cache of
the physical `Value` attributes. If any of the physical `Value` attributes
cache is empty (this situation occurs during the first acquisition right after
the Sardana startup) then all the physical `Value` attributes are updated with
the fresh readout from the hardware prior to the calculation.

When none of the physical channels is acquiring, then the `Value` attribute
read executes the hardware readout of all the physical `Value` attributes and
returns the result of the calculation based on these updated values.

## General

### Ignoring cache

The `Force_HW_Read` Tango property set to `True` ignores the cache value and
always reads from the hardware. For the PseudoCounters this implies the
hardware readout of all the underneath physical channels prior to the
calculation.

### Events

The `Value` attributes of CT, 0D, 1D and 2D emits change events when the
absolute change criteria is met. Since the CT and 0D are being updated during
the acquisition, an intermediate events may also occur. The PseudoCounter
`Value` attribute does not emit events.

### MeasurementGroup count

The MeasurementGroup count (single synchronized acquisition), implemented on
the Taurus extension level, is commonly used in macros e.g. `ct`, `ascan`, etc.
The count obtains the acquisition results by the `Value` attributes read.
This application collides with the read of the ongoing acquisition and causes
the following problems:

- Since the count read is performed when there is no acquisition in progress,
the hardware readout is repeated unnecesarily - one readout was already done
at the end of the acquisition. 
- The controller (plugin) does not know if it should return the value
corresponing to the acquisition that has just finished, or the result of the
ongoing acquisition.
- The `Value` read is executed per channel, meaning that we can not profit
from the hardware access optimization possible with the `(Pre)Read{One,All}`
sequence.
- The presence of the PseudoCounters in the MeaseurementGroup provokes
subsequent repetitions of the hardware readouts of the underneath physical
channels.

## Summary

All the preceding explanation can be summarized in this table:

Aspect | CT | 0D | 1D, 2D | PseudoCounter
------ | -- | -- | ------ | -------------
Intermediate readouts while acquiring | Yes | Yes | No | -
Events | Yes | Yes | Yes | No
`Force_HW_Read` property | Yes | Yes | Yes | Yes
`CurrentValue` attribute | No | Yes | No | No

# Specification

## Option 1 - Value and CurrentValue attributes

The `Value` attribute has two roles: it keeps the result of the most recent
acquisition and provides the intermediate result updates, via events, during
the acquisition (CT and 0Ds only).

Its read can return:
- `None` - after the Sardana startup
- An intermediate result (cache filled by the acquisition) - if the acquisition
is in progress
- A result of the last acquisition - all the other cases
 
The `CurrentValue` attribute provides the ongoing measurement results of a channel.
It is not possible to read it when the channel is acquiring.
This is because it could interfere with the hardware readouts performed by
the acquisition action - all the readouts are executed via the same API -
`(Pre)Read{One,All}` sequence.
 
Managing the concurrent access to the hardware during the readouts becomes
a critical aspect now.

This will require applying the following rules:
- The `CurrentValue` attribute read will acquire the `ActionContext` - lock the
element. So starting the acquisition while the `CurrentValue` read takes place
will have to wait until the `ActionContext` gets released.
- The whole acquisition action, including setting of the `synchronization`
type and any other configuration, the state readouts and the value readouts,
will be enclosed by the `ActionContext`. This will prevent interleaving of the
unrelated readouts.
- The intention of the `CurrentValue` attribute read while the acquisition is
in progress will raise an exception, otherwise, these request could be required
to wait long - until the acquisition ends.

In summary, the acquisition action start is "patient" - it waits until the
`CurrentValue` read returns, and the `CurrentValue` read is "impatient" -
it gives up if the acquisition is in progress.
 
It won't be possible to take a profit of the read sequence optimizations
in case of the multiple axes readouts, because the channels will be read
separately (either Taurus or Tango polling). But in the future, we could think
of adding to the Pool a common action that will poll the elements with a given
frequency. This way the user will be allowed to add or remove the elements to
these polling action. But this is definitely out of the scope of this SEP.

### To be decided
- Should we clear the `Value` attribute cache at the beginning of the
acquisition. So that if someone reads the attribute before the acquisition has
finished, or before an intermediate readout, it does not return the previous
acquisition final result?
- Which attribute names are better: `Value` and `CurrentValue` or
`LastValue` and `Value`?
- We could allow the 0D `CurrentValue` attribute read while the acquisition is
in progress
- We could allow the `CurrentValue` attribute read of the other channels while
the acquisition is in progress, but does it have sense?
Is there any hardware that supports it?

 
### Pros

- The behavior of `Value` and `CurrentValue` attributes will be almost the same
for all the experimental channels.
- It will be possible to retrieve the acquisition result after the acquisition
via a synchronous readout of the attribute. This is especially useful for the
pure Tango clients and ease development of the Taurus widgets.
- The hardware readout is done only once and its result is stored in the
`Value` attribute for further consultation.
- The hardware readout can be optimized with the `(Pre)Read{One,All}`
sequence.
- 0D already has the `CurrentValue` attribute
 
### Implementation:

- `CurrentValue(SardanaAttribute)` attribute is added to the `PoolBaseChannel`.
- `CurrentValue` is extended with the `update` method. This method will use... 
- `get_current_value` method is added to the `PoolBaseChannel` class.
- Prevent `CurrentValue` attribute readouts while acquiring. Do it on both,
core and Tango levels. On the core level using the `OperationContext` - if set,
raise an exception. On the Tango level using the state machine.
- The `update` method of the `Value` attributes is removed - the `Value`
attributes can be updated only by the acquisition actions.
- `Value` attributes of physical channels and pseudo counters are not connected
by events anymore.
- `PoolBaseChannel.get_value` kwarg `cache` disappears - this method always
returns what is in the attribute at the moment.
- PsuedoCounters gets locked by the `OperationContext` while acquiring.
- PseudoCounters that are not based on any of the physical channels are read by
the acquisition action (the read moment changes - now at the beginning of the
acquisition)
- Enclose the whole acquisition action in the `ActionContext`: load
configuration e.g. `synchronization`, etc.
- Add new type of synchronization: `Autonomous` (or `Independent`)
- Reset controller's synchronization to `Autonomous` in the acquisition action
finish hook.

## Option 2 - Only Value attribute.

The `Value` attribute mixes both roles. It provides the software synchronized
acquisition intermediate and final results and the hardware synchronized
acqusition most recent acquisition index results via events. The ongoing
acquisition results are available via read.

### Cons
 
- The `Value` attribute on a trend may mix the unrelated values. This may be
confusing to the user.
- In order to obtain the acquisition result it is necessary to listen to the
`ValueBuffer` events.
- Since the `Value` attribute emits events, the graphical widgets will need to
make an extra poll of the attribute to show the ongoing acquisition results
(similarly to PMTV and taurustrend of Motor `Position` attribute)

### Implementation

- Refactor MeasurementGroup `count` method to listen to the `ValueBuffer`
events and not read the `Value` attribute.
- It is necessary to implement the most of the Option 1 points, apart of the
ones about the `CurrentValue` attribute...
 
## Option 3 - Ongoing acquisition is not supported

The `Value` attribute read can return:
- `None` - after the Sardana startup
- An intermediate result (cache filled by the acquisition) - if the acquisition
is in progress (CT and 0Ds only)
- A result of the last acquisition - all the other cases

The `Value` attribute read will never execute the hardware readout

### Implementation

- The `Force_HW_Read` property can be eliminated.
- `PoolBaseChannel.get_value` kwarg `cache` disappears - this method always
returns what is in the attribute at the moment.

0D will maintain the `CurrentValue` attribute as it is now. 

# Changes

- 2017-06-08 [reszelaz](https://github.com/reszelaz) Draft version.




