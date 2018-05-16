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

import newportXPS.XPS as XPS
import time

from sardana import State
from sardana.pool.controller import MotorController

from sardana.pool.controller import Type, Description, DefaultValue, Access, FGet, FSet, DataAccess, Memorize, Memorized


class NewportXPSController(MotorController):
    ctrl_properties = {'IP': {Type: str, Description: 'The IP of the XPS controller', DefaultValue: 'xps-controller.hhg.lab'},
						     'port': {Type: int, Description: 'The port of the XPS controller', DefaultValue: 5001},
						     }
    
    axis_attributes  = {'group': {Type: str, Description: 'Group name of the axis', DefaultValue: 'Single1', Access: DataAccess.ReadWrite, Memorized: Memorize},
                       'positioner': {Type: str, Description: 'Positioner name of the axis', DefaultValue: 'pos', Access: DataAccess.ReadWrite, Memorized: Memorize}
                       }
    
    MaxDevice = 2
    timeOut = 5000
	
    def __init__(self, inst, props, *args, **kwargs):
        super(NewportXPSController, self).__init__(
            inst, props, *args, **kwargs)

        # initialize hardware communication
        self.XPS = XPS.XPS()
        self.socketIDmove  = self.XPS.TCP_ConnectToServer(self.IP, self.port, self.timeOut)
        self.socketIDstate = self.XPS.TCP_ConnectToServer(self.IP, self.port, self.timeOut)
        self.socketIDread  = self.XPS.TCP_ConnectToServer(self.IP, self.port, self.timeOut)
        self.socketIDabort = self.XPS.TCP_ConnectToServer(self.IP, self.port, self.timeOut,1)
        self.socketSGamma  = self.XPS.TCP_ConnectToServer(self.IP, self.port, self.timeOut, 1)
                
        # do some initialization
        self._motors = {}
        self._target = {}
        self._threshold = 0.1
        

    def AddDevice(self, axis):
        self._motors[axis] = {}
        self._motors[axis]['target'] = None
        [_, resp] = self.XPS.ObjectsListGet(self.socketIDabort)
        [self._motors[axis]['group'], self._motors[axis]['positioner'], _] =  resp.split(';', 2 )
        
    def DeleteDevice(self, axis):
        del self._motors[axis]
        del self._target[axis]

    StateMap = {
        1: State.On,
        2: State.Moving,
        3: State.Fault,
    }

    def StateOne(self, axis):
        group = self._motors[axis]['group']
        positioner = self._motors[axis]['positioner']
        
        if group is None or positioner is None:
            raise ValueError('Group or positioner not set for this axis')
            
        limit_switches = MotorController.NoLimitSwitch
        target = self._motors[axis]['target']
        pos = self.ReadOne(axis)
        
        if (target is not None) and (abs(pos - target) > self._threshold):
            MOVING = True
        else:
            MOVING = False
                                        
        [_, state] = self.XPS.GroupStatusGet(self.socketIDstate, group)
        time.sleep(0.01)        
                
        if ((state >= 43) & (state <= 44)) or MOVING:
            return self.StateMap[2], 'stage is moving', limit_switches
        elif (state >= 0) & (state <= 9):
            return self.StateMap[3], 'stage not initialized', limit_switches
        elif (state >= 21) & (state <= 39):
            return self.StateMap[3], 'stage disabled', limit_switches
        elif (state >= 10) & (state <= 19):
            return self.StateMap[1], 'ready state', limit_switches
        else:
            return self.StateMap[3], 'state unknown', limit_switches
    
    def ReadOne(self, axis):
        group = self._motors[axis]['group']
        positioner = self._motors[axis]['positioner']
        
        if group is None or positioner is None:
            raise ValueError('Group or positioner not set for this axis')
            
        [_, pos] = self.XPS.GroupPositionCurrentGet(self.socketIDread, group, 1)
        time.sleep(0.01)
        
        return pos

    def StartOne(self, axis, position):
        group = self._motors[axis]['group']
        positioner = self._motors[axis]['positioner']
        
        if group is None or positioner is None:
            raise ValueError('Group or positioner not set for this axis')
        
        self.XPS.GroupMoveAbsolute(self.socketIDmove, group, [position])
        self._motors[axis]['target'] = position
        time.sleep(0.01)
        
    def StopOne(self, axis):
        group = self._motors[axis]['group']
        positioner = self._motors[axis]['positioner']
        
        if group is None or positioner is None:
            raise ValueError('Group or positioner not set for this axis')
        
        self.XPS.GroupMoveAbort(self.socketIDabort, group)
        time.sleep(0.01)
        
    def AbortOne(self, axis):
        group = self._motors[axis]['group']
        positioner = self._motors[axis]['positioner']
        
        if group is None or positioner is None:
            raise ValueError('Group or positioner not set for this axis')
        
        self.XPS.GroupMoveAbort(self.socketIDabort, group)
        time.sleep(0.01)
    
    def GetAxisPar(self, axis, name):
        name = name.lower()
        positioner = self._motors[axis]['positioner']
                
        if positioner is None:
            raise ValueError('positioner not set for this axis')
        
        if name == "acceleration" or name == "deceleration":
            [_, vel, acc, _, _] = self.XPS.PositionerSGammaParametersGet(self.socketSGamma, positioner)
            v = vel/acc
        elif name == "velocity":
            [_, v, _, _, _] = self.XPS.PositionerSGammaParametersGet(self.socketSGamma, positioner)
        elif name == "base_rate":
            v = .001
        return v

    def SetAxisPar(self, axis, name, value):
        name = name.lower()
        positioner = self._motors[axis]['positioner']

        if positioner is None:
            raise ValueError('positioner not set for this axis')
            
        if name == "acceleration" or name == "deceleration":
            [_, vel, acc, minJerk, maxJerk] = self.XPS.PositionerSGammaParametersGet(self.socketSGamma, positioner)
            self.XPS.PositionerSGammaParametersSet(self.socketSGamma, positioner, vel, value, minJerk, maxJerk)
        elif name == "velocity":
            [_, vel, acc, minJerk, maxJerk] = self.XPS.PositionerSGammaParametersGet(self.socketSGamma, positioner)
            self.XPS.PositionerSGammaParametersSet(self.socketSGamma, positioner, value, acc, minJerk, maxJerk)

    def GetAxisExtraPar(self, axis, name):
        """ Get Smaract axis particular parameters.
        @param axis to get the parameter
        @param name of the parameter to retrive
        @return the value of the parameter
        """
        name = name.lower()
        
        if name == 'group':
            result = self._motors[axis]['group']
        elif name == 'positioner':
            result = self._motors[axis]['positioner']
        else:
            raise ValueError('There is not %s attribute' % name)
        return result

    def SetAxisExtraPar(self, axis, name, value):
        """ Set Smaract axis particular parameters.
        @param axis to set the parameter
        @param name of the parameter
        @param value to be set
        """
        name = name.lower()
        if name == 'group':
            self._motors[axis]['group'] = value
        elif name == 'positioner':
            self._motors[axis]['positioner'] = value
        else:
            raise ValueError('There is not %s attribute' % name)

    