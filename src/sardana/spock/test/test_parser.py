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

"""Tests for parser utilities."""

from taurus.external import unittest
from taurus.test import insertTest
from sardana.spock.parser import ParamParser


@insertTest(helper_name="parse",
            params_str='ScanFile "[\\"file.nxs\\", \\"file.dat\\"]"',
            params=["ScanFile", '["file.nxs", "file.dat"]'])
@insertTest(helper_name="parse", params_str="[1 [] 3]",
            params=[["1", [], "3"]])
@insertTest(helper_name="parse",
            params_str="2 3 ['Hello world!' 'How are you?']",
            params=["2", "3", ["Hello world!", "How are you?"]])
@insertTest(helper_name="parse", params_str="ScanFile file.dat",
            params=["ScanFile", "file.dat"])
@insertTest(helper_name="parse", params_str="'2 3'", params=["2 3"])
@insertTest(helper_name="parse", params_str='"2 3"', params=["2 3"])
@insertTest(helper_name="parse", params_str="[[mot01 3][mot02 5]] ct01 999",
            params=[[["mot01", "3"], ["mot02", "5"]], "ct01", "999"])
@insertTest(helper_name="parse", params_str="[[2 3][4 5]]",
            params=[[["2", "3"], ["4", "5"]]])
@insertTest(helper_name="parse", params_str="1 [2 3]",
            params=["1", ["2", "3"]])
@insertTest(helper_name="parse", params_str="2 3", params=["2", "3"])
class ParamParserTestCase(unittest.TestCase):
    """Unit tests for ParamParser class."""

    def parse(self, params_str, params):
        """Helper method to test parameters parsing. To be used with insertTest
        decorator.
        """
        p = ParamParser()
        result = p.parse(params_str)
        msg = "Parsing failed (result: %r; expected: %r)" %\
            (result, params)
        self.assertListEqual(result, params, msg)
