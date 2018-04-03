    Title: Migration of third-party repositories (controllers and macros)
    SEP: 16
    State: DRAFT
    Reason:
     SEP15 migrated the Sardana repository from SourceForge to GitHub.
     The third-party repositories are still at SourceForge and a decision
     is pending on what to do with them.
    Date: 2017-04-03
    Drivers: Zbigniew Reszela <zreszela@cells.es>
    URL: http://github.com/reszelaz/sardana/blob/aa0ec93c7e868409a1a362c28fbadbe2a68e8b8f/doc/source/sep/SEP16.md
    License: http://www.jclark.com/xml/copying.txt
    Abstract:
     SEP15 migrated the Sardana project from SourceForge to GitHub but
     left the third-party repositories, controllers and macros, at their
     original location. This SEP takes care about the third-party
     repositories reorganization so the plugins maintenance will become
     more developer friendly and plugins more accessible to the user.
     This is achieved by simply transferring the project ownerships
     from the Sardana administrators to the plugins developers at the same
     time giving some advices on how to organize the projects based
     on the current experience.


Current Situation
-----------------

Controllers and macros repositories are two separate repositories which
host all the plugins, both the ones that are generic and the ones which
are specific to the systems like ALBA’s or DESY’s beamlines.

The controllers repository has two top level directories which divide
the plugins into the ones written in Python and the ones written in C++
(obsolete). Underneath, one directory per controller type exists e.g. motor,
pseudomotor, countertimer, etc. Finally, controller modules are either
directly placed in that directories e.g. AdlinkAICoTiCtrl.py, or
a dedicated directory is created for a given controller IcePAPCtrl or
a family of them PmacCtrl.

In the macros repository, the macro modules are either grouped in
directories, usually per system, e.g. ALBA_BL22_CLAESS, DESY_P01 or placed
directly in the repository e.g. albaemmacros.py.

No third party repository exists neither for recorders, nor for GUIs/widgets.

Objectives
----------

1. Enable natural way of working using git, like for example, use of the
feature branches, pull-requests, tags, etc.
2. Let developers organize plugins in projects so they could have their own
issue trackers, wiki pages, etc.
3. Do not force the hosting platform.
4. Give visibility to the well maintained plugins.

Design
------

* Sardana organization will no more manage the plugins repositories.
  These will be managed directly by their developers.
* Sardana organization will advice on how to organize the plugin projects.
* Sardana organization will maintain a register of the third party plugins.

### Register

A new repository, called sardana-plugins, will be added to the sardana-org
GitHub organization. This repository will not contain any of the plugins
itself but will serve as a register of all the plugins. The only role of this
register will be to list all the plugins together with the information
on where to find more information about them e.g. links to the project pages
or artifacts. Github searches over this repository will be useful when looking
for a plugin.

**Option 1**

This is a conservative option. It simply reflects the organization of
the current repositories and adds two more categories: Recorders and GUIs.

Register will be divided in the following categories:
* Motor controllers
* Pseudomotor controllers
* Counter/timer controllers
* Pseudocounter controllers
* I/O register controllers
* 0D controllers
* 1D controllers
* 2D controllers
* Trigger/gate controllers
* Macros
* Recorders
* GUIs

**Option 2**

This option is more revolutionary. Register will be divided into the following
categories:
* Hardware - lists plugins for specific hardware like, motor controllers,
  counting cards, etc. Example: IcePAP, Pmac, NI6602.
* Instrument - lists plugins for a specific instrument like, tables,
  monochromators, attenuators. Example: three-legged table, DCM.
* System - lists plugins for the complete systems e.g. beamlines, laboratories.
* Software - lists plugins for interacting with other control systems,
  frameworks  e.g. Lima, Tango, Taurus.
* Other - lists plugins that does not meet any other criteria.

**Option 3**

Mix of options 1 and 2. The register will have all the categories from option 1
and the System category from option 2. This is because maintaining an
up-to-date register of plugins from a system like a beamline is not realistic.

This sardana-plugins repository will be managed exactly the same as the sardana
repository (administrators, push permissions, etc.). In order to add a new
plugin to the register, one would need to open a PR.

Implementation
--------------

1. Implement sardana-plugins register: use the markdown format with one file
   per category.
2. Start accepting PR to the sardana-plugins register whenever this SEP gets
   into the CANDIDATE state.
3. Remove write permissions to the current third-party repositories
   in SourceForge with the Jul18 release.

Advices on how to manage plugins projects
---------------------------------------------------

(Since I anticipate this section to evolve over time it will not be part of
this SEP but will be added to the documentation)

1. Description of the plugins e.g. the purpose, dependencies, installation
   instructions must be documented e.g. README file, project’s wiki pages
   or documentation.
2. Related controllers, macros, recorders and GUIs should coexist in the same
   repository e.g. IcePAP controller (motor and trigger/gate) and IcePAP
   macros. In this case a top level directories in the repository
   e.g. controllers and macros could be useful to group them.
