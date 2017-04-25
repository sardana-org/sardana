#!/usr/bin/env python
import PyTango

##############################################################################
##
# This file is part of Sardana
##
# http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
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

__all__ = ["TriggerGate", "TriggerGateClass"]

__docformat__ = 'restructuredtext'

import sys
import time

from PyTango import DevFailed, DevVoid, DevLong, DevState, AttrQuality, \
    DevString, Except, SCALAR, ErrSeverity, READ

from taurus.core.util.log import DebugIt

from sardana import State, SardanaServer
from sardana.sardanaattribute import SardanaAttribute
from sardana.tango.core.util import to_tango_type_format, exception_str

from sardana.tango.pool.PoolDevice import PoolElementDevice, \
    PoolElementDeviceClass


class TriggerGate(PoolElementDevice):

    def __init__(self, dclass, name):
        PoolElementDevice.__init__(self, dclass, name)

    def init(self, name):
        PoolElementDevice.init(self, name)

    def _is_allowed(self, req_type):
        return PoolElementDevice._is_allowed(self, req_type)

    def get_tg(self):
        return self.element

    def set_tg(self, tg):
        self.element = tg

    tg = property(get_tg, set_tg)

    @DebugIt()
    def delete_device(self):
        PoolElementDevice.delete_device(self)
        tg = self.tg
        if tg is not None:
            tg.remove_listener(self.on_tg_changed)

    @DebugIt()
    def init_device(self):
        PoolElementDevice.init_device(self)

        tg = self.tg
        if tg is None:
            full_name = self.get_full_name()
            name = self.alias or full_name
            self.tg = tg = \
                self.pool.create_element(type="TriggerGate",
                                         name=name, full_name=full_name, id=self.Id, axis=self.Axis,
                                         ctrl_id=self.Ctrl_id)

        tg.add_listener(self.on_tg_changed)
        self.set_state(DevState.ON)

    def on_tg_changed(self, event_source, event_type, event_value):
        try:
            self._on_tg_changed(event_source, event_type, event_value)
        except not DevFailed:
            msg = 'Error occurred "on_tg_changed(%s.%s): %s"'
            exc_info = sys.exc_info()
            self.error(msg, event_type.name,
                       exception_str(*exc_info[:2]))
            self.debug("Details", exc_info=exc_info)

    def _on_tg_changed(self, event_source, event_type, event_value):
        # during server startup and shutdown avoid processing element
        # creation events
        if SardanaServer.server_state != State.Running:
            return

        timestamp = time.time()
        name = event_type.name.lower()

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
        else:
            if isinstance(event_value, SardanaAttribute):
                if event_value.error:
                    error = Except.to_dev_failed(*event_value.exc_info)
                else:
                    value = event_value.value
                timestamp = event_value.timestamp
            else:
                value = event_value

        self.set_attribute(attr, value=value, w_value=w_value,
                           timestamp=timestamp, quality=quality,
                           priority=priority, error=error, synch=False)


class TriggerGateClass(PoolElementDeviceClass):

    def _get_class_properties(self):
        ret = PoolElementDeviceClass._get_class_properties(self)
        ret['Description'] = "Trigger/Gate device class"
        ret['InheritedFrom'].insert(0, 'PoolElementDevice')
        return ret
