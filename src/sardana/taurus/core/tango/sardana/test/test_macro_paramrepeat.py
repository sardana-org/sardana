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
from sardana.taurus.core.tango.sardana.test.res.params_definitions import *

"""
@insertTest(helper_name='verifyEncoding', macro_name="mv_like_macro",
            param_def=params_definition_move, macro_params=move_parameters_1,
            expected_params_list=expected_result_1)
@insertTest(helper_name='verifyEncoding', macro_name="mv_like_macro",
            param_def=params_definition_move, macro_params=move_parameters_2,
            expected_params_list=expected_result_2)
@insertTest(helper_name='verifyEncoding', macro_name="mv_like_macro",
            param_def=params_definition_move, macro_params=move_parameters_3,
            expected_params_list=expected_result_3)
@insertTest(helper_name='verifyEncoding', macro_name="mv_like_macro",
            param_def=params_definition_move, macro_params=move_parameters_4,
            expected_params_list=expected_result_4)
@insertTest(helper_name='verifyEncoding', macro_name="mv_like_macro",
            param_def=params_definition_move, macro_params=move_parameters_5,
            expected_params_list=expected_result_5)
@insertTest(helper_name='verifyEncoding', macro_name="mv_like_macro",
            param_def=params_definition_move, macro_params=move_parameters_6,
            expected_params_list=expected_result_6)
@insertTest(helper_name='verifyEncoding', macro_name="mv_like_macro",
            param_def=params_definition_move, macro_params=move_parameters_7,
            expected_params_list=expected_result_7)
@insertTest(helper_name='verifyEncoding', macro_name="mv_like_macro",
            param_def=params_definition_move, macro_params=move_parameters_8,
            expected_params_list=expected_result_8)
@insertTest(helper_name='verifyEncoding', macro_name="mv_like_macro",
            param_def=params_definition_float, macro_params=float_parameters_9,
            expected_params_list=expected_result_9)
@insertTest(helper_name='verifyEncoding', macro_name="float_macro",
            param_def=params_definition_float, macro_params=float_parameters_10,
            expected_params_list=expected_result_10)
@insertTest(helper_name='verifyEncoding', macro_name="float_macro",
            param_def=params_definition_float, macro_params=float_parameters_11,
            expected_params_list=expected_result_11)
@insertTest(helper_name='verifyEncoding', macro_name="float_macro",
            param_def=params_definition_float, macro_params=float_parameters_12,
            expected_params_list=expected_result_12)
@insertTest(helper_name='verifyEncoding', macro_name="float_macro",
            param_def=params_definition_float, macro_params=float_parameters_13,
            expected_params_list=expected_result_13)"""

"""@insertTest(helper_name='verifyEncoding', macro_name="floats_motors_macro",
            param_def=paramsrepdef_floats_motors,
            macro_params=floatlist_motorlist_parameters_14,
            expected_params_list=expected_result_14)
@insertTest(helper_name='verifyEncoding', macro_name="floats_motors_macro",
            param_def=paramsrepdef_floats_motors,
            macro_params=floatlist_motorlist_parameters_15,
            expected_params_list=expected_result_15)
@insertTest(helper_name='verifyEncoding', macro_name="floats_motors_macro",
            param_def=paramsrepdef_floats_motors,
            macro_params=floatlist_motorlist_parameters_16,
            expected_params_list=expected_result_16)"""
@insertTest(helper_name='verifyEncoding', macro_name="floats_motors_macro",
            param_def=paramsrepdef_floats_motors,
            macro_params=floatlist_motorlist_parameters_17,
            expected_params_list=expected_result_17)
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
        #print(macro_name)
        #print(param_def)
        #print(macro_params)
        #print(expected_params_list)
        node.fromList(macro_params)

        #import lxml
        #xml = node.toXml(withId=False)
        #print lxml.etree.tostring(xml, pretty_print=True)



        output_params_list = node.toList()
        #print(output_params_list)
        print(output_params_list)
        output_params_list.pop(0)
        print(output_params_list)

        msg = ("Parameters list is not encoded/decoded correctly. \n"
               "expected: %s \n"
               "received: %s" % (expected_params_list, output_params_list))
        self.assertEqual(output_params_list, expected_params_list, msg)




