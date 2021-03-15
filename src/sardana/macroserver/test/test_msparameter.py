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

import unittest
from taurus.test import insertTest

from sardana.macroserver.macro import Type
from sardana.macroserver.msparameter import ParamDecoder, WrongParamType

from sardana.macroserver.mstypemanager import TypeManager


class FakeMacroServer(object):
    name = "FakeMacroServer"

macro_server = FakeMacroServer()
TYPE_MANAGER = TypeManager(macro_server)

params_def1 = [
    {
        "name": "param1",
        "type": Type.String,
        "default_value": None,
        "description": "param1 description"
    }
]

params_def2 = [
    {
        "name": "param1",
        "type": Type.Integer,
        "default_value": None,
        "description": "param1 description"
    }
]

params_def3 = [
    {
        "name": "param1",
        "type": [
            {
                "name": "subparam1",
                "type": Type.Integer,
                "default_value": None,
                "description": "subparam1 description",
            }
        ],
        "default_value": None,
        "description": "param1 description",
        "min": 0,
        "max": None
    }
]

params_raw1 = ["value1"]
params_raw2 = [[1]]
params_raw3 = []
expected_params1 = ["value1"]
expected_params2 = [[1]]
expected_params3 = []

doc1 = "Decode macro with one single parameter with correct value"
doc2 = "Decode macro with one single parameter with wrong value"
doc3 = "Decode macro with one simple repeat parameter with correct value"
doc4 = "Decode macro with one simple repeat parameter with min=0 and no values"


@insertTest(helper_name="decode", test_method_name="test_decode1",
            test_method_doc=doc1, params_def=params_def1,
            params_raw=params_raw1, expected_params=expected_params1)
@insertTest(helper_name="decode", test_method_name="test_decode2",
            test_method_doc=doc2, params_def=params_def2,
            params_raw=params_raw1, expected_exception=WrongParamType)
@insertTest(helper_name="decode", test_method_name="test_decode3",
            test_method_doc=doc3, params_def=params_def3,
            params_raw=params_raw1, expected_exception=WrongParamType)
@insertTest(helper_name="decode", test_method_name="test_decode4",
            test_method_doc=doc4, params_def=params_def3,
            params_raw=params_raw3, expected_params=expected_params3)
class TestParamDecoder(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.type_manager = TYPE_MANAGER
        # use this code to parameter types of sardana interfaces e.g. Motor
#         type_motor = self.type_manager.getTypeObj(Type.Motor)
#         type_motor.getObj = lambda name:name

    def decode(self, params_def, params_raw, expected_params=None,
               expected_exception=None):
        """Test decoding of macro parameters using ParamDecoder class by
        comparing the result with either of the expected_params or the
        expcted_exception result, not both of them.

        :param params_def: list(dict) where each dict represents one parameter
            definition (required keys: name, type, default_value, description
            and min & max in case of the repeat parameters)
        :param params_raw: list of parameter values or XML strucutre with
            parameter values
        :param expected_params: list of the expected parameter values after the
            decoding process
        :param expected_exception: expected exception class
        """
        if expected_params is None and expected_exception is None:
            raise ValueError("missing expected_params or expected_exception")
        if not expected_params is None and not expected_exception is None:
            raise ValueError("too many expected expected values")
        exception = None
        try:
            param_decoder = ParamDecoder(self.type_manager, params_def,
                                         params_raw)
        except Exception as e:
            exception = e
        if expected_params:
            exception_message = getattr(exception, "message", None)
            msg = "unexpected exception: %s (%s)" % (exception,
                                                     exception_message)
            self.assertIsNone(exception, msg)
            params = param_decoder.getParamList()
            msg = ("decoding result (%s) does not match with the expected"
                   " result (%s)" % (params, expected_params))
            self.assertListEqual(params, expected_params, msg)
        if expected_exception:
            msg = ("decoding exception type (%s) does not match with the"
                   " expected exception type (%s)" % (type(exception),
                                                      expected_exception))
            self.assertIsInstance(exception, expected_exception, msg)

    def tearDown(self):
        unittest.TestCase.tearDown(self)
