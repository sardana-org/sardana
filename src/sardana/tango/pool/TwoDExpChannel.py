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

__all__ = ["TwoDExpChannel", "TwoDExpChannelClass"]

__docformat__ = 'restructuredtext'

import sys
import time

from PyTango import DevFailed, DevVoid, DevString, DevState, AttrQuality, \
    Except, READ, SCALAR, READ_WRITE, DevEncoded

from taurus.core.util.log import DebugIt

from sardana import State, DataFormat, SardanaServer
from sardana.sardanaattribute import SardanaAttribute
from sardana.pool.controller import TwoDController, MaxDimSize, Type
from sardana.tango.core.util import to_tango_type_format, exception_str,\
    memorize_write_attribute
from sardana.tango.pool.PoolDevice import PoolTimerableDevice, \
    PoolTimerableDeviceClass


class TwoDExpChannel(PoolTimerableDevice):

    def __init__(self, dclass, name):
        PoolTimerableDevice.__init__(self, dclass, name)
        self._first_read_cache = False
        self._first_read_ref_cache = False

    def init(self, name):
        PoolTimerableDevice.init(self, name)

    def get_twod(self):
        return self.element

    def set_twod(self, twod):
        self.element = twod

    twod = property(get_twod, set_twod)

    @DebugIt()
    def delete_device(self):
        PoolTimerableDevice.delete_device(self)
        twod = self.twod
        if twod is not None:
            twod.remove_listener(self.on_twod_changed)

    @DebugIt()
    def init_device(self):
        PoolTimerableDevice.init_device(self)
        twod = self.twod
        if twod is None:
            full_name = self.get_full_name()
            name = self.alias or full_name
            self.twod = twod = \
                self.pool.create_element(type="TwoDExpChannel",
                                         name=name, full_name=full_name, id=self.Id, axis=self.Axis,
                                         ctrl_id=self.Ctrl_id)
            if self.instrument is not None:
                twod.set_instrument(self.instrument)
        twod.add_listener(self.on_twod_changed)

        # force a state read to initialize the state attribute
        #state = ct.state
        self.set_state(DevState.ON)

    def on_twod_changed(self, event_source, event_type, event_value):
        try:
            self._on_twod_changed(event_source, event_type, event_value)
        except not DevFailed:
            msg = 'Error occurred "on_twod_changed(%s.%s): %s"'
            exc_info = sys.exc_info()
            self.error(msg, self.motor.name, event_type.name,
                       exception_str(*exc_info[:2]))
            self.debug("Details", exc_info=exc_info)

    def _on_twod_changed(self, event_source, event_type, event_value):
        # during server startup and shutdown avoid processing element
        # creation events
        if SardanaServer.server_state != State.Running:
            return

        timestamp = time.time()
        name = event_type.name.lower()
        name = name.replace('_', '')  # for integration_time events

        try:
            attr = self.get_attribute_by_name(name)
        except DevFailed:
            return

        quality = AttrQuality.ATTR_VALID
        priority = event_type.priority
        value, w_value, error = None, None, None

        if name == "state":
            value = self.calculate_tango_state(event_value)
        elif name == "status":
            value = self.calculate_tango_status(event_value)
        elif name == "valuebuffer":
            value = self._encode_value_chunk(event_value)
            self._first_read_cache = True
        elif name == "valuerefbuffer":
            value = self._encode_value_ref_chunk(event_value)
            self._first_read_ref_cache = True
        else:
            if isinstance(event_value, SardanaAttribute):
                if event_value.error:
                    error = Except.to_dev_failed(*event_value.exc_info)
                else:
                    value = event_value.value
                timestamp = event_value.timestamp
            else:
                value = event_value

            if (name in ("timer", "valuereftemplate", "valuerefenabled")
                    and value is None):
                value = "None"
            elif name == "datasource" and value is None:
                full_name = self.get_full_name()
                # for Taurus 3/4 compatibility
                if not full_name.startswith("tango://"):
                    full_name = "tango://{0}".format(full_name)
                value = "{0}/value".format(full_name)
            elif name == "value":
                state = self.twod.get_state()
                if state == State.Moving:
                    quality = AttrQuality.ATTR_CHANGING
        self.set_attribute(attr, value=value, w_value=w_value,
                           timestamp=timestamp, quality=quality,
                           priority=priority, error=error, synch=False)

    def always_executed_hook(self):
        #state = to_tango_state(self.twod.get_state(cache=False))
        pass

    def read_attr_hardware(self, data):
        pass

    def get_dynamic_attributes(self):
        cache_built = hasattr(self, "_dynamic_attributes_cache")

        std_attrs, dyn_attrs = \
            PoolTimerableDevice.get_dynamic_attributes(self)

        if not cache_built:
            # For value attribute, listen to what the controller says for data
            # type (between long and float) and length
            value = std_attrs.get('value')
            if value is not None:
                _, data_info, attr_info = value
                ttype, _ = to_tango_type_format(attr_info.dtype)
                data_info[0][0] = ttype
                shape = attr_info.maxdimsize
                data_info[0][3] = shape[0]
                data_info[0][4] = shape[1]
        return std_attrs, dyn_attrs

    def initialize_dynamic_attributes(self):
        attrs = PoolTimerableDevice.initialize_dynamic_attributes(self)

        # referable channels
        # TODO: not 100% sure if valuereftemplate and valuerefenabled should
        # not belong to detect_evts
        non_detect_evts = ("valuebuffer", "valueref", "valuerefbuffer",
                           "valuereftemplate", "valuerefenabled")
        for attr_name in non_detect_evts:
            if attr_name in attrs:
                self.set_change_event(attr_name, True, False)

    def read_Value(self, attr):
        twod = self.twod
        # TODO: decide if we force the controller developers to store the
        # last acquired value in the controllers or we always will use
        # cache. This is due to the fact that the clients (MS) read the value
        # after the acquisition had finished.
        use_cache = twod.is_in_operation() and not self.Force_HW_Read
        # For the moment we just check if we recently receive ValueBuffer.
        # event. In this case, we use cache and clean the flag
        # so the cached value will be returned only at the first readout
        # after the acquisition. This is a workaround for the count executed
        # by the MacroServer e.g. step scans or ct which read the value after
        # the acquisition.
        if not use_cache and self._first_read_cache:
            use_cache = True
            self._first_read_cache = False
        value = twod.get_value(cache=use_cache, propagate=0)
        if value.error:
            Except.throw_python_exception(*value.exc_info)
        state = twod.get_state(cache=use_cache, propagate=0)
        quality = None
        if state == State.Moving:
            quality = AttrQuality.ATTR_CHANGING
        self.set_attribute(attr, value=value.value, quality=quality,
                           timestamp=value.timestamp, priority=0)

    def is_Value_allowed(self, req_type):
        if self.get_state() in [DevState.FAULT, DevState.UNKNOWN]:
            return False
        return True

    def read_ValueRef(self, attr):
        twod = self.twod
        value_ref = twod.get_value_ref()
        if value_ref.error:
            Except.throw_python_exception(*value_ref.exc_info)
        use_cache = twod.is_in_operation() and not self.Force_HW_Read
        state = twod.get_state(cache=use_cache, propagate=0)
        quality = None
        if state == State.Moving:
            quality = AttrQuality.ATTR_CHANGING
        self.set_attribute(attr, value=value_ref.value, quality=quality,
                           timestamp=value_ref.timestamp, priority=0)

    def read_ValueRefPattern(self, attr):
        value_ref_pattern = self.twod.get_value_ref_pattern()
        if value_ref_pattern is None:
            value_ref_pattern = "None"
        attr.set_value(value_ref_pattern)

    @memorize_write_attribute
    def write_ValueRefPattern(self, attr):
        value_ref_pattern = attr.get_write_value()
        if value_ref_pattern == "None":
            value_ref_pattern = None
        self.twod.value_ref_pattern = value_ref_pattern

    def read_ValueRefEnabled(self, attr):
        value_ref_enabled = self.twod.is_value_ref_enabled()
        if value_ref_enabled is None:
            raise Exception("value reference enabled flag is unknown")
        attr.set_value(value_ref_enabled)

    @memorize_write_attribute
    def write_ValueRefEnabled(self, attr):
        value_ref_enabled = attr.get_write_value()
        if value_ref_enabled == "None":
            value_ref_enabled = None
        self.twod.value_ref_enabled = value_ref_enabled

    def read_DataSource(self, attr):
        data_source = self.twod.get_data_source()
        if data_source is None:
            full_name = self.get_full_name()
            # for Taurus 3/4 compatibility
            if not full_name.startswith("tango://"):
                full_name = "tango://{0}".format(full_name)
            data_source = "{0}/value".format(full_name)
        attr.set_value(data_source)

    def Start(self):
        self.twod.start_acquisition()


_DFT_VALUE_INFO = TwoDController.standard_axis_attributes['Value']
_DFT_VALUE_MAX_SHAPE = _DFT_VALUE_INFO[MaxDimSize]
_DFT_VALUE_TYPE, _DFT_VALUE_FORMAT = to_tango_type_format(
    _DFT_VALUE_INFO[Type], DataFormat.TwoD)


class TwoDExpChannelClass(PoolTimerableDeviceClass):

    #    Class Properties
    class_property_list = {
    }

    #    Device Properties
    device_property_list = {
    }

    device_property_list.update(PoolTimerableDeviceClass.device_property_list)

    #    Command definitions
    cmd_list = {
        'Start':   [[DevVoid, ""], [DevVoid, ""]],
    }
    cmd_list.update(PoolTimerableDeviceClass.cmd_list)


    #    Attribute definitions
    attr_list = {
        'DataSource': [[DevString, SCALAR, READ]],
    }
    attr_list.update(PoolTimerableDeviceClass.attr_list)

    standard_attr_list = {
        'Value': [[_DFT_VALUE_TYPE, _DFT_VALUE_FORMAT, READ,
                   _DFT_VALUE_MAX_SHAPE[0], _DFT_VALUE_MAX_SHAPE[1]],
                  {'abs_change': '1.0', }],
        # TODO: here we override type by DevEncoded
        'ValueRefBuffer': [[DevEncoded, SCALAR, READ]]
    }
    standard_attr_list.update(PoolTimerableDeviceClass.standard_attr_list)

    def _get_class_properties(self):
        ret = PoolTimerableDeviceClass._get_class_properties(self)
        ret['Description'] = "2D device class"
        ret['InheritedFrom'].insert(0, 'PoolTimerableDevice')
        return ret
