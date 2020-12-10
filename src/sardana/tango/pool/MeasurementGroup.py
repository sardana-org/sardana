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

"""The sardana tango measurement group module"""

__all__ = ["MeasurementGroup", "MeasurementGroupClass"]

__docformat__ = 'restructuredtext'

import sys
import time

from PyTango import Except, DevVoid, DevLong, DevDouble, DevString, \
    DispLevel, DevState, AttrQuality, READ, READ_WRITE, SCALAR, Util

from taurus.core.util.codecs import CodecFactory
from taurus.core.util.log import DebugIt

from sardana import State, SardanaServer
from sardana.sardanaattribute import SardanaAttribute
from sardana.pool import AcqMode
from sardana.pool.pooldefs import SynchDomain, SynchParam
from sardana.tango.core.util import exception_str
from sardana.tango.pool.PoolDevice import PoolGroupDevice, PoolGroupDeviceClass


class MeasurementGroup(PoolGroupDevice):

    def __init__(self, dclass, name):
        PoolGroupDevice.__init__(self, dclass, name)

    def init(self, name):
        PoolGroupDevice.init(self, name)

    def get_measurement_group(self):
        return self.element

    def set_measurement_group(self, measurement_group):
        self.element = measurement_group

    measurement_group = property(get_measurement_group, set_measurement_group)

    @DebugIt()
    def delete_device(self):
        PoolGroupDevice.delete_device(self)
        mg = self.measurement_group
        if mg is not None:
            mg.remove_listener(self.on_measurement_group_changed)

    @DebugIt()
    def init_device(self):
        PoolGroupDevice.init_device(self)
        # state and status are already set by the super class
        detect_evts = "moveable", "synchdescription", \
                      "softwaresynchronizerinitialdomain"
        # TODO: nbstarts could be moved to detect events with
        # abs_change criteria of 1, but be careful with
        # tango-controls/pytango#302
        non_detect_evts = "configuration", "integrationtime", "monitorcount", \
                          "acquisitionmode", "elementlist", "latencytime", \
                          "nbstarts"
        self.set_change_events(detect_evts, non_detect_evts)

        self.Elements = list(self.Elements)
        for i in range(len(self.Elements)):
            try:
                self.Elements[i] = int(self.Elements[i])
            except:
                pass
        mg = self.measurement_group
        if mg is None:
            full_name = self.get_full_name()
            name = self.alias or full_name
            self.measurement_group = mg = \
                self.pool.create_measurement_group(name=name,
                                                   full_name=full_name,
                                                   id=self.Id,
                                                   user_elements=self.Elements)
        mg.add_listener(self.on_measurement_group_changed)

        # force a state read to initialize the state attribute
        # state = self.measurement_group.state
        self.set_state(DevState.ON)

    def on_measurement_group_changed(self, event_source, event_type,
                                     event_value):
        try:
            self._on_measurement_group_changed(
                event_source, event_type, event_value)
        except:
            msg = 'Error occured "on_measurement_group_changed(%s.%s): %s"'
            exc_info = sys.exc_info()
            self.error(msg, self.measurement_group.name, event_type.name,
                       exception_str(*exc_info[:2]))
            self.debug("Details", exc_info=exc_info)

    def _on_measurement_group_changed(self, event_source, event_type,
                                      event_value):
        # during server startup and shutdown avoid processing element
        # creation events
        if SardanaServer.server_state != State.Running:
            return

        timestamp = time.time()
        name = event_type.name
        name = name.replace('_', '')
        multi_attr = self.get_device_attr()
        attr = multi_attr.get_attr_by_name(name)
        quality = AttrQuality.ATTR_VALID
        priority = event_type.priority
        error = None

        if name == "state":
            event_value = self.calculate_tango_state(event_value)
        elif name == "status":
            event_value = self.calculate_tango_status(event_value)
        elif name == "acquisitionmode":
            event_value = AcqMode.whatis(event_value)
        elif name == "configuration":
            cfg = self.measurement_group.get_user_configuration()
            codec = CodecFactory().getCodec('json')
            _, event_value = codec.encode(('', cfg))
        elif name == "synchdescription":
            codec = CodecFactory().getCodec('json')
            _, event_value = codec.encode(('', event_value))
        elif name == "moveable" and event_value is None:
            event_value = 'None'
        else:
            if isinstance(event_value, SardanaAttribute):
                if event_value.error:
                    error = Except.to_dev_failed(*event_value.exc_info)
                timestamp = event_value.timestamp
                event_value = event_value.value

        self.set_attribute(attr, value=event_value, timestamp=timestamp,
                           quality=quality, priority=priority, error=error,
                           synch=False)

    def _synch_description_str2enum(self, _synch_description_str):
        """Translates synchronization description data structure so it uses
        SynchParam and SynchDomain enums as keys instead of strings.

        .. todo:: At some point remove the backwards compatibility
          for memorized values created with Python 2. In Python 2 IntEnum was
          serialized to "<class>.<attr>" e.g. "SynchDomain.Time" and we were
          using a class method `fromStr` to interpret the enumeration objects.
        """
        synch_description = []
        for group_str in _synch_description_str:
            group = {}
            for param_str, conf_str in group_str.items():
                try:
                    param = SynchParam(int(param_str))
                except ValueError:
                    param = SynchParam.fromStr(param_str)
                if isinstance(conf_str, dict):
                    conf = {}
                    for domain_str, value in conf_str.items():
                        try:
                            domain = SynchDomain(int(domain_str))
                        except ValueError:
                            domain = SynchDomain.fromStr(domain_str)
                        conf[domain] = value
                else:
                    conf = conf_str
                group[param] = conf
            synch_description.append(group)
        return synch_description

    def always_executed_hook(self):
        pass
        # state = to_tango_state(self.motor_group.get_state(cache=False))

    def read_attr_hardware(self, data):
        pass

    def read_IntegrationTime(self, attr):
        it = self.measurement_group.integration_time
        if it is None:
            it = float('nan')
        attr.set_value(it)

    def write_IntegrationTime(self, attr):
        self.measurement_group.integration_time = attr.get_write_value()

    def read_MonitorCount(self, attr):
        it = self.measurement_group.monitor_count
        if it is None:
            it = 0
        attr.set_value(it)

    def write_MonitorCount(self, attr):
        self.measurement_group.monitor_count = attr.get_write_value()

    def read_AcquisitionMode(self, attr):
        acq_mode = self.measurement_group.acquisition_mode
        acq_mode_str = AcqMode.whatis(acq_mode)
        attr.set_value(acq_mode_str)

    def write_AcquisitionMode(self, attr):
        acq_mode_str = attr.get_write_value()
        try:
            acq_mode = AcqMode.lookup[acq_mode_str]
        except KeyError:
            raise Exception("Invalid acquisition mode. Must be one of " +
                            ", ".join(list(AcqMode.keys())))
        self.measurement_group.acquisition_mode = acq_mode

    def read_Configuration(self, attr):
        cfg = self.measurement_group.get_user_configuration()
        codec = CodecFactory().getCodec('json')
        data = codec.encode(('', cfg))
        attr.set_value(data[1])

    def write_Configuration(self, attr):
        data = attr.get_write_value()
        cfg = CodecFactory().decode(('json', data))
        util = Util.instance()
        if util.is_svr_starting():
            self.measurement_group._config._value_ref_compat = True
        else:
            self.measurement_group._config._value_ref_compat = False
        self.measurement_group.set_configuration_from_user(cfg)

    def read_NbStarts(self, attr):
        nb_starts = self.measurement_group.nb_starts
        if nb_starts is None:
            nb_starts = int('nan')
        attr.set_value(nb_starts)

    def write_NbStarts(self, attr):
        self.measurement_group.nb_starts = attr.get_write_value()

    def read_Moveable(self, attr):
        moveable = self.measurement_group.moveable
        if moveable is None:
            moveable = 'None'
        attr.set_value(moveable)

    def write_Moveable(self, attr):
        moveable = attr.get_write_value()
        if moveable == 'None':
            moveable = None
        self.measurement_group.moveable = moveable

    def read_SynchDescription(self, attr):
        synch_description = self.measurement_group.synch_description
        codec = CodecFactory().getCodec('json')
        data = codec.encode(('', synch_description))
        attr.set_value(data[1])

    def write_SynchDescription(self, attr):
        data = attr.get_write_value()
        synch_description = CodecFactory().decode(('json', data))
        # translate dictionary keys
        synch_description = \
            self._synch_description_str2enum(synch_description)
        self.measurement_group.synch_description = synch_description

    def read_LatencyTime(self, attr):
        latency_time = self.measurement_group.latency_time
        attr.set_value(latency_time)

    def read_SoftwareSynchronizerInitialDomain(self, attr):
        domain = self.measurement_group.sw_synch_initial_domain
        d = SynchDomain(domain).name
        attr.set_value(d)

    def write_SoftwareSynchronizerInitialDomain(self, attr):
        data = attr.get_write_value()
        try:
            domain = SynchDomain[data]
        except KeyError:
            raise Exception("Invalid domain (can be either Position or Time)")
        self.measurement_group.sw_synch_initial_domain = domain

    def Prepare(self):
        self.measurement_group.prepare()

    def Start(self):
        try:
            self.wait_for_operation()
        except:
            raise Exception("Cannot acquire: already involved in an operation")
        self.measurement_group.start_acquisition()

    def Stop(self):
        self.measurement_group.stop()


class MeasurementGroupClass(PoolGroupDeviceClass):

    #    Class Properties
    class_property_list = {
    }

    #    Device Properties
    device_property_list = {
    }
    device_property_list.update(PoolGroupDeviceClass.device_property_list)

    #    Command definitions
    cmd_list = {
        'Prepare': [[DevVoid, ""], [DevVoid, ""]],
        'Start': [[DevVoid, ""], [DevVoid, ""]]
    }
    cmd_list.update(PoolGroupDeviceClass.cmd_list)

    #    Attribute definitions
    attr_list = {
        'IntegrationTime': [[DevDouble, SCALAR, READ_WRITE],
                            {'Memorized': "true",
                             'Display level': DispLevel.OPERATOR}],
        'MonitorCount': [[DevLong, SCALAR, READ_WRITE],
                         {'Memorized': "true",
                          'Display level': DispLevel.OPERATOR}],
        'AcquisitionMode': [[DevString, SCALAR, READ_WRITE],
                            {'Memorized': "true",
                             'Display level': DispLevel.OPERATOR}],
        'Configuration': [[DevString, SCALAR, READ_WRITE],
                          {'Memorized': "true",
                           'Display level': DispLevel.EXPERT}],
        'NbStarts': [[DevLong, SCALAR, READ_WRITE],
                     {'Memorized': "true",
                      'Display level': DispLevel.OPERATOR}],
        'Moveable': [[DevString, SCALAR, READ_WRITE],
                     {'Memorized': "true",
                      'Display level': DispLevel.EXPERT}],
        # TODO: Does it have sense to memorize SynchDescription?
        'SynchDescription': [[DevString, SCALAR, READ_WRITE],
                             {'Memorized': "true",
                              'Display level': DispLevel.EXPERT}],
        'LatencyTime': [[DevDouble, SCALAR, READ],
                        {'Display level': DispLevel.EXPERT}],
        'SoftwareSynchronizerInitialDomain': [[DevString, SCALAR, READ_WRITE],
                                              {'Memorized': "true",
                                               'Display level':
                                               DispLevel.OPERATOR}],

    }
    attr_list.update(PoolGroupDeviceClass.attr_list)

    def _get_class_properties(self):
        ret = PoolGroupDeviceClass._get_class_properties(self)
        ret['Description'] = "Measurement group device class"
        ret['InheritedFrom'].insert(0, 'PoolGroupDevice')
        return ret
