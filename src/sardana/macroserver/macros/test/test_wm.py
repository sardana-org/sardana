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

"""Tests for wm macros"""

from taurus.external import unittest
from sardana.macroserver.macros.test import (RunMacroTestCase, testRun,
                                             getMotors)

# get handy motor names from sardemo
_m1, _m2 = getMotors()[:2]


class WBase(RunMacroTestCase):

    """Base class for testing macros used to read position.
    """

    def macro_runs(self, **kw):
        """Testing the execution of the 'wm' macro and verify that the log
        'output' exists.
        """
        RunMacroTestCase.macro_runs(self, **kw)
        self.logOutput = self.macro_executor.getLog("output")
        msg = "wm macro did not return any data."
        self.assertTrue(len(self.logOutput) > 0, msg)


@testRun(macro_params=[_m1], wait_timeout=5.0)
class WmTest(WBase, unittest.TestCase):

    """Test of wm macro. It verifies that the macro 'wm' can be executed.
    It inherits from WmBase and from unittest.TestCase.
    It tests the execution of the 'wm' macro and verifies that the log 'output'
    exists.
    """
    macro_name = "wm"
