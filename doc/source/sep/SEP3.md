	Title: Adapt to TEP3 (Tango-independent taurus.core)
	SEP: 3
	State: REJECTED (handled in TEP3 and TEP14)
	Date: 2013-06-26
	Drivers: Carlos Falcon-Torres <cfalcon@cells.es>, Carlos Pascual-Izarra <cpascual@cells.es>
	URL: http://www.sardana-controls.org/sep/?SEP3.md
	License: http://www.jclark.com/xml/copying.txt
	Abstract:
	The goal of this SEP is to adapt Sardana to the changes from the Taurus 
	Enhancement Proposal #3 (TEP3) which refactors the taurus core to provide 
	independence from Tango. 



REJECTION NOTICE
=================

This SEP is obsoleted since the scope of the original [TEP3][] to which this SEP refers was splitted into [TEP3][] and [TEP14][] and their implementation into Taurus4.

**The required adaptation of sardana to Taurus4 will be handled in ticket [SF#452][]**

Introduction & Motivation
=========================

THIS proposal is a consequence of the [TEP3][], which 
describes the refactoring of Taurus to make the Tango dependency optional 
instead of mandatory. The [TEP3][] deprecates many APIs and introduces some 
backward incompatibilities. The SEP3 aims to adapt Sardana to the changes 
imposed by [TEP3][].

Note: originally, the [TEP3][] was started as SEP3 and it only became split 
after the application of [SEP10][]. Most of the requirements initially 
stated in the SEP3 draft have been moved to the [TEP3][], and only those 
requirements specifically affecting the sardana code remain in this SEP.

Requirements
==================

* Sardana should work with the changes implemented in the TEP3.

* Reliance on backwards-compatibility APIs should be avoided.

Implementation
==============

The necessary changes are implemented in the *sep3* branch of the sardana 
canonical repository (git://git.code.sf.net/p/sardana/sardana.git)

Links to more details and discussions
======================================

The discussions about the SEP3 itself are in the sardana-devel mailing list.

License
=======

The following copyright statement and license apply to SEP3 (this
document).

Copyright (c) 2013 CELLS / ALBA Synchrotron, Bellaterra, Spain

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
========

2013-06-26
[cmft](https://sourceforge.net/u/cmft/) First draft based on previous 
documents and discussions with [tiagocoutinho](https://sf.net/u/tiagocoutinho/) 
and [cpascual](https://sf.net/u/cpascual/)

2013-11-04
[cpascual](https://sf.net/u/cpascual/) Partial rewrite of section on 
implementation. Also some spellchecking.

2013-11-04
[cpascual](https://sf.net/u/cpascual/) Partial rewrite of section on 
implementation. Also some spellchecking.

2013-11-06
[cmft](https://sf.net/u/cmft/) Including  "getting things done" section

2014-04-28
[cmft](https://sf.net/u/cmft/) Changed API description for validators

2014-08-13
[cpascual](https://sf.net/u/cpascual/) General update of the document 
based on code review and discussions with [cmft](https://sf.net/u/cmft/). 
Also added the "Changes" section.

2014-08-14
[cpascual](https://sf.net/u/cpascual/) Added some more tasks to 
implementation plan and reference to [Taurus_URIRefactoring] document

2014-10-03
[cpascual](https://sf.net/u/cpascual/) Updated pending tasks and completed 
some info about validators

2015-05-06
[cpascual](https://sf.net/u/cpascual/) Updated to reflect split into SEP3 
and TEP3 according to [SEP10][]

2015-05-06
[cpascual](https://sf.net/u/cpascual/) changed from DRAFT to CANDIDATE

2016-04-04
[cpascual](https://sf.net/u/cpascual/) changed from CANDIDATE to REJECTED (it is obsoleted by Taurus4)

2016-11-29: 
[mrosanes](https://github.com/sagiss) Migrate SEP3 from SF wiki to independent file, modify URL, fix formatting and correct links.


[TEP3]: http://www.taurus-scada.org/tep/?TEP3.md
[TEP14]: http://www.taurus-scada.org/tep/?TEP14.md
[SF#452]: https://github.com/sardana-org/sardana/issues/297
[SEP10]: http://www.sardana-controls.org/sep/?SEP10.md
