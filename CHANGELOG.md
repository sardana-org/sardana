# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).
This file follows the formats and conventions from [keepachangelog.com]


## [2.4.0] 2018-03-14

### Added
- General hooks - hooks that can be configured with `defgh`, `udefgh` and `lsgh`
  macros instead of attaching them programatically (#200, #646)
- New API to `Stoppable` interface of pool controllers that allows synchronized
  multiaxes stop/abort (#157, #592)
- Macro execution logs can be saved to a file. Controlled with `logmacro` macro and
  `LogMacroDir`, `LogMacroFormat` environment variables (#102, #480)
- `addctrlib`, `relctrllib`, `relctrlcls` macros usefull when developing
  controller classes (#541)
- `meshct` macro - mesh composed from row scans executed in the continuous
  way (#659)
- Optional sending of logs to Logstash (www.elastic.co) configurable with
  `LogstashHost` and `LogstashPort` Tango properties of Pool and MacroServer
  (#699).
- Relative continuous scans like `dscanct`, `d2scanct`, etc. (#605, #688)
- Expose acquisition data in `ct` and `uct` macros via data macro property
  (#471, #682, #684)
- Notification to the user in case of a failed operation of stopping in spock
  (#592)
- Timeout/watchdog in continuous scans - especially usefull when
  triggers may be missed e.g. not precise positioning (#136, #601)
- Reintroduce intermediate events for counter/timer channels while
  software acquisition is in progress (#625)
- TaurusCounterTimerController - that can connect to different data
  sources e.g. EPICS by using Taurus schemes (#628)
- Allow deleting multiple measurement groups and multiple controllers
  with udefmeas and udefctrl macros respectivelly (#361, #547)
- Improve exception hangling in ascanct & co. (#600)
- Allow to hide Taurus 4 related deprecation warnings
  (`TAURUS_MAX_DEPRECATION_COUNTS` sardana custom setting) (#550)
- Optional data extrapolation for the very first records in ascanct & co.
  (`ApplyExtrapolation` environment variable) (#588)
- Inform about an error when reading the sofware synchronized channel so
  the record can be completed - value for the given trigger will not
  arrive anymore (#581, #582)
- `--file` option to sequencer - it allows to load a sequence file
  directly on the application startup moment (#283, #551)
- Report error line number when loading a sequence from a txt file
  fails (#114, #552)
- Present available pools at the macroserver creation moment in the
  alphabetical order (#585, #586)
- Present available doors at the spock profile creation moment in the
  alphabetical order (#221, #558, #673)
- `DiffractometerType` is stored in crystal file in HKL controller (#679)
- Some backwards compatibility for element names in PQDN - recently
  Taurus started using only FQDN (#625, #627)
- Improve DumbRecorder (example of a custom file recorder) to write to
  a file.
- Data in scan Records can now be accessed via dict-like syntax (#644)
- Example of a macro that uses other macros as hooks #649

### Fixed
- Spock waits until macro stopping is finished after Ctrl+C (#34. #596)
- Limits of the underneeth motors are checked if we move a pseudo motor
  (#36, #663, #704)
- Limits of the underneeth motors are checked if we move a motor group
  (#259, #560)
- Eliminate a possibility of deadlock when aborting a macro (#693, #695,
  #708)
- Acquisition start sequence which in case of starting disabled channels
  could unintentionally change the measurement group's configuration (#607,
  #615)
- Selection of the master timer/monitor for each of the acquisition
  sub-actions (hardware and software) (#614)
- Avoid "already involved in motion" errors due to wrong handling of
  operation context and Tango state machine (#639)
- Protect software synchronizer from errors in reading motor's position
  (#694, #700)
- Make the information about the element's instrument fully dynamic and
  remove it from the serialized information (#122, #619)
- uct macro (#319, #627)
- Avoid measurement group start failures when to the disabled controller
  is offline (#677, #681)
- Allow to stop macro when it was previously paused (#348, #548)
- Bug in theoretical motor position in ascanct & co. (#591)
- Counter/timer TaurusValue widget when used with Taurus 4 - correctly show
  the element's name (#617)
- `relmaclib` reports the error message in case the macro has parameters
  definition is incorrect (#377, #642)
- Icons in macroexecution widgets when used with Taurus 4 (#578)
- Spurious errors when reading RecordData attribute, normally triggered
  on event subscription e.g. macrogui (#447, #598)
- Possible too early acquisition triggering by trigger/gate due to the
  wrong order ot starting trigger/gate and software synchronizer in the
  synchronization action (#597)
- Validation of motor positions agains their limits in ascanct & co. (#595)
- Generation of theoretical timestamps in ascanct & co. (#602)
- Maintain macrobutton's text when MacroServer is shut down (#293, #559)
- Number of repetitions (always pass 1) passed to experimental channel
  controllers in case software synchronization is in use (#594)
- `Hookable.hooks` proprty setting - now it cleans the previous
  configuration (#655)
- `getData` of scan macros from the GSF (#683, #687)
- Make PoolUtil thread-safe (#662, #655)
- Dummy counter/timer now returns partial value when its acquisition was
  aborted (#626)
- Workaround for #427: make default values for repeat parameters of `wa`,
  `pwa` and all list macros fully functional - also support execution with
  `Macro.execMacro` (#654)
- `getIntervalEstimation` method of the GSF for some scanning modes (#661)
- Improved MacroServer creation wizard (#676)

### Changed
- FQDN are now used internally by sardana in its identifiers (#668, partially)
- Make explicit file descriptor buffer synchronization (force effective write to
  the file system) in SPEC and FIO recorders (#651)
- Rename edctrl to edctrlcls macro (#541)
- The way how the master timer/monitor for the acquisition actions is selected.
  Previously the first one for the given synchronization was used, now it is
  taken into account if it is enabled or disabled (next ones may be used then).
  (#647, #648)
- Macrobutton's text to from "<macro_name>" to "Run/Abort <macro_name>"
  (#322, #554, #658)
- Color policy in spock for IPython >= 5 from Linux to Neutral (#706 and #712)

### Removed
- `ElementList` attribute from the Door Tango device - `Element` attribute is
  available on the MacroServer device (#556, #557, #653)
- `raw_stop_all`, `raw_stop_one`, `_raw_stop_all`, `_raw_stop_one`, `stop_all`,
  `stop_one`, `raw_abort_all`, `raw_abort_one`, `_raw_abort_all`, `_raw_abort_one`,
  `abort_all`, `abort_one` methods of the `PoolController` class (#592)


## [2.3.2] - 2017-08-11
For a full log of commits between versions run (in your git repo):
`git log 2.3.1..2.3.2`

### Fixed
- Provides metadatab in setup.py to be complient with PyPI

## [2.3.1] - 2017-08-11
For a full log of commits between versions run (in your git repo):
`git log 2.3.0..2.3.1`

### Fixed
- Appveyor build for Python 2.7 64 bits

## [2.3.0] - 2017-08-11
For a full log of commits between versions run (in your git repo):
`git log 2.2.3..2.3.0`

### Added
- Generic continuous scans - `ascanct` & co. (SEP6)
  - TriggerGate element and its controller to plug in hardware with
    the synchronization capabilities
  - Software synchronizer that emulate hardware TriggerGate elements
  - Possibility to execute multiple, synchronized by hardware or software, 
    in time or position domain (also non equidistant) acquisitions with the
    Measurement Group
  - CTExpChannel can report acquired and indexed values in chunks in
    continuous acquisition
  - `synchronizer` parameter to the Measurement Group configuration
  - `latency_time` parameter to the experimental channel controllers
  - `ApplyInterpolation` environment variable, applicable to `ascanct` & co.
  - "How to write a counter/timer controller" documentation
  - "How to write a trigger/gate controller" documentation
- 0DExpChannel may report acquired and indexed values in chunks in
  continuous acquisition (#469)
- PseudoCounter may return calculated (from the buffered physical
  channels values) and indexed values in chunks in continuous acquisition
  (#469)
- `timescan` macro to run equidistant time scans and `TScan` class to
  develop custom time scans (#104, #485)
- New recorder for NXscan that does not use the nxs module (NAPI) but h5py
  instead (#460)
- New spock syntax based on the square brackets to use repeat parameters
  without limitations (#405)
- Possibility to specify the IORegister value attribute data type between
  `int`, `float` or `bool` even in the same controller (#459, #458)
- Possibility to duplicate repeats of the repeat parameters in macroexecutor
  and sequencer (#426)
- Tooltip with parameters description in the macro execution widgets:
  MacroExecutor and Sequencer (#302)
- Generic main to the macrobutton widget that allows to execute "any" macro
- Overview of Pool elements documentation.
- API fo Pool elements documentation.
- Flake8 check-on-push for CI (#451)
- Continuous integration service for Windows platform - AppVeyor (#383, #497)

### Changed
- `ascanct` & co. macro parameters to more resemble parameters of step scans
  (SEP6)
- `trigger_type` was renamed to `synchronization` in Measurement Group
  configuration and as the experimental channel controller parameter (SEP6)
- make the new NXscanH5_FileRecorder the default one for .h5 files (#460) 
- A part of the 0D's core API was changed in order to be more consistent with
  the new concept of value buffer (#469):
  - `BaseAccumulation.append_value` -> `BaseAccumulation.append`
  - `Value.get_value_buffer` -> `Value.get_accumulation_buffer`
  - `Value.append_value` -> `Value.append_buffer`
  - `PoolZeoDExpChannel.get_value_buffer` -> `PoolZeoDExpChannel.get_accumulation_buffer`
  - `PoolZeoDExpChannel.value_buffer` -> `PoolZeoDExpChannel.accumulation_buffer`
- `nr_of_points` attribute of `aNscan` class was renamed to `nr_points` (#469)
- IORegister value attribute default data type from `int` to `float` and as a
  consequence its Tango attribute data type from `DevLong` to `DevDouble` and
  the `write_ioreg` and `read_ioreg` macro parameter and result type respectively
  (#459, #458)
- Use of ordereddict module. Now it is used from the standard library (Python >= 2.7)
  instead of `taurus.external`. For Python 2.6 users this means a new dependency
  `ordereddict` from PyPI (#482)
- Applied AutoPEP8 to whole project (#446)

### Deprecated
- `LoadOne` API had changed - `repetitions` was added as a mandatory argument
  and the old API is deprecated (SEP6)
- OD's `ValueBuffer` Tango attribute is deprecated in favor of the
  `AccumulationBuffer` attribute (#469)

### Removed
- intermediate events being emitted by the CTExpChannel Value attribute while
  acquiring with the count updates - temporarily removed (SEP6)
- units level from the Measurement Group configuration (#218)

### Fixed
- Spurious errors when hangling macros stop/abort e.g. dscan returning to initial
  position, restoring velocitues after continuous scan, etc. due to the lack of
  synchronization between stopping/aborting macro reserved objects and execution of
  on_stop/on_abort methods (#8, #503)
- Hangs and segmentation faults during the MacroServer shutdown process (#273, #494,
  #505. #510)
- macrobutton widget working with the string parameters containing white spaces
  (#423)
- Restoring macros from the list of favorites in the macroexecutor (#441, #495)
- Macro execution widgets connecting to the MacroServer in a Tango database
  different than the default one e.g. using `--tango-host` option
- Logging of the macro result composed from more than one item in Spock (#366, #496)
- MacroServer start and instance creation when using it as standalone server
  i.e. without any Pool (#493)
- One of the custom recorder examples - DumbRecorder (#511)


## [2.2.3] - 2017-01-12
For a full log of commits between versions run (in your git repo):
`git log 2.2.2..2.2.3`

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
[Unreleased]: https://github.com/sardana-org/sardana/compare/2.3.2...HEAD
[2.4.0]: https://github.com/sardana-org/sardana/compare/2.3.2...2.4.0
[2.3.2]: https://github.com/sardana-org/sardana/compare/2.3.1...2.3.2
[2.3.1]: https://github.com/sardana-org/sardana/compare/2.3.0...2.3.1
[2.3.0]: https://github.com/sardana-org/sardana/compare/2.2.3...2.3.0
[2.2.3]: https://github.com/sardana-org/sardana/compare/2.2.2...2.2.3
[2.2.2]: https://github.com/sardana-org/sardana/compare/2.2.1...2.2.2
[2.2.1]: https://github.com/sardana-org/sardana/compare/2.2.0...2.2.1
[2.2.0]: https://github.com/sardana-org/sardana/compare/2.1.1...2.2.0
[2.1.1]: https://github.com/sardana-org/sardana/compare/2.1.0...2.1.1
[2.1.0]: https://github.com/sardana-org/sardana/compare/2.0.0...2.1.0
[2.0.0]: https://github.com/sardana-org/sardana/compare/1.6.1...2.0.0
[1.6.1]: https://github.com/sardana-org/sardana/compare/1.6.0...1.6.1
[1.6.0]: https://github.com/sardana-org/sardana/releases/tag/1.6.0
