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

"""This file contains the code for an hypothetical Springfield motor controller
used in documentation"""

import pyagilis as agilis

from sardana import State
from sardana.pool.controller import MotorController
from sardana import DataAccess
from sardana.pool.controller import Type, Description, DefaultValue, Access, FGet, FSet


class AgilisCONEXagpController(MotorController):
    ctrl_properties = {'port': {Type: str, Description: 'The port of the rs232 device', DefaultValue: '/dev/ttyUSB0'}}

    axis_attributes = {
        "Homing" : {
                Type         : bool,
                Description  : "(de)activates the motor homing algorithm",
                DefaultValue : False,
            },
    }
    
    MaxDevice = 1
    
    def __init__(self, inst, props, *args, **kwargs):
        super(AgilisCONEXagpController, self).__init__(
            inst, props, *args, **kwargs)

        # initialize hardware communication
        self.agilis = agilis.controller.AGP(self.port)
        if self.agilis.getStatus() == 0: # not referenced
            self.agilis.home()
        # do some initialization
        self._motors = {}

    def AddDevice(self, axis):
        self._motors[axis] = True

    def DeleteDevice(self, axis):
        del self._motors[axis]

    StateMap = {
        1: State.On,
        2: State.Moving,
        3: State.Fault,
    }

    def StateOne(self, axis):
        limit_switches = MotorController.NoLimitSwitch     
        state = self.agilis.getStatus()
                
        return self.StateMap[state], 'some text', limit_switches

    def ReadOne(self, axis):
        return self.agilis.getCurrentPosition()

    def StartOne(self, axis, position):
        self.agilis.moveAbsolute(position)

    def StopOne(self, axis):
        self.agilis.stop()

    def AbortOne(self, axis):
        self.agilis.stop()
        
    def setHoming(self, axis, value):
        """Homing for given axis"""
        if value:       
            self.agilis.home()
    
    def getHoming(self, axis):
        """Homing for given axis"""       
        return False

    
