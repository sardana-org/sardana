#!/usr/bin/env python

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

"""The device pool submodule.
It contains specific part of sardana device pool"""


__all__ = ["InterruptException", "StopException", "AbortException",
           "ReleaseException",
           "BaseElement", "ControllerClass", "ControllerLibrary",
           "PoolElement", "Controller", "ComChannel", "ExpChannel",
           "CTExpChannel", "ZeroDExpChannel", "OneDExpChannel",
           "TwoDExpChannel", "PseudoCounter", "Motor", "PseudoMotor",
           "MotorGroup", "TriggerGate",
           "MeasurementGroup", "IORegister", "Instrument", "Pool",
           "registerExtensions", "getChannelConfigs"]

__docformat__ = 'restructuredtext'

import copy
import operator
import os
import sys
import time
import traceback
import weakref
import json
from datetime import datetime
import numpy
import threading
import PyTango
import collections

from PyTango import DevState, AttrDataFormat, AttrQuality, DevFailed, \
    DeviceProxy, AttributeProxy
from taurus import Factory, Device
from taurus.core.taurusbasetypes import TaurusEventType

from taurus.core.tango.tangovalidator import TangoAttributeNameValidator, \
    TangoDeviceNameValidator
from taurus.core.util.log import Logger
from taurus.core.util.codecs import CodecFactory
from taurus.core.util.containers import CaselessDict
from taurus.core.util.event import EventGenerator, AttributeEventWait, \
    AttributeEventIterator
from taurus.core.tango import TangoDevice, FROM_TANGO_TO_STR_TYPE

from sardana import sardanacustomsettings
from .sardana import BaseSardanaElementContainer, BaseSardanaElement
from .motion import Moveable, MoveableSource

from sardana.pool import AcqSynchType
from sardana.taurus.core.tango.sardana import PlotType

Ready = Standby = DevState.ON
Counting = Acquiring = Moving = DevState.MOVING
Alarm = DevState.ALARM
Fault = DevState.FAULT

CHANGE_EVT_TYPES = TaurusEventType.Change, TaurusEventType.Periodic

MOVEABLE_TYPES = 'Motor', 'PseudoMotor', 'MotorGroup'

QUALITY = {
    AttrQuality.ATTR_VALID: 'VALID',
    AttrQuality.ATTR_INVALID: 'INVALID',
    AttrQuality.ATTR_CHANGING: 'CHANGING',
    AttrQuality.ATTR_WARNING: 'WARNING',
    AttrQuality.ATTR_ALARM: 'ALARM',
    None: 'UNKNOWN'
}


def _is_referable(channel):
    # Equivalent to ExpChannel.isReferable.
    # Use DeviceProxy instead of taurus to avoid crashes in Py3
    # See: tango-controls/pytango#292
    if isinstance(channel, str):
        channel = DeviceProxy(channel)
    return "valueref" in list(map(str.lower, channel.get_attribute_list()))


class InterruptException(Exception):
    pass


class StopException(InterruptException):
    pass


class AbortException(InterruptException):
    pass


class ReleaseException(InterruptException):
    pass


class BaseElement(object):
    """ The base class for elements in the Pool (Pool itself, Motor,
    ControllerClass, ExpChannel all should inherit from this class directly or
    indirectly)
    """

    def __repr__(self):
        pd = self.getPoolData()
        return "{0}({1})".format(pd['type'], pd['full_name'])

    def __str__(self):
        return self.getName()

    def serialize(self):
        return self.getPoolData()

    def str(self, n=0):
        """Returns a sequence of strings representing the object in
        'consistent' way.
        Default is to return <name>, <controller name>, <axis>

        :param n: the number of elements in the tuple."""
        if n == 0:
            return CodecFactory.encode(('json'), self.serialize())
        return self._str_tuple[:n]

    def __lt__(self, o):
        return self.getPoolData()['full_name'] < o.getPoolData()['full_name']

    def getName(self):
        return self.getPoolData()['name']

    def getPoolObj(self):
        """Get reference to this object's Pool."""
        return self._pool_obj

    def getPoolData(self):
        """Get reference to this object's Pool data."""
        return self._pool_data


class ControllerClass(BaseElement):
    def __init__(self, **kw):
        self.__dict__.update(kw)
        self.path, self.f_name = os.path.split(self.file_name)
        self.lib_name, self.ext = os.path.splitext(self.f_name)

    def __repr__(self):
        pd = self.getPoolData()
        return "ControllerClass({0})".format(pd['full_name'])

    def getSimpleFileName(self):
        return self.f_name

    def getFileName(self):
        return self.file_name

    def getClassName(self):
        return self.getName()

    def getType(self):
        return self.getTypes()[0]

    def getTypes(self):
        return self.types

    def getLib(self):
        return self.f_name

    def getGender(self):
        return self.gender

    def getModel(self):
        return self.model

    def getOrganization(self):
        return self.organization

    def __lt__(self, o):
        if self.getType() != o.getType():
            return self.getType() < o.getType()
        if self.getGender() != o.getGender():
            return self.getGender() < o.getGender()
        return self.getClassName() < o.getClassName()


class ControllerLibrary(BaseElement):
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def getType(self):
        return self.getTypes()[0]

    def getTypes(self):
        return self.type


class TangoAttributeEG(Logger, EventGenerator):
    """An event generator for a 'State' attribute"""

    def __init__(self, attr):
        self._attr = attr
        self.call__init__(Logger, 'EG', attr)
        event_name = '%s EG' % (attr.getParentObj().getNormalName())
        self.call__init__(EventGenerator, event_name)

        self._attr.addListener(self)

    def getAttribute(self):
        return self._attr

    def eventReceived(self, evt_src, evt_type, evt_value):
        """Event handler from Taurus"""
        if evt_type not in CHANGE_EVT_TYPES:
            return
        if evt_value is None:
            v = None
        else:
            v = evt_value.rvalue
            if hasattr(v, "magnitude"):
                v = v.magnitude
        EventGenerator.fireEvent(self, v)

    def read(self, force=False):
        try:
            last_val = self._attr.read(cache=not force).rvalue
            if hasattr(last_val, "magnitude"):
                last_val = last_val.magnitude
            self.last_val = last_val
        except:
            self.error("Read error")
            self.debug("Details:", exc_info=1)
            self.last_val = None
        return EventGenerator.read(self)

    def readValue(self, force=False):
        r = self.read(force=force)
        if r is None:
            # do a retry
            r = self.read(force=force)
        return r

    def write(self, value):
        self._attr.write(value, with_read=False)

    def __getattr__(self, name):
        return getattr(self._attr, name)


def reservedOperation(fn):
    def new_fn(*args, **kwargs):
        self = args[0]
        wr = self.getReservedWR()
        if wr is not None:
            if wr().isStopped():
                raise StopException("stopped before calling %s" % fn.__name__)
            elif wr().isAborted():
                raise AbortException("aborted before calling %s" % fn.__name__)
        try:
            return fn(*args, **kwargs)
        except:
            print("Exception occurred in reserved operation:"
                  " clearing events...")
            self._clearEventWait()
            raise

    return new_fn


def get_pool_for_device(db, device):
    server_devs = db.get_device_class_list(device.info().server_id)
    for dev_name, klass_name in zip(server_devs[0::2], server_devs[1::2]):
        if klass_name == "Pool":
            return Device(dev_name)


class PoolElement(BaseElement, TangoDevice):
    """Base class for a Pool element device."""

    def __init__(self, name, **kwargs):
        """PoolElement initialization."""
        self._reserved = None
        self._evt_wait = None
        self.__go_start_time = 0
        self.__go_end_time = 0
        self.__go_time = 0
        self._total_go_time = 0
        self.call__init__(TangoDevice, name, **kwargs)

        # dict<string, TangoAttributeEG>
        # key : the attribute name
        # value : the corresponding TangoAttributeEG
        self._attrEG = CaselessDict()

        # force the creation of a state attribute
        self.getStateEG()

    def _find_pool_obj(self):
        pool = get_pool_for_device(self.getParentObj(), self.getDeviceProxy())
        return pool

    def _find_pool_data(self):
        pool = self._find_pool_obj()
        return pool.getElementInfo(self.getFullName())._data

    # Override BaseElement.getPoolObj because the reference to pool object may
    # not be filled. This reference is filled when the element is obtained
    # using Pool.getObject. If one obtain the element directly using Taurus
    # e.g. mot = taurus.Device(<mot_name>) it won't be filled. In this case
    # look for the pool object using the database information.
    def getPoolObj(self):
        try:
            return self._pool_obj
        except AttributeError:
            self._pool_obj = self._find_pool_obj()
            return self._pool_obj

    # Override BaseElement.getPoolData because the reference to pool data may
    # not be filled. This reference is filled when the element is obtained
    # using Pool.getPoolData. If one obtain the element directly using Taurus
    # e.g. mot = taurus.Device(<mot_name>) it won't be filled. In this case
    # look for the pool object and its data using the database information.
    def getPoolData(self):
        try:
            return self._pool_data
        except AttributeError:
            self._pool_data = self._find_pool_data()
            return self._pool_data

    def cleanUp(self):
        TangoDevice.cleanUp(self)
        self._reserved = None
        f = self.factory()

        attr_map = self._attrEG
        for attr_name in list(attr_map.keys()):
            attrEG = attr_map.pop(attr_name)
            attr = attrEG.getAttribute()
            attrEG = None
            f.removeExistingAttribute(attr)

    def reserve(self, obj):
        if obj is None:
            self._reserved = None
            return
        self._reserved = weakref.ref(obj, self._unreserveCB)

    def _unreserveCB(self, obj):
        self.unreserve()

    def unreserve(self):
        self._reserved = None

    def isReserved(self, obj=None):
        if obj is None:
            return self._reserved is not None
        else:
            o = self._reserved()
            return o == obj

    def getReservedWR(self):
        return self._reserved

    def getReserved(self):
        if self._reserved is None:
            return None
        return self._reserved()

    def dump_attributes(self):
        attr_names = self.get_attribute_list()
        req_id = self.read_attributes_asynch(attr_names)
        return self.read_attributes_reply(req_id, 2000)

    def _getAttrValue(self, name, force=False):
        attrEG = self._getAttrEG(name)
        if attrEG is None:
            return None
        return attrEG.readValue(force=force)

    def _getAttrEG(self, name):
        attrEG = self.getAttrEG(name)
        if attrEG is None:
            attrEG = self._createAttribute(name)
        return attrEG

    def _createAttribute(self, name):
        attrObj = self.getAttribute(name)
        if attrObj is None:
            self.warning("Unable to create attribute %s" % name)
            return None, None
        attrEG = TangoAttributeEG(attrObj)
        self._attrEG[name] = attrEG
        return attrEG

    def _getEventWait(self):
        if self._evt_wait is None:
            # create an object that waits for attribute events.
            # each time we use it we have to connect and disconnect to an
            # attribute
            self._evt_wait = AttributeEventWait()
        return self._evt_wait

    def _clearEventWait(self):
        self._evt_wait = None

    def getStateEG(self):
        return self._getAttrEG('state')

    def getControllerName(self):
        return self.getControllerObj().name

    def getControllerObj(self):
        full_ctrl_name = self.getPoolData()['controller']
        return self.getPoolObj().getObj(full_ctrl_name, "Controller")

    def getAxis(self):
        return self.getPoolData()['axis']

    def getType(self):
        return self.getPoolData()['type']

    def waitReady(self, timeout=None):
        return self.getStateEG().waitEvent(Moving, equal=False,
                                           timeout=timeout)

    def getAttrEG(self, name):
        """Returns the TangoAttributeEG object"""
        return self._attrEG.get(name)

    def getAttrObj(self, name):
        """Returns the taurus.core.tangoattribute.TangoAttribute object"""
        attrEG = self._attrEG.get(name)
        if attrEG is None:
            return None
        return attrEG.getAttribute()

    def getInstrumentObj(self):
        return self._getAttrEG('instrument')

    def getInstrumentName(self, force=False):
        instr_name = self._getAttrValue('instrument', force=force)
        if not instr_name:
            return ''
        # instr_name = instr_name[:instr_name.index('(')]
        return instr_name

    def setInstrumentName(self, instr_name):
        self.getInstrumentObj().write(instr_name)

    def getInstrument(self):
        instr_name = self.getInstrumentName()
        if not instr_name:
            return None
        return self.getPoolObj().getObj("Instrument", instr_name)

    @reservedOperation
    def start(self, *args, **kwargs):
        evt_wait = self._getEventWait()
        evt_wait.connect(self.getAttribute("state"))
        try:
            evt_wait.waitEvent(DevState.MOVING, equal=False)
            # Clear event set to not confuse the value coming from the
            # connection with the event of of end of the operation
            # in the next wait event. This was observed on Windows where
            # the time stamp resolution is very poor.
            evt_wait.clearEventSet()
            self.__go_time = 0
            self.__go_start_time = ts1 = time.time()
            self._start(*args, **kwargs)
            ts2 = time.time()
            evt_wait.waitEvent(DevState.MOVING, after=ts1)
        except:
            evt_wait.disconnect()
            raise
        ts2 = evt_wait.getRecordedEvents().get(DevState.MOVING, ts2)
        return (ts2,)

    def waitFinish(self, timeout=None, id=None):
        """Wait for the operation to finish

        :param timeout: optional timeout (seconds)
        :type timeout: float
        :param id: id of the opertation returned by start
        :type id: tuple(float)
        """
        if timeout is None:
            # 0.1 s of timeout with infinite retries facilitates aborting
            # by raising exceptions from a different threads
            timeout = 0.1
            retries = -1
        else:
            # Due to taurus-org/taurus #573 we need to divide the timeout
            # in two intervals
            timeout = timeout / 2
            retries = 1
        if id is not None:
            id = id[0]
        evt_wait = self._getEventWait()
        try:
            evt_wait.waitEvent(DevState.MOVING, after=id, equal=False,
                               timeout=timeout, retries=retries)
        finally:
            self.__go_end_time = time.time()
            self.__go_time = self.__go_end_time - self.__go_start_time
            evt_wait.disconnect()

    @reservedOperation
    def go(self, *args, **kwargs):
        self._total_go_time = 0
        start_time = time.time()
        eid = self.start(*args, **kwargs)
        timeout = kwargs.get('timeout')
        self.waitFinish(id=eid, timeout=timeout)
        self._total_go_time = time.time() - start_time

    def getLastGoTime(self):
        """Returns the time it took for last go operation"""
        return self.__go_time

    def getTotalLastGoTime(self):
        """Returns the time it took for last go operation, including dead time
        to prepare, wait for events, etc"""
        return self._total_go_time

    def abort(self, wait_ready=True, timeout=None):
        state = self.getStateEG()
        state.lock()
        try:
            self.command_inout("Abort")
            if wait_ready:
                self.waitReady(timeout=timeout)
        finally:
            state.unlock()

    def stop(self, wait_ready=True, timeout=None):
        state = self.getStateEG()
        state.lock()
        try:
            self.command_inout("Stop")
            if wait_ready:
                self.waitReady(timeout=timeout)
        finally:
            state.unlock()

    def information(self, tab='    '):
        msg = self._information(tab=tab)
        return "\n".join(msg)

    def _information(self, tab='    '):
        indent = "\n" + tab + 10 * ' '
        msg = [self.getName() + ":"]
        try:
            t = time.time()
            state_time = datetime.fromtimestamp(t).strftime("%H:%M:%S.%f")
            # TODO: use expiration_period=float("inf") to always use event
            #  value (taurus-org/taurus#1105)
            state = self.stateObj.read()
            state_time = state.time.strftime("%H:%M:%S.%f")
            # state_value is DevState enumeration (IntEnum)
            state = state.rvalue.name.capitalize()
        except DevFailed as df:
            if len(df.args):
                state = df.args[0].desc
            else:
                e_info = sys.exc_info()[:2]
                state = traceback.format_exception_only(*e_info)[0].rstrip()
        except Exception:
            e_info = sys.exc_info()[:2]
            state = traceback.format_exception_only(*e_info)[0].rstrip()
        msg.append(tab + "   State: " + state + " ({})".format(state_time))

        try:
            t = time.time()
            status_time = datetime.fromtimestamp(t).strftime("%H:%M:%S.%f")
            # TODO: ideally status should come from the event and no extra
            #  readout should be made
            status = self.read_attribute("status")
            status_time = status.time.strftime("%H:%M:%S.%f")
            status = status.value.replace('\n', indent)
        except DevFailed as df:
            if len(df.args):
                status = df.args[0].desc
            else:
                e_info = sys.exc_info()[:2]
                status = traceback.format_exception_only(*e_info)[0].rstrip()
        except Exception:
            e_info = sys.exc_info()[:2]
            status = traceback.format_exception_only(*e_info)[0].rstrip()
        msg.append(tab + "  Status: " + status + " ({})".format(status_time))

        return msg


class Controller(PoolElement):
    """ Class encapsulating Controller functionality."""

    def __init__(self, name, **kw):
        """PoolElement initialization."""
        self.call__init__(PoolElement, name, **kw)

    def getModuleName(self):
        return self.getPoolData()['module']

    def getClassName(self):
        return self.getPoolData()['klass']

    def getTypes(self):
        return self.getPoolData()['types']

    def getMainType(self):
        return self.getPoolData()['main_type']

    def addElement(self, elem):
        axis = elem.getAxis()
        self._elems[axis] = elem
        self._last_axis = max(self._last_axis, axis)

    def removeElement(self, elem):
        axis = elem.getAxis()
        del self._elems[elem.getAxis()]
        if axis == self._last_axis:
            self._last_axis = max(self._elems)

    def getElementByAxis(self, axis):
        pool = self.getPoolObj()
        for _, elem in \
                list(pool.getElementsOfType(self.getMainType()).items()):
            if (elem.controller != self.getFullName() or
                    elem.getAxis() != axis):
                continue
            return elem

    def getElementByName(self, name):
        pool = self.getPoolObj()
        for _, elem in \
                list(pool.getElementsOfType(self.getMainType()).items()):
            if (elem.controller != self.getFullName() or
                    elem.getName() != name):
                continue
            return elem

    def getUsedAxes(self):
        """Return axes in use by this controller

        :return: list of axes
        :rtype: list<int>
        """

        pool = self.getPoolObj()
        axes = []
        for _, elem in \
                list(pool.getElementsOfType(self.getMainType()).items()):
            if elem.controller != self.getFullName():
                continue
            axes.append(elem.getAxis())
        return sorted(axes)

    def getLastUsedAxis(self):
        """Return the last used axis (the highest axis) in this controller

        :return: last used axis
        :rtype: int or None
        """
        used_axes = self.getUsedAxes()
        if len(used_axes) == 0:
            return None
        return max(used_axes)

    def __lt__(self, o):
        return self.getName() < o.getName()


class ComChannel(PoolElement):
    """ Class encapsulating CommunicationChannel functionality."""
    pass


class ExpChannel(PoolElement):
    """ Class encapsulating ExpChannel functionality."""

    def __init__(self, name, **kw):
        """ExpChannel initialization."""
        self.call__init__(PoolElement, name, **kw)
        self._last_integ_time = None
        self._last_value_ref_pattern = None
        self._last_value_ref_enabled = None

        self._value_buffer = {}
        self._value_buffer_cb = None
        codec_name = getattr(sardanacustomsettings, "VALUE_BUFFER_CODEC")
        self._value_buffer_codec = CodecFactory().getCodec(codec_name)

        self._value_ref_buffer = {}
        self._value_ref_buffer_cb = None
        codec_name = getattr(sardanacustomsettings, "VALUE_REF_BUFFER_CODEC")
        self._value_ref_buffer_codec = CodecFactory().getCodec(codec_name)

    def isReferable(self):
        if "valueref" in list(map(str.lower, self.get_attribute_list())):
            return True
        return False

    def getIntegrationTime(self):
        return self._getAttrValue('IntegrationTime')

    def getIntegrationTimeObj(self):
        return self._getAttrEG('IntegrationTime')

    def setIntegrationTime(self, integ_time):
        self.getIntegrationTimeObj().write(integ_time)

    def putIntegrationTime(self, integ_time):
        if self._last_integ_time == integ_time:
            return
        self._last_integ_time = integ_time
        self.getIntegrationTimeObj().write(integ_time)

    def getValueObj_(self):
        """Retrurns Value attribute event generator object.

        :return: Value attribute event generator
        :rtype: TangoAttributeEG

        ..todo:: When support to Taurus 3 will be dropped provide getValueObj.
        Taurus 3 TaurusDevice class already uses this name.
        """
        return self._getAttrEG('value')

    def getValue(self, force=False):
        return self._getAttrValue('value', force=force)

    def getValueBufferObj(self):
        return self._getAttrEG('valuebuffer')

    def getValueBuffer(self):
        return self._value_buffer

    def valueBufferChanged(self, value_buffer):
        if value_buffer is None:
            return
        _, value_buffer = self._value_buffer_codec.decode(value_buffer)
        indexes = value_buffer["index"]
        values = value_buffer["value"]
        for index, value in zip(indexes, values):
            self._value_buffer[index] = value

    def getValueRefObj(self):
        """Return ValueRef attribute event generator object.

        :return: ValueRef attribute event generator
        :rtype: TangoAttributeEG
        """
        return self._getAttrEG('value')

    def getValueRef(self, force=False):
        return self._getAttrValue('valueref', force=force)

    def getValueRefBufferObj(self):
        return self._getAttrEG('valuerefbuffer')

    def getValueRefBuffer(self):
        return self._value_ref_buffer

    def valueBufferRefChanged(self, value_ref_buffer):
        if value_ref_buffer is None:
            return
        _, value_ref_buffer = self._value_ref_buffercodec.decode(
            value_ref_buffer)
        indexes = value_ref_buffer["index"]
        value_refs = value_ref_buffer["value_ref"]
        for index, value_ref in zip(indexes, value_refs):
            self._value_ref_buffer[index] = value_ref

    def getValueRefPattern(self):
        return self._getAttrValue('ValueRefPattern')

    def getValueRefPatternObj(self):
        return self._getAttrEG('ValueRefPattern')

    def setValueRefPattern(self, value_ref_pattern):
        self.getValueRefPatternObj().write(value_ref_pattern)

    def putValueRefPattern(self, value_ref_pattern):
        if self._last_value_ref_pattern == value_ref_pattern:
            return
        self._last_value_ref_pattern = value_ref_pattern
        self.getValueRefPatternObj().write(value_ref_pattern)

    def isValueRefEnabled(self):
        return self._getAttrValue('ValueRefEnabled')

    def getValueRefEnabledObj(self):
        return self._getAttrEG('ValueRefEnabled')

    def setValueRefEnabled(self, value_ref_enabled):
        self.getValueRefEnabledObj().write(value_ref_enabled)

    def putValueRefEnabled(self, value_ref_enabled):
        if self._last_value_ref_enabled == value_ref_enabled:
            return
        self._last_value_ref_enabled = value_ref_enabled
        self.getValueRefEnabledObj().write(value_ref_enabled)

    def _start(self, *args, **kwargs):
        self.Start()

    def go(self, *args, **kwargs):
        """Count and report count result.

        Configuration measurement, then start and wait until finish.

        .. note::
            The count (go) method API is partially experimental (value
            references may be changed to values whenever possible in the
            future). Backwards incompatible changes may occur if deemed
            necessary by the core developers.

        :return: state and value (or value reference - experimental)
        :rtype: :obj:`tuple`
        """
        start_time = time.time()
        integration_time = args[0]
        self.putIntegrationTime(integration_time)
        PoolElement.go(self)
        state = self.getStateEG().readValue()
        if self.isReferable() and self.isValueRefEnabled():
            result = self.getValueRef()
        else:
            result = self.getValue()
        ret = state, result
        self._total_go_time = time.time() - start_time
        return ret

    startCount = PoolElement.start
    waitCount = PoolElement.waitFinish
    count = go
    stopCount = PoolElement.abort
    stop = PoolElement.stop


class TimerableExpChannel(ExpChannel):

    def getTimer(self):
        return self._getAttrValue('Timer')

    def getTimerObj(self):
        return self._getAttrEG('Timer')

    def setTimer(self, timer):
        self.getTimerObj().write(timer)


class CTExpChannel(TimerableExpChannel):
    """ Class encapsulating CTExpChannel functionality."""
    pass


class ZeroDExpChannel(ExpChannel):
    """ Class encapsulating ZeroDExpChannel functionality."""
    pass


class OneDExpChannel(TimerableExpChannel):
    """ Class encapsulating OneDExpChannel functionality."""
    pass


class TwoDExpChannel(TimerableExpChannel):
    """ Class encapsulating TwoDExpChannel functionality."""
    pass


class PseudoCounter(ExpChannel):
    """ Class encapsulating PseudoCounter functionality."""
    pass


class TriggerGate(PoolElement):
    """ Class encapsulating TriggerGate functionality."""
    pass


class Motor(PoolElement, Moveable):
    """ Class encapsulating Motor functionality."""

    def __init__(self, name, **kw):
        """PoolElement initialization."""
        self.call__init__(PoolElement, name, **kw)
        self.call__init__(Moveable)

    def getPosition(self, force=False):
        return self._getAttrValue('position', force=force)

    def getDialPosition(self, force=False):
        return self._getAttrValue('dialposition', force=force)

    def getVelocity(self, force=False):
        return self._getAttrValue('velocity', force=force)

    def getAcceleration(self, force=False):
        return self._getAttrValue('acceleration', force=force)

    def getDeceleration(self, force=False):
        return self._getAttrValue('deceleration', force=force)

    def getBaseRate(self, force=False):
        return self._getAttrValue('base_rate', force=force)

    def getBacklash(self, force=False):
        return self._getAttrValue('backlash', force=force)

    def getLimitSwitches(self, force=False):
        return self._getAttrValue('limit_switches', force=force)

    def getOffset(self, force=False):
        return self._getAttrValue('offset', force=force)

    def getStepPerUnit(self, force=False):
        return self._getAttrValue('step_per_unit', force=force)

    def getSign(self, force=False):
        return self._getAttrValue('Sign', force=force)

    def getSimulationMode(self, force=False):
        return self._getAttrValue('SimulationMode', force=force)

    def getPositionObj(self):
        return self._getAttrEG('position')

    def getDialPositionObj(self):
        return self._getAttrEG('dialposition')

    def getVelocityObj(self):
        return self._getAttrEG('velocity')

    def getAccelerationObj(self):
        return self._getAttrEG('acceleration')

    def getDecelerationObj(self):
        return self._getAttrEG('deceleration')

    def getBaseRateObj(self):
        return self._getAttrEG('base_rate')

    def getBacklashObj(self):
        return self._getAttrEG('backlash')

    def getLimitSwitchesObj(self):
        return self._getAttrEG('limit_switches')

    def getOffsetObj(self):
        return self._getAttrEG('offset')

    def getStepPerUnitObj(self):
        return self._getAttrEG('step_per_unit')

    def getSimulationModeObj(self):
        return self._getAttrEG('step_per_unit')

    def setVelocity(self, value):
        return self.getVelocityObj().write(value)

    def setAcceleration(self, value):
        return self.getAccelerationObj().write(value)

    def setDeceleration(self, value):
        return self.getDecelerationObj().write(value)

    def setBaseRate(self, value):
        return self.getBaseRateObj().write(value)

    def setBacklash(self, value):
        return self.getBacklashObj().write(value)

    def setOffset(self, value):
        return self.getOffsetObj().write(value)

    def setStepPerUnit(self, value):
        return self.getStepPerUnitObj().write(value)

    def setSign(self, value):
        return self.getSignObj().write(value)

    # -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # Moveable interface
    #

    def _start(self, *args, **kwargs):
        new_pos = args[0]
        if isinstance(new_pos, collections.Sequence):
            new_pos = new_pos[0]
        try:
            self.write_attribute('position', new_pos)
        except DevFailed as df:
            for err in df.args:
                if err.reason == 'API_AttrNotAllowed':
                    raise RuntimeError('%s is already moving' % self)
                else:
                    raise
        self.final_pos = new_pos

    def go(self, *args, **kwargs):
        start_time = time.time()
        PoolElement.go(self, *args, **kwargs)
        ret = self.getStateEG().readValue(), self.readPosition()
        self._total_go_time = time.time() - start_time
        return ret

    startMove = PoolElement.start
    waitMove = PoolElement.waitFinish
    move = go
    getLastMotionTime = PoolElement.getLastGoTime
    getTotalLastMotionTime = PoolElement.getTotalLastGoTime

    @reservedOperation
    def iterMove(self, new_pos, timeout=None):
        if isinstance(new_pos, collections.Sequence):
            new_pos = new_pos[0]
        state, pos = self.getAttribute("state"), self.getAttribute("position")

        evt_wait = self._getEventWait()
        evt_wait.connect(state)
        evt_wait.lock()
        try:
            # evt_wait.waitEvent(DevState.MOVING, equal=False)
            time_stamp = time.time()
            try:
                self.getPositionObj().write(new_pos)
            except DevFailed as err_traceback:
                for err in err_traceback.args:
                    if err.reason == 'API_AttrNotAllowed':
                        raise RuntimeError('%s is already moving' % self)
                    else:
                        raise
            self.final_pos = new_pos
            # putting timeout=0.1 and retries=1 is a patch for the case when
            # the initial moving event doesn't arrive do to an unknown
            # tango/pytango error at the time
            evt_wait.waitEvent(DevState.MOVING, time_stamp,
                               timeout=0.1, retries=1)
        finally:
            evt_wait.unlock()
            evt_wait.disconnect()

        evt_iter_wait = AttributeEventIterator(state, pos)
        evt_iter_wait.lock()
        try:
            for evt_data in evt_iter_wait.events():
                src, value = evt_data
                if src == state and value != DevState.MOVING:
                    raise StopIteration
                yield value
        finally:
            evt_iter_wait.unlock()
            evt_iter_wait.disconnect()

    def readPosition(self, force=False):
        return [self.getPosition(force=force)]

    def getMoveableSource(self):
        return self.getPoolObj()

    def getSize(self):
        return 1

    def getIndex(self, name):
        if name.lower() == self.getName().lower():
            return 0
        return -1

    #
    # End of Moveable interface
    # -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    def _information(self, tab='    '):
        msg = PoolElement._information(self, tab=tab)
        try:
            position = self.read_attribute("position")
            pos = str(position.value)
            if position.quality != AttrQuality.ATTR_VALID:
                pos += " [" + QUALITY[position.quality] + "]"
        except DevFailed as df:
            if len(df.args):
                pos = df.args[0].desc
            else:
                e_info = sys.exc_info()[:2]
                pos = traceback.format_exception_only(*e_info)
        except:
            e_info = sys.exc_info()[:2]
            pos = traceback.format_exception_only(*e_info)

        msg.append(tab + "Position: " + str(pos))
        return msg


class PseudoMotor(PoolElement, Moveable):
    """ Class encapsulating PseudoMotor functionality."""

    def __init__(self, name, **kw):
        """PoolElement initialization."""
        self.call__init__(PoolElement, name, **kw)
        self.call__init__(Moveable)

    def getPosition(self, force=False):
        return self._getAttrValue('position', force=force)

    def getDialPosition(self, force=False):
        return self.getPosition(force=force)

    def getPositionObj(self):
        return self._getAttrEG('position')

    def getDialPositionObj(self):
        return self.getPositionObj()

    # -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # Moveable interface
    #

    def _start(self, *args, **kwargs):
        new_pos = args[0]
        if isinstance(new_pos, collections.Sequence):
            new_pos = new_pos[0]
        try:
            self.write_attribute('position', new_pos)
        except DevFailed as df:
            for err in df.args:
                if err.reason == 'API_AttrNotAllowed':
                    raise RuntimeError('%s is already moving' % self)
                else:
                    raise
        self.final_pos = new_pos

    def go(self, *args, **kwargs):
        start_time = time.time()
        PoolElement.go(self, *args, **kwargs)
        ret = self.getStateEG().readValue(), self.readPosition()
        self._total_go_time = time.time() - start_time
        return ret

    startMove = PoolElement.start
    waitMove = PoolElement.waitFinish
    move = go
    getLastMotionTime = PoolElement.getLastGoTime
    getTotalLastMotionTime = PoolElement.getTotalLastGoTime

    def readPosition(self, force=False):
        return [self.getPosition(force=force)]

    def getMoveableSource(self):
        return self.getPoolObj()

    def getSize(self):
        return 1

    def getIndex(self, name):
        if name.lower() == self.getName().lower():
            return 0
        return -1

    #
    # End of Moveable interface
    # -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    def _information(self, tab='    '):
        msg = PoolElement._information(self, tab=tab)
        try:
            position = self.read_attribute("position")
            pos = str(position.value)
            if position.quality != AttrQuality.ATTR_VALID:
                pos += " [" + QUALITY[position.quality] + "]"
        except DevFailed as df:
            if len(df.args):
                pos = df.args[0].desc
            else:
                e_info = sys.exc_info()[:2]
                pos = traceback.format_exception_only(*e_info)
        except:
            e_info = sys.exc_info()[:2]
            pos = traceback.format_exception_only(*e_info)

        msg.append(tab + "Position: " + str(pos))
        return msg


class MotorGroup(PoolElement, Moveable):
    """ Class encapsulating MotorGroup functionality."""

    def __init__(self, name, **kw):
        """PoolElement initialization."""
        self.call__init__(PoolElement, name, **kw)
        self.call__init__(Moveable)

    def _create_str_tuple(self):
        return 3 * ["TODO"]

    def getMotorNames(self):
        return self.getPoolData()['elements']

    def hasMotor(self, name):
        motor_names = list(map(str.lower, self.getMotorNames()))
        return name.lower() in motor_names

    def getPosition(self, force=False):
        return self._getAttrValue('position', force=force)

    def getPositionObj(self):
        return self._getAttrEG('position')

    # -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # Moveable interface
    #

    def _start(self, *args, **kwargs):
        new_pos = args[0]
        try:
            self.write_attribute('position', new_pos)
        except DevFailed as df:
            for err in df.args:
                if err.reason == 'API_AttrNotAllowed':
                    raise RuntimeError('%s is already moving' % self)
                else:
                    raise
        self.final_pos = new_pos

    def go(self, *args, **kwargs):
        start_time = time.time()
        PoolElement.go(self, *args, **kwargs)
        ret = self.getStateEG().readValue(), self.readPosition()
        self._total_go_time = time.time() - start_time
        return ret

    startMove = PoolElement.start
    waitMove = PoolElement.waitFinish
    move = go
    getLastMotionTime = PoolElement.getLastGoTime
    getTotalLastMotionTime = PoolElement.getTotalLastGoTime

    def readPosition(self, force=False):
        return self.getPosition(force=force)

    def getMoveableSource(self):
        return self.getPoolObj()

    def getSize(self):
        return len(self.getMotorNames())

    def getIndex(self, name):
        try:
            motor_names = list(map(str.lower, self.getMotorNames()))
            return motor_names.index(name.lower())
        except:
            return -1

    #
    # End of Moveable interface
    # -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    def _information(self, tab='    '):
        msg = PoolElement._information(self, tab=tab)
        try:
            position = self.read_attribute("position")
            pos = str(position.value)
            if position.quality != AttrQuality.ATTR_VALID:
                pos += " [" + QUALITY[position.quality] + "]"
        except DevFailed as df:
            if len(df.args):
                pos = df.args[0].desc
            else:
                e_info = sys.exc_info()[:2]
                pos = traceback.format_exception_only(*e_info)
        except:
            e_info = sys.exc_info()[:2]
            pos = traceback.format_exception_only(*e_info)

        msg.append(tab + "Position: " + str(pos))
        return msg


class BaseChannelInfo(object):
    def __init__(self, data):
        # dict<str, obj>
        # channel data
        self.raw_data = data
        self.__dict__.update(data)


class TangoChannelInfo(BaseChannelInfo):
    def __init__(self, data, info):
        BaseChannelInfo.__init__(self, data)
        # PyTango.AttributeInfoEx
        self.set_info(info)

    def has_info(self):
        return self.raw_info is not None

    def set_info(self, info):
        self.raw_info = info

        if info is None:
            return

        data = self.raw_data

        if 'data_type' not in data:
            data_type = info.data_type
            try:
                self.data_type = FROM_TANGO_TO_STR_TYPE[data_type]
            except KeyError as e:
                # For backwards compatibility:
                # starting from Taurus 4.3.0 DevVoid was added to the dict
                if data_type == PyTango.DevVoid:
                    self.data_type = None
                else:
                    raise e

        if 'shape' not in data:
            shape = ()
            if info.data_format == AttrDataFormat.SPECTRUM:
                shape = (info.max_dim_x,)
            elif info.data_format == AttrDataFormat.IMAGE:
                shape = (info.max_dim_x, info.max_dim_y)
            self.shape = shape
        else:
            shape = self.shape
        self.shape = list(shape)

    def __getattr__(self, name):
        if self.has_info():
            return getattr(self.raw_info, name)
        cls_name = self.__class__.__name__
        raise AttributeError("'%s' has no attribute '%s'" % (cls_name, name))


def getChannelConfigs(mgconfig, ctrls=None, sort=True):
    '''
    gets a list of channel configurations of the controllers of the given
    measurement group configuration. It optionally filters to those channels
    matching given lists of controller.

    :param ctrls: (seq<str> or None) a sequence of strings to filter the
                  controllers. If None given, all controllers will be used
    :param sort: (bool) If True (default) the returned list will be sorted
                 according to channel index (if given in channeldata) and
                 then by channelname.

    :return: (list<tuple>) A list of channelname,channeldata pairs.
    '''
    chconfigs = []
    if not mgconfig:
        return []
    for ctrl_name, ctrl_data in list(mgconfig['controllers'].items()):
        if ctrls is None or ctrl_name in ctrls:
            for ch_name, ch_data in list(ctrl_data['channels'].items()):
                ch_data.update({'_controller_name': ctrl_name})
                chconfigs.append((ch_name, ch_data))
    if sort:
        # sort the channel configs by index (primary sort) and then by channel
        # name.
        # sort by channel_name
        chconfigs = sorted(chconfigs, key=lambda c: c[0])
        # sort by index (give a very large index for those which don't have it)
        chconfigs = sorted(chconfigs, key=lambda c: c[1].get('index', 1e16))
    return chconfigs


class MGConfiguration(object):
    def __init__(self, mg, data):
        self._mg = weakref.ref(mg)
        self._raw_data = None
        self._pending_event_data = None
        self._local_changes = False
        self.set_data(data)

    def set_data(self, data, force=False):
        # dict<str, list[DeviceProxy, CaselessDict<str, dict>]>
        # where key is a device name and value is a list with two elements:
        #  - A device proxy or None if there was an error building it
        #  - A dict where keys are attribute names and value is a reference to
        #    a dict representing channel data as received in raw data
        self.tango_dev_channels = None

        # Number of elements in tango_dev_channels in error (could not build
        # DeviceProxy, probably)
        self.tango_dev_channels_in_error = 0

        # dict<str, tuple<str, str, TangoChannelInfo>>
        # where key is a channel name and value is a tuple of three elements:
        #  - device name
        #  - attribute name
        #  - attribute information or None if there was an error trying to get
        #    the information
        self.tango_channels_info = None

        # Number of elements in tango_channels_info_in_error in error
        # (could not build attribute info, probably)
        self.tango_channels_info_in_error = 0

        # dict<str, dict>
        # where key is a channel name and data is a reference to a dict
        # representing channel data as received in raw data
        self.non_tango_channels = None

        # object each time
        if isinstance(data, str):
            data = CodecFactory().decode(('json', data))
        if not force:
            if self._raw_data == data:
                # The new data received on the on_change_event was generated by
                # this object.
                return
            elif self._local_changes:
                self._pending_event_data = data
                return
        self._pending_event_data = None
        self._local_changes = False

        self._raw_data = data
        self.__dict__.update(data)

        # dict<str, dict>
        # where key is the channel name and value is the channel data in form
        # of a dict as received by the MG configuration attribute
        self.channels = channels = CaselessDict()
        self.channels_names = channels_names = CaselessDict()
        self.channels_labels = channels_labels = CaselessDict()
        self.controllers_names = controllers_names = CaselessDict()
        self.controllers_channels = controllers_channels = CaselessDict()
        self.controllers_alias = CaselessDict()

        # TODO private controllers attr
        for ctrl_name, ctrl_data in list(self.controllers.items()):
            try:
                if ctrl_name != '__tango__':
                    proxy = DeviceProxy(ctrl_name)
                    ctrl_full_name = ctrl_name
                    ctrl_name = proxy.alias()
                    self.controllers_alias[ctrl_full_name] = ctrl_name

                controllers_names[ctrl_name] = ctrl_data
                controllers_channels[ctrl_name] = []
            except Exception:
                pass
            for channel_name, channel_data in \
                    list(ctrl_data['channels'].items()):
                channels[channel_name] = channel_data
                name = channel_data['name']
                channels_names[name] = channel_data
                label = channel_data['label']
                channels_labels[name] = channel_data
                index = channel_data['index']
                ch_data = {'fullname': channel_name,
                           'label': label,
                           'name': name,
                           'index': index}
                controllers_channels[ctrl_name].append(ch_data)

        #####################
        # @todo: the for-loops above could be replaced by something like:
        # self.channels = channels = \
        #      CaselessDict(getChannelConfigs(data, sort=False))
        #####################

        # Create ordered list by channel index in the MG as cache
        #    channel_list: seq<dict> each element is the channel data in form
        #    of a dict as received by the MG configuration attribute.
        #    channel_list_name: seq<str>
        #    controller_list_names: seg<str>
        self.channel_list = len(channels) * [None]
        self.channel_list_name = len(channels) * [None]
        self.controller_list_name = []

        for channel, channel_data in channels.items():
            idx = channel_data['index']
            self.channel_list[idx] = channel_data
            self.channel_list_name[idx] = channel

        for channel_name in self.channel_list_name:
            ctrl = self._get_ctrl_for_element(channel_name)
            if ctrl not in self.controller_list_name:
                self.controller_list_name.append(ctrl)

    def _build(self):
        # internal channel structure that groups channels by tango device so
        # they can be read as a group minimizing this way the network requests
        self.tango_dev_channels = tg_dev_chs = CaselessDict()
        self.tango_dev_channels_in_error = 0
        self.tango_channels_info = tg_chs_info = CaselessDict()
        self.tango_channels_info_in_error = 0
        self.non_tango_channels = n_tg_chs = CaselessDict()
        self.cache = cache = {}

        tg_attr_validator = TangoAttributeNameValidator()
        for channel_name, channel_data in list(self.channels.items()):
            cache[channel_name] = None
            data_source = channel_data['source']
            params = tg_attr_validator.getUriGroups(data_source)
            if params is None:
                # Handle NON tango channel
                n_tg_chs[channel_name] = channel_data
            else:
                # Handle tango channel
                dev_name = params['devname'].lower()
                attr_name = params['_shortattrname'].lower()
                host, port = params.get('host'), params.get('port')
                if host is not None and port is not None:
                    dev_name = "tango://{0}:{1}/{2}".format(host, port,
                                                            dev_name)
                dev_data = tg_dev_chs.get(dev_name)
                # technical debt: read Value or ValueRef attribute
                # ideally the source configuration should include this info
                # Use DeviceProxy instead of taurus to avoid crashes in Py3
                # See: tango-controls/pytango#292
                # channel = Device(dev_name)
                # if (isinstance(channel, ExpChannel)
                #         and channel.isReferable()
                #         and channel_data.get("value_ref_enabled", False)):
                if (_is_referable(dev_name)
                        and channel_data.get("value_ref_enabled", False)):
                    attr_name += "Ref"
                if dev_data is None:
                    # Build tango device
                    dev = None
                    try:
                        dev = DeviceProxy(dev_name)
                    except:
                        self.tango_dev_channels_in_error += 1
                    tg_dev_chs[dev_name] = dev_data = [dev, CaselessDict()]
                dev, attr_data = dev_data
                attr_data[attr_name] = channel_data

                # get attribute configuration
                attr_info = None
                if dev is None:
                    self.tango_channels_info_in_error += 1
                else:
                    try:
                        tg_attr_info = dev.get_attribute_config_ex(attr_name)[
                            0]
                    except:
                        tg_attr_info = \
                            self._build_empty_tango_attr_info(channel_data)
                        self.tango_channels_info_in_error += 1
                    attr_info = TangoChannelInfo(channel_data, tg_attr_info)

                tg_chs_info[channel_name] = dev_name, attr_name, attr_info

    def _build_empty_tango_attr_info(self, channel_data):
        ret = PyTango.AttributeInfoEx()
        ret.name = channel_data['name']
        ret.label = channel_data['label']
        return ret

    def prepare(self):
        # first time? build everything
        if self.tango_dev_channels is None:
            return self._build()

        # prepare missing tango devices
        if self.tango_dev_channels_in_error > 0:
            for dev_name, dev_data in list(self.tango_dev_channels.items()):
                if dev_data[0] is None:
                    try:
                        dev_data[0] = DeviceProxy(dev_name)
                        self.tango_dev_channels_in_error -= 1
                    except:
                        pass

        # prepare missing tango attribute configuration
        if self.tango_channels_info_in_error > 0:
            for _, attr_data in list(self.tango_channels_info.items()):
                dev_name, attr_name, attr_info = attr_data
                if attr_info.has_info():
                    continue
                dev = self.tango_dev_channels[dev_name]
                if dev is None:
                    continue
                try:
                    tg_attr_info = dev.get_attribute_config_ex(attr_name)[0]
                    attr_info.set_info(tg_attr_info)
                    self.tango_channels_info_in_error -= 1
                except:
                    pass

    def getChannels(self):
        return self.channel_list

    def getChannelInfo(self, channel_name):
        try:
            return self.tango_channels_info[channel_name]
        except Exception:
            channel_name = channel_name.lower()
            for d_name, a_name, ch_info in \
                    list(self.tango_channels_info.values()):
                if ch_info.name.lower() == channel_name:
                    return d_name, a_name, ch_info

    def getChannelsInfo(self, only_enabled=False):
        """Returns information about the channels present in the measurement
        group in a form of dictionary, where key is a channel name and value is
        a tuple of three elements:
            - device name
            - attribute name
            - attribute information or None if there was an error trying to get
              the information

        :param only_enabled: flag to filter out disabled channels
        :type only_enabled: bool
        :return: dictionary with channels info
        :rtype: dict<str, tuple<str, str, TangoChannelInfo>>
        """
        self.prepare()
        ret = CaselessDict(self.tango_channels_info)
        ret.update(self.non_tango_channels)
        for ch_name, (_, _, ch_info) in list(ret.items()):
            if only_enabled and not ch_info.enabled:
                ret.pop(ch_name)
        return ret

    def getChannelsInfoList(self, only_enabled=False):
        """Returns information about the channels present in the measurement
        group in a form of ordered, based on the channel index, list.

        :param only_enabled: flag to filter out disabled channels
        :type only_enabled: bool
        :return: list with channels info
        :rtype: list<TangoChannelInfo>
        """
        channels_info = self.getChannelsInfo(only_enabled=only_enabled)
        ret = []
        for _, (_, _, ch_info) in list(channels_info.items()):
            ret.append(ch_info)
        ret = sorted(ret, key=lambda x: x.index)
        return ret

    def getCountersInfoList(self):
        channels_info = self.getChannelsInfoList()
        timer_name, idx = self.timer, -1
        for i, ch in enumerate(channels_info):
            if ch['full_name'] == timer_name:
                idx = i
                break
        if idx >= 0:
            channels_info.pop(idx)
        return channels_info

    def getTangoDevChannels(self, only_enabled=False):
        """Returns Tango channels (attributes) that could be used to read
        measurement group results in a form of dict where key is a device name
        and value is a list with two elements:
            - A device proxy or None if there was an error building it
            - A dict where keys are attribute names and value is a reference to
              a dict representing channel data as received in raw data

        :param only_enabled: flag to filter out disabled channels
        :type only_enabled: bool
        :return: dict with Tango channels
        :rtype: dict<str, list[DeviceProxy, CaselessDict<str, dict>]>
        """
        if not only_enabled:
            return self.tango_dev_channels
        tango_dev_channels = {}
        for dev_name, dev_data in list(self.tango_dev_channels.items()):
            dev_proxy, attrs = dev_data[0], copy.deepcopy(dev_data[1])
            for attr_name, channel_data in list(attrs.items()):
                if not channel_data["enabled"]:
                    attrs.pop(attr_name)
            tango_dev_channels[dev_name] = [dev_proxy, attrs]
        return tango_dev_channels

    def read(self, parallel=True):
        if parallel:
            return self._read_parallel()
        return self._read()

    def _read_parallel(self):
        self.prepare()
        ret = CaselessDict(self.cache)
        dev_replies = {}

        # deposit read requests
        tango_dev_channels = self.getTangoDevChannels(only_enabled=True)
        for _, dev_data in list(tango_dev_channels.items()):
            dev, attrs = dev_data
            if dev is None:
                continue
            try:
                dev_replies[dev] = dev.read_attributes_asynch(
                    list(attrs.keys())), attrs
            except Exception:
                dev_replies[dev] = None, attrs

        # gather all replies
        for dev, reply_data in list(dev_replies.items()):
            reply, attrs = reply_data
            try:
                data = dev.read_attributes_reply(reply, 0)
                for data_item in data:
                    channel_data = attrs[data_item.name]
                    if data_item.has_failed:
                        value = None
                    else:
                        value = data_item.value
                    ret[channel_data['full_name']] = value
            except Exception:
                for _, channel_data in list(attrs.items()):
                    ret[channel_data['full_name']] = None

        return ret

    def _read(self):
        self.prepare()
        ret = CaselessDict(self.cache)
        tango_dev_channels = self.getTangoDevChannels(only_enabled=True)
        for _, dev_data in list(tango_dev_channels.items()):
            dev, attrs = dev_data
            try:
                data = dev.read_attributes(list(attrs.keys()))
                for data_item in data:
                    channel_data = attrs[data_item.name]
                    if data_item.has_failed:
                        value = None
                    else:
                        value = data_item.value
                    ret[channel_data['full_name']] = value
            except Exception:
                for _, channel_data in list(attrs.items()):
                    ret[channel_data['full_name']] = None
        return ret

    def _get_channel_data(self, channel_name):
        if channel_name in self.channels_names:
            return self.channels_names[channel_name]
        elif channel_name in self.channels_labels:
            return self.channels_labels[channel_name]
        elif channel_name in self.channels:
            return self.channels[channel_name]
        v = TangoDeviceNameValidator()
        names = v.getNames(channel_name)
        msg = 'element "{}" is not in {}'.format(channel_name, self.label)
        if names is None:
            v = TangoAttributeNameValidator()
            names = v.getNames(channel_name)
            if names is None:
                raise KeyError(msg)
        full_name = names[0]
        data = self.channels.get(full_name)
        if data is None:
            raise KeyError(msg)
        return data

    def _get_ctrl_data(self, ctrl_name):
        if ctrl_name in self.controllers_names:
            return self.controllers_names[ctrl_name]
        elif ctrl_name in self.controllers:
            return self.controllers[ctrl_name]
        v = TangoDeviceNameValidator()
        names = v.getNames(ctrl_name)
        msg = 'element "{}" is not in {}'.format(ctrl_name, self.label)
        if names is None:
            raise KeyError(msg)
        full_name = names[0]
        data = self.controllers.get(full_name)
        if data is None:
            raise KeyError(msg)
        return data

    def _set_channels_key(self, key, value, channels_names=None,
                          apply_cfg=True):

        self._local_changes = True
        if channels_names is None:
            channels_names = self.channels.keys()
        # Protections:
        if key in ['enabled', 'output']:
            if type(value) != bool:
                raise ValueError('The value must be a boolean')

        for channel_name in channels_names:
            channel = self._get_channel_data(channel_name)
            channel[key] = value
        if apply_cfg:
            self.applyConfiguration()

    def _get_channels_key(self, key, channels_names=None, use_fullname=False):
        """
        Helper method to return the value for one channel configuration key,
        if the key does not exist the value will be None.
        """
        result = collections.OrderedDict({})

        if channels_names is None:
            channels_names = self.channel_list_name

        for channel_name in channels_names:
            channel = self._get_channel_data(channel_name)
            if use_fullname:
                label = channel['full_name']
            else:
                label = channel['label']
            try:
                value = channel[key]
            except KeyError:
                result[label] = None
                continue
            if key == 'plot_axes':
                res = []
                for v in value:
                    if v not in ['<mov>', '<idx>']:
                        v = self.channels[v]['label']
                    res.append(v)
                value = res
            result[label] = value
        return result

    def _set_ctrls_key(self, key, value, ctrls_names=None, apply_cfg=True):
        self._local_changes = True
        if ctrls_names is None:
            ctrls_names = self.controllers.keys()

        for ctrl_name in ctrls_names:
            # if ctrl_name == '__tango__':
            #     continue
            ctrl = self._get_ctrl_data(ctrl_name)
            ctrl[key] = value
        if apply_cfg:
            self.applyConfiguration()

    def _get_ctrls_key(self, key, ctrls_names=None, use_fullname=False):
        """
        Helper method to return the value for one controller configuration key,
        if the key does not exist the value will be None.
        """
        result = collections.OrderedDict({})
        if ctrls_names is None:
            ctrls_names = self.controller_list_name

        for ctrl_name in ctrls_names:
            if ctrl_name == '__tango__':
                result[ctrl_name] = None
                continue
            ctrl = self._get_ctrl_data(ctrl_name)

            if use_fullname:
                label = ctrl_name
            else:
                label = DeviceProxy(ctrl_name).alias()

            try:
                value = ctrl[key]
            except KeyError:
                result[label] = None
                continue

            if key in ['timer', 'monitor']:
                value = self.channels[value]['label']
            elif key == 'synchronizer' and value != 'software':
                value = DeviceProxy(value).alias()

            result[label] = value
        return result

    def _get_ctrl_for_channel(self, channels_names, unique=False):
        result = collections.OrderedDict({})

        if channels_names is None:
            channels_names = self.channel_list_name

        for channel_name in channels_names:
            channel = self._get_channel_data(channel_name)
            try:
                ctrl = channel['_controller_name']
            except KeyError:
                ctrl = '__tango__'
            if unique and ctrl in result.values():
                raise KeyError('There are more than one channel of the same '
                               'controller')
            result[channel['full_name']] = ctrl

        return result

    def _get_ctrl_channels(self, ctrl, use_fullname=False):
        idx_channel = {}
        if ctrl not in self.controllers_channels:
            ctrl = self.controllers_alias[ctrl]
        channels_datas = self.controllers_channels[ctrl]
        for channel_data in channels_datas:
            if use_fullname:
                name = channel_data['fullname']
            else:
                name = channel_data['label']
            idx = channel_data['index']
            idx_channel[idx] = name
        channels = []
        for idx in sorted(idx_channel):
            channels.append(idx_channel[idx])

        return channels

    def _get_channels_for_element(self, element, use_fullname=False):
        channels = []
        if element in self.controllers_channels:
            channels += self._get_ctrl_channels(element, use_fullname)
        else:
            channels += [element]
        return channels

    def _get_ctrl_for_element(self, element):
        if element in self.controllers_channels:
            ctrl = element
        else:
            # TODO: find more elegant way
            channel_ctrl = self._get_ctrl_for_channel([element])
            ctrl = list(channel_ctrl.values())[0]
        return ctrl

    def applyConfiguration(self, timeout=3):
        if not self._local_changes:
            return
        if self._pending_event_data is not None:
            self.set_data(self._pending_event_data, force=True)
            raise RuntimeError('The configuration changed on the server '
                               'during your changes.')
        mg = self._mg()
        try:
            mg.setConfiguration(self._raw_data)
        except Exception as e:
            self._local_changes = False
            self._pending_event_data = None
            data = mg.getConfigurationAttrEG().readValue(force=True)
            self.set_data(data, force=True)
            raise e
        self._local_changes = False
        self._pending_event_data = None
        if not mg._flg_event.wait(timeout):
            raise RuntimeError('timeout on applying configuration')

    def _getValueRefEnabledChannels(self, channels=None, use_fullname=False):
        """get acquisition Enabled channels.

        :param channels: (seq<str>) a list of channels names to get the
        Enabled info
        :param use_fullname: (bool) returns a full name instead sardana
        element name

        :return a OrderedDict where the key are the channels and value the
        Enabled state
        """

        return self._get_channels_key('value_ref_enabled', channels,
                                      use_fullname)

    def _setValueRefEnabledChannels(self, state, channels=None,
                                    apply_cfg=True):
        """Enable acquisition of the indicated channels.

        :param state: <bool> The state of the channels to be set.
        :param channels: (seq<str>) a sequence of strings indicating
                         channel names
        """
        self._set_channels_key('value_ref_enabled', state, channels, apply_cfg)

    def _getValueRefPatternChannels(self, channels=None, use_fullname=False):
        """get acquisition Enabled channels.

        :param channels: (seq<str>) a list of channels names to get the
        Enabled info
        :param use_fullname: (bool) returns a full name instead sardana
        element name

        :return a OrderedDict where the key are the channels and value the
        Enabled state
        """

        return self._get_channels_key('value_ref_pattern', channels,
                                      use_fullname)

    def _setValueRefPatternChannels(self, pattern, channels=None,
                                    apply_cfg=True):
        """Enable acquisition of the indicated channels.

        :param pattern: <str> The state of the channels to be set.
        :param channels: (seq<str>) a sequence of strings indicating
                         channel names
        """
        self._set_channels_key('value_ref_pattern', pattern, channels,
                               apply_cfg)

    def _getEnabledChannels(self, channels=None, use_fullname=False):
        """get acquisition Enabled channels.

        :param channels: (seq<str>) a list of channels names to get the
        Enabled info
        :param use_fullname: (bool) returns a full name instead sardana
        element name

        :return a OrderedDict where the key are the channels and value the
        Enabled state
        """

        return self._get_channels_key('enabled', channels, use_fullname)

    def _setEnabledChannels(self, state, channels=None, apply_cfg=True):
        """Enable acquisition of the indicated channels.

        :param state: <bool> The state of the channels to be set.
        :param channels: (seq<str>) a sequence of strings indicating
                         channel names
        """
        self._set_channels_key('enabled', state, channels, apply_cfg)

    def _getOutputChannels(self, channels=None, use_fullname=False):
        """get the output State of the channels.

        :param channels: (list<str>) a string indicating the channel name,
        in case of None, it will return all the Outputs Info
        :param use_fullname: (bool) returns a full name instead sardana
        element name

        :return a OrderedDict where keys are channel names and
        value the Outputs configuration
        """

        return self._get_channels_key('output', channels, use_fullname)

    def _setOutputChannels(self, state, channels=None, apply_cfg=True):
        """Set the Output state of the indicated channels.

        :param state: (bool) Indicate the state of the output.
        :param channels: (seq<str>) a sequence of strings indicating
                         channel names
        """

        self._set_channels_key('output', state, channels, apply_cfg)

    def _getPlotTypeChannels(self, channels=None, use_fullname=False):
        """get the Plot Type for the channel indicated. In case of empty
        channel value it will return  all the Plot Type Info

        :param channels: (list<str>) Indicate the channel to return the
        Plot Type Info
        :param use_fullname: (bool) returns a full name instead sardana
        element name

        :return  a OrderedDict where keys are channel names and
        value the plot axes info
        """
        # TODO: Change to return enum value SEP12
        return self._get_channels_key('plot_type', channels, use_fullname)

    def _setPlotTypeChannels(self, ptype, channels=None, apply_cfg=True):
        """Set the Plot Type for the indicated channels.

        :param ptype: <str> string indicating the type name
        :param channels: (seq<str>) a list of strings indicating the channels
        to apply the PlotType
        """

        msg_error = 'Wrong value! PlotType allowed: ' \
                    '{0}'.format(PlotType.keys())
        if type(ptype) == str:
            if ptype.lower() not in map(str.lower, PlotType.keys()):
                raise ValueError(msg_error)
            for value in PlotType.keys():
                if value.lower() == ptype.lower():
                    ptype = PlotType[value]
                    break
        elif type(ptype) == int:
            try:
                PlotType[ptype]
            except Exception:
                raise ValueError(msg_error)
        else:
            raise ValueError()
        self._set_channels_key('plot_type', ptype, channels, apply_cfg)

    def _getPlotAxesChannels(self, channels=None, use_fullname=False):
        """get the PlotAxes for the channel indicated. In case of empty channel
        value it will return  all the PlotAxes Info

        :param channels: (list<str>) Indicate the channel to return the
        PlotAxes Info
        :param use_fullname: (bool) returns a full name instead sardana
        element name

        :return  a OrderedDict where keys are channel names and
        value the plot axes info
        """

        return self._get_channels_key('plot_axes', channels, use_fullname)

    def _setPlotAxesChannels(self, axes, channels_names=None, apply_cfg=True):
        """Set the PlotAxes for the indicated channels.

        :param axes: <seq(str)> string indicating the axis name
        :param channels_names: (seq<str>) a list of strings indicating the
        channels to apply the PlotAxes
        """
        # Validate axes values
        for i, value in enumerate(axes):
            if value in ['<idx>', '<mov>']:
                continue
            else:
                axes[i] = self._get_channel_data(value)["full_name"]

        if channels_names is None:
            channels_names = self.channels.keys()

        for channel_name in channels_names:
            channel_data = self._get_channel_data(channel_name)

            # Check the current channel plot type
            plot_type = PlotType[PlotType[channel_data['plot_type']]]
            if plot_type == PlotType.No:
                raise RuntimeError('You must set firs the PlotType')
            elif plot_type == PlotType.Spectrum:
                if len(axes) != 1:
                    raise ValueError('The Spectrum Type only allows one axis')
            elif plot_type == PlotType.Image:
                if len(axes) != 2:
                    raise ValueError('The Image Type only allows two axis')

        self._set_channels_key('plot_axes',  axes, [channel_name], apply_cfg)

    def _getCtrlsTimer(self, ctrls=None, use_fullname=False):
        """get the acquisition Timer.

        :param ctrls: <list(str)> list of Controllers names to get the timer
        info
        :param use_fullname: <bool> returns a full name instead sardana
        element name

        :return a OrderedDict where keys are controller names and
        value the Timer Info
        """

        return self._get_ctrls_key('timer', ctrls, use_fullname)

    def _setCtrlsTimer(self, timers, apply_cfg=True):
        """Set the acquisition Timer to the controllers compatibles,
        it finds the controller comptible with this timer and set it
        .
        :param timer_name: <str> strings indicating the timer name
        """
        result = self._get_ctrl_for_channel(timers, unique=True)
        meas_ctrl = self.channels[self.timer]['_controller_name']

        for timer, ctrl in result.items():
            if ctrl == meas_ctrl:
                self._local_changes = True
                self._raw_data['timer'] = timer
            self._set_ctrls_key('timer', timer, [ctrl], apply_cfg)

    def _getCtrlsMonitor(self, ctrls=None, use_fullname=False):
        """get the Monitor for the channel indicated. In case of empty channel
        value it will return  all the Monitor Info

        :param ctrls: <str> Indicate the controllers to return the Monitor Info
        :param use_fullname: <bool> returns a full name instead sardana
        element name

        :return  a OrderedDict where keys are channel names and
        value the Monitor Info
        """

        return self._get_ctrls_key('monitor', ctrls, use_fullname)

    def _setCtrlsMonitor(self, monitors, apply_cfg=True):
        """Set the Monitor for to the controllers compatibles,
        it finds the controller comptible with this timer and set it

        :param monitors: (seq<str>) a list of strings indicating the channels
        to apply the monitor
        :param monitor: <str> string indicating the monitor name
        """

        result = self._get_ctrl_for_channel(monitors, unique=True)
        meas_ctrl = self.channels[self.monitor]['_controller_name']

        for monitor, ctrl in result.items():
            if ctrl == meas_ctrl:
                self._local_changes = True
                self._raw_data['monitor'] = monitor
            self._set_ctrls_key('monitor', monitor, [ctrl], apply_cfg)

    def _getCtrlsSynchronization(self, ctrls=None, use_fullname=False):
        """get the Synchronization for the channel indicated. In case of empty
        ctrl value it will return  all the Synchronization Info

        :param ctrl: <str> Indicate the controllers to return the
        Synchronization Info
        :param use_fullname: <bool> returns a full name instead sardana
        element name

        :return  a OrderedDict where keys are controllers names and
        value the Synchronization Info
        """

        return self._get_ctrls_key('synchronization', ctrls, use_fullname)

    def _setCtrlsSynchronization(self, synchronization, ctrls=None,
                                 apply_cfg=True):
        """Set the Synchronization to the indicated controllers.

        :param synchronization: <str> string indicating the synchronization
        :param ctrls: (seq<str>) a list of strings indicating the channels
        to apply the Synchronization
        name
        """
        msg_error = 'Wrong value! Synchronization allowed: ' \
                    '{0}'.format(AcqSynchType.keys())
        if type(synchronization) == str:
            if synchronization.lower() not in map(str.lower,
                                                  AcqSynchType.keys()):
                raise ValueError(msg_error)
            for value in AcqSynchType.keys():
                if value.lower() == synchronization.lower():
                    synchronization = AcqSynchType[value]
                    break
        elif type(synchronization) == int:
            try:
                AcqSynchType[synchronization]
            except Exception:
                raise ValueError(msg_error)
        else:
            raise ValueError()
        self._set_ctrls_key('synchronization', synchronization, ctrls,
                            apply_cfg)

    def _getCtrlsSynchronizer(self, ctrls=None, use_fullname=False):
        """get the synchronizer for the channel indicated. In case of empty
        channel value it will return  all the Synchronizers Info

        :param ctrls: <str> Indicate the controllers to return the
        Synchronizer Info
        :param use_fullname: <bool> returns a full name instead sardana
        element name
        :return  a OrderedDict where keys are controllers names and
        value the synchronizer info
        """

        return self._get_ctrls_key('synchronizer', ctrls, use_fullname)

    def _setCtrlsSynchronizer(self, synchronizer, ctrls=None, apply_cfg=True):
        """Set the synchronizer for the indicated controollers. In case of
        empty ctrls value it will be applied to all the controllers

        :param syncronizer: <str> string indicating the synchronizer name
        :param ctrls: (seq<str>) a list of strings indicating the
        controllers to apply the synchronizer
        """
        if synchronizer == 'software':
            pass
        else:
            # TODO: Improve how to check if the element is a trigger_gate
            sync = Device(synchronizer)
            if 'triggergate' not in sync.fullname:
                raise ValueError('The "{0}" is not a '
                                 'triggergate'.format(synchronizer))
            synchronizer = sync.fullname
        self._set_ctrls_key('synchronizer', synchronizer, ctrls, apply_cfg)

    def _getTimerName(self):
        return self._getTimer()['name']

    def _getTimer(self):
        return self.channels[self.timer]

    def _getTimerValue(self):
        return self._getTimerName()

    def _getMonitorName(self):
        return self._getMonitor()['name']

    def _getMonitor(self):
        return self.channels[self.monitor]

    def getValues(self, parallel=True):
        return self.read(parallel=parallel)

    def _getCounters(self):
        return [c for c in self.getChannels() if c['full_name'] != self.timer]

    def _getChannelNames(self):
        return [ch['name'] for ch in self.getChannels()]

    def _getCounterNames(self):
        return [ch['name'] for ch in self.getCounters()]

    def _getChannelLabels(self):
        return [ch['label'] for ch in self.getChannels()]

    def _getCounterLabels(self):
        return [ch['label'] for ch in self.getCounters()]

    def _getChannel(self, name):
        return self.channels[name]

    def getChannelsEnabledInfo(self):
        """
        Returns information about **only enabled** channels present in the
        measurement group in a form of ordered, based on the channel index,
        list.

        :return: list with channels info
        :rtype: list<TangoChannelInfo>
        """
        return self.getChannelsInfoList(only_enabled=True)

    def getCountersInfo(self):
        return self.getCountersInfoList()

    def setTimer(self, timer, apply_cfg=True):
        """DEPRECATED: Set the Global Timer to the measurement group.

        Also it changes the timer in the controllers with the previous timer.

        :param timer: <str> timer name
        """
        self._mg().warning("setTimer() is deprecated since 3.0.3. "
                           "Global measurement group timer does not exist")
        result = self._get_ctrl_for_channel([timer], unique=True)

        for timer, ctrl in result.items():
            self._local_changes = True
            self._raw_data['timer'] = timer
            self._set_ctrls_key('timer', timer, [ctrl], apply_cfg)

    def getTimer(self):
        """DEPRECATED"""
        self._mg().warning("getTimer() is deprecated since 3.0.3. "
                           "Global measurement group timer does not exist")
        return self._getTimer()

    def getMonitor(self):
        """DEPRECATED"""
        self._mg().warning("getMonitor() is deprecated since 3.0.3. "
                           "Global measurement group monitor does not exist")
        return self._getMonitor()

    def __repr__(self):
        return json.dumps(self._raw_data, indent=4, sort_keys=True)


class MeasurementGroup(PoolElement):
    """MeasurementGroup Sardana-Taurus extension.

    Setting configuration parameters using e.g.,
    `~sardana.taurus.core.tango.sardana.pool.MeasurementGroup.setEnabled` or
    `~sardana.taurus.core.tango.sardana.pool.MeasurementGroup.setTimer`, etc.
    by default applies changes on the server. Since setting the configuration
    means passing to the server all the configuration parameters of
    the measurement group at once this behavior can be changed with the
    ``apply=False``. Then the configuration changes are kept locally.
    This is useful when changing more then one parameter. In this case only
    setting of the last parameter should use ``apply=True`` or use
    `~sardana.taurus.core.tango.sardana.pool.MeasurementGroup.applyConfiguration`
    afterwards::

        # or in a macro use: meas_grp = self.getMeasurementGroup("mntgrp01")
        meas_grp = taurus.Device("mntgrp01")
        meas_grp.setEnabled(False, apply=False)
        meas_grp.setEnabled(True, "ct01", "ct02")
    """

    def __init__(self, name, **kw):
        """PoolElement initialization."""
        self._configuration = None
        self._channels = None
        self._last_integ_time = None
        self.call__init__(PoolElement, name, **kw)

        self._flg_event = threading.Event()
        self.__cfg_attr = self.getAttribute('configuration')
        self.__cfg_attr.addListener(self.on_configuration_changed)

        self._value_buffer_cb = None
        self._value_buffer_channels = None
        codec_name = getattr(sardanacustomsettings, "VALUE_BUFFER_CODEC")
        self._value_buffer_codec = CodecFactory().getCodec(codec_name)

        self._value_ref_buffer_cb = None
        self._value_ref_buffer_channels = None
        codec_name = getattr(sardanacustomsettings, "VALUE_REF_BUFFER_CODEC")
        self._value_ref_buffer_codec = CodecFactory().getCodec(codec_name)

    def cleanUp(self):
        PoolElement.cleanUp(self)
        f = self.factory()
        f.removeExistingAttribute(self.__cfg_attr)

    def _create_str_tuple(self):
        channel_names = ", ".join(self.getChannelNames())
        return self.getName(), self.getTimerName(), channel_names

    def getConfigurationAttrEG(self):
        return self._getAttrEG('Configuration')

    def setConfiguration(self, configuration):
        self._flg_event.clear()
        codec = CodecFactory().getCodec('json')
        f, data = codec.encode(('', configuration))
        self.write_attribute('configuration', data)

    def _setConfiguration(self, data):
        if self._configuration is None:
            self._configuration = MGConfiguration(self, data)
        else:
            self._configuration.set_data(data)

    def getConfiguration(self, force=False):
        if force or self._configuration is None:
            data = self.getConfigurationAttrEG().readValue(force=True)
            self._setConfiguration(data)
        return self._configuration

    def on_configuration_changed(self, evt_src, evt_type, evt_value):
        if evt_type not in CHANGE_EVT_TYPES:
            return
        self.info("Configuration changed")
        self._setConfiguration(evt_value.rvalue)
        self._flg_event.set()

    def getValueBuffers(self):
        value_buffers = []
        for channel_info in self.getChannels():
            channel = Device(channel_info["full_name"])
            value_buffers.append(channel.getValueBuffer())
        return value_buffers

    def getIntegrationTime(self):
        return self._getAttrValue('IntegrationTime')

    def getIntegrationTimeObj(self):
        return self._getAttrEG('IntegrationTime')

    def setIntegrationTime(self, ctime):
        self.getIntegrationTimeObj().write(ctime)

    def putIntegrationTime(self, ctime):
        if self._last_integ_time == ctime:
            return
        self.getIntegrationTimeObj().write(ctime)
        self._last_integ_time = ctime

    def getAcquisitionModeObj(self):
        return self._getAttrEG('AcquisitionMode')

    def getAcquisitionMode(self):
        return self._getAttrValue('AcquisitionMode')

    def setAcquisitionMode(self, acqMode):
        self.getAcquisitionModeObj().write(acqMode)

    def getSynchDescriptionObj(self):
        return self._getAttrEG('SynchDescription')

    def getSynchDescription(self):
        return self._getAttrValue('SynchDescription')

    def setSynchDescription(self, synch_description):
        codec = CodecFactory().getCodec('json')
        _, data = codec.encode(('', synch_description))
        self.getSynchDescriptionObj().write(data)
        self._last_integ_time = None

    def _get_channels_for_elements(self, elements):
        if not elements:
            return None
        config = self.getConfiguration()
        channels = []
        for element in elements:
            channels += config._get_channels_for_element(element)
        return channels

    def _get_ctrl_for_elements(self, elements):
        if not elements:
            return None
        ctrls = []
        config = self.getConfiguration()
        for element in elements:
            ctrl = config._get_ctrl_for_element(element)
            if ctrl in ctrls:
                continue
            ctrls.append(ctrl)
        return ctrls

    def setOutput(self, output, *elements, apply=True):
        """Set the output configuration for the given elements.

        Channels and controllers are accepted as elements. Setting the output
        on the controller means setting it to all channels of this controller
        present in this measurement group.

        :param output: `True` - output enabled, `False` - output disabled
        :type output: bool
        :param elements: sequence of element names or full names, no elements
            means set to all
        :type elements: list(str)
        :param apply: `True` - apply on the server, `False` - do not apply yet
            on the server and keep locally (default: `True`)
        :type apply: bool
        """

        channels = self._get_channels_for_elements(elements)
        config = self.getConfiguration()
        config._setOutputChannels(output, channels, apply_cfg=apply)

    def getOutput(self, *elements, ret_full_name=False):
        """Get the output configuration of the given elements.

        Channels and controllers are accepted as elements. Getting the output
        from the controller means getting it from all channels of this
        controller present in this measurement group.

        :param elements: sequence of element names or full names, no elements
            means get from all
        :type elements: list(str)
        :param ret_full_name: whether keys in the returned dictionary are
            full names or names (default: `False` means return names)
        :type ret_full_name: bool
        :return: ordered dictionary where keys are **channel** names (or full
            names if `ret_full_name=True`) and values are their output
            configurations. Note that even if the *elements* contained
            controllers, the returned configuration will always contain
            only channels.
        :rtype: dict(str, bool)
        """
        channels = self._get_channels_for_elements(elements)
        config = self.getConfiguration()
        return config._getOutputChannels(channels, use_fullname=ret_full_name)

    def setEnabled(self, enabled, *elements, apply=True):
        """Set the enabled configuration for the given elements.

        Channels and controllers are accepted as elements. Setting the enabled
        on the controller means setting it to all channels of this controller
        present in this measurement group.

        :param enabled: `True` - element enabled, `False` - element disabled
        :type enabled: bool
        :param elements: sequence of element names or full names, no elements
            means set to all
        :type elements: list(str)
        :param apply: `True` - apply on the server, `False` - do not apply yet
            on the server and keep locally (default: `True`)
        :type apply: bool
        """

        channels = self._get_channels_for_elements(elements)
        config = self.getConfiguration()
        config._setEnabledChannels(enabled, channels, apply_cfg=apply)

    def getEnabled(self, *elements, ret_full_name=False):
        """Get the output configuration of the given elements.

        Channels and controllers are accepted as elements. Getting the enabled
        from the controller means getting it from all channels of this
        controller present in this measurement group.

        :param elements: sequence of element names or full names, no elements
            means get from all
        :type elements: list(str)
        :param ret_full_name: whether keys in the returned dictionary are
            full names or names (default: `False` means return names)
        :type ret_full_name: bool
        :return: ordered dictionary where keys are **channel** names (or full
            names if `ret_full_name=True`) and values are their output
            configurations. Note that even if the *elements* contained
            controllers, the returned configuration will always contain
            only channels.
        :rtype: dict(str, bool)
        """
        channels = self._get_channels_for_elements(elements)
        config = self.getConfiguration()
        return config._getEnabledChannels(channels, use_fullname=ret_full_name)

    def setPlotType(self, plot_type, *elements, apply=True):
        """Set the enabled configuration for the given elements.

        Channels and controllers are accepted as elements. Setting the plot
        type on the controller means setting it to all channels of this
        controller present in this measurement group.

        :param plot_type: 'No'/0 , 'Spectrum'/1, 'Image'/2
        :type plot_type: str or int
        :param elements: sequence of element names or full names, no elements
            means set to all
        :type elements: list(str)
        :param apply: `True` - apply on the server, `False` - do not apply yet
            on the server and keep locally (default: `True`)
        :type apply: bool
        """

        channels = self._get_channels_for_elements(elements)
        config = self.getConfiguration()
        config._setPlotTypeChannels(plot_type, channels, apply_cfg=apply)

    def getPlotType(self, *elements, ret_full_name=False):
        """Get the output configuration of the given elements.

        Channels and controllers are accepted as elements. Getting the plot
        type from the controller means getting it from all channels of this
        controller present in this measurement group.

        :param elements: sequence of element names or full names, no elements
            means get from all
        :type elements: list(str)
        :param ret_full_name: whether keys in the returned dictionary are
            full names or names (default: `False` means return names)
        :type ret_full_name: bool
        :return: ordered dictionary where keys are **channel** names (or full
            names if `ret_full_name=True`) and values are their output
            configurations. Note that even if the *elements* contained
            controllers, the returned configuration will always contain
            only channels.
        :rtype: dict(str, int)
        """
        channels = self._get_channels_for_elements(elements)
        config = self.getConfiguration()
        # TODO Change the documentation when _getPlotTypeChannels return enum
        #  value
        return config._getPlotTypeChannels(channels,
                                           use_fullname=ret_full_name)

    def setPlotAxes(self, plot_axes, *elements, apply=True):
        """Set the enabled configuration for the given elements.

        Channels and controllers are accepted as elements. Setting the plot
        axes on the controller means setting it to all channels of this
        controller present in this measurement group.

        :param plot_axes: ['<mov>'] / ['<mov>', '<idx>']
        :type plot_axes: list(str)
        :param elements: sequence of element names or full names, no elements
            means set to all
        :type elements: list(str)
        :param apply: `True` - apply on the server, `False` - do not apply yet
            on the server and keep locally (default: `True`)
        :type apply: bool
        """

        channels = self._get_channels_for_elements(elements)
        config = self.getConfiguration()
        config._setPlotAxesChannels(plot_axes, channels, apply_cfg=apply)

    def getPlotAxes(self, *elements, ret_full_name=False):
        """Get the output configuration of the given elements.

        Channels and controllers are accepted as elements. Getting the plot
        axes from the controller means getting it from all channels of this
        controller present in this measurement group.

        :param elements: sequence of element names or full names, no elements
            means get from all
        :type elements: list(str)
        :param ret_full_name: whether keys in the returned dictionary are
            full names or names (default: `False` means return names)
        :type ret_full_name: bool
        :return: ordered dictionary where keys are **channel** names (or full
            names if `ret_full_name=True`) and values are their output
            configurations. Note that even if the *elements* contained
            controllers, the returned configuration will always contain
            only channels.
        :rtype: dict(str, str)
        """
        channels = self._get_channels_for_elements(elements)
        config = self.getConfiguration()
        return config._getPlotAxesChannels(channels,
                                           use_fullname=ret_full_name)

    def setValueRefEnabled(self, value_ref_enabled, *elements, apply=True):
        """Set the output configuration for the given elements.

        Channels and controllers are accepted as elements. Setting the value
        reference enabled on the controller means setting it to all channels
        of this controller present in this measurement group.

        :param value_ref_enabled: `True` - enabled, `False` - disabled
        :type value_ref_enabled: bool
        :param elements: sequence of element names or full names, no elements
            means set to all
        :type elements: list(str)
        :param apply: `True` - apply on the server, `False` - do not apply yet
            on the server and keep locally (default: `True`)
        :type apply: bool
        """

        channels = self._get_channels_for_elements(elements)
        config = self.getConfiguration()
        config._setValueRefEnabledChannels(value_ref_enabled, channels,
                                           apply_cfg=apply)

    def getValueRefEnabled(self, *elements, ret_full_name=False):
        """Get the value reference enabled configuration of the given elements.

        Channels and controllers are accepted as elements. Getting the value
        from the controller means getting it from all channels of this
        controller present in this measurement group.

        :param elements: sequence of element names or full names, no elements
            means get from all
        :type elements: list(str)
        :param ret_full_name: whether keys in the returned dictionary are
            full names or names (default: `False` means return names)
        :type ret_full_name: bool
        :return: ordered dictionary where keys are **channel** names (or full
            names if `ret_full_name=True`) and values are their output
            configurations. Note that even if the *elements* contained
            controllers, the returned configuration will always contain
            only channels.
        :rtype: dict(str, bool)
        """
        channels = self._get_channels_for_elements(elements)
        config = self.getConfiguration()
        return config._getValueRefEnabledChannels(channels,
                                                  use_fullname=ret_full_name)

    def setValueRefPattern(self, value_ref_pattern, *elements, apply=True):
        """Set the output configuration for the given elements.

        Channels and controllers are accepted as elements. Setting the value
        reference pattern on the controller means setting it to all channels
        of this controller present in this measurement group.

        :param value_ref_pattern: `/path/file{index:03d}.txt`
        :type value_ref_pattern: :py:obj:`str`
        :param elements: sequence of element names or full names, no elements
            means set to all
        :type elements: list(str)
        :param apply: `True` - apply on the server, `False` - do not apply yet
            on the server and keep locally (default: `True`)
        :type apply: bool
        """

        channels = self._get_channels_for_elements(elements)
        config = self.getConfiguration()
        config._setValueRefPatternChannels(value_ref_pattern, channels,
                                           apply_cfg=apply)

    def getValueRefPattern(self, *elements, ret_full_name=False):
        """Get the value reference enabled configuration of the given elements.

        Channels and controllers are accepted as elements. Getting the value
        from the controller means getting it from all channels of this
        controller present in this measurement group.

        :param elements: sequence of element names or full names, no elements
            means get from all
        :type elements: list(str)
        :param ret_full_name: whether keys in the returned dictionary are
            full names or names (default: `False` means return names)
        :type ret_full_name: bool
        :return: ordered dictionary where keys are **channel** names (or full
            names if `ret_full_name=True`) and values are their output
            configurations. Note that even if the *elements* contained
            controllers, the returned configuration will always contain
            only channels.
        :rtype: dict(str, str)
        """
        channels = self._get_channels_for_elements(elements)
        config = self.getConfiguration()
        return config._getValueRefPatternChannels(channels,
                                                  use_fullname=ret_full_name)

    def _get_value_per_channel(self, config, ctrls_values, use_fullname=False):
        channels_values = collections.OrderedDict({})
        for ctrl, value in ctrls_values.items():
            for channel in config._get_ctrl_channels(ctrl, use_fullname):
                channels_values[channel] = value
        return channels_values

    def setTimer(self, timer, *elements, apply=True):
        """Set the timer configuration for the given channels of the same
        controller.

        .. note:: Currently the controller's timer must be unique. Hence this
           method will set it for the whole controller regardless of the
           ``elements`` argument.

        :param timer: channel use as timer
        :type timer: :py:obj:`str`
        :param elements: sequence of channels names or full names, no elements
            means set to all
        :type elements: list(str)
        :param apply: `True` - apply on the server, `False` - do not apply yet
            on the server and keep locally (default: `True`)
        :type apply: bool
        """
        config = self.getConfiguration()
        # TODO: Implement solution to set the timer per channel when it is
        #  allowed.
        config._setCtrlsTimer([timer], apply_cfg=apply)

    def getTimer(self, *elements, ret_full_name=False, ret_by_ctrl=False):
        """Get the timer configuration of the given elements.

        Channels and controllers are accepted as elements. Getting the output
        from the controller means getting it from all channels of this
        controller present in this measurement group, unless
        `ret_by_ctrl=True`.

        :param elements: sequence of element names or full names, no elements
            means get from all
        :type elements: list(str)
        :param ret_full_name: whether keys in the returned dictionary are
            full names or names (default: `False` means return names)
        :type ret_full_name: bool
        :param ret_by_ctrl: whether keys in the returned dictionary are
            controllers or channels (default: `False` means return channels)
        :type ret_by_ctrl: bool
        :return: ordered dictionary where keys are **channel** names (or full
            names if `ret_full_name=True`) and values are their timer
            configurations
        :rtype: dict(str, str)
        """
        # TODO: Implement solution to set the timer per channel when it is
        #  allowed.
        ctrls = self._get_ctrl_for_elements(elements)
        config = self.getConfiguration()
        ctrls_timers = config._getCtrlsTimer(ctrls, use_fullname=ret_full_name)
        if ret_by_ctrl:
            return ctrls_timers
        else:
            return self._get_value_per_channel(config, ctrls_timers,
                                               use_fullname=ret_full_name)

    def setMonitor(self, monitor, *elements, apply=True):
        """Set the monitor configuration for the given channels of the same
        controller.

        .. note:: Currently the controller's monitor must be unique.
           Hence this method will set it for the whole controller regardless of
           the ``elements`` argument.

        :param monitor: channel use as monitor
        :type monitor: :py:obj:`str`
        :param elements: sequence of channels names or full names, no elements
            means set to all
        :type elements: list(str)
        :param apply: `True` - apply on the server, `False` - do not apply yet
            on the server and keep locally (default: `True`)
        :type apply: bool
        """
        config = self.getConfiguration()
        # TODO: Implement solution to set the moniotor per channel when it is
        #  allowed.
        config._setCtrlsMonitor([monitor], apply_cfg=apply)

    def getMonitor(self, *elements, ret_full_name=False, ret_by_ctrl=False):
        """Get the monitor configuration of the given elements.

        Channels and controllers are accepted as elements. Getting the output
        from the controller means getting it from all channels of this
        controller present in this measurement group, unless
        `ret_by_ctrl=True`.

        :param elements: sequence of element names or full names, no elements
            means get from all
        :type elements: list(str)
        :param ret_full_name: whether keys in the returned dictionary are
            full names or names (default: `False` means return names)
        :type ret_full_name: bool
        :param ret_by_ctrl: whether keys in the returned dictionary are
            controllers or channels (default: `False` means return channels)
        :type ret_by_ctrl: bool
        :return: ordered dictionary where keys are **channel** names (or full
            names if `ret_full_name=True`) and values are their monitor
            configurations
        :rtype: dict(str, str)
        """
        # TODO: Implement solution to set the timer per channel when it is
        #  allowed.
        ctrls = self._get_ctrl_for_elements(elements)
        config = self.getConfiguration()
        ctrls_monitor = config._getCtrlsMonitor(ctrls,
                                                use_fullname=ret_full_name)
        if ret_by_ctrl:
            return ctrls_monitor
        else:
            return self._get_value_per_channel(config, ctrls_monitor,
                                               use_fullname=ret_full_name)

    def setSynchronizer(self, synchronizer, *elements, apply=True):
        """Set the synchronizer configuration for the given channels or
        controller.

        .. note:: Currently the controller's synchronizer must be unique.
           Hence this method will set it for the whole controller regardless of
           the ``elements`` argument.

        :param synchronizer: triger/gate element name or software
        :type synchronizer: :py:obj:`str`
        :param elements: sequence of channels names or full names, no elements
            means set to all
        :type elements: list(str)
        :param apply: `True` - apply on the server, `False` - do not apply yet
            on the server and keep locally (default: `True`)
        :type apply: bool
        """
        config = self.getConfiguration()
        # TODO: Implement solution to set the timer per channel when it is
        #  allowed.
        ctrls = self._get_ctrl_for_elements(elements)
        config._setCtrlsSynchronizer(synchronizer, ctrls, apply_cfg=apply)

    def getSynchronizer(self, *elements, ret_full_name=False,
                        ret_by_ctrl=False):
        """Get the synchronizer configuration of the given elements.

        Channels and controllers are accepted as elements. Getting the output
        from the controller means getting it from all channels of this
        controller present in this measurement group, unless
        `ret_by_ctrl=True`.

        :param elements: sequence of element names or full names, no elements
            means get from all
        :type elements: list(str)
        :param ret_full_name: whether keys in the returned dictionary are
            full names or names (default: `False` means return names)
        :type ret_full_name: bool
        :param ret_by_ctrl: whether keys in the returned dictionary are
            controllers or channels (default: `False` means return channels)
        :type ret_by_ctrl: bool
        :return: ordered dictionary where keys are **channel** names (or full
            names if `ret_full_name=True`) and values are their synchronizer
            configurations
        :rtype: dict(str, str)
        """
        # TODO: Implement solution to set the synchronizer per channel when it
        #  is allowed.
        ctrls = self._get_ctrl_for_elements(elements)
        config = self.getConfiguration()
        ctrls_sync = config._getCtrlsSynchronizer(ctrls,
                                                  use_fullname=ret_full_name)
        if ret_by_ctrl:
            return ctrls_sync
        else:
            return self._get_value_per_channel(config, ctrls_sync,
                                               use_fullname=ret_full_name)

    def setSynchronization(self, synchronization, *elements, apply=True):
        """Set the synchronization configuration for the given channels or
        controller.

        .. note:: Currently the controller's synchronization must be unique.
           Hence this method will set it for the whole controller regardless of
           the ``elements`` argument.

        :param synchronization: synchronization type e.g. Trigger, Gate or
          Start
        :type synchronization: `sardana.pool.AcqSynchType`
        :param elements: sequence of channels names or full names, no elements
            means set to all
        :type elements: list(str)
        :param apply: `True` - apply on the server, `False` - do not apply yet
            on the server and keep locally (default: `True`)
        :type apply: bool
        """
        config = self.getConfiguration()
        # TODO: Implement solution to set the synchronization per channel when
        #  it is allowed.
        ctrls = self._get_ctrl_for_elements(elements)
        config._setCtrlsSynchronization(synchronization, ctrls,
                                        apply_cfg=apply)

    def getSynchronization(self, *elements, ret_full_name=False,
                           ret_by_ctrl=False):
        """Get the synchronization configuration of the given elements.

        Channels and controllers are accepted as elements. Getting the output
        from the controller means getting it from all channels of this
        controller present in this measurement group, unless
        `ret_by_ctrl=True`.

        :param elements: sequence of element names or full names, no elements
            means get from all
        :type elements: list(str)
        :param ret_full_name: whether keys in the returned dictionary are
            full names or names (default: `False` means return names)
        :type ret_full_name: bool
        :param ret_by_ctrl: whether keys in the returned dictionary are
            controllers or channels (default: `False` means return channels)
        :type ret_by_ctrl: bool
        :return: ordered dictionary where keys are **channel** names (or full
            names if `ret_full_name=True`) and values are their
            synchronization configurations
        :rtype: dict<`str`, `sardana.pool.AcqSynchType`>
        """
        # TODO: Implement solution to set the synchronization per channel
        #  when it is allowed.
        ctrls = self._get_ctrl_for_elements(elements)
        config = self.getConfiguration()
        ctrls_sync = \
            config._getCtrlsSynchronization(ctrls, use_fullname=ret_full_name)
        if ret_by_ctrl:
            return ctrls_sync
        else:
            return self._get_value_per_channel(config, ctrls_sync,
                                               use_fullname=ret_full_name)

    def applyConfiguration(self):
        """Apply configuration changes kept locally on the server.

        Setting configuration parameters using e.g.,
        `~sardana.taurus.core.tango.sardana.pool.MeasurementGroup.setEnabled`
        or
        `~sardana.taurus.core.tango.sardana.pool.MeasurementGroup.setTimer`,
        etc.
        with ``apply=False`` keeps the changes locally. Use this method to
        apply them on the server afterwards.
        """
        self.getConfiguration().applyConfiguration()

    #########################################################################
    # TODO: review the following API

    def getChannelsEnabledInfo(self):
        """Returns information about **only enabled** channels present in the
        measurement group in a form of ordered, based on the channel index,
        list.
        :return: list with channels info
        :rtype: list<TangoChannelInfo>
        """
        return self.getConfiguration().getChannelsInfoList(only_enabled=True)

    def getCountersInfo(self):
        return self.getConfiguration().getCountersInfoList()

    def getValues(self, parallel=True):
        return self.getConfiguration().getValues(parallel)

    def getChannels(self):
        return self.getConfiguration().getChannels()

    def getCounters(self):
        return self.getConfiguration()._getCounters()

    def getChannelNames(self):
        return self.getConfiguration()._getChannelNames()

    def getCounterNames(self):
        return self.getConfiguration()._getCounterNames()

    def getChannelLabels(self):
        return self.getConfiguration()._getChannelLabels()

    def getCounterLabels(self):
        return self.getConfiguration()._getCounterLabels()

    def getChannel(self, name):
        return self.getConfiguration()._getChannel(name)

    def getChannelInfo(self, name):
        return self.getConfiguration().getChannelInfo(name)

    #########################################################################

    def getChannelsInfo(self):
        """DEPRECATED"""
        self.warning('Deprecation warning: you should use '
                     '"getChannelsInfoList" instead of "getChannelsInfo"')
        return self.getConfiguration().getChannelsInfoList()

    def getMonitorName(self):
        """DEPRECATED"""
        self.warning("getMonitorName() is deprecated since 3.0.3. "
                     "Global measurement group monitor does not exist.")
        return self.getConfiguration()._getMonitorName()

    def getTimerName(self):
        """DEPRECATED"""
        self.warning("getTimerName() is deprecated since 3.0.3. "
                     "Global measurement group timer does not exist.")
        return self.getConfiguration()._getTimerName()

    def getTimerValue(self):
        """DEPRECATED"""
        self.warning("getTimerValue() is deprecated since 3.0.3. "
                     "Global measurement group timer does not exist.")
        return self.getConfiguration()._getTimerValue()

    def enableChannels(self, channels):
        '''DEPRECATED: Enable acquisition of the indicated channels.

        :param channels: (seq<str>) a sequence of strings indicating
           channel names
        '''
        self.warning("enableChannels() in deprecated since 3.0.3. "
                     "Use setEnabled() instead.")
        self.setEnabled(True, *channels)

    def disableChannels(self, channels):
        '''DEPRECATED: Disable acquisition of the indicated channels.

        :param channels: (seq<str>) a sequence of strings indicating
           channel names
        '''
        self.warning("enableChannels() in deprecated since 3.0.3. "
                     "Use setEnabled() instead.")
        self.setEnabled(False, *channels)

    # NbStarts Methods
    def getNbStartsObj(self):
        return self._getAttrEG('NbStarts')

    def setNbStarts(self, starts):
        self.getNbStartsObj().write(starts)

    def getNbStarts(self):
        return self._getAttrValue('NbStarts')

    def getMoveableObj(self):
        return self._getAttrEG('Moveable')

    def getMoveable(self):
        return self._getAttrValue('Moveable')

    def getLatencyTimeObj(self):
        return self._getAttrEG('LatencyTime')

    def getLatencyTime(self):
        return self._getAttrValue('LatencyTime')

    def setMoveable(self, moveable=None):
        if moveable is None:
            moveable = 'None'  # Tango attribute is of type DevString
        self.getMoveableObj().write(moveable)

    def valueBufferChanged(self, channel, value_buffer):
        """Receive value buffer updates, pre-process them, and call
        the subscribed callback.

        :param channel: channel that reports value buffer update
        :type channel: ExpChannel
        :param value_buffer: json encoded value buffer update, it contains
            at least values and indexes
        :type value_buffer: :obj:`str`
        """
        if value_buffer is None:
            return
        _, value_buffer = self._value_buffer_codec.decode(value_buffer)
        values = value_buffer["value"]
        if isinstance(values[0], list):
            np_values = list(map(numpy.array, values))
            value_buffer["value"] = np_values
        self._value_buffer_cb(channel, value_buffer)

    def subscribeValueBuffer(self, cb=None):
        """Subscribe to channels' value buffer update events. If no
        callback is passed, the default channel's callback is subscribed which
        will store the data in the channel's value_buffer attribute.

        :param cb: callback to be subscribed, None means subscribe the default
            channel's callback
        :type cb: callable
        """
        self._value_buffer_channels = []
        for channel_info in self.getChannels():
            full_name = channel_info["full_name"]
            value_ref_enabled = channel_info.get("value_ref_enabled", False)
            # Use DeviceProxy instead of taurus to avoid crashes in Py3
            # See: tango-controls/pytango#292
            if _is_referable(full_name) and value_ref_enabled:
                continue
            channel = Device(full_name)
            value_buffer_obj = channel.getValueBufferObj()
            if cb is not None:
                self._value_buffer_cb = cb
                value_buffer_obj.subscribeEvent(self.valueBufferChanged,
                                                channel, False)
            else:
                value_buffer_obj.subscribeEvent(channel.valueBufferChanged,
                                                with_first_event=False)
            self._value_buffer_channels.append(channel)

    def unsubscribeValueBuffer(self, cb=None):
        """Unsubscribe from channels' value buffer events. If no callback is
        passed, unsubscribe the channel's default callback.

        :param cb: callback to be unsubscribed, None means unsubscribe the
            default channel's callback
        :type cb: callable
        """
        for channel_info in self.getChannels():
            full_name = channel_info["full_name"]
            value_ref_enabled = channel_info.get("value_ref_enabled", False)
            # Use DeviceProxy instead of taurus to avoid crashes in Py3
            # See: tango-controls/pytango#292
            if _is_referable(full_name) and value_ref_enabled:
                continue
            channel = Device(full_name)
            value_buffer_obj = channel.getValueBufferObj()
            if cb is not None:
                value_buffer_obj.unsubscribeEvent(self.valueBufferChanged,
                                                  channel)
                self._value_buffer_cb = None
            else:
                value_buffer_obj.unsubscribeEvent(channel.valueBufferChanged)
        self._value_buffer_channels = None

    def valueRefBufferChanged(self, channel, value_ref_buffer):
        """Receive value ref buffer updates, pre-process them, and call
        the subscribed callback.

        :param channel: channel that reports value ref buffer update
        :type channel: ExpChannel
        :param value_ref_buffer: json encoded value ref buffer update,
            it contains at least value refs and indexes
        :type value_ref_buffer: :obj:`str`
        """
        if value_ref_buffer is None:
            return
        _, value_ref_buffer = self._value_ref_buffer_codec.decode(
            value_ref_buffer)
        self._value_ref_buffer_cb(channel, value_ref_buffer)

    def subscribeValueRefBuffer(self, cb=None):
        """Subscribe to channels' value ref buffer update events. If no
        callback is passed, the default channel's callback is subscribed which
        will store the data in the channel's value_buffer attribute.

        :param cb: callback to be subscribed, None means subscribe the default
            channel's callback
        :type cb: callable
        """
        self._value_ref_buffer_channels = []
        for channel_info in self.getChannels():
            full_name = channel_info["full_name"]
            value_ref_enabled = channel_info.get("value_ref_enabled", False)
            # Use DeviceProxy instead of taurus to avoid crashes in Py3
            # See: tango-controls/pytango#292
            if not _is_referable(full_name):
                continue
            if not value_ref_enabled:
                continue
            channel = Device(full_name)
            value_ref_buffer_obj = channel.getValueRefBufferObj()
            if cb is not None:
                self._value_ref_buffer_cb = cb
                value_ref_buffer_obj.subscribeEvent(
                    self.valueRefBufferChanged, channel, False)
            else:
                value_ref_buffer_obj.subscribeEvent(
                    channel.valueRefBufferChanged, with_first_event=False)
            self._value_ref_buffer_channels.append(channel)

    def unsubscribeValueRefBuffer(self, cb=None):
        """Unsubscribe from channels' value ref buffer events. If no
        callback is passed, unsubscribe the channel's default callback.

        :param cb: callback to be unsubscribed, None means unsubscribe the
            default channel's callback
        :type cb: callable
        """
        for channel_info in self.getChannels():
            full_name = channel_info["full_name"]
            value_ref_enabled = channel_info.get("value_ref_enabled", False)
            # Use DeviceProxy instead of taurus to avoid crashes in Py3
            # See: tango-controls/pytango#292
            if not _is_referable(full_name):
                continue
            if not value_ref_enabled:
                continue
            channel = Device(full_name)
            value_ref_buffer_obj = channel.getValueRefBufferObj()
            if cb is not None:
                value_ref_buffer_obj.unsubscribeEvent(
                    self.valueRefBufferChanged, channel)
                self._value_ref_buffer_cb = None
            else:
                value_ref_buffer_obj.unsubscribeEvent(
                    channel.valueRefBufferChanged)
        self._value_ref_buffer_channels = None

    def _start(self, *args, **kwargs):
        try:
            self.Start()
        except DevFailed as e:
            # TODO: Workaround for CORBA timeout on measurement group start
            # remove it whenever sardana-org/sardana#93 gets implemented
            if e.args[-1].reason == "API_DeviceTimedOut":
                self.error("start timed out, trying to stop")
                self.stop()
                self.debug("stopped")
            raise e

    def prepare(self):
        self.command_inout("Prepare")

    def count_raw(self, start_time=None):
        """Raw count and report count values.

        Simply start and wait until finish, no configuration nor preparation.

        .. note::
            The count_raw method API is partially experimental (value
            references may be changed to values whenever possible in the
            future). Backwards incompatible changes may occur if deemed
            necessary by the core developers.

        :param start_time: start time of the whole count operation, if not
          passed a current timestamp will be used
        :type start_time: :obj:`float`
        :return: channel names and values (or value references - experimental)
        :rtype: :obj:`dict` where keys are channel full names and values are
          channel values (or value references - experimental)
        """
        if start_time is None:
            start_time = time.time()
        PoolElement.go(self)
        state = self.getStateEG().readValue()
        if state == Fault:
            msg = "Measurement group ended acquisition with Fault state"
            raise Exception(msg)
        values = self.getValues()
        ret = state, values
        self._total_go_time = time.time() - start_time
        return ret

    def go(self, *args, **kwargs):
        """Count and report count values.

        Configuration and prepare for measurement, then start and wait until
        finish.

        .. note::
            The count (go) method API is partially experimental (value
            references may be changed to values whenever possible in the
            future). Backwards incompatible changes may occur if deemed
            necessary by the core developers.

        :return: channel names and values (or value references - experimental)
        :rtype: :obj:`dict` where keys are channel full names and values are
          channel values (or value references - experimental)
        """
        start_time = time.time()
        cfg = self.getConfiguration()
        cfg.prepare()
        integration_time = args[0]
        if integration_time is None or integration_time == 0:
            return self.getStateEG().readValue(), self.getValues()
        self.putIntegrationTime(integration_time)
        self.setMoveable(None)
        self.setNbStarts(1)
        self.prepare()
        return self.count_raw(start_time)

    def count_continuous(self, synch_description, value_buffer_cb=None,
                         value_ref_buffer_cb=None):
        """Execute measurement process according to the given synchronization
        description.

        :param synch_description: synchronization description
        :type synch_description: list of groups with equidistant
          synchronizations
        :param value_buffer_cb: callback on value buffer updates
        :type value_buffer_cb: callable
        :param value_ref_buffer_cb: callback on value reference
          buffer updates
        :type value_ref_buffer_cb: callable
        :return: state and eventually value buffers if no callback was passed
        :rtype: tuple<list<DevState>,<list>>

        .. todo:: Think of unifying measure with count.

        .. note:: The measure method has been included in MeasurementGroup
            class on a provisional basis. Backwards incompatible changes
            (up to and including removal of the method) may occur if
            deemed necessary by the core developers.
        """
        start_time = time.time()
        cfg = self.getConfiguration()
        cfg.prepare()
        self.setSynchDescription(synch_description)
        self.prepare()
        self.subscribeValueBuffer(value_buffer_cb)
        self.subscribeValueRefBuffer(value_ref_buffer_cb)
        try:
            self.count_raw(start_time)
        finally:
            self.unsubscribeValueBuffer(value_buffer_cb)
            self.unsubscribeValueRefBuffer(value_ref_buffer_cb)
        state = self.getStateEG().readValue()
        if state == Fault:
            msg = "Measurement group ended acquisition with Fault state"
            raise Exception(msg)
        if value_buffer_cb is None:
            value_buffers = self.getValueBuffers()
        else:
            value_buffers = None
        ret = state, value_buffers
        self._total_go_time = time.time() - start_time
        return ret

    startCount = PoolElement.start
    waitCount = PoolElement.waitFinish
    count = go
    stopCount = PoolElement.abort
    stop = PoolElement.stop


class IORegister(PoolElement):
    """ Class encapsulating IORegister functionality."""

    def __init__(self, name, **kw):
        """IORegister initialization."""
        self.call__init__(PoolElement, name, **kw)

    def getValueObj(self):
        return self._getAttrEG('value')

    def readValue(self, force=False):
        return self._getAttrValue('value', force=force)

    def startWriteValue(self, new_value, timeout=None):
        try:
            self.getValueObj().write(new_value)
            self.final_val = new_value
        except DevFailed as err_traceback:
            for err in err_traceback.args:
                if err.reason == 'API_AttrNotAllowed':
                    raise RuntimeError('%s is already chaging' % self)
                else:
                    raise

    def waitWriteValue(self, timeout=None):
        pass

    def writeValue(self, new_value, timeout=None):
        self.startWriteValue(new_value, timeout=timeout)
        self.waitWriteValue(timeout=timeout)
        return self.getStateEG().readValue(), self.readValue()

    writeIORegister = writeIOR = writeValue
    readIORegister = readIOR = getValue = readValue


class Instrument(BaseElement):
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def getFullName(self):
        return self.full_name

    def getParentInstrument(self):
        return self.getPoolObj().getObj(self.parent_instrument)

    def getParentInstrumentName(self):
        return self.parent_instrument

    def getChildrenInstruments(self):
        raise NotImplementedError
        return self._children

    def getElements(self):
        raise NotImplementedError
        return self._elements

    def getType(self):
        return self.klass


class Pool(TangoDevice, MoveableSource):
    """ Class encapsulating device Pool functionality."""

    def __init__(self, name, **kw):
        self.call__init__(TangoDevice, name, **kw)
        self.call__init__(MoveableSource)

        self._elements = BaseSardanaElementContainer()
        self.__elements_attr = self.getAttribute("Elements")
        self.__elements_attr.addListener(self.on_elements_changed)

    def cleanUp(self):
        TangoDevice.cleanUp(self)
        f = self.factory()
        f.removeExistingAttribute(self.__elements_attr)

    def getObject(self, element_info):
        elem_type = element_info.getType()
        data = element_info._data
        if elem_type in ('ControllerClass', 'ControllerLibrary', 'Instrument'):
            klass = globals()[elem_type]
            kwargs = dict(data)
            kwargs['_pool_data'] = data
            kwargs['_pool_obj'] = self
            return klass(**kwargs)
        obj = Factory().getDevice(element_info.full_name, _pool_obj=self,
                                  _pool_data=data)
        return obj

    def on_elements_changed(self, evt_src, evt_type, evt_value):
        if evt_type == TaurusEventType.Error:
            msg = evt_value
            if isinstance(msg, DevFailed):
                d = msg.args[0]
                # skip configuration errors
                if d.reason == "API_BadConfigurationProperty":
                    return
                if d.reason in ("API_DeviceNotExported",
                                "API_CantConnectToDevice"):
                    msg = "Pool was shutdown or is inaccessible"
                else:
                    msg = "{0}: {1}".format(d.reason, d.desc)
            self.warning("Received elements error event %s", msg)
            self.debug(evt_value)
            return
        elif evt_type not in CHANGE_EVT_TYPES:
            return
        try:
            elems = CodecFactory().decode(evt_value.rvalue)
        except:
            self.error("Could not decode element info")
            self.info("value: '%s'", evt_value.rvalue)
            self.debug("Details:", exc_info=1)
            return
        elements = self.getElementsInfo()
        for element_data in elems.get('new', ()):
            element_data['manager'] = self
            element = BaseSardanaElement(**element_data)
            elements.addElement(element)
        for element_data in elems.get('del', ()):
            element = self.getElementInfo(element_data['full_name'])
            try:
                elements.removeElement(element)
            except:
                self.warning("Failed to remove %s", element_data)
        for element_data in elems.get('change', ()):
            # TODO: element is assigned but not used!! (check)
            element = self._removeElement(element_data)
            element = self._addElement(element_data)
        return elems

    def _addElement(self, element_data):
        element_data['manager'] = self
        element = BaseSardanaElement(**element_data)
        self.getElementsInfo().addElement(element)
        return element

    def _removeElement(self, element_data):
        name = element_data['full_name']
        element = self.getElementInfo(name)
        self.getElementsInfo().removeElement(element)
        return element

    def getElementsInfo(self):
        return self._elements

    def getElements(self):
        return self.getElementsInfo().getElements()

    def getElementInfo(self, name):
        return self.getElementsInfo().getElement(name)

    def getElementNamesOfType(self, elem_type):
        return self.getElementsInfo().getElementNamesOfType(elem_type)

    def getElementsOfType(self, elem_type):
        return self.getElementsInfo().getElementsOfType(elem_type)

    def getElementsWithInterface(self, interface):
        return self.getElementsInfo().getElementsWithInterface(interface)

    def getElementWithInterface(self, elem_name, interface):
        return self.getElementsInfo().getElementWithInterface(elem_name,
                                                              interface)

    def getObj(self, name, elem_type=None):
        if elem_type is None:
            return self.getElementInfo(name)
        elif isinstance(elem_type, str):
            elem_types = elem_type,
        else:
            elem_types = elem_type
        name = name.lower()
        for e_type in elem_types:
            elems = self.getElementsOfType(e_type)
            for elem in list(elems.values()):
                if elem.name.lower() == name:
                    return elem
            elem = elems.get(name)
            if elem is not None:
                return elem

    def __repr__(self):
        return self.getNormalName()

    def __str__(self):
        return repr(self)

    # -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # MoveableSource interface
    #

    def getMoveable(self, names):
        """getMoveable(seq<string> names) -> Moveable

        Returns a moveable object that handles all the moveable items given in
        names."""
        # if simple motor just return it (if the pool has it)
        if isinstance(names, str):
            names = names,

        if len(names) == 1:
            name = names[0]
            return self.getObj(name, elem_type=MOVEABLE_TYPES)

        # find a motor group that contains elements
        moveable = self.__findMotorGroupWithElems(names)

        # if none exists create one
        if moveable is None:
            mgs = self.getElementsOfType('MotorGroup')
            i = 1
            pid = os.getpid()
            while True:
                name = "_mg_ms_{0}_{1}".format(pid, i)
                exists = False
                for mg in list(mgs.values()):
                    if mg.name == name:
                        exists = True
                        break
                if not exists:
                    break
                i += 1
            moveable = self.createMotorGroup(name, names)
        return moveable

    def __findMotorGroupWithElems(self, names):
        names_lower = list(map(str.lower, names))
        len_names = len(names)
        mgs = self.getElementsOfType('MotorGroup')
        for mg in list(mgs.values()):
            mg_elems = mg.elements
            if len(mg_elems) != len_names:
                continue
            for mg_elem, name in zip(mg_elems, names_lower):
                if mg_elem.lower() != name:
                    break
            else:
                return mg

    #
    # End of MoveableSource interface
    # -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    def _wait_for_element_in_container(self, container, elem_name, timeout=0.5,
                                       contains=True):
        start = time.time()
        cond = True
        nap = 0.01
        if timeout:
            nap = timeout / 10
        while cond:
            elem = container.getElement(elem_name)
            if contains:
                if elem is not None:
                    return elem
            else:
                if elem is None:
                    return True
            if timeout:
                dt = time.time() - start
                if dt > timeout:
                    self.info("Timed out waiting for '%s' in container",
                              elem_name)
                    return
            time.sleep(nap)

    def createMotorGroup(self, mg_name, elements):
        params = [mg_name, ] + list(map(str, elements))
        self.debug('trying to create motor group for elements: %s', params)
        self.command_inout('CreateMotorGroup', params)
        elements_info = self.getElementsInfo()
        return self._wait_for_element_in_container(elements_info, mg_name)

    def createMeasurementGroup(self, mg_name, elements):
        params = [mg_name, ] + list(map(str, elements))
        self.debug('trying to create measurement group: %s', params)
        self.command_inout('CreateMeasurementGroup', params)
        elements_info = self.getElementsInfo()
        return self._wait_for_element_in_container(elements_info, mg_name)

    def deleteMeasurementGroup(self, name):
        return self.deleteElement(name)

    def createElement(self, name, ctrl, axis=None):
        ctrl_type = ctrl.types[0]
        if axis is None:
            last_axis = ctrl.getLastUsedAxis()
            if last_axis is None:
                axis = str(1)
            else:
                axis = str(last_axis + 1)
        else:
            axis = str(axis)
        cmd = "CreateElement"
        pars = ctrl_type, ctrl.name, axis, name
        self.command_inout(cmd, pars)
        elements_info = self.getElementsInfo()
        return self._wait_for_element_in_container(elements_info, name)

    def renameElement(self, old_name, new_name):
        self.debug('trying to rename element: %s to: %s', old_name, new_name)
        self.command_inout('RenameElement', [old_name, new_name])
        elements_info = self.getElementsInfo()
        return self._wait_for_element_in_container(elements_info, new_name,
                                                   contains=True)

    def deleteElement(self, name):
        self.debug('trying to delete element: %s', name)
        self.command_inout('DeleteElement', name)
        elements_info = self.getElementsInfo()
        return self._wait_for_element_in_container(elements_info, name,
                                                   contains=False)

    def createController(self, class_name, name, *props):
        ctrl_class = self.getObj(class_name, elem_type='ControllerClass')
        if ctrl_class is None:
            raise Exception("Controller class %s not found" % class_name)
        cmd = "CreateController"
        pars = [ctrl_class.types[0], ctrl_class.file_name, class_name, name]
        pars.extend(list(map(str, props)))
        self.command_inout(cmd, pars)
        elements_info = self.getElementsInfo()
        return self._wait_for_element_in_container(elements_info, name)

    def deleteController(self, name):
        return self.deleteElement(name)

    def createInstrument(self, full_name, class_name):
        self.command_inout("CreateInstrument", [full_name, class_name])
        elements_info = self.getElementsInfo()
        return self._wait_for_element_in_container(elements_info, full_name)


def registerExtensions():
    factory = Factory()
    factory.registerDeviceClass("Pool", Pool)

    hw_type_names = [
        'Controller',
        'ComChannel', 'Motor', 'PseudoMotor', 'TriggerGate',
        'CTExpChannel', 'ZeroDExpChannel', 'OneDExpChannel', 'TwoDExpChannel',
        'PseudoCounter', 'IORegister', 'MotorGroup', 'MeasurementGroup']

    hw_type_map = [(name, globals()[name]) for name in hw_type_names]

    for klass_name, klass in hw_type_map:
        factory.registerDeviceClass(klass_name, klass)


def unregisterExtensions():
    factory = Factory()
    factory.unregisterDeviceClass("Pool")

    hw_type_names = [
        'Controller',
        'ComChannel', 'Motor', 'PseudoMotor', 'TriggerGate',
        'CTExpChannel', 'ZeroDExpChannel', 'OneDExpChannel', 'TwoDExpChannel',
        'PseudoCounter', 'IORegister', 'MotorGroup', 'MeasurementGroup']

    for klass_name in hw_type_names:
        factory.unregisterDeviceClass(klass_name)
