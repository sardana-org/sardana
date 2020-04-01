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

"""Module with tests for macro related utils."""

from lxml import etree

import unittest
from taurus.test import insertTest
from sardana.taurus.core.tango.sardana.macro import MacroNode
from sardana.taurus.core.tango.sardana.macro import createMacroNode
from sardana.macroserver.macro import Type
from sardana.taurus.core.tango.sardana.test import (pt3d_param_def,
                                                    pt5d_param_def,
                                                    pt7d_param_def,
                                                    pt10d_param_def,
                                                    pt12d_param_def,
                                                    pt13d_param_def,
                                                    pt14d_param_def)
# TODO: Use unittest.mock instead of this fake class.
from sardana.macroserver.mstypemanager import TypeManager
from sardana.util.parser import ParamParser


class FakeMacroServer(object):
    name = "FakeMacroServer"

macro_server = FakeMacroServer()
tm = TypeManager(macro_server)

# TODO: Move the parameter definition to res/paramdef.py module
pt8_params_def = [
    {
        "name": "m_p_pair",
        "type": [
            {
                "name": "motor",
                "type": Type.Motor,
                "default_value": None,
                "description": "motor",
            },
            {
                "name": "pos",
                "type": Type.Integer,
                "default_value": None,
                "description": "position",
            }
        ],
        "description": "pair of motor and position",
        "min": 1,
        "max": None
    }
]
pt8_params_str = "mot73 5.0 mot74 8.0"

#
pt8_xml = \
    '''<macro name="pt8">
  <paramrepeat name="m_p_pair">
    <repeat nr="1">
      <param name="motor" value="mot73"/>
      <param name="pos" value="5.0"/>
    </repeat>
    <repeat nr="2">
      <param name="motor" value="mot74"/>
      <param name="pos" value="8.0"/>
    </repeat>
  </paramrepeat>
</macro>'''


@insertTest(helper_name='verifyXML', macro_name="pt8", param_def=pt8_params_def,
            param_str=pt8_params_str, expected_xml_rep=pt8_xml)
class MacroNodeTestCase(unittest.TestCase):

    def _validateXML(self, macronode_xml, expected_xml):
        '''
        :param macronode_xml: macronode lxml.etree
        :param expected_xml:  expected lxml.etree
        '''
        expected_str = etree.tostring(expected_xml, encoding='unicode')
        macronode_str = etree.tostring(macronode_xml, encoding='unicode',
                                       pretty_print=True)
        msg = "XML encodings are not equal"
        # TODO: check why macronode_str has an extra whitespace charactger
        # at the end. strips should not be necessary
        self.assertEqual(expected_str.strip(), macronode_str.strip(), msg)

    def verifyXML(self, macro_name, param_def, param_str, expected_xml_rep):
        """
        Helper to verify the generated XML of a macroNode
        :param macro_name: (str) name of the macro
        :param param_def:   (list<dict>) macro parameters definition
        :param param_value: (list<str>) list of strins representing macro
            parameters values
        :param expected_xml_rep: "pretty print" string representation of a XML
            macroNode
        """
        param_parser = ParamParser(param_def)
        param_value = param_parser.parse(param_str)
        # Create the MacroNide with the inputs
        macronode = createMacroNode(macro_name, param_def, param_value)
        # Get the MacroNode equivalent XML tree
        macronode_xml = macronode.toXml()
        # Create a XML tree
        expected_xml = etree.fromstring(expected_xml_rep)
        # Validate the XML tree
        self._validateXML(macronode_xml, expected_xml)


#### Testing a list of elements (floats) ####
@insertTest(helper_name='verifyEncoding',
            param_def=pt3d_param_def,
            macro_params=[["1", "3", "15"]],
            expected_params_list=[["1", "3", "15"]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt3d_param_def,
            macro_params=[["3", [], "4"]],
            expected_params_list=[["3", "100", "4"]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt3d_param_def,
            macro_params=[[[], [], []]],
            expected_params_list=[["100", "100", "100"]]
            )
#### Testing one element (moveable) followed by a ####
############ list of elements (floats). ##############
@insertTest(helper_name='verifyEncoding',
            param_def=pt5d_param_def,
            macro_params=["mot01", ["1", "3", "15"]],
            expected_params_list=["mot01", ["1", "3", "15"]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt5d_param_def,
            macro_params=[[], ["1", "3", "15"]],
            expected_params_list=["mot99", ["1", "3", "15"]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt5d_param_def,
            macro_params=["mot01", [[], "3", "15"]],
            expected_params_list=["mot01", ["100", "3", "15"]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt5d_param_def,
            macro_params=[[], ["1", [], "15"]],
            expected_params_list=["mot99", ["1", "100", "15"]]
            )
#### Testing a list of pairs of elements (moveable, float). ####
@insertTest(helper_name='verifyEncoding',
            param_def=pt7d_param_def,
            macro_params=[[["mot01", "0"]]],
            expected_params_list=[[['mot01', "0"]]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt7d_param_def,
            macro_params=[[["mot01"]]],
            expected_params_list=[[['mot01', "100"]]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt7d_param_def,
            macro_params=[[[]]],
            expected_params_list=[[['mot99', "100"]]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt7d_param_def,
            macro_params=[[[[], "50"]]],
            expected_params_list=[[['mot99', "50"]]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt7d_param_def,
            macro_params=[[['mot99', []]]],
            expected_params_list=[[['mot99', "100"]]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt7d_param_def,
            macro_params=[[["mot01", "0"], ["mot02", "5"], ["mot03", "10"]]],
            expected_params_list=[[["mot01", "0"], ["mot02", "5"],
                                   ["mot03", "10"]]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt7d_param_def,
            macro_params=[[["mot01", "0"], [], ["mot03"]]],
            expected_params_list=[[["mot01", "0"], ["mot99", "100"],
                                   ["mot03", "100"]]]
            )
# Testing the outer default parameters for the whole repetition.
# This test is commented because this option is not functional at the moment.
# See ticket #427 referring to this bug.
#@insertTest(helper_name='verifyEncoding',
#            param_def=pt7d_param_def,
#            macro_params=[[[]]],
#            expected_params_list=[[['mot01', "50"]]],
#            )
#### Testing list of elements (moveables) followed by a ####
################# single parameter (float). ################
@insertTest(helper_name='verifyEncoding',
            param_def=pt10d_param_def,
            macro_params=[["1", "3", "15"], "mot01"],
            expected_params_list=[["1", "3", "15"], "mot01"]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt10d_param_def,
            macro_params=[["1", "3", []], "mot01"],
            expected_params_list=[["1", "3", "100"], "mot01"]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt10d_param_def,
            macro_params=[["1", "3", "15"], []],
            expected_params_list=[["1", "3", "15"], "mot99"]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt10d_param_def,
            macro_params=[["1", [], "15"], []],
            expected_params_list=[["1", "100", "15"], "mot99"],
            )
#### Testing lists of elements (floats), followed by another list of ####
######################### elements (moveables). #########################
@insertTest(helper_name='verifyEncoding',
            param_def=pt12d_param_def,
            macro_params=[["1", "3", "4"], ["mot1", "mot2"]],
            expected_params_list=[["1", "3", "4"], ["mot1", "mot2"]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt12d_param_def,
            macro_params=[["1", [], "4"], [[], "mot2"]],
            expected_params_list=[["1", "100", "4"], ["mot99", "mot2"]]
            )
########################### Testing nested paramRepeats ##################
############## Groups of motors, where each group is a motor list ########
@insertTest(helper_name='verifyEncoding',
            param_def=pt13d_param_def,
            macro_params=[[["mot2", "mot3"], ["mot4", "mot5", "mot6"]]],
            expected_params_list=[[["mot2", "mot3"], ["mot4", "mot5", "mot6"]]]
            )
########################### Testing nested paramRepeats ##################
## Groups of motors, where each group is a motor list followed by a number
@insertTest(helper_name='verifyEncoding',
            param_def=pt14d_param_def,
            macro_params=[[[["mot2", "mot3"], 4],
                           [["mot4", "mot5", "mot6"], 5]]],
            expected_params_list=[[[["mot2", "mot3"], 4],
                                   [["mot4", "mot5", "mot6"], 5]]]
            )
class ParamsTestCase(unittest.TestCase):

    def verifyEncoding(self, param_def, macro_params, expected_params_list):
        """
        Helper to verify the correct building of the parameters objects tree.
        Verify that the list is recreated correctly from the parameters
        objects tree.
        :param param_def:   (list<dict>) macro parameters definition
        :param macro_params: (list<str>) list of strings representing macro
            parameters values.
        :param expected_params_list: (list<str>) expected parameters list.
        """

        # Create the MacroNode with the inputs
        node = MacroNode(name="macro_name", params_def=param_def)
        node.fromList(macro_params)

        output_params_list = node.toList()
        output_params_list.pop(0)

        msg = ("Parameters list is not encoded/decoded correctly. \n"
               "expected: %s \n"
               "received: %s" % (expected_params_list, output_params_list))
        self.assertEqual(output_params_list, expected_params_list, msg)


class DuplicateTestCase(unittest.TestCase):

    """
    Duplicate a RepeatNode and check that it has been correctly duplicated.
    """

    def testDuplication(self):
        """
        Helper to verify the correct duplication of a RepeatNode. Duplication
        of parameters.

        ..todo:: To be more unit test the use of MacroNode class should be
        avoided. Use of RepeatParamNode and its children should be enough.
        """

        # Create the MacroNode
        node = MacroNode(name="macro_name", params_def=pt7d_param_def)
        repeat_node_params = [['mot01', '0'], ['mot02', '2'], ['mot03', '4']]
        node.fromList([repeat_node_params])

        # Number of nodes before duplication
        num_initial_nodes = len(node.child(0))

        # Duplicate one RepeatNode
        num_node_to_duplicate = 1
        node_to_duplicate = node.child(0).child(num_node_to_duplicate)
        node_to_duplicate.duplicateNode()

        # Number of nodes after duplication
        num_final_nodes = len(node.child(0))

        # We get the last element RepeatNode.
        output_params_list = node.child(0).toList()
        repeat_node = node_to_duplicate.toList()
        expected_params_list = repeat_node_params + [repeat_node]

        msg = ("Repeat Node has not been correctly duplicated\n"
               "expected parameters: %s \n"
               "received parameters: %s" % (expected_params_list,
                                            output_params_list))
        self.assertEqual(output_params_list, expected_params_list, msg)

        expected_number_of_nodes = num_initial_nodes + 1
        msg = "Number of nodes after repeat node duplication is not correct"
        self.assertEqual(num_final_nodes, expected_number_of_nodes, msg)

        for i in range(expected_number_of_nodes):
            node_num = i + 1

            expected_name = '#' + str(node_num)
            new_node_name = node.child(0).child(i).name()
            msg = ("Name of node %d is not correct\n"
                   "expected name: %s \n"
                   "received name: %s" % (node_num,
                                          expected_name,
                                          new_node_name))
            self.assertEqual(new_node_name, expected_name, msg)
