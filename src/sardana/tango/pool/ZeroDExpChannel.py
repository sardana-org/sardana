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

""" """

__all__ = ["ZeroDExpChannel", "ZeroDExpChannelClass"]

__docformat__ = 'restructuredtext'

import time

from PyTango import Except
from PyTango import DevVoid, DevDouble, DevString
from PyTango import DispLevel, DevState, AttrQuality
from PyTango import READ, READ_WRITE, SCALAR, SPECTRUM

from taurus.core.util.log import DebugIt

from sardana import State, DataFormat, SardanaServer
from sardana.sardanaattribute import SardanaAttribute
from sardana.pool.controller import ZeroDController, Type
from sardana.tango.core.util import to_tango_type_format

from sardana.tango.pool.PoolDevice import PoolExpChannelDevice, \
    PoolExpChannelDeviceClass


class ZeroDExpChannel(PoolExpChannelDevice):

    def __init__(self, dclass, name):
        PoolExpChannelDevice.__init__(self, dclass, name)

    def init(self, name):
        PoolExpChannelDevice.init(self, name)

    def get_zerod(self):
        return self.element

    def set_zerod(self, zerod):
        self.element = zerod

    zerod = property(get_zerod, set_zerod)

    @DebugIt()
    def delete_device(self):
        PoolExpChannelDevice.delete_device(self)
        zerod = self.zerod
        if zerod is not None:
            zerod.remove_listener(self.on_zerod_changed)

    @DebugIt()
    def init_device(self):
        PoolExpChannelDevice.init_device(self)
        zerod = self.zerod
        if zerod is None:
            full_name = self.get_full_name()
            name = self.alias or full_name
            self.zerod = zerod = \
                self.pool.create_element(type="ZeroDExpChannel", name=name,
                                         full_name=full_name, id=self.Id, axis=self.Axis,
                                         ctrl_id=self.Ctrl_id)
        zerod.add_listener(self.on_zerod_changed)

        # force a state read to initialize the state attribute
        #state = zerod.state
        self.set_state(DevState.ON)

    def on_zerod_changed(self, event_source, event_type, event_value):
        # during server startup and shutdown avoid processing element
        # creation events
        if SardanaServer.server_state != State.Running:
            return

        timestamp = time.time()
        quality = AttrQuality.ATTR_VALID
        priority = event_type.priority
        value = None
        error = None

        name = event_type.name.lower()
        attr_name = name
        attr = self.get_device_attr().get_attr_by_name(attr_name)

        if name == "state":
            value = self.calculate_tango_state(event_value)
        elif name == "status":
            value = self.calculate_tango_status(event_value)
        elif name == "valuebuffer":
            value = self._encode_value_chunk(event_value)
        elif name == "value":
            if isinstance(event_value, SardanaAttribute):
                if event_value.error:
                    error = Except.to_dev_failed(*event_value.exc_info)
                else:
                    value = event_value.value
                timestamp = event_value.timestamp
            else:
                value = event_value

            if name == "value":
                state = self.zerod.get_state()
                if state == State.Moving:
                    quality = AttrQuality.ATTR_CHANGING
        self.set_attribute(attr, value=value, timestamp=timestamp,
                           quality=quality, priority=priority, error=error,
                           synch=False)

    def always_executed_hook(self):
        #state = to_tango_state(self.zerod.get_state(cache=False))
        pass

    def read_attr_hardware(self, data):
        pass

    def get_dynamic_attributes(self):
        cache_built = hasattr(self, "_dynamic_attributes_cache")

        std_attrs, dyn_attrs = \
            PoolExpChannelDevice.get_dynamic_attributes(self)

        if not cache_built:
            # For value attribute, listen to what the controller says for data
            # type (between long and float)
            value = std_attrs.get('value')
            if value is not None:
                attr_name, data_info, attr_info = value
                ttype, _ = to_tango_type_format(attr_info.dtype)
                data_info[0][0] = ttype

                # Add manually a 'CurrentValue' with the same time as 'Value'
                attr_name = 'CurrentValue'
                attr_info = attr_info.copy()
                attr_info.description = attr_name
                std_attrs[attr_name] = [attr_name, data_info, attr_info]

        return std_attrs, dyn_attrs

    def initialize_dynamic_attributes(self):
        attrs = PoolExpChannelDevice.initialize_dynamic_attributes(self)

        detect_evts = "value",
        non_detect_evts = "valuebuffer",

        for attr_name in detect_evts:
            if attr_name in attrs:
                self.set_change_event(attr_name, True, True)
        for attr_name in non_detect_evts:
            if attr_name in attrs:
                self.set_change_event(attr_name, True, False)

    def read_Value(self, attr):
        zerod = self.zerod
        value = zerod.get_accumulated_value()
        quality = None
        if self.get_state() == State.Moving:
            quality = AttrQuality.ATTR_CHANGING
        self.set_attribute(attr, value=value.value,
                           quality=quality, priority=0)

    def read_CurrentValue(self, attr):
        zerod = self.zerod
        #use_cache = ct.is_action_running() and not self.Force_HW_Read
        use_cache = self.get_state() == State.Moving and not self.Force_HW_Read
        value = zerod.get_current_value(cache=use_cache, propagate=0)
        if value.error:
            Except.throw_python_exception(*value.exc_info)
        quality = None
        state = zerod.get_state(cache=use_cache, propagate=0)
        if state == State.Moving:
            quality = AttrQuality.ATTR_CHANGING
        self.set_attribute(attr, value=value.value, quality=quality,
                           priority=0, timestamp=value.timestamp)

    def Start(self):
        self.zerod.start_acquisition()

    def read_AccumulationBuffer(self, attr):
        attr.set_value(self.zerod.get_accumulation_buffer())

    def read_TimeBuffer(self, attr):
        attr.set_value(self.zerod.get_time_buffer())

    def read_AccumulationType(self, attr):
        attr.set_value(self.zerod.get_accumulation_type())

    def write_AccumulationType(self, attr):
        self.zerod.set_accumulation_type(attr.get_write_value())

    def _is_allowed(self, req_type):
        return PoolExpChannelDevice._is_allowed(self, req_type)

    is_Value_allowed = _is_allowed
    is_CurrentValue_allowed = _is_allowed
    is_AccumulationType_allowed = _is_allowed
    is_AccumulationBuffer_allowed = _is_allowed
    is_TimeBuffer_allowed = _is_allowed


_DFT_VALUE_INFO = ZeroDController.standard_axis_attributes['Value']
_DFT_VALUE_TYPE, _DFT_VALUE_FORMAT = to_tango_type_format(
    _DFT_VALUE_INFO[Type], DataFormat.Scalar)


class ZeroDExpChannelClass(PoolExpChannelDeviceClass):

    #    Class Properties
    class_property_list = {
    }

    #    Device Properties
    device_property_list = {
    }
    device_property_list.update(PoolExpChannelDeviceClass.device_property_list)

    #    Command definitions
    cmd_list = {
        'Start':   [[DevVoid, ""], [DevVoid, ""]],
    }
    cmd_list.update(PoolExpChannelDeviceClass.cmd_list)

    #    Attribute definitions
    attr_list = {
        'AccumulationBuffer': [[DevDouble, SPECTRUM, READ, 16 * 1024]],
        'TimeBuffer': [[DevDouble, SPECTRUM, READ, 16 * 1024]],
        'AccumulationType': [[DevString, SCALAR, READ_WRITE],
                             {'Memorized': "true",
                              'label': "Accumulation Type",
                              'Display level': DispLevel.EXPERT}],
    }
    attr_list.update(PoolExpChannelDeviceClass.attr_list)

    standard_attr_list = {
        'Value': [[_DFT_VALUE_TYPE, SCALAR, READ, ],
                  {'abs_change': '1.0', }],
    }
    standard_attr_list.update(PoolExpChannelDeviceClass.standard_attr_list)

    def _get_class_properties(self):
        ret = PoolExpChannelDeviceClass._get_class_properties(self)
        ret['Description'] = "0D experimental channel device class"
        ret['InheritedFrom'].insert(0, 'PoolExpChannelDevice')
        return ret
