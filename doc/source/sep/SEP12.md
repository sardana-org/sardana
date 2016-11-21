	Title: Use python Enum instead of taurus Enumeration
	SEP: 12
	State: CANDIDATE
	Date: 2014-02-28
	Drivers: Tiago Coutinho <coutinho@esrf.fr>
	URL: http://www.sardana-controls.org/sep/?SEP12.md
	License: http://www.jclark.com/xml/copying.txt
	Abstract:
	Currently, taurus uses an internal private implementation of Enumeration.
	This SEP suggests to replace the private Enumeration with the standard 
	python Enum approved in python 3.4. Old python versions can use an 
	official back-port.
	Taurus can provide an internal implementation in case none of the 
	previous is available.
