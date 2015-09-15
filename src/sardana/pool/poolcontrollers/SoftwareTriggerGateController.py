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
from sardana.pool.pooldefs import SynchDomain, SynchValue
from sardana.util.funcgenerator import RectangularFunctionGenerator
from sardana.pool.controller import TriggerGateController

class SoftwareTriggerGateController(TriggerGateController):
    """Basic controller intended for demonstration purposes only.
    """
    gender = "Simulation"
    organization = "ALBA-Cells"
    MaxDevice = 1

    def __init__(self, inst, props, *args, **kwargs):
        """Constructor"""
        TriggerGateController.__init__(self, inst, props, *args, **kwargs)
        self.tg = {}

    def add_listener(self, listener):
        '''Backdoor method to attach listeners. It will be removed whenever 
        a proper EventChannel mechanism will be implemented'''
        self.tg[0].add_listener(listener)

    def remove_listener(self, listener):
        self.tg[0].remove_listener(listener)

    def SetAxisPar(self, axis, name, value):
        pass

    def GetAxisPar(self, axis, name):
        return None

    def SetConfiguration(self, axis, conf):
        idx = axis - 1
        tg = self.tg[idx]
        # TODO: implement nonequidistant triggering
        conf = conf[0]
        delay = conf['delay'][SynchDomain.Time][SynchValue]
        total_time = conf['total'][SynchDomain.Time][SynchValue]
        active_time = conf['active'][SynchDomain.Time][SynchValue]
        passive_time = total_time - active_time
        repeats = conf['repeats']
        tg.setOffset(delay)
        tg.setActiveInterval(active_time)
        tg.setPassiveInterval(passive_time)
        tg.setRepetitions(repeats)

    def GetConfiguration(self, axis):
        idx = axis - 1
        tg = self.tg[idx]
        # TODO: implement nonequidistant triggering
        active_time=tg.getActiveInterval(),
        passive_time=tg.getPassiveInterval()
        total_time = active_time + passive_time
        conf = [dict(delay=tg.getOffset(),
                         total=total_time,
                         active=active_time,
                         repeats=tg.getRepetitions()
                         )]
        return conf

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
        self._log.debug('PreStartOne(%d): entering...' % axis)
        idx = axis - 1
        self.tg[idx].prepare()
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
        self._log.debug('AbortOne(%d): entering...' % axis)
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
