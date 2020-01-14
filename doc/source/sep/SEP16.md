    Title: Plugins (controllers, macros, etc.) catalogue
    SEP: 16
    State: ACCEPTED
    Reason:
     SEP15 migrated the Sardana repository from SourceForge to GitHub.
     The third-party repositories are still at SourceForge and a decision
     is pending on what to do with them.
    Date: 2017-04-03
    Drivers: Zbigniew Reszela <zreszela@cells.es>
    URL: https://github.com/reszelaz/sardana/blob/sep16/doc/source/sep/SEP16.md
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
feature branches, pull-requests, tags, independent git history etc.
2. Let developers organize their repositories according to their preferences.
3. Let developers organize plugins in projects so they could have their own
issue trackers, wiki pages, etc.
4. Do not force the hosting platform.
5. Give visibility to the well maintained plugins.

Design
------

* Sardana organization will no more manage the plugins repositories.
  These will be managed directly by their developers.
* Sardana organization will advice on how to organize the plugin projects.
* Sardana organization will maintain a catalogue of the third party plugins.

### Old third-party repositories

The old third-party repositories([controllers](https://sourceforge.net/p/sardana/controllers.git/ci/master/tree/)
and [macros](https://sourceforge.net/p/sardana/macros.git/ci/master/tree/))
will stay opened until we move the actively maintained plugins. This process
may continue after this SEP gets ACCEPTED.

### Advices on how to organize plugins projects

This SEP leaves to the plugin developer the decision on how to organize the 
project. However based on years of experience of developing Sardana plugins
we have observed some common patterns and questions that emerge to the 
developer on how to organize the project. The Community will maintain a 
document with a set of advices, analysis of possible scenarios and lessons 
learnt on how to organize plugins projects but won't give neither clear
answers nor rules. This document is out of the scope of this SEP is
we anticipate it to evolve in the future and be very dynamic.

### Catalogue

A new repository, called sardana-plugins, will be added to the sardana-org
GitHub organization. This repository will not contain any of the plugins
itself but will serve as a catalogue of all the plugins. The only role of this
catalogue will be to list all the plugins together with the information
on where to find more information about them e.g. links to the project pages
or artifacts. Github searches over this repository will be useful when looking
for a plugin.

The catalogue will group plugins in categories. The categories may change in
 the future and new categories may be added. Also plugins may change between
 categories in order to facilitate the users the process of finding them.

Initially the following categories will be created:

* Hardware - lists plugins for specific hardware like, motor controllers,
  counting cards, etc. Example: IcePAP, Pmac, NI6602.
* Instrument - lists plugins for a specific instrument like, tables,
  monochromators, attenuators. Example: three-legged table, DCM.
* System - lists plugins for the complete systems e.g. beamlines, laboratories.
* Software/Interfaces - lists plugins for interacting with other control 
systems, frameworks  e.g. Lima, Tango, Taurus.
* Other - lists plugins that does not meet any other criteria.

See Appendix 1 for alternative options that were evaluated.

The sardana-plugins repository will be managed exactly the same 
as the sardana repository (administrators, push permissions, etc.). In order
to add a new plugin to the catalogue, one would need to open a PR with the 
necessary changes in the catalogue. Anyone interested in receiving updates
on new plugins in the catalogue will just need to subscribe to this GitHub 
repository.

Implementation
--------------

### Old third-party repositories

* Whenever a plugin module is moved away from the old repository it is 
necessary to delete this module from the old location.
* A README file gets added to the old repository with information about this
SEP and location of the plugins catalogue.

### Advices on how to organize plugins projects

Currently the advices on how to organize plugins projects are written in
this [wiki page](https://github.com/sardana-org/sardana/wiki/How-to-organize-your-plugin-project).
This location may change in the future without affecting this SEP

### Catalogue

1. Implement sardana-plugins catalogue using the markdown format with one file
   per category. The plugin projects are listed alphabetically within the 
   category. This format and organization of files may change in the future 
   not affecting this SEP.
2. Start accepting PR to the sardana-plugins catalogue whenever this SEP gets
   into the CANDIDATE state.

Appendix 1
----------
**Alternative Option 1**

(This option was discarded when discussing the SEP but is kept here for 
reference)

This is a conservative option. It simply reflects the organization of
the current repositories and adds two more categories: Recorders and GUIs.

Catalogue will be divided in the following categories:
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

**Alternative Option 2**

(This option was discarded when discussing the SEP but is kept here for 
reference)

Mix of selected categories and alternative option 1. The catalogue 
will have all the categories from the alternative option 1
and the System category from the selected categories. The extra System 
category is because maintaining an up-to-date catalogue of plugins from a 
system like a beamline is not realistic.



Changes
-------

- 2017-04-03 [reszelaz](https://github.com/reszelaz) Create SEP16 draft
- 2019-07-16 [reszelaz](https://github.com/reszelaz) Rename register to 
catalogue
- 2019-07-16 [reszelaz](https://github.com/reszelaz) Move to CANDIDATE after
meeting with DESY, MAXIV and SOLARIS
- 2019-11-28 [reszelaz](https://github.com/reszelaz) Move to ACCEPTED after
meeting with DESY, MAXIV and SOLARIS

