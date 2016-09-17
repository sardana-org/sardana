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
from sardana.util.funcgenerator import RectangularFunctionGenerator,\
                                       PositionFunctionGenerator
from sardana.pool.controller import TriggerGateController
from sardana.pool.pooltriggergate import TGEventType

class SoftwareTriggerGateController(TriggerGateController):
    """Basic controller intended for demonstration purposes only.
    """
    gender = "Simulation"
    organization = "ALBA-Cells"
    MaxDevice = 1

    def __init__(self, inst, props, *args, **kwargs):
        """Constructor"""
        TriggerGateController.__init__(self, inst, props, *args, **kwargs)
        # store position based generators per axis
        self.pos_generator = {}
        # store time based generators per axis
        self.time_generator = {}
        # store generator currently being used per axis
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

    def _SetConfigurationPosition(self, tg, conf):
        event_values = []
        event_conditions = []
        event_types = []
        event_ids = []
        event_id = 0
        for group in conf:
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

    def _SetConfigurationTime(self, tg, conf):
        # TODO: implement nonequidistant triggering
        conf = conf[0]
        delay = conf[SynchParam.Delay][SynchDomain.Time]
        total_time = conf[SynchParam.Total][SynchDomain.Time]
        active_time = conf[SynchParam.Active][SynchDomain.Time]
        passive_time = total_time - active_time
        repeats = conf[SynchParam.Repeats]
        tg.setOffset(delay)
        tg.setActiveInterval(active_time)
        tg.setPassiveInterval(passive_time)
        tg.setRepetitions(repeats)

    def SetConfiguration(self, axis, conf):
        idx = axis - 1
        total_param = conf[0][SynchParam.Total]
        if total_param.has_key(SynchDomain.Position):
            tg = self.pos_generator[idx]
            self._SetConfigurationPosition(tg, conf)

        elif total_param.has_key(SynchDomain.Time):
            tg = self.time_generator[idx]
            self._SetConfigurationTime(tg, conf)
        else:
            msg = 'Synchronization must be defined in either Position or' + \
                  ' Time domain.'
            raise ValueError(msg)
        self.tg[idx] = tg
        self.conf[idx] = conf

    def GetConfiguration(self, axis):
        idx = axis - 1
        # TODO: extract configuration from generators
        conf = self.conf[idx]
        return conf

    def AddDevice(self, axis):
        self._log.debug('AddDevice(%d): entering...' % axis)
        idx = axis - 1
        self.time_generator[idx] = self.tg[idx] = RectangularFunctionGenerator()
        self.pos_generator[idx] = PositionFunctionGenerator()

    def StateOne(self, axis):
        """Get the dummy trigger/gate state"""
        self._log.debug('StateOne(%d): entering...' % axis)
        sta = State.On
        status = "Stopped"
        idx = axis - 1
        if self.tg[idx].isGenerating():
            sta = State.Moving
            status = "Moving"
        self._log.debug('StateOne(%d): returning (%s, %s)' % \
                        (axis, sta, status))
        return sta, status

    def PreStartOne(self, axis, value=None):
        self._log.debug('PreStartOne(%d): entering...' % axis)
        idx = axis - 1
        tg = self.tg[idx]
        tg.prepare()
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
        self.tg[idx].stop()    def set_axis_par(self, axis, par, value):
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