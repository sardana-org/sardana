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

import time
import copy
from sardana.sardanavalue import SardanaValue
from sardana import State, DataAccess
from sardana.pool import AcqSynch
from sardana.pool.controller import CounterTimerController, Type, Access,\
    Description, Memorize, NotMemorized, Type, Description, DefaultValue, Access, FGet, FSet

import sys
sys.path.append("C:\Users\korff\Documents\Python Scripts\zhiBoxcar")
from boxcars import boxcars
	
class zhiCounterTimerController(CounterTimerController):
    """The most basic controller intended from demonstration purposes only.
    This is the absolute minimum you have to implement to set a proper counter
    controller able to get a counter value, get a counter state and do an
    acquisition.

    This example is so basic that it is not even directly described in the
    documentation"""
    ctrl_properties = {'IP': {Type: str, Description: 'The IP of the ZHI controller', DefaultValue: '127.0.0.1'},
						'port': {Type: int, Description: 'The port of the ZHI controller', DefaultValue: 8004}}
       
    
    def AddDevice(self, axis):
        pass

    def DeleteDevice(self, axis):
        pass

    def __init__(self, inst, props, *args, **kwargs):
        """Constructor"""
        super(zhiCounterTimerController,
              self).__init__(inst, props, *args, **kwargs)
        self.zhi = boxcars(self.IP, self.port, api_level=4)
        self.data = []
        self.isAquiring = False

    def ReadOne(self, axis):
        """Get the specified counter value"""
        return self.data[axis]

    def StateOne(self, axis):
        """Get the specified counter state"""
        if self.isAquiring == False:
            return State.On, "Counter is stopped"
        else:
            return State.Moving, "Counter is acquiring"

    def StartOne(self, axis, value=None):
        """acquire the specified counter"""
        #print('axis {} value {}'.format(axis,value))
        
        if axis == 0:
            self.isAquiring = True
            a = time.time()
            self.data = self.zhi.get_data(value)
            b = time.time()
            #print('elapsed time: {}'.format(b-a))
            self.isAquiring = False
    
    def StartAll(self):
        pass
    
    def LoadOne(self, axis, value, repetitions):
        pass

    def StopOne(self, axis):
        """Stop the specified counter"""
        pass