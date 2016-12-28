# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).
This file follows the formats and conventions from [keepachangelog.com]


## [Unreleased]

### Added
-

## [2.2.0] - 2016-12-22
For a full log of commits between versions run (in your git repo):
`git log 2.1.1..2.1.2`

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
[Unreleased]: https://github.com/sardana-org/sardana/compare/2.2.0...HEAD
[2.2.0]: https://github.com/sardana-org/sardana/compare/2.1.1...2.2.0
[2.1.1]: https://github.com/sardana-org/sardana/compare/2.1.0...2.1.1
[2.1.0]: https://github.com/sardana-org/sardana/compare/2.0.0...2.1.0
[2.0.0]: https://github.com/sardana-org/sardana/compare/1.6.1...2.0.0
[1.6.1]: https://github.com/sardana-org/sardana/compare/1.6.0...1.6.1
[1.6.0]: https://github.com/sardana-org/sardana/releases/tag/1.6.0
