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

from taurus.external import unittest

from sardana.macroserver.macros.test import RunMacroTestCase, testRun
from sardana.tango.macroserver.test import BaseMacroServerTestCase


@testRun(macro_name="lsgh", wait_timeout=1)
@testRun(macro_name="defgh", macro_params=["lsm", "pre-acq"], wait_timeout=1)
@testRun(macro_name="defgh", macro_params=["lsm mot.*", "pre-acq"],
         wait_timeout=1)
@testRun(macro_name="udefgh", wait_timeout=1)
class GeneralHooksTest(BaseMacroServerTestCase, RunMacroTestCase,
                  unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        BaseMacroServerTestCase.setUp(self)
        RunMacroTestCase.setUp(self)

    def test_gh(self):
        self.macro_runs(macro_name="defgh", macro_params=["lsm", "pre-acq"],
                        wait_timeout=1)
        self.macro_runs(macro_name="ct", macro_params=[".1"], wait_timeout=1)
        self.macro_runs(macro_name="udefgh", macro_params=["lsm", "pre-acq"],
                        wait_timeout=1)

    def tearDown(self):
        BaseMacroServerTestCase.tearDown(self)
        RunMacroTestCase.tearDown(self)
        unittest.TestCase.tearDown(self)
