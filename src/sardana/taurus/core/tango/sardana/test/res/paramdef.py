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
test_macro for testing encoding and decoding of macro parameters.
The following parameter definitions are based in the macro examples present in
the module sardana.macroserver.macros.examples.parameters"""


# pt3 like parameter definition, but using default values.
pt3_param_def_d1 = [
    {'name': 'numb_list',
     'default_value': None,
     'type': [
        {'name': 'float',
         'default_value': 100
         }
        ]}
    ]


# pt5 like parameter definition, but using default values.
pt5_param_def_d1 = [
    {'name': 'motor',
     'default_value': "mot99"
     },
    {'name': 'float_list',
     'default_value': None,
     'type': [
        {'name': 'float',
         'default_value': 100
         }
        ]}
    ]


# pt7 like parameter definition, but using default values.
pt7_param_def_d1 = [
    {'name': 'motor_pos_list',
     'default_value': None,
     'type': [
        {'name': 'motor',
         'default_value': "mot99"
         },
        {'name': 'pos',
         'default_value': 100
         }
        ]}
    ]


# pt12 like parameter definition, but using default values.
pt12_param_def_d1 = [
    {'name': 'numb_list',
     'default_value': None,
     'type': [
        {'name': 'float',
         'default_value': 100
         }]
     },
    {'name': 'motors_list',
     'default_value': None,
     'type': [
        {'name': 'motor',
         'default_value': 'mot99'
         }]
    }
    ]

