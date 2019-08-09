# Guidelines for Contributing to Sardana

The Sardana repository uses nvie's branching model, known as [GitFlow][].

In this model, there are two long-lived branches:

- `master`: used for official releases. **Contributors should 
  not need to use it or care about it**
- `develop`: reflects the latest integrated changes for the next 
  release. This is the one that should be used as the base for 
  developing new features or fixing bugs. 

For the contributions, we use the [Fork & Pull Model][]:

1. The contributor first [forks][] the official sardana repository
2. The contributor commits change to a branch based on the 
   `develop` branch and pushes it to the forked repository.
3. The contributor creates a [Pull Request][] (PR) against the `develop` 
   branch of the official sardana repository.
4. Anybody interested may review and comment on the PR, and 
   suggest changes to it (even doing PRs against the PR branch).
   At this point more changes can be committed on the 
   requestor's branch until the result is satisfactory.
5. Once the proposed code is considered ready by an appointed sardana 
   integrator, the integrator merges the PR into `develop`.

## Notes:
  
- These contribution guidelines are very similar but not identical to 
  those for the [GithubFlow][] workflow. Basically, most of the 
  GitHubFlow recommends can be applied for Sardana except that the 
  role of the `master` branch in GithubFlow is done by `develop` in our 
  case. 
  
- If the contributor wants to explicitly draw the attention of some 
  specific person to the review process, [mentions][] can be used
  
- If a pull request (or a specific commit) fixes an open issue, the pull
  request (or commit) message may contain a `Fix #N` tag (N being 
  the number of the issue) which will automatically [close the related 
  issue][tag_issue_closing]

# Coding conventions:

In general, the contributions to Sardana should consider following:

- The code must comply with the sardana coding conventions:
  - We try to follow the standard Python style conventions as
    described in [Style Guide for Python Code](http://www.python.org/peps/pep-0008.html)
  - Code **must** be python 2.6 compatible
  - Use 4 spaces for indentation
  - use ``lowercase`` for module names. If possible prefix module names with the
    word ``sardana`` (like :file:`sardanautil.py`) to avoid import mistakes.
  - use ``CamelCase`` for class names
  - "shebang line" should be the first line of a python module 
    ```
    #!/usr/bin/env python
    ```
  - python module should contain license information (see template below)
  - avoid populate namespace by making private definitions private (``__`` prefix)
    or/and implementing ``__all__`` (see template below)
  - whenever a python module can be executed from the command line, it should 
    contain a ``main`` function and a call to it in a ``if __name__ == "__main__"``
    like statement (see template below)
  - document all code using [Sphinx][] extension to [reStructuredText]{}

- The contributor must be clearly identified. The commit author 
  email should be valid and usable for contacting him/her.

- Commit messages  should follow the [commit message guidelines][]. 
  Contributions may be rejected if their commit messages are poor.

- The licensing terms for the contributed code must be compatible 
  with (and preferably the same as) the license chosen for the Sardana 
  project (at the time of writing this file, it is the [LGPL][], 
  version 3 *or later*).

The following code can be used as a template for writing new python modules to
Sardana:

```python
    #!/usr/bin/env python
    # -*- coding: utf-8 -*-

    ##############################################################################
    ##
    ## This file is part of Sardana
    ## 
    ## http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
    ##
    ## Copyright 2019 CELLS / ALBA Synchrotron, Bellaterra, Spain
    ## 
    ## Sardana is free software: you can redistribute it and/or modify
    ## it under the terms of the GNU Lesser General Public License as published by
    ## the Free Software Foundation, either version 3 of the License, or
    ## (at your option) any later version.
    ## 
    ## Sardana is distributed in the hope that it will be useful,
    ## but WITHOUT ANY WARRANTY; without even the implied warranty of
    ## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    ## GNU Lesser General Public License for more details.
    ## 
    ## You should have received a copy of the GNU Lesser General Public License
    ## along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
    ##
    ##############################################################################

    """A :mod:`sardana` module written for template purposes only"""

    __all__ = ["SardanaDemo"]
    
    __docformat__ = "restructuredtext"
    
    class SardanaDemo(object):
        """This class is written for template purposes only"""
        
    def main():
        print "SardanaDemo"s
    
    if __name__ == "__main__":
        main()
```

# Documentation Style Guide

- All standalone documentation should be written in plain text (``.rst``) files
  using [reStructuredText][] for markup and formatting. All such
  documentation should be placed in directory `doc/source` of the Sardana
  source tree. The documentation in this location will serve as the main source
  for Sardana documentation and all existing documentation should be converted
  to this format.
- **Up to which level we will guarantee the documentation to be addressable?** 
   We guarantee up to three levels of the documentation chapters to be addressable.
   For example: Sardana Documentation (level 1) -> Developer's Guide (level 2) -> Writing macros (level 3)
- **How to document Tango specific interfaces/implementation?**
   Sardana documentation should be as much as possible Control System (server layer) agnostic.
   In general, only the Tango API should contain Tango interfaces explanation.
- **How to refer to Sardana and its elements**
   We use the following names:
   * Sardana - Sardana project
   * Sardana server - Sardana server
   * Device Pool - Pool of devices
   * Pool server - Device Pool server process
   * MacroServer - Environment where macros are defined and Macro execution contexts resides 
   * MacroServer server - MacroServer server process
   * macro - user procedure
   * Spock - Sardana CLI
- **Which writing style should I use?**
   We suggest to use the second person writing style, for example:
   "In order to stop the macro you need to press Ctrl+C".

# Continuous Integration

We practice Continuous Integration (CI) in the Sardana project for any PR or direct
push to its `master` or `develop` branches. At the time of writing this guide this
includes the following jobs:

- [Sardana tests](https://sardana-controls.org/devel/howto_test/index.html)
  run, at least, on the current Debian stable release will be executed by [Sardana travis-ci][].
  You may use [sardana-test Docker container](https://hub.docker.com/r/reszelaz/sardana-test)

- [Sardana travis-ci][] will check it for each Pull Request (PR) using
  the latest version of [flake8 available on PyPI][]. The check
  will be done just on this part of code that is modified by the PR
  together with some lines of context.
  In case the check fails, please correct the errors and commit
  to the PR branch again. You may consider running the check locally
  using the [flake8_diff.sh][] script in order to avoid unnecessary commits.

- [Sardana travis-ci][] will build the documentation and publish it on GitHubPages:
  [](www.sardana-controls.org) and check if there are any [Sphinx][]
  build warnings.

Failure of any of the above jobs will give information to the sardana integrtors that your
PR is not ready for review. If you find problems with fixing these errors do not hesitate to ask for
help in the PR conversation!


[gitflow]: http://nvie.com/posts/a-successful-git-branching-model/
[Fork & Pull Model]: https://en.wikipedia.org/wiki/Fork_and_pull_model
[forks]: https://help.github.com/articles/fork-a-repo/
[Pull Request]: https://help.github.com/articles/creating-a-pull-request/
[commit message guidelines]: http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
[GitHubFlow]: https://guides.github.com/introduction/flow/index.html
[mentions]: https://github.com/blog/821-mention-somebody-they-re-notified
[tag_issue_closing]: https://help.github.com/articles/closing-issues-via-commit-messages/
[Sardana]: http://www.sardana-controls.org
[LGPL]: http://www.gnu.org/licenses/lgpl.html
[Sardana travis-ci]: https://travis-ci.org/sardana-org/sardana
[flake8_diff.sh]: https://github.com/sardana-org/sardana/blob/develop/ci/flake8_diff.sh
[flake8 available on PyPI]: https://pypi.org/project/flake8
[Sphinx]: http://www.sphinx-doc.org
[reStructuredText]: http://docutils.sourceforge.net/rst.html
