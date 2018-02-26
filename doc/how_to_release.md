# How to release (draft)

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
   personal fork (in which case you should do step 4.iv **now** to allow other
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
    4. Create a PR to merge the `release-XXX` against the **`master`** branch
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

## Manual test checklist

This is a check-list of manual tests. It is just orientative. Expand it
at will. This list assumes a clean environment with all Sardana dependencies
already installed and access to a Tango system with the TangoTest DS running.

Hint: this list can be used as a template to be copy-pasted on a release PR

### Installation
- [ ] Install Sardana from the tar.gz : `pip install <tarball_artifact_URL>`

### Create testing environment and run testsuite
- [] Start Pool demo2. In a console do `Pool demo2`.
- [] Start MacroServer demo2 and connect to the Pool demo2.
  In another console do: `MacroServer demo2`
- [] Set MacroServer's MacroPath to <sardana>/macroserver/macros/examples.
  In another IPython console do: `PyTango.DeviceProxy('<macroserver>').put_property({'MacroPath':'<path_to_sardana_installation_dir>/macroserver/macros/examples'})`
- [] Restart MacroServer e.g. Ctrl+C in the MacroServer's console and
  start it again.
- [] Create spock profile demo2. In another console do `spock --profile=demo2`
- [] In spock run `sar_demo` macro.
- [] Edit <path_to_sardana_installation_dir>/sardanacustomsettings.py to point to the correct door e.g. `UNITTEST_DOOR_NAME = "door/demo2/1"`
- [] Run testsuite. In another console do `sardanatestsuite`

