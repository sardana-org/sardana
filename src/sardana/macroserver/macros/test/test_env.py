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

"""Tests for environment macros"""

import unittest
from sardana.macroserver.macros.test import RunMacroTestCase, testRun


@testRun
class DumpenvTest(RunMacroTestCase, unittest.TestCase):
    """Test case for dumpenv macro
    """
    macro_name = "dumpenv"


@testRun
class LsvoTest(RunMacroTestCase, unittest.TestCase):
    """Test case for lsvo macro
    """
    macro_name = "lsvo"


@testRun(macro_params=["PosFormat", "3"])
class SetvoTest(RunMacroTestCase, unittest.TestCase):
    """Test case for setvo macro
    """
    macro_name = "setvo"


@testRun(macro_params=["PosFormat"])
class UsetvoTest(RunMacroTestCase, unittest.TestCase):
    """Test case for usetvo macro
    """
    macro_name = "usetvo"


@testRun
@testRun(macro_params=["ascan"])
@testRun(macro_params=["ascan", "dscan"])
class LsenvTest(RunMacroTestCase, unittest.TestCase):
    """Test case for lsvo macro
    """
    macro_name = "lsenv"


@testRun(macro_params=["MyEnvVar", "test.dat"])
class SenvTest(RunMacroTestCase, unittest.TestCase):
    """Test case for senv macro
    """
    macro_name = "senv"


@testRun(macro_params=["MyEnvVar"])
class UsenvTest(RunMacroTestCase, unittest.TestCase):
    """Test case for usenv macro
    """
    macro_name = "usenv"
