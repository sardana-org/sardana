	Title: Continuous Scan Implementation
	SEP: 6
	State: CANDIDATE
	Date: 2013-07-29
	Drivers: Zbigniew Reszela <zreszela@cells.es>
	URL: http://www.sardana-controls.org/sep/?SEP6.md
	License: http://www.jclark.com/xml/copying.txt
	Abstract:
	 Generic Scan Framework requires extension for a new type of scans: continuous scans.
	 Various types of synchronization between moveable and acquisition elements exists:
	 software (so called best effort) and hardware (either position or time driven).
	 The challenge of this SEP is to achieve the maximum generalization and transparency 
	 level between all types of continuous scans (and probably step scans as well). This 
	 design and implementation will require enhancement of the already existing elements of 
	 Sardana: controllers, moveables, experimental channels and measurement group and 
	 probably definition of new elements e.g. triggers. A proof of concept work was already 
	 done at ALBA, and it could be used as a base for the further design and development.
