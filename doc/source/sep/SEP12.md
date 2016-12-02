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


Motivation
==========

Enums have been added to [Python 3.4](http://docs.python.org/3.4/library/enum.html "enum in python 3.4") ([PEP 435](http://legacy.python.org/dev/peps/pep-0435/#id26)). Official Enum implementation has lots of advantages when compared with taurus private implementation of Enumeration:

* [Class API](http://legacy.python.org/dev/peps/pep-0435/#id26) and [Functional API](http://legacy.python.org/dev/peps/pep-0435/#functional-api)
* human readable string representation
* proper *repr*
* type of an enumeration member is the enumeration it belongs to
* Enums also have a property that contains just their item name
* Support iteration, in definition order
* Enumeration members are hashable, so they can be used in dictionaries and sets
* Error checking when there are repeated enumeration members
* Enumerations are pickable
* Enumerations are comparable
* Enumerations members are not restricted to integers. For example, they can be strings


Implementation
==============

The official python enum module is only present since 3.4. Fortunately python enum has been back-ported to python >= 2.4 in a package called [enum34](https://pypi.python.org/pypi/enum34).

Taurus code should access Enum class using the mechanism devised in [SEP11].
This mechanism will:

    <if python >= 3.4> 
      use python standard enum
    <elif enum34 back-port package is installed>
      use enum from enum34
    <else>
      use private implementation of enum34 provided by taurus

The official back-port of enum34 is just a simple python module with the definition of the <code>Enum</code> and <code>IntEnum</code> classes. As a last resort (python < 3.4 *and* enum34 back-port not installed), taurus can provide a private implementation of enum34. Therefore, enum34 is an **optional** dependency of taurus.

This SEP proposes to change the internal taurus code to use the new Enum (directly or indirectly).

Backward compatibility
----------------------

In order to maintain backward compatibility the <code>taurus.core.util.enumeration</code> will still exist but its usage should be marked as deprecated.

These are the foreseen compatibility issues:

1. taurus Enumeration has some methods: whatis, has_key, keys, get which are not in the standard python Enum.
2. Some improper usage of taurus Enumeration
    1. usage of Enumeration member as an integer.
    2. taurus Enumeration item can be accessed with the dictionary interface both with Enum key or Enum value (example: <code>LockStatus\["Locked"\]</code> or <code>LockStatus\[2\]</code>). Python Enum only supports dictionary access with key (which makes sense, of course)

To solve problem 1, the SEP proposes to re-factor all calls to these methods with the python Enum equivalent code. Further, taurus enumerations that inherit from <code>taurus.core.util.Enumeration</code> should inherit instead from a new <code>taurus.core.util.Enum</code> which in turn inherits from <code>enum.Enum</code> and implements the missing methods. This reduces the risk of backward incompatibility to a minimum.

Problem 2.1 is an improper usage of Enumeration. The SEP assumes that this specific improper usage is internal to taurus and it proposes that effort is spent to make sure this is fixed internally in taurus (Example of this improper usage in taurus.qt.qtgui.display.qled)

Problem 2.2 comes from a faulty design in the original Enumeration API. It seems to be technically impossible to simulate this behavior using the python Enum. It is actually against enumeration design to do this sort of thing. Taurus code is free from its usage so internally no change is required. 

Although most enumerations are intended to be used only internally by taurus, and because of the dynamic nature of python, improper usage of taurus enumerations by third-party taurus applications can never be guaranteed. These applications, if they exist, would require changes to work with a new version of taurus. This is, in fact, a general statement that could be applied to any change in python code. This SEP considers important that it is mentioned explicitly anyway.

License
=======

Copyright (c) 2014 Tiago Coutinho

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

* 2016-11-29 [mrosanes](https://github.com/sagiss) 
  Migrate SEP12 from SF wiki to independent file.

* 2014-03-05 [tiagocoutinho](https://sourceforge.net/u/tiagocoutinho/)
  Changed state to CANDIDATE

* 2014-03-03 [tiagocoutinho](https://sourceforge.net/u/tiagocoutinho/)
  Add internal implementation and backward compatibility details

* 2014-02-24 [tiagocoutinho](https://sourceforge.net/u/tiagocoutinho/)
  Initial version
 
