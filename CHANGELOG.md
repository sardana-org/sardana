# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).
This file follows the formats and conventions from [keepachangelog.com]


## [Unreleased]

### Added
- New recorder for NXscan that does not use the nxs module (NAPI) but h5py
  instead (#460)
- New spock syntax based on the square brackets to use repeat parameters
  without limitations (#405)
- Possibility to duplicate repeats of the repeat parameters in macroexecutor
  and sequencer (#426)
- Tooltip with parameters description in the macro execution widgets:
  MacroExecutor and Sequencer (#302)
- Generic main to the macrobutton widget that allows to execute "any" macro
- TriggerGate element and its controller to plug in hardware with
  the synchronization capabilities (SEP6)
- software synchronizer that emulate hardware TriggerGate elements (SEP6)
- possibility to execute multiple, synchronized by hardware or software, 
  in time or position domain (also non equidistant) acquisitions with the
  Measurement Group (SEP6)
- CTExpChannel may report acquired and indexed values in chunks in
  continuous acquisition (SEP6)
- 0DExpChannel may report acquired and indexed values in chunks in
  continuous acquisition (#469)
- PseudoCounter may return calculated (from the buffered physical
  channels values) and indexed values in chunks in continuous acquisition
  (#469) 
- `timescan` macro to run equidistant time scans and `TScan` class to
  develop custom time scans (#104, #485)
- `synchronizer` parameter to the Measurement Group configuration (SEP6)
- `latency_time` parameter to the experimental channel controllers (SEP6)
- `ApplyInterpolation` environment variable, applicable to `ascanct` & co.
  (SEP6)
- "How to write a counter/timer controller" documentation (SEP6)
- "How to write a trigger/gate controller" documentation (SEP6)
- Flake8 check-on-push for CI (#451)
- Continuous integration service for Windows platform - AppVeyor (#383, #497)
- Possibility to specify the IORegister value attribute data type between
  `int`, `float` or `bool` even in the same controller (#459, #458)

### Changed
- make the new NXscanH5_FileRecorder the default one for .h5 files (#460) 
- `ascanct` & co. macro parameters to more resemble parameters of step scans
  (SEP6)
- `trigger_type` was renamed to `synchronization` in Measurement Group
  configuration and as the experimental channel controller parameter (SEP6)
- Applied AutoPEP8 to whole project (#446)
- A part of the 0D's core API was changed in order to be more consistent with
  the new concept of value buffer (#469):
  - `BaseAccumulation.append_value` -> `BaseAccumulation.append`
  - `Value.get_value_buffer` -> `Value.get_accumulation_buffer`
  - `Value.append_value` -> `Value.append_buffer`
  - `PoolZeoDExpChannel.get_value_buffer` -> `PoolZeoDExpChannel.get_accumulation_buffer`
  - `PoolZeoDExpChannel.value_buffer` -> `PoolZeoDExpChannel.accumulation_buffer`
- `nr_of_points` attribute of `aNscan` calss was renamed to `nr_points`
- IORegister value attribute default data type from `int` to `float` and as a
  consequence its Tango attribute data type from `DevLong` to `DevDouble` and
  the `write_ioreg` and `read_ioreg` macro parameter and result type respectively
  (#459, #458)
- Use of ordereddict module. Now it is used from the standard library (Python >= 2.7)
  instead of `taurus.external`. For Python 2.6 users this means a new dependency
  `ordereddict` from PyPI (#482)

### Deprecated
- `LoadOne` API had changed - `repetitions` was added as a mandatory argument
  and the old API is deprecated (SEP6)
- OD's `ValueBuffer` Tango attribute is deprecated in favor of the
  `AccumulationBuffer` attribute (#469)

### Removed
- units level from the Measurement Group configuration (#218)
- intermediate events being emitted by the CTExpChannel Value attribute while
  acquiring with the count updates (SEP6)

### Fixed
- Macro execution widgets connecting to the MacroServer in a Tango database
  different than the default one e.g. using `--tango-host` option
- macrobutton widget working with the string parameters containing white spaces
  (#423)
- Restoring macros from the list of favorites in the macroexecutor (#441, #495)
- Logging of the macro result composed from more than one item in Spock (#366, #496)


## [2.2.3] - 2017-01-12
For a full log of commits between versions run (in your git repo):
`git log 2.2.3..2.2.3`

### Fixed
- Avoid to run sardana.tango.pool tests in sardana_unitsuite (related to #402)

## [2.2.2] - 2017-01-10
For a full log of commits between versions run (in your git repo):
`git log 2.2.1..2.2.2`

### Fixed
- saving of PreScanSnapshot environment variable from expconf widget (#411)
- travis-ci build failures due to configuration file not adapted to setuptools

## [2.2.1] - 2016-12-30
For a full log of commits between versions run (in your git repo):
`git log 2.2.0..2.2.1`

### Fixed
- Build of documentation on RTD

## [2.2.0] - 2016-12-22
For a full log of commits between versions run (in your git repo):
`git log 2.1.1..2.2.0`

### Added
- Possibility to store data of 1D channels in SPEC files (#360)
- Pseudo counters documentation (overview and "how to" controllers) (#436)
- sardanatestsuite script to run sardana tests (#368)
- bumpversion support
- This CHANGELOG.md file

### Changed
- setup.py implementation from distutils to setuptools (#368)
- waitFinish (used to execute async operations) is not reservedOperation (#362)

### Deprecated
- sardana.spock.release module

### Removed
- sardanaeditor widget support to taurus < 4 & spyder < 3 (sardanaeditor
will become functional from taurus release corresponding to milestone Jan17)
(#354)

### Fixed
- Disable/enable experimental channels in measurement group (#367)
- Pseudo counters based on 0D channels (#370)
- AccumulationType attribute of 0D channels (#385)
- Display (now case sensitive) of measurement groups names in expconf widget
(SF #498)
- spock prompt in IPython > 5 (#371)
- renameelem macro (#316)
- Tango device server scripts on Windows (#350)
- Use of DirectoryMap environment variable with list of values
- Other bugs: #271, #338, #341, #345, #351, #353, #357, #358, #359, #364, #386


## [2.1.1] - 2016-09-27
For a full log of commits between versions run (in your git repo):
`git log 2.1.0..2.1.1`

### Fixed
SF issues: #426, #507, #508, #509, #511


## [2.1.0] - 2016-09-13
For a full log of commits between versions run (in your git repo):
`git log 2.0.0..2.1.0`
Main improvements since sardana 2.0.0 (aka Jan16) are:

### Added
- Compatibility layer in order to support Taurus v3 and v4.
- itango dependency to make Sardana compatible with PyTango 9.2.0. 
Sardana CLI client (spock) has been adapted. (SF #487)
- Optional block output of the scan records in spock. The new records
can be printed on top of the previous ones. (SF #492)

### Changed
- Re-introduce a possibility to decode repeat parameters for macros that use
only one repeat parameter, located at the end of the definition, from a flat
list parameters. (SF #491)
- Improve the sequencer behaviour. (SF #483, #485)
- Documentation. (SF #489, #490, #491)

### Fixed
- Sporadic "already involved in operation" errors in the scans when using
0D experimental channels. (SF #104)
- Bugs (SF #499, #493, #492, #488, #485, #484, #483, #482, #478,
 #418, #405, #104)


## [2.0.0] - 2016-04-28
For a full log of commits between versions run (in your git repo):
`git log 1.6.1..2.0.0`
Main improvements since sardana 1.6.1 (aka Jul15) are:

### Added
- HKL support (SEP4)
- Support to external recorders (SF #380, #409, #417);
  Sardana recorder classes and related utilities have been relocated.
- Macro tw has been added in the standard macros (SF #437)
- Possibility to rename pool elements (SF #430)

### Changed
- Improve support of repeat macro parameters (SF #3, #466);
  multiple and/or nested and/or arbitrarily placed repeat parameters are
  allowed now.
- Door Device status reports information about the macro being run 
  (SF #120, #427)
- Door is now in ON state after user abort (SF #427)
- Correct PoolPath precedence to respect the order (SF #6)

### Fixed
- Bugs (SF #223, #359, #377, #378, #379, #381, #382, #387, #388, #390,
  #394, #403, #406, #411, #415, #424, #425, #431, #447, #449, #451, #453, #454,
  #461)

### Removed
- Templates to fix issue with rtd theme (#447)


## [1.6.1] - 2015-07-28
For a full log of commits between versions run (in your git repo):
`git log 1.6.0..1.6.1` 

### Changed
- Update man pages
- bumpversion


## [1.6.0] - 2015-07-27
Release of Sardana 1.6.0 (the Jul15 milestone)
Main improvements since sardana 1.5.0 (aka Jan15):

### Added
- macros dmesh and dmeshc (#283)
- Document DriftCorrection feature
- Sardana documentation is now available in RTD (SF #5, #358)
- Option to display controller and axis number, in the output from wm/wa 
  (SF #239)

### Changed
- Allow Sardana execution on Windows (SF #228)
- Improve speed of wa macro(SF #287)
- Allow undefine many elements at the same time, using udefelem (SF #127)
- Allow reading of motor position when the motor is out of SW limits (SF #238)

### Fixed
- meshc scan
- Bug in ascanc when using a pseudomotor (SF #353)
- Bugs related to loading macros/modules (SF #121 ,#256)
- Bug with PoolMotorTV showing AttributeError (SF #368 ,#369, #371)
- Bugs and features related with test framework (SF #249, #328, #357)
- Bugs (SF #65, #340, #341, #344, #345, #347, #349)



[keepachangelog.com]: http://keepachangelog.com
[Unreleased]: https://github.com/sardana-org/sardana/compare/2.2.3...HEAD
[2.2.3]: https://github.com/sardana-org/sardana/compare/2.2.2...2.2.3
[2.2.2]: https://github.com/sardana-org/sardana/compare/2.2.1...2.2.2
[2.2.1]: https://github.com/sardana-org/sardana/compare/2.2.0...2.2.1
[2.2.0]: https://github.com/sardana-org/sardana/compare/2.1.1...2.2.0
[2.1.1]: https://github.com/sardana-org/sardana/compare/2.1.0...2.1.1
[2.1.0]: https://github.com/sardana-org/sardana/compare/2.0.0...2.1.0
[2.0.0]: https://github.com/sardana-org/sardana/compare/1.6.1...2.0.0
[1.6.1]: https://github.com/sardana-org/sardana/compare/1.6.0...1.6.1
[1.6.0]: https://github.com/sardana-org/sardana/releases/tag/1.6.0
