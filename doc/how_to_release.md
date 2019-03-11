# How to release

This is a guide for sardana release managers: it details the steps for making
an official release, including a checklist of stuff that should be manually
tested.

## The release process

1. During all the development, use the Milestones to keep track of the intended
   release for each issue.
2. Previous to the release deadline, re-check the open issues/PR and update
   the assignation issues/PR to the release milestone. Request feedback from
   the devel community.
3. Work to close all the PR/issues remaining open in the milestone. This can
   be either done in develop or in a release branch called `release-XXX`
   (where `XXX` is the milestone name, e.g. `Jul17`). If a release branch is
   used, `develop` is freed to continue with integrations that may not be
   suitable for this release. On the other hand, it adds a bit more work
   because the release-related PRs (which are done against the `release-XXX`
   branch), may need to be also merged to develop.
   Note: the `release-XXX` branch *can* live in the sardana-org repo or on a
   personal fork (in which case you should do step 4.v **now** to allow other
   integrators to push directly to it).
4. Create the release branch if it was not done already in the previous step
   and:
    1. Review and update the CHANGELOG.md if necessary. See [this](http://keepachangelog.com).
    2. Bump version using `bumpversion <major|minor|patch> && bumpversion release`
       (use [semver](http://semver.org/) criteria to choose amongst `major`,
       `minor` or `patch`. OPTIONAL: Sardana depends on Taurus, and the
       required version of Taurus may need to be bumped as well. Taurus and
       other dependencies are specified in: `setup.py` (requires list of
       strings) and `src/sardana/requirements.py` (`__requires__` dictionary
       and taurus.core value).
    3. The version numbers used in the man pages of the Sardana scripts are
       bumped (you may use `taurus/doc/makeman` script executing it from the
       doc directory e.g. `sardana/doc`) and committing the changes.
       There is a known [problem with the spock version number](https://github.com/sardana-org/sardana/issues/518).
    4. In the code use version number instead of milestone in deprecation
       warnings (if any) e.g. replace *Jul18* with *2.5.0*.
    5. Create a PR to merge the `release-XXX` against the **`master`** branch
       of the sardana-org repo
5. Request reviews in the PR from at least one integrator from each
   participating institute. The master branch is protected, so the reviews need
   to be cleared (or dismissed with an explanation) before the release can be
   merged.
6. Perform manual tests (see checklist below). You may use the CI artifacts
   (e.g., from appveyor) and post the results in the comments of the PR.
7. Once all reviews are cleared, update the date of the release in the
   CHANGELOG.md, merge the PR and tag in master.
8. Merge also the  `release-XXX` branch into develop, and bump the version of
   develop with `bumpversion patch`
9. Release to PyPI **from a clean checkout** and using [twine](https://github.com/pypa/twine):
   ```
   cd /tmp
   git clone https://github.com/sardana-org/sardana.git -b <RELEASE_TAG>
   cd sardana
   python setup.py sdist bdist_wheel
   twine upload dist/*
   ```
10. Complete GitHub release (upload artifacts, edit text)
11. Create news in www.tango-controls.org
    1. On the News page click on Submit a news and fill up the form (if it doesn't work, try opening in new tab):
       * Title: New Release Of Sardana X.X.X (Jan|JulXX)
       * Ilustration: sardana or official logo (use png)
       * Summary: short summary of the news (do not include the whole changelog here..)
       * Categories: Release
    2. After submitting click on Modify this content text of the area \<\<Content\>\> and provide detailes of the release e.g. changelog.
12. Notify mailing lists (sardana-users@lists.sourceforge.net, sardana-devel@lists.sourceforge.net, info@tango-controls.org)

## Manual test checklist

This is a check-list of manual tests. It is just orientative. Expand it
at will. This list assumes a clean environment with all Sardana dependencies
already installed and access to a Tango system with the TangoTest DS running.

Hint: this list can be used as a template to be copy-pasted on a release manual test issues

### Installation
- [ ] Install Sardana (on Linux from the tar.gz : `pip install <tarball_artifact_URL>`
  and on Windows from MSI)
  **Note:** On openSuse 11.1 there are problems with pip, try `python setup
  .py install`

### Create testing environment and run testsuite
- [ ] Start Pool demo2. In a console do `Pool demo2`.
- [ ] Start MacroServer demo2 and connect to the Pool demo2.
  In another console do: `MacroServer demo2`
- [ ] Set MacroServer's MacroPath to point to the macro examples.
  In another IPython console do:
  `PyTango.DeviceProxy('macroserver/demo2/1').put_property({'MacroPath':'<path_to_sardana_installation_dir>/macroserver/macros/examples'})`
  **Note:** Remember to use OS path separator e.g. '/' on Linux and '\' on 
  Windows
- [ ] Restart MacroServer e.g. Ctrl+C in the MacroServer's console and
  start it again.
- [ ] Create spock profile demo2. In another console do `spock --profile=demo2`
- [ ] In spock run `sar_demo` macro.
- [ ] Edit `<path_to_sardana_installation_dir>/sardanacustomsettings.py`
  to point to the demo2 door e.g. `UNITTEST_DOOR_NAME = "door/demo2/1"`
- [ ] Run testsuite. In another console do `sardanatestsuite`
  **Note:** On openSuse 11.1 and Windows there are known problems with 
  testsuite. Check previous release comments.

### Test Sardana using Spock and expconf
- [ ] Test interactive macros from spock e.g. `ask_for_moveable`, `ask_peak`
  **Note**: On Windows there are known bugs. 
- [ ] Execute `umvr` macro and verify that the position updates arrives.
- [ ] In expconf configure scan files by setting ScanDir to: `/tmp/` on Linux
  `C:\Users\<username>\tmp` on Windows and ScanFile to: `demo1.h5, demo1.dat`.
- [ ] Configure online plot to show counters: On expconf GUI select for all
  the counter channels, Plot Type 'Spectrum' and Plot Axes '\<mov\>'
- [ ] Configure snapshot group: with a motor and the `sys/tg_test/1/ampli`
  attribute.
- [ ] Add the `sys/tg_test/1/double_scalar` attribute to the measurement
  group.
- [ ] Open online plot (This should ask to enable JsonRecorder, set it to true. Otherwise enable it in spock: `senv JsonRecorder True`).
- [ ] Run step scan
- [ ] Verify that records appear in spock output.
- [ ] Verify that records were stored in scan files.
- [ ] Verify that records were plotted on the online plot
- [ ] Run `showscan` and access to the last scan data.
- [ ] With `edmac` modify existing macro: `ask_peak` and run it to verify that the change
  was applied.
- [ ] With `edmac` create a new macro in a new macro library:
  `edmac my_macro <path_to_sardana_installation_dir>/macroserver/macros/examples/my_macros.py`
  and run it.
  **Note:** Remember to use OS path separator e.g. '/' on Linux and '\' on 
  Windows

### Test Sardana with TaurusGUI

- [ ] Create the GUI using this [guide](https://sourceforge.net/p/sardana/wiki/Howto-GUI_creation)

#### PMTV (PoolMotorTaurusValue)
- [ ] Move motors from the slit panel in absolute and relative modes.
- [ ] Show expert view.
- [ ] Show compact mode.

#### macroexecutor
- [ ] Execute `ascan` macro
- [ ] Pause it in the middel and resume
- [ ] Abort it
- [ ] Add it to favorites
- [ ] Run `lsm` macro
- [ ] Execute `ascan` from favorites
- [ ] Run `lsmac` macro
- [ ] Execute `ascan` from history
- [ ] Edit `dscan` macro in spock yellow line and run it
- [ ] Restart macroexecutor application
- [ ] Run `lsm` from history
- [ ] Run `ascan` from favorites

#### sequencer
- [ ] Add `ascan` macro to the sequence
- [ ] Add `lsct` macro as a `post-acq` hook of `ascan`
- [ ] Add `dscan` macro to the sequence
- [ ] Run the sequence
- [ ] Save sequence to a file
- [ ] Start new sequence
- [ ] Load sequence from a files
- [ ] Run the loaded sequence

#### sardanaeditor
**Note:** There are known bugs on CentOS and Windows
- [ ] Open sardanaeditor with macroserver name as argument.
- [ ] Browse macro libraries and open an existing macro.
- [ ] Edit existing macro and save & apply chaneges.
- [ ] Execute macro to see if changes were aplied.
- [ ] Create a new macro using template.
- [ ] Execute the newly created macro.
