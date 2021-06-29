
.. currentmodule:: sardana.test.

.. _sardana-test-run-commands:

===========================
Run tests from command line
===========================

Run test suite
--------------

We recommend using pytest to run Sardana tests. Please refer to
`pytest documentation <https://docs.pytest.org/en/latest/usage.html>`_
on how to execute tests.

.. note::
  Currently the majority of the Sardana tests are written using unittest.
  We plan to gradually migrate them to pytest.

.. _sardana-test-sar_demo:

sar_demo test environment
-------------------------

Some of the Sardana tests e.g. the ones that test the macros, require a running Sardana
instance with the sar_demo macro executed previously. By default the tests will try to
connect to the `door/demo1/1` door in order to run the macros there. The default door
name can be changed with the `sardana.sardanacustomsettings.UNITTEST_DOOR_NAME`
module.

