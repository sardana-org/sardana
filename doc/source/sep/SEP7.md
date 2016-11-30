	Title: Code contribution workflow
	SEP: 7
	State: OBSOLETE
	Reason: 
	 SEP15 obsoletes SEP7. Most of the contribution procedure is 
	 no longer applicable due to the adoption of a workflow based on Pull Requests.
	Date: 2013-12-13
	Drivers: Carlos Pascual-Izarra <cpascual@cells.es>
	URL: http://www.sardana-controls.org/sep/?SEP7.md
	License: http://www.jclark.com/xml/copying.txt
	Abstract:
	 Define the procedures for contributing code to sardana. It covers git 
	 repository conventions and organization as well as workflows and tools
	 for reviewing code contributions.



Introduction
============

This is a proposal to define the mechanisms for contributing code to Sardana. It describes the agreed conventions for using the git repository as well as the workflow(s) and tools used for reviewing code prior to its acceptance into the official sardana repository.

This proposal tries to answer the following questions:

- Which conventions (e.g., naming, organization...) are used in the official git repository?
- How should one submit a proposed contribution?
- Who approves/rejects proposed contributions?
- Which tools/workflows are used for reviewing the proposed contributed code?


Goals and constraints
=====================

The following goals and constraints are taken into consideration for this proposal:

General:

- **Open development**: we want to encourage participation and contribution. We want an open development project (not just open source). 
- **Code review**: we want sardana to be robust. Contributed code should be reviewed.
- **Integration manager availability**: currently none of the involved people can dedicate 100% of time to coordination tasks. We need to minimize and share the load of coordination/integration.
- **Autonomy for contributions to 3rd party code**: the sardana project also hosts repositories for specific hardware and 3rd party code (currently,  Macros and Controllers, see [SEP1]). More flexible policies should apply to contributions to these repositories, giving just a minimum set of rules and giving more freedom to 3rd parties for self-organization.

Specific/technical:

- **Avoid multiplicity of platforms**: we host the code in 3 git repositories hosted in sourceforge.net (see [SEP1]) and favour the tools already provided by SourceForge to the Sardana project.
- **SF account required**: we assume that all contributors already have a sourceforge.net account
- **Minimise platform lock-down**: it should be possible to move the project to a different platform if needed in the future, without data loss and without forcing big workflow changes.
- **Minimise imposed log-ins**: contributors and reviewers should be able to do most (if possible, all) their daily work without needing to log into SourceForge. Workflows of contribution/code review which integrate a mailing-list interface are preferred.
- **Contributions traceability**: We would like to have a way of tracking the status of contributions (e.g., proposed / changes needed / accepted / rejected).


Which conventions (e.g., naming, organization...) are used in the official git repository?
==========================================================================================

Branching model for the core repository of sardana
--------------------------------------------------

The official repository of sardana (from now on also called "origin") is organised following the [gitflow](http://nvie.com/posts/a-successful-git-branching-model/) branching model, in which there are two main long-running branches (*master* and *develop*) and a number of support finite-life branches (feature, release and hotfix branches). 

Please refer to http://nvie.com/posts/a-successful-git-branching-model for a full description of the gitflow. The following are notes to complement the gitflow general information with specific details on the implementation of the gitflow model in Sardana:

- The *master* branch reflects the latest official Sardana release. Only the Integration/Release Managers can push to the *master* branch.
- The *develop* branch reflects the latest development changes that have already been integrated for the next release. Only the Integration Managers can push to the *develop* branch.
- New features, bug fixes, etc. must be developed in *feature* branches. They branch off *develop*. Once they are ready and the code passed the review, the feature branch can be merged into *develop* by an Integration Manager. These branches may exist only in local clones of contributors, or in repositories forked from development or, in certain cases, in the official repository (see below).
- The two other types of supporting branches (release branches and hotfix branches) are managed by the Integration/Release managers for the purpose of preparing official releases.

In the Sardana project, we use a special type of *feature* branches called *sepX* branches: unlike other *feature* branches which typically only exist in the contributor local repository (or maybe in a public fork of the official repository), the *sepX* feature branches are hosted in the oficial repository. The *sepX* branch may be created if required during the DRAFT or CANDIDATE phases of the *X*th Sardana Enhancement Proposal, and is merged to *develop* if the SEPX is APPROVED. Only the person(s) dessignated by the SEPX driver -and approved by the Sardana project Admins- can push to the official *sepX* branch. These designated person(s) are considered **"SepX Integration Lieutenants"**.

**Tip**: You can find a set of practical examples on working with the sardana branching model in the [sardana git recipes](http://sf.net/p/sardana/wiki/git-recipes/)

Branching model for the 3rd party code repositories
---------------------------------------------------

The main differences between the core repository and the 3rd party code repositories are:

- The 3rd party code is not subject to the same release schedule than the core code (e.g. the release schedule of a given macro is up to the responsible for that macro, and not synchronized with the release of other macros). 

- The 3rd party code repositories (e.g. the Controllers and Macros repositories) are open for pushing commits by a larger group of contributors (write permissions are granted liberally to people who request them to the Sardana project Administrators). 

- Each file (or whole directory) in the 3rd party repositories must provide contact information of the person who assumes responsibility for it (and this person should have write permission). In absence of explicit information in the file headers, the last person who committed to the file is assumed to be the responsible for it.

- There are no appointed Integration Managers for the 3rd party code. The repository is self-organised, and conflicts are avoided by following conventions and discussing in the mailing lists.

Because of these differences, the branching model is much more simple and flexible for the 3rd party repositories:

- There is only one main branch, *master*, which contains code that is deemed to be production-ready by the responsibles of each piece of code.

- Feature branches may be created from (and merged into) *master* for developing new features, but the state of *master* should always be kept "production-ready". The decision on when to merge a given feature branch into *master* should be taken by consensus of the responsibles for all the pieces of code affected by the merge. If the discussions for this are not held publicly (i.e., in the mailing list), it is considered a nice courtesy to *at least* inform in the sardana-devel mailing list of the decission taken .


How should one submit a proposed contribution?
==============================================

In general, code submissions for inclusion in the sardana repositories should take the following into account:

- It must comply with the [**Sardana coding conventions**](http://www.tango-controls.org/static/sardana/latest/doc/html/devel/guide_coding.html).
- The **contributor must be clearly identified** and provide a valid email address which can be used to contact him/her.
- Commit messages  should be [properly formatted](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html).
- The **licensing terms** for the contributed code must be compatible with (and preferably the same as) the license chosen for the Sardana project (at the time of writing this SEP, it is the [LGPL](http://www.gnu.org/licenses/lgpl.html), version 3 *or later*).


Submitting code for the core repository of sardana
---------------------------------------------------

The discussion and public tracking of contributed code is done on the [sardana-devel mailing list](https://lists.sf.net/lists/listinfo/sardana-devel).

Code contributions should be sent to sardana-devel@lists.sourceforge.net either in form of patches (formatted with **git format-patch**, as explained [here](http://www.git-scm.com/book/en/Distributed-Git-Contributing-to-a-Project#Public-Large-Project)) or as a pull request (formatted with **git request-pull** as explained [here](http://www.git-scm.com/book/en/Distributed-Git-Contributing-to-a-Project#Public-Small-Project)).

Specific notes for contributing via patches:

- The preferred way of sending the patch formatted with *git format-patch* is using *git send-email*
- Please read http://www.git-scm.com/book/en/Distributed-Git-Contributing-to-a-Project#Public-Large-Project (and use it as a guide)


Specific notes for contributing via pull requests:

- Please read http://www.git-scm.com/book/en/Distributed-Git-Contributing-to-a-Project#Public-Small-Project (and use it as a guide)
- Important: prepend the subject of your email to the mailing list with **`[PULL]`**
- If the changes are not too big, consider using the "-p" option to *git request-pull* (it includes the diff info in the body of the email)

**Tip**: You can find a set of practical examples on how to submit code according to the SEP7 specifications in the [sardana git recipes](http://sf.net/p/sardana/wiki/git-recipes/)

Submitting code for the 3rd party code repositories
---------------------------------------------------

No formal review process takes place for code contributed to the 3rd party repositories. Anyone with writing permission is allowed to create a branch in them and push code to it. But note that, before pushing to the master branch, you should seek permission from the people responsible for any files that are affected by the merge.

We also encourage contributors to use the sardana-devel mailing list for discussing and coordinating changes to the 3rd party repositories and, in any case, to at least send an email to the list when a relevant change is made.


Who approves/rejects proposed contributions?
============================================

The Sardana community elects a group of people to act as "Integration Managers".

For a given contribution to be accepted into the *develop* branch of the official **core** repository, it has to be submitted to the sardana-devel mailing list (as explained before) and approved by at least one **Integration Manager**. If the contributor happens to be an Integration Manager, it is considered good practice to get the approval of *another* Integration Manager before accepting it (although this can be relaxed for trivial contributions).

For a given contribution to be accepted into the *sepX* branch of the official **core** repository, it has to be submitted to the sardana-devel mailing list (as explained before) and approved by at least one **SepX Integration Lieutenant**. If the contributor happens to be a SepX Integration Lieutenant, the previous rule can be relaxed, and direct pushes may be allowed. Note that ultimately, the approval of an **Integration Manager** is required once the *sepX* branch is to be merged into the *develop* branch.

In the case of the **3rd party** repositories, no approval is required (see the section about "Submitting code for the 3rd party code repositories").


Which tools/workflows are used for reviewing the proposed contributed code?
===========================================================================

The code review process for contributions to the official sardana **core** repository is as follows:

1- The contributor submits a contribution to the mailing list (see "How should one submit a proposed contribution?" above).

2- The contribution is publicly reviewed in the mailing list (everyone is encouraged to participate in the review). 

3- During this phase, the contributor may be asked for further clarifications and/or corrections to the contributed code (in which case a resubmission may be required).

4- Eventually, an Integration Manager (or a SepX Integration Lieutenant if the contribution is for a *sepX* branch) may either accept the contribution and integrate it into the official repository, or reject it. In both cases, he/she is posts a message in the mailing list informing of the decision.

**Tip**: You can find a set of practical examples on how to integrate contributed code according to the SEP7 specifications in the [sardana git recipes](http://sf.net/p/sardana/wiki/git-recipes/)


Naming convention for feature branches
--------------------------------------

The integration of contributed code by an Integration Manager (or Lieutenant) usually involves merging some local branch (let's call it *A*) into the branch that tracks the official repository. Although the *A* branch itself stays local, its name appears in the merge commit message (ending up in the official history). Therefore the following naming convention should be used:

- If the contributed code is related to a bug in the ticket tracker, the branch *A* should be called *bug-N*, where *N* is the ticket number.

- If the contributed code is related to a feature-request in the ticket tracker, the branch *A* should be called *feature-N*, where *N* is the ticket number. Note: in some occasions *feat-N* has mistakenly been used instead of *feature-N* for these branch names. *feature-N* is the recommended convention for branch names.

- In the remaining cases, any descriptive name can be used for branch *A* (preferably lower case and reasonably short) provided that it doesn't use any of the reserved names (i.e. *master*, *develop*, *release-\**, *hotfix-\**, *sepX*, *bug-N*, *feature-N*)

Note that those who contribute code via patches do not need to worry about this convention since their local branch names do not affect the official repository history. Nevertheless, it can be a good practice to follow anyway.
 

Transition phase (obsolete)
===========================

The development and contribution to Sardana could not be stopped till the approval of this SEP, so a set of transitional rules reflecting the *de-facto* conventions that were in place before its approval were summarised in the SEP7. Once SEP7 is approved, these conventions **no longer apply**, and are kept here only for reference (and in order to help understanding the commit history of the project).

Code review (Transitional-obsolete)
-----------------------------------

Before the migration to Git, the sardana and taurus SVN repositories were relatively open to unreviewed commits.

During the Sardana Workshop in Barcelona in June 2013, 3 people (Antonio Milan, Teresa Nunez and Carlos Pascual) were appointed to review new code contributions, but the workflow was not established. 

Note: Since Zbigniew Reszela took the responsibility for the Sardana coordination in ALBA, he was added to the Project Admininstrators group and also to the code reviewing team.

Until this or another related SEP is approved, [using *git format-patch* and *git send-email*](http://git-scm.com/book/en/Distributed-Git-Contributing-to-a-Project#Public-Large-Project) for sending patch proposals to the sardana-devel list is the preferred option. 

Repository organization (Transitional-obsolete)
-----------------------------------------------

The repository organization as of august 2013 reflects what was inherited from the previous SVN. Until the approval of this or another SEP which changes it, we shall continue working as follows:

- The development is done by committing to the master branch.
- Pushing to the official repository is limited to those with admin permissions in the Sardana project (other people may submit patches to the sardana-devel list)
- Work on feature branches (i.e. the *sepX* branches) is done on *sepX* branches **on separate forked repositories** (the fork can be done, e.g. with https://sourceforge.net/p/sardana/sardana.git/fork ), and when ready, a "merge-request" or a "request-pull" or  a patch series is submitted for inclusion in the official repository. The discussion (and code review, if any) for the work on the feature branches, should be done in the sardana-devel list.
- Provisional permissions for pushing code to 3rd party macros and controllers repositories can be requested to the sardana project admins. Alternatively, working on a forked repository and submitting a patch or request-pull on the sardana-devel is also possible.


Links to more details and discussions
=====================================

The main discussions for this SEP take place in the [sardana-devel mailing list](https://sourceforge.net/p/sardana/mailman/).

This SEP uses concepts and nomenclature from [chapter 5 of Pro-Git book](http://git-scm.com/book/en/Distributed-Git)

License
=======

Copyright (c) 2013  Carlos Pascual-Izarra

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Changes
=======

* 2016-11-22: [mrosanes](https://github.com/sagiss/) 
  Migrate SEP7 from SF wiki to independent file, 
  modify URL and change SEP state from ACCEPTED to OBSOLETE according SEP15.

* 2015-01-27: [cpascual](https://sourceforge.net/u/cpascual/) 
  Added note in the naming convention for feature branches (about preference of feature-N over feat-N for branches associated to feature-request tickets) 

* 2013-12-13: [cpascual](https://sourceforge.net/u/cpascual/) 
  Changedd state to ACCEPTED, after introducing modification to the procedure for accepting contributions to *sepX* branches, [as agreed in the sardana-devel mailing list](https://sourceforge.net/p/sardana/mailman/message/31694852/)

* 2013-11-29: [cpascual](https://sourceforge.net/u/cpascual/) 
  Preparing for passing to ACCEPTED. Transitional notes removed or moved to appendix and links to practical instructions for the workflow added.

* 2013-11-04: [cpascual](https://sourceforge.net/u/cpascual/) 
  Promoted from DRAFT to CANDIDATE state

* 2013-08-29: [cpascual](https://sourceforge.net/u/cpascual/) 
  First *complete* draft written after merging all inputs from the sardana-devel mailing list as well as private discussions.

* 2013-08-05: [cpascual](https://sourceforge.net/u/cpascual/) 
  Initial version written
