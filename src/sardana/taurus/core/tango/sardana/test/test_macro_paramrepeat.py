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

"""Module with tests for macro related utils."""


from taurus.external import unittest
from taurus.test import insertTest
from sardana.taurus.core.tango.sardana.macro import MacroNode
from sardana.taurus.core.tango.sardana.test.res.paramdef import *

#### Testing a list of elements (floats) ####
# Old interface
@insertTest(helper_name='verifyEncoding',
            macro_name="numb_list_macro",
            param_def=pt3_like_param_def,
            macro_params=["1", "3", "15"],
            expected_params_list=[["1", "3", "15"]]
            )
@insertTest(helper_name='verifyEncoding',
            macro_name="numb_list_macro",
            param_def=pt3_like_param_def,
            macro_params=[["1", "3", "15"]],
            expected_params_list=[["1", "3", "15"]]
            )
@insertTest(helper_name='verifyEncoding',
            macro_name="numb_list_macro",
            param_def=pt3_like_param_def,
            macro_params=[[[], [], []]],
            expected_params_list=[["100", "100", "100"]]
            )
@insertTest(helper_name='verifyEncoding',
            macro_name="numb_list_macro",
            param_def=pt3_like_param_def,
            macro_params=[[["1"], ["3"], ["15"]]],
            expected_params_list=[["1", "3", "15"]]
            )
@insertTest(helper_name='verifyEncoding',
            macro_name="numb_list_macro",
            param_def=pt3_like_param_def,
            macro_params=[["3", [], "4"]],
            expected_params_list=[["3", "100", "4"]]
            )

#### Testing one element (moveable) followed by a ####
############ list of elements (floats). ##############
# It should be possible to do so?
@insertTest(helper_name='verifyEncoding',
            macro_name="motor_floats_macro",
            param_def=pt5_like_param_def,
            macro_params=["mot01", "1", "3", "15"],
            expected_params_list=["mot01", ["1", "3", "15"]]
            )
@insertTest(helper_name='verifyEncoding',
            macro_name="motor_floats_macro",
            param_def=pt5_like_param_def,
            macro_params=["mot01", ["1", "3", "15"]],
            expected_params_list=["mot01", ["1", "3", "15"]]
            )
@insertTest(helper_name='verifyEncoding',
            macro_name="motor_floats_macro",
            param_def=pt5_like_param_def,
            macro_params=["mot01", [["1"], ["3"], ["15"]]],
            expected_params_list=["mot01", ["1", "3", "15"]]
            )
@insertTest(helper_name='verifyEncoding',
            macro_name="motor_floats_macro",
            param_def=pt5_like_param_def,
            macro_params=["mot01", [[], ["3"], ["15"]]],
            expected_params_list=["mot01", ["100", "3", "15"]]
            )
@insertTest(helper_name='verifyEncoding',
            macro_name="motor_floats_macro",
            param_def=pt5_like_param_def,
            macro_params=["mot01", [["1"], "3", []]],
            expected_params_list=["mot01", ["1", "3", "100"]]
            )
@insertTest(helper_name='verifyEncoding',
            macro_name="motor_floats_macro",
            param_def=pt5_like_param_def,
            macro_params=[[], ["1", "3", "15"]],
            expected_params_list=["mot01", ["1", "3", "100"]]
            )
@insertTest(helper_name='verifyEncoding',
            macro_name="motor_floats_macro",
            param_def=pt5_like_param_def,
            macro_params=[[], ["1", [], "15"]],
            expected_params_list=["mot01", ["1", "100", "15"]]
            )
@insertTest(helper_name='verifyEncoding',
            macro_name="motor_floats_macro",
            param_def=pt5_like_param_def,
            macro_params=[[], [["1"], [], ["15"]]],
            expected_params_list=["mot01", ["1", "100", "15"]]
            )

#### Testing a list of pairs of elements (moveable, float). ####
@insertTest(helper_name='verifyEncoding',
            macro_name="mv_like_macro",
            param_def=pt7_like_paramdef,
            macro_params=[[["mot01", "0"]]],
            expected_params_list=[[['mot01', "0"]]]
            )
@insertTest(helper_name='verifyEncoding',
            macro_name="mv_like_macro",
            param_def=pt7_like_paramdef,
            macro_params=[[["mot01"]]],
            expected_params_list=[[['mot01', "100"]]]
            )
@insertTest(helper_name='verifyEncoding',
            macro_name="mv_like_macro",
            param_def=pt7_like_paramdef,
            macro_params=[[[]]],
            expected_params_list=[[['mot99', "100"]]]
            )
# TODO: These case maybe should not be allowed. It introduces benefits but can
# contain some ambiguity.
@insertTest(helper_name='verifyEncoding',
            macro_name="mv_like_macro",
            param_def=pt7_like_paramdef,
            macro_params=[[[[], "50"]]],
            expected_params_list=[[['mot99', "50"]]]
            )
# TODO: These case maybe should not be allowed. It introduces benefits but can
# contain some ambiguity.
@insertTest(helper_name='verifyEncoding',
            macro_name="mv_like_macro",
            param_def=pt7_like_paramdef,
            macro_params=[[['mot99', []]]],
            expected_params_list=[[['mot99', "100"]]]
            )
# TODO: These case most probably should not be allowed. It introduces benefits
# but can contain some ambiguity. To be studied in detail: it is important
# that the information interpreted by Sardana is the one that the user
# has the intention to give to Sardana. If a user can 'write' two different
# behaviors in the same exact way, maybe Sardana will not execute the
# user intention.
@insertTest(helper_name='verifyEncoding',
            macro_name="mv_like_macro",
            param_def=pt7_like_paramdef,
            macro_params=[[[['mot01'], ["40"]]]],
            expected_params_list=[[['mot01', "40"]]]
            )
@insertTest(helper_name='verifyEncoding',
            macro_name="mv_like_macro",
            param_def=pt7_like_paramdef,
            macro_params=[[["mot01", "0"], ["mot02", "5"], ["mot03", "10"]]],
            expected_params_list=[[["mot01", "0"], ["mot02", "5"],
                                   ["mot03", "10"]]]
            )
@insertTest(helper_name='verifyEncoding',
            macro_name="mv_like_macro",
            param_def=pt7_like_paramdef,
            macro_params=[[["mot01", "0"], [], ["mot03"]]],
            expected_params_list=[[["mot01", "0"], ["mot99", "100"],
                                   ["mot03", "100"]]]
            )

#### Testing lists of elements (floats), followed by another list of ####
######################### elements (moveables). #########################
@insertTest(helper_name='verifyEncoding',
            macro_name="floats_motors_macro",
            param_def=pt12_like_param_def,
            macro_params=[[["1"], ["3"], ["4"]], [["mot1"],["mot2"]]],
            expected_params_list=[["1", "3", "4"], ["mot1", "mot2"]]
            )
@insertTest(helper_name='verifyEncoding',
            macro_name="floats_motors_macro",
            param_def=pt12_like_param_def,
            macro_params=[["1", "3", "4"], ["mot1", "mot2"]],
            expected_params_list=[["1", "3", "4"], ["mot1", "mot2"]]
            )
@insertTest(helper_name='verifyEncoding',
            macro_name="floats_motors_macro",
            param_def=pt12_like_param_def,
            macro_params=[["1", [], "4"], [[], "mot2"]],
            expected_params_list=[["1", "3", "4"], ["mot1", "mot2"]]
            )
@insertTest(helper_name='verifyEncoding',
            macro_name="floats_motors_macro",
            param_def=pt12_like_param_def,
            macro_params=[[["1"], "3", "4"], ["mot1", ["mot2"]]],
            expected_params_list=[["1", "3", "4"], ["mot1", "mot2"]]
            )

class ParamsTestCase(unittest.TestCase):

    def verifyEncoding(self, macro_name, param_def, macro_params,
                       expected_params_list):
        """
        Helper to verify the correct building of the parameters objects tree.
        Verify that the list is recreated correctly from the parameters
        objects tree.
        :param macro_name: (str) name of the macro
        :param param_def:   (list<dict>) macro parameters definition
        :param macro_params: (list<str>) list of strings representing macro
            parameters values.
        :param expected_params_list: (list<str>) expected parameters list.
        """

        # Create the MacroNode with the inputs
        node = MacroNode(name=macro_name, params_def=param_def)
        node.fromList(macro_params)

        output_params_list = node.toList()
        output_params_list.pop(0)
        print(output_params_list)

        msg = ("Parameters list is not encoded/decoded correctly. \n"
               "expected: %s \n"
               "received: %s" % (expected_params_list, output_params_list))
        self.assertEqual(output_params_list, expected_params_list, msg)


