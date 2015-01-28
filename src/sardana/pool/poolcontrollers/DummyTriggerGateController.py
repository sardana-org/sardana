##############################################################################
##
## This file is part of Sardana
##
## http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
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

import time

from sardana import State
from sardana.pool.controller import TriggerGateController

class DummyTriggerGateController(TriggerGateController):
    """Basic controller intended for demonstration purposes only.
    """
    gender = "Simulation"
    organization = "ALBA-Cells"
    MaxDevice = 128
    
    def __init__(self, inst, props, *args, **kwargs):
        """Constructor"""
        TriggerGateController.__init__(self, inst, props, *args, **kwargs)

    def AddDevice(self, axis):
        pass

    def DeleteDevice(self, axis):
        pass

    def PreStateAll(self):
        pass

    def StateAll(self):
        pass

    def PreStateOne(self, axis):
        pass

    def StateOne(self, axis):
        """Get the dummy trigger/gate state"""
        sta = State.On
        status = "Stopped"
        return sta, status

    def PreStartAll(self):
        pass

    def StartAll(self):
        pass

    def PreStartOne(self, axis, value=None):
        return True

    def StartOne(self, axis):
        """Start the specified trigger"""
        pass

    def AbortOne(self, axis):
        pass

    def PreReadAll(self):
        pass

    def ReadAll(self):
        pass

    def PreReadOne(self,axis):
        pass

    def ReadOne(self, axis):
        pass

    def LoadOne(self, axis, value):
        pass