	Title: Direct load of .ui files
	SEP: 11
	State: ACCEPTED
	Date: 2014-07-24
	Drivers: Tiago Coutinho <coutinho@esrf.fr>
	URL: http://www.sardana-controls.org/sep/?SEP11.md
	License: http://www.jclark.com/xml/copying.txt
	Abstract:
	Currently, some taurus widgets are designed using the QtDesigner.
	The resulting .ui files are transformed into python code with taurusuic4(pyuic4).
	The widgets use the generated code to build themselves.
	This approach has some problems. This SEP tries to solve them by directly building
	the widgets with the original .ui file.
