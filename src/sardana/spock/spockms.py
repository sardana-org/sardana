#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

"""This package provides the spock macroserver connectivity"""

__all__ = ['GUIViewer', 'SpockBaseDoor', 'QSpockDoor', 'SpockDoor',
           'SpockMacroServer']

import os
import ctypes
import PyTango

from taurus.core import TaurusEventType, TaurusSWDevState, TaurusDevState

from sardana.sardanautils import is_pure_str, is_non_str_seq
from sardana.spock import genutils
from sardana.util.parser import ParamParser
from sardana import sardanacustomsettings

CHANGE_EVTS = TaurusEventType.Change, TaurusEventType.Periodic


if genutils.get_gui_mode() == 'qt':
    from sardana.taurus.qt.qtcore.tango.sardana.macroserver import QDoor, QMacroServer
    BaseDoor = QDoor
    BaseMacroServer = QMacroServer
    BaseGUIViewer = object
else:
    from sardana.taurus.core.tango.sardana.macroserver import BaseDoor, BaseMacroServer
    BaseGUIViewer = object


RUNNING_STATE = TaurusDevState.Ready


class GUIViewer(BaseGUIViewer):

    def __init__(self, door=None):
        BaseGUIViewer.__init__(self)
        self._door = door

    def run(self):
        self.plot()

    def show_scan(self, scan_nb=None, scan_history_info=None, directory_map=None):
        scan_dir, scan_file = None, None
        if scan_nb is None:
            import h5py
            for scan in reversed(scan_history_info):
                scan_dir = scan.get('ScanDir')
                scan_file = scan.get('ScanFile')
                if scan_dir is None or scan_file is None:
                    continue
                if not isinstance(scan_file, str):
                    scan_files = scan_file
                    scan_file = None
                    for fname in scan_files:
                        try:
                            h5py.File(os.path.join(scan_dir, fname), "r")
                        except IOError:
                            pass
                        else:
                            scan_file = fname
                            break
                    if scan_file is None:
                        print("Cannot plot scan:")
                        print("It only works with HDF5 files.")
                        return
                else:
                    try:
                        h5py.File(os.path.join(scan_dir, scan_file), "r")
                    except IOError:
                        print("Cannot plot scan:")
                        print("It only works with HDF5 files.")
                        return
                break
            else:
                print("Cannot plot scan:")
                print("No scan in scan history was saved into a file")
                return
        else:
            for scan in reversed(scan_history_info):
                if scan['serialno'] == scan_nb:
                    scan_dir = scan.get('ScanDir')
                    scan_file = scan.get('ScanFile')
                    if scan_dir is None or scan_file is None:
                        print("Cannot plot scan:")
                        print("Scan %d was not saved into a file" % (scan_nb,))
                        return
                    if not isinstance(scan_file, str):
                        scan_file = scan_file[0]
                    break
            else:
                print("Cannot plot scan:")
                print("Scan %d not found in scan history" % (scan_nb,))
                return

        remote_file = os.path.join(scan_dir, scan_file)

        locations = [scan_dir]
        local_file = None
        if directory_map is None or not scan_dir in directory_map:
            if os.path.isdir(scan_dir):
                if scan_file in os.listdir(scan_dir):
                    local_file = remote_file
        else:
            local_directories = directory_map[scan_dir]
            # local_directories may be either a string or a list of strings
            # the further logic is unified to work on a list, so convert it
            if isinstance(local_directories, str):
                local_directories = [local_directories]
            locations = local_directories
            if scan_dir not in locations:
                locations.append(scan_dir)
            for local_directory in local_directories:
                if os.path.isdir(local_directory):
                    if scan_file in os.listdir(local_directory):
                        local_file = os.path.join(local_directory, scan_file)
                        break
        if local_file is None:
            print("Cannot plot scan:")
            print("Could not find %s in any of the following locations:" %
                  (scan_file,))
            print("\n".join(locations))
            return

        import taurus.qt.qtgui.extra_nexus
        taurus_nexus_widget = taurus.qt.qtgui.extra_nexus.TaurusNeXusBrowser()
        taurus_nexus_widget.setMinimumSize(800, 600)

        print("Trying to open local scan file %s..." % (local_file,))
        taurus_nexus_widget.openFile(local_file)
        taurus_nexus_widget.show()
        nexus_widget = taurus_nexus_widget.neXusWidget()
        entry_name = "entry%d" % scan["serialno"]
        measurement_name = "%s/measurement" % entry_name
        title_name = "%s/title" % entry_name
        windowTitle = scan_file + "[" + entry_name + "]"

        try:
            #entry_index = taurus_nexus_widget.findNodeIndex(local_file, entry_name)
            measurement_index = taurus_nexus_widget.findNodeIndex(
                local_file, measurement_name)
            # nexus_widget.setRootIndex(entry_index)
            nexus_widget.setCurrentIndex(measurement_index)
            nexus_widget.expand(measurement_index)
            title_index = taurus_nexus_widget.findNodeIndex(
                local_file, title_name)
            file_model = nexus_widget.model()
            title = file_model.getNodeFromIndex(title_index)[0]
            windowTitle += " - " + title
        except Exception as e:
            print("Cannot plot scan:")
            print(str(e))

        taurus_nexus_widget.setWindowTitle(windowTitle)

    def plot(self):
        try:
            import sps
        except Exception:
            print('sps module not available. No plotting')
            return

        try:
            import pylab
        except Exception:
            print("pylab not available (try running 'spock -pylab'). "
                  "No plotting")
            return

        door = genutils.get_door()

        try:
            env = dict(door.getEnvironmentObj().read().value)
        except Exception as e:
            print('Unable to read environment. No plotting')
            print(str(e))
            return

        program = door.getNormalName().replace('/', '').replace('_', '')
        try:
            array = env['ActiveMntGrp'].replace(
                '/', '').replace('_', '').upper() + "0D"
            array_ENV = '%s_ENV' % array
        except:
            print('ActiveMntGrp not defined. No plotting')
            return

        if not program in sps.getspeclist():
            print('%s not found. No plotting' % program)
            return

        if not array in sps.getarraylist(program):
            print('%s not found in %s. No plotting' % (array, program))
            return

        if not array_ENV in sps.getarraylist(program):
            print('%s not found in %s. No plotting' % (array_ENV, program))
            return

        try:
            mem = sps.attach(program, array)
            mem_ENV = sps.attach(program, array_ENV)
        except Exception as e:
            print('sps.attach error: %s. No plotting' % str(e))
            return

        # reconstruct the environment
        i, env = 0, {}
        while mem_ENV[i][0] != '':
            line = mem_ENV[i].tostring()
            eq, end = line.index('='), line.index('\x00')
            k, v = line[:eq], line[eq + 1:end]
            env[k] = v
            i += 1

        labels = env['axistitles'].split(' ')

        col_nb = len(labels)

        if col_nb < 4:
            print('No data columns available in sps')
            return

        rows = int(env['nopts'])

        m = mem.transpose()

        x = m[1][:rows]
        colors = 'bgrcmyk'
        col_nb = min(col_nb, len(colors) + 3)
        # skip point_nb, motor and timer columns
        for i in range(3, col_nb):
            y = m[i][:rows]
            line, = pylab.plot(x, y, label=labels[i])
            line.linestyle = '-'
            line.linewidth = 1
            line.color = colors[i - 3]
        pylab.legend()


class SpockBaseDoor(BaseDoor):
    """A CLI version of the Door device"""

    console_editors = 'vi', 'vim', 'nano', 'joe', 'pico', 'emacs'

    Critical = 'Critical'
    Error = 'Error'
    Info = 'Info'
    Warning = 'Warning'
    Output = 'Output'
    Debug = 'Debug'
    Result = 'Result'
    RecordData = 'RecordData'

    MathFrontend = "matplotlib"

    def __init__(self, name, **kw):
        self._consoleReady = kw.get("consoleReady", False)
        if 'silent' not in kw:
            kw['silent'] = False
        self._lines = []
        self._spock_state = None
        self._plotter = GUIViewer(self)
        self.call__init__(BaseDoor, name, **kw)

    def create_input_handler(self):
        from sardana.spock.inputhandler import SpockInputHandler

        return SpockInputHandler()

    def get_color_mode(self):
        return genutils.get_color_mode()

    def _get_macroserver_for_door(self):
        ret = genutils.get_macro_server()
        return ret

    def _preprocessParameters(self, parameters):
        if is_pure_str(parameters):
            inside_str = False
            pars = []
            par = ''
            for c in parameters:
                if c == '"':
                    if inside_str:
                        inside_str = False
                        pars.append(par)
                        par = ''
                    else:
                        inside_str = True
                elif c == ' ':
                    if inside_str:
                        par += c
                    else:
                        pars.append(par)
                        par = ''
                else:
                    par += c
            if par:
                pars.append(par)
            return pars
        elif is_non_str_seq(parameters):
            return parameters

    def preRunMacro(self, obj, parameters):
        return BaseDoor.preRunMacro(self, obj, self._preprocessParameters(parameters))

    def runMacro(self, obj, parameters=[], synch=False):
        return BaseDoor.runMacro(self, obj, parameters=parameters, synch=synch)

    def _handle_second_release(self):
        try:
            self.write('4th Ctrl-C received: Releasing...\n')
            self.release()
            self.block_lines = 0
            self.release()
            self.writeln("Releasing done!")
        except KeyboardInterrupt:
            self.write('5th Ctrl-C received: Giving up...\n')
            self.write('(The macro is probably still executing the on_abort '
                       'method. Either wait or restart the server.)\n')

    def _handle_first_release(self):
        try:
            self.write('3rd Ctrl-C received: Releasing...\n')
            self.block_lines = 0
            self.release()
            self.writeln("Releasing done!")
        except KeyboardInterrupt:
            self._handle_second_release()

    def _handle_abort(self):
        try:
            self.write('2nd Ctrl-C received: Aborting...\n')
            self.block_lines = 0
            self.abort()
            self.writeln("Aborting done!")
        except KeyboardInterrupt:
            self._handle_first_release()

    def _handle_stop(self):
        try:
            self.write('\nCtrl-C received: Stopping...\n')
            self.block_lines = 0
            self.stop()
            self.writeln("Stopping done!")
        except KeyboardInterrupt:
            self._handle_abort()

    def _runMacro(self, xml, **kwargs):
        # kwargs like 'synch' are ignored in this re-implementation
        if self._spock_state != RUNNING_STATE:
            print("Unable to run macro: No connection to door '%s'" %
                  self.getSimpleName())
            raise Exception("Unable to run macro: No connection")
        if self.stateObj.read().rvalue == PyTango.DevState.RUNNING:
            print("Another macro is running. Wait until it finishes...")
            raise Exception("Unable to run macro: door in RUNNING state")
        if xml is None:
            xml = self.getRunningXML()
        kwargs['synch'] = True
        try:
            return BaseDoor._runMacro(self, xml, **kwargs)
        except KeyboardInterrupt:
            self._handle_stop()
        except PyTango.DevFailed as e:
            if is_non_str_seq(e.args) and \
               not isinstance(e.args, str):
                reason, desc = e.args[0].reason, e.args[0].desc
                macro_obj = self.getRunningMacro()
                if reason == 'MissingParam':
                    print("Missing parameter:", desc)
                    print(macro_obj.getInfo().doc)
                elif reason == 'WrongParam':
                    print("Wrong parameter:", desc)
                    print(macro_obj.getInfo().doc)
                elif reason == 'UnkownParamObj':
                    print("Unknown parameter:", desc)
                elif reason == 'MissingEnv':
                    print("Missing environment:", desc)
                elif reason in ('API_CantConnectToDevice',
                                'API_DeviceNotExported'):
                    self._updateState(self._old_sw_door_state,
                                      TaurusSWDevState.Shutdown, silent=True)
                    print("Unable to run macro: No connection to door '%s'" %
                          self.getSimpleName())
                else:
                    print("Unable to run macro:", reason, desc)

    def _getMacroResult(self, macro):
        ret = None
        if macro.info.hasResult():
            ret = macro.getResult()

            if ret is None:
                return None

            if macro.info.getResult().type == 'File':

                commit_cmd = macro.info.hints['commit_cmd']

                if commit_cmd is None:
                    return ret

                local_f_name = ret[0]
                remote_f_name = ret[1]
                line_nb = ret[3]
                commit = CommitFile(commit_cmd, local_f_name, remote_f_name)
                self.pending_commits.update({remote_f_name: commit})
                ip = genutils.get_ipapi()
                editor = genutils.get_editor()

                cmd = 'edit -x -n %s %s' % (line_nb, local_f_name)
                if editor not in self.console_editors:
                    cmd = 'bg _ip.magic("' + cmd + '")'
                ip.magic(cmd)
                # The return value of the macro was saved in a file and opened
                # with edit so we don't return anything to avoid big outputs
                # to the console
                ret = None
        return ret

    def plot(self):
        self._plotter.run()

    def show_scan(self, scan_nb=None):
        env = self.getEnvironment()
        scan_history_info = env.get("ScanHistory")
        directory_map = env.get("DirectoryMap")
        self._plotter.show_scan(scan_nb=scan_nb,
                                scan_history_info=scan_history_info,
                                directory_map=directory_map)

    def stateChanged(self, s, t, v):
        old_sw_state = self._old_sw_door_state
        BaseDoor.stateChanged(self, s, t, v)
        new_sw_state = self._old_sw_door_state
        self._updateState(old_sw_state, new_sw_state)

    def _updateState(self, old_sw_state, new_sw_state, silent=False):
        user_ns = genutils.get_ipapi().user_ns
        if new_sw_state == RUNNING_STATE:
            user_ns['DOOR_STATE'] = ""
        else:
            user_ns['DOOR_STATE'] = " (OFFLINE)"

        if not self.isConsoleReady():
            self._spock_state = new_sw_state
            return

        ss = self._spock_state
        if ss is not None and ss != new_sw_state and not silent:
            if ss == RUNNING_STATE:
                self.write_asynch(
                    "\nConnection to door '%s' was lost.\n" % self.getSimpleName())
            elif new_sw_state == RUNNING_STATE:
                self.write_asynch("\nConnection to the door (%s) has "
                                  "been restablished\n" % self.getSimpleName())
        self._spock_state = new_sw_state

    def write_asynch(self, msg):
        self._lines.append(msg)

    def pre_prompt_hook(self, ip):
        self._flush_lines()

    def _flush_lines(self):
        for l in self._lines:
            self.write(l)
        self._lines = []

    def setConsoleReady(self, state):
        self._consoleReady = state

    def isConsoleReady(self):
        return self._consoleReady

    def write(self, msg, stream=None):
        if not self.isConsoleReady():
            return
        return BaseDoor.write(self, msg, stream=stream)

    def processRecordData(self, data):
        if data is None:
            return
        data = data[1]
        if (isinstance(data, dict)
                and 'type' in data
                and data['type'] == 'function'):
            func_name = data['func_name']
            if func_name.startswith("pyplot."):
                try:
                    from taurus.external.qt import Qt
                except ImportError:
                    print("Qt binding is not available. Macro plotting cannot work without it.")
                    return
                func_name = self.MathFrontend + "." + func_name
            args = data['args']
            kwargs = data['kwargs']

            members = func_name.split(".")
            mod_list, fname = members[:-1], members[-1]
            mod_name = ".".join(mod_list)
            if mod_name:
                mod = __import__(mod_name, fromlist=mod_list)
                func = getattr(mod, fname)
            else:
                func = __builtins__[fname]
            try:
                func(*args, **kwargs)
            except Exception as e:
                self.logReceived(
                    self.Warning, ['Unable to execute %s: ' % func_name, str(e)])

    _RECORD_DATA_THRESOLD = 4 * 1024 * 1024  # 4Mb

    def _processInput(self, input_data):
        pyos_inputhook_ptr = ctypes.c_void_p.in_dll(
            ctypes.pythonapi, "PyOS_InputHook")
        old_pyos_inputhook_ptr = pyos_inputhook_ptr.value
        pyos_inputhook_ptr.value = ctypes.c_void_p(None).value
        ret = BaseDoor._processInput(self, input_data)
        pyos_inputhook_ptr.value = old_pyos_inputhook_ptr
        return ret

    def _processRecordData(self, data):
        if data is None:
            return
        value = data.value
        size = len(value[1])
        if size > self._RECORD_DATA_THRESOLD:
            sizekb = size // 1024
            self.logReceived(self.Info, ['Received long data record (%d Kb)' % sizekb,
                                         'It may take some time to process. Please wait...'])
        return BaseDoor._processRecordData(self, data)


class QSpockDoor(SpockBaseDoor):

    def __init__(self, name, **kw):
        self.call__init__(SpockBaseDoor, name, **kw)

        self.recordDataUpdated.connect(self.processRecordData)

    def recordDataReceived(self, s, t, v):
        if genutils.get_pylab_mode() == "inline":
            if t not in CHANGE_EVTS:
                return
            res = BaseDoor.recordDataReceived(self, s, t, v)
            self.processRecordData(res)
        else:
            res = SpockBaseDoor.recordDataReceived(self, s, t, v)
        return res

    def create_input_handler(self):
        from sardana.spock.inputhandler import SpockInputHandler
        from sardana.spock.qtinputhandler import InputHandler

        inputhandler = getattr(sardanacustomsettings, 'SPOCK_INPUT_HANDLER',
                               "CLI")

        if inputhandler == "Qt":
            return InputHandler()
        else:
            return SpockInputHandler()


class SpockDoor(SpockBaseDoor):

    def _processRecordData(self, data):
        data = SpockBaseDoor._processRecordData(self, data)
        return self.processRecordData(data)


class SpockMacroServer(BaseMacroServer):
    """A CLI version of the MacroServer device"""

    def __init__(self, name, **kw):
        self._local_magic = {}
        self._local_var = set()
        self.call__init__(BaseMacroServer, name, **kw)

    def on_elements_changed(self, evt_src, evt_type, evt_value):
        return BaseMacroServer.on_elements_changed(self, evt_src, evt_type,
                                                   evt_value)

    _SKIP_ELEMENTS = 'controller', 'motorgroup', 'instrument', \
        'controllerclass', 'controllerlib', 'macrolib'

    def _addElement(self, element_data):
        element = BaseMacroServer._addElement(self, element_data)
        elem_type = element.type
        if "MacroCode" in element.interfaces:
            self._addMacro(element)
        elif elem_type not in self.NO_CLASS_TYPES:
            # TODO: when it becomes possible to do:
            # some taurus.Device.<attr name> = <value>
            # replace device_proxy with element
            device_proxy = element.getObj().getDeviceProxy()
            genutils.expose_variable(element.name, device_proxy)
        return element

    def _removeElement(self, element_data):
        element = BaseMacroServer._removeElement(self, element_data)
        elem_type = element.type
        if "MacroCode" in element.interfaces:
            self._removeMacro(element)
        elif elem_type not in self.NO_CLASS_TYPES:
            genutils.unexpose_variable(element.name)
        return element

    def _addMacro(self, macro_info):
        macro_name = str(macro_info.name)

        # IPython < 1 magic commands have different API
        if genutils.get_ipython_version_list() < [1, 0]:
            def macro_fn(shell, parameter_s='', name=macro_name):
                door = genutils.get_door()
                ms = genutils.get_macro_server()
                params_def = ms.getMacroInfoObj(name).parameters
                parameters = split_macro_parameters(parameter_s, params_def)
                door.runMacro(macro_name, parameters, synch=True)
                macro = door.getLastRunningMacro()
                if macro is not None:  # maybe none if macro was aborted
                    return macro.getResult()
        else:
            def macro_fn(parameter_s='', name=macro_name):
                door = genutils.get_door()
                ms = genutils.get_macro_server()
                params_def = ms.getMacroInfoObj(name).parameters
                parameters = split_macro_parameters(parameter_s, params_def)
                door.runMacro(macro_name, parameters, synch=True)
                macro = door.getLastRunningMacro()
                if macro is not None:  # maybe none if macro was aborted
                    return macro.getResult()

        macro_fn.__name__ = macro_name
        macro_fn.__doc__ = macro_info.doc + "\nWARNING: do not rely on the" \
                                            " file path below\n"

        # register magic command
        genutils.expose_magic(macro_name, macro_fn)
        self._local_magic[macro_name] = macro_fn

        return macro_info

    def _removeMacro(self, macro_info):
        macro_name = macro_info.name
        genutils.unexpose_magic(macro_name)
        del self._local_magic[macro_name]


def split_macro_parameters(parameters_s, params_def):
    """Split string with macro parameters into a list with macro parameters.
    Whitespaces are the separators between the parameters.

    Repeat parameters are encapsulated in square brackets and its internal
    repetitions, if composed from more than one item are also encapsulated
    in brackets. In this case the output list contains lists internally.

    :param parameters_s: input string containing parameters
    :type parameters_s: string
    :return:  parameters represented as a list (may contain internal lists
    :rtype: list
    """
    parser = ParamParser(params_def)
    return parser.parse(parameters_s)
