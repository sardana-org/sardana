	Title: msenv taurus scheme
	SEP: 14
	State: DRAFT
	Date: 2015-09-18
	Drivers: cfalcon <cfalcon@cells.es>
	URL: http://www.sardana-controls.org/sep/?SEP14.md
	License: http://www.jclark.com/xml/copying.txt
	Abstract:
	Nowadays, access to the environment variables of the MacroServer is not 
	user friendly. MacroServer exposes its environment as an event driven 
	attribute called Environment, with a pickled dictionary as its value. 
	We propose a taurus scheme, msenv, responsible for translating each 
	variable of the enviroment to a taurus attribute.


Introduction
------------
This SEP describes how to create a new taurus scheme for accessing the MacroServer (from now on also refered as MS) environment variables. The goal of this scheme is to propose the read/write logic of the the environment variables as well as its change events mechanism (especially usefull for resolving inconsistency between the multiple environment clients).

Description of the current situation
--------------------------------
The MacroServer loads the environment variables from the encoded file located in /tmp/tango/MacroServer/<macroservername>. The MS loads the variable at the startup, and it overrides the file each time the user creates/changes variables.

The environment variables can be defined at four levels (from less to more retricitive precedence) :

* Global (level 1): MS level. It is the most common and the default way of defining variables.
* Door (level 2): The variables are applicable to all macros run at a given door.
* Macro (level 3): The variables are applicable to a given macro run at any door.
* Door.Macro (level 4): A cobination of level 2 and level 3 -  The variables are applicable to a given macro run at a given door. This is the most restrictive way.

When someone asks for a variable and it does not exist in the scope the environment manager of the MacroServer tries to get it from the lower scope (4 -> 3 -> 2 ->1 ). TODO: confirm that 

The Sardana CLI ("Spock"), connects to a door (configurable via profile) and offers a way to read/write the MacroServer environment. Using Spock a user can set or modify the whole environment (on all levels). This is done using the *senv* and *usenv* macros:

Lets see an example:
```python
#!/usr/bin/python
senv ScanDir "/tmp" # global level
# or
senv DOOR_NAME.ScanDir  "/tmp" # door level
# or
senv MACRO_NAME.ScanDir "/tmp" # macro level
# or
senv DOOR_NAME.MACRO_NAME.ScanDir "/tmp" # door.macro level
```

A user friendly access to the environement from outside of the **Spock** has been a requirement for a long time. Nowadays, developers are forced to do complicated scripts for read/write environment variables or simply give up with its use in favor of the intermediate Tango device servers (responsible for configuration) in their applications.

Lets see an example:
```python
#!/usr/bin/python
import taurus
from taurus.core.util import CodecFactory

attr_env = taurus.Attribute('macroserver/cfalcon/1/environment')
env_value = attr_env.read().value
decoded_env_value = CodecFactory().decode(env_value, 'pickle')
print decoded_env_value['new']['ScanDir']
```
Requirements
------------
This SEP proposes to create a simple taurus scheme for read and write of the MS environment variables. The scheme should use the folowing URI names:

* Authority - a Tango Database: msenv:[//HOST:PORT]  
* Device - a MS Tango device: msenv:[AUTHORITY]/domain/family/member
* Attribute - an environment variable name (in either of the following formats <name>, <door>.<name>, <macro>.<name>, <door>.<macro>.<name>): msenv:DEVICE/variable 

**Some expected attribute URIs:**

* msenv://Foo:1000/macroserver/Foo/1/ScanDir
* msenv://macroserver/Foo/1/ScanDir
* msenv://Foo:1000/macroserver/Foo/1/door1.ScanDir
* msenv://Foo:1000/macroserver/Foo/1/ascan.ScanDir
* msenv://Foo:1000/macroserver/Foo/1/door1.ascan.ScanDir

Implementation
--------------

* Authority: 
    * Internally it should  use a proxy to a Tango Database.
    * The authority value should represent all the MS evnironments defined in the Tango Database
* Device: 
    * Internally it should use a proxy to a MS Environment Tango attribute.
    * It should subscribe to Tango change events of the MS Environment attribute and propagate them to the corresponding attributes. 
    * The device value should represent all the MS environment variables.
    * The device should notify an event when the environment variables are created, modified or deleted TODO: is it possible to have events of taurus Deviaces?
* Attribute:
    * Read of the attribute should always return the cached values from the latest event.
    * Write of the attribute should write the Enviroment Tango attribute using its parent object - MacroServer Device.
    * Write of the attribute should always write the specific variable e.g. ascan.ScanFile
    * Read of the attribute should fallback to the higher level of the variable in case the specific variable does not exists e. g. if the variable ascan.ScanFile is not defined, attribute readout should return value of the ascan variable.

TODO
```python
#!/usr/bin/python
import taurus, PyTango
def listener(s, t, v):
	if isinstance(v, PyTango.DeviceAttribute):
    	print "Event ", v.value

env = taurus.Attribute("macroserver/cfalcon/1/environment")
env.addListener(listener)
# Fist event (get all the environment)
Event  ('pickle', '\x80\x02}q\x00U\x03newq\x01}q\x02(U\x06ScanIDq\x03K0U\x08ScanFileq\x04U\x0bmyscans.tx ...)
# From spock change the ScanDirq
Event  ('pickle', '\x80\x02}q\x00U\x06changeq\x01}q\x02U\x07ScanDirq\x03U\x04/tmpq\x04ss.')
```

License
-------
Copyright (c) 2015 Carlos Falcon-Torres

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
2016-11-29: 
[mrosanes](https://github.com/sagiss) Migrate SEP14 from SF wiki to independent file, modify URL and fix formatting.
