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

"""Tests for ct macros"""

from taurus.external import unittest
from sardana.macroserver.macros.test import RunStopMacroTestCase
from sardana.macroserver.macros.test import testRun
from sardana.macroserver.macros.test import testStop


@testRun(macro_name="ct", macro_params=['.1'], wait_timeout=2.5)
@testRun(macro_name="ct", macro_params=['.3'], wait_timeout=2.5)
@testStop(macro_name="ct", macro_params=['1'], stop_delay=.1, wait_timeout=3.5)
# TODO: uncomment these test when bug-474 is fixed:
# https://sourceforge.net/p/sardana/tickets/474/
#@testRun(macro_name="uct", macro_params=['.1'], wait_timeout=2)
#@testRun(macro_name="uct", macro_params=['.3'], wait_timeout=2)
#@testStop(macro_name="uct", macro_params=['1'], stop_delay=.1, wait_timeout=3)
class CtTest(RunStopMacroTestCase, unittest.TestCase):

    """Test of ct macro. It verifies that macro ct can be executed.
    It inherits from RunStopMacroTestCase and from unittest.TestCase.
    It tests two executions of the ct macro with two different input
    parameters.
    Then it does another execution and it tests if the execution can be
    aborted.
    """
    pass
