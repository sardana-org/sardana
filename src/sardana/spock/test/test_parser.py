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


# @insertTest(helper_name="parse",
#             params_str='ScanFile "[\\"file.nxs\\", \\"file.dat\\"]"',
#             params=["ScanFile", '["file.nxs", "file.dat"]'])
# @insertTest(helper_name="parse", params_str="[1 [] 3]",
#             params=[["1", [], "3"]])
# @insertTest(helper_name="parse",
#             params_str="2 3 ['Hello world!' 'How are you?']",
#             params=["2", "3", ["Hello world!", "How are you?"]])
# @insertTest(helper_name="parse", params_str="ScanFile file.dat",
#             params=["ScanFile", "file.dat"])
# @insertTest(helper_name="parse", params_str="'2 3'", params=["2 3"])
# @insertTest(helper_name="parse", params_str='"2 3"', params=["2 3"])
# @insertTest(helper_name="parse", params_str="[[mot01 3][mot02 5]] ct01 999",
#             params=[[["mot01", "3"], ["mot02", "5"]], "ct01", "999"])
# @insertTest(helper_name="parse", params_str="[[2 3][4 5]]",
#             params=[[["2", "3"], ["4", "5"]]])
# @insertTest(helper_name="parse", params_str="1 [2 3]",
#             params=["1", ["2", "3"]])
# @insertTest(helper_name="parse", params_str="2 3", params=["2", "3"])
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


pt0_params_def = []

pt1d_params_def = [
    {
        "default_value": 99,
        "description": "some bloody float",
        "max": None,
        "min": 1,
        "name": "value",
        "type": "Float"
    }
]

pt3_params_def = [
    {
        "default_value": None,
        "description": "List of values",
        "max": None,
        "min": 1,
        "name": "numb_list",
        "type": [
            {
                "default_value": None,
                "description": "value",
                "max": None,
                "min": 1,
                "name": "position",
                "type": "Float"
            }
        ]
    }
]

pt3d_params_def = [
    {
        "default_value": None,
        "description": "List of values",
        "max": None,
        "min": 1,
        "name": "numb_list",
        "type": [
            {
                "default_value": 21,
                "description": "value",
                "max": None,
                "min": 1,
                "name": "position",
                "type": "Float"
            }
        ]
    }
]

pt5_params_def = [
    {
        "default_value": None,
        "description": "Motor to move",
        "max": None,
        "min": 1,
        "name": "motor",
        "type": "Motor"
    },
    {
        "default_value": None,
        "description": "List of values",
        "max": None,
        "min": 1,
        "name": "numb_list",
        "type": [
            {
                "default_value": None,
                "description": "value",
                "max": None,
                "min": 1,
                "name": "position",
                "type": "Float"
            }
        ]
    }
]

pt7_params_def = [
    {
        "default_value": None,
        "description": "List of motor/position pairs",
        "max": None,
        "min": 1,
        "name": "m_p_pair",
        "type": [
            {
                "default_value": None,
                "description": "Motor to move",
                "max": None,
                "min": 1,
                "name": "motor",
                "type": "Motor"
            },
            {
                "default_value": None,
                "description": "Position to move to",
                "max": None,
                "min": 1,
                "name": "position",
                "type": "Float"
            }
        ]
    }
]

pt10_params_def = [
    {
        "default_value": None,
        "description": "List of values",
        "max": None,
        "min": 1,
        "name": "numb_list",
        "type": [
            {
                "default_value": None,
                "description": "value",
                "max": None,
                "min": 1,
                "name": "pos",
                "type": "Float"
            }
        ]
    },
    {
        "default_value": None,
        "description": "Motor to move",
        "max": None,
        "min": 1,
        "name": "motor",
        "type": "Motor"
    },
]

pt13_params_def = [
    {
        "default_value": None,
        "description": "Motor groups",
        "max": None,
        "min": 1,
        "name": "motor_group_list",
        "type": [
            {
                "default_value": None,
                "description": "List of motors",
                "max": None,
                "min": 1,
                "name": "motor list",
                "type": [
                    {
                        "default_value": None,
                        "description": "Motor to move",
                        "max": None,
                        "min": 1,
                        "name": "motor",
                        "type": "Motor"
                    }
                ]
            }
        ]
    }
]

pt14_params_def = [
    {
        "default_value": None,
        "description": "Motor groups",
        "max": None,
        "min": 1,
        "name": "motor_group_list",
        "type": [
            {
                "default_value": None,
                "description": "List of motors",
                "max": None,
                "min": 1,
                "name": "motor list",
                "type": [
                    {
                        "default_value": None,
                        "description": "Motor to move",
                        "max": None,
                        "min": 1,
                        "name": "motor",
                        "type": "Motor"
                    }
                ]
            },
            {
                "default_value": None,
                "description": "Number",
                "max": None,
                "min": 1,
                "name": "float",
                "type": "Float"
            }
        ]
    }
]


@insertTest(helper_name="parse", params_def=pt0_params_def,
            params_str="", params=[])
@insertTest(helper_name="parse", params_def=pt1d_params_def,
            params_str="1", params=["1"])
@insertTest(helper_name="parse", params_def=pt1d_params_def,
            params_str="", params=[])
@insertTest(helper_name="parse", params_def=pt3_params_def,
            params_str="1 34 15", params=[["1", "34", "15"]])
@insertTest(helper_name="parse", params_def=pt3_params_def,
            params_str="[1 34 15]", params=[["1", "34", "15"]])
@insertTest(helper_name="parse", params_def=pt3d_params_def,
            params_str="1 34 15", params=[["1", "34", "15"]])
@insertTest(helper_name="parse", params_def=pt3d_params_def,
            params_str="[1 34 15]", params=[["1", "34", "15"]])
@insertTest(helper_name="parse", params_def=pt3d_params_def,
            params_str="[1 [] 15]", params=[["1", [], "15"]])
@insertTest(helper_name="parse", params_def=pt5_params_def,
            params_str="mot1 1 3", params=["mot1", ["1", "3"]])
@insertTest(helper_name="parse", params_def=pt5_params_def,
            params_str="mot1 [1 3]", params=["mot1", ["1", "3"]])
@insertTest(helper_name="parse", params_def=pt7_params_def,
            params_str="mot1 1 mot2 3",
            params=[[["mot1", "1"], ["mot2", "3"]]])
@insertTest(helper_name="parse", params_def=pt7_params_def,
            params_str="[[mot1 1] [mot2 3]]",
            params=[[["mot1", "1"], ["mot2", "3"]]])
@insertTest(helper_name="parse", params_def=pt10_params_def,
            params_str="[1 3] mot1", params=[["1", "3"], "mot1"])
@insertTest(helper_name="parse", params_def=pt10_params_def,
            params_str="1 mot1", params=[["1"], "mot1"])
@insertTest(helper_name="parse", params_def=pt13_params_def,
            params_str="[[mot1 mot2] [mot3 mot4]]",
            params=[[["mot1", "mot2"], ["mot3", "mot4"]]])
@insertTest(helper_name="parse", params_def=pt14_params_def,
            params_str="[[[mot1 mot2] 3] [[mot3] 5]]",
            params=[[[["mot1", "mot2"], "3"], [["mot3"], "5"]]])
class ParamParserWithDefTestCase(unittest.TestCase):
    """Unit tests for ParamParser class initialized with parameters
    definition.
    """
    def parse(self, params_def, params_str, params):
        p = ParamParser(params_def)
        result = p.parse(params_str)
        msg = "Parsing failed (result: %r; expected: %r)" % \
              (result, params)
        self.assertListEqual(result, params, msg)
