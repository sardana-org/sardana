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

"""This module contains the definition of a discrete pseudo motor controller
for the Sardana Device Pool"""

__all__ = ["DiscretePseudoMotorController"]

__docformat__ = 'restructuredtext'

import json

from sardana import DataAccess
from sardana.pool.controller import PseudoMotorController
from sardana.pool.controller import Type, Access, Description

CALIBRATION = 'Calibration'
LABELS = 'Labels'
MSG_API = 'Configuration attribute is in use. Labels and Calibration ' \
          'attributes are deprecated since version 2.5.0'


class DiscretePseudoMotorController(PseudoMotorController):
    """
    A discrete pseudo motor controller which converts physical motor
    positions to discrete values"""

    gender = "DiscretePseudoMotorController"
    model = "PseudoMotor"
    organization = "Sardana team"
    image = ""

    pseudo_motor_roles = ("DiscreteMoveable",)
    motor_roles = ("ContinuousMoveable",)

    axis_attributes = {CALIBRATION:  # type hackish until arrays supported
                       {Type: str,
                        Description: 'Flatten list of a list of triples and '
                                     '[min,cal,max]. Deprecated since '
                                     'version 2.5.0.',
                        Access: DataAccess.ReadWrite,
                        'fget': 'get%s' % CALIBRATION,
                        'fset': 'set%s' % CALIBRATION},
                       LABELS:  # type hackish until arrays supported
                       {Type: str,
                        Description: 'String list with the meaning of each '
                                     'discrete position. Deprecated since '
                                     'version 2.5.0.',
                        Access: DataAccess.ReadWrite,
                        'fget': 'get%s' % LABELS,
                        'fset': 'set%s' % LABELS},
                       'Configuration':
                       # type hackish until encoded attributes supported
                       {Type: str,
                        Description: 'String dictionary mapping the labels'
                                     ' and discrete positions',
                        Access: DataAccess.ReadWrite}
                       }

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        self._calibration = []
        self._positions = []
        self._labels = []
        self._configuration = None
        self._calibration_cfg = None
        self._positions_cfg = None
        self._labels_cfg = None

    def GetAxisAttributes(self, axis):
        axis_attrs = PseudoMotorController.GetAxisAttributes(self, axis)
        axis_attrs = dict(axis_attrs)
        axis_attrs['Position']['type'] = float
        return axis_attrs

    def CalcPseudo(self, axis, physical_pos, curr_pseudo_pos):
        if self._configuration is not None:
            positions = self._positions_cfg
            calibration = self._calibration_cfg
            labels = self._labels_cfg
        else:
            # TODO: Remove when we drop support to Labels and Calibration
            positions = self._positions
            calibration = self._calibration
            labels = self._labels

        llabels = len(labels)
        lcalibration = len(calibration)

        value = physical_pos[0]
        # case 0: nothing to translate, only round about integer the attribute
        # value
        if llabels == 0:
            return int(value)
        # case 1: only uses the labels. Available positions in POSITIONS
        elif lcalibration == 0:
            value = int(value)
            try:
                positions.index(value)
            except Exception:
                raise Exception("Invalid position.")
            else:
                return value
        # case 1+fussy: the physical position must be in one of the defined
        # ranges, and the DiscretePseudoMotor position is defined in labels
        elif llabels == lcalibration:
            for fussyPos in calibration:
                if value >= fussyPos[0] and value <= fussyPos[2]:
                    return positions[calibration.index(fussyPos)]
            # if the loop ends, current value is not in the fussy areas.
            raise Exception("Invalid position.")
        else:
            raise Exception("Bad configuration on axis attributes.")

    def CalcPhysical(self, axis, pseudo_pos, curr_physical_pos):

        if self._configuration is not None:
            positions = self._positions_cfg
            calibration = self._calibration_cfg
            labels = self._labels_cfg
        else:
            # TODO: Remove when we drop support to Labels and Calibration
            positions = self._positions
            calibration = self._calibration
            labels = self._labels

        # If Labels is well defined, the write value must be one this struct
        llabels = len(labels)
        lcalibration = len(calibration)
        value = pseudo_pos[0]

        # case 0: nothing to translate, what is written goes to the attribute
        if llabels == 0:
            return value
        # case 1: only uses the labels. Available positions in POSITIONS
        elif lcalibration == 0:
            self._log.debug("Value = %s", value)
            try:
                positions.index(value)
            except Exception:
                raise Exception("Invalid position.")
            return value
        # case 1+fussy: the write to the to the DiscretePseudoMotorController
        # is translated to the central position of the calibration.
        elif llabels == lcalibration:
            self._log.debug("Value = %s", value)
            try:
                destination = positions.index(value)
            except Exception:
                raise Exception("Invalid position.")
            self._log.debug("destination = %s", destination)
            calibrated_position = calibration[
                destination][1]  # central element
            self._log.debug("calibrated_position = %s", calibrated_position)
            return calibrated_position

    # TODO: Remove when we drop support to Labels and Calibration
    def getLabels(self, axis):
        if self._configuration is not None:
            raise ValueError(MSG_API)

        self._log.warning("Labels attribute is deprecated since version "
                          "2.5.0. Use Configuration attribute instead.")

        # hackish until we support DevVarDoubleArray in extra attrs
        labels = self._labels
        positions = self._positions
        labels_str = ""
        for i in range(len(labels)):
            labels_str += "%s:%d " % (labels[i], positions[i])
        return labels_str[:-1]  # remove the final space

    # TODO: Remove when we drop support to Labels and Calibration
    def setLabels(self, axis, value):
        if self._configuration is not None:
            raise ValueError(MSG_API)

        self._log.warning("Labels attribute is deprecated since version "
                          "2.5.0. Use Configuration attribute instead.")

        # hackish until we support DevVarStringArray in extra attrs
        labels = []
        positions = []
        for pair in value.split():
            l, p = pair.split(':')
            labels.append(l)
            positions.append(int(p))
        if len(labels) == len(positions):
            self._labels = labels
            self._positions = positions
        else:
            raise Exception("Rejecting labels: invalid structure")

    # TODO: Remove when we drop support to Labels and Calibration
    def getCalibration(self, axis):
        if self._configuration is not None:
            raise ValueError(MSG_API)
        self._log.warning("Calibration attribute is deprecated since version "
                          "2.5.0. Use Configuration attribute instead.")

        return json.dumps(self._calibration)

    # TODO: Remove when we drop support to Labels and Calibration
    def setCalibration(self, axis, value):
        if self._configuration is not None:
            raise ValueError(MSG_API)
        self._log.warning("Calibration attribute is deprecated since version "
                          "2.5.0. Use Configuration attribute instead.")

        try:
            self._calibration = json.loads(value)
        except Exception:
            raise Exception("Rejecting calibration: invalid structure")

    def getConfiguration(self, axis):
        if self._configuration is None:
            # TODO: Remove when we drop support to Labels and Calibration
            return self._getConfiguration()
        else:
            return json.dumps(self._configuration)

    # TODO: Remove when we drop support to Labels and Calibration
    def _getConfiguration(self):
        mapping = dict()
        llab = len(self._labels)
        lcal = len(self._calibration)

        if llab == 0:
            return json.dumps(mapping)
        elif lcal > 0 and lcal != llab:
            msg = 'Calibration and Labels have different length'
            raise RuntimeError(msg)

        for idx, label in enumerate(self._labels):
            pos = self._positions[idx]
            mapping[label] = {'pos': int(pos)}
            if lcal > 0:
                minimum, set, maximum = self._calibration[idx]
                mapping[label]['set'] = set
                mapping[label]['min'] = minimum
                mapping[label]['max'] = maximum

        return json.dumps(mapping)

    def setConfiguration(self, axis, value):
        try:
            mapping = json.loads(value)
            labels = []
            positions = []
            calibration = []
            for k, v in mapping.items():
                labels.append(k)
                pos = int(v['pos'])
                if pos in positions:
                    msg = 'position {0} is already used'.format(pos)
                    raise ValueError(msg)
                positions.append(pos)
                if all([x in v.keys() for x in ['min', 'set', 'max']]):
                    calibration.append([v['min'], v['set'], v['max']])
            self._labels_cfg = labels
            self._positions_cfg = positions
            self._calibration_cfg = calibration
            self._configuration = json.loads(value)
        except Exception as e:
            msg = "invalid configuration: {0}".format(e)
            raise Exception(msg)
