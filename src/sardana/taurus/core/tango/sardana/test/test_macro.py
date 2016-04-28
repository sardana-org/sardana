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
from sardana.taurus.core.tango.sardana.macro import createMacroNode
from sardana.macroserver.macro import Type

# TODO: Use unittest.mock instead of this fake class.
from sardana.macroserver.mstypemanager import TypeManager
class FakeMacroServer(object):
    name = "FakeMacroServer"

macro_server = FakeMacroServer()
tm = TypeManager(macro_server)


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
