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

__all__ = ["CTExpChannel", "CTExpChannelClass"]

__docformat__ = 'restructuredtext'

import sys
import time

from PyTango import DevFailed, DevVoid, DevDouble, DevState, AttrQuality, \
    DevString, Except, READ, SCALAR

from taurus.core.util.log import DebugIt

from sardana import State, SardanaServer
from sardana.sardanaattribute import SardanaAttribute
from sardana.tango.core.util import to_tango_type_format, exception_str

from sardana.tango.pool.PoolDevice import PoolExpChannelDevice, \
    PoolExpChannelDeviceClass


class CTExpChannel(PoolExpChannelDevice):

    def __init__(self, dclass, name):
        PoolExpChannelDevice.__init__(self, dclass, name)
        self._first_read_cache = False

    def init(self, name):
        PoolExpChannelDevice.init(self, name)

    def get_ct(self):
        return self.element

    def set_ct(self, ct):
        self.element = ct

    ct = property(get_ct, set_ct)

    @DebugIt()
    def delete_device(self):
        PoolExpChannelDevice.delete_device(self)
        ct = self.ct
        if ct is not None:
            ct.remove_listener(self.on_ct_changed)

    @DebugIt()
    def init_device(self):
        PoolExpChannelDevice.init_device(self)

        ct = self.ct
        if ct is None:
            full_name = self.get_full_name()
            name = self.alias or full_name
            self.ct = ct = \
                self.pool.create_element(type="CTExpChannel",
                                         name=name, full_name=full_name, id=self.Id, axis=self.Axis,
                                         ctrl_id=self.Ctrl_id)
            if self.instrument is not None:
                ct.set_instrument(self.instrument)
        ct.add_listener(self.on_ct_changed)

        # force a state read to initialize the state attribute
        #state = ct.state
        self.set_state(DevState.ON)

    def on_ct_changed(self, event_source, event_type, event_value):
        try:
            self._on_ct_changed(event_source, event_type, event_value)
        except not DevFailed:
            msg = 'Error occurred "on_ct_changed(%s.%s): %s"'
            exc_info = sys.exc_info()
            self.error(msg, self.motor.name, event_type.name,
                       exception_str(*exc_info[:2]))
            self.debug("Details", exc_info=exc_info)

    def _on_ct_changed(self, event_source, event_type, event_value):
        # during server startup and shutdown avoid processing element
        # creation events
        if SardanaServer.server_state != State.Running:
            return

        timestamp = time.time()
        name = event_type.name.lower()
        attr_name = name
        # TODO: remove this condition when Data attribute will be substituted
        # by ValueBuffer
        if name == "valuebuffer":
            attr_name = "data"

        try:
            attr = self.get_attribute_by_name(attr_name)
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
        else:
            if isinstance(event_value, SardanaAttribute):
                if event_value.error:
                    error = Except.to_dev_failed(*event_value.exc_info)
                else:
                    value = event_value.value
                timestamp = event_value.timestamp
            else:
                value = event_value
            if name == "value":
                w_value = event_source.get_value_attribute().w_value
                state = self.ct.get_state()
                if state == State.Moving:
                    quality = AttrQuality.ATTR_CHANGING

        self.set_attribute(attr, value=value, w_value=w_value,
                           timestamp=timestamp, quality=quality,
                           priority=priority, error=error, synch=False)

    def always_executed_hook(self):
        #state = to_tango_state(self.ct.get_state(cache=False))
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
                _, data_info, attr_info = value
                ttype, _ = to_tango_type_format(attr_info.dtype)
                data_info[0][0] = ttype
        return std_attrs, dyn_attrs

    def initialize_dynamic_attributes(self):
        attrs = PoolExpChannelDevice.initialize_dynamic_attributes(self)

        detect_evts = "value",
        non_detect_evts = "data",

        for attr_name in detect_evts:
            if attr_name in attrs:
                self.set_change_event(attr_name, True, True)
        for attr_name in non_detect_evts:
            if attr_name in attrs:
                self.set_change_event(attr_name, True, False)

    def read_Value(self, attr):
        ct = self.ct
        # TODO: decide if we force the controller developers to store the
        # last acquired value in the controllers or we always will use
        # cache. This is due to the fact that the clients (MS) read the value
        # after the acquisition had finished.
        use_cache = ct.is_in_operation() and not self.Force_HW_Read
        # For the moment we just check if we recently receive ValueBuffer.
        # event. In this case, we use cache and clean the flag
        # so the cached value will be returned only at the first readout
        # after the acquisition. This is a workaround for the count executed
        # by the MacroServer e.g. step scans or ct which read the value after
        # the acquisition.
        if not use_cache and self._first_read_cache:
            use_cache = True
            self._first_read_cache = False
        value = ct.get_value(cache=use_cache, propagate=0)
        if value.error:
            Except.throw_python_exception(*value.exc_info)
        state = ct.get_state(cache=use_cache, propagate=0)
        quality = None
        if state == State.Moving:
            quality = AttrQuality.ATTR_CHANGING
        self.set_attribute(attr, value=value.value, quality=quality,
                           timestamp=value.timestamp, priority=0)

    def is_Value_allowed(self, req_type):
        if self.get_state() in [DevState.FAULT, DevState.UNKNOWN]:
            return False
        return True

    def Start(self):
        self.ct.start_acquisition()


class CTExpChannelClass(PoolExpChannelDeviceClass):

    #    Class Properties
    class_property_list = {}

    #    Device Properties
    device_property_list = {}
    device_property_list.update(PoolExpChannelDeviceClass.device_property_list)

    #    Command definitions
    cmd_list = {
        'Start':   [[DevVoid, ""], [DevVoid, ""]],
    }
    cmd_list.update(PoolExpChannelDeviceClass.cmd_list)

    #    Attribute definitions
    attr_list = {}
    attr_list.update(PoolExpChannelDeviceClass.attr_list)

    standard_attr_list = {
        'Value': [[DevDouble, SCALAR, READ],
                  {'abs_change': '1.0', }]
    }
    standard_attr_list.update(PoolExpChannelDeviceClass.standard_attr_list)

    def _get_class_properties(self):
        ret = PoolExpChannelDeviceClass._get_class_properties(self)
        ret['Description'] = "Counter/Timer device class"
        ret['InheritedFrom'].insert(0, 'PoolExpChannelDevice')
        return ret
