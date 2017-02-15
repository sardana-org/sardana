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

"""Resource file containing parameter definitions, to be used in
test_macro for testing encoding and decoding of macro parameters."""

pt3_like_param_def = [
    {'name': 'numb_list',
     'default_value': None,
     'type': [
        {'name': 'float',
         'default_value': 100,
         'type': 'Float'}
        ]}
    ]

pt5_like_param_def = [
    {'name': 'motor',
     'default_value': "mot99",
     'type': 'Moveable'},
    {'name': 'float_list',
     'default_value': None,
     'type': [
        {'name': 'float',
         'default_value': 100,
         'type': 'Float'}
        ]}
    ]

pt7_like_paramdef = [
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

pt12_like_param_def = [
    {'name': 'numb_list',
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

