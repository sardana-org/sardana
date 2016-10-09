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
from sardana.util.funcgenerator import FunctionGenerator
from sardana.pool.controller import TriggerGateController
from sardana.sardanathreadpool import get_thread_pool

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
        self.event_map = {}
        self.conf = {}

    def add_listener(self, axis, listener):
        '''Backdoor method to attach listeners. It will be removed whenever 
        a proper EventChannel mechanism will be implemented'''
        idx = axis - 1
        tg = self.tg[idx]
        tg.add_listener(listener)

    def remove_listener(self, axis, listener):
        idx = axis - 1
        tg = self.tg[idx]
        tg.remove_listener(listener)

    def subscribe_event(self, axis, attribute):
        self.event_map[attribute] = axis

    def unsubscribe_event(self, axis, attribute):
        self.event_map.pop(attribute)

    def event_received(self, *args, **kwargs):
        s, _, _ = args
        axis = self.event_map[s]
        idx = axis - 1
        tg = self.tg[idx]
        tg.event_received(*args, **kwargs)

    def SetConfiguration(self, axis, conf):
        idx = axis - 1
        tg = self.tg[idx]
        tg.set_configuration(conf)
        self.conf[idx] = conf

    def GetConfiguration(self, axis):
        idx = axis - 1
        # TODO: extract configuration from generators
        conf = self.conf[idx]
        return conf

    def AddDevice(self, axis):
        self._log.debug('AddDevice(%d): entering...' % axis)
        idx = axis - 1
        self.tg[idx] = FunctionGenerator()

    def StateOne(self, axis):
        """Get the dummy trigger/gate state"""
        try:
            self._log.debug('StateOne(%d): entering...' % axis)
            sta = State.On
            status = "Stopped"
            idx = axis - 1
            tg = self.tg[idx]
            if tg.is_started():
                sta = State.Moving
                status = "Started"
            if tg.is_running():
                status = "Running"
            self._log.debug('StateOne(%d): returning (%s, %s)' % \
                            (axis, sta, status))
        except Exception, e:
            print e
        return sta, status

    def PreStartOne(self, axis, value=None):
        return True

    def StartOne(self, axis):
        """Start the specified trigger
        """
        self._log.debug('StartOne(%d): entering...' % axis)
        idx = axis - 1
        tg = self.tg[idx]
        tg.start()
        get_thread_pool().add(tg.run)

    def AbortOne(self, axis):
        """Start the specified trigger
        """
        self._log.debug('AbortOne(%d): entering...' % axis)
        idx = axis - 1
        self.tg[idx].stop()

    def set_axis_par(self, axis, par, value):
        idx = axis - 1
        tg = self.tg[idx]
        if par == "active_domain":
            tg.active_domain = value
        elif par == "passive_domain":
            tg.passive_domain = value

    def get_axis_par(self, axis, par):
        idx = axis - 1
        tg = self.tg[idx]
        if par == "active_domain":
            return tg.active_domain
        elif par == "passive_domain":
            return tg.passive_domain
