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

import unittest

from sardana.macroserver.macros.test import RunMacroTestCase, testRun
from sardana.tango.macroserver.test import BaseMacroServerTestCase
from sardana.tango.pool.test.test_measurementgroup import MeasSarTestTestCase
from sardana.macroserver.macros.test.test_scanct import mg_config4


@testRun(macro_name="lsgh", wait_timeout=1)
@testRun(macro_name="defgh", macro_params=["lsm", "pre-acq"], wait_timeout=1)
@testRun(macro_name="defgh", macro_params=["lsm mot.*", "pre-acq"],
         wait_timeout=1)
@testRun(macro_name="udefgh", wait_timeout=1)
class GeneralHooksMacrosTest(RunMacroTestCase, unittest.TestCase):
    pass


class GeneralHooksTest(MeasSarTestTestCase, BaseMacroServerTestCase,
                       RunMacroTestCase, unittest.TestCase):

    def setUp(self):
        MeasSarTestTestCase.setUp(self)
        BaseMacroServerTestCase.setUp(self)
        RunMacroTestCase.setUp(self)
        unittest.TestCase.setUp(self)

    def create_meas(self, config):
        MeasSarTestTestCase.create_meas(self, config)
        self.macro_executor.run(macro_name='senv',
                                macro_params=['ActiveMntGrp', '_test_mg_1'],
                                sync=True, timeout=1.)

    def test_gh(self):
        self.macro_runs(macro_name="defgh", macro_params=["lsm", "pre-acq"],
                        wait_timeout=1)
        self.create_meas(mg_config4)
        self.macro_runs(macro_name="ct", macro_params=[".1"], wait_timeout=1)
        self.macro_runs(macro_name="udefgh", macro_params=["lsm", "pre-acq"],
                        wait_timeout=1)

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        RunMacroTestCase.tearDown(self)
        BaseMacroServerTestCase.tearDown(self)
        MeasSarTestTestCase.tearDown(self)
