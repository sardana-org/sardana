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
import copy

import numpy
try:
    import h5py
except ImportError:
    pass

from sardana import State
from sardana.pool import AcqSynch
from sardana.pool.controller import TwoDController, Referable, \
    Type, Description, MaxDimSize, FGet, FSet, DefaultValue


def gauss(x, mean, ymax, fwhm, yoffset=0):
    return yoffset + ymax * numpy.power(2, -4 * ((x - mean) / fwhm)**2)


def generate_img(x_size, y_size, amplitude):
    x = numpy.linspace(-10, 10, x_size)
    y = numpy.linspace(-10, 10, y_size)
    x, y = numpy.meshgrid(x, y)
    img = (gauss(x, 0, amplitude, 4) * gauss(y, 0, amplitude, 4))
    return img


def generate_ref(pattern, idx):
    if pattern is None or pattern == "":
        pattern = "h5file:///tmp/dummy2d_default_{index}.h5"
    msg = None
    try:
        uri = pattern.format(index=idx)
    except Exception:
        uri = pattern
        msg = ("Not able to format value reference template "
               "with index. Trying to use directly the template...")
    match_res = re.match(
        r"(?P<scheme>h5file)://(?P<path>\S+)::(?P<dataset>\S+)",
        uri)
    if match_res is None:
        match_res = re.match(
            r"(?P<scheme>(h5file|file))://(?P<path>\S+)",
            uri)
    if match_res is None:
        raise Exception("invalid value reference template")
    scheme = match_res.group("scheme")
    path = match_res.group("path")
    try:
        dataset_name = match_res.group("dataset")
    except IndexError:
        if scheme == "h5file":
            dataset_name = "dataset"
        else:
            dataset_name = None
    return scheme, path, dataset_name, msg


def save_img(img, path, dataset_name):
    msg = None
    if "h5py" not in sys.modules:
        msg = "Not able to store h5 file (h5py is not available)"
    try:
        h5f = h5py.File(path, "w")
        h5f.create_dataset(dataset_name, data=img)
    except Exception:
        msg = "Not able to store h5 file."
    return msg


class Channel:

    def __init__(self, idx):
        self.idx = idx            # 1 based index
        self.value = []
        self.value_ref = None
        self.is_counting = False
        self.acq_idx = 0
        self.buffer_values = []
        self.buffer_value_refs = []
        self.amplitude = BaseValue('1.0')
        self.saving_enabled = False
        self.value_ref_pattern = "h5file:///tmp/dummy2d_default_{index}.h5"
        self.value_ref_enabled = False
        self.roi = [0, 0, 0, 0]


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


class BasicDummyTwoDController(TwoDController):
    """This class represents a basic, dummy Sardana TwoD controller."""

    gender = "Simulation"
    model = "Basic"
    organization = "Sardana team"

    MaxDevice = 1024

    BufferSize = 1024, 1024

    default_latency_time = 0.0

    ctrl_attributes = {
        "Synchronizer": {
                Type: str,
                Description: ("Hardware (external) emulated synchronizer. "
                              "Can be any of dummy trigger/gate elements "
                              "from the same pool.")
            },
    }

    axis_attributes = {
        'Amplitude': {
            Type: str,
            FGet: 'getAmplitude',
            FSet: 'setAmplitude',
            Description: ("Amplitude. Maybe a number or a tango attribute "
                          "(must start with tango://)"),
            DefaultValue: '1.0'
        },
        'RoI': {
            Type: (int,),
            FGet: 'getRoI',
            FSet: 'setRoI',
            Description: ("Region of Interest of image "
                          "(begin_x, end_x, begin_y, end_y)"),
            DefaultValue: [0, 0, 0, 0]
        }
    }

    def __init__(self, inst, props, *args, **kwargs):
        TwoDController.__init__(self, inst, props, *args, **kwargs)
        self.channels = self.MaxDevice * [None, ]
        self.start_time = None
        self.integ_time = None
        self.repetitions = None
        self.latency_time = None
        self.acq_cycle_time = None  # integ_time + latency_time
        self.estimated_duration = None
        self.start_idx = None
        self._synchronization = AcqSynch.SoftwareTrigger
        self.read_channels = {}
        self.counting_channels = {}
        # name of synchronizer element
        self._synchronizer = None
        # synchronizer element (core)
        self.__synchronizer_obj = None
        # flag whether the controller was armed for hardware synchronization
        self._armed = False

    def GetAxisAttributes(self, axis):
        # the default max shape for 'value' is (16*1024,).
        # We don't need so much so we set it to BufferSize
        attrs = super(BasicDummyTwoDController, self).GetAxisAttributes(axis)
        attrs['Value'][MaxDimSize] = self.BufferSize
        return attrs

    def AddDevice(self, axis):
        idx = axis - 1
        self.channels[idx] = channel = Channel(axis)
        channel.value = numpy.zeros(self.BufferSize, dtype=numpy.float64)

    def DeleteDevice(self, axis):
        idx = axis - 1
        self.channels[idx] = None

    def PrepareOne(self, axis, value, repetitions, latency, nb_starts):
        self.start_idx = -1

    def LoadOne(self, axis, integ_time, repetitions, latency_time):
        self.integ_time = integ_time
        self.repetitions = repetitions
        self.latency_time = latency_time
        self.acq_cycle_time = acq_cycle_time = integ_time + latency_time
        self.estimated_duration = acq_cycle_time * repetitions - latency_time

    def PreStartAll(self):
        self.counting_channels = {}
        self.read_channels = {}
        self.start_idx += 1

    def PreStartOne(self, axis, value):
        idx = axis - 1
        channel = self.channels[idx]
        channel.value = None
        channel.acq_idx = 0
        channel.buffer_values = []
        self.counting_channels[axis] = channel
        self.read_channels[axis] = channel
        return True

    def StartOne(self, axis, value):
        if self._synchronization in (AcqSynch.SoftwareStart,
                                     AcqSynch.SoftwareTrigger):
            self.counting_channels[axis].is_counting = True

    def StartAll(self):
        if self._synchronization in (AcqSynch.HardwareStart,
                                     AcqSynch.HardwareTrigger,
                                     AcqSynch.HardwareGate):
            self._connect_hardware_synchronization()
            self._armed = True
        else:
            self.start_time = time.time()

    def _updateChannelState(self, axis, elapsed_time):
        if self._synchronization == AcqSynch.SoftwareTrigger:
            if self.integ_time is not None:
                # counting in time
                if elapsed_time >= self.integ_time:
                    self._finish(elapsed_time)
        elif self._synchronization in (AcqSynch.HardwareTrigger,
                                       AcqSynch.HardwareGate,
                                       AcqSynch.HardwareStart,
                                       AcqSynch.SoftwareStart):
            if self.integ_time is not None:
                # counting in time
                if elapsed_time > self.estimated_duration:
                    self._finish(elapsed_time)

    def StateOne(self, axis):
        idx = axis - 1
        sta = State.On
        status = "Stopped"
        if self._armed:
            sta = State.Moving
            status = "Armed"
        elif axis in self.counting_channels and self.start_time is not None:
            channel = self.channels[idx]
            now = time.time()
            elapsed_time = now - self.start_time
            self._updateChannelState(axis, elapsed_time)
            if channel.is_counting:
                sta = State.Moving
                status = "Acquiring"
                # TODO: do it only once at the end
                self._updateChannelValue(axis, elapsed_time)
        return sta, status

    def _updateChannelValue(self, axis, elapsed_time):
        channel = self.channels[axis - 1]
        if channel.acq_idx == self.repetitions:
            return
        x_size = self.BufferSize[0]
        y_size = self.BufferSize[1]
        amplitude = axis * self.integ_time * channel.amplitude.get()
        img = generate_img(x_size, y_size, amplitude)
        roi = channel.roi
        if roi != [0, 0, 0, 0]:
            img = img[roi[0]:roi[1], roi[2]:roi[3]]
        if self._synchronization == AcqSynch.SoftwareTrigger:
            channel.value = img
            channel.acq_idx += 1
        elif self._synchronization in (AcqSynch.HardwareTrigger,
                                       AcqSynch.HardwareGate,
                                       AcqSynch.HardwareStart,
                                       AcqSynch.SoftwareStart):
            acq_cycle_time = self.acq_cycle_time
            nb_elapsed_acq, resting = divmod(elapsed_time, acq_cycle_time)
            nb_elapsed_acq = int(nb_elapsed_acq)
            # do not wait the last latency_time
            if (nb_elapsed_acq == self.repetitions - 1
                    and resting > self.integ_time):
                nb_elapsed_acq += 1
            if nb_elapsed_acq > self.repetitions:
                nb_elapsed_acq = self.repetitions
            nb_new_acq = nb_elapsed_acq - channel.acq_idx
            if nb_new_acq == 0:
                return
            channel.buffer_values.extend([img] * nb_new_acq)
            channel.acq_idx += nb_new_acq

    def ReadOne(self, axis):
        self._log.debug('ReadOne(%d): entering...' % axis)
        try:
            channel = self.read_channels[axis]
        except KeyError:
            # TODO: After SEP17 this won't be necessary anymore.
            msg = "no acquisition done on axis {0} so far".format(axis)
            raise RuntimeError(msg)
        ret = None
        if self._synchronization in (AcqSynch.HardwareTrigger,
                                     AcqSynch.HardwareGate,
                                     AcqSynch.HardwareStart,
                                     AcqSynch.SoftwareStart):
            values = copy.deepcopy(channel.buffer_values)
            channel.buffer_values.__init__()
            ret = values
        elif self._synchronization == AcqSynch.SoftwareTrigger:
            ret = channel.value
        self._log.debug('ReadOne(%d): returning %s' % (axis, repr(ret)))
        return ret

    def _finish(self, elapsed_time, axis=None):
        if axis is None:
            for axis, channel in list(self.counting_channels.items()):
                channel.is_counting = False
                self._updateChannelValue(axis, elapsed_time)
        elif axis in self.counting_channels:
            channel = self.counting_channels[axis]
            channel.is_counting = False
            self._updateChannelValue(axis, elapsed_time)
            self.counting_channels.pop(axis)
        if self._synchronization in (AcqSynch.HardwareStart,
                                     AcqSynch.HardwareTrigger,
                                     AcqSynch.HardwareGate):
            self._disconnect_hardware_synchronization()
            self._armed = False
        self.start_time = None

    def AbortOne(self, axis):
        if axis not in self.counting_channels:
            return
        now = time.time()
        if self.start_time is not None:
            elapsed_time = now - self.start_time
        else:
            elapsed_time = 0
        self._finish(elapsed_time, axis)

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

    def getRoI(self, axis):
        idx = axis - 1
        channel = self.channels[idx]
        return channel.roi

    def setRoI(self, axis, value):
        idx = axis - 1
        channel = self.channels[idx]
        try:
            value = value.tolist()
        except AttributeError:
            pass
        if len(value) != 4:
            raise ValueError("RoI is not a list of four elements")
        if any(not isinstance(v, int) for v in value):
            raise ValueError("RoI is not a list of integers")
        if value != [0, 0, 0, 0]:
            if value[1] <= value[0]:
                raise ValueError("RoI[1] is lower or equal than RoI[0]")
            if value[3] <= value[2]:
                raise ValueError("RoI[3] is lower or equal than RoI[2]")
        x_dim = self.BufferSize[0]
        if value[0] > (x_dim - 1):
            raise ValueError(
                "RoI[0] exceeds detector X dimension - 1 ({})".format(
                    x_dim - 1))
        if value[1] > x_dim:
            raise ValueError(
                "RoI[1] exceeds detector X dimension ({})".format(x_dim))
        y_dim = self.BufferSize[1]
        if value[2] > (y_dim - 1):
            raise ValueError(
                "RoI[2] exceeds detector Y dimension - 1 ({})".format(
                    y_dim - 1))
        if value[3] > y_dim:
            raise ValueError(
                "RoI[3] exceeds detector Y dimension ({})".format(y_dim))
        channel.roi = value

    def GetCtrlPar(self, par):
        if par == "synchronization":
            return self._synchronization
        elif par == "latency_time":
            return self.default_latency_time

    def SetCtrlPar(self, par, value):
        if par == "synchronization":
            self._synchronization = value

    def GetAxisPar(self, axis, par):
        idx = axis - 1
        channel = self.channels[idx]
        if par == "shape":
            roi = channel.roi
            if roi == [0, 0, 0, 0]:
                return self.BufferSize
            return [roi[1] - roi[0], roi[3] - roi[2]]

    def getSynchronizer(self):
        if self._synchronizer is None:
            return "None"
        else:
            # get synchronizer object to only check it exists
            self._synchronizer_obj
            return self._synchronizer

    def setSynchronizer(self, synchronizer):
        if synchronizer == "None":
            synchronizer = None
        self._synchronizer = synchronizer
        self.__synchronizer_obj = None  # invalidate cache

    @property
    def _synchronizer_obj(self):
        """Get synchronizer object with cache mechanism.

        If synchronizer object is not cached ("""
        if self.__synchronizer_obj is not None:
            return self.__synchronizer_obj
        synchronizer = self._synchronizer
        if synchronizer is None:
            msg = "Hardware (external) emulated synchronizer is not set"
            raise ValueError(msg)
        # getting pool (core) element - hack
        pool_ctrl = self._getPoolController()
        pool = pool_ctrl.pool
        try:
            synchronizer_obj = pool.get_element_by_name(synchronizer)
        except Exception:
            try:
                synchronizer_obj = pool.get_element_by_full_name(synchronizer)
            except Exception:
                msg = "Unknown synchronizer {0}".format(synchronizer)
                raise ValueError(msg)
        self.__synchronizer_obj = synchronizer_obj
        return synchronizer_obj

    def _connect_hardware_synchronization(self):
        # obtain dummy trigger/gate controller (plugin) instance - hack
        tg_ctrl = self._synchronizer_obj.controller.ctrl
        idx = self._synchronizer_obj.axis - 1
        func_generator = tg_ctrl.tg[idx]
        func_generator.add_listener(self)

    def _disconnect_hardware_synchronization(self):
        # obtain dummy trigger/gate controller (plugin) instance - hack
        tg_ctrl = self._synchronizer_obj.controller.ctrl
        idx = self._synchronizer_obj.axis - 1
        func_generator = tg_ctrl.tg[idx]
        func_generator.remove_listener(self)

    def event_received(self, src, type_, value):
        """Callback for dummy trigger/gate function generator events
        e.g. start, active passive
        """
        # for the moment only react on first trigger
        if type_.name.lower() == "start":
            self._armed = False
            for axis, channel in self.counting_channels.items():
                channel.is_counting = True
            self.start_time = time.time()


class DummyTwoDController(BasicDummyTwoDController, Referable):
    """This class is the Tango Sardana TwoDController controller for tests"""

    model = "Best"

    axis_attributes = dict(BasicDummyTwoDController.axis_attributes)
    axis_attributes.update(
        {
             "SavingEnabled": {
                Type: bool,
                FGet: "isSavingEnabled",
                FSet: "setSavingEnabled",
                Description: ("Enable/disable saving of images in HDF5 files."
                              " Use with care in high demanding (fast)"
                              " acquisitions. Trying to save at high rate may"
                              " hang the acquisition process.")
             }
        }
    )

    def __init__(self, inst, props, *args, **kwargs):
        BasicDummyTwoDController.__init__(self, inst, props, *args, **kwargs)

    def PrepareOne(self, axis, value, repetitions, latency, nb_starts):
        BasicDummyTwoDController.PrepareOne(self, axis, value, repetitions,
                                            latency, nb_starts)
        idx = axis - 1
        channel = self.channels[idx]
        value_ref_pattern = channel.value_ref_pattern
        saving_enabled = channel.saving_enabled
        # just validate if the pattern is correct, index does not matter
        # that's why 0 is used
        scheme, path, dataset_name, msg = generate_ref(value_ref_pattern,
                                                       0)
        if scheme != "h5file" and saving_enabled:
            raise Exception("only h5file saving is supported")

    def _updateChannelValue(self, axis, elapsed_time):
        channel = self.channels[axis - 1]
        if channel.acq_idx == self.repetitions:
            return
        x_size = self.BufferSize[0]
        y_size = self.BufferSize[1]
        amplitude = axis * self.integ_time * channel.amplitude.get()
        img = generate_img(x_size, y_size, amplitude)
        roi = channel.roi
        if roi != [0, 0, 0, 0]:
            img = img[roi[0]:roi[1], roi[2]:roi[3]]
        if self._synchronization == AcqSynch.SoftwareTrigger:
            channel.value = img
            if channel.value_ref_enabled:
                img_idx = self.start_idx * self.repetitions + channel.acq_idx
                value_ref_pattern = channel.value_ref_pattern
                scheme, path, dataset_name, msg = generate_ref(
                    value_ref_pattern, img_idx)
                if msg is not None:
                    self._log.warning(msg)
                value_ref = scheme + "://" + path
                if channel.saving_enabled:
                    msg = save_img(img, path, dataset_name)
                    if msg is not None:
                        self._log.warning(msg)
                    else:
                        # we succeeded to save in HDF5
                        value_ref = value_ref + "::" + dataset_name
                channel.value_ref = value_ref
            channel.acq_idx += 1
        elif self._synchronization in (AcqSynch.HardwareTrigger,
                                       AcqSynch.HardwareGate,
                                       AcqSynch.HardwareStart,
                                       AcqSynch.SoftwareStart):
            acq_cycle_time = self.acq_cycle_time
            nb_elapsed_acq, resting = divmod(elapsed_time, acq_cycle_time)
            nb_elapsed_acq = int(nb_elapsed_acq)
            # do not wait the last latency_time
            if (nb_elapsed_acq == self.repetitions - 1
                    and resting > self.integ_time):
                nb_elapsed_acq += 1
            if nb_elapsed_acq > self.repetitions:
                nb_elapsed_acq = self.repetitions
            nb_new_acq = nb_elapsed_acq - channel.acq_idx
            if nb_new_acq == 0:
                return
            channel.buffer_values.extend([img] * nb_new_acq)
            if channel.value_ref_enabled:
                start = self.start_idx * self.repetitions + channel.acq_idx
                for img_idx in range(start, start + nb_new_acq):
                    value_ref_pattern = channel.value_ref_pattern
                    scheme, path, dataset_name, msg = generate_ref(
                        value_ref_pattern, img_idx)
                    if msg is not None:
                        self._log.warning(msg)
                    value_ref = scheme + "://" + path
                    if channel.saving_enabled:
                        msg = save_img(img, path, dataset_name)
                        if msg is not None:
                            self._log.warning(msg)
                        else:
                            # we succeeded to save in HDF5
                            value_ref = value_ref + "::" + dataset_name
                    channel.buffer_value_refs.append(value_ref)
            channel.acq_idx += nb_new_acq

    def RefOne(self, axis):
        self._log.debug("RefOne(%s)", axis)
        channel = self.read_channels[axis]
        ret = None
        if self._synchronization in (AcqSynch.HardwareTrigger,
                                     AcqSynch.HardwareGate,
                                     AcqSynch.HardwareStart,
                                     AcqSynch.SoftwareStart,):
            value_refs = copy.deepcopy(channel.buffer_value_refs)
            channel.buffer_value_refs.__init__()
            ret = value_refs
        elif self._synchronization == AcqSynch.SoftwareTrigger:
            ret = channel.value_ref
        self._log.debug('RefOne(%d): returning %s' % (axis, repr(ret)))
        return ret

    def SetAxisPar(self, axis, parameter, value):
        idx = axis - 1
        channel = self.channels[idx]
        if parameter == "value_ref_pattern":
            channel.value_ref_pattern = value
        elif parameter == "value_ref_enabled":
            channel.value_ref_enabled = value

    def isSavingEnabled(self, axis):
        idx = axis - 1
        channel = self.channels[idx]
        return channel.saving_enabled

    def setSavingEnabled(self, axis, value):
        idx = axis - 1
        channel = self.channels[idx]
        channel.saving_enabled = value
