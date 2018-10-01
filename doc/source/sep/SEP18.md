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
5. *Extend Generic Scan Framework* (GSF), more preciselly scan in step mode 
with measurement preparation (repetitions=n) if possible i.e. scan macro knows
beforehand the number of points.

Implementation
--------------

Measurement group is extended by the *prepare* command with two parameters: 
synchronization description and number of repeats (these repeats is a 
different concept then the one from the synchronization description). The 
second one indicates  how many times measurement group will be started, with
the *start* command, to measure according to the synchronization description. 

1. Measurement group - Tango device class
    * Add `Prepare` command. TODO: investigate the best way to pass 
    synchronization description, as JSON serialized string, together with the 
    repeats integer.
    * Remove `synchronization` attribute (experimental API) - no backwards 
    compatibility.
2. Measurement group - core class
    * Add `prepare(synchronization, repeats=1)` method
    * Remove `synchronization` property  (experimental API) - no backwards 
    compatibility. 
3. Measurement group - Taurus extension
    * Add `prepare` method which simply maps to `Prepare` Tango command
    * Add `count_single` (TODO: find the best name for this 
    method, other candidates are `count_raw`, `acquire`) method according to 
    the following pseudo code:
        * `Start()`
        * `waitFinish()`
    * Implement `count` method according to the following pseudo code:
        * `prepare(synchronization & repeats = 1)` where synchronization 
        contains the integration time
        * `count_single()`
    * Implement `count_continuous` (previous `measure`) method according to 
    the following pseudo code:
        * `prepare(synchronization & repeats = 1)` where synchronization may
        contain the continuous acquisition description
        * `subscribeValueBuffer()`
        * `count_single()`
        * `unsubscribeValueBuffer()`
4. GSF - step scan
    * `SScan` implemented according to the following pseudo code:
        * If number of points is known:
            * `prepare(synchronization, repeats=n)` where synchronization 
            contains the integration time and n means number of points
            * `for step in range(n): count_single()`
        * If number of points is unknown:
            * `while new_step: count()`
