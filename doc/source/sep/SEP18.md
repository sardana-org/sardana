    Title: Extend acquisition and synchronization concepts for SEP2 needs.
    SEP: 18
    State: DRAFT
    Reason:
     New acquisition and synchronization concepts are necessary in order to
      properly integrate 1D and 2D experimental channels in Sardana (SEP2).
    Date: 2018-05-30
    Drivers: Zbigniew Reszela <zreszela@cells>             
    URL: https://github.com/reszelaz/sardana/blob/sep18/doc/source/sep/SEP18.md
    License: http://www.jclark.com/xml/copying.txt
    Abstract:
     SEP6 defined some acquisition and synchronization concepts for the needs
     of the continuous scan. When working on the 1D and 2D experimental 
     channels integration we see that more concepts are necessary. This SEP 
     introduces them.

Terminology
-----------

* Measurement - a measurement process that may, but not necessarily, involve 
multiple acquisitions e.g. measurement group count, continuous scan, step scan.
* Acquisition - a single acquisition e.g. over an integration time, which is a 
part of a measurement

Current Limitations
-------------------

* The Software and Hardware synchronization types terminology is not self 
descriptive. Internal and External terminology describes better these types.
* Some hardware or even the Lima library allows some synchronization modes 
that are not foreseen in Sardana and are necessary.
* Some experimental channels could benefit from preparing them for multiple 
acquisitions before the measurement e.g. software synchronized continuous 
scan or step scan.

Objectives
----------

Overcome the above limitations.

Design
------

1. Document well that:
    * Software(Trigger|Gate) are synonyms to Internal (Trigger|Gate). 
    Internal means that Sardana will synchronize the acquisitions.
    * Hardware(Trigger|Gate) are synonyms to External(Trigger|Gate).
    External means that an external to Sardana object (could be hardware)
    will synchronize the acquisitions.
2. Extend AcqSynch with two new options:
    * SoftwareStart (which means internal start)
    * HardwareStart (which means external start)
3. Extend AcqSynchType with one new option (supported from expconf):
    * Start
4. Allow different types of preparation of channels:
    * Per measurement preparation with repetitions=n e.g. Prepare(One|All) 
    or a controller parameter
    * Per acquisition preparation with repetitions=1 e.g. Load(One|All)
6. Modify acquisition actions (and synchronization action if necessary) so 
they support the new concepts added in points 2 and 4.
5. Extend GSF (step mode) with measurement preparation (repetitions=n) if 
possible i.e. scan macro knows beforehand the number of points.
