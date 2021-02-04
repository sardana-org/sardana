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

"""This module contains macros that demonstrate the usage of macro parameters"""

from sardana.macroserver.macro import Macro, Type

__all__ = ["pt0", "pt1", "pt2", "pt3", "pt3d", "pt4", "pt5", "pt6", "pt7",
           "pt7d1", "pt7d2", "pt8", "pt9", "pt10", "pt11", "pt12", "pt13",
           "pt14", "pt14d", "twice"]


class pt0(Macro):
    """Macro without parameters. Pretty dull.
       Usage from Spock, ex.:
       pt0
       """

    param_def = []

    def run(self):
        pass


class pt1(Macro):
    """Macro with one float parameter: Each parameter is described in the
    param_def sequence as being a sequence of four elements: name, type,
    default value and description.
    Usage from Spock, ex.:
    pt1 1
    """

    param_def = [['value', Type.Float, None, 'some bloody float']]

    def run(self, f):
        pass


class pt1d(Macro):
    """Macro with one float parameter with default value..
    Usage from Spock, ex.:
    pt1d 1
    pt1d
    """

    param_def = [['value', Type.Float, None, 'some bloody float']]

    def run(self, f):
        pass


class pt2(Macro):
    """Macro with one Motor parameter: Each parameter is described in the
    param_def sequence as being a sequence of four elements: name, type,
    default value and description.
    Usage from Spock, ex.
    pt2 mot1
    """

    param_def = [['motor', Type.Motor, None, 'some bloody motor']]

    def run(self, m):
        pass


class pt3(Macro):
    """Macro with a list of numbers as parameter: the type is a sequence of
    parameter types which is repeated. In this case it is a repetition of a
    float so only one parameter is defined.
    By default the repetition as a semantics of 'at least one'
    Usages from Spock, ex.:
    pt3 [1 34 15]
    pt3 1 34 15
    """

    param_def = [
        ['numb_list', [['pos', Type.Float, None, 'value']], None, 'List of values'],
    ]

    def run(self, *args, **kwargs):
        pass


class pt3d(Macro):
    """Macro with a list of numbers as parameter: the type is a sequence of
    parameter types which is repeated. In this case it is a repetition of a
    float so only one parameter is defined. The parameter has a default value.
    By default the repetition as a semantics of 'at least one'
    Usages from Spock, ex.:
    pt3d [1 34 15]
    pt3d 1 34 15
    Usage taken the default value, ex.:
    pt3d [1 [] 15]
    """

    param_def = [
        ['numb_list', [['pos', Type.Float, 21, 'value']], None, 'List of values'],
    ]

    def run(self, *args, **kwargs):
        pass


class pt4(Macro):
    """Macro with a list of motors as parameter: the type is a sequence of
    parameter types which is repeated. In this case it is a repetition of a
    motor so only one parameter is defined.
    By default the repetition as a semantics of 'at least one'.
    Usages from Spock, ex.:
    pt4 [mot1 mot2 mot3]
    pt4 mot1 mot2 mot3
    """

    param_def = [
        ['motor_list', [['motor', Type.Motor, None, 'motor name']],
            None, 'List of motors'],
    ]

    def run(self, *args, **kwargs):
        pass


class pt5(Macro):
    """Macro with a motor parameter followed by a list of numbers.
    Usages from Spock, ex.:
    pt5 mot1 [1 3]
    pt5 mot1 1 3
    """

    param_def = [
        ['motor', Type.Motor, None, 'Motor to move'],
        ['numb_list', [['pos', Type.Float, None, 'value']], None, 'List of values'],
    ]

    def run(self, *args, **kwargs):
        pass


class pt6(Macro):
    """Macro with a motor parameter followed by a list of numbers. The list as
    explicitly stated an optional last element which is a dictionary that defines the
    min and max values for repetitions.
    Usages from Spock, ex.:
    pt6 mot1 [1 34 1]
    pt6 mot1 1 34 1
    """

    param_def = [
        ['motor', Type.Motor, None, 'Motor to move'],
        ['numb_list', [['pos', Type.Float, None, 'value'], {
            'min': 1, 'max': None}], None, 'List of values'],
    ]

    def run(self, *args, **kwargs):
        pass


class pt7(Macro):
    """Macro with a list of pair Motor,Float.
    Usages from Spock, ex.:
    pt7 [[mot1 1] [mot2 3]]
    pt7 mot1 1 mot2 3
    """

    param_def = [
        ['m_p_pair', [['motor', Type.Motor, None, 'Motor to move'],
                      ['pos',   Type.Float, None, 'Position to move to']],
         None, 'List of motor/position pairs']
    ]

    def run(self, *args, **kwargs):
        pass


class pt7d1(Macro):
    """Macro with a list of pair Motor,Float. Default value for last
    repeat parameter element.
    Usages from Spock, ex.:
    pt7d1 [[mot1 1] [mot2 3]]
    pt7d1 mot1 1 mot2 3
    Using default value, ex.:
    pt7d1 [[mot1] [mot2 3]] # at any repetition
    pt7d1 mot1 # if only one repetition

    """

    param_def = [
        ['m_p_pair', [['motor', Type.Motor, None, 'Motor to move'],
                      ['pos',   Type.Float, 2, 'Position to move to']],
         None, 'List of motor/position pairs']
    ]

    def run(self, *args, **kwargs):
        pass


class pt7d2(Macro):
    """Macro with a list of pair Motor,Float. Default value for both
    repeat parameters elements.
    Usages from Spock, ex.:
    pt7d2 [[mot1 1] [mot2 3]]
    pt7d2 mot1 1 mot2 3
    Using both default values, ex.:
    pt7d2 [[] [mot2 3] []] # at any repetition
    """

    param_def = [
        ['m_p_pair', [['motor', Type.Motor, 'mot1', 'Motor to move'],
                      ['pos',   Type.Float, 2, 'Position to move to']],
         None, 'List of motor/position pairs']
    ]

    def run(self, *args, **kwargs):
        pass


class pt8(Macro):
    """Macro with a list of pair Motor,Float. The min and max elements have been
    explicitly stated.
    Usages from Spock, ex.:
    pt8 [[mot1 1] [mot2 3]]
    pt8 mot1 1 mot2 3
    """

    param_def = [
        ['m_p_pair', [['motor', Type.Motor, None, 'Motor to move'],
                      ['pos',   Type.Float, None, 'Position to move to'],
                      {'min': 1, 'max': 2}],
         None, 'List of motor/position pairs']
    ]

    def run(self, *args, **kwargs):
        pass


class pt9(Macro):
    """Same as macro pt7 but with min and max number of repetitions of the
    repeat parameter.
    Usages from Spock, ex.:
    pt9 [[mot1 1][mot2 3]]
    pt9 mot1 1 mot2 3
    """

    param_def = [
        ['m_p_pair', [['motor', Type.Motor, None, 'Motor to move'],
                      ['pos',  Type.Float, None, 'Position to move to'],
                      {'min': 1, 'max': 2}],
         None, 'List of motor/position pairs'],
    ]

    def run(self, *args, **kwargs):
        pass


class pt10(Macro):
    """Macro with list of numbers followed by a motor parameter. The repeat
    parameter may be defined as first one.
    Usage from Spock, ex.:
    pt10 [1 3] mot1
    pt10 1 mot1 # if only one repetition
    """

    param_def = [
        ['numb_list', [['pos', Type.Float, None, 'value']], None, 'List of values'],
        ['motor', Type.Motor, None, 'Motor to move']
    ]

    def run(self, *args, **kwargs):
        pass


class pt11(Macro):
    """Macro with counter parameter followed by a list of numbers, followed by
    a motor parameter. The repeat parameter may be defined in between other
    parameters.
    Usages from Spock, ex.:
    pt11 ct1 [1 3] mot1
    pt11 ct1 1 mot1 # if only one repetition
    """

    param_def = [
        ['counter', Type.ExpChannel, None, 'Counter to count'],
        ['numb_list', [['pos', Type.Float, None, 'value']], None, 'List of values'],
        ['motor', Type.Motor, None, 'Motor to move']
    ]

    def run(self, *args, **kwargs):
        pass


class pt12(Macro):
    """Macro with list of motors followed by list of numbers. Two repeat
    parameters may defined.
    Usage from Spock, ex.:
    pt12 [1 3 4] [mot1 mot2]
    pt12 1 mot1 # if only one repetition for each repeat parameter
    """

    param_def = [
        ['numb_list', [['pos', Type.Float, None, 'value']], None, 'List of values'],
        ['motor_list', [['motor', Type.Motor, None, 'Motor to move']],
         None, 'List of motors']
    ]

    def run(self, *args, **kwargs):
        pass


class pt13(Macro):
    """Macro with list of motors groups, where each motor group is a list of
    motors. Repeat parameters may be defined as nested.
    Usage from Spock, ex.:
    pt13 [[mot1 mot2] [mot3 mot4]]
"""

    param_def = [
        ['motor_group_list',
         [['motor_list', [['motor', Type.Motor, None, 'Motor to move']],
           None, 'List of motors']],
         None, 'Motor groups']
    ]

    def run(self, *args, **kwargs):
        pass


class pt14(Macro):
    """Macro with list of motors groups, where each motor group is a list of
    motors and a float. Repeat parameters may be defined as nested.
    Usage from Spock, ex.:
    pt14 [[[mot1 mot2] 3] [[mot3] 5]]
    """

    param_def = [
        ['motor_group_list',
         [['motor_list', [['motor', Type.Motor, None, 'Motor to move']], None, 'List of motors'],
          ['float', Type.Float, None, 'Number']],
         None, 'Motor groups']
    ]

    def run(self, *args, **kwargs):
        pass


class pt14d(Macro):
    """Macro with list of motors groups, where each motor group is a list of
    motors and a float. Repeat parameters may be defined as nested.
    Default values can be used.
    Usages taken default values, ex.:
    pt14d [[[mot1 mot2] 3] [[mot3] []]]
    pt14d [[[mot1 []] 3] [[mot3] []]]
    pt14d [[[[]] 3] [[mot3] []]]
    """

    param_def = [
        ['motor_group_list',
         [['motor_list', [['motor', Type.Motor, 'mot1', 'Motor to move']], None, 'List of motors'],
          ['float', Type.Float, 33, 'Number']],
         None, 'Motor groups']
    ]

    def run(self, *args, **kwargs):
        pass


class twice(Macro):
    """A macro that returns a float that is twice its input. It also sets its
    data to be a dictionary with 'in','out' as keys and value,result
    as values, respectively"""

    # uncomment the following lines as necessary. Otherwise you may delete them
    param_def = [["value", Type.Float, 23, "value to be doubled"]]
    result_def = [["result", Type.Float, None,
                   "the double of the given value"]]
    #hints = {}
    # env = (,)

    # uncomment the following lines if need prepare. Otherwise you may delete them
    # def prepare(self):
    #    pass

    def run(self, n):
        ret = 2 * n
        self.setData({'in': n, 'out': ret})
        return ret
