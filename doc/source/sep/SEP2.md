	Title: Improve integration of 1D and 2D experimental channels
	SEP: 2
	State: DRAFT
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
	Lima). In this case Sardana will be just notified about the data source
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

In a single count or in a step scan data is transferred via ``Value`` 
attribute readout and the data source is transferred via ``Datasource`` 
attribute readout at the end of the acquisition.

In a continuous scan 1D experimental channel data is transferred via `Data` 
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

1D and 2D data from a step scan are correctly stored in the file:

```
import h5py
h5py.File("<path-to-file>").items()[-1][1]["measurement"]["twod01"][0]`
```

Data source is not stored in the file:

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

* **saving capability** (external saving) - Applies to a controller or a
channel. The controller (plugin) announces the external saving capability if it
implements the necessary API for handling saving e.g. value source readout or
saving configuration.
For the moment, all channels proceeding from a controller with saving capability
automatically announce saving capability.
* **value source** - source in form of the URI to the value of a single
acquisition. It is prefered to use the term **value source** instead of the
**data source** because sardana refers to the acquisition result with the term
value.

# Scope

1. Allow data saving duality (internal vs. external) for 1D/2D controller axes.
* **internal** - sardana reads the values and saves them.
* **external** - hardware (or an intermediate software layer e.g. Lima) saves
the values and sardana reads the value sources and uses them to refer to the
data.
Here, it is important to stress the difference between the data reading and data
saving. Channel values may be read for eventual pre-processing by pseudo counters
but these values do not need to be saved as experimental channel values by
sardana. Instead, for example, only the pseudo counter values may be saved by
sardana.
TODO: decide whether both, internal and external saving, can be used at the same
time.
2. Add saving configuration API to channels and controllers (plugins) with
saving capability. Channels and controllers without saving capability will not
expose this API.
3. Add saving configuration API to the measurement group.
4. Add saving configuration API to the scan framework.
5. Implement referencing to value sources in the HDF5 file recorder.

# Out of scope

1. Referencing to value sources in Spec file recorder - will be driven
as a separate PR.
2. Saving configuration widgets (both at the channel level and at the 
measurement group level) - will be driven as a separate PR.
3. Internal/external data pre-processing and its configuration e.g. pseudo 
counters for ROI, binning, etc. - will be driven as a separate PR/SEP.

# Specification

## Changes in the current implementation

1. Rename `Datasource` (Tango) and `data_source` (core) attributes to
`ValueSource` (Tango) and `value_source` (core).
TODO: vote for the best names. Alternative names (for simplicity):
`Source` (Tango) and `source` (core).
2. Make `data_source` parameter deprecated in the `GetAxisPar`.
3. Rename `Data` (Tango) attribute (marked as experimental API) to `ValueBuffer`
4. Change `ValueBuffer` format from
`{"index": seq<int>, "data": seq<str>}` to `{"index": seq<int>, "value": seq<str>}`

## When to read the value and when to read the value source?

* When to read the value (currently using the `[Pre]Read{One,All}` methods
of the `Readable` interface)? When any of these conditions applies:
    * the channel does not have saving capability
    * the channel has saving capability but it is disabled
    * internal saving is enabled for the channel
    * there is a pseudo counter based on this channel
* When to read the value source?
    * the channel have saving capability and it is enabled

## Controller (plugin) API for reading value source

* Controller which would like to read the value source must inherit from the
`Sourceable` interface.
TODO: vote for the best name. Alternative name is `Savable`.
* This controller must implement the `SourceOne` method which receives as
argument the axis number and returns either a single value source (if software
trigger/gate synchronization is in use) or a sequence of value sources.
In the future, if necessary, other methods could be added `[Pre]Source{One|All}`
to allow multi axis queries.

## Channel API for reading value source

* `ValueSourceBuffer` (Tango) and `value_source_buffer` attributes are used for
passing value source sequences (chunks). The Tango attribute is of the
`DevString` type and will work with the JSON serialized data structures of the
following format: `{"index": seq<int>, "value_source": seq<str>}`.
TODO: vote for the best name. Alternative names: `SourceBuffer` (Tango)
and `source_buffer` (core) for attributes, and the following data structure:
`{"index": seq<int>, "source": seq<str>}`.

## Single count (Taurus extension) read

* If channel has saving enabled then the `count` method returns value source,
otherwise it returns value.

## How to determine if channel/controller has saving capability

* Saving capability is based on inheriting from the `Sourceable` interface.
Inheriting from this interface is optional. 
    
Now all channels provided by the controller will have saving capability. In the
future we could allow specifying it per channel (e.g. timer channel (scalar)
could not have this capability).

## Controller API for saving configuration

This API is based on axis parameters
* `GetAxisPar(axis, parameter)`
* `SetAxisPar(axis, parameter, value)`
    
Parameters: `value_source_template` (str), `overwrite_policy` (enum),
`saving_enabled` (bool). See "Channel API for saving configuration" for more
details about the format.
    
## Channel API for saving configuration

A channel with saving capability exports the following additional interface:

* `ValueSourceTemplate` (Tango) and `value_source_template` (core) attributes 
of the string type (use Python str.format() convention
e.g. `file:/tmp/sample1_{index:02d}`)
* `OverwritePolicy` (Tango) and `overwrite_policy` (core) attributes of the
enumeration type (abort, overwrite, append)
* `SavingEnabled` (Tango) and `saving_enabled` (core) attributes of the boolean
type.

## Measurement Group API for saving configuration

Measurement Group configuration has the following configuration parameters per
channel `saving` (internal and/or external), `value_source_template` and
`overwrite_policy`. The last two have the same format as explained in "Channel
API for saving configuration".

## Scan framework API for saving configuration

The `ScanValueSourceTemplate` environment variable is used to alternate the
Measurement Group's configuration (value_source_template) during the scan
(backup/restore). It uses Python str.format() convention
e.g. `file:/tmp/sample1_{index:02d}`
or `file:/{scan_dir}/{scan_file}/{channel}/sample1_{index:02d}`.


Links to more details and discussions
-------------------------------------

The discussions about the SEP2 itself:
* [SEP2 PR](https://github.com/sardana-org/sardana/pull/775)
* [ROI pseudocounters from 2Dcounter issue](https://github.com/sardana-org/sardana/issues/982)
* [scanID and pointNb in controller issue](https://github.com/sardana-org/sardana/issues/979)


Changes
-------

2018-12-03
[reszelaz](https://github.com/reszelaz) Change driver and rewrite SEP2

2016-11-30
[mrosanes](https://github.com/sagiss) Migrate SEP2 from SF wiki to independent
markdown language file and correct formatting.
