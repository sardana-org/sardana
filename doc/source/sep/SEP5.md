	Title: Implementation of tests infrastructure
	SEP: 5
	State: ACCEPTED
	Date: 2014-04-29
	Drivers: Marc Rosanes Siscart <mrosanes@cells.es>; Carlos Pascual Izarra <cpascual@cells.es>
	URL: http://www.sardana-controls.org/sep/?SEP5.md
	License: http://www.jclark.com/xml/copying.txt
	Abstract:
	This SEP describes how to implement code testing in Sardana.
	It defines the conventions used in relation with code testing and 
	describes the tools provided by Sardana to help in developing tests.



Introduction
============

Code testing is necessary in Sardana mainly for the following reasons:
- It is necessary for Continuous Integration
- It helps integration managers in evaluating contributed code
- It facilitates adoption, contribution and packaging
- It helps detecting errors, bugs and regressions in the code
- It enables test-driven programming techniques
 
This SEP describes how to implement code testing in Sardana.
It focuses in:

- Describing concepts and conventions regarding code testing in Sardana
- Defining a methodology for performing the tests
- Providing tools and reusable code to automate/facilitate test creation

Note that this SEP does not pretend to provide a set of tests covering most of Sardana, but aims to provide some general tools and guidelines which would enable such tests to be written.


Glossary
========

- [Unit testing](http://en.wikipedia.org/w/index.php?title=Unit_testing&oldid=585783088): has the goal of isolate each part of the program and show that individual parts are correct in terms of requirements and functionality.

- [Integration testing](http://en.wikipedia.org/w/index.php?title=Integration_testing&oldid=579207501): consists of testing combined parts of an application to determine if they function correctly together.

- [System testing](http://en.wikipedia.org/w/index.php?title=System_testing&oldid=563079756): System tests are used to test the system as a whole. Here the system is typically seen as a black-box.

- Module: in this SEP we use 'module' to refer to a Python (sub)module that can be implemented either as a .py file or as a directory containing an `__init__.py` file.  


Description of situation previous to SEP5
=========================================

The situation in pre-SEP5 is that the testing process is poorly implemented in Sardana: testing is informal and non-automatic, and different approaches for testing are used for different parts of the code. 


Goals & Constrains
==================

The following goals and constraints are taken into consideration for this proposal:

- A common framework should be defined.
- Tests code should be easily identifiable and not mixed with "implementation" code.
- Tests included in Sardana must not depend on external infrastructure: an isolated machine in which Sardana is installed and configured should be able to run all the tests.
- For maintainability and portability reasons the testing framework should avoid or minimize introducing new dependencies to Sardana.
- Whenenever possible, tests should be automatic (capable of running unattended). Non-automatic tests shall be clearly identified and its execution must be optional.
- Sardana should provide helper code to simplify the creation of new tests.
- Optionally: Ease code coverage report.


Implementation
==============

In this section we present the framework and the conventions about file naming/organization and code style/documentation that we should follow when testing Sardana. 

In Sardana we use Unit testing (white box testing) as a first testing level. Integration and System testing (grey/black box testing) are performed as a second testing level.


1- Framework
------------

The framework used to perform the Tests is PyUnit which is provided by the `taurus.external.unittest`. This module is essentially the [unittest](http://docs.python.org/2/library/unittest.html) from the Standard Python Library, but it transparently falls back to the [unittest2](http://pypi.python.org/pypi/unittest2) backport if needed (i.e. when the Python version is below 2.7)

If needed, PyQt4.QtTest can be used for aiding in the test of Qt widgets.


2- Organization
---------------

The organization and naming conventions are taken among other reasons in order to allow test auto-discovering thanks to unittest.

Three main kind of files can be found in our Test framework. The **Test modules** inside which the tests will be coded, the **Util modules** and the **Resources**. 

All these files shall be placed under subdirectories named 'test'. The *test* subdirectories can be located inside any Sardana source subfolder according with the part of the code that our test module is testing. 

Each *test* directory must have an `__init__.py` file in order to allow them to be importable. 


#####**Test Case modules**#####

These are submodules containing actual Test Cases (i.e. these are the modules being run while performing tests). Their names are formed by the 'test_' prefix, followed by the name of the module being tested (in the case of Unit tests) or by a name describing the functionality being tested (in the case of Integration and System tests). 

In most cases, Test Case modules are not meant to be imported externally and, therefore, their symbols are not made available from the test parent module.

Hereafter we give some examples of possible Sardana test modules and their organization inside the Sardana code tree:

Example1: for a Unit Test which tests the module implemented in `<sardana>/src/sardana/sardanabase.py`, we create a `<sardana>/src/sardana/test` folder in which we place our `test_sardanabase` module (either implemented as a `test_sardanabase.py` file or as a subdirectory named `test_sardanabase` containing an `__init__.py` file).

Example2: for a stress test of the Pool, the test module would be located in `<sardana>/src/sardana/pool/test/` and can be called test_stress.py.

#####**Util modules**#####

Test directories can have a series of *util submodules* containing common classes and methods that can be imported by other modules. These *util submodules* will not contain any Test Case and shall NOT be prefixed by 'test_'. Other than that, they can be named freely. 

Some methods, classes, constants, etc, from util modules may be imported by other test code; thus, they should be made importable directly from the test parent module (furthermore, the recommended import style is using the parent test module, rather than the util submodule).

#####**Resources**#####

Test directories may have a subdirectory named **res**, containing any necessary resource files for our test. A resource file could be for example: myresource.txt. There are no restrictions at all for the resource file names.

*res* directories must contain an `__init__.py` file in order to ease resource handling.


3- Coding
---------

The following information is useful for the test developer who wants to start coding tests. 

The first point refers to the process of coding using the PyUnit framework. The second point refers to the test documentation that has to be written while coding a specific test.


#####**Testing using PyUnit unittest framework**#####

From now on, we will refer to the `unittest` module, but it should be kept in mind that it should always be imported from `taurus.external`.

Each Sardana Test Case is a class that inherits from `unittest.TestCase`.

Abstract classes to be inherited from a Sardana Test Case must not inherit from `unittest.TestCase`, to avoid them being automatically included in test suites by unittest. Instead, multiple inheritance is to be used by the Sardana Test Case classes.

Each test should be implemented in a separate method which name begins by 'test'.

Preconditions are implemented in the `setUp` method, and postconditions are implemented in the `tearDown` method. Note that 'setUp' and `tearDown` will be executed before and after each test method. The implementation of these two methods is not mandatory but it can be useful.

For executing the Sardana Test Suite go to `<sardana>/src/sardana/test` and execute:
`python testsuite.py`

The test framework should provide utilities to skip certain types of tests, such as these which are interactive or those requiring GUI availability (see, e.g. `taurus.test.skipUnlessGui`)

For a detailed description on how to code using the PyUnit framework, you can refer to the following link: 
http://docs.python.org/2/library/unittest.html


#####**Test Case Documentation**#####

Every Test Case module can contain one or more classes inheriting from `unittest.TestCase`. Each class can have multiple test methods testing different features. 

The tests documentation is written at the Module, Class and Method docstrings using sphinx, as well as in assert messages. In the case of method docstrings, it is recommended to limit the use of sphinx formatting to a level where it is legible as plain text (because PyUnit uses method docstrings in its test summaries).

The following is a list of elements that should be documented (while many are mandatory for integration/system tests, most are optional for unit tests, as indicated in each case):

- In the module docstring:
    - Description of common aspects to the various classes inside a test module. Optional in all cases (unit, integration and system test modules).

- In the Class docstring:
    - Test Case ID. Try to be unique, compose the id from project name, module, submodule, etc. and assign them consecutive numbers. Uppercase and underscore separated IDs are preferred. E.g. MACROSERVER_SCAN_1, POOL_MOTION_123. ( Optional for unit tests )
    - Test Case title. ( Optional for unit tests )
    - Brief explanation about the aspect of the system that is going to be tested. Any aspects common to all the methods of the class can be commented in this field. 
    - Automation. Whether this Test Case is automated or not. ( Optional for unit tests )
    - List the test execution steps in detail. Write the test steps in the order in which these should be executed. Make sure to provide as much details as you can. ( Optional for unit tests )

- In the setUp method docstring:
    - Any prerequisite that must be fulfilled in the setup, before execution of the Test Case. List all pre-conditions in order to successfully execute this Test Case.  

- In each Test method docstring (applies to those methods of a TestCase whose name starts by "test"):
    - Brief explanation of what a given method is testing. This docstring may be shown when running the test.

- In the assert messages:
    - Describe the given inputs
    - Describe what should be the system output after test execution (the expected output).
    - You may as well provide provide the actual output. 

- In the tearDown method docstring: 
    - Describe what should be the state of the system after executing this Test Case.

For any other code not covered here (e.g. helper methods in the TestCase class), just use the standard documentation practices recommended for the Sardana project.

For examples on how to document test code according to the above conventions see:
- `sardana.macroserver.macros.test.test_scan`
- `sardana.macroserver.macros.test.test_list`


Links for more details and discussions
======================================

The discussions about the SEP5 itself are in the [sardana-devel mailing list](https://sourceforge.net/p/sardana/mailman/).


License
=======

The following copyright statement and license apply to SEP5 (this
document).

Copyright (c) 2013 Marc Rosanes Siscart - Carlos Pascual Izarra

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

2013-07-01
[mrosanes](https://sourceforge.net/u/mrosanes/) Creation of SEP5

2013-08-19
[mrosanes](https://sourceforge.net/u/mrosanes/) modified SEP5. We have added various sections: logical structure, implementation, etc. Reason: Internal discussions at Alba between zreszela, cpascual and mrosanes.

2013-08-21
[mrosanes](https://sourceforge.net/u/mrosanes/) added the section Changes in order to keep a tracking of the changed done, by creating a log. Reason: Internal discussions at Alba between zreszela, cpascual and mrosanes.

2013-08-22
[mrosanes](https://sourceforge.net/u/mrosanes/) deletes references to Taurus, as Taurus is part of Sardana.

2013-08-23
[mrosanes](https://sourceforge.net/u/mrosanes/) modified the chapter implementation, structure and naming convention after speaking about it at Alba between cpascual, zreszela and mrosanes.

2013-08-26
[mrosanes](https://sourceforge.net/u/mrosanes/) modified the chapter documentation after speaking about it at Alba between cpascual, zreszela and mrosanes.

2013-08-26
[mrosanes](https://sourceforge.net/u/mrosanes/) documented the chapter coding by presenting the PyUnit framework.

2013-08-29
[mrosanes](https://sourceforge.net/u/mrosanes/) documented the chapter Implementation/Framework, remarking the usage of Python2.7 for coding the test modules. PyUnit requires Python2.7 for its full functionality.  

2013-09-02
[mrosanes](https://sourceforge.net/u/mrosanes/) added link to Sardana mailing list and archives.

2013-09-02
[mrosanes](https://sourceforge.net/u/mrosanes/) added details in integration/system test documentation.

2013-09-05
[mrosanes](https://sourceforge.net/u/mrosanes/) added details and corrections in test documentation.

2013-09-06
[mrosanes](https://sourceforge.net/u/mrosanes/) added example of Test Case documentation generated with Sphinx.

2013-09-06
[cpascual](https://sourceforge.net/u/cpascual/) of introductory text (abstract, intro, goals,... )

2013-11-26
[mrosanes](https://sourceforge.net/u/mrosanes/) minor changes in style and Implementation/Framework

2013-12-13
[mrosanes](https://sourceforge.net/u/mrosanes/) Section 'Theory' disappears and is fused with implementation. 'Glossary' section is created. 

2013-01-14
[mrosanes](https://sourceforge.net/u/mrosanes/) [cpascual](https://sourceforge.net/u/cpascual/) [zreszela](https://sourceforge.net/u/zreszela/) Modified and upgraded Implementation section.

2013-02-07
[gjover](https://sourceforge.net/u/gjover/) Modification of 'Test Case Documentation' section.
[mrosanes](https://sourceforge.net/u/mrosanes/) Update modifications in the wiki.

2014-03-25
[mrosanes](https://sourceforge.net/u/mrosanes/) Correct orthography and how to execute the test suite.

2014-03-26
[mrosanes](https://sourceforge.net/u/mrosanes/) Naming test autodiscovering. ENABLE_GUI_TESTS flag and interactive tests flag.

2014-03-31
[mrosanes](https://sourceforge.net/u/mrosanes/) Some corrections and text restructuring in the Implementation introduction and Implementation->Organization. 

2014-03-31
[mrosanes](https://sourceforge.net/u/mrosanes/) [cpascual](https://sourceforge.net/u/cpascual/) General corrections and text restructuring in Implementation introduction and Implementation->Organization. 

2014-04-01
[mrosanes](https://sourceforge.net/u/mrosanes/) SEP5 from DRAFT to CANDIDATE.

2014-04-01
[cpascual](https://sourceforge.net/u/cpascual/) Some format and minor changes 

2014-04-29
[cpascual](https://sourceforge.net/u/cpascual/) SEP5 goes from CANDIDATE to ACCEPTED

2015-05-13
[cpascual](https://sourceforge.net/u/cpascual/) Fixed date in header to reflect acceptance date

2015-05-15
[cpascual](https://sourceforge.net/u/cpascual/) Another fix in dates (copy-paste error solved)

2016-11-29
[mrosanes](https://github.com/sagiss) Migrate SEP5 from SF wiki to independent file, modify URL and fix formatting.
