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

"""Resource file containing parameter definitions and related
input and expected parameters, to be used in test_macro for testing
encoding and decoding of macro parameters."""


################################################################################

params_definition_move = [
    {'name': 'motor_pos_list',
     'default_value': None,
     'type': [
        {'name': 'motor',
         'default_value': "mot99",
         'type': 'Moveable'},
        {'name': 'pos',
         'default_value': 100,
         'type': 'Float'}
        ]}
    ]


move_parameters_1 = [[["mot01", "0"]]]
expected_result_1 = [[['mot01', "0"]]]

move_parameters_2 = [[["mot01"]]]
expected_result_2 = [[['mot01', "100"]]]

move_parameters_3 = [[[]]]
expected_result_3 = [[['mot99', "100"]]]

### These case maybe should not be allowed. It introduces benefits but can
### contain some ambiguity.
move_parameters_4 = [[[[], "50"]]]
expected_result_4 = [[['mot99', "50"]]]

### These case maybe should not be allowed. It introduces benefits but can
### contain some ambiguity.
move_parameters_5 = [[['mot99', []]]]
expected_result_5 = [[['mot99', "100"]]]

### These case most probably should not be allowed. It introduces benefits but
### can contain some ambiguity. To be studied in detail: it is important
### that the information interpreted by Sardana is the one that the user
### has the intention to give to Sardana. If a user can 'write' two different
### behaviors in the same exact way, maybe Sardana will not execute the
### user intention.
move_parameters_6 = [[[['mot01'], ["40"]]]]
expected_result_6 = [[['mot01', "40"]]]

move_parameters_7 = [[["mot01", "0"], ["mot02", "5"], ["mot03", "10"]]]
expected_result_7 = [[["mot01", "0"], ["mot02", "5"], ["mot03", "10"]]]

move_parameters_8 = [[["mot01", "0"], [], ["mot03"]]]
expected_result_8 = [[["mot01", "0"], ["mot99", "100"], ["mot03", "100"]]]


################################################################################


params_definition_float = [
    {'name': 'float_list',
     'default_value': None,
     'type': [
        {'name': 'float',
         'default_value': 100,
         'type': 'Float'}
        ]}
    ]


# Old interface
float_parameters_9 = ["1", "3", "15"]
expected_result_9 = [["1", "3", "15"]]

# New interface
float_parameters_10 = [["1", "3", "15"]]
expected_result_10 = [["1", "3", "15"]]

float_parameters_11 = [[[], [], []]]
expected_result_11 = [["100", "100", "100"]]

float_parameters_12 = [[["1"], ["3"], ["15"]]]
expected_result_12 = [["1", "3", "15"]]

float_parameters_13 = [["3", [], "4"]]
expected_result_13 = [["3", "100", "4"]]


################################################################################


paramsrepdef_floats_motors = [
    {'name': 'floats_list',
     'default_value': None,
     'type': [
        {'name': 'float',
         'default_value': 100,
         'type': 'Float'}]
     },
    {'name': 'motors_list',
     'default_value': None,
     'type': [
        {'name': 'motor',
         'default_value': 'mot99',
         'type': 'Moveable'}]
    }
    ]

floatlist_motorlist_parameters_14 = [[["1"], ["3"], ["4"]], [["mot1"],["mot2"]]]
expected_result_14 = [["1", "3", "4"], ["mot1", "mot2"]]

floatlist_motorlist_parameters_15 = [["1", "3", "4"], ["mot1", "mot2"]]
expected_result_15 = [["1", "3", "4"], ["mot1", "mot2"]]

floatlist_motorlist_parameters_16 = [["1", [], "4"], [[], "mot2"]]
expected_result_16 = [["1", "3", "4"], ["mot1", "mot2"]]

floatlist_motorlist_parameters_17 = [[["1"], "3", "4"], ["mot1", ["mot2"]]]
expected_result_17 = [["1", "3", "4"], ["mot1", "mot2"]]

################################################################################



















