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

__all__ = ["PseudoCounter", "PseudoCounterClass"]

__docformat__ = 'restructuredtext'

import sys
import time

from PyTango import Except, READ, SCALAR, DevDouble, \
    DevVarStringArray, DevVarDoubleArray, DevState, AttrQuality, DevFailed

from taurus.core.util.log import DebugIt

from sardana import State, SardanaServer
from sardana.sardanaattribute import SardanaAttribute
from sardana.tango.core.util import to_tango_type_format, exception_str, \
    throw_sardana_exception
from sardana.tango.pool.PoolDevice import PoolExpChannelDevice, \
    PoolExpChannelDeviceClass


class PseudoCounter(PoolExpChannelDevice):

    def __init__(self, dclass, name):
        PoolExpChannelDevice.__init__(self, dclass, name)
        self._first_read_cache = False

    def init(self, name):
        PoolExpChannelDevice.init(self, name)

    def _is_allowed(self, req_type):
        return PoolExpChannelDevice._is_allowed(self, req_type)

    def get_pseudo_counter(self):
        return self.element

    def set_pseudo_counter(self, pseudo_counter):
        self.element = pseudo_counter

    pseudo_counter = property(get_pseudo_counter, set_pseudo_counter)

    @DebugIt()
    def delete_device(self):
        PoolExpChannelDevice.delete_device(self)
        pseudo_counter = self.pseudo_counter
        if pseudo_counter is not None:
            pseudo_counter.remove_listener(self.on_pseudo_counter_changed)

    @DebugIt()
    def init_device(self):
        PoolExpChannelDevice.init_device(self)

        self.Elements = map(int, self.Elements)
        pseudo_counter = self.pseudo_counter
        if pseudo_counter is None:
            full_name = self.get_full_name()
            name = self.alias or full_name
            self.pseudo_counter = pseudo_counter = \
                self.pool.create_element(type="PseudoCounter", name=name,
                                         full_name=full_name, id=self.Id, axis=self.Axis,
                                         ctrl_id=self.Ctrl_id, user_elements=self.Elements)
            if self.instrument is not None:
                pseudo_counter.set_instrument(self.instrument)
        pseudo_counter.add_listener(self.on_pseudo_counter_changed)

        self.set_state(DevState.ON)

    def on_pseudo_counter_changed(self, event_source, event_type,
                                  event_value):
        try:
            self._on_pseudo_counter_changed(event_source, event_type,
                                            event_value)
        except:
            msg = 'Error occurred "on_pseudo_counter_changed(%s.%s): %s"'
            exc_info = sys.exc_info()
            self.error(msg, self.pseudo_counter.name, event_type.name,
                       exception_str(*exc_info[:2]))
            self.debug("Details", exc_info=exc_info)

    def _on_pseudo_counter_changed(self, event_source, event_type,
                                   event_value):
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
        elif name == "value":
            if isinstance(event_value, SardanaAttribute):
                # first obtain the value - during this process it may
                # enter into the error state, either when updating the elements
                # values or when calculating the pseudo value
                value = event_value.value
                if event_value.error:
                    error = Except.to_dev_failed(*event_value.exc_info)
                timestamp = event_value.timestamp
            else:
                value = event_value

            state = self.pseudo_counter.get_state(propagate=0)
            if state == State.Moving:
                quality = AttrQuality.ATTR_CHANGING
        else:
            if isinstance(event_value, SardanaAttribute):
                if event_value.error:
                    error = Except.to_dev_failed(*event_value.exc_info)
                else:
                    value = event_value.value
                timestamp = event_value.timestamp

        self.set_attribute(attr, value=value, w_value=w_value,
                           timestamp=timestamp, quality=quality,
                           priority=priority, error=error, synch=False)

    def always_executed_hook(self):
        #state = to_tango_state(self.pseudo_counter.get_state(cache=False))
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
        pseudo_counter = self.pseudo_counter
        use_cache = pseudo_counter.is_in_operation() and not self.Force_HW_Read
        if not use_cache and self._first_read_cache:
            use_cache = True
            self._first_read_cache = False
        value_attr = pseudo_counter.get_value(cache=use_cache, propagate=0)
        # first obtain the value - during this process it may
        # enter into the error state, either when updating the elements
        # values or when calculating the pseudo value
        value = value_attr.value
        if value_attr.error:
            Except.throw_python_exception(*value_attr.exc_info)
        quality = None
        state = pseudo_counter.get_state(cache=use_cache, propagate=0)
        if state == State.Moving:
            quality = AttrQuality.ATTR_CHANGING
        timestamp = value_attr.value
        self.set_attribute(attr, value=value, quality=quality,
                           priority=0, timestamp=timestamp)

    is_Value_allowed = _is_allowed

    def CalcPseudo(self, physical_values):
        """Returns the pseudo counter value for the given physical counters"""
        if not len(physical_values):
            physical_values = None
        result = self.pseudo_counter.calc(physical_values=physical_values)
        if result.error:
            throw_sardana_exception(result)
        return result.value

    def CalcAllPseudo(self, physical_values):
        """Returns the pseudo counter values for the given physical counters"""
        if not len(physical_values):
            physical_values = None
        result = self.pseudo_counter.calc(physical_values=physical_values)
        if result.error:
            throw_sardana_exception(result)
        return result.value


class PseudoCounterClass(PoolExpChannelDeviceClass):

    #    Class Properties
    class_property_list = {
    }

    #    Device Properties
    device_property_list = {
        "Elements":    [DevVarStringArray, "elements used by the pseudo", []],
    }
    device_property_list.update(PoolExpChannelDeviceClass.device_property_list)

    #    Command definitions
    cmd_list = {
        'CalcPseudo': [[DevVarDoubleArray, "physical values"], [DevDouble, "pseudo counter"]],
        'CalcAllPseudo': [[DevVarDoubleArray, "physical positions"], [DevVarDoubleArray, "pseudo counter values"]],
    }
    cmd_list.update(PoolExpChannelDeviceClass.cmd_list)

    #    Attribute definitions
    standard_attr_list = {
        'Value': [[DevDouble, SCALAR, READ]],
    }
    standard_attr_list.update(PoolExpChannelDeviceClass.standard_attr_list)

    def _get_class_properties(self):
        ret = PoolExpChannelDeviceClass._get_class_properties(self)
        ret['Description'] = "Pseudo counter device class"
        ret['InheritedFrom'].insert(0, 'PoolExpChannelDevice')
        return ret
