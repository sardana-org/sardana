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

"""Expert macros"""



__all__ = ["addctrllib", "addmaclib", "commit_ctrllib", "defctrl", "defelem",
           "defm", "defmeas", "edctrlcls", "edctrllib", "prdef",
           "relctrlcls", "relctrllib", "rellib", "relmac", "relmaclib",
           "send2ctrl", "udefctrl", "udefelem", "udefmeas", "sar_info"]

__docformat__ = 'restructuredtext'

import sys
import traceback
import array

from sardana.macroserver.msexception import UnknownMacroLibrary
from sardana.macroserver.msparameter import WrongParam
from sardana.macroserver.macro import Macro, Type, Table, LibraryError

##########################################################################
#
# Configuration related macros
#
##########################################################################


class defm(Macro):
    """Creates a new motor in the active pool"""

    param_def = [['motor name', Type.String, None, 'motor name'],
                 ['controller', Type.Controller, None, 'Controller name'],
                 ['axis', Type.Integer, None, 'motor axis'], ]

    def run(self, name, controller, axis):
        pool = controller.getPoolObj()
        if axis == -1:
            axis = None
        elem = pool.createElement(name, controller, axis)
        self.print("Created %s" % str(elem))


class defmeas(Macro):
    """Create a new measurement group. First channel in channel_list MUST
    be an internal sardana channel. At least one channel MUST be a
    Counter/Timer (by default, the first Counter/Timer in the list will
    become the master)."""

    param_def = [
        ['name',  Type.String, None, 'Measurement group name'],
        ['channel_list', [['channel', Type.String, None,
                           'Measurement Channel']],
            None, 'List of measurement channels'],
    ]

    def prepare(self, name, channel_list, **opts):

        mntgrp_list = self.findObjs(name, type_class=Type.MeasurementGroup)

        if len(mntgrp_list) != 0:
            raise Exception(
                'A measurement group with that name already exists')

    def run(self, name, channel_list):
        channel0 = self.getObj(channel_list[0])
        pool = channel0.getPoolObj()
        mg = pool.createMeasurementGroup(name, channel_list)
        self.print("Created %s" % str(mg))


class udefmeas(Macro):
    """Deletes existing measurement groups"""

    param_def = [
        ['mntgrps', [['mntgrp', Type.MeasurementGroup, None,
                      'Measurement group name'],
                     {'min': 1}],
         None, 'List of measurement group names'], ]

    def run(self, mntgrps):
        for mntgrp in mntgrps:
            pool = mntgrp.getPoolObj()
            pool.deleteMeasurementGroup(mntgrp.getName())


class defelem(Macro):
    """Creates an element on a controller with an axis"""

    param_def = [['name', Type.String, None, 'new element name'],
                 ['ctrl', Type.Controller, None, 'existing controller'],
                 ['axis', Type.Integer, -1, 'axis in the controller (default is -1, meaning add to the end)'], ]

    def run(self, name, ctrl, axis):
        pool = ctrl.getPoolObj()
        if axis == -1:
            axis = None
        elem = pool.createElement(name, ctrl, axis)
        self.print("Created %s" % str(elem))


class renameelem(Macro):
    """Renames any type of Pool elements apart of Pools."""

    param_def = [['element', Type.PoolElement, None, 'element to be renamed'],
                 ['new_name', Type.String, None, 'new name']]

    def prepare(self, elem, new_name):
        if elem.getType() == "Pool":
            raise WrongParam('Pool elements can not be renamed')

    def run(self, elem, new_name):
        pool = elem.getPoolObj()
        old_name = elem.getName()
        pool.renameElement(old_name, new_name)
        self.print("Renamed %s to %s" % (old_name, new_name))


class udefelem(Macro):
    """Deletes existing elements"""

    param_def = [
        ['elements', [['element', Type.Element, None, 'element name'],
                      {'min': 1}],
         None, 'List of element(s) name'],
    ]

    def run(self, elements):
        for element in elements:
            pool = element.getPoolObj()
            pool.deleteElement(element.getName())


class defctrl(Macro):
    """Creates a new controller
    'role_prop' is a sequence of roles and/or properties.
    - A role is defined as <role name>=<role value> (only applicable to pseudo controllers)
    - A property is defined as <property name> <property value>

    If both roles and properties are supplied, all roles must come before properties.
    All controller properties that don't have default values must be given.

    Example of creating a motor controller (with a host and port properties):

    [1]: defctrl SuperMotorController myctrl host homer.springfield.com port 5000

    Example of creating a Slit pseudo motor (sl2t and sl2b motor roles, Gap and
    Offset pseudo motor roles):

    [1]: defctrl Slit myslit sl2t=mot01 sl2b=mot02 Gap=gap01 Offset=offset01"""

    param_def = [['class',  Type.ControllerClass, None, 'controller class'],
                 ['name',  Type.String, None, 'new controller name'],
                 ['roles_props', [['role_prop', Type.String, None,
                                   'a role or property item'], {'min': 0}],
                  None, 'roles and/or properties']]

    def run(self, ctrl_class, name, props):
        pool = ctrl_class.getPoolObj()
        elem = pool.createController(ctrl_class.name, name, *props)
        self.print("Created %s" % str(elem))


class udefctrl(Macro):
    """Deletes existing controllers"""

    param_def = [
        ['controllers', [['controller', Type.Controller, None,
                          'controller name'], {'min': 1}],
         None, 'List of controller(s) name(s)'], ]

    def run(self, controllers):
        for controller in controllers:
            pool = controller.getPoolObj()
            ctrl_name = controller.getName()
            try:
                pool.deleteController(ctrl_name)
            except Exception:
                msg = "{0} and subsequent controllers (if any) "\
                      "could not be deleted".format(ctrl_name)
                self.error(msg)
                raise


##########################################################################
#
# Controller related macros
#
##########################################################################


class send2ctrl(Macro):
    """Sends the given data directly to the controller"""

    param_def = [['controller', Type.Controller, None, 'Controller name'],
                 ['data', [['string item', Type.String, None,
                            'a string item']],
                  None, 'data to be sent']]

    def run(self, controller, data):
        name = controller.getName()
        pool = controller.getPoolObj()
        str_data = " ".join(data)
        res = pool.SendToController([name, str_data])
        if res:
            self.output(res)

##########################################################################
#
# Library handling related macros
#
##########################################################################


class edctrlcls(Macro):
    """Returns the contents of the library file which contains the given
       controller code."""

    param_def = [
        ['ctrlclass',  Type.ControllerClass, None, 'Controller class name']
    ]

    result_def = [
        ['filedata',  Type.File, None, 'The file data object.']
    ]

    hints = {'commit_cmd': 'commit_ctrllib'}

    def run(self, ctrlclass):
        f_name = ctrlclass.file
        pool = ctrlclass.getPool()
        data = pool.GetFile(f_name)
        data = array.array('B', data).tostring()
        line_nb = 1
        for line in data.splitlines():
            line = line.strip(' \t')
            if line.startswith('class') and line.find(ctrlclass.name) > 0 and \
                    line.endswith(":"):
                break
            line_nb = line_nb + 1
        return [f_name, data, line_nb]


class edctrllib(Macro):
    """Returns the contents of the given library file"""

    param_def = [
        ['filename',  Type.Filename, None, 'Absolute path and file name or '
         'simple filename. Relative paths are not allowed.']
    ]

    result_def = [
        ['filedata',  Type.File, None, 'The file data object']
    ]

    hints = {'commit_cmd': 'commit_ctrllib'}

    def run(self, filename):
        pool = self.getManager().getPool()
        data = pool.GetFile(filename)
        return [filename, array.array('B', data).tostring(), 0]


class commit_ctrllib(Macro):
    """Puts the contents of the given data in a file inside the pool"""

    param_def = [
        ['filename',  Type.Filename, None, 'Absolute path and file name'],
        ['username',  Type.User, None, 'The user name'],
        ['comment',  Type.String, None, 'A description of the changes made to '
         'the file'],
        ['filedata',  Type.File, None, 'The file data object']
    ]

    def run(self, filename, username, comment, filedata):
        pool = self.getManager().getPool()
        meta = filename + '\0' + username + '\0' + comment + '\0'
        data = array.array('B', meta)
        data.extend(array.array('B', filedata))
        pool.PutFile(data.tolist())

##########################################################################
#
# Macro handling related macros
#
##########################################################################


class prdef(Macro):
    """Returns the the macro code for the given macro name."""

    param_def = [
        ['macro_name', Type.MacroCode, None, 'macro name']
    ]

    def run(self, macro_data):
        code_lines, _ = macro_data.code
        for code_line in code_lines:
            self.output(code_line.strip('\n'))


class relctrllib(Macro):
    """Reloads the given controller library code from the pool server
    filesystem.
    """

    param_def = [["ctrl_library", Type.ControllerLibrary, None,
                  "Controller library to reload"]]

    def run(self, ctrl_library):
        pool = ctrl_library.getPoolObj()
        pool.ReloadControllerLib(ctrl_library.name)


class addctrllib(Macro):
    """Adds the given controller library code to the pool server filesystem.

    .. note:: Currently this macro does not report eventual errors,
              for example Python syntax errors, in the controller plugin
              module. So if it silently exits but the controller library is
              not correctly loaded please check the server logs for more
              information.
    """

    param_def = [["ctrl_library_name", Type.String, None,
                  "The module name to be loaded (without extension)"]]

    def run(self, ctrl_library_name):
        # TODO: make it compatible with multiple pools
        pool = self.getPools()[0]
        pool.ReloadControllerLib(ctrl_library_name)


class relctrlcls(Macro):
    """Reloads the given controller class code from the pool server filesystem.
    """

    param_def = [["ctrl_class", Type.ControllerClass, None, "Controller "
                                                            "class to reload"]]

    def run(self, ctrl_class):
        pool = ctrl_class.getPoolObj()
        pool.ReloadControllerClass(ctrl_class.name)


class rellib(Macro):

    """Reloads the given python library code from the macro server filesystem.

    .. warning:: use with extreme care! Accidentally reloading a system
                 module or an installed python module may lead to unpredictable
                 behavior

    .. warning:: Prior to the Sardana version 1.6.0 this macro was successfully
                 reloading python libraries located in the MacroPath.
                 The MacroPath is not a correct place to locate your python
                 libraries. They may be successfully loaded on the MacroServer
                 startup, but this can not be guaranteed.
                 In order to use python libraries within your macro code,
                 locate them in either of valid system PYTHONPATH or
                 MacroServer PythonPath property (of the host where
                 MacroServer runs).
                 In order to achieve the previous behavior, just configure the
                 the same directory in both system PYTHONPATH (or MacroServer's
                 PythonPath) and MacroPath.

    .. note:: if python module is used by any macro, don't forget to reload
              the corresponding macros afterward so the changes take effect."""

    param_def = [
        ['module_name', Type.String, None,
         'The module name to be reloaded (without extension)']
    ]

    def run(self, module_name):
        try:
            self.reloadLibrary(module_name)
            self.output("%s successfully (re)loaded", module_name)
        except LibraryError:
            self.error("Cannot use rellib to reload a macro library. "
                       "Use 'relmaclib' instead")
        except ImportError:
            msg = "".join(traceback.format_exception_only(*sys.exc_info()[:2]))
            self.error(msg)


class relmaclib(Macro):
    """Reloads the given macro library code from the macro server filesystem."""

    param_def = [
        ['macro_library', Type.MacroLibrary, None,
         'The module name to be reloaded (without extension)']
    ]

    def run(self, macro_library):
        name = macro_library.name
        new_macro_library = self.reloadMacroLibrary(name)
        if new_macro_library.has_errors():
            self.warning("%s could not be (re)loaded", name)
            exc_info = new_macro_library.get_error()
            msg = "".join(traceback.format_exception_only(*exc_info[:2]))
            self.error(msg)
            self.warning("The old %s macro library is still available.", name)
        else:
            macros = new_macro_library.get_macros()
            self.output(
                "%s successfully (re)loaded (found %d macros)", name, len(macros))


class addmaclib(Macro):
    """Loads a new macro library.

    .. warning:: Keep in mind that macros from the new library can override
                 macros already present in the system.
    """
    param_def = [
        ['macro_library_name', Type.String, None,
         'The module name to be loaded (without extension)']
    ]

    def prepare(self, macro_library_name):
        try:
            _ = self.getMacroLib(macro_library_name)
        except UnknownMacroLibrary:
            pass
        else:
            raise WrongParam('%s macro library is already loaded' %
                             macro_library_name)

    def run(self, macro_library_name):
        old_macros = self.getMacroNames()
        new_macro_library = self.reloadMacroLibrary(macro_library_name)
        if new_macro_library.has_errors():
            self.warning("%s could not be added", macro_library_name)
            exc_info = new_macro_library.get_error()
            msg = "".join(traceback.format_exception_only(*exc_info[:2]))
            self.error(msg)
        else:
            new_metamacros = new_macro_library.get_macros()
            # retrieving the macro names from the metamacros
            new_macros = [metamacro.name for metamacro in new_metamacros]
            self.output("%s successfully loaded (found %d macros)",
                        macro_library_name, len(new_macros))
            # intersection between old and new indicates the overridden macros
            overridden_macros = list(set(old_macros) & set(new_macros))
            if len(overridden_macros) > 0:
                msg = ('%s macro library has overridden the following ' +
                       'macros: %s') % (macro_library_name, overridden_macros)
                self.warning(msg)


class relmac(Macro):
    """Reloads the given macro code from the macro server filesystem.
    Attention: All macros inside the same file will also be reloaded."""

    param_def = [
        ['macro_code', Type.MacroCode, None, 'macro name to be reloaded']
    ]

    def run(self, macro_code):
        name = macro_code.name
        macro_library_name = macro_code.lib.name
        macro_library = self.reloadMacro(name)
        if macro_library.has_errors():
            self.warning("%s could not be (re)loaded", name)
            exc_info = macro_library.get_error()
            msg = "".join(traceback.format_exception_only(*exc_info[:2]))
            self.error(msg)
            self.warning("The old %s macro is still available.", name)
        else:
            maclibname = macro_library_name
            self.output("%s macro successfully (re)loaded", name)
            macros_in_lib = macro_library.get_macros()
            self.output("\nAll macros from macro library %s have " +
                        "been reloaded:", maclibname)
            self.output([macro.name for macro in macros_in_lib])


class sar_info(Macro):
    """Prints details about the given sardana object"""

    param_def = [
        ['obj', Type.Object, None, 'obj']
    ]

    def run(self, obj):
        self.dump_properties(obj)
        # self.output("")
        # self.dump_attributes(obj)

    def dump_properties(self, obj):
        data = obj.serialize()

        table = Table([list(data.values())], row_head_str=list(data.keys()),
                      row_head_fmt='%*s', col_sep='  =  ')
        self.output("Properties:")
        self.output("-----------")
        for line in table.genOutput():
            self.output(line)

    def dump_attributes(self, obj):
        try:
            dev_attrs = obj.dump_attributes()
        except AttributeError:
            return

        row_head, values = [], []
        for dev_attr in dev_attrs:
            row_head.append(dev_attr.name)
            if dev_attr.has_failed:
                err = dev_attr.get_err_stack()
                if len(err):
                    value = err[0].desc
                else:
                    value = "Unknown error!"
            else:
                value = str(dev_attr.value)
            values.append(value)
        table = Table([values], row_head_str=row_head,
                      row_head_fmt='%*s', col_sep='  =  ')
        self.output("Attributes:")
        self.output("-----------")
        for line in table.genOutput():
            self.output(line)
