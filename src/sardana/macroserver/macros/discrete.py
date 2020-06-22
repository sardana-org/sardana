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

""" Discrete pseudo motor controller configuration related macros"""

__all__ = ["def_discr_pos", "udef_discr_pos", "prdef_discr"]

__docformat__ = 'restructuredtext'

import math
from taurus.core.util.codecs import CodecFactory
from taurus.console.table import Table
from sardana.macroserver.macro import Macro, Type


class DiscretePseudoMotorConfiguration(dict):

    def __init__(self, pseudo_obj, macro):
        self.pseudo = pseudo_obj
        self.macro = macro
        _physical_motor_name = self.pseudo.physical_elements[0]
        self.motor = macro.getMoveable(_physical_motor_name)
        cf = CodecFactory()
        self.json = cf.getCodec('json')
        conf = self.get_configuration()
        self.update(conf)

    def get_configuration(self):
        value = self.pseudo.getAttribute('configuration').read().value
        fmt, data = self.json.decode(('json', value))
        return data

    def has_calibration(self):
        return all(['set' in list(self[x].keys()) for x in list(self.keys())])

    def add_point(self, label, pos, setpos, dmin, dmax):
        point = dict()
        point['pos'] = int(pos)
        label = label.upper()
        # Calculate point calibration if required
        if self.has_calibration():
            # Set to current physical position if no value supplied as argument
            if math.isinf(setpos):
                point['set'] = self.motor.position
            else:
                point['set'] = float(setpos)
            # If point exists, we use current min, max values
            if (label in list(self.keys())
                    and math.isinf(dmin)
                    and math.isinf(dmax)):
                p = self[label]
                min_pos = point['set'] + p['set'] - p['min']
                max_pos = point['set'] + p['set'] - p['max']
            # else, new point has new calibration,
            elif math.isinf(dmin) and math.isinf(dmax):
                min_pos = point['set']
                max_pos = point['set']
            else:
                min_pos = point['set'] + dmin
                max_pos = point['set'] + dmax

            point['min'] = min_pos
            point['max'] = max_pos

        self[label] = point
        self._update()

    def remove_point(self, label):
        try:
            label = label.upper()
            self.pop(label)
            self._update()
        except Exception as e:
            self.macro.error('Cannot remove label {0}\n{1}'.format(label, e))

    def _update(self):
        try:
            fmt, value = self.json.encode(('', self))
            self.pseudo.getAttribute('configuration').write(value)
            self.macro.debug('Updated configuration:\n{0}'.format(self))
        except Exception as e:
            msg = 'Cannot update configuration]\n{0}\{1}'.format(e, self)
            self.macro.error(msg)

    def __str__(self):
        fmt, value = self.json.encode(('', self), indent=4, sort_keys=True)
        return value


class def_discr_pos(Macro):
    """
    Define a (calibrated) point for a discrete pseudomotor configuration.

    The mandatory parameters to execute the macro are: pseudo, label and pos.

    Two different scenarios exist: To define a new point or to modify an
    existing one. The controller protects from uploading repeated pos values.

    If the point is new, the default dmin and dmax parameters are used to
    construct the calibration. If no set point is provided, the current
    physical position is used instead.

    If the point already exists, the values are updated as in the previous
    case. However, if no dmin and dmax are provided, the previous
    calibration values for dmin and dmax are calculated and used to rebuild
    the calibration.

    .. note::
        The def_discr_pos macro has been included in sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the macro) may occur if
        deemed necessary by the core developers.
    """
    param_def = [
        ['pseudo', Type.PseudoMotor, None, 'Discrete pseudomotor name.'],
        ['label', Type.String, None, 'Label name.'],
        ['pos', Type.Integer, None, 'Discrete (pseudo) position.'],
        ['set', Type.Float, float('inf'), 'Continuous position.'],
        ['dmin', Type.Float, float('-inf'),
         'Delta increment used to define the minimum position.'],
        ['dmax', Type.Float, float('inf'),
         'Delta increment used to define the maximum position.'],
        ]

    def run(self, pseudo, label, pos, setpos, dmin, dmax):
        conf = DiscretePseudoMotorConfiguration(pseudo, self)
        conf.add_point(label, pos, setpos, dmin, dmax)


class udef_discr_pos(Macro):
    """
    Remove a point from a discrete pseudomotor configuration.

    .. note::
        The udef_discr_pos macro has been included in sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the macro) may occur if
        deemed necessary by the core developers.
    """
    param_def = [
        ['pseudo', Type.PseudoMotor, None, 'Discrete pseudomotor name'],
        ['label', Type.String, None, 'Label name'],
    ]

    def run(self, pseudo, label):
        conf = DiscretePseudoMotorConfiguration(pseudo, self)
        conf.remove_point(label)


class prdef_discr(Macro):
    """
    Print discrete pseudomotor configuration.

    .. note::
    The prdef_discr_pos macro has been included in sardana
    on a provisional basis. Backwards incompatible changes
    (up to and including removal of the macro) may occur if
    deemed necessary by the core developers.
    """
    param_def = [
        ['pseudo', Type.PseudoMotor, None, 'Discrete pseudomotor name'],
    ]

    def run(self, pseudo):
        conf = DiscretePseudoMotorConfiguration(pseudo, self)
        col_head_str = [['pos'], ['set'], ['min'], ['max']]
        row_head_str = []
        value_list = []

        for k, v in list(conf.items()):
            row_head_str.append(k)
            _row_values = [k]
            for i in col_head_str:
                _row_values.append(v[i[0]])
            value_list.append(_row_values)

        if len(value_list):
            # Sort by position column
            value_list = sorted(value_list, key=lambda x: x[1])
            # Transpose matrix
            value_list = list(map(list, list(zip(*value_list))))
            # Extract sorted row headers
            row_head_str = value_list[0]
            # Extract sorted values
            value_list = value_list[1:]
            table = Table(value_list, row_head_str=row_head_str,
                          col_head_str=col_head_str, col_head_width=15)
            for line in table.genOutput():
                self.output(line)
        else:
            self.output('No configuration available')
