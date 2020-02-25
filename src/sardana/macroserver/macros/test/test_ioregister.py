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

"""Tests for ioregister macros"""

import unittest
from sardana.macroserver.macros.test import RunMacroTestCase, testRun, getIORs

IOR_NAME = getIORs()[0]


@testRun(macro_name="write_ioreg", macro_params=[IOR_NAME, "1"],
         wait_timeout=1)
@testRun(macro_name="read_ioreg", macro_params=[IOR_NAME], wait_timeout=1)
class IORegisterTest(RunMacroTestCase, unittest.TestCase):
    """Test case for ioregister macros
    """
    pass
