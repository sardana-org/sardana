#!/usr/bin/env python

##############################################################################
##
## This file is part of Sardana
##
## http://www.sardana-controls.org/
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
##
## Sardana is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## Sardana is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################

"""Tests for standard macros"""

from taurus.external import unittest
from sardana.macroserver.macros.test import RunMacroTestCase, testRun,\
    getMotors

MOT_NAME1, MOT_NAME2 = getMotors()[:2]

#TODO: these tests randomly causes segfaults. fix it!
# @testRun(macro_name="wu", wait_timeout=1)
# @testRun(macro_name="wa", wait_timeout=1)
# @testRun(macro_name="wa", macro_params=["mot.*"], wait_timeout=1)
# @testRun(macro_name="pwa", wait_timeout=1)
# @testRun(macro_name="wm", macro_params=[MOT_NAME1], wait_timeout=1)
# @testRun(macro_name="wm", macro_params=[MOT_NAME1, MOT_NAME2], wait_timeout=1)
# @testRun(macro_name="wum", macro_params=[MOT_NAME1], wait_timeout=1)
# @testRun(macro_name="wum", macro_params=[MOT_NAME1, MOT_NAME2], wait_timeout=1)
# @testRun(macro_name="pwm", macro_params=[MOT_NAME1], wait_timeout=1)
# @testRun(macro_name="pwm", macro_params=[MOT_NAME1, MOT_NAME2], wait_timeout=1)
# class WhereTest(RunMacroTestCase, unittest.TestCase):
#     """Test case for where macros
#     """
#     pass

@testRun(macro_name="set_lim", macro_params=[MOT_NAME1, "-100", "100"],
         wait_timeout=1)
@testRun(macro_name="set_lm", macro_params=[MOT_NAME1, "-1000", "1000"],
         wait_timeout=1)
class LimTest(RunMacroTestCase, unittest.TestCase):
    """Test case for limit macros
    """
    pass


@testRun(macro_name="set_pos", macro_params=[MOT_NAME1, "0"],
         wait_timeout=1)
@testRun(macro_name="set_user_pos", macro_params=[MOT_NAME1, "0"],
         wait_timeout=1)
class PosTest(RunMacroTestCase, unittest.TestCase):
    """Test case for position macros
    """
    pass


class MoveTest(RunMacroTestCase, unittest.TestCase):
    """Test case for position macros
    """
    def test_move(self):
        self.macro_runs("set_user_pos", macro_params=[MOT_NAME1, "0"],
                        wait_timeout=1)
        self.macro_runs("mv", macro_params=[MOT_NAME1, "1"], wait_timeout=3)
        self.macro_runs("umv", macro_params=[MOT_NAME1, "0"], wait_timeout=3)
        self.macro_runs("mvr", macro_params=[MOT_NAME1, "1"], wait_timeout=3)
        self.macro_runs("umvr", macro_params=[MOT_NAME1, "-1"], wait_timeout=3)


@testRun(macro_params=[MOT_NAME1])
class MstateTest(RunMacroTestCase, unittest.TestCase):

    macro_name = "mstate"


@testRun(macro_params=["blabla"])
class ReportTest(RunMacroTestCase, unittest.TestCase):

    macro_name = "report"
