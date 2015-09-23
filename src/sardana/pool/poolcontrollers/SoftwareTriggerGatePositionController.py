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
import numpy as np
from sardana import State
from sardana.pool.pooldefs import SynchDomain, SynchParam
from sardana.util.funcgenerator import PositionFunctionGenerator
from sardana.pool.controller import TriggerGateController
from sardana.pool.pooltriggergate import TGEventType

class SoftwareTriggerGatePositionController(TriggerGateController):
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

    def SetConfiguration(self, axis, configuration):
        idx = axis - 1
        tg = self.tg[idx]
        self.conf[idx] = configuration
        # TODO: implement nonequidistant triggering
        event_values = []
        event_conditions = []
        event_types = []
        event_ids = []
        event_id = 0
        for group in configuration:
            repeats = group[SynchParam.Repeats]
            initial = group[SynchParam.Initial][SynchDomain.Position]
            for repeat in xrange(repeats):
                event_values.append(initial)
                event_types.append(TGEventType.Active)
                active = group[SynchParam.Active][SynchDomain.Position]
                # determine the event conditions
                comparison = np.greater_equal
                if active < 0:
                    comparison  = np.less_equal
                event_conditions.extend([comparison, comparison])
                final = initial + active
                event_values.append(final)
                event_types.append(TGEventType.Passive)
                event_ids.extend([event_id, event_id])
                total = group[SynchParam.Total][SynchDomain.Position]
                initial = initial + total
                event_id += 1
                repeat += 1
        tg.setConfiguration(event_values, event_conditions, event_types,\
                            event_ids)

    def GetConfiguration(self, axis):
        idx = axis - 1
        return self.conf[idx]

    def AddDevice(self, axis):
        self._log.debug('AddDevice(%d): entering...' % axis)
        idx = axis - 1
        self.tg[idx] = PositionFunctionGenerator()

    def GetDevice(self, axis):
        idx = axis - 1
        return self.tg[idx]

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