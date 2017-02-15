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

from lxml import etree

from taurus.external import unittest
from taurus.test import insertTest
from sardana.taurus.core.tango.sardana.macro import MacroNode
from sardana.taurus.core.tango.sardana.macro import createMacroNode
from sardana.macroserver.macro import Type
from sardana.taurus.core.tango.sardana.test import (pt3_param_def_d1,
                                                    pt5_param_def_d1,
                                                    pt7_param_def_d1,
                                                    pt12_param_def_d1)
# TODO: Use unittest.mock instead of this fake class.
from sardana.macroserver.mstypemanager import TypeManager
class FakeMacroServer(object):
    name = "FakeMacroServer"

macro_server = FakeMacroServer()
tm = TypeManager(macro_server)

# TODO: Move the parameter definition to res/paramdef.py module
pt8_params_def = [
    {
        "name" : "m_p_pair",
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
pt8_params_value = ["mot73", "5.0", "mot74", "8.0"]

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
            param_value=pt8_params_value, expected_xml_rep=pt8_xml)
class MacroNodeTestCase(unittest.TestCase):

    def _validateXML(self, macronode_xml, expected_xml):
        '''
        :param macronode_xml: macronode lxml.etree
        :param expected_xml:  expected lxml.etree
        '''
        expected_str = etree.tostring(expected_xml)
        macronode_str = etree.tostring(macronode_xml, pretty_print=True)
        msg = "XML encodings are not equal"
        # TODO: check why macronode_str has an extra whitespace charactger 
        # at the end. strips should not be necessary
        self.assertEquals(expected_str.strip(), macronode_str.strip(), msg)

    def verifyXML(self, macro_name, param_def, param_value, expected_xml_rep):
        """
        Helper to verify the generated XML of a macroNode
        :param macro_name: (str) name of the macro
        :param param_def:   (list<dict>) macro parameters definition
        :param param_value: (list<str>) list of strins representing macro
            parameters values
        :param expected_xml_rep: "pretty print" string representation of a XML
            macroNode
        """
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
            param_def=pt3_param_def_d1,
            macro_params=[["1", "3", "15"]],
            expected_params_list=[["1", "3", "15"]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt3_param_def_d1,
            macro_params=[["3", [], "4"]],
            expected_params_list=[["3", "100", "4"]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt3_param_def_d1,
            macro_params=[[[], [], []]],
            expected_params_list=[["100", "100", "100"]]
            )

#### Testing one element (moveable) followed by a ####
############ list of elements (floats). ##############

@insertTest(helper_name='verifyEncoding',
            param_def=pt5_param_def_d1,
            macro_params=["mot01", ["1", "3", "15"]],
            expected_params_list=["mot01", ["1", "3", "15"]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt5_param_def_d1,
            macro_params=[[], ["1", "3", "15"]],
            expected_params_list=["mot99", ["1", "3", "15"]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt5_param_def_d1,
            macro_params=["mot01", [[], "3", "15"]],
            expected_params_list=["mot01", ["100", "3", "15"]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt5_param_def_d1,
            macro_params=[[], ["1", [], "15"]],
            expected_params_list=["mot99", ["1", "100", "15"]]
            )

#### Testing a list of pairs of elements (moveable, float). ####
@insertTest(helper_name='verifyEncoding',
            param_def=pt7_param_def_d1,
            macro_params=[[["mot01", "0"]]],
            expected_params_list=[[['mot01', "0"]]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt7_param_def_d1,
            macro_params=[[["mot01"]]],
            expected_params_list=[[['mot01', "100"]]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt7_param_def_d1,
            macro_params=[[[]]],
            expected_params_list=[[['mot99', "100"]]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt7_param_def_d1,
            macro_params=[[[[], "50"]]],
            expected_params_list=[[['mot99', "50"]]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt7_param_def_d1,
            macro_params=[[['mot99', []]]],
            expected_params_list=[[['mot99', "100"]]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt7_param_def_d1,
            macro_params=[[["mot01", "0"], ["mot02", "5"], ["mot03", "10"]]],
            expected_params_list=[[["mot01", "0"], ["mot02", "5"],
                                   ["mot03", "10"]]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt7_param_def_d1,
            macro_params=[[["mot01", "0"], [], ["mot03"]]],
            expected_params_list=[[["mot01", "0"], ["mot99", "100"],
                                   ["mot03", "100"]]]
            )

#### Testing lists of elements (floats), followed by another list of ####
######################### elements (moveables). #########################
@insertTest(helper_name='verifyEncoding',
            param_def=pt12_param_def_d1,
            macro_params=[["1", "3", "4"], ["mot1", "mot2"]],
            expected_params_list=[["1", "3", "4"], ["mot1", "mot2"]]
            )
@insertTest(helper_name='verifyEncoding',
            param_def=pt12_param_def_d1,
            macro_params=[["1", [], "4"], [[], "mot2"]],
            expected_params_list=[["1", "100", "4"], ["mot99", "mot2"]]
            )

class ParamsTestCase(unittest.TestCase):

    def verifyEncoding(self, param_def, macro_params, expected_params_list):
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
        node = MacroNode(name="macro_name", params_def=param_def)
        node.fromList(macro_params)

        output_params_list = node.toList()
        output_params_list.pop(0)

        msg = ("Parameters list is not encoded/decoded correctly. \n"
               "expected: %s \n"
               "received: %s" % (expected_params_list, output_params_list))
        self.assertEqual(output_params_list, expected_params_list, msg)


