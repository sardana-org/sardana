
.. currentmodule:: sardana.test.

.. _sardana-test-run-commands:

===========================
Run tests from command line
===========================

Run test suite
--------------

Running the Sardana test suite from command line can be done in two
different ways:

1) Sardana tests can be executed using the `setuptools` test command prior to
   the installation by executing the following command from within the sardana
   project directory:
   
       python setup.py test

   This will execute only a subset of all the sardana tests - the unit test suite.
   The functional tests, that require the :ref:`sardana-test-sar_demo`, are
   excluded on purpose.

2) The complete Sardana test suite, that includes the unit and the functional tests
   can be executed only after the Sardana installation by executing the
   `sardanatestsuite` script.

Run a single test
-----------------

Executing a single test from command line is done by doing:

       python -m unittest test_name

Where test_name is the test module that has to be run.

That can be done with more verbosity by indicating the option -v.

       python -m unittest -v test_name 

.. _sardana-test-sar_demo:

sar_demo test environment
-------------------------

Some of the Sardana tests e.g. the ones that test the macros, require a running Sardana
instance with the sar_demo macro executed previosly. By default the tests will try to
connect to the `door/demo1/1` door in order to run the macros there. The default door
name can be changed in the `sardanacustomsettings` module.

