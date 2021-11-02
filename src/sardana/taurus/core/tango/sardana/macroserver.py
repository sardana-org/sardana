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

"""The macroserver submodule. It contains specific part of macroserver"""

__all__ = ['BaseInputHandler', 'BaseDoor', 'BaseMacroServer',
           'registerExtensions']

__docformat__ = 'restructuredtext'

import sys
import time
import uuid
import math
import weakref
import threading
import os.path as osp
import os

from lxml import etree

import PyTango

from taurus import Device, Factory
from taurus.core.taurusmanager import TaurusManager
from taurus.core.taurusbasetypes import TaurusEventType, TaurusSWDevState, \
    TaurusSerializationMode

from taurus.core import TaurusDevState
from taurus.core.util.log import Logger
from taurus.core.util.containers import CaselessDict
from taurus.core.util.codecs import CodecFactory
from taurus.core.util.event import EventGenerator, AttributeEventWait
from taurus.core.tango import TangoDevice


from sardana.sardanautils import recur_map
from .macro import MacroInfo, Macro, MacroNode, ParamFactory, \
    SingleParamNode, ParamNode, createMacroNode
from .sardana import BaseSardanaElementContainer, BaseSardanaElement
from .pool import getChannelConfigs
from itertools import zip_longest

CHANGE_EVT_TYPES = TaurusEventType.Change, TaurusEventType.Periodic


def get_terminal_size(fileno=None):
    try:
        if fileno is None:
            fileno = sys.stdout.fileno()
        if not os.isatty(fileno):
            return None
        return os.get_terminal_size(fileno)
    except Exception:
        return None


def _get_nb_lines(nb_chrs, max_chrs):
    return int(math.ceil(float(nb_chrs)/max_chrs))


class Attr(Logger, EventGenerator):

    def __init__(self, dev, name, obj_class, attr):
        self._dev = weakref.ref(dev)
        self._obj_class = obj_class
        self._attr = attr
        self.call__init__(Logger, name)
        event_name = '%s %s' % (dev.getNormalName(), name)
        self.call__init__(EventGenerator, event_name)

        self._attr.addListener(self)

    def eventReceived(self, src, type, evt_value):
        if type == TaurusEventType.Error:
            self.fireEvent(None)
        elif type != TaurusEventType.Config:
            if evt_value:
                self.fireEvent(evt_value.rvalue)
            else:
                self.fireEvent(None)

    def getTaurusAttribute(self):
        return self._attr
    
    def read(self, cache=False):
        return self._attr.read(cache)

    def __getattr__(self, name):
        return getattr(self._attr, name)


class LogAttr(Attr):

    def __init__(self, dev, name, obj_class, attr, max_buff_size=4096):
        self._log_buffer = []
        self._max_buff_size = max_buff_size
        self.call__init__(Attr, dev, name, obj_class, attr)

    def getLogBuffer(self):
        return self._log_buffer

    def clearLogBuffer(self):
        self._log_buffer = []

    def eventReceived(self, src, type, evt_value):
        if type == TaurusEventType.Change:
            if evt_value is None or evt_value.rvalue is None:
                self.fireEvent(None)
            else:
                self._log_buffer.extend(evt_value.rvalue)
                while len(self._log_buffer) > self._max_buff_size:
                    self._log_buffer.pop(0)
                if evt_value:
                    self.fireEvent(evt_value.rvalue)


class BaseInputHandler(object):

    def __init__(self):
        try:
            self._input = raw_input
        except NameError:
            self._input = input

    def input(self, input_data=None):
        if input_data is None:
            input_data = {}
        prompt = input_data.get('prompt')
        ret = dict(input=None, cancel=False)
        try:
            if prompt is None:
                ret['input'] = self._input()
            else:
                ret['input'] = self._input(prompt)
        except:
            ret['cancel'] = True
        return ret

    def input_timeout(self, input_data):
        print("input timeout")


class MacroServerDevice(TangoDevice):
    """A class encapsulating a generic macro server device (usually a
    MacroServer or a Door"""

    def _getEventWait(self):
        if not hasattr(self, '_evt_wait'):
            # create an object that waits for attribute events.
            # each time we use it we have to connect and disconnect to an
            # attribute
            self._evt_wait = AttributeEventWait()
        return self._evt_wait


class ExperimentConfiguration(object):

    def __init__(self, door):
        self._door = door

    def get(self, cache=False):
        door = self._door
        macro_server = door.macro_server
        env = door.getEnvironment()

        ret = dict(ScanDir=env.get('ScanDir'),
                   DataCompressionRank=env.get('DataCompressionRank', 1),
                   PreScanSnapshot=env.get('PreScanSnapshot', []))
        scan_file = env.get('ScanFile')
        if scan_file is None:
            scan_file = []
        elif isinstance(scan_file, str):
            scan_file = [scan_file]
        ret['ScanFile'] = scan_file
        mnt_grps = macro_server.getElementsOfType("MeasurementGroup")
        mnt_grps_names = [mnt_grp.name for mnt_grp in list(mnt_grps.values())]
        mnt_grps_full_names = list(mnt_grps.keys())

        active_mnt_grp = env.get('ActiveMntGrp')
        if active_mnt_grp is None and len(mnt_grps):
            active_mnt_grp = mnt_grps_names[0]
            door.putEnvironment('ActiveMntGrp', active_mnt_grp)

        ret['ActiveMntGrp'] = active_mnt_grp
        ret['MntGrpConfigs'] = mnt_grp_configs = CaselessDict()

        if len(mnt_grps) == 0:
            return ret

        mnt_grp_grps = PyTango.Group("grp")
        # use full names cause we may be using a different Tango database
        mnt_grp_grps.add(mnt_grps_full_names)

        codec = CodecFactory().getCodec('json')
        replies = mnt_grp_grps.read_attribute("configuration")
        for mnt_grp, reply in zip(mnt_grps_names, replies):
            try:
                mnt_grp_configs[mnt_grp] = \
                    codec.decode(('json', reply.get_data().value))[1]
            except Exception as e:
                from taurus.core.util.log import warning
                warning('Cannot load Measurement group "%s": %s',
                        repr(mnt_grp), repr(e))
        return ret

    def set(self, conf, mnt_grps=None):
        """Sets the ExperimentConfiguration dictionary."""
        if mnt_grps is None:
            mnt_grps = list(conf['MntGrpConfigs'].keys())

        codec = CodecFactory().getCodec('json')
        msg_error = ''
        for mnt_grp in mnt_grps:
            try:
                mnt_grp_cfg = conf['MntGrpConfigs'][mnt_grp]
                if mnt_grp_cfg is None:  # a mntGrp to be deleted
                    pool = self._getPoolOfElement(mnt_grp)
                    pool.DeleteElement(mnt_grp)
                else:
                    try:
                        # TODO: Fix incorrect implementation. It must check if
                        #  the measurement group is part of the Pools
                        #  controlled by the MacroServer. Otherwise,
                        #  it must raise an exception.
                        mnt_grp_dev = Device(mnt_grp)
                    except Exception:
                        # if the mnt_grp did not already exist, create it now
                        chconfigs = getChannelConfigs(mnt_grp_cfg)
                        chnames, chinfos = list(zip(*chconfigs))  # unzipping
                        # We assume that all the channels belong to the same
                        # pool!
                        pool = self._getPoolOfElement(chnames[0])
                        pool.createMeasurementGroup([mnt_grp] + list(chnames))
                        mnt_grp_dev = Device(mnt_grp)

                    # TODO when we start using measurement group extension
                    # change the code below with the following:
                    # mnt_grp.setConfiguration(mnt_grp_cfg)

                    data = codec.encode(('', mnt_grp_cfg))[1]
                    mnt_grp_dev.write_attribute('configuration', data)
            except PyTango.DevFailed as df:
                # Take the description of the first exception.
                desc = df.args[0].desc
                desc = desc.replace('\r', '')
                desc = desc.replace('\n', '')
                msg_error += 'Measurement Group {0}:\n'\
                             '{1}\n\n'.format(mnt_grp, desc)

        if len(msg_error) > 0:
            raise RuntimeError(msg_error)

        # Send the environment changes
        env = dict(ScanDir=conf.get('ScanDir'),
                   ScanFile=conf.get('ScanFile'),
                   DataCompressionRank=conf.get('DataCompressionRank', -1),
                   ActiveMntGrp=conf.get('ActiveMntGrp'),
                   PreScanSnapshot=conf.get('PreScanSnapshot'))

        self._door.putEnvironments(env)

    def _getPoolOfElement(self, elementname):
        ms = self._door.macro_server
        einfo = ms.getElementInfo(elementname)
        poolname = einfo.pool
        return ms.getElementInfo(poolname)

#    @property
#    def _pool(self):
#        pooldict = self._door.macro_server.getElementsOfType('Pool')
#        if len(pooldict)==0:
#            raise ValueError('Cannot access the Pool')
#        elif len(pooldict)>1:
#            raise ValueError('Multiple pools are not supported')
#        poolinfo = pooldict.values()[0]
#        return poolinfo


class BaseDoor(MacroServerDevice):
    """ Class encapsulating Door device functionality."""

    On = PyTango.DevState.ON
    Running = PyTango.DevState.RUNNING
    Paused = PyTango.DevState.STANDBY

    Critical = 'Critical'
    Error = 'Error'
    Warning = 'Warning'
    Info = 'Info'
    Output = 'Output'
    Debug = 'Debug'
    Result = 'Result'
    RecordData = 'RecordData'

    BlockStart = '<BLOCK>'
    BlockFinish = '</BLOCK>'

    log_streams = (Error, Warning, Info, Output, Debug, Result)

    # maximum execution time without user interruption
    # this also means a time window within door state events must arrive
    # 0.1 s was not enough on Windows (see sardana-ord/sardana#725)
    InteractiveTimeout = .3

    def __init__(self, name, **kw):
        self._log_attr = CaselessDict()
        self._block_lines = 0
        self._in_block = False
        self._macro_server = None
        self._running_macros = None
        self._running_macro = None
        self._last_running_macro = None
        self._user_xml = None
        self._ignore_logs = kw.get("ignore_logs", False)
        self._silent = kw.get("silent", True)
        self._debug = kw.get("debug", False)
        self._output_stream = kw.get("output", sys.stdout)
        self._writeLock = threading.Lock()
        self._input_handler = self.create_input_handler()
        self._len_last_data_line = 1

        self.call__init__(MacroServerDevice, name, **kw)

        self._old_door_state = PyTango.DevState.UNKNOWN
        self._old_sw_door_state = TaurusDevState.Undefined

        self.stateObj.addListener(self.stateChanged)

        for log_name in self.log_streams:
            tg_attr = self.getAttribute(log_name)
            attr = LogAttr(self, log_name, None, tg_attr)
            if log_name == 'Result':
                attr.subscribeEvent(self.resultReceived, log_name)
            else:
                attr.subscribeEvent(self.logReceived, log_name)
            self._log_attr[log_name] = attr

        self.__input_attr = self.getAttribute("Input")
        self.__input_attr.addListener(self.inputReceived)

        self.__record_data_attr = self.getAttribute('RecordData')
        self.__record_data_attr.addListener(self.recordDataReceived)

        self.__macro_status_attr = self.getAttribute('MacroStatus')
        self.__macro_status_attr.addListener(self.macroStatusReceived)

        self._experiment_configuration = ExperimentConfiguration(self)

    def create_input_handler(self):
        return BaseInputHandler()

    def get_input_handler(self):
        return self._input_handler

    def get_color_mode(self):
        return "NoColor"

    # def macrosChanged(self, s, v, t):
    #    pass

    @property
    def log_start(self):
        if not hasattr(self, "_log_start"):
            import taurus.core.util.console
            if self.get_color_mode() == "NoColor":
                kls = taurus.core.util.console.NoColors
            else:
                kls = taurus.core.util.console.TermColors
            self._log_start = {BaseDoor.Critical: kls.LightRed,
                               BaseDoor.Error: kls.Red,
                               BaseDoor.Info: kls.LightBlue,
                               BaseDoor.Warning: kls.Brown,
                               BaseDoor.Output: kls.Normal,
                               BaseDoor.Debug: kls.DarkGray,
                               BaseDoor.Result: kls.LightGreen}
        return self._log_start

    @property
    def log_stop(self):
        if not hasattr(self, "_log_stop"):
            import taurus.core.util.console
            if self.get_color_mode() == "NoColor":
                kls = taurus.core.util.console.NoColors
            else:
                kls = taurus.core.util.console.TermColors
            self._log_stop = {BaseDoor.Critical: kls.Normal,
                              BaseDoor.Error: kls.Normal,
                              BaseDoor.Info: kls.Normal,
                              BaseDoor.Warning: kls.Normal,
                              BaseDoor.Output: kls.Normal,
                              BaseDoor.Debug: kls.Normal,
                              BaseDoor.Result: kls.Normal}
        return self._log_stop

    def getStateAttr(self):
        return self._state_attr

    @property
    def macro_server(self):
        if self._macro_server is None:
            self._macro_server = self._get_macroserver_for_door()
        return self._macro_server

    def _get_macroserver_for_door(self):
        """Returns the MacroServer device object in the same DeviceServer as
        this door"""
        db = self.getParentObj()
        door_name = self.dev_name()
        server_list = list(db.get_server_list('MacroServer/*'))
        server_list += list(db.get_server_list('Sardana/*'))
        for server in server_list:
            server_devs = db.get_device_class_list(server)
            devs, klasses = server_devs[0::2], server_devs[1::2]
            for dev in devs:
                if dev.lower() == door_name:
                    for i, klass in enumerate(klasses):
                        if klass == 'MacroServer':
                            full_name = db.getFullName() + "/" + devs[i]
                            return self.factory().getDevice(full_name)
        else:
            return None

    def setDebugMode(self, state):
        self._debug = state

    def getDebugMode(self):
        return self._debug

    def setSilent(self, yesno):
        self._silent = yesno

    def isSilent(self):
        return self._silent

    def getLogObj(self, log_name='Debug'):
        return self._log_attr.get(log_name, None)

    def getRunningXML(self):
        return self._user_xml

    def getRunningMacro(self):
        return self._running_macro

    def getLastRunningMacro(self):
        return self._last_running_macro

    def abort(self, synch=True):
        if not synch:
            self.command_inout("AbortMacro")
            return

        evt_wait = AttributeEventWait(self.getAttribute("state"))
        evt_wait.lock()
        try:
            time_stamp = time.time()
            self.command_inout("AbortMacro")
            evt_wait.waitForEvent((self.Running, ), equal=False,
                                  after=time_stamp,
                                  reactivity=self.InteractiveTimeout)
        finally:
            evt_wait.unlock()
            evt_wait.disconnect()

    def release(self, synch=True):
        if not synch:
            try:
                self.command_inout("ReleaseMacro")
            except PyTango.DevFailed as df:
                # Macro already finished - no need to release
                if df.args[0].reason == "API_CommandNotAllowed":
                    pass
            return

        evt_wait = AttributeEventWait(self.getAttribute("state"))
        evt_wait.lock()
        try:
            time_stamp = time.time()
            try:
                self.command_inout("ReleaseMacro")
            except PyTango.DevFailed as df:
                # Macro already finished - no need to release
                if df.args[0].reason == "API_CommandNotAllowed":
                    return
            evt_wait.waitForEvent((self.Running, ), equal=False,
                                  after=time_stamp,
                                  reactivity=self.InteractiveTimeout)
        finally:
            evt_wait.unlock()
            evt_wait.disconnect()

    def stop(self, synch=True):
        if not synch:
            self.command_inout("StopMacro")
            return

        evt_wait = AttributeEventWait(self.getAttribute("state"))
        evt_wait.lock()
        try:
            time_stamp = time.time()
            self.command_inout("StopMacro")
            evt_wait.waitForEvent((self.Running, ), equal=False,
                                  after=time_stamp,
                                  reactivity=self.InteractiveTimeout)
        finally:
            evt_wait.unlock()
            evt_wait.disconnect()
    

    def _clearLogBuffer(self):
        list(map(LogAttr.clearLogBuffer, list(self._log_attr.values())))

    def _clearRunMacro(self):
        self._running_macros = None
        self._running_macro = None
        self._user_xml = None
        self._block_lines = 0

    def _createMacroXml(self, macro_name, macro_params):
        """Creation of the macro XML object.

        :param macro_name: (str) macro name
        :param macro_params: (sequence[str]) list of parameter values,
            if repeat parameters are used parameter values may be sequences
            itself.
        :return (lxml.etree._Element) macro XML element
        """
        macro_info = self.macro_server.getMacroInfoObj(macro_name)
        params_def = macro_info.parameters
        macro_node = createMacroNode(macro_name, params_def, macro_params)
        return macro_node.toXml()

    def preRunMacro(self, obj, parameters):
        self._clearLogBuffer()
        self._clearRunMacro()

        xml_root = None
        if isinstance(obj, str):
            if obj.startswith('<') and not parameters:
                xml_root = etree.fromstring(obj)
            else:
                macros = []
                if len(parameters) == 0:
                    macros_strs = obj.split('\n')
                    for m in macros_strs:
                        pars = m.split()
                        macros.append((pars[0], pars[1:]))
                else:
                    parameters = recur_map(str, parameters)
                    macros.append((obj, parameters))
                xml_root = xml_seq = etree.Element('sequence')
                for m in macros:
                    macro_name = m[0]
                    macro_params = m[1]
                    xml_macro = self._createMacroXml(macro_name, macro_params)
                    xml_macro.set('id', str(uuid.uuid1()))
                    xml_seq.append(xml_macro)
        elif etree.iselement(obj):
            xml_root = obj
        else:
            raise TypeError('obj must be a string or a etree.Element')

        self._running_macros = {}
        for macro_xml in xml_root.xpath('//macro'):
            id, name = macro_xml.get('id'), macro_xml.get('name')
            self._running_macros[id] = Macro(self, name, id, macro_xml)
        return xml_root

    def postRunMacro(self, result, synch):
        pass

    def runMacro(self, obj, parameters=[], synch=False):
        self._user_xml = self.preRunMacro(obj, parameters)
        result = self._runMacro(self._user_xml, synch=synch)
        return self.postRunMacro(result, synch)

    def _runMacro(self, xml, synch=False):
        if not synch:
            return self.command_inout("RunMacro",
                                      [etree.tostring(xml,
                                                      encoding='unicode')])
        timeout = self.InteractiveTimeout
        evt_wait = self._getEventWait()
        evt_wait.connect(self.getAttribute("state"))
        evt_wait.lock()
        try:
            evt_wait.waitForEvent((self.Running, ), equal=False,
                                  reactivity=timeout)
            # Clear event set to not confuse the value coming from the
            # connection with the event of of end of the macro execution
            # in the next wait event. This was observed on Windows where
            # the time stamp resolution is not better than 1 ms.
            evt_wait.clearEventSet()
            ts = time.time()
            result = self.command_inout("RunMacro",
                                        [etree.tostring(xml,
                                                        encoding='unicode')])
            evt_wait.waitForEvent((self.Running, ), after=ts,
                                  reactivity=timeout)
            if synch:
                evt_wait.waitForEvent((self.Running, ), equal=False, after=ts,
                                      reactivity=timeout)
        finally:
            self._clearRunMacro()
            evt_wait.unlock()
            evt_wait.disconnect()
        return result

    def stateChanged(self, s, t, v):
        # In contrary to the Taurus3 the Taurus4 raises exceptions when the
        # device server is getting down and we try to retrieve the state.
        # In this case provide the same behavior as Taurus3 - assign None to
        # the old state
        try:
            self._old_door_state = self.stateObj.rvalue
        except PyTango.DevFailed:
            self._old_door_state = None

        self._old_sw_door_state = self.state

    def resultReceived(self, log_name, result):
        """Method invoked by the arrival of a change event on the Result
        attribute"""
        if self._ignore_logs or self._running_macro is None:
            return
        self._running_macro.setResult(result)
        return result

    def putEnvironment(self, name, value):
        self.macro_server.putEnvironment(name, value)

    def putEnvironments(self, obj):
        self.macro_server.putEnvironments(obj)

    setEnvironment = putEnvironment
    setEnvironments = putEnvironments

    def getEnvironment(self, name=None):
        return self.macro_server.getEnvironment(name=name)

    def inputReceived(self, s, t, v):
        if t not in CHANGE_EVT_TYPES:
            return
        if v is None or self._running_macros is None:
            return
        input_data = CodecFactory().decode(('json', v.value))
        self.processInput(input_data)

    def processInput(self, input_data):
        TaurusManager().addJob(self._processInput, None, input_data)

    def _processInput(self, input_data):
        input_type = input_data['type']
        if input_type == 'input':
            result = self._input_handler.input(input_data)
            if result['input'] == '' and 'default_value' in input_data:
                result['input'] = input_data['default_value']
            result = CodecFactory().encode('json', ('', result))[1]
            self.write_attribute('Input', result)
        elif input_type == 'timeout':
            self._input_handler.input_timeout(input_data)

    def recordDataReceived(self, s, t, v):
        if t not in CHANGE_EVT_TYPES:
            return
        return self._processRecordData(v)

    def _processRecordData(self, data):
        if data is None or data.rvalue is None:
            return
        data = data.rvalue

        size = len(data[1])
        if size == 0:
            return
        format = data[0]
        codec = CodecFactory().getCodec(format)
        data = codec.decode(data)
        return data

    def processRecordData(self, data):
        pass

    def macroStatusReceived(self, s, t, v):
        if v is None or self._running_macros is None:
            return
        if t not in CHANGE_EVT_TYPES:
            return

        v = v.value
        if not len(v[1]):
            return
        format = v[0]
        codec = CodecFactory().getCodec(format)

        fmt, data = codec.decode(v)
        for macro_status in data:
            id = macro_status.get('id')
            macro = self._running_macros.get(id)
            self._last_running_macro = self._running_macro = macro
            # if we don't have the ID it's because the macro is running a
            # submacro or another client is connected to the same door (shame
            #  on him!) and executing a macro we discard this event
            if macro is not None:
                macro.__dict__.update(macro_status)
        return data

    def logReceived(self, log_name, output):
        term_size = get_terminal_size()
        max_chrs = term_size.columns if term_size else None
        if not output or self._silent or self._ignore_logs:
            return

        if log_name == self.Debug and not self._debug:
            return

        o = self.log_start[log_name]
        for line in output:
            if not self._debug:
                if line == self.BlockStart:
                    self._in_block = True
                    for i in range(self._block_lines):
                        if max_chrs is None:
                            nb_lines = 1
                        else:
                            nb_lines = _get_nb_lines(
                                self._len_last_data_line,
                                max_chrs)
                        # per each line: erase current line,
                        # go up one line and erase current line
                        o += '\x1b[2K\x1b[1A\x1b[2K' * nb_lines
                    self._block_lines = 0
                    continue
                elif line == self.BlockFinish:
                    self._in_block = False
                    continue
                else:
                    self._len_last_data_line = len(line)
                    if self._in_block:
                        self._block_lines += 1
                    else:
                        self._block_lines = 0

            o += "%s\n" % line
        o += self.log_stop[log_name]
        self.write(o)

    def write(self, msg, stream=None):
        if self.isSilent():
            return
        out = self._output_stream
        if stream is not None:
            start, stop = self.log_start.get(stream), self.log_stop.get(stream)
            if start is not None and stop is not None:
                out.write(start)
                out.write(msg)
                out.write(stop)
                out.flush()
                return
        out.write(msg)
        out.flush()

    def writeln(self, msg='', stream=None):
        self.write("%s\n" % msg, stream=stream)

    def getExperimentConfigurationObj(self):
        return self._experiment_configuration

    def getExperimentConfiguration(self):
        return self._experiment_configuration.get()

    def setExperimentConfiguration(self, config, mnt_grps=None):
        self._experiment_configuration.set(config, mnt_grps=mnt_grps)


class UnknownMacroServerElementFormat(Exception):
    pass


class MacroPath(object):

    def __init__(self, ms):
        self._ms = weakref.ref(ms)
        self.refresh()

    def refresh(self):
        self.macro_path = mp = self._ms().get_property("MacroPath")[
            "MacroPath"]
        self.base_macro_path = osp.commonprefix(self.macro_path)
        self.rel_macro_path = [osp.relpath for p in (mp, self.base_macro_path)]


class Environment(dict):

    def __init__(self, macro_server):
        dict.__setattr__(self, "_macro_server_", weakref.ref(macro_server))

    def __setattr__(self, key, value):
        ms = self._macro_server_()
        if ms is not None:
            ms.putEnvironment(key, value)

    def __getattr__(self, key):
        return self[key]

    def __delattr__(self, key):
        ms = self._macro_server_()
        if ms is not None:
            ms.removeEnvironment(key)

    def __dir__(self):
        return [key for key in list(self.keys()) if not key.startswith("_")]


class BaseMacroServer(MacroServerDevice):
    """Class encapsulating Macro Server device functionality."""

    def __init__(self, name, **kw):
        self._env = Environment(self)
        self._elements = BaseSardanaElementContainer()
        self.call__init__(MacroServerDevice, name, **kw)

        self.__elems_attr = self.getAttribute("Elements")
        try:
            serialization_mode = TaurusSerializationMode.TangoSerial
        except AttributeError:
            serialization_mode = TaurusSerializationMode.Serial
        self.__elems_attr.setSerializationMode(serialization_mode)
        self.__elems_attr.addListener(self.on_elements_changed)
        self.__elems_attr.setSerializationMode(
            TaurusSerializationMode.Concurrent)

        self.__env_attr = self.getAttribute('Environment')
        try:
            serialization_mode = TaurusSerializationMode.TangoSerial
        except AttributeError:
            serialization_mode = TaurusSerializationMode.Serial
        self.__env_attr.setSerializationMode(serialization_mode)
        self.__env_attr.addListener(self.on_environment_changed)
        self.__env_attr.setSerializationMode(
            TaurusSerializationMode.Concurrent)

    NO_CLASS_TYPES = 'ControllerClass', 'ControllerLibrary', \
                     'MacroLibrary', 'Instrument', 'Meta', 'ParameterType'

    def on_environment_changed(self, evt_src, evt_type, evt_value):
        try:
            return self._on_environment_changed(evt_src, evt_type, evt_value)
        except Exception:
            self.error("Exception occurred processing environment")
            self.error("Details:", exc_info=1)
            return set(), set(), set()

    def _on_environment_changed(self, evt_src, evt_type, evt_value):
        ret = added, removed, changed = set(), set(), set()
        if evt_type not in CHANGE_EVT_TYPES:
            return ret

        env = CodecFactory().decode(evt_value.rvalue)

        for key, value in list(env.get('new', {}).items()):
            self._addEnvironment(key, value)
            added.add(key)
        for key in env.get('del', []):
            self._removeEnvironment(key)
            removed.add(key)
        for key, value in list(env.get('change', {}).items()):
            self._removeEnvironment(key)
            self._addEnvironment(key, value)
            changed.add(key)
        return ret

    def _addEnvironment(self, key, value):
        self._env[key] = value

    def _removeEnvironment(self, key):
        try:
            self._env.pop(key)
        except KeyError:
            pass

    def putEnvironment(self, name, value):
        self.putEnvironments({name: value})

    def putEnvironments(self, obj):
        obj = dict(new=obj)
        codec = CodecFactory().getCodec('pickle')
        self.write_attribute('Environment', codec.encode(('', obj)))

    setEnvironment = putEnvironment
    setEnvironments = putEnvironments

    def getEnvironment(self, name=None):
        if name is None:
            return self._env
        else:
            return self._env[name]

    def removeEnvironment(self, key):
        keys = key,
        return self.removeEnvironments(keys)

    def removeEnvironments(self, keys):
        obj = {'del': keys}
        codec = CodecFactory().getCodec('pickle')
        self.write_attribute('Environment', codec.encode(('', obj)))

    def getObject(self, element_info):
        elem_type = element_info.getType()
        if elem_type in self.NO_CLASS_TYPES:
            obj = object()
        elif "MacroCode" in element_info.interfaces:
            obj = self._createMacroClassObject(element_info)
        else:
            obj = self._createDeviceObject(element_info)
        return obj

    def _createMacroClassObject(self, element_info):
        return MacroInfo(from_json=element_info._data)

    def _createDeviceObject(self, element_info):
        return Factory().getDevice(element_info.full_name)

    def on_elements_changed(self, evt_src, evt_type, evt_value):
        try:
            return self._on_elements_changed(evt_src, evt_type, evt_value)
        except Exception:
            self.error("Exception occurred processing elements")
            self.error("Details:", exc_info=1)
            return set(), set(), set()

    def _on_elements_changed(self, evt_src, evt_type, evt_value):
        ret = added, removed, changed = set(), set(), set()
        if evt_type not in CHANGE_EVT_TYPES:
            return ret
        try:
            elems = CodecFactory().decode(evt_value.rvalue)
        except:
            self.error("Could not decode element info format=%s len=%s",
                       evt_value.rvalue[0], len(evt_value.rvalue[1]))
            return ret

        for element_data in elems.get('new', ()):
            element_data['manager'] = self
            element = self._addElement(element_data)
            added.add(element)
        for element_data in elems.get('del', ()):
            element = self._removeElement(element_data)
            removed.add(element)
        for element_data in elems.get('change', ()):
            element = self._removeElement(element_data)
            element_data['manager'] = self
            element = self._addElement(element_data)
            changed.add(element)
        return ret

    def _addElement(self, element_data):
        element = BaseSardanaElement(**element_data)
        self.getElementsInfo().addElement(element)
        return element

    def _removeElement(self, element_data):
        full_name = element_data['full_name']
        element = self.getElementInfo(full_name)
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

    def getElementNamesWithInterface(self, interface):
        return self.getElementsInfo().getElementNamesWithInterface(interface)

    def getElementsWithInterface(self, interface):
        return self.getElementsInfo().getElementsWithInterface(interface)

    def getElementsWithInterfaces(self, interfaces):
        return self.getElementsInfo().getElementsWithInterfaces(interfaces)

    def getElementsOfType(self, elem_type):
        return self.getElementsInfo().getElementsOfType(elem_type)

    def getElementsOfTypes(self, elem_types):
        elems = CaselessDict()
        for elem_type in elem_types:
            elems.update(self.getElementsOfType(elem_type))
        return elems

    def getInterfaces(self):
        return self.getElementsInfo().getInterfaces()

    def getExpChannelElements(self):
        channel_types = "CTExpChannel", "ZeroDExpChannel", "OneDExpChannel", \
            "TwoDExpChannel", "PseudoCounter"
        return self.getElementsOfTypes(channel_types)

    # -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # Macro API
    # -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    def getMacros(self):
        iname = 'MacroCode'
        return dict(self.getElementsInfo().getElementsWithInterface(iname))

    def getMacroInfoObj(self, macro_name):
        iname = 'MacroCode'
        return self.getElementsInfo().getElementWithInterface(macro_name,
                                                              iname)

    def getMacroStrList(self):
        return self.getElementNamesWithInterface('MacroCode')

    def getMacroNodeObj(self, macro_name):
        """
        This method retrieves information about macro from MacroServer
        and creates MacroNode object, filled with all information about
        parameters.

        :param macro_name: (str) macro name

        :return: (MacroNode)

        See Also: fillMacroNodeAddidtionalInfos
        """

        macroInfoObj = self.getMacroInfoObj(macro_name)
        if macroInfoObj is None:
            return
        # fill macro parameters
        paramsInfo = macroInfoObj.parameters
        macroNode = MacroNode(name=macro_name, params_def=paramsInfo)
        hasParams = bool(len(paramsInfo))
        macroNode.setHasParams(hasParams)
        # fill allowed hook places
        allowedHookPlaces = []
        hints = macroInfoObj.hints
        if hints is not None:
            for hook in hints.get('allowsHooks', []):
                allowedHookPlaces.append(str(hook))
        macroNode.setAllowedHookPlaces(allowedHookPlaces)
        return macroNode

    def validateMacroName(self, macroName):
        macroInfo = self.getElementInfo(macroName)
        if macroInfo is None:
            raise Exception(
                "%s macro does not exist in this sardana system." % macroName)
        elif macroInfo.type != 'MacroClass':
            raise Exception("%s element is not a macro." % macroName)
        return True

    def validateMacroNode(self, macroNode):
        paramNodes = macroNode.children()
        for paramNode in paramNodes:
            self.validateParamNode(paramNode)
        return True

    def validateParamNode(self, paramNode):
        assert isinstance(paramNode, ParamNode)
        if isinstance(paramNode, SingleParamNode):
            self.validateSingleParam(paramNode)
        else:
            self.validateRepeatParam(paramNode)
        return True

    def validateSingleParam(self, singleParamNode):
        name = singleParamNode.name()
        type = singleParamNode.type()
        value = singleParamNode.value()

        if type == "Boolean":
            pass
        elif type == "Env":
            pass
        elif type == "File":
            pass
        elif type == "Filename":
            pass
        elif type == "MotorParam":
            pass
        elif type == "String":
            pass
        elif type == "User":
            pass
        elif type == "MotorParam":
            pass
        elif type == "Integer":
            int(value)
            min = singleParamNode.min()
            max = singleParamNode.max()
            if min is not None and value < min:
                raise Exception(
                    "%s parameter value: %s is below minimum allowed value."
                    % (name, value))
            if max is not None and value > max:
                raise Exception(
                    "%s parameter value: %s is above maximum allowed value."
                    % (name, value))
        elif type == "Float":
            float(value)
            min = singleParamNode.min()
            max = singleParamNode.max()
            if min is not None and value < min:
                raise Exception(
                    "%s parameter value: %s is below minimum allowed value."
                    % (name, value))
            if max is not None and value > max:
                raise Exception(
                    "%s parameter value: %s is above maximum allowed value."
                    % (name, value))
        else:
            allowedInterfaces = list(self.getInterfaces().keys())
            if type not in allowedInterfaces:
                raise Exception(
                    "No element with %s interface exist in this sardana "
                    "system." % type)
            allowedValues = self.getElementNamesWithInterface(type)
            if value not in allowedValues:
                raise Exception(
                    "%s element with %s interface does not exist in this "
                    "sardana system." % (value, type))
        return True

    def validateRepeatParam(self, repeatParamNode):
        paramName = repeatParamNode.name()
        if repeatParamNode.isBelowMin():
            raise Exception(
                "%s param repeats has not enough repeats." % (paramName))
        if repeatParamNode.isAboveMax():
            raise Exception(
                "%s param repeat has too many repeats." % (paramName))
        repetitions = repeatParamNode.children()
        for repeat in repetitions:
            params = repeat.children()
            for param in params:
                if isinstance(param, SingleParamNode):
                    self.validateSingleParam(param)
                else:
                    self.validateRepeatParam(param)
        return True

    def fillMacroNodeAdditionalInfos(self, macroNode):
        """
        This method fills macroNode information which couldn't be stored
        in XML file.

        :param macroNode: (MacroNode) macro node obj populated from XML
          information

        See also: getMacroNodeObj
        """
        macroName = macroNode.name()
        macroInfoObj = self.getMacroInfoObj(macroName)
        if macroInfoObj is None:
            msg = "It was not possible to get information about {0} " \
                  "macro. Check if MacroServer is alive and if this macro " \
                  "exist.".format(macroName)
            self.info(msg)
            raise Exception("no info about macro {0}".format(macroName))
        allowedHookPlaces = []
        hints = macroInfoObj.hints or {}
        for hook in hints.get("allowsHooks", []):
            allowedHookPlaces.append(str(hook))
        macroNode.setAllowedHookPlaces(allowedHookPlaces)
        hasParams = macroInfoObj.hasParams()
        macroNode.setHasParams(hasParams)
        if hasParams:
            paramList = macroInfoObj.getParamList()
            for paramNode, paramInfo in zip(macroNode.params(), paramList):
                self.__fillParamNodeAdditionalInfos(paramNode, paramInfo)

    def __fillParamNodeAdditionalInfos(self, paramNode, paramInfo):
        """
        This is a protected method foreseen to use only internally by
        fillMacroNodeAdditionaInfos, to be called for every param node obj."""
        type = paramInfo.get('type')
        paramNode.setDescription(str(paramInfo.get("description")))
        min = paramInfo.get("min")
        paramNode.setMin(min)
        max = paramInfo.get("max")
        paramNode.setMax(max)
        if isinstance(type, list):
            paramNode.setParamsInfo(type)
            for repeatNode in paramNode.children():
                for internalParamNode, internalParamInfo in zip(
                        repeatNode.children(), type):
                    self.__fillParamNodeAdditionalInfos(
                        internalParamNode, internalParamInfo)
        else:
            paramNode.setType(str(type))
            paramNode.setDefValue(str(paramInfo.get("default_value")))

    def __fillParamNodesValues(self, paramInfo, paramNode):
        """
        This is a protected method foreseen to use only internally by
        __fillParamNodesValues, to be called for every param node obj.

        :param paramInfo, paramNode:
        :return:

        """

        paramType = paramInfo.get('type')
        paramNode.setDescription(str(paramInfo.get("description")))
        min = paramInfo.get("min")
        paramNode.setMin(min)
        max = paramInfo.get("max")
        paramNode.setMax(max)
        paramNode.setName(paramInfo['name'])
        if isinstance(paramType, list):
            for repeatNode in paramNode.children():
                children = repeatNode.children()
                for child, paramT in zip_longest(children, paramType):
                    if child is None:
                        node = ParamFactory(paramT, repeatNode)
                        repeatNode.insertChild(node)
                    else:
                        self.__fillParamNodesValues(paramT, child)

        else:
            paramNode.setType(str(paramType))
            paramNode.setDefValue(str(paramInfo.get("default_value")))

    def printTree(self, nodes, tabs=0):
        tabs = tabs + 1
        for node in nodes:
            print(('\t'*tabs) + str(type(node)) + str(node))
            if isinstance(node, SingleParamNode):
                pass
            else:
                nodes = node.children()
                self.printTree(nodes, tabs)

    def __recreateParamNodeAdditionalInfos(self, paramNode, paramInfo):
        """
        This is a protected method foreseen to use only internally by
        fillMacroNodeAdditionaInfos, to be called for every param node obj."""
        paramType = paramInfo.get('type')
        min = paramInfo.get("min")
        max = paramInfo.get("max")
        paramNode.setMin(min)
        paramNode.setMax(max)
        paramNode.setDescription(str(paramInfo.get("description")))

        if isinstance(paramType, list):
            paramNode.setParamsInfo(paramType)
            for repeatNode in paramNode.children():
                for internalParamNode, internalParamInfo in zip(
                        repeatNode.children(), paramType):
                    self.__recreateParamNodeAdditionalInfos(
                        internalParamNode, internalParamInfo)
        else:
            paramNode.setType(paramType)
            paramNode.setDefValue(str(paramInfo.get("default_value")))

    def getMacroPathObj(self, cache=False):
        if not hasattr(self, "_macro_path"):
            self._macro_path = MacroPath(self)
        elif not cache:
            self._macro_path.refresh()
        return self._macro_path


def registerExtensions():
    """Registers the macroserver extensions in the
    :class:`taurus.core.tango.TangoFactory`"""
    factory = Factory('tango')
    factory.registerDeviceClass('MacroServer', BaseMacroServer)
    factory.registerDeviceClass('Door', BaseDoor)


def unregisterExtensions():
    """Registers the macroserver extensions in the
    :class:`taurus.core.tango.TangoFactory`"""
    factory = Factory('tango')
    factory.unregisterDeviceClass('MacroServer')
    factory.unregisterDeviceClass('Door')
