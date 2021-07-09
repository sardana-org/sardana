	Title: Refactor plugin system
	SEP: 19
	State: DRAFT
	Date: 2020-04-30
	Drivers: Zbigniew Reszela <zreszela@cells.es>
	URL: http://www.sardana-controls.org/sep/?SEP19.md
	License: http://www.jclark.com/xml/copying.txt
	Abstract:
	Sardana comes with custom plugin system for controllers,
    macros and recorders. While it worked pretty well for years
    it has some limitations when used in advanced projects, complicates
    configuration management and is a non-standard solution.
    This SEP refactors the plugin system to use setuptools "entry points".
    
# Rationale and goals

The current Sardana plugin system is a very powerful custom solution which
strongest point is the possibility to add, remove and reload plugins at
runtime. On the other hand it was demonstrated e.g.
[sardana-org/sardana#246](https://github.com/sardana-org/sardana/issues/246)
or
[sardana-org/sardana#247](https://github.com/sardana-org/sardana/issues/247)
that its assumption of plugin classes defined in simple python modules
becomes a limitation. In addition installation of plugins requires a manual,
or hard to script, step of configuring discovery paths.

The goal of this SEP is to refactor the Sardana plugin system in such a way so
it fully supports python programming principles e.g. plugin classes
inheritance, code organization in packages and modules, etc. at the same time
reducing to maximum the manual configuration steps.

# Current Sardana plugin system

The Sardana plugin system works similarly for controllers, macros and recorders.
However it is the macros part which currently brings most advanced
features. For this reason, this SEP focuses on the macro plugins assuming that
the other plugins will simply follow this example.

## Current Macro plugin system

Macros are plugins discovered by scanning `MacroPath` directories for python
modules and inspecting them for classes inheriting from the `Macro` class
or decorated with the `macro` decorator.

Macro plugins comes with the following features:
1. MacroServer keeps a register of all loaded plugins e.g.,
   * `lsmac` lists all macros (with info on which of them overwrites another)
   * `lsmaclib` lists all macro modules
2. Macro code can be reloaded at runtime
   * `relmac` and `relmaclib` macros reloads a macro module (giving info on
   eventual syntax errors)
   * `addmaclib` inspects a new python module present in `MacroPath` for
   macros
3. Macro code can be edited/printed from the client
   * `edmac` spock magic command edits macro code or creates new macros in
   an existing module or in a new module in the highest priority `MacroPath`
   * `prdef` macro prints macro code
4. Macros can be overridden
   * any macro (including built-in macros) could be overridden by a macro
   with the same name higher in the `MacroPath` hierarchy
   * any macro module (including built-in modules) could be overridden
   by a module with the same name higher in `MacroPath` hierarchy
5. MacroServer's `sys.path` can be extended in a custom way:
   * `PathonPath` serves to add arbitrary modules
   * `rellib` macro serves to reload an arbitrary module

## Current Sardana plugin system usege patterns

Sardana plugins are most frequently developed/installed by the following user
profiles:

1. Administrator - typically a Control Engineer giving controls support
to the laboratory
    1. Production ready plugins are installed and not foreseen
    for development. The discovery path is configured accordingly. Eventually
    local modification hot fixes are possible.
    2. Plugins under development are edited and commissioned until considered
    production ready. The discovery path is configured accordingly.
2. Manager - typically a scientist working permanently in the laboratory
    1. Due to the constant necessity to fine tune the plugins, frequently
    under time pressure, the plugins are typically considered under continuous
    development.
    2. The discovery path(s) is usually pre-configured by the administrator and
    the manager places the python modules with the plugins in a flat directory.
    Usually there is only one such a directory per laboratory but multiple
    directories e.g. one per scientist working in the laboratory, are also
    possible.
3. User - typically a visiting Scientist accessing the laboratory
for an experiment
    1. These plugins (usually macros) are quickly prepared and continuously
    edited.
    2. Usually these plugins goes to the Manager's plugin directory but
    ideally there should be one directory per user proposal (what would
    require to configure the discovery path accordingly).

# Specification

The refactored Sardana plugin system will be based on the setuptools
*entry points* mechanism which was successfully evaluated in similar previous
works in the Taurus project:
[TEP13](https://github.com/taurus-org/taurus/blob/develop/doc/source/tep/TEP13.md),
[Add mechanism to discover taurus.qt.qtgui plugins (taurus-org/taurus#684)](https://github.com/taurus-org/taurus/pull/684),
[Add scheme entry point in TaurusManager (taurus-org/taurus#833)](https://github.com/taurus-org/taurus/pull/833/)

This SEP reuses naming convention defined in the
[`pkg_resources` overview](https://setuptools.readthedocs.io/en/latest/pkg_resources.html#overview_).

## Entry point groups

Plugin projects will use setuptools *entry points* to announce Sardana
plugins. At the time of writing of this SEP we specify the entry point group
names for macros, controllers, recorders and widgets respectively:
* `sardana.macroserver.macros`
* `sardana.pool.controllers`
* `sardana.macroserver.recorders`
* TODO: widgets (or maybe these should be entry points to Taurus?)

In the future other groups may be added.

## Suggested new Sardana plugin system usage patterns

Based on the user profile analysis this SEP recommends the following new usage
patterns.

1. Administrator
    1. Production ready distributions will be installed and are not foreseen
    for development. Eventual local modification hot fixes are possible even
    at runtime. Adding new plugins to such distributions is not recommended.
    It is recommended that production ready distribution explicitly define
    entry points in the `setup.py`.
    2. Projects under development will be installed in editable mode using
    pip. 
2. Manager
    1. Create new plugin project (usually done only once and could be even
    done by the Administrator).
        1. Create a new plugin project from the template (see Appendix 1)
        in a workspace directory (by default HOME of the current user).
        2. Install this plugin project in editable mode e.g. `pip3 install -e .`.
        Eventual syntax errors will be reported when running installation.
        The first error will abort the installation process.
        Note that during the installation process the modules will be imported
        and inspected for plugins to fill in the *entry points* information
        automatically.
        3. If done at runtime the newly installed distribution must be added
        to the server process e.g. with the `addplugdist`.
    2. Reload
        1. Reload plugin - this will be done as before e.g. `relmac`, with
        the highlight of the syntax errors. There is only one difference - this
        will not discover added/removed plugins in the same module.
        2. Reload plugin module - this will be done as before e.g. `relmaclib`
        with the highlight of the syntax errors. There is only one difference -
        the modules will be referenced with the full module path e.g.
        `sardana_bl04.macro.hotblower`.
        Note that if plugins were added/removed in the module this will 
        modify the distribution metadata (`entry_points.txt`) and trigger a
        global discovery of plugins (~1 s of extra time for 10 000 plugins).
    3. Add module - this will be done very similar to the previous usage
    e.g. `addmaclib`. There are two differences: the modules will be
    referenced with the full module path e.g. `sardana_bl04.macro.hotblower`
    and the distribution name would need to be provided. Environment variable
    e.g. `DefaultDistribution` could make it optional.
    4. Edit plugin e.g. `edmac`
        1. If an existing macro is passed as argument this will work exactly
        as before with only one difference. On applying changes user will have
        an option to reload only this or all macros.
        2. If a new macro is passed as argument then it will be either created
        in the module passed as argument or in the `DefaultMacroModule` of the
        `DefaultDistribution` or in `macro` module of the newly created
         distribution (in HOME) called `sardana-<instance>` which will be
         installed with `pip` before proceeding to macro edition. 
3. User
    1. It is recommended that each user/proposal has its own plugin project.
    2. The rest of the usage patterns are similar to the Manager. 

## Summary of changes

### Added
* Environment variable `DefaultDistribution`
* Environment variable `DefaultMacroModule`
* Additional optional parameter *distribution* to `addmaclib` macro
* Additional optional argument *distribution* to `edmac` magic command
  in case a module is specified.

### Changed
* Macro modules are referred with full module path
  e.g. `sardana_bl09.macro.hotblower` - this affects `relmaclib`
  and `addmaclib` macros. 

### Removed
* Possibility to overwrite non built-in plugins.
* Possibility to overwrite plugin module
* `rellib` macro
* `PythonPath` properties of Pool and MacroServer

# Implementation

Implementation will directly use `pkg_resources` module.
TODO: evaluate use of
[importlib-metadata](https://importlib-metadata.readthedocs.io/en/latest/)
project - standard from Python 3.8.

A PoC was developed in the
[test-entry-points](https://github.com/reszelaz/test-entry-points) repository.

TODO: check if it will be possible to use dots in magic command completion e.g. 
`relmaclib sardana_bl04.macro.hotblower`

TODO: prepare implementation plan

# Roadmap

1. Try to introduce experimental support for entry points ASAP. For example
treating its plugins similarly to the built-in plugins.
2. Fully refactor plugins system.
3. Validate this SEP by extracting HKL plugins (controller, macros and
widgets) to a separate project.

# Summary of benefits  

1. No need to configure path properties what facilitates deployment
and configuration management.
2. Robust inheritance from plugin classes.
3. Freedom on how to organize modules in packages in plugin projects.
4. No module name conflicts e.g. `homing` module for macros in both IcePAP
and Smaract.
5. No module name restriction e.g. currently forbidden names are `examples`
or `test`.
6. `relmac` only reloads a given macro and not all from the module.
7. Entry points are Python standard.

# Other options

1. Do not change anything.
     * **\+** no changes to the users
     * **\-** there are ~20 tickets which refer to the plugin system.
     Some of them will be automatically solved by this refactoring.
2. Mixed solution (old plugin discovery mechanism + entry points)
    * **\+** no changes to the users if these are happy with what they have
    * **\-** hard to maintain two implementations
3. Entry points solution but with forcing users to install every time
they add plugins.
    * **\+** no to modify `entry-points.txt` metadata file.
    * **\-** more difficult to report syntax errors on reload  

# Appendix 1 - New plugin project template

```
sardana-<name>
├──setup.py
└──sardana_<name>
   ├──__init__.py
   ├──controller.py  # optional; with FooMotorCtrl class template
   ├──macro.py  # optional; with bar macro function template
   └──recorder.py  # optional; with BazRecorder class template 
```

With `setup.py` default contents:

```python
from setuptools import setup, find_packages

from sardana.pool import find_ctrl_ep
from sardana.macroserver import find_macro_ep
from sardana.macroserver import find_recorder_ep

setup(
    name="plugin_project3",
    version="0.1",
    packages=find_packages(),
    install_requires=["sardana"],
    entry_points={
        "sardana.macroserver.macros": find_macro_ep(),
        "sardana.pool.controllers": find_ctrl_ep(),
        "sardana.pool.recorders": find_recorder_ep(),
    }
)
```
