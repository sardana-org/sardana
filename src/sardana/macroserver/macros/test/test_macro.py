import os

from taurus.external import unittest

from sardana.macroserver.macros.test import RunMacroTestCase, testRun
from sardana.tango.macroserver.test import BaseMacroServerTestCase


@testRun(macro_name="runMacro")
@testRun(macro_name="createMacro")
@testRun(macro_name="execMacro")
class MacroTest(BaseMacroServerTestCase, RunMacroTestCase, unittest.TestCase):

    def setUp(self):
        macros_test_path = '../../test/res/macros'
        source = os.path.join(os.path.dirname(__file__), macros_test_path)
        path = os.path.abspath(source)
        properties = {'MacroPath': [path]}
        unittest.TestCase.setUp(self)
        BaseMacroServerTestCase.setUp(self, properties)
        RunMacroTestCase.setUp(self)

    def tearDown(self):
        BaseMacroServerTestCase.tearDown(self)
        RunMacroTestCase.tearDown(self)
        unittest.TestCase.tearDown(self)
