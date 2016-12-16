
.. currentmodule:: sardana.test.

.. _sardana-test-run-commands:


===========================
Run tests from command line
===========================


Run the whole Sardana test suite
--------------------------------

Running the whole Sardana test suite from command line can be done in three 
different ways: 

1) Executing sardanatestsuite
    By executing the script *sardanatestsuite*
    (this script is made available after sardana installation).

2) Explicitly executing testsuite.py
    By going to the Sardana directory:
    <sardana_root>/src/sardana/test/.

    And executing:
    *python testsuite.py*

3) Using setuptools
    By going to the code root directory:
    <sardana_root>

    and executing:
    *python setup.py test*

    *'python setup.py test'* must allow to be executed before sardana 
    installation. For this reason it only executes the actual unittests. 
    Macro tests are not executed because they require sar_demo environment 
    which is not still ready before sardana installation.

 

Run a single test
-----------------

Executing a single test from command line is done by doing:
    python -m unittest test_name

    Where test_name is the test module that has to be run.

That can be done with more verbosity by indicating the option -v.
    python -m unittest -v test_name 


