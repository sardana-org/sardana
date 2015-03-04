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


from sardana import State
from sardana.util.funcgenerator import RectangularFunctionGenerator
from sardana.pool.controller import TriggerGateController

class DummyTriggerGateController(TriggerGateController):
    """Basic controller intended for demonstration purposes only.
    """
    gender = "Simulation"
    organization = "ALBA-Cells"
    MaxDevice = 1
    
    def __init__(self, inst, props, *args, **kwargs):
        """Constructor"""
        TriggerGateController.__init__(self, inst, props, *args, **kwargs)
        self.tg = {}
        
#     def add_listener(self, listener):
#         '''Backdoor method to attach listeners. It will be removed whenever 
#         a proper EventChannel mechanism will be implemented'''
#         self.tg[0].add_listener(listener)
        
    def SetAxisPar(self, axis, name, value):
        idx = axis - 1
        tg = self.tg[idx]
        name = name.lower()
        if name == 'offset':
            tg.setOffset(value)
        elif name == 'active_period':
            tg.setActivePeriod(value)
        elif name == 'passive_period':
            tg.setPassivePeriod(value)
        elif name == 'repetitions':
            tg.setRepetitions(value)
            
    def GetAxisPar(self, axis, name):
        idx = axis - 1
        tg = self.tg[idx]
        name = name.lower()
        if name == 'offset':
            v = tg.setOffset()
        elif name == 'active_period':
            v = tg.setActivePeriod()
        elif name == 'passive_period':
            v = tg.getPassivePeriod()
        elif name == "repetitions":
            v = tg.getRepetitions()
        return v

    def AddDevice(self, axis):
        self._log.debug('AddDevice(%d): entering...' % axis)
        idx = axis - 1
        self.tg[idx] = RectangularFunctionGenerator()

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
        self._log.debug('StateOne(%d): entering...' % axis)
        sta = State.On
        status = "Stopped"
        idx = axis - 1
        if self.tg[idx].isGenerating():
            sta = State.Moving
            status = "Moving"
        self._log.debug('StateOne(%d): returning (%s, %s)' % (axis, sta, status))
        return sta, status

    def PreStartAll(self):
        pass

    def StartAll(self):
        pass

    def PreStartOne(self, axis, value=None):
        return True

    def StartOne(self, axis):
        """Start the specified trigger
        """
        self._log.debug('StartOne(%d): entering...' % axis)
        idx = axis - 1
        self.tg[idx].start()        

    def AbortOne(self, axis):
        """Start the specified trigger
        """
        self._log.debug('StartOne(%d): entering...' % axis)
        idx = axis - 1
        self.tg[idx].stop()

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
