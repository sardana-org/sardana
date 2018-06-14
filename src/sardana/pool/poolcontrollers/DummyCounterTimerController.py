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
    Description, Memorize, NotMemorized


class Channel:

    def __init__(self, idx):
        self.idx = idx            # 1 based index
        self.value = 0.0
        self.is_counting = False
        self.active = True
        self.repetitions = 0
        self._counter = 0
        self.mode = AcqSynch.SoftwareTrigger
        self.buffer_values = []


class DummyCounterTimerController(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller for tests"

    gender = "Simulation"
    model = "Basic"
    organization = "Sardana team"

    MaxDevice = 1024

    StoppedMode = 0
    TimerMode = 1
    MonitorMode = 2
    CounterMode = 3

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        self._synchronization = AcqSynch.SoftwareTrigger
        self._latency_time = 0
        self.channels = self.MaxDevice * [None, ]
        self.reset()

    def reset(self):
        self.start_time = None
        self.integ_time = None
        self.monitor_count = None
        self.read_channels = {}
        self.counting_channels = {}

    def AddDevice(self, ind):
        idx = ind - 1
        self.channels[idx] = Channel(ind)

    def DeleteDevice(self, ind):
        idx = ind - 1
        self.channels[idx] = None

    def PreStateAll(self):
        pass

    def PreStateOne(self, ind):
        pass

    def StateAll(self):
        pass

    def StateOne(self, ind):
        self._log.debug('StateOne(%d): entering...' % ind)
        idx = ind - 1
        sta = State.On
        status = "Stopped"
        if ind in self.counting_channels:
            channel = self.channels[idx]
            now = time.time()
            elapsed_time = now - self.start_time
            self._updateChannelState(ind, elapsed_time)
            if channel.is_counting:
                sta = State.Moving
                status = "Acquiring"
        ret = (sta, status)
        self._log.debug('StateOne(%d): returning %s' % (ind, repr(ret)))
        return sta, status

    def _updateChannelState(self, ind, elapsed_time):
        channel = self.channels[ind - 1]
        if channel.mode == AcqSynch.SoftwareTrigger:
            if self.integ_time is not None:
                # counting in time
                if elapsed_time >= self.integ_time:
                    self._finish(elapsed_time)
            elif self.monitor_count is not None:
                # monitor counts
                v = int(elapsed_time * 100 * ind)
                if v >= self.monitor_count:
                    self._finish(elapsed_time)
        elif channel.mode in (AcqSynch.HardwareTrigger, AcqSynch.HardwareGate):
            if self.integ_time is not None:
                # counting in time
                # if elapsed_time >= self.integ_time*channel.repetitions:
                if elapsed_time > channel.repetitions * (self.integ_time +
                                                         self._latency_time):
                    # if elapsed_time >= self.integ_time:
                    self._finish(elapsed_time)

    def _updateChannelValue(self, ind, elapsed_time):
        channel = self.channels[ind - 1]

        if channel.mode == AcqSynch.SoftwareTrigger:
            if self.integ_time is not None:
                t = elapsed_time
                t = min([elapsed_time, self.integ_time])
                if ind == self._timer:
                    channel.value = t
                else:
                    channel.value = t * channel.idx
            elif self.monitor_count is not None:
                channel.value = int(elapsed_time * 100 * ind)
                if ind == self._monitor:
                    if not channel.is_counting:
                        channel.value = self.monitor_count
        elif channel.mode in (AcqSynch.HardwareTrigger, AcqSynch.HardwareGate):
            if self.integ_time is not None:
                t = elapsed_time
                n = int(t / self.integ_time)
                cp = 0
                if n > channel.repetitions:
                    cp = n - channel.repetitions
                n = n - channel._counter - cp
                t = self.integ_time
                if ind == self._timer:
                    channel.buffer_values = [t] * n
                else:
                    channel.buffer_values = [t * channel.idx] * n

    def _finish(self, elapsed_time, ind=None):
        if ind is None:
            for ind, channel in self.counting_channels.items():
                channel.is_counting = False
                self._updateChannelValue(ind, elapsed_time)
        else:
            if ind in self.counting_channels:
                channel = self.counting_channels[ind]
                channel.is_counting = False
                self._updateChannelValue(ind, elapsed_time)
                self.counting_channels.pop(ind)
            else:
                channel = self.channels[ind - 1]
                channel.is_counting = False

    def PreReadAll(self):
        self.read_channels = {}

    def PreReadOne(self, ind):
        channel = self.channels[ind - 1]
        self.read_channels[ind] = channel

    def ReadAll(self):
        # if in acquisition then calculate the values to return
        if self.counting_channels:
            now = time.time()
            elapsed_time = now - self.start_time
            for ind, channel in self.read_channels.items():
                self._updateChannelState(ind, elapsed_time)
                if channel.is_counting:
                    self._updateChannelValue(ind, elapsed_time)

    def ReadOne(self, ind):
        self._log.debug('ReadOne(%d): entering...' % ind)
        channel = self.read_channels[ind]
        ret = None
        if channel.mode in (AcqSynch.HardwareTrigger, AcqSynch.HardwareGate):
            values = copy.deepcopy(channel.buffer_values)
            ret = []
            for v in values:
                ret.append(SardanaValue(v))
            channel.buffer_values.__init__()
            channel._counter = channel._counter + len(values)
        elif channel.mode == AcqSynch.SoftwareTrigger:
            v = channel.value
            ret = SardanaValue(v)
        self._log.debug('ReadOne(%d): returning %s' % (ind, repr(ret)))
        return ret

    def PreStartAll(self):
        self.counting_channels = {}

    def PreStartOne(self, ind, value=None):
        self._log.debug('PreStartOne(%d): entering...' % ind)
        idx = ind - 1
        channel = self.channels[idx]
        channel.value = 0.0
        channel._counter = 0
        channel.buffer_values = []
        self.counting_channels[ind] = channel
        return True

    def StartOne(self, ind, value=None):
        self._log.debug('StartOne(%d): entering...' % ind)
        self.counting_channels[ind].is_counting = True

    def StartAll(self):
        self.start_time = time.time()

    def LoadOne(self, ind, value, repetitions):
        if value > 0:
            self.integ_time = value
            self.monitor_count = None
        else:
            self.integ_time = None
            self.monitor_count = -value
        self._repetitions = repetitions
        for channel in self.channels:
            if channel:
                channel.repetitions = repetitions

    def AbortOne(self, ind):
        now = time.time()
        if ind in self.counting_channels:
            elapsed_time = now - self.start_time
            self._finish(elapsed_time, ind=ind)

    def GetCtrlPar(self, par):
        if par == 'synchronization':
            return self._synchronization
        elif par == 'latency_time':
            return self._latency_time

    def SetCtrlPar(self, par, value):
        if par == 'synchronization':
            self._synchronization = value
            for channel in self.channels:
                if channel:
                    channel.mode = value
