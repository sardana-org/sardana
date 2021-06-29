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

import json
import time
import threading

from lxml import etree

from PyTango import Util, DevFailed, Except, DevVoid, DevLong, \
    DevLong64, DevString, DevState, DevEncoded, \
    DevVarStringArray, ArgType, \
    READ, READ_WRITE, SCALAR, SPECTRUM

from taurus.core.util.log import DebugIt, LogFilter
from taurus.core.util.codecs import CodecFactory

from sardana import State, InvalidId, SardanaServer
from sardana.sardanaattribute import SardanaAttribute
from sardana.macroserver.macro import Macro
from sardana.macroserver.msdoor import BaseInputHandler
from sardana.macroserver.msexception import MacroServerException
from sardana.tango.core.util import throw_sardana_exception
from sardana.tango.core.attributehandler import AttributeLogHandler
from sardana.tango.core.SardanaDevice import SardanaDevice, SardanaDeviceClass
from sardana.macroserver.msexception import InputCancelled


class TangoInputHandler(BaseInputHandler):

    def __init__(self, door, attr):
        self._value = None
        self._input_waitting = False
        self._input_event = threading.Event()
        self._door = door
        self._attr = attr

    def input(self, input_data=None):
        if input_data is None:
            input_data = {}
        self.input_data = input_data
        timeout = input_data.get('timeout')
        input_data = json.dumps(input_data)
        self._value = None
        self._input_waitting = True
        try:
            self._door.set_attribute(self._attr, value=input_data)
            res = self.input_wait(timeout=timeout)
        finally:
            self._input_waitting = False

        if res is None or res.get('cancel', False):
            raise InputCancelled('Input cancelled by user')
        return res['input']

    def input_received(self, value):
        if not self._input_waitting:
            return
        self._value = json.loads(value)
        self._input_event.set()

    def input_wait(self, timeout=None):
        wait = self._input_event.wait(timeout)
        # if there was a timeout:
        # - set the value to the default value (if one exists)
        # - inform clients that timeout occured and they should not wait for
        #   user input anymore
        if not self._input_event.is_set():
            if 'default_value' in self.input_data:
                self._value = dict(input=self.input_data['default_value'])
            self.send_input_timeout()
        self._input_event.clear()
        return self._value

    def send_input_timeout(self):
        idata = self.input_data
        input_data = dict(type="timeout", macro_id=idata['macro_id'])
        if 'default_value' in idata:
            input_data['default_value'] = idata['default_value']
        input_data = json.dumps(input_data)
        door = self._door
        door.set_attribute(self._attr, value=input_data)


class TangoFunctionHandler(object):

    def __init__(self, door, attr, module_name, format="bz2_pickle"):
        self.door = door
        self.attr = attr
        self.module_name = module_name
        self.format = format

    def handle(self, func_name, *args, **kwargs):
        codec = CodecFactory().getCodec(self.format)
        data = dict(type='function', func_name=func_name,
                    args=args, kwargs=kwargs)
        event_value = codec.encode(('', data))
        self.door.set_attribute(self.attr, value=event_value)

    def __getattr__(self, name):
        def f(*args, **kwargs):
            full_name = self.module_name + "." + name
            return self.handle(full_name, *args, **kwargs)
        f.__name__ = name
        return f


class TangoPylabHandler(TangoFunctionHandler):

    def __init__(self, door, attr, format="bz2_pickle"):
        TangoFunctionHandler.__init__(self, door, attr, "pylab",
                                      format="bz2_pickle")


class TangoPyplotHandler(TangoFunctionHandler):

    def __init__(self, door, attr, format="bz2_pickle"):
        TangoFunctionHandler.__init__(self, door, attr, "pyplot",
                                      format="bz2_pickle")


class Door(SardanaDevice):

    def __init__(self, dclass, name):
        SardanaDevice.__init__(self, dclass, name)
        self._last_result = ()
        self._input_handler = None

    def init(self, name):
        SardanaDevice.init(self, name)
        self._door = None
        self._macro_server_device = None

    def get_door(self):
        return self._door

    def set_door(self, door):
        self._door = door

    door = property(get_door, set_door)

    @property
    def macro_server_device(self):
        return self._macro_server_device

    @property
    def macro_server(self):
        return self.door.macro_server

    def delete_device(self):
        if self.getRunningMacro():
            self.debug("aborting running macro")
            self.macro_executor.abort()
            self.macro_executor.clearMacroStack()

        for handler, filter, format in list(self._handler_dict.values()):
            handler.finish()

        door = self.door
        if door is not None:
            door.remove_listener(self.on_door_changed)

    @DebugIt()
    def init_device(self):
        SardanaDevice.init_device(self)
        levels = 'Critical', 'Error', 'Warning', 'Info', 'Output', 'Debug'
        detect_evts = ()
        non_detect_evts = ['State', 'Status', 'Result', 'RecordData',
                           'MacroStatus', 'Input'] + list(levels)
        self.set_change_events(detect_evts, non_detect_evts)

        util = Util.instance()
        db = util.get_database()

        # Find the macro server for this door
        macro_servers = util.get_device_list_by_class("MacroServer")
        if self.MacroServerName is None:
            self._macro_server_device = macro_servers[0]
        else:
            ms_name = self.MacroServerName.lower()
            for ms in macro_servers:
                if ms.get_name().lower() == ms_name or \
                   ms.alias.lower() == ms_name:
                    self._macro_server_device = ms
                    break

        # support for old doors which didn't have ID
        if self.Id == InvalidId:
            self.Id = self.macro_server_device.macro_server.get_new_id()
            db.put_device_property(self.get_name(), dict(Id=self.Id))

        door = self.door
        if door is None:
            full_name = self.get_name()
            name = full_name
            macro_server = self.macro_server_device.macro_server
            self.door = door = \
                macro_server.create_element(type="Door", name=name,
                                            full_name=full_name, id=self.Id)
            self._setupLogHandlers(levels)

        multi_attr = self.get_device_attr()

        input_attr = multi_attr.get_attr_by_name('Input')
        self._input_handler = ih = TangoInputHandler(self, input_attr)
        door.set_input_handler(ih)

        recorddata_attr = multi_attr.get_attr_by_name('RecordData')
        self._pylab_handler = pylabh = TangoPylabHandler(self, recorddata_attr)
        door.set_pylab_handler(pylabh)

        self._pyplot_handler = pyploth = TangoPyplotHandler(
            self, recorddata_attr)
        door.set_pyplot_handler(pyploth)

        door.add_listener(self.on_door_changed)
        self.set_state(DevState.ON)

    def _setupLogHandlers(self, levels):
        self._handler_dict = {}
        for level in levels:
            handler = AttributeLogHandler(self, level,
                                          max_buff_size=self.MaxMsgBufferSize)
            filter = LogFilter(level=getattr(self, level))
            handler.addFilter(filter)
            self.addLogHandler(handler)
            format = None
            self._handler_dict[level] = handler, filter, format

    def on_door_changed(self, event_source, event_type, event_value):
        # during server startup and shutdown avoid processing element
        # creation events
        if SardanaServer.server_state != State.Running:
            return

        timestamp = time.time()

        name = event_type.name.lower()

        multi_attr = self.get_device_attr()
        try:
            attr = multi_attr.get_attr_by_name(name)
        except DevFailed:
            return

        if name == "state":
            event_value = self.calculate_tango_state(event_value)
        elif name == "status":
            event_value = self.calculate_tango_status(event_value)
        elif name == "recorddata":
            format, value = event_value
            if format is None:
                format = "utf8_json"
            codec = CodecFactory().getCodec(format)
            event_value = codec.encode(('', value))
        else:
            if isinstance(event_value, SardanaAttribute):
                if event_value.error:
                    error = Except.to_dev_failed(*event_value.exc_info)
                timestamp = event_value.timestamp
                event_value = event_value.value

            if attr.get_data_type() == ArgType.DevEncoded:
                codec = CodecFactory().getCodec('utf8_json')
                event_value = codec.encode(('', event_value))
        self.set_attribute(attr, value=event_value, timestamp=timestamp)

    @property
    def macro_executor(self):
        return self.door.macro_executor

    def getRunningMacro(self):
        return self.door.running_macro

    def always_executed_hook(self):
        pass

    def dev_status(self):
        self._status = SardanaDevice.dev_status(self)
        self._status += '\n Macro stack ([state] macro):'
        macro = self.getRunningMacro()
        mstack = ''
        while macro is not None:
            mstate = macro.getMacroStatus()['state']
            mstack = '\n    -[%s]\t%s' % (mstate, macro.getCommand()) + mstack
            macro = macro.getParentMacro()
        self._status += mstack
        return self._status

    def read_attr_hardware(self, data):
        pass

    def readLogAttr(self, attr):
        name = attr.get_name()
        handler, filter, format = self._handler_dict[name]
        handler.read(attr)

    read_Critical = read_Error = read_Warning = read_Info = read_Output = \
        read_Debug = read_Trace = readLogAttr

    def read_Input(self, attr):
        attr.set_value('')

    def write_Input(self, attr):
        value = attr.get_write_value()
        self.door.get_input_handler().input_received(value)

    def sendRecordData(self, format, data):
        self.push_change_event('RecordData', format, data)

    def getLogAttr(self, name):
        return self._handler_dict.get(name)

    def read_Result(self, attr):
        #    Add your own code here
        attr.set_value(self._last_result)

    def read_RecordData(self, attr):
        try:
            macro_data = self.door.get_macro_data()
            codec = CodecFactory().getCodec('bz2_pickle')
            data = codec.encode(('', macro_data))
        except MacroServerException as mse:
            throw_sardana_exception(mse)

        attr.set_value(*data)
        # workaround for a bug in PyTango (tango-controls/pytango#147),
        # i.e. temporary solution for issue #447
        # (storing reference to data so it can not be destroyed by GC)
        self.__buf_data = data

    def read_MacroStatus(self, attr):
        attr.set_value('', '')

    def AbortMacro(self):
        macro = self.getRunningMacro()
        if macro is None:
            return
        self.debug("aborting %s" % macro._getDescription())
        self.macro_executor.abort()

    def ReleaseMacro(self):
        macro = self.getRunningMacro()
        if macro is None:
            return
        self.debug("releasing %s" % macro._getDescription())
        self.macro_executor.release()

    def is_ReleaseMacro_allowed(self):
        is_release_allowed = (self.get_state() == Macro.Running
                              or self.get_state() == Macro.Pause)
        return is_release_allowed


    def PauseMacro(self):
        macro = self.getRunningMacro()
        if macro is None:
            print("Unable to pause Null macro")
            return
        self.macro_executor.pause()

    def is_PauseMacro_allowed(self):
        return self.get_state() == Macro.Running

    def StopMacro(self):
        macro = self.getRunningMacro()
        if macro is None:
            return
        self.debug("stopping %s" % macro._getDescription())
        self.macro_executor.stop()

    def is_StopMacro_allowed(self):
        is_stop_allowed = (self.get_state() == Macro.Running or
                           self.get_state() == Macro.Pause)
        return is_stop_allowed

    def ResumeMacro(self):
        macro = self.getRunningMacro()
        if macro is None:
            return
        self.debug("resuming %s" % macro._getDescription())
        self.macro_executor.resume()

    def is_ResumeMacro_allowed(self):
        return self.get_state() == Macro.Pause

    def RunMacro(self, par_str_list):
        # first empty all the buffers
        for handler, filter, fmt in list(self._handler_dict.values()):
            handler.clearBuffer()

        if len(par_str_list) == 0:
            return []

        xml_seq = self.door.run_macro(par_str_list, asynch=True)
        return [etree.tostring(xml_seq, encoding='unicode',
                               pretty_print=False)]

    def is_RunMacro_allowed(self):
        return self.get_state() in [Macro.Finished, Macro.Abort,
                                    Macro.Exception]

    def SimulateMacro(self, par_str_list):
        raise Exception("Not implemented yet")

    def GetMacroEnv(self, argin):
        macro_name = argin[0]
        if len(argin) > 1:
            macro_env = argin[1:]
        else:
            macro_env = self.door.get_macro_class_info(macro_name).env
        env = self.door.get_env(macro_env, macro_name=macro_name)
        ret = []
        for k, v in env.items():
            ret.extend((k, v))
        return ret

    def is_GetMacroEnv_allowed(self):
        return self.get_state() in [Macro.Finished, Macro.Abort,
                                    Macro.Exception]


class DoorClass(SardanaDeviceClass):

    #    Class Properties
    class_property_list = {
    }

    #    Device Properties
    device_property_list = {
        'Id': [DevLong64, "Internal ID", [InvalidId]],
        'MaxMsgBufferSize':
            [DevLong,
             'Maximum size for the Output, Result, Error, Warning, Debug and '
             'Info buffers',
             [512]],
        'MacroServerName':
            [DevString,
             'Name of the macro server device to connect to. [default: None, '
             'meaning connect to the first registered macroserver',
             None],
    }

    #    Command definitions
    cmd_list = {
        'PauseMacro':
            [[DevVoid, ""],
             [DevVoid, ""]],
        'AbortMacro':
            [[DevVoid, ""],
             [DevVoid, ""]],
        'ReleaseMacro':
            [[DevVoid, ""],
             [DevVoid, ""]],
        'StopMacro':
            [[DevVoid, ""],
             [DevVoid, ""]],
        'ResumeMacro':
            [[DevVoid, ""],
             [DevVoid, ""]],
        'RunMacro':
            [[DevVarStringArray, 'Macro name and parameters'],
             [DevVarStringArray, 'Macro Result']],
        'SimulateMacro':
            [[DevVarStringArray, 'Macro name and parameters'],
             [DevVarStringArray, 'Macro statistics']],
        'GetMacroEnv':
            [[DevVarStringArray, 'Macro name followed by an '
                'optional list of environment names'],
             [DevVarStringArray, 'Macro environment as a list of '
                'pairs keys, value']],
        #        'ReloadMacro':
        #            [[DevVarStringArray, "Macro(s) name(s)"],
        #            [DevVarStringArray, "[OK] if successfull or a traceback " \
        #                "if there was a error (one string with complete traceback of " \
        #                "each error)"]],
        #        'ReloadMacroLib':
        #            [[DevVarStringArray, "MacroLib(s) name(s)"],
        #            [DevVarStringArray, "[OK] if successfull or a traceback " \
        #                "if there was a error (one string with complete traceback of " \
        #                "each error)"]],
    }

    #    Attribute definitions
    attr_list = {
        'Result': [[DevString, SPECTRUM, READ, 512],
                   {'label': 'Result for the last macro', }],
        'Critical': [[DevString, SPECTRUM, READ, 512],
                     {'label': 'Macro critical error message', }],
        'Error': [[DevString, SPECTRUM, READ, 512],
                  {'label': 'Macro error message', }],
        'Warning': [[DevString, SPECTRUM, READ, 512],
                    {'label': 'Macro warning message', }],
        'Info': [[DevString, SPECTRUM, READ, 512],
                 {'label': 'Macro information message', }],
        'Debug': [[DevString, SPECTRUM, READ, 512],
                  {'label': 'Macro debug message', }],
        'Output': [[DevString, SPECTRUM, READ, 512],
                   {'label': 'Macro output message', }],
        'Input': [[DevString, SCALAR, READ_WRITE],
                  {'label': 'Macro input prompt', }],
        'RecordData': [[DevEncoded, SCALAR, READ],
                       {'label': 'Record Data', }],
        'MacroStatus': [[DevEncoded, SCALAR, READ],
                        {'label': 'Macro Status', }],
    }
