# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).
This file follows the formats and conventions from [keepachangelog.com]

Find Sardana issues in the following locations:
[old SF sardana issues](https://sourceforge.net/p/sardana/tickets/)
[migrated sardana issues](https://github.com/sardana-org/sardana/issues)


## [Unreleased]

### Added
- bumpversion support
- This CHANGELOG.md file


## [2.1.1] - 2016-09-27
For a full log of commits between versions run (in your git repo):
`git log 2.1.0..2.1.1`

### Fixed
Fix SF issues: #509, #507, #508, #511, #426


## [2.1.0] - 2016-09-13
For a full log of commits between versions run (in your git repo):
`git log 2.1.0..2.0.0`
Main improvements since sardana 2.0.0 (aka Jan16) are:

### Added
- Add itango dependency to make Sardana compatible with the latest
PyTango 9.2.0. Sardana CLI client (spock) has been adapted. (SF #487)
- Add an optional block output of the scan records in spock - the new records
can be printed on top of the previous ones. (SF #492)

### Changed
- Make Sardana compatible with Taurus4. Since Taurus4 introduces some
backwards incompatibilities (http://sourceforge.net/p/tauruslib/wiki/TEP14)
Sardana implements a compatibility layer in order to supprt Taurus v3 and v4.
Taurus4 deprecation warnings are present. (SF #452)
- Re-introduce a possibility to decode repeat parameters for macros that use
only one repeat parameter, located at the end of the definition, from a flat
list parameters - grouping is not necessary. (SF #491)
- Improve the sequencer behaviour. (SF #483, #485)
- Improve the documentation. (SF #489, #490, #491)

### Fixed
- Fix sporadic "already involved in operation" errors in the scans when using
0D experimental channels. (#104)
- Solve other bugs (SF #499, #493, #492, #488, #485, #484, #483, #482, #478,
 #418, #405, #104)


## [2.0.0] - 2016-04-28
For a full log of commits between versions run (in your git repo):
`git log 1.6.2..2.0.0`
Main improvements since sardana 1.6.1 (aka Jul15) are:

### Added
- Add HKL support (SEP4)
- Add support to external recorders (#380, #409, #417);
  Sardana recorder classes and related utilities were relocated.
- Add macro tw to standard macros (#437)
- Add possibility to rename pool elements (#430)

### Changed
- Improve support of repeat macro parameters (#3, #466) -
  multiple and/or nested and/or arbitrarily placed repeat parameters are
  allowed now; some external macros may experience backwards incompatibility -
- Improve the Door status behaviour (#120, #427)
- Correct PoolPath precedence - now it respects the order (#6) -
  it may change behavior of systems where controller overriding was used

### Fixed
- Solve other bugs (#223, #359, #377, #378, #379, #381, #382, #387, #388, #390,
  #394, #403, #406, #411, #415, #424, #425, #431, #447, #449, #451, #453, #454,
  #461)

### Removed
- Remove templates to fix issue with rtd theme (#447)


## [1.6.1] - 2015-07-28
For a full log of commits between versions run (in your git repo):
`git log 1.6.0..1.6.1` 
Hotfix in order to bump the version number so the distribution files change 
names.

### Changed
- Update man pages
- PyPI does not allow to upload the same files twice. See:
  https://sourceforge.net/p/pypi/support-requests/468
  https://www.reddit.com/r/Python/comments/35xr2q/howto_overwrite_package_when_reupload_to_pypi
  During the release process, the first upload was erroneous - wrong version of
  Python was assigned to the files. These files were removed.


## [1.6.0] - 2015-07-27
Release of Sardana 1.6.0 (the Jul15 milestone)
Main improvements since sardana 1.5.0 (aka Jan15) are:

### Added
- Allow Sardana execution on Windows (#228)
- New macros dmesh and dmeshc (#283)
- Document DriftCorrection feature
- Sardana docs available in RTD (#5, #358)
- Add option to display controller and axis number, in the output from wm/wa (#239)

### Changed
- Improve speed of wa macro(#287)
- Allow undefine many elements at the same time, using udefelem (#127)
- Allow reading of motor position when the motor is out of SW limits (#238)

### Fixed
- Fix meshc scan
- Solve bug in ascanc when using a pseudomotor (#353)
- Solve bugs related to loading macros/modules (#121 ,#256)
- Solve bug with PoolMotorTV showing AttributeError (#368 ,#369, #371)
- Solve bugs and features related with test framework (#249, #328, #357)
- Solve other bugs (#65, #340, #341, #344, #345, #347, #349)



[keepachangelog.com]: http://keepachangelog.com
[Unreleased]: https://github.com/sardana-org/sardana/tree/develop
[2.1.1]: https://github.com/sardana-org/sardana/releases/tag/2.1.1
[2.0.0]: https://github.com/sardana-org/sardana/releases/tag/2.0.0
[1.6.1]: https://github.com/sardana-org/sardana/releases/tag/1.6.1
[1.6.0]: https://github.com/sardana-org/sardana/releases/tag/1.6.0


