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

from sardana.pool.controller import (
    DefaultValue,
    Description,
    FGet,
    FSet,
    MaxDimSize,
    PseudoCounterController,
    Type
)


def _get_physical_shape(pool_ctrl):
    pool = pool_ctrl.pool
    physical_id = pool_ctrl._counter_ids[0]
    physical = pool.get_element_by_id(physical_id)
    return physical.shape


class TwoDRoI(PseudoCounterController):
    """A simple pseudo counter which receives an image from a 2D experimental
       channel and returns a 2D RoI"""

    counter_roles = "TwoD",

    axis_attributes = {
        'RoI': {
            Type: (int,),
            FGet: 'getRoI',
            FSet: 'setRoI',
            Description: ("Region of Interest of image "
                          "(begin_x, end_x, begin_y, end_y)"),
            DefaultValue: [0, 0, 0, 0]
        }
    }

    def __init__(self, inst, props):
        PseudoCounterController.__init__(self, inst, props)
        self.roi = None

    def GetAxisAttributes(self, axis):
        axis_attrs = PseudoCounterController.GetAxisAttributes(self, axis)
        axis_attrs = dict(axis_attrs)
        axis_attrs['Value'][Type] = ((float, ), )
        axis_attrs['Value'][MaxDimSize] = (1024, 1024)
        return axis_attrs

    def Calc(self, axis, counter_values):
        twod = counter_values[0]
        if self.roi == [0, 0, 0, 0]:
            return twod
        twod_roi = twod[self.roi[0]:self.roi[1], self.roi[2]:self.roi[3]]
        return twod_roi

    def getRoI(self, axis):
        return self.roi

    def setRoI(self, axis, value):
        try:
            value = value.tolist()
        except AttributeError:
            pass
        if len(value) != 4:
            raise ValueError("RoI is not a list of four elements")
        if any(not isinstance(v, int) for v in value):
            raise ValueError("RoI is not a list of integers")
        if value != [0, 0, 0, 0]:
            if value[1] <= value[0]:
                raise ValueError("RoI[1] is lower or equal than RoI[0]")
            if value[3] <= value[2]:
                raise ValueError("RoI[3] is lower or equal than RoI[2]")
        self.roi = value

    def GetAxisPar(self, axis, par):
        if par == "shape":
            roi = self.roi
            if roi == [0, 0, 0, 0]:
                # getting pool (core) element - hack
                pool_ctrl = self._getPoolController()
                return _get_physical_shape(pool_ctrl)
            return [roi[1] - roi[0], roi[3] - roi[2]]
