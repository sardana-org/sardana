from sardana.tango.macroserver.test import BaseMacroServerTestCase
from sardana.macroserver.macros.test import RunMacroTestCase, testRun
from taurus.external import unittest
import os

@testRun(macro_name="runMacro")
@testRun(macro_name="createMacro")
@testRun(macro_name="execMacro")
class MacroTest(BaseMacroServerTestCase, RunMacroTestCase, unittest.TestCase):

    def setUp(self):
        macros_test_path = '../../test/res/macros'
        path = os.path.abspath(os.path.join(os.path.dirname( __file__ ),
                                           macros_test_path))
        environment = {'MacroPath': [path]}
        unittest.TestCase.setUp(self)
        BaseMacroServerTestCase.setUp(self, properties=environment)
        RunMacroTestCase.setUp(self)


    def tearDown(self):
        BaseMacroServerTestCase.tearDown(self)
        RunMacroTestCase.tearDown(self)
        unittest.TestCase.tearDown(self)

