##############################################################################
#
# This file is part of Sardana
#
# http://www.sardana-controls.org/
##
# Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
#
# Sardana is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sardana is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from sardana import State
from sardana.pool.controller import CounterTimerController, Type,\
    Description, Access, DataAccess
from taurus import Attribute


class TaurusCounterTimerController(CounterTimerController):
    """
    This controller provides interface to use Taurus Attributes.
    """

    axis_attributes = {
        "TaurusAttribute": {Type: str,
                            Description: 'Taurus attribute ',
                            Access: DataAccess.ReadWrite}
    }

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        self._axes_taurus_attr = {}

    def AddDevice(self, axis):
        self._axes_taurus_attr[axis] = ''

    def DeleteDevice(self, axis):
        self._axes_taurus_attr.pop(axis)

    def LoadOne(self, axis, value, repetitions, latency):
        pass

    def StateOne(self, axis):
        state = State.On
        status_string = 'The state is ON.'
        return state, status_string

    def StartOne(self, axis, _):
        pass

    def StartAll(self):
        pass

    def ReadOne(self, axis):
        attr = Attribute(self._axes_taurus_attr[axis])
        value = attr.read().rvalue
        try:
            value = value.magnitude
        except:
            pass
        return value

    def AbortOne(self, axis):
        pass

    def getTaurusAttribute(self, axis):
        return self._axes_taurus_attr[axis]

    def setTaurusAttribute(self, axis, value):
        self._axes_taurus_attr[axis] = value
