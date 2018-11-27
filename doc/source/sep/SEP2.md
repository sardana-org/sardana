	Title: Improve integration of 1D and 2D experimental channels
	SEP: 2
	State: DRAFT
	Date: 2018-11-26
	Drivers: Zbigniew Reszelaz zreszela@cells.es
	URL: http://www.sardana-controls.org/sep/?SEP2.md
	License: http://www.jclark.com/xml/copying.txt
	Abstract:
	1D and 2D experimental channels may produce big arrays of data at high
	frame rate. Extracting this data and storing it using Sardana recorders, 
	as it is currently implemented, is not always optimal. This SEP will add
	a data saving duality, optionally, leaving the data storage at the
	responsibility of the detector (or an intermediate software layer e.g. 
	Lima). In this case Sardana will be just notified about the URI of the 
	data which could be used for eventual reference.
	Furthermore, the experimental channel data may require to be 
	reduced/pre-processes either externally or internally by Sardana. 
	Typical operations are ROI and binning. This SEP will not implement them.


# Description of current situation

It is possible to execute the following measurements: single count, 
step scans or continuous scans with 1D and 2D experimental channels 
(continuous scans work only with 1D).

In the measurement group one can add either a 1D/2D experimental channel 
or its ``Datasource`` attribute and both these work in a single count or a 
step scan. In the continuous scan the ``Datasource`` attribute do not work
directly. 

Data source is by default composed by Sardana, but could be returned by
the controller with the ``GetPar`` method.

In a single count or in a step scan data is transferred via ``Value`` 
attribute readout and the Data source is transferred via ``Datasource`` 
attribute readout at the end of the acquisition.

In a continuous scan 1D experimental channel data is transferred via `Data` 
(`ValueBuffer`) attribute change events after prior serialization with JSON.

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

1D is stored in the file. Scan header is annotated with: `#@MCA`, `#@CHANN`,
`#@MCA_NB`, `#@DET`; and the 1D data starting with `@A` are preceding the 
records.

2D is not stored in the file.

Data source is correctly stored in the file. This is not compatible
with the [Spec format](https://certif.com/spec_manual/user_1_4_1.html)
which says:

> Following the scan header is the scan data. These are just lines of
space-separated numbers that correspond to the column headers given with #L.


## Output recorder:

1D and 2D data are displayed as their shapes.

Data source is not displayed, just `<string>` placeholder is displayed.


# Scope

1. Allow data saving duality for 1D/2D controllers axes which may:
  * report only the data
  * report only the URI
  * report both data (for eventual pre-processing by the pseudo counters) and
  URI
2. Implement data referencing with URI in H5 file recorder.
3. Add (optional) interface for 1D/2D experimental channels for 
saving configuration. Which would translate into the 1D/2D controllers 
saving configuration interface.
4. Add persistent saving configuration on the experiment configuration / 
measurement group level.

# Out of scope

1. Data referencing with URI in Spec file recorder - will be handled as a 
separate PR *a posteriori*.
2. Saving configuration widgets (both at the channel level and at the 
experiment configuration / measurement group level) - will be handled as a 
separate PR *a posteriori*.
3. Internal/external data pre-processing and its configuration e.g. pseudo 
counters for ROI, binning, etc. - will be handled as a separate PR/SEP *a 
posteriori*.


Links to more details and discussions
-------------------------------------

The discussions about the SEP2 itself:
* [SEP2 PR](https://github.com/sardana-org/sardana/pull/775)
* [ROI pseudocounters from 2Dcounter issue](https://github.com/sardana-org/sardana/issues/982)
* [scanID and pointNb in controller issue](https://github.com/sardana-org/sardana/issues/979)


Changes
-------

2018-11-27
[reszelaz](https://github.com/reszelaz) Change driver and rewrite SEP2
2016-11-30
[mrosanes](https://github.com/sagiss) Migrate SEP2 from SF wiki to independent markdown language file and correct formatting.
 



