#!/usr/bin/env python

##############################################################################
##
# This file is part of Sardana
##
# http://www.sardana-controls.org/
##
# Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
##
# Sardana is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
##
# Sardana is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
##
# You should have received a copy of the GNU Lesser General Public License
# along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################

import os

import unittest

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
        RunMacroTestCase.tearDown(self)
        BaseMacroServerTestCase.tearDown(self)
        unittest.TestCase.tearDown(self)
