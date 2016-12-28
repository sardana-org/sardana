    Title: Introducing Sardana Enhancement Proposals (SEPs)
    SEP: 0
    State: OBSOLETE
    Reason: 
     SEP15 obsoletes TEP0. https://sourceforge.net/p/sardana/wiki/SEP is no 
     longer the index for SEPs, nor it is a wiki. The "Creating a SEP section" of 
     SEP0 is superseded by the one with the same name in SEP15.
    Date: 2016-04-07
    Drivers: Carlos Pascual-Izarra <cpascual@cells.es>
    URL: http://www.sardana-controls.org/sep/?SEP0.md
    License: http://www.jclark.com/xml/copying.txt
    Abstract:
    Workflow for managing discussions about improvements to Sardana
    and archiving their outcomes.


Introduction
------------

This is a proposal to organize discussions about Sardana enhancements,
reflect their current status and, in particular, to archive their
outcomes, via a new lightweight process based on Sardana Enhancement
Proposals (SEPs). This idea is a shameless copy of the Debian Enhancement Proposal
system with a few adjustments to the Sardana project reality.


Motivation
----------

The main reason for using SEPs is to provide a central index in which to list such
proposals, which would be useful to see at a glance what open fronts
there are at a given moment in Sardana, and who is taking care of them
and, additionally, to serve as a storage place for successfully
completed proposals, documenting the outcome of the discussion and the
details of the implementation.


Workflow
--------

A "Sardana enhancement" can be pretty much any change to Sardana,
technical or otherwise. Examples of situations when the SEP process
might be or might have been used include:

* Introducing a new feature in Sardana (e.g. HKL support)
* Introducing/modifying a policy or workflow for the community

The workflow is very simple, and is intended to be quite lightweight:
an enhancement to Sardana is suggested, discussed, implemented, and
becomes accepted practice (or policy, if applicable), in the normal
Sardana way. As the discussion progresses, the enhancement is assigned
certain states, as explained below. During all the process, a single URL
maintained by the proposers can be used to check the status of the
proposal.

The result of all this is:

  1. an implementation of the enhancement and
  2. a document that can be referred to later on without having to dig
     up and read through large discussions.

The actual discussions should happen in the sardana mailing lists (normally sardana-devel, unless the discussion may benefit from getting input from the wider audience of sardana-users). This way, SEPs do not act as yet another forum to be followed.

In the same way, SEPs do not give any extra powers or authority to
anyone: they rely on reaching consensus,
by engaging in discussions on mailing lists, IRC, or real life meetings
as appropriate. In case of dispute, the ultimate decision lies in the Sardana Executive Committee defined in the Sardana MoU.

The person or people who do the suggestion are the "drivers" of the
proposal and have the responsibility of writing the initial draft, and
of updating it during the discussions, see below.


Proposal states
---------------

![SEP state diagram](res/sep0_workflow.png)

A given SEP can be in one of the following *states*:

* DRAFT
* CANDIDATE
* ACCEPTED
* REJECTED
* OBSOLETE

The ideal progression of states is DRAFT -> CANDIDATE -> ACCEPTED, but
reality requires a couple of other states and transitions as well.

### DRAFT state: discussion

* every new proposal starts as a DRAFT
* anyone can propose a draft
* each draft has a number (next free one from document index)
* normal discussion and changes to the text happen in this state
* drafts should include *extra* criteria for success (in addition to
  having obtained consensus, see below), that is, requirements to
  finally become ACCEPTED

#### DRAFT -> CANDIDATE: rough consensus

In order for a SEP to become CANDIDATE, the following condition should
be met:

* consensus exists for *what* should be done, and *how* it should be
  done (agreement needs to be expressed by all affected parties, not
  just the drivers; silence is not agreement, but unanimity is not
  required, either)

### CANDIDATE: implementation + testing

The CANDIDATE state is meant to prove, via a suitable implementation
and its testing, that a given SEP is feasible.

* of course, implementation can start in earlier states
* changes to the text can happen also in this period, primarily based
  on feedback from implementation
* this period must be long enough that there is consensus that the
  enhancement works (on the basis of implementation evaluation)
* since SEP are not necessarily technical, "implementation" does not
  necessarily mean coding

#### CANDIDATE -> ACCEPTED: working implementation

In order for a SEP to become ACCEPTED, the following condition should
be met:

* consensus exists that the implementation has been a success

### ACCEPTED: have fun

Once accepted:

* the final version of the SEP text is archived on the Sardana wiki
* if applicable, the proposed SEP change is integrated into
  authoritative texts such as policy, developer's reference, etc.

#### {DRAFT, CANDIDATE} -> REJECTED

A SEP can become REJECTED in the following cases:

* the drivers are no longer interested in pursuing the SEP and
  explicitly acknowledge so
* there are no modifications to a SEP in DRAFT state for 6 months or
  more
* there is no consensus either on the draft text or on the fact that
  the implementation is working satisfactorily

#### ACCEPTED -> OBSOLETE: no longer relevant

A SEP can become OBSOLETE when it is no longer relevant, for example:

* a new SEP gets accepted overriding previous SEPs (in that case the
  new SEP should refer to the one it OBSOLETE-s)
* the object of the enhancement is no longer in use

### {REJECTED, OBSOLETE}

In one of these states, no further actions are needed.

It is recommended that SEPs in one of these states carry a reason
describing why they have moved to such a state.


What the drivers should do
--------------------------

The only additional burden of the SEP process falls on the shoulders of its
drivers. They have to take care of all the practical work of writing
and maintaining the text, so that everyone else can just continue
discussing things as before.  Driver's burden can be summarized as:

* Write the draft text and update it during discussion.
* Determine when (rough) consensus in discussion has been reached.
* Implement, or find volunteers to implement.
* Determine when consensus of implementation success has been reached,
  when the testing of the available implementation has been satisfactory.
* Update the SEP with progress updates at suitable intervals, until the
  SEP has been accepted (or rejected).

If the drivers go missing in action, other people may step in and
courteously take over the driving position.

**Note**: the drivers can of course participate in the discussion as
everybody else, but have no special authority to impose their ideas to
others. <q>SEP gives pencils, not hammers.</q>


Format and content
------------------

A SEP is basically a free-form plain text file, except that it must
start with a paragraph of the following RFC822-style headers:

* Title: the full title of the document
* SEP: the number for this SEP
* State: the current state of this revision
* Date: the date of this revision
* Drivers: a list of drivers (names and e-mail addresses), in RFC822
  syntax for the To: header
* URL: during DRAFT state, a link to the wiki place of the draft
  (typically probably https://sourceforge.net/p/sardana/wiki/SEPxxx)
* Abstract: a short paragraph describing the SEP

(Additionally, REJECTED SEPs can carry a "Reason:" field describing
why they were rejected.)

The rest of the file is free form. Since the SEP is kept in a wiki, using
its markup syntax is, of course, a good idea.

Suggested document contents:

* An introduction, giving an overview of the situation and the motivation
  for the SEP.
* A plan for implementation, especially indicating what parts of Sardana need
  to be changed, and preferably indicating who will do the work.
* Preferably a list of criteria to judge whether the implementation has been
  a success.
* Links to mailing list threads, perhaps highlighting particularly important
  messages.


License
-------

The SEP must have a license that is DFSG free. You may choose the
license freely, but the "Expat" license is recommended. The
official URL for it is <http://www.jclark.com/xml/copying.txt> and
the license text is:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Copyright (c) <year>  <your names>

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The justification for this recommendation is that this license is one
of the most permissive of the well-known licenses. By using this
license, it is easy to copy parts of the SEP to other places, such as
documentation for Sardana development or embedded in individual
packages.



Creating a SEP
--------------

The procedure to create a SEP is simple: send an e-mail to
`sardana-devel@lists.sourceforge.net`, stating that you're taking the next
available number, and including the first paragraph of the SEP as
explained above. It is very important to include the list of drivers,
and the URL where the draft will be kept up to date. The next available
SEP number can be obtained by consulting 
<https://sourceforge.net/p/sardana/wiki/SEP>.

It is also a very good idea to mention in this mail the place where the
discussion is going to take place, with a pointer to the thread in the
mailing list archives if it has already started.

The actual place where the SEP draft is going to be published is up to the SEP driver (e.g., it can be a plain text file or sphinx file in a code repository) but the sardana project provides infrastructure to host it in its wiki for convenience. If you decide to host the SEP draft in the sardana wiki, just create a new wiki page named <https://sourceforge.net/p/sardana/wiki/SEPxxx>, where xxx is the SEP number.

Independently of where the draft is hosted you should edit the list of SEPs in <https://sourceforge.net/p/sardana/wiki/SEP> to add a link to the new SEP.



Revising an accepted SEP
------------------------

If the feature, or whatever, of the SEP needs further changing later,
the process can start over with the accepted version of the SEP document
as the initial draft. The new draft will get a new SEP number. Once the
new SEP is accepted, the old one should move to OBSOLETE state.

As an exception, **trivial** changes may be done in the same SEP without
requiring a new SEP number as long as:

- the intention to change is communicated by the usual channels, and
- the change is approved by the community, and
- the change gets registered in the document (e.g., in a "Changes" 
section of the document)

**Note:** A *trivial change* here is understood as a *small modification* that 
*does not alter the intention* of the previous text and simply *corrects* 
something that is clearly an *unintended* mistake (e.g., fixing a typo, 
fixing a broken link, fixing a formatting mistake). *Format translations* (e.g. 
adapting the Markdown formatting to reStructuredText format), can also be considered
trivial changes. In case of doubt or discrepancies, it is always better
to opt for the standard procedure of creating a new SEP that obsoletes 
the current one.

License
-------

The following copyright statement and license apply to SEP0 (this
document).

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
-------

* 2016-11-22: [mrosanes](https://github.com/sagiss/) 
  Migrate SEP from SF wiki to independent file, 
  modify URL. Pass from ACCEPTED to OBSOLETE according SEP15.

* 2016-11-22:
  [mrosanes](https://github.com/sagiss/) Create SEP0.md.

* 2016-04-07: 
  [cpascual](https://sourceforge.net/u/cpascual/) Pass from CANDIDATE to ACCEPTED (it was in candidate for testing its application with several real cases, but its text has been basically unaltered since 2013)
  
* 2014-05-22: 
  [cpascual](https://sourceforge.net/u/cpascual/) Minor formatting changes

* 2013-12-09:
  [cpascual](https://sourceforge.net/u/cpascual/) Added provision for Trivial Changes in "Revising an accepted SEP" section

* 2013-08-21:
  [cpascual](https://sourceforge.net/u/cpascual/) Clarification of the procedure for creating a new SEP

* 2013-06-06:
  [cpascual](https://sourceforge.net/u/cpascual/) Initial version written after crude "translation" of the [DEP0](http://dep.debian.net/deps/dep0/)


