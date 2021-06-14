# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).
This file follows the formats and conventions from [keepachangelog.com]

## [Unreleased]

### Added

* `rscan`, `r2scan` and `r3scan` scan macros (formerly available as examples
   under different names `regscan`, `reg2scan` and `reg3scan`)
   * added _hooks_ and _scan data_ support to these macros
   * changed `region_nr_intervals` macro parameter type to integer
   * moved `integ_time` macro parameter at the end of the parameters list
* `lsp` macro: list Pools the MacroServer is connected to (#1599)
* Possibility to _release_ hung operations e.g. motion or acquisition due to a hung element (#1582)
   * _release_ element and _release_ action concepts to the core
   * `Release` Tango command to Pool element devices
   * `release()` method to the Taurus extensions
   * macro release will automatically release the element hung on aborting (3rd Ctrl+C)


### Removed

* `regscan`, `reg2scan` and `reg3scan` scan macro examples

### Fixed

* Make MeasurementGroup state readout evaluate states of the involved elements (#1316, #1591)
* Prevent start of operation e.g. motion or acquisition already on the client side when the
  state is not On or Alarm (#1592, #1594)
* Stop/abort element in `ct` macro when used with channels (#1595)
* Use `AttributeEventWait.waitForEvent()` instead of deprecated `AttributeEventWait.waitEvent()` (#1593)
* Do not reserve _instruments_ in scans what avoids stopping them (#1577)
* Make PMTV relative move combobox accept only positive numbers (#1571, #1572)
* Remove usage of taurus deprecated features (#1552)
* Update MeasurementGroup's Elements property when Configuration attr is written (#1610)

## [3.1.1] 2021-06-11

### Fixed

* Allow to stop/abort macro executing other hooked macros (#1603, #1608)

### Deprecated

* `MacroExecutor.clearRunningMacro()` in favor of `MacroExecutor.clearMacroStack()` (#1608)

## [3.1.0] 2021-05-17

### Added

* _H5 write session_ to avoid file locking problems and to introduce SWMR mode support (#1124, #1457)
  * `h5_start_session`, `h5_start_session_path`, `h5_end_session`, `h5_end_session_path`
    and `h5_ls_session` macros
  * `h5_write_session` context manager
* `shape` controller axis parameter (plugin), `shape` experimental channel
  attribute (kernel) and `Shape` Tango attribute to the experimental channels
  (#1296, #1466)
* *scan information* and *scan point* forms to the *showscan online* widget (#1386, #1477, #1479)
* `ScanPlotWidget`, `ScanPlotWindow`, `ScanInfoForm`, `ScanPointForm` and `ScanWindow`
  widget classes for easier composition of custom GUIs involving online scan plotting (#1386)
* Handle `pre-move` and `post-move` hooks by: `mv`, `mvr`, `umv`, `umvr`, `br`, `ubr` (#1471, #1480)
  * `motors` attribute to these macros which contains list of motors that will be moved
  * `sardanacustomettings.PRE_POST_MOVE_HOOK_IN_MV` for disabling these hooks
* Include trigger/gate elements in the per-measurement preparation (#1432, #1443, #1468)
  * Add `PrepareOne()` to TriggerGate controller.
  * Call TriggerGate controller preparation methods in the _acquision action_
* Add `ScanUser` environment variable (#1355)
* Support `PosFormat` _ViewOption_ in `umv` macro (#176, #1555)
* Allow to programmatically disable *deterministic scan* optimization (#1426, #1427)
* Initial delay in position domain to the synchronization description
  in *ct* like continuous scans (#1428)
* Avoid double printing of user units in PMTV: read widget and units widget (#1424)
* Allowed hooks to macro description in Spock (#1523)
* Assert motor sign is -1 or 1 (#1345, #1507)
* _last macro_ concept to the `MacroExecutor` (kernel) #1559
* Documentation on how to write 1D and 2D controllers (#1494)
* Mechanism to call `SardanaDevice.sardana_init_hook()` before entering in the server event loop (#674, #1545)
* Missing documentation of SEP18 concepts to how-to counter/timer controller (#995, #1492)
* Document how to properly deal with exceptions in macros in order to not interfer 
  with macro stopping/aborting (#1461)
* Documentation on how to start Tango servers on fixed IP - ORBendPoint (#1470)
* Documentation example on how to more efficiently access Tango with PyTango
  in macros/controllers (#1456)
* "What's new?" section to docs (#1584)
* More clear installation instructions (#727, #1580)
* napoleon extension to the sphinx configuration (#1533)
* LICENSE file to python source distribution (#1490)

### Changed

* Experimental channel shape is now considered as a result of the configuration
  and not part of the measurement group configuration (#1296, #1466)
* Use `LatestDeviceImpl` (currently `Device_5Impl`) for as a base class of the Sardana Tango
  devices (#1214, #1301, #1531)
* Read experimental channel's `value` in serial mode to avoid involvement of a worker thread (#1512)
* Bump taurus requirement to >= 4.7.1.1 on Windows (#1583)

### Removed

* `shape` from the measurement group configuration and `expconf` (#1296, #1466)

### Fixed

* Subscribing to Pool's Elements attribute at Sardana server startup (#674, #1545)
* Execute per measurement preparation in `mesh` scan macro (#1437)
* Continously read value references in hardware synchronized acquisition 
  instead of reading only at the end (#1442, #1448)
* Ensure order of moveables is preserved in Motion object (#1505)
* Avoid problems when defining different, e.g. shape, standard attributes,
  e.g. pseudo counter's value, in controllers (#1440, #1446)
* Storing string values in PreScanSnapshot in NXscanH5_FileRecorder (#1486)
* Storing string values as custom data in NXscanH5_FileRecorder (#1485)
* Stopping/aborting grouped movement when backlash correction would be applied (#1421, #1474, #1539)
* Storing string datasets with `h5py` > 3 (#1510)
* Fill parent_macro in case of executing XML hooks e.g. in sequencer (#1497)
* Remove redundant print of positions at the end of umv (#1526)
* Problems with macro id's when `sequencer` executes from _plain text_ files (#1215, #1216)
* `sequencer` loading of plain text sequences in spock syntax with macro functions (#1422)
* MacroServer crash at exit on Windows by avoiding the abort of the already finished macro (#1077, #1559)
* Allow running Spock without Qt bindings (#1462, #1463)
* Spock issues at startup on Windows (#536)
* Fix getting macroserver from remote door in Sardana-Taurus Door extension (#1506)
* MacroServer opening empty environment files used with dumb backend (#1425, #1514, #1517, #1520)
* Respect timer/monitor passed in measurement group configuration (#1516, #1521)
* Setting `Hookable.hooks` to empty list (#1522)
* `Macro.hasResult()` and `Macro.hasParams()` what avoids adding empty _Parameters_ and _Result_
  sections in the macro description in Spock (#1524)
* Apply position formatting (configured with `PosFormat` _view option_)
  to the limits in the `wm` macro (#1529, #1530)
* Prompt in QtSpock when used with new versions of the `traitlets` package (#1566)
* Use equality instead of identity checks for numbers and strings (#1491)
* Docstring of QtSpockWidget (#1484)
* Recorders tests helpers (#1439)
* Disable flake8 job in travis CI (#1455)
* `createMacro()` and `prepareMacro()` docstring (#1460, #1444)
* Make write of MeasurementGroup (Taurus extension) integration time more robust (#1473)
* String formatting when rising exceptions in pseudomotors (#1469)
* h5storage tests so they pass on Windows and mark the `test_VDS` as xfail (#1562, #1563).
* Recorder test on Windows - use `os.pathsep` as recorder paths separator (#1556)
* Measurement group tango tests - wrong full name composition (#1557)
* Avoid crashes of certain combinations of tests on Windows at process exit (#1558)
* Skip execution of Pool's `DeleteElement` Tango command in tests for Windows in order to
  avoid server crashes (#540, #1567)
* Skip QtSpock `test_get_value` test if qtconsole >= 4.4.0 (#1564)
* Increase timeout for QtSpock tests (#1568)

## [3.0.3] 2020-09-18

### Added

* Support to Python >= 3.5 (#1089, #1173, #1201, #1313, #1336)
* Showscan online based on pyqtgraph (#1285)
  * multiple plots in the same MultiPlot widget (as opposed to different panels before)
  * option to group curves by x-axis or individual plot per curve
  * new showscan console script
  * support fast scans: update curves at a fix rate (5Hz)
  * better curve colors and symbols
* Measurement group (Taurus extension) configuration API with methods to
  set/get: enabled, output, plot type, plot axes, timer, monitor, synchronizer,
  value ref enabled, value ref pattern parameters(#867, #1415, #1416)
* Experiment configuration (expconf) macros
  * Measurement group configuration macros: `set_meas_conf` and `get_meas_conf` (#690)
  * Active measurement group selection macros: `set_meas` and `get_meas` (#690)
  * Pre-scan snapshot macros: `lssnap`, `defsnap` and `udefsnap` (#1199)
* Automatic scan statistics calculation with the `scanstats` macro as the `post-scan`
  hook stored in the `ScanStats` environment variable (#880, #1402)
* `pic`, `cen` to move the scanned motor to the peak and center of FWHM values
  respectively (#890)
* `where` macro to print the scanned motor position (#890)
* `plotselect` macro for configuring channels for online scan plotting (#824)
* `genv` macro for printing environment variable values (#888)
* QtSpock widget (`QtSpock` and `QtSpockWidget`) - *experimental* (#1109)
* Dump info on channels if MG acq fails in step scan, ct and uct (#1308)
* Add timestamp to element's dumped information (#1308)
* Quality to `SardanaAttribute` (#1353)
* Instruments creation and configuration in sar_demo (#1198)
* Allow _experimental channel acquisition_ with PoolChannelTaurusValue (PCTV) widget (#1203)
* Documentation to Taurus Extensions of Sardana Devices: MacroServer part
  and the whole Sardana part of the Qt Taurus Extensions (#1228, #1233)
* Advertise newfile macro in case no ScanDir or ScanFile is set (#1254, #1258)
* Improve scans to detect if a ScanFile od ScanDir are set but empty (#1262)
* Possibility to view debug messages in `DoorOutput` widget - enable/disable
  using context menu option (#1242)
* Improve user experience with PMTV:
  * Store PMTV (motor widget) configurations: *expert view* and *write mode*
    (relative or absolute) permanently as TaurusGUI settings (#1286)
  * Do not create encoder widget in PMTV if the motod does not have encoder
    in order to avoid errors comming from the polling (#209, #1288)
  * Change limit switches indicators from buttons to labels (#210, #1290)
* Improve documentation (#1241)
* Better macro exception message and hint to use `www` (#1191)
* Stress tests (on the Taurus level) for measurements (#1353)
* Add basic information to "how to write custom recorder" to
  the documentation (#1275)
* Register a TaurusValue factory for pool widgets (#1333)
* Direct links to Sardana-Taurus model API (#1335)
* Use GitHub workflows to upload to PyPI (#1253, #1166, #1408, #1189)

### Fixed

* Improve macro aborting in Spock (2nd, 3rd and eventual 4th Ctrl+C now act
  on the macro). Also print additional information on what is happening while
  stopping and aborting (#1256, #978, #34) 
* Use `tango.EnsureOmnitThread` to protect Sardana threads
  (Tango is not thread safe) (#1298)
* Avoid using Tango `AttributeProxy` in limits protection to not be affected
  by bug tango-controls/pytango#315 (#1302)
* Avoid deadlock in Sardana-Taurus models e.g. `MeasurementGroup.count()` or
  `Motor.move()` (#1348)
  * Remove redundant protection in PoolElement.start() and waitFinish()
* Fast repetitions of single acquisition measurements (counts) on MeasurementGroup (#1353)
* Pre-mature returning to ON state of MeasurementGroup at the end of measurement (#1353) 
* Default macro parameter values in macroexecutor (#1153)
* Executing RunMacro Door's command with string parameters containing spaces (#1240)
* `macroxecutor` and `sequencer` now react on added/removed macros #295
* Avoid printing `None` in `wm` and `wa` macros for `DialPosition` attribute and print
  the `Position` attribute twice for pseudo motors (#929, #953, #1411, #1412)
* Setting of environment variables in Python 3.7 (#1195)
* Use `taurus.external.qt.compat.PY_OBJECT` in singal signatures instead of `object`
  to avoid problems when using `builtins` from `future` (#1082)
* Remove Taurus deprecated code what reduces deprecation warnings (#1206, #1252)
* Macro functions which define results now really report the result (#1238)
* Use of env and hints in `macro` function decorator (#1239)
* Fix several issues with PMTV:
  * Reset pending operations of absolute movement on switching to relative movement (#1293)
  * PMTV widget not updating the following attributes: limit switches, state
    and status (#1244)
* Avoid Taurus GUI slowness on startup and changing of perspectives due to too
  large macroexecutor history by limitting it to 100 -
  configurable with `MACROEXECUTOR_MAX_HISTORY` (#1307)
* OutputBlock view option when macros produce outputs at high rate (#1245)
* `showscan online` shows only the online trend and not erroneously online and offline
  (#1260, #1400)
* Fix fast operations (motion & acq) by propertly clearing operation context and
  resetting of acq ctrls dicts (#1300)
* Premature end of acquisition on Windows (#1397)
* `timescan` with referable channels (#1399, #1401)
* Use proper python3 executable regardeless of installation (#1398)
* Environment variables validation before macro execution when these are defined
  on door's or macro's level (#1390)
* Use more efficient way to get terminal size for better printing spock output (#1245, #1268)
* Measurement groups renaming with `renameelem` macro(#951)
* `macroexecutor` correctly loads macro combo box if it was started with server down and 
  server started afterwards (#599, #1278)
* `TaurusMacroExecutorWidget` does not use _parent model_ feature (#599, #1278)
* `TaurusSequencerWidget` does not use _parent model_ feature (#1284)
* Macro plotting in new versions of ipython and matplotlib require extra call to
  `pyplot.draw()` to make sure that the plot is refreshed (#1280)
* Controller's `StateOne()` that returns only state (#621, #1342)
* Fix problems with non-timerable channels in expconf (#1409)
* Allow MacroButton widget to be smaller - minimum size to show the macro name (#1265)
* Remove TangoAttribute controllers from Sardana (#181, #1279)
* Remove deprecation warning revealed when running test suite (#1267)
* Remove event filtering in `DynamicPlotManager` (showscan online) (#1299)
* Avoid unnecessary creations of DeviceProxies in `ascanct` (#1281)
* Macro modules with annotated functions are properly interpreted by the MacroServer
  (#1366, #1367)
* Adapt to new taurus behavior of `cmd_line_parser` kwarg of `TaurusApplication` (#1306)
* Fix dummy C/T and 2D controller classes in the case the start sequence was interrupted
  (#1188, #1309)
* Fix dummy motor velocity so it respects steps_per_unit (#1310)
* Make handling of `Macro.sendRecordData()` with arbitrary data more robust in Spock
  (#1320, #1319)
* Use `utf8_json` as default codec (in Tango) if `Macro.sendRecordData()` does not specify one
  (#1320, #1319)
* Avoid repeating of positions when `regscan`, `reg2scan` and `reg3scan` pass through start
  position(s) (#1326)
* `test_stop_meas_cont_acquisition_3` spurious failures (#1188, #1353) 
* Build docs with Sphinx 3 (#1330) 

### Deprecated

* `DoorDebug` widget - use `DoorOutput` with enabled debugging (#1242)
* Global measurement group timer/monitor on all levels (#867)
* `value_ref_enabled` and `value_ref_pattern` measurement group parameters
  for non-referable channels (#867) 

### Changed

* Avoid extra state readout at the end of acquisition (#1354)
* Renamed _synchronization_ to _synch description_
  * Tango MeasurementGroup `Synchronization` attribute to `SynchDescription`
  * Core MeasurementGroup `synchronization` property to `synch_description`
  * Sardana-Taurus Device MeasurementGroup `getSynchronizationObj()`,
    `getSynchronization()` and `setSynchronization()` methods to
    `getSynchDescriptionObj()`,`getSynchDescription()`
    and `setSynchDescription()` (#1337)
  * `SynchronizationDescription` helper class to `SynchDescription`
* Requirements are no longer checked when importing sardana (#1185)
* Measurement group (Taurus extension) configuration API methods, known in 
  the old sense for setting a global measurement group timer/monitor:
  `getTimer()`, `setTimer()`, `getMonitor()` were moved to `MGConfiguration`
  class and are deprecated (#867)
* `macroexecutor` and `sequencer` discard settings if the models passed
  as command line arguments had changed with respect to the previous execution
  (#1278, #1284)

### Removed

* Support to Python < 3.5 (#1089, #1173, #1201, #1263)
* `sardana.macroserver.macro.ParamRepeat` class (#1315, #1358)
* Backwards compatibility for measurement group start without preparation
  (#1315, #1373)
* Controller API (#1315, #1361):
  * `class_prop`
  * `ctrl_extra_attributes`
  * `inst_name`
  * `SetPar()` and `GerPar()`
  * `SetExtraAttributePar()` and `GetExtraAttributePar()`
  * `ctrl_properties` with "Description" as `str`
* `CounterTimerController` controller API (#1315, #1362, #1403):
  * `_trigger_type`
  * `PreStartAllCT()`, `PreStartOneCT()`, `StartAllCT()` and `StartOneCT()`
* `PseudoMotorController` controller API (#1315, #1363)
  * `calc_all_pseudo()`, `calc_all_physical()`, `calc_pseudo()` and `calc_physical()`
* `PseudoCounterController` controller API (#1315, #1364)
  * `calc()`
* `IORegisterController` controller API (#1315, #1365):
  * `predefined_values`
* `Loadable` backawards compatibility (without `repetitions` and `latency` arguments)
  (#1315, #1370)
* `PoolMotorSlim` widget (#1315, #1380)
* Door's Tango device `Abort` command (#1315, #1376)
* Backwards compatibility in measurement group configuration (#1315, #1372)
  * not complete names (without the scheme and PQDN)
  * `trigger_type`
* `Label` and `Calibration` attributes of `DiscretePseudMotor` controller
  (#1315, #1374)
* MacroButton's methods (#1315, #1379, #1405)
  * `toggleProgress()`
  * `updateMacroArgumentFromSignal()`
  * `connectArgEditors()`
* `Controller`'s (Taurus extension) `getUsedAxis` method (#1315, #1377)
* `sardana.taurus.qt.qtgui.extra_macroexecutor.dooroutput.DoorAttrListener` class
  (#1315, #1378)
* "Show/hide plots" button in `expconf` (#960, #1255, #1257)
* `plotsButton` argument in `ExpDescriptionEditor` constructor (#960, #1255, #1257)
* `showscan online_raw` magic command in spock (#1260)
* `online` kwarg in `SpockBaseDoor` constructor (#1260)
* `sardana.requirements` (#1185)
* `sardanatestsuite` and `sardana.test.testsuite.*` utility functions (#1347)
* Hook places: `hooks` and `pre-start` (#1315, #1359)
* `FileRecorder` macro hint (#1315, #1360)
* `sardana.release` attributes: `version_info` and `revision` (#1315, #1357)
* `sardana.spock.release` module (#1315, #1357)
* Support to IPython < 1 (#1315, #1375)

## [2.8.6] 2020-08-10

### Fixed

* MacroButton with repeat parameters (#1172, #1314)

## [2.8.5] 2020-04-27

### Fixed

* Reintroduce backwards compatibility for measurement groups' configurations
  (URIs) created with Taurus 3 (#1266, #1271)

## [2.8.4] 2019-11-13

### Fixed

* fix compatibility with python 2.6 when overwritting macros 
* fscan macro that was broken 2.6.0 (#1218, #1220)

### Deprecated

* `nr_points` attribute of scan macros e.g., aNscan family of scans, `fscan` etc.
  (#1218, #1220)

## [2.8.3] 2019-09-16

### Fixed

* Removing latencytime from detect_evt (as propossed in #1190)

## [2.8.2] 2019-09-13

### Fixed

* Hangs of MacroServer when PyTango `AttributeProxy` and `DeviceProxy` objects
  were garbage collected (#1080, #1190, #1193)

## [2.8.1] 2019-07-22

### Fixed

* Remove uncompleted optimization when applying measurement group
  configuration (#1171, #1174)

## [2.8.0] 2019-07-01

### Added

* SEP2 - Improve integration of 1D and 2D experimental channels (#775):
  * Possibility to report acquisition results in form of value references (in 
  the URI format) of 1D and 2D experimental channels:
    * `Referable` base class to inherit from when developing a controller 
    plugin
    * `ValueRef` and `ValueRefBuffer` Tango attributes and `value_ref` and 
    `value_ref_buffer` core attributes to propagate value references 
    proceeding from the controllers.
  * Possibility to configure value referencing from the measurement group level
    (_Ref Enabled_ and _Ref Pattern_ columns in expconf and 
    `value_ref_pattern` and `value_ref_enabled` configuration parameters) or
    a single channel level (`ValueRefPattern` and `ValueRefEnabled` Tango 
    attributes) which both reach the controller plugin as axis parameters 
    `value_ref_pattern` and `value_ref_enabled`.
  * Creation of Virtual Data Sets (VDS) for value references of _h5file_ scheme
    in HDF5 file recorder.
  * Possibility to still use pseudo counters based on 1D and 2D experimental
    channels when value referencing is in use.
  * Possibility to include 2D experimental channels in continuous acquisition
    using value reporting (`ValueBuffer` Tango attribute to 2DExpChannel and
    `value_buffer` core attribute)
  * `VALUE_BUFFER_CODEC` and `VALUE_REF_BUFFER_CODEC` to sardanacustomsettings.
* Reintroduce `showscan online` to spock (#1042)
* Full support to *spock syntax* in loading sequences from files (#645, #672)
* Info in `lsmac` output about macros being overridden (#930, #947)
* Allow to configure timeout on pool element's (Taurus extensions) *go* methods e.g.
  `move`, `count`, etc. (#992)
* Emulated hardware triggering between dummy counter/timer and trigger/gate elements
  (#1100)
* Macro example demonstrating how to add an extra scan column with motor
  positions shifted to the middle of the scan interval: `ascanct_midtrigger`
  (#1105)
* Support to 7 axes geometry in `pa` macro (#1116)
* Protection to `showscan` when a non HDF5 file is getting opened (#1073)
* Auto-deploy to PyPI with Travis (#1113)
* Print output of `send2ctrl` macro only if it contains something (#1120)
* Add `DescriptionLength` view option for adjusting the `lsdef` macro description
  (#1107, #1108)
* Add `ShowScanOnline` component to Taurus Qt extensions (#1042)

### Changed

* `Data` Tango attribute of experimental channels (CTExpChannel,
  ZeroDExpChannel, OneDExpChannel, PseudoCounter) to `ValueBuffer` (SEP2, #775)
* Value buffer data structure format from `{"index": seq<int>, "data": seq<str>}`
  to `{"index": seq<int>, "value": seq<str>}` (SEP2, #775)
* Default encoding of `ValueBuffer` and `ValueRefBuffer` attributes (SEP2, #775)
  from JSON to pickle
* Mapping of Integer data type to Tango DevLong64 (#1083)

### Fixed

* Hanging scans by avoiding deepcopy of `DeviceProxy` (#1102)
* Restore motor parameters (vel, acc, dec) before going to start position in dNscact
  macros (#1085)
* Calculation of nb_starts argument of `PrepareOne` method of timerable controllers
  when software synchronization is in use (#1110)
* Interactive macros on Windows (#347)
* expconf when empty (unspecified) DataType (#1076)
* Output block of scan records which do not fit the console width (#924)
* Fix bug on exception popups in macroexecutor (#1079, #1088)
* Cyclic references between scan macros and GSF internals (#816, #1115)
* Enable expconf buttons (Reload and Apply) when local configuration was kept after
  receiving external changes (#959, #1093)
* Avoid external changes pop-up when synchronizer is changed in the expconf by
  removing global measurement group synchronizer (#1103)
* Show external changes pop-up in expconf when last measurement group is deleted
  remotelly (#1099)
* Pop-up message when expconf configuration changed externally (#1094)
* Remove circlular references between the macro object and the FIO recorder (#1121)

### Deprecated

* Datasource Tango attribute, data_source core attributes and data_source
1D and 2D controller axis parameter (SEP2, #775).

### Removed

* `ValueBuffer` Tango attribute of 0D exp. channels deprecated in version
2.3.0. `AccumulationBuffer` attribute serves for the same need (SEP2, #775).
Exceptionally no major version bump is done cause it seems like this attribute
was not used programmatically in third party plugins/GUIs. 

## [2.7.2] 2019-05-28

### Fixed

* Several issues with measurement group configuration and `epxconf` (#1090)

### Deprecated

* Measurement group configuration `timer` and `monitor` - there are no 
equivalents, these roles are assigned based on the channel's order per each 
of the synchronization types: trigger, gate and start (#1090)

## [2.7.1] 2019-03-29

### Fixed

* Do not read 1D and 2D experimental channels during software acquisition loop
  reintroduced after fixing it in 2.6.0 (#1086).

## [2.7.0] 2019-03-11

### Added

* Possibility to directly acquire an experimental channel (without the need to define
  a measurement group) (#185, #997, #1048, #1061)
  * `IntegrationTime` (Tango) and `integration_time` (core) attributes to all experimental
    channels
  * `Timer` (Tango) and `timer` (core) attribute to all timerable experimental channels
  * `default_timer` class attribute to all timerable controllers (plugins) to let them
    announce the default timer axis
* Possibility to pass an experimental channel (now compatible only with timerable channels) 
  as a parameter of `ct` and `uct` macros in order to acquire directly on the channel (#1049)
* `Countable` element type that includes measurement group and experimental channels (#1049)
* `newfile` macro for setting `ScanDir`, `ScanFile` and `ScanID` env variables (#777)
* Warning message when hooks gets overridden with `Hookable.hooks` property (#1041)
* Acquisition macro examples (#1047)

### Fixed

* `expconf` warns only about the following environment variables changes: `ScanFile`,
  `ScanDir`, `ActiveMntGrp`, `PreScanSnapshot` and `DataCompressionRank` (#1040)
* MeasurementGroup's Moveable attribute when set to "None" in Tango is used as None
  in the core (#1001)
* Compatibility of measurement group plotting configurations created with
  sardana < 2.4.0 and taurus < 4.3.0 (#1017, #1022)
* General Hook tests (#1062)
 
## [2.6.1] 2019-02-04

This is a special release for meeting the deadline of debian buster freeze (debian 10).

### Fixed
- String parameter editor in macroexecutor and sequencer (#1030, #1031)
- Documentation on differences between `Hookable.hooks` and `Hookable.appendHook`
  (#962, #1013)

## [2.6.0] 2019-01-31

This is a special release for meeting the deadline of debian buster freeze (debian 10).

### Added
- New acquisition and synchronization concepts (SEP18, #773):
  - Preparation of measurement group for a group of acquisitions is mandatory
    (`Prepare` Tango command and `prepare` core method; `NbStarts` Tango
    attribute and `nb_starts` core attribute; `count`, `count_raw` and
    `count_continuous` methods in Taurus extension)
  - Preparation of timerable controllers is optional (`PrepareOne` method)
  - `SoftwareStart` and `HardwareStart` options in `AcqSynch` enumeration and
    `Start` in `AcqSynchType` enumeration (the second one is available in
    the `expconf` as synchronization option)
  - `start` and `end` events in software synchronizer
  - `PoolAcquisitionSoftwareStart` acquisition action
  - `SoftwareStart` and `HardwareStart` synchronization in
    `DummyCounterTimerController`
- Support to Qt5 for Sardana-Taurus widgets and Sardana-Taurus extensions (#1006,
  #1009)
- Possibility to define macros with optional parameters. These must be the last
  ones in the definition (#285, #876, #943, #941, #955)
- Possibility to pass values of repeat parameters with just one member without
  the need to encapsulate them in square brackets (spock syntax) or list
  (macro API) (#781, #983)
- Possibility to change data format (shape) of of pseudo counter values (#986)
- Check scan range agains motor limits wheneve possible (#46, #963)
- Workaround for API_DeviceTimedOut errors on MeasurementGroup Start. Call Stop
  in case this error occured (#764).
- Optional measurement group parameter to `ct` and `uct` macros (#940, #473)
- Support to "PETRA3 P23 6C" and "PETRA3 P23 4C" diffractometers by means
  of new controller classes and necessary adaptation to macros (#923, #921)
- Top LICENSE file that applies to the whole project (#938)
- Document remote connection to MacroServer Python process (RConsolePort Tango
  property) (#984)
- sardana.taurus.qt.qtgui.macrolistener (moved from taurus.qt.qtgui.taurusgui)
- Documentation on differences between `Hookable.hooks` and `Hookable.appendHook`
  (#962, #1013)

### Fixed
- Do not read 1D and 2D experimental channels during software acquisition loop
  (#967)
- Make `expconf` react on events of environment, measurement groups and their
  configurations. An event offers an option to reload the whole experiment
  configuration or keep the local changes. `expconf` started with
  `--auto-update` option will automatically reload the whole experiment
  configuration (#806, #882, #988, #1028, #1033)
- Reload macro library overriding another library (#927, #946)
- Avoid final padding in timescan when it was stopped by user (#869, #935)
- Moveables limits check in continuous scans when moveables position attribute
  has unit configured and Taurus 4 is used (quantities) (#989, #990)
- Hook places advertised by continuous scans so the `allowHooks` hint and the
  code are coherent (#936)
- Macro/controller module description when module does not have a docstring
  (#945)
- Make `wu` macro respect view options (#1000, #1002)
- Make cleanup (remove configuration) if spock profile creation was interrupted
  or failed (#791, #793)
- Spock considers passing supernumerary parameters as errors (#438, #781)
- MacroServer starts without the Qt library installed (#781, #907, #908)
- Make `Description` an optional part of controller's properties definition (#976)
- Correcting bug in hkl macros introduced when extending macros for new
  diffractometer types: angle order was switched

### Changed
- MacroButton stops macros instead of aborting them (#931, #943)
- Spock syntax and advanced spock syntax are considered as one in documentaion
  (#781)
- Move pre-scan and post-scan hooks out of `scan_loop` method (#920, #922,
  #933)
- Logstash handler from python-logstash to python-logstash-async (#895)
- Move `ParamParser` to `sardana.util.parser` (#781, #907, #908)
- SpockCommandWidget.returnPressed method renamed to onReturnPressed
- SpockCommandWidget.textChanged method renamed to onTextChanged

### Deprecated
- Measurement group start without prior preparation (SEP18, #773)
- Loadable controller's API: `LoadOne(axis, value, repeats)`
  in favor of `LoadOne(axis, value, repeats, latency)` (SEP18, #773)
- Unused class `sardana.taurus.qt.qtgui.extra_macroexecutor.dooroutput.DoorAttrListener`

### Removed
- Support to Qt < 4.7.4 (#1006, #1009)

## [2.5.0] 2018-08-10

### Added
- `def_discr_pos`, `udef_discr_pos` and `prdef_discr` macros for configuring
  discrete pseudo motors (#801)
- `Configuration` attribute to discrete pseudo motor (#801)
- Avoid desynchronization of motion and acquisition in time synchronized
  continuous scans by checking whether the motor controller accepts the scan
  velocity and in case it rounds it up, reduce the scan velocity (#757)
- `repeat` macro for executing n-times a set of macros passed as parameters
  or attached as hooks (#310, #745, #892)
- `pre-acq` and `post-acq` hooks to the `ct` macro (#808)
- `pre-acq` and `post-acq` hooks to the continuous scans: `ascanct` family
  macros (#780)
- `pre-acq` and `post-acq` hooks to `timescan` macro (#885)
- `SoftwareSynhronizerInitialDomain` Tango attribute to
  the Measurement Group Tango device and `sw_synch_initial_domain` attribute
  to the `PoolMeasurementGroup` (#759) - experimental
- Default macro logging filter which improves the output of logging messages.
  Filter can be configured with sardanacustomsettings (#730)
- Possibiltiy to configure ORB end point for Tango servers with Tango DB
  free property (#874)
- Enhance software synchronization by allowing function generation when
  group has 1 repeat only (#786)
- Tab completion in spock for Boolean macro parameters (#871)
- Information about controller properties in `sar_info` macro (#855, #866)

### Fixed
- Ensure that value buffer (data) events are handled sequentially so data
  are not wrongly interpreted as lost (#794, #813)
- Push change events from code for measurement group attributes: moveable,
  latency time and synchronization (#736, #738)
- `getPoolObj` random `AttributeErrors: _pool_obj` errors in macros (#865, #57)
- Pre-scan snapshot (#753)
- Avoid loading configuration to disabled controllers in measurement group
  acquisition (#758)
- Spock returning prompt too early not allowing to stop macros on Windows
  (#717, #725, #905)
- Validation of starts and finals for a2scanct, a3scanct, meshct, ... (#734)
- `defelem` macro when using default axis number (#568, #609)
- Boolean macro parameter validation - now works only True, true, 1
  or False, false, 0 (#871)
- Remove numpy and pylab symbols from spock namespace in order to
  not collide with macros e.g. repeat, where, etc. (#893)
- Make SPEC_FileRecorder use LF instead of CRLF even on windows (#750)
- Appending of hooks from sequence XML (#747)
- Avoid problems with MacroServer attributes (Environment and Elements) in
  taurus extesnions by using newly introduced (in taurus 4.4.0) TangoSerial
  serialization mode (#897)
- Pseudo counters in continuous acquisition (#899)
- Split of `PoolPath`, `MacroPath` and `RecorderPath` with OS separator (#762)
- `lsgh` list hooks multiple times to reflect the configuration (#774)
- Avoid errors if selected trajectory in HKL controller doesnot exists (#752)
- Pass motion range information with `MoveableDesc` in `mesh` scan (#864)
- `getElementByAxis` and `getElementByName` of Controller Taurus extension
  class (#872)
- `GScan` intervals estimation (#772)
- `meshct` intervals estimation (#768)
- Documentation on how to install and use Sardana from Git clone (#751)
- Documentation (Sphinx) build warnings (#859, #179, #219, #393)

### Changed
- Change epoch from float to formatted date & time in Spec recorder (#766)
- Documentation hosting from ReadTheDocs to Github Pages (build on Travis) (#826)
- Door and MacroServer references in spock configuration file (profile) to
  use FQDN URI references (#894, #668)

### Deprecated
- `Label` and `Calibration` attributes of discrete pseudo motor in favor
  of `Configuration` attribute (#801)
- `PoolMotorSlim` widget in favor of `PoolMotorTV` widget (#163, #785) 
- `Controller.getUsedAxis` (Taurus device extension) in favor
of `Controller.getUsedAxes` (#609)

### Removed
- Signal `modelChanged()` from ParamBase class to use the call to 
  method onModelChanged directly instead


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
[Unreleased]: https://github.com/sardana-org/sardana/compare/3.1.0...HEAD
[3.1.1]: https://github.com/sardana-org/sardana/compare/3.1.1...3.1.0
[3.1.0]: https://github.com/sardana-org/sardana/compare/3.1.0...3.0.3
[3.0.3]: https://github.com/sardana-org/sardana/compare/3.0.3...2.8.6
[2.8.6]: https://github.com/sardana-org/sardana/compare/2.8.6...2.8.5
[2.8.5]: https://github.com/sardana-org/sardana/compare/2.8.5...2.8.4
[2.8.4]: https://github.com/sardana-org/sardana/compare/2.8.4...2.8.3
[2.8.3]: https://github.com/sardana-org/sardana/compare/2.8.3...2.8.2
[2.8.2]: https://github.com/sardana-org/sardana/compare/2.8.2...2.8.1
[2.8.1]: https://github.com/sardana-org/sardana/compare/2.8.1...2.8.0
[2.8.0]: https://github.com/sardana-org/sardana/compare/2.8.0...2.7.2
[2.7.2]: https://github.com/sardana-org/sardana/compare/2.7.1...2.7.2
[2.7.1]: https://github.com/sardana-org/sardana/compare/2.7.0...2.7.1
[2.7.0]: https://github.com/sardana-org/sardana/compare/2.6.1...2.7.0
[2.6.1]: https://github.com/sardana-org/sardana/compare/2.6.0...2.6.1
[2.6.0]: https://github.com/sardana-org/sardana/compare/2.5.0...2.6.0
[2.5.0]: https://github.com/sardana-org/sardana/compare/2.4.0...2.5.0
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
