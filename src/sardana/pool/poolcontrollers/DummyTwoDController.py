##############################################################################
##
# This file is part of Sardana
##
# http://www.tango-controls.org/static/sardana/latest/doc/html/axisex.html
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

import re
import sys
import time

import numpy
try:
    import h5py
except ImportError:
    pass

from sardana import State
from sardana.pool.controller import TwoDController, Referable, MaxDimSize


def gauss(x, mean, ymax, fwhm, yoffset=0):
    return yoffset + ymax * numpy.power(2, -4 * ((x - mean) / fwhm)**2)


class Channel:

    def __init__(self, idx):
        self.idx = idx            # 1 based axisex
        self.value = []
        self.is_counting = False
        self.active = True
        self.amplitude = BaseValue('1.0')
        self.value_ref_pattern = "h5file:///tmp/dummy2d_default_{index}.h5"
        self.value_ref_enabled = True


class BaseValue(object):

    def __init__(self, value):
        self.raw_value = value
        self.init()

    def init(self):
        self.value = float(self.raw_value)

    def get(self):
        return self.value

    def get_value_name(self):
        return self.raw_value


class TangoValue(BaseValue):

    def init(self):
        import PyTango
        self.attr_proxy = PyTango.AttributeProxy(self.raw_value)

    def get(self):
        return self.attr_proxy.read().value


class DummyTwoDController(TwoDController, Referable):
    "This class is the Tango Sardana OneDController controller for tests"

    gender = "Simulation"
    model = "Basic"
    organization = "Sardana team"

    MaxDevice = 1024

    BufferSize = 1024, 1024

    axis_attributes = {
        'Amplitude': {
            'type': str,
            'fget': 'getAmplitude',
            'fset': 'setAmplitude',
            'description': 'Amplitude. Maybe a number or a tango attribute(must start with tango://)',
            'defaultvalue': '1.0'},
    }

    def __init__(self, inst, props, *args, **kwargs):
        TwoDController.__init__(self, inst, props, *args, **kwargs)
        self.channels = self.MaxDevice * [None, ]
        self.reset()

    def GetAxisAttributes(self, axis):
        # the default max shape for 'value' is (16*1024,). We don't need so much
        # so we set it to BufferSize
        attrs = super(DummyTwoDController, self).GetAxisAttributes(axis)
        attrs['Value'][MaxDimSize] = self.BufferSize
        return attrs

    def reset(self):
        self.start_time = None
        self.integ_time = None
        self.monitor_count = None
        self.img_idx = None
        self.read_channels = {}
        self.counting_channels = {}

    def AddDevice(self, axis):
        idx = axis - 1
        self.channels[idx] = channel = Channel(axis)
        channel.value = numpy.zeros(self.BufferSize, dtype=numpy.float64)

    def DeleteDevice(self, axis):
        idx = axis - 1
        self.channels[idx] = None

    def PreStateAll(self):
        pass

    def PreStateOne(self, axis):
        pass

    def StateAll(self):
        pass

    def StateOne(self, axis):
        idx = axis - 1
        sta = State.On
        status = "Stopped"
        if axis in self.counting_channels:
            channel = self.channels[idx]
            now = time.time()
            elapsed_time = now - self.start_time
            self._updateChannelState(axis, elapsed_time)
            if channel.is_counting:
                sta = State.Moving
                status = "Acquiring"
                self._updateChannelValue(axis, elapsed_time)
        return sta, status

    def _updateChannelState(self, axis, elapsed_time):
        channel = self.channels[axis - 1]
        if self.integ_time is not None:
            # counting in time
            if elapsed_time >= self.integ_time:
                self._finish(elapsed_time)
        elif self.monitor_count is not None:
            # monitor counts
            v = int(elapsed_time * 100 * axis)
            if v >= self.monitor_count:
                self._finish(elapsed_time)

    def _updateChannelValue(self, axis, elapsed_time):
        channel = self.channels[axis - 1]
        t = elapsed_time
        if self.integ_time is not None and not channel.is_counting:
            t = self.integ_time
        x = numpy.linspace(-10, 10, self.BufferSize[0])
        y = numpy.linspace(-10, 10, self.BufferSize[1])
        x, y = numpy.meshgrid(x, y)
        amplitude = axis * t * channel.amplitude.get()
        channel.value = gauss(x, 0, amplitude, 4) * gauss(y, 0, amplitude, 4)

    def _finish(self, elapsed_time, axis=None):
        if axis is None:
            for axis, channel in self.counting_channels.items():
                channel.is_counting = False
                self._updateChannelValue(axis, elapsed_time)
        else:
            if axis in self.counting_channels:
                channel = self.counting_channels[axis]
                channel.is_counting = False
                self._updateChannelValue(axis, elapsed_time)
            else:
                channel = self.channels[axis - 1]
                channel.is_counting = False
        self.counting_channels = {}


    def ReadOne(self, axis):
        self._log.debug("ReadOne(%s)", axis)
        return self.read_channels[axis].value

    def RefOne(self, axis):
        self._log.debug("RefOne(%s)", axis)
        idx = axis - 1
        channel = self.channels[idx]
        value_ref_pattern = channel.value_ref_pattern
        if value_ref_pattern is None:
            value_ref_pattern = "h5file:///tmp/dummy2d_default_{index}.h5"
        try:
            value_ref_uri = value_ref_pattern.format(index=self.img_idx)
        except Exception:
            value_ref_uri = value_ref_pattern
            msg = ("Not able to format value reference template "
                   "with index. Trying to use directly the template...")
            self._log.warning(msg, exc_info=True)
        match_res = re.match(r"h5file://(?P<path>\S+)::(?P<dataset>\S+)",
                             value_ref_uri)
        if match_res is None:
            match_res = re.match(r"h5file://(?P<path>\S+)", value_ref_uri)
        if match_res is None:
            raise Exception("invalid value reference template")
        path = match_res.group("path")
        try:
            dataset_name = match_res.group("dataset")
        except IndexError:
            dataset_name = "dataset"
        if "h5py" in sys.modules:
            h5f = h5py.File(path, "w")
            img = self.read_channels[axis].value
            h5f.create_dataset(dataset_name, data=img)
        else:
            msg = "Not able to store h5 file (h5py is not available)"
            self._log.warning(msg)
        ref = "h5file:" + path + "::" + dataset_name
        return ref

    def PreStartAll(self):
        self.counting_channels = {}
        self.read_channels = {}

    def PreStartOne(self, axis, value):
        idx = axis - 1
        channel = self.channels[idx]
        channel.value = 0.0
        self.counting_channels[axis] = channel
        self.read_channels[axis] = channel
        return True

    def StartOne(self, axis, value):
        self.img_idx += 1
        self.counting_channels[axis].is_counting = True

    def StartAll(self):
        self.start_time = time.time()

    def PrepareOne(self, axis, value, repetitions, latency, nb_starts):
        self.img_idx = -1

    def LoadOne(self, axis, value):
        idx = axis - 1
        if value > 0:
            self.integ_time = value
            self.monitor_count = None
        else:
            self.integ_time = None
            self.monitor_count = -value

    def AbortOne(self, axis):
        now = time.time()
        if axis in self.counting_channels:
            elapsed_time = now - self.start_time
            self._finish(elapsed_time, axis=axis)

    def getAmplitude(self, axis):
        idx = axis - 1
        channel = self.channels[idx]
        return channel.amplitude.get_value_name()

    def setAmplitude(self, axis, value):
        idx = axis - 1
        channel = self.channels[idx]

        klass = BaseValue
        if value.startswith("tango://"):
            klass = TangoValue
        channel.amplitude = klass(value)

    def SetAxisPar(self, axis, parameter, value):
        idx = axis - 1
        channel = self.channels[idx]
        if parameter == "value_ref_pattern":
            channel.value_ref_pattern = value
        elif parameter == "value_ref_enabled":
            channel.value_ref_enabled = value
