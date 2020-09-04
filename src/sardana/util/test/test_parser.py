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

import unittest
from taurus.test import insertTest
from sardana.util.parser import ParamParser


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

pt2_params_def = [
    {
        "default_value": None,
        "description": "some bloody motor",
        "max": None,
        "min": 1,
        "name": "motor",
        "type": "Motor"
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

pt4_params_def = [
    {
        "default_value": None,
        "description": "List of motors",
        "max": None,
        "min": 1,
        "name": "motor_list",
        "type": [
            {
                "default_value": None,
                "description": "motor name",
                "max": None,
                "min": 1,
                "name": "motor",
                "type": "Motor"
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
                "name": "pos",
                "type": "Float"
            }
        ]
    }
]

pt6_params_def = [
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
                "name": "pos",
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

pt7d1_params_def = [
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
                "default_value": 2,
                "description": "Position to move to",
                "max": None,
                "min": 1,
                "name": "pos",
                "type": "Float"
            }
        ]
    }
]

pt7d2_params_def = [
    {
        "default_value": None,
        "description": "List of motor/position pairs",
        "max": None,
        "min": 1,
        "name": "m_p_pair",
        "type": [
            {
                "default_value": 'mot1',
                "description": "Motor to move",
                "max": None,
                "min": 1,
                "name": "motor",
                "type": "Motor"
            },
            {
                "default_value": 2,
                "description": "Position to move to",
                "max": None,
                "min": 1,
                "name": "pos",
                "type": "Float"
            }
        ]
    }
]

pt8_params_def = [
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
                "max": 2,
                "min": 1,
                "name": "pos",
                "type": "Float"
            }
        ]
    }
]

pt9_params_def = [
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
                "max": 2,
                "min": 1,
                "name": "pos",
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

pt11_params_def = [

    {
        "default_value": None,
        "description": "Counter to count",
        "max": None,
        "min": 1,
        "name": "counter",
        "type": "ExpChannel"
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
                "name": "pos",
                "type": "Float"
            },
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

pt12_params_def = [

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
            },
        ]
    },
    {
        "default_value": None,
        "description": "List of Motors",
        "max": None,
        "min": 1,
        "name": "motor_list",
        "type": [
            {
                "default_value": 'mot1',
                "description": "Motor to move",
                "max": None,
                "min": 1,
                "name": "motor",
                "type": "Motor"
            },
        ]
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
                "name": "motor_list",
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

pt14d_params_def = [
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
                "name": "motor_list",
                "type": [
                    {
                        "default_value": "mot1",
                        "description": "Motor to move",
                        "max": None,
                        "min": 1,
                        "name": "motor",
                        "type": "Motor"
                    }
                ]
            },
            {
                "default_value": 33,
                "description": "Number",
                "max": None,
                "min": 1,
                "name": "float",
                "type": "Float"
            }
        ]
    }
]

extra1_params_def = [
    {
        "default_value": None,
        "description": "Parameter",
        "max": None,
        "min": 1,
        "name": "param",
        "type": "String"
    },
    {
        "default_value": None,
        "description": "List of Scan files",
        "max": None,
        "min": 1,
        "name": "ScanFiles List",
        "type": [
            {
                "default_value": None,
                "description": "ScanFile",
                "max": None,
                "min": 1,
                "name": "ScanFile",
                "type": "String",
            }
        ]
    }
]

extra2_params_def = [

    {
        "default_value": None,
        "description": "Value 1",
        "max": None,
        "min": 1,
        "name": "value1",
        "type": "Float"
    },
    {
        "default_value": None,
        "description": "Value 2",
        "max": None,
        "min": 1,
        "name": "value2",
        "type": "float"
    },
    {
        "default_value": None,
        "description": "List of Strings",
        "max": None,
        "min": 1,
        "name": "string_list",
        "type": [
            {
                "default_value": None,
                "description": "string",
                "max": None,
                "min": 1,
                "name": "string",
                "type": "String"
            },
        ]
    },
]
extra3_params_def = [

    {
        "default_value": None,
        "description": "param",
        "max": None,
        "min": 1,
        "name": "param",
        "type": "String"
    },
    {
        "default_value": None,
        "description": "Value",
        "max": None,
        "min": 1,
        "name": "value",
        "type": "String"
    },
]

extra4_params_def = [

    {
        "default_value": None,
        "description": "value 1",
        "max": None,
        "min": 1,
        "name": "value1",
        "type": "Float"
    },
    {
        "default_value": None,
        "description": "Value 2",
        "max": None,
        "min": 1,
        "name": "value2",
        "type": "Float"
    },
]


extra5_params_def = [

    {
        "default_value": None,
        "description": "List of Motor and Values",
        "max": None,
        "min": 1,
        "name": "numb_list",
        "type": [
            {
                "default_value": None,
                "description": "Motor",
                "max": None,
                "min": 1,
                "name": "pos",
                "type": "Motor"
            },
            {
                "default_value": None,
                "description": "Position to move to",
                "max": 2,
                "min": 1,
                "name": "pos",
                "type": "Float"
            }
        ]
    },
    {
        "default_value": None,
        "description": "Counter to use",
        "max": None,
        "min": 1,
        "name": "counter",
        "type": "ExpChan"
    },
    {
        "default_value": None,
        "description": "Value",
        "max": None,
        "min": 1,
        "name": "Value",
        "type": "Float"
    }
]
extra6_params_def = [

    {
        "default_value": None,
        "description": "List of Values",
        "max": None,
        "min": 1,
        "name": "numb_list",
        "type": [
            {
                "default_value": None,
                "description": "Value 1",
                "max": None,
                "min": 1,
                "name": "value1",
                "type": "Float"
            },
            {
                "default_value": None,
                "description": "Value 2",
                "max": None,
                "min": 1,
                "name": "value2",
                "type": "Float"
            }
        ]
    }
]

extra7_params_def = [

    {
        "default_value": None,
        "description": "value 1",
        "max": None,
        "min": 1,
        "name": "value1",
        "type": "Float"
    },
    {
        "default_value": None,
        "description": "List of Values",
        "max": None,
        "min": 1,
        "name": "numb_list",
        "type": [
            {
                "default_value": None,
                "description": "Value 2.1",
                "max": None,
                "min": 1,
                "name": "value21",
                "type": "Float"
            },
            {
                "default_value": None,
                "description": "Value 2.2",
                "max": None,
                "min": 1,
                "name": "value22",
                "type": "Float"
            }
        ]
    }
]
extra8_params_def = [

    {
        "default_value": None,
        "description": "value 1",
        "max": None,
        "min": 1,
        "name": "value1",
        "type": "Float"
    },
    {
        "default_value": None,
        "description": "Value 2",
        "max": None,
        "min": 1,
        "name": "value2",
        "type": "Float"
    },
]


# parameters examples tests
@insertTest(helper_name="parse", params_def=pt0_params_def,
            params_str="", params=[])
@insertTest(helper_name="parse", params_def=pt1d_params_def,
            params_str="1", params=["1"])
@insertTest(helper_name="parse", params_def=pt1d_params_def,
            params_str="", params=[])
@insertTest(helper_name="parse", params_def=pt2_params_def,
            params_str="mot1", params=["mot1"])
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
@insertTest(helper_name="parse", params_def=pt4_params_def,
            params_str="[mot1 mot2 mot3]", params=[["mot1", "mot2", "mot3"]])
@insertTest(helper_name="parse", params_def=pt4_params_def,
            params_str="mot1 mot2 mot3", params=[["mot1", "mot2", "mot3"]])
@insertTest(helper_name="parse", params_def=pt5_params_def,
            params_str="mot1 1 3", params=["mot1", ["1", "3"]])
@insertTest(helper_name="parse", params_def=pt5_params_def,
            params_str="mot1 [1 3]", params=["mot1", ["1", "3"]])
@insertTest(helper_name="parse", params_def=pt6_params_def,
            params_str="mot1 [1 34 1]", params=["mot1", ["1", "34", "1"]])
@insertTest(helper_name="parse", params_def=pt6_params_def,
            params_str="mot1 1 34 1", params=["mot1", ["1", "34", "1"]])
@insertTest(helper_name="parse", params_def=pt7_params_def,
            params_str="mot1 1 mot2 3",
            params=[[["mot1", "1"], ["mot2", "3"]]])
@insertTest(helper_name="parse", params_def=pt7_params_def,
            params_str="[[mot1 1] [mot2 3]]",
            params=[[["mot1", "1"], ["mot2", "3"]]])
@insertTest(helper_name="parse", params_def=pt7d1_params_def,
            params_str="[[mot1 1] [mot2 3]]",
            params=[[["mot1", "1"], ["mot2", "3"]]])
@insertTest(helper_name="parse", params_def=pt7d1_params_def,
            params_str="mot1 1 mot2 3",
            params=[[["mot1", "1"], ["mot2", "3"]]])
@insertTest(helper_name="parse", params_def=pt7d1_params_def,
            params_str="[[mot1] [mot2 3]]",
            params=[[["mot1"], ["mot2", "3"]]])
@insertTest(helper_name="parse", params_def=pt7d2_params_def,
            params_str="[[mot1 1] [mot2 3]]",
            params=[[["mot1", "1"], ["mot2", "3"]]])
@insertTest(helper_name="parse", params_def=pt7d2_params_def,
            params_str="mot1 1 mot2 3",
            params=[[["mot1", "1"], ["mot2", "3"]]])
@insertTest(helper_name="parse", params_def=pt7d2_params_def,
            params_str="[[] [mot2 3] []]",
            params=[[[], ["mot2", "3"], []]])
@insertTest(helper_name="parse", params_def=pt8_params_def,
            params_str="[[mot1 1] [mot2 3]]",
            params=[[["mot1", "1"], ["mot2", "3"]]])
@insertTest(helper_name="parse", params_def=pt8_params_def,
            params_str="mot1 1 mot2 3",
            params=[[["mot1", "1"], ["mot2", "3"]]])
@insertTest(helper_name="parse", params_def=pt9_params_def,
            params_str="[[mot1 1] [mot2 3]]",
            params=[[["mot1", "1"], ["mot2", "3"]]])
@insertTest(helper_name="parse", params_def=pt9_params_def,
            params_str="mot1 1 mot2 3",
            params=[[["mot1", "1"], ["mot2", "3"]]])
@insertTest(helper_name="parse", params_def=pt10_params_def,
            params_str="[1 3] mot1", params=[["1", "3"], "mot1"])
@insertTest(helper_name="parse", params_def=pt10_params_def,
            params_str="1 mot1", params=[["1"], "mot1"])
@insertTest(helper_name="parse", params_def=pt11_params_def,
            params_str="ct1 [1 3] mot1", params=["ct1", ["1", "3"], "mot1"])
@insertTest(helper_name="parse", params_def=pt12_params_def,
            params_str="[1 3 4] [mot1 mot2]",
            params=[["1", "3", "4"], ["mot1", "mot2"]])
@insertTest(helper_name="parse", params_def=pt13_params_def,
            params_str="[[mot1 mot2] [mot3 mot4]]",
            params=[[["mot1", "mot2"], ["mot3", "mot4"]]])
@insertTest(helper_name="parse", params_def=pt14_params_def,
            params_str="[[[mot1 mot2] 3] [[mot3] 5]]",
            params=[[[["mot1", "mot2"], "3"], [["mot3"], "5"]]])
@insertTest(helper_name="parse", params_def=pt14d_params_def,
            params_str="[[[mot1 mot2] 3] [[mot3] []]]",
            params=[[[["mot1", "mot2"], "3"], [["mot3"], []]]])
@insertTest(helper_name="parse", params_def=pt14d_params_def,
            params_str="[[[mot1 []] 3] [[mot3] []]]",
            params=[[[["mot1", []], "3"], [["mot3"], []]]])
@insertTest(helper_name="parse", params_def=pt14d_params_def,
            params_str="[[[[]] 3] [[mot3] []]]",
            params=[[[[[]], "3"], [["mot3"], []]]])
# extra tests for complex parameter values
@insertTest(helper_name="parse", params_def=extra1_params_def,
            params_str="ScanFile ['file.nxs' 'file.dat']",
            params=["ScanFile", ["file.nxs", "file.dat"]])
@insertTest(helper_name="parse", params_def=extra2_params_def,
            params_str="2 3 ['Hello world!' 'How are you?']",
            params=["2", "3", ["Hello world!", "How are you?"]])
@insertTest(helper_name="parse", params_def=extra3_params_def,
            params_str="ScanFile file.dat",
            params=["ScanFile", "file.dat"])
@insertTest(helper_name="parse", params_def=extra4_params_def,
            params_str="'2 3'", params=["2 3"])
@insertTest(helper_name="parse", params_def=extra5_params_def,
            params_str="[[mot01 3][mot02 5]] ct01 999",
            params=[[["mot01", "3"], ["mot02", "5"]], "ct01", "999"])
@insertTest(helper_name="parse", params_def=extra6_params_def,
            params_str="[[2 3][4 5]]",
            params=[[["2", "3"], ["4", "5"]]])
@insertTest(helper_name="parse", params_def=extra7_params_def,
            params_str="1 [2 3]",
            params=["1", ["2", "3"]])
@insertTest(helper_name="parse", params_def=extra8_params_def,
            params_str="2 3", params=["2", "3"])
class ParamParserTestCase(unittest.TestCase):
    """Unit tests for ParamParser class. Mainly based on macro examples for
    parameters definition.
    """
    def parse(self, params_def, params_str, params):
        """Helper method to test parameters parsing. To be used with
        insertTest decorator.
        """
        p = ParamParser(params_def)
        result = p.parse(params_str)
        msg = "Parsing failed (result: %r; expected: %r)" % \
              (result, params)
        self.assertListEqual(result, params, msg)
