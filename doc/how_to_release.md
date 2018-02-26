# How to release (draft)

This is a guide for sardana release managers: it details the steps for making
an official release, including a checklist of stuff that should be manually
tested.

## The release process

1. During all the development, use the Milestones to keep track of the intended
   release for each issue
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
    1. Review and update the CHANGELOG.md if necessary. See [this](http://keepachangelog.com)
    2. Bump version using `bumpversion <major|minor|patch> && bumpversion release`
       (use [semver](http://semver.org/) criteria to choose amongst `major`,
       `minor` or `patch`
    3. The version numbers used in the man pages of the Sardana scripts are
       bumped (you may use `taurus/doc/makeman` script executing it from the
       doc directory e.g. `sardana/doc`) and committing the changes.
    4. Create a PR to merge the `release-XXX` against the **`master`** branch
       of the sardana-org repo
    OPTIONAL: Sardana depends on Taurus, and the required version of Taurus
    may need to be bumped as well. Taurus and other dependencies are specified
    in: `setup.py` (requires list of strings) and `src/sardana/requirements.py`
    (`__requires__` dictionary and taurus.core value).
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