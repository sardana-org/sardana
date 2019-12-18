	Title: Improve integration of 1D and 2D experimental channels
	SEP: 2
	State: ACCEPTED
	Date: 2018-12-03
	Drivers: Zbigniew Reszela zreszela@cells.es
	URL: http://www.sardana-controls.org/sep/?SEP2.md
	License: http://www.jclark.com/xml/copying.txt
	Abstract:
	1D and 2D experimental channels may produce big arrays of data at high
	frame rate. Reading this data and storing it using sardana recorders, 
	as it is currently implemented, is not always optimal. This SEP will add
	a data saving duality, optionally, leaving the data storage at the
	responsibility of the detector (or an intermediate software layer e.g. 
	Lima). In this case the sardana kernel will be just notified about
	the reference to the data.
	Furthermore, the experimental channel data may require to be 
	pre-processed/reduced either externally or internally by Sardana. 
	Typical operations are ROI and binning. This SEP will not implement them.


# Description of current situation

It is possible to execute the following measurements: single count, 
step scans or continuous scans with 1D and 2D experimental channels 
(continuous scans work only with 1D).

In the measurement group one can add either a 1D/2D experimental channel 
or its ``Datasource`` attribute and both these work in a single count or a 
step scan. In continuous scan the ``Datasource`` attribute does not work. 

Data source is by default composed by Sardana, but could be returned by
the controller with the ``GetAxisPar`` method.

In a single count, or in a step scan, the data is transferred via the ``Value`` 
attribute readout and the data source is transferred via the ``Datasource`` 
attribute readout at the end of the acquisition.

In a continuous scan 1D experimental channel data is transferred via the `Data` 
(to be renamed to `ValueBuffer`) attribute change events after prior
serialization with JSON.

The following example shows how a single count or a step scan work:

```
Door> defmeas mntgrp-1d2d ct01 oned01 twod01 oned01/datasource twod01/datasource
Door> senv ActiveMntGrp mntgrp-1d2d
Door> ct
Door> ascan mot01 0 1 1 0.1
```


## H5 recorder (`NXscanH5_FileRecorder`)

1D and 2D data from a step scan are correctly stored in the file.
You can check it with the following code:

```
import h5py
h5py.File("<path-to-file>").items()[-1][1]["measurement"]["twod01"][0]`
```

Data source is not stored in the file. You can check it with the following
code:

```
import h5py
h5py.File("<path-to-file>").items()[-1][1]["measurement"].keys()
```

## Spec recorder:

1D data are stored in the file. Scan header is annotated with: `#@MCA`,
`#@CHANN`, `#@MCA_NB`, `#@DET`; and the 1D data starting with `@A` are
preceding the records.

2D data are not stored in the file.

Data source is stored in the file. This is not compatible
with the [Spec format](https://certif.com/spec_manual/user_1_4_1.html)
which says:

> Following the scan header is the scan data. These are just lines of
space-separated numbers that correspond to the column headers given with #L.


## Output recorder:

1D and 2D data are displayed as their shapes.

Data source is not displayed, just `<string>` placeholder is displayed.

# Terminology

* **referencing capability** (a.k.a. external saving) - applies to a controller or a
channel. The controller (plugin) announces the referencing capability if it
implements the necessary API for reporting the acquisition results in form
of the references to the data.
For the moment, all channels proceeding from a controller with referencing capability
automatically *inherits* the referencing capability.
* **value reference** - reference to the acquired data in the URI format.
It is prefered to use the term **value references** instead of the
**data source** because in sardana we use the *value* term for the acquisition result.

# Scope

1. Allow data saving duality (internal vs. external) for 1D/2D controller axes.
* **internal** - sardana reads the values and saves them.
* **external** - hardware (or an intermediate software layer e.g. Lima) saves
the values and sardana reads the value references and uses them to refer to the
data.
Here, it is important to stress the difference between the data reading and data
saving. Channel values may be read for eventual pre-processing by pseudo counters
but these values do not need to be saved as experimental channel values by
sardana. Instead, for example, only the pseudo counter values may be saved by
sardana. 
2. Add referencing configuration API to channels and controllers (plugins) with
referencing capability. Channels and controllers without referencing capability
will not expose this API.
3. Add referencing configuration API to the measurement group.
5. Implement storing value references in the HDF5 file recorder.
If the value reference is a dataset in another HDF5 file this means
creating a Virtual Data Set (VDS). Otherwise this means just having a reference in the
string format.

# Out of scope

1. Storing value references in the Spec file recorder. This will be driven
as a separate PR.
2. Referencing configuration widgets (both at the channel level and at the 
measurement group level). This will be driven as a separate PR.
3. Internal/external data pre-processing and its configuration e.g. pseudo 
counters for ROI, binning, etc. This will be driven as a separate PR/SEP.
4. Consolidation of data in the HDF5 file.
5. Handling references pointing to multiple values e.g. multiple detector frames
stored in the same HDF5 file.
6. Overwrite policy configuration.

# General idea

This SEP is divided in two main parts and could be described as two opposite 
flows of information.
* First, downstream (from the plugin up the recorder), transfer of value 
references instead of values.
* Second, upstream (from the user to the plugin), configuration of value 
referencing e.g. where to save the image files on disk.

While going through the specification details it is convenient to follow
schemes of the information flows for each of these two parts. The first part
is showed on slide 46 and the second on slide 47 of the
[Sardana: new features and developments](https://indico.helmholtz-berlin.de/getFile.py/access?contribId=31&sessionId=1&resId=0&materialId=slides&confId=11)
presentation during the ABCDA Workshop at BESSY.
 
# Specification

## Changes in the current implementation

1. Rename `Datasource` (Tango) and `data_source` (core) attributes to
`ValueRef` (Tango) and `value_ref` (core).
2. Make `data_source` parameter deprecated in the `GetAxisPar`.
3. Rename `Data` (Tango) attribute (marked as experimental API) to `ValueBuffer`
4. Change `ValueBuffer` format from
`{"index": seq<int>, "data": seq<str>}` to `{"index": seq<int>, "value": seq<str>}`

## When to read the value and when to read the value reference?

* When to read the value (currently using the `[Pre]Read{One,All}` methods
of the `Readable` interface)? When any of these conditions applies:
    * the channel does not have referencing capability
    * the channel has referencing capability but it is disabled
    * there is a pseudo counter based on this channel
* When to read the value reference?
    * the channel has referencing capability and it is enabled

## Controller (plugin) API for reading value reference

* Controller which would like to read the value reference must inherit from the
`Referable` interface.
* This controller must implement the `RefOne` method which receives as
argument the axis number and returns either a single value reference (if software
trigger/gate synchronization is in use) or a sequence of value references.
In the future, if necessary, other methods could be added `[Pre]Ref{One|All}`
to allow multi axes queries.

## Channel API for reading value reference

* `ValueRefBuffer` (Tango) and `value_ref_buffer` attributes are used for
passing value reference sequences (chunks). The Tango attribute is of the
`DevEncoded` type and its data structures are of the
following format: `{"index": seq<int>, "value_ref": seq<str>}`.

## Single count (MeasurementGroup Taurus extension) read

* If channel does not read the value but reads the value reference the `count` 
method return the value reference instead of the value for this channel. When 
channel reads the value then it returns value for this channel as it is now.
The fact of returning the value reference is considered as experimental API.
In the future it may change to also return the value if we achieve to extract
 it from the URI.


## How to determine if channel/controller has referencing capability

* Referencing capability is based on inheriting from the `Referable` interface.
Inheriting from this interface is optional. 
    
Now all channels provided by the controller with the referencing capability
will inherit this capability as well. In the future we could allow specifying
it per channel (e.g. timer channel (scalar) could not have this capability).

## Controller API for referencing configuration

This API is based on axis parameters - only set (in the future we could
evaluate having the get part as well).
* `SetAxisPar(axis, parameter, value)`
    
Parameters: `value_ref_pattern` (str), `value_ref_enabled` (bool). See
"Channel API for referencing configuration" for more details about the format.
    
## Channel API for referencing configuration

A channel with referencing capability exports the following additional interface:

* `ValueRefPattern` (Tango) and `value_ref_pattern` (core) attributes
of the string type (use Python str.format() convention
e.g. `file:///tmp/sample1_{index:02d}`)
* `ValueRefEnabled` (Tango) and `value_ref_enabled` (core) attributes of the boolean
type.

## Measurement Group API for referencing configuration

Measurement Group configuration has the following configuration parameters per
channel `saving` (value (internal) or value_ref (external)) and `value_ref_pattern`.
The last one has the same format as explained in "Channel API for saving 
configuration".


Links to more details and discussions
-------------------------------------

The discussions about the SEP2 itself:
* [SEP2 PR](https://github.com/sardana-org/sardana/pull/775)
* [ROI pseudocounters from 2Dcounter issue](https://github.com/sardana-org/sardana/issues/982)
* [scanID and pointNb in controller issue](https://github.com/sardana-org/sardana/issues/979)


Changes
-------

2019-06-17
[reszelaz](https://github.com/reszelaz) Accept after positive votes from:
DESY, MaxIV, Solaris and Alba. 

2019-05-14
[reszelaz](https://github.com/reszelaz) Remove "Scan framework API for 
referencing configuration" from the scope.

2019-01-21
[reszelaz](https://github.com/reszelaz) Rename terms e.g. value source to value reference,
saving capability to referencing capability, etc.

2018-12-03
[reszelaz](https://github.com/reszelaz) Change driver and rewrite SEP2

2016-11-30
[mrosanes](https://github.com/sagiss) Migrate SEP2 from SF wiki to independent
markdown language file and correct formatting.
