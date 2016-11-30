	Title: Lima integration
	SEP: 2
	State: DRAFT
	Date: 2013-06-25
	Drivers: Gabriel Jover-Manas gjover@cells.es
	URL: http://www.sardana-controls.org/sep/?SEP2.md
	License: http://www.jclark.com/xml/copying.txt
	Abstract:
	Lima is a powerful library adding an abstraction layer to control a 
	broad collection of detectors and perform image post processing.
	This SEP proposes the integration of Lima in order to get full access 
	from Sardana.


Introduction
------------

This SEP describes how to integrate Lima with Sardana at different levels.


Description of current situation
--------------------------------

A Lima controller has been developed in order to control one camera via a LimaCCDs Tango Device Server. Currently ReadOne method returns a numpy array with the image. Moving such amount of data in the Pool is far from optimal and we have the limitation of controlling just one camera per controller


Requirements
------------

The following requirements are given in rough order of importance 

 1. Avoid passing image data via ReadOne. We may define the data source and fix the recorder to read/write the image in final destination.
 2. Create a controller that calls Lima directly
 3. Implement multi-camera controller synchronizing acquisitions with different cameras


Links to more details and discussions
-------------------------------------

The discussions about the SEP2 itself are in the sardana-devel mailing list.


License
-------

The following copyright statement and license apply to SEP2 (this
document).

Copyright (c) 2013  Gabriel Jover-Manas

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

2016-11-30 
[mrosanes](https://github.com/sagiss) Migrate SEP2 from SF wiki to independent markdown language file and correct formatting.



