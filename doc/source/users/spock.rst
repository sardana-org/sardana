
.. _sardana-spock:

=====
Spock
=====

*Spock* is the prefered :term:`CLI` for sardana. It is based on IPython_. Spock
automatically loads other IPython_ extensions like the ones for PyTango_ and
*pylab*. It as been extended in sardana to provide a customized interface for
executing macros and automatic access to sardana elements.

Spock tries to mimic SPEC_'s command line interface. Most SPEC_ commands are
available from spock console.

.. figure:: /_static/spock_snapshot01.png
    :height: 600
    :align: center
    
    Spock :term:`CLI` in action

Starting spock from the command line
------------------------------------

To start spock just type in the command line::

    marge@machine02:~$ spock

This will start spock with a "default profile" for the user your are logged
with. There may be many sardana servers running on your system so the first
time you start spock, it will ask you to which sardana system you want to
connect to by asking to which of the existing doors you want to use::

    marge@machine02:~$ spock
    Profile 'spockdoor' does not exist. Do you want to create one now ([y]/n)? 
    Available Door devices from homer:10000 :
    On Sardana LAB-01:
        LAB-01-D01 (running)
        LAB-01-D02 (running)
    On Sardana LAB-02:
        LAB-02-D01
    Please select a Door from the list? LAB-01-D01
    Storing ipy_profile_spockdoor.py in /home/marge/.ipython... [DONE]

.. note::
    If only one Door exists in the entire system, spock will automatically
    connect to that door thus avoiding the previous questions.

Afterward, spock :term:`CLI` will start normally:

.. sourcecode:: spock

    Spock 7.2.1 -- An interactive sardana client.

    help      -> Spock's help system.
    object?   -> Details about 'object'. ?object also works, ?? prints more.

    Spock's sardana extension 1.0 loaded with profile: spockdoor (linked to door 'LAB-01-D01')

    LAB-01-D01 [1]:
.. note::
    If you want to connect to another gate you need to create a new spock profile.

Starting spock with a custom profile
------------------------------------

spock allows each user to start a spock session with different configurations
(known in spock as *profiles*). All you have to do is start spock with 
the profile name as an option. 

If you use ipython version > 0.10 you can do it using **--profile** option::

    spock --profile=<profile name>
    
Example::

    marge@machine02:~$ spock --profile=D1
    
    
Otherwise (ipython version 0.10) you can do it using **-p** option::

    spock -p <profile name>
    
Example::

    marge@machine02:~$ spock -p D1

The first time a certain profile is used you will be asked to which door you
want to connect to (see previous chapter).

.. note::
  Spock profiles are stored by default in ``~/.ipython/profile_<profile_name>``
  directory. For more information please refer to the
  `IPython documentation <http://ipython.readthedocs.io/en/stable/config/intro.html#profiles>`_.

Spock IPython_ Primer
---------------------

As mentioned before, spock console is based on IPython_. Everything you can do
in IPython is available in spock. The IPython_ documentation provides excelent
tutorials, tips & tricks, cookbooks, videos, presentations and reference guide.
For comodity we summarize some of the most interesting IPython_ chapters here:

.. hlist::
    :columns: 2

    * `IPython web page <http://ipython.org/>`_
    * :ref:`tutorial`
    * :ref:`tips`
    * :ref:`command_line_options`

Executing macros
----------------

Executing sardana macros in spock is the most useful feature of spock. It is
very simple to execute a macro: just type the macro name followed by a space
separated list of parameters (if the macro has any parameters). For example,
one of the most used macros is the
:class:`~sardana.macroserver.macros.standard.wa` (stands for "where all") that
shows all current motor positions. To execute it just type:

.. sourcecode:: spock

    LAB-01-D01 [1]: wa
    
    Current Positions  (user, dial)

       Energy       Gap    Offset
     100.0000   43.0000  100.0000
     100.0000   43.0000  100.0000

(:term:`user` for :term:`user position` (number above); :term:`dial` for
:term:`dial position` (number below).)
   
A similar macro exists that only shows the desired motor positions
(:class:`~sardana.macroserver.macros.standard.wm`):

.. sourcecode:: spock

    LAB-01-D01 [1]: wm gap offset
                    Gap     Offset
    User                          
     High         500.0      100.0
     Current      100.0       43.0
     Low            5.0     -100.0
    Dial                          
     High         500.0      100.0
     Current      100.0       43.0
     Low            5.0     -100.0

To get the list of all existing macros use
:class:`~sardana.macroserver.macros.expert.lsmac`:

.. sourcecode:: spock

    LAB-01-D01 [1]: lsdef
                   Name        Module                                            Brief Description
    ------------------- ------------- ------------------------------------------------------------
                 a2scan         scans two-motor scan.     a2scan scans two motors, as specifi[...]
                 a2scan         scans three-motor scan .     a3scan scans three motors, as sp[...]
                  ascan         scans Do an absolute scan of the specified motor.     ascan s[...]
                defmeas        expert                               Create a new measurement group
                  fscan         scans N-dimensional scan along user defined paths.     The mo[...]
                    lsa         lists                                   Lists all existing objects
                    lsm         lists                                             Lists all motors
                  lsmac        expert                                            Lists all macros.
                     mv      standard                   Move motor(s) to the specified position(s)
                    mvr      standard            Move motor(s) relative to the current position(s)
                     wa      standard                                     Show all motor position.
                     wm      standard                   Show the position of the specified motors.
    <...>

Miscellaneous
~~~~~~~~~~~~~

    - :class:`~sardana.macroserver.macros.lists.lsm` shows the list of
      motors.
    - :class:`~sardana.macroserver.macros.lists.lsct` shows the list of
      counters.
    - :class:`~sardana.macroserver.macros.lists.lsmeas` shows the list of
      measurement groups
    - :class:`~sardana.macroserver.macros.lists.lsctrl` shows the list of
      controllers
    - :class:`~sardana.macroserver.macros.expert.sar_info` *object*
      displays detailed information about an element

.. _sardana-spock-stopping:

Stopping macros
---------------

Some macros may take a long time to execute. To stop a macro in the middle of
its execution type :kbd:`Control+c`. If the stopping process last too long,
you may trigger the aborting process with a second :kbd:`Control+c`.
Here be patient, further issuing of :kbd:`Control+c` may leave your macro
in an uncontrolled way. Use them only if you are sure that the aborting
process will not bring your system to a safe state.

Macros that move motors or acquire data from sensors will automatically stop all
motion and/or all acquisition.

While stopping and aborting macros Spock reports you what happens behind the
scene with informative messages:

.. sourcecode:: spock

    LAB-01-D01 [1]: ascan mot01 0 10 100 0.1
    Operation will be saved in /tmp/test.h5 (HDF5::NXscan from NXscanH5_FileRecorder)
    Scan #342 started at Wed Sep  9 23:01:14 2020. It will take at least 0:00:10.174246
                                           tg_test
     #Pt No    mot01      ct01     gct01    double_scalar     dt
       0         0        0.1     2.98023e-08      243.47     0.0967791
       1        0.1       0.1     5.91929e-08      243.47     0.239136
       2        0.2       0.1     1.1595e-07      243.47     0.384191
    ^C
    Ctrl-C received: Stopping...
    Stopping Motion(['mot01']) reserved by ascan
    Motion(['mot01']) stopped
    Stopping mntgrp_expconf reserved by ascan
    mntgrp_expconf stopped
    Operation saved in /tmp/test.h5 (HDF5::NXscan)
    Scan #342 ended at Wed Sep  9 23:01:15 2020, taking 0:00:01.055814. Dead time 33.7% (motion dead time 12.8%)
    Executing ascan.on_stop method...
    Stopping done!

Exiting spock
-------------

To exit spock type :kbd:`Control+d` or :samp:`exit()` inside a spock console.

.. _sardana-spock-gettinghelp:

Getting help
------------

spock not only knows all the macros the sardana server can run but it also
information about each macro parameters, result and documentation. Therefore it
can give you precise help on each macro. To get help about a certain macro just
type the macro name directly followed by a question mark('?'):

.. sourcecode:: spock

    LAB-01-D01 [1]: ascan?
    
    Syntax:
            ascan <motor> <start_pos> <final_pos> <nr_interv> <integ_time>
    
    Do an absolute scan of the specified motor.
        ascan scans one motor, as specified by motor. The motor starts at the
        position given by start_pos and ends at the position given by final_pos.
        The step size is (start_pos-final_pos)/nr_interv. The number of data points collected
        will be nr_interv+1. Count time is given by time which if positive,
        specifies seconds and if negative, specifies monitor counts. 
    
    Parameters:
            motor : (Motor) Motor to move
            start_pos : (Float) Scan start position
            final_pos : (Float) Scan final position
            nr_interv : (Integer) Number of scan intervals
            integ_time : (Float) Integration time
    
Moving motors
-------------

A single motor may be moved using the
:class:`~sardana.macroserver.macros.standard.mv` *motor* *position* macro.
Example:

.. sourcecode:: spock

    LAB-01-D01 [1]: mv gap 50

will move the *gap* motor to 50. The prompt only comes back after the motion as
finished.

Alternatively, you can have the motor position displayed on the screen as it is
moving by using the :class:`~sardana.macroserver.macros.standard.umv` macro
instead. To stop the motor(s) before they have finished moving, type
:kbd:`Control+c`.

You can use the :class:`~sardana.macroserver.macros.standard.mvr` *motor*
*relative_position* macro to move a motor relative to its current position:

.. sourcecode:: spock

    LAB-01-D01 [1]: mvr gap 2
    
will move *gap* by two user units.

Counting
--------

You can count using the :class:`~sardana.macroserver.macros.standard.ct` *value*
macro. Without arguments, this macro counts for one second using the active
measurement group set by the environment variable *ActiveMntGrp*.


.. sourcecode:: spock

    Door_lab-01_1 [1]: ct 1.6

    Wed Jul 11 11:47:55 2012

      ct01  =         1.6
      ct02  =         3.2
      ct03  =         4.8
      ct04  =         6.4
    
To see the list of available measurement groups type
:class:`~sardana.macroserver.macros.lists.lsmeas`. The active measuremnt group
is marked with an asterisk (*):

.. sourcecode:: spock

    Door_lab-01_1 [1]: lsmeas

      Active        Name   Timer Experim. channels                                          
     -------- ---------- ------- -----------------------------------------------------------
        *       mntgrp01    ct01 ct01, ct02, ct03, ct04                                     
                mntgrp21    ct04 ct04, pcII0, pcII02                                        
                mntgrp24    ct04 ct04, pcII0

to switch active measurement groups type
:class:`~sardana.macroserver.macros.env.senv` **ActiveMntGrp** *mg_name*.

You can also create, modify and select measurement groups using the
:ref:`expconf <expconf_ui>` command

Scanning
--------

Sardana provides a catalog of different standard scan macros. Absolute-position
motor scans such as :class:`~sardana.macroserver.macros.scan.ascan`,
:class:`~sardana.macroserver.macros.scan.a2scan` and
:class:`~sardana.macroserver.macros.scan.a3scan` move one, two or three motors
at a time. Relative-position motor scans are
:class:`~sardana.macroserver.macros.scan.dscan`,
:class:`~sardana.macroserver.macros.scan.d2scan` and
:class:`~sardana.macroserver.macros.scan.d3scan`. The relative-position scans
all return the motors to their starting positions after the last point. Two
motors can be scanned over a grid of points using the
:class:`~sardana.macroserver.macros.scan.mesh` scan. 

*Continuous* versions exist of many of the standard scan macros (e.g.
:class:`~sardana.macroserver.macros.scan.ascanc`,
:class:`~sardana.macroserver.macros.scan.d3scanc`,
:class:`~sardana.macroserver.macros.scan.meshc`,...). The continuous scans
differ from their standard counterparts (also known as *step* scans) in that
the data acquisition is done without stopping the motors. Continuous scans are
generally faster but less precise than step scans, and some details must be
considered (see :ref:`sardana-users-scan`).

As it happens with :class:`~sardana.macroserver.macros.standard.ct`, the scan
macros will also use the active measurement group to decide which experiment
channels will be involved in the operation.

Here is the output of performing an
:class:`~sardana.macroserver.macros.scan.ascan` of the gap in a slit:

.. sourcecode:: spock

    LAB-01-D01 [1]: ascan gap 0.9 1.1 20 1
    ScanDir is not defined. This operation will not be stored persistently. Use "senv ScanDir <abs directory>" to enable it
    Scan #4 started at Wed Jul 11 12:56:47 2012. It will take at least 0:00:21
     #Pt No    gap       ct01      ct02      ct03
      0        0.9          1       4604      8939
      1       0.91          1       5822      8820
      2       0.92          1       7254      9544
      3       0.93          1       9254      8789
      4       0.94          1      11265      8804
      5       0.95          1      13583      8909
      6       0.96          1      15938      8821
      7       0.97          1      18076      9110
      8       0.98          1      19638      8839
      9       0.99          1      20825      8950
     10          1          1      21135      8917
     11       1.01          1      20765      9013
     12       1.02          1      19687      9135
     13       1.03          1      18034      8836
     14       1.04          1      15876      8901
     15       1.05          1      13576      8933
     16       1.06          1      11328      9022
     17       1.07          1       9244      9205
     18       1.08          1       7348      8957
     19       1.09          1       5738      8801
     20        1.1          1       4575      8975
    Scan #4 ended at Wed Jul 11 12:57:18 2012, taking 0:00:31.656980 (dead time was 33.7%)



Scan storage
~~~~~~~~~~~~

As you can see, by default, the scan is not recorded into any file. To store
your scans in a file, you must set the environment variables **ScanDir** and
**ScanFile**:

.. sourcecode:: spock

    LAB-01-D01 [1]: senv ScanDir /tmp
    ScanDir = /tmp
    
    LAB-01-D01 [2]: senv ScanFile scans.h5
    ScanFile = scans.h5
    
Sardana will activate a proper recorder to store the scans persistently
(currently, *.h5* will store in `NeXus`_ format. All other extensions are
interpreted as `SPEC`_ format).

You can also store in multiples files by assigning the **ScanFile** with a list
of files:
    
.. sourcecode:: spock

    LAB-01-D01 [2]: senv ScanFile "['scans.h5', 'scans.dat']"
    ScanFile = ['scans.h5', 'scans.dat']

.. _sardana-spock-showscan:

Viewing scan data
~~~~~~~~~~~~~~~~~

You can show plots for the current scan (i.e. plotting the scan *online*) by
launching the :func:`showscan online <sardana.spock.magic.showscan>` command.

Sardana provides also a scan data viewer for scans which were stored in a `NeXus`_
file: :ref:`showscan_ui`. It can be launched using :func:`showscan <sardana.spock.magic.showscan>`
spock command. It accepts scan number as an argument, and will show the last scan
when invoked without arguments.

The history of scans is available through the
:class:`~sardana.macroserver.macros.scan.scanhist` macro:

.. sourcecode:: spock

    LAB-01-D01 [1]: scanhist
       #                           Title            Start time              End time        Stored
     --- ------------------------------- --------------------- --------------------- -------------
       1    dscan mot01 20.0 30.0 10 0.1   2012-07-03 10:35:30   2012-07-03 10:35:30   Not stored!
       3    dscan mot01 20.0 30.0 10 0.1   2012-07-03 10:36:38   2012-07-03 10:36:43   Not stored!
       4   ascan gap01 10.0 100.0 20 1.0              12:56:47              12:57:18   Not stored!
       5     ascan gap01 1.0 10.0 20 0.1              13:19:05              13:19:13      scans.h5

Accessing macro data
--------------------

The command :class:`~sardana.spock.magic.macrodata`  allows to retrieve the data of the last macro run in spock.
If this macro does not provide any data an error message is thrown.
Example accesing scan data:

.. sourcecode:: spock

   Door_1 [9]: ascan mot17 1 10 2 1
   ScanDir is not defined. This operation will not be stored persistently. Use "expconf" (or "senv ScanDir <abs directory>") to enable it
   Scan #2 started at Tue Feb 13 11:16:18 2018. It will take at least 0:00:05.048528
   #Pt No    mot17      ct17      ct19      ct20       dt
   0         1         1         3         4      0.865325
   1        5.5        1         3         4      2.51148    
   2         10        1         3         4      4.16662   
   Scan #2 ended at Tue Feb 13 11:16:24 2018, taking 0:00:05.201949. Dead time 42.3% (motion dead time 40.5%)         
   Door_1 [10]: r = %macrodata  
   Door_1 [11]: r[0].data.keys()   
   Result [11]:            
   ['point_nb',                     
   'timestamp',                
   'mot17',                       
   'haso111n:10000/expchan/ctctrl05/4', 
   'haso111n:10000/expchan/ctctrl05/1',  
   'haso111n:10000/expchan/ctctrl05/3'] 
   Door_1 [12]: r[0].data['point_nb']   
   Result [12]: 0  
   Door_1 [13]: r[0].data['mot17'] 
   Result [13]: 1.0  
   Door_1 [16]: r[0].data['haso111n:10000/expchan/ctctrl05/1']
   Result [16]: 1.0

.. |br| raw:: html

    <br>

.. _sardana-spock-viewoptions:

Changing appearance with View Options
-------------------------------------

The *View Options* allow the users to customize the output displayed by certain
macros. They are set by the macro :class:`~sardana.macroserver.macros.env.setvo`.
The macro :class:`~sardana.macroserver.macros.env.usetvo` returns the
*View Options* to the default value. And the macro
:class:`~sardana.macroserver.macros.env.lsvo` lists the current values.
       
Available *View Options*:

- **ShowDial**: Select if the :term:`dial` information of the motor should be
  displayed. |br| Default value ``False`` (no :term:`dial` but only
  :term:`user` information).
- **ShowCtrlAxis**: Select if the name of the controller the motor belongs to
  should be displayed. Default value ``False`` (no controller name).
- **PosFormat**: Set the number of decimal digits displayed in the motor
  position/limits. |br| Default value ``-1`` (all digits).
- **OutputBlock**: Set if the line information during scans is appended to the
  output or updated. |br| Default value ``False`` (lines are appended to the
  displayed output during the scan).
- **DescriptionLength**: Length (number of characters) of the macro
  description printed by ``lsdef`` macro. |br| Default value ``60``.

  
Editing macros
--------------

The command :class:`~sardana.spock.magic.edmac` allows to edit the macros
directly from spock. See :ref:`sardana-macros-howto` section.


Debugging problems
------------------

Spock provides some commands that help to debug or recognize the errors in
case a macro fails when being executed.

    - :class:`~sardana.spock.magic.www` prints the error message from the
      last macro execution

    - :class:`~sardana.spock.magic.debug` used with ``on`` as parameter
      activates the print out of the debug messages during macro execution.
      Set it to ``off`` to deactivate it.

    - :class:`~sardana.spock.magic.post_mortem` prints the current logger
      messages. If no argument is specified it reads the ``debug`` stream.
      Valid values are ``output``, ``critical``, ``error``, ``warning``,
      ``info``, ``debug`` and ``result``.

.. _sardana-spock-syntax:

Spock syntax
------------

*Spock syntax* is used to execute macros. It is based on space
separated list of parameter values. If the string parameter values contain
spaces itself these **must** be enclosed in quotes, either single quotes
``''`` or double quotes ``""``.

The spock syntax was extended with the use of square brackets ``[]`` for
macros which define
:ref:`repeat parameters <sardana-macro-repeat-parameters>` as arguments.
Repeat parameter values must be enclosed in square brackets. If the repeat
parameter is composed from more than one internal parameter its every
repetition must be enclosed in another square brackets as well.

For example, the ``move_with_timeout`` macro::

    class move_with_timeout(Macro):
        """Execute move with a timeout"""

        param_def = [
            ['m_p_pair',
             [['motor', Type.Motor, None, 'Motor to move'],
              ['pos',  Type.Float, None, 'Position to move to']],
             None, 'List of motor/position pairs'],
            ['timeout', Type.Float, None, 'Timeout value']
        ]

        def run(self, *args, **kwargs):
            pass

Must use the square brackets for the ``m_p_pair`` parameter and its
repeats:

.. sourcecode:: spock

   Door_1 [1]: move_with_timeout [[th 8.4] [tth 16.8]] 50

However for the commodity reasons the square brackets may be skipped. The
following examples explain in which cases.

Repeat parameter is the last one
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When the repeat parameter is the last one in the parameters definition
both square brackets (for the repeat parameter and for the repetition) may
be skipped.

For example, the ``move`` macro::

    class move(Macro):
        """Execute move"""

        param_def = [
            ['m_p_pair',
             [['motor', Type.Motor, None, 'Motor to move'],
              ['pos',  Type.Float, None, 'Position to move to']],
             None, 'List of motor/position pairs']
        ]

        def run(self, *args, **kwargs):
            pass

May skip the square brackets for the ``m_p_pair`` parameter and its
repeats:

.. sourcecode:: spock

   Door_1 [1]: move th 8.4 tth 16.8

This is equivalent to:

.. sourcecode:: spock

   Door_1 [1]: move [[th 8.4] [tth 16.8]]

Repeat parameter has only one internal parameter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When the repeat parameter contains only one internal parameter the square
brackets for the repetition **must** be skipped.

For example, the ``power_motor`` macro::

    class power_motor(Macro):
        """Power on/off motor(s)"""

        param_def = [
            ['motor_list', [['motor', Type.Motor, None, 'motor name']],
                None, 'List of motors'],
            ['power_on', Type.Boolean, None, 'motor power state']
        ]

        def run(self, *args, **kwargs):
            pass

Must use the square brackets for the ``motor_list`` parameter but not for
its repeats:

.. sourcecode:: spock

   Door_1 [1]: power_motor [th tth] True

Repeat parameter has only one internal parameter and only one repetition value
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When the repeat parameter contains only one internal parameter and you
would like to pass only one repetition value then the square brackets for
the repeat parameter may be skipped as well resulting in no square brackets
being used.

This assumes the ``power_motor`` macro from the previous example.
The following two macro executions are equivalent:

.. sourcecode:: spock

    Door_1 [1]: power_motor th True
    Door_1 [2]: power_motor [th] True

A set of macro examples defining complex repeat parameters can be found in
:ref:`sardana-devel-macro-parameter-examples`.
You can see the invocation example for each of these macros in its docstring.


Using spock as a Python_ console
--------------------------------

You can write any Python_ code inside a spock console since spock uses IPython_
as a command line interpreter. For example, the following will work inside a
spock console:

.. sourcecode:: spock

    LAB-01-D01 [1]: def f():
               ...:     print("Hello, World!")
               ...:
               ...:
    
    LAB-01-D01 [2]: f()
    Hello, World!
    

Using spock as a Tango_ console
-------------------------------

As mentioned in the beginning of this chapter, the sardana spock automatically
activates the PyTango_ 's ipython console extension [#]_. Therefore all Tango_
features are automatically available on the sardana spock console. For example,
creating a :class:`tango.DeviceProxy` will work inside the sardana spock
console:

.. sourcecode:: spock

    LAB-01-D01 [1]: tgtest = Device("sys/tg_test/1")
    
    LAB-01-D01 [2]: print(tgtest.state())
    RUNNING

.. rubric:: Footnotes

.. [#] The PyTango_ ipython documentation can be found here: ITango_

.. _ALBA: http://www.cells.es/
.. _ANKA: http://http://ankaweb.fzk.de/
.. _ELETTRA: http://http://www.elettra.trieste.it/
.. _ESRF: http://www.esrf.eu/
.. _FRMII: http://www.frm2.tum.de/en/index.html
.. _HASYLAB: http://hasylab.desy.de/
.. _MAX-lab: http://www.maxlab.lu.se/maxlab/max4/index.html
.. _SOLEIL: http://www.synchrotron-soleil.fr/


.. _Tango: http://www.tango-controls.org/
.. _PyTango: http://packages.python.org/PyTango/
.. _ITango: https://pythonhosted.org/itango/
.. _Taurus: http://packages.python.org/taurus/
.. _QTango: http://www.tango-controls.org/download/index_html#qtango3
.. _`PyTango installation steps`: http://packages.python.org/PyTango/start.html#getting-started
.. _Qt: http://qt.nokia.com/products/
.. _PyQt: http://www.riverbankcomputing.co.uk/software/pyqt/
.. _PyQwt: http://pyqwt.sourceforge.net/
.. _Python: http://www.python.org/
.. _IPython: http://ipython.org/
.. _ATK: http://www.tango-controls.org/Documents/gui/atk/tango-application-toolkit
.. _Qub: http://www.blissgarden.org/projects/qub/
.. _numpy: http://numpy.scipy.org/
.. _SPEC: http://www.certif.com/
.. _EPICS: http://www.aps.anl.gov/epics/
.. _NeXus: http://www.nexusformat.org/
