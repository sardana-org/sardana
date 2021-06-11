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

"""This module contains the class definition for the MacroServer macro
manager"""

__all__ = ["MacroManager", "MacroExecutor", "is_macro"]

__docformat__ = 'restructuredtext'

import re
import os
import sys
import copy
import inspect
import logging
import functools
import traceback
import threading

from lxml import etree

import time

from PyTango import DevFailed

from collections import OrderedDict

from taurus.core.util.log import Logger
from taurus.core.util.codecs import CodecFactory

from sardana.sardanadefs import ElementType
from sardana.sardanamodulemanager import ModuleManager
from sardana.sardanaexception import format_exception_only_str
from sardana.sardanautils import is_pure_str, is_non_str_seq, recur_map

from sardana.macroserver.msmanager import MacroServerManager
from sardana.macroserver.msmetamacro import MACRO_TEMPLATE, MacroLibrary, \
    MacroClass, MacroFunction
from sardana.macroserver.msparameter import ParamDecoder, FlatParamDecoder, \
    WrongParam
from sardana.macroserver.macro import Macro, MacroFunc, ExecMacroHook, \
    Hookable
from sardana.macroserver.msexception import UnknownMacroLibrary, \
    LibraryError, UnknownMacro, MissingEnv, AbortException, StopException, \
    ReleaseException, MacroServerException, UnknownEnv
from sardana.util.parser import ParamParser
from sardana.util.thread import raise_in_thread

# These classes are imported from the "client" part of sardana, if finally
# both the client and the server side needs them, place them in some
# common location
from sardana.taurus.core.tango.sardana.macro import createMacroNode


_BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def islambda(f):
    """inspect doesn't come with islambda so I create one :-P"""
    return inspect.isfunction(f) and \
        f.__name__ == (lambda: True).__name__


def _is_macro(macro, abs_file=None, logger=None):
    """Helper function to determine if a certain python object is a valid
    macro"""
    if inspect.isclass(macro):
        if not issubclass(macro, Macro):
            return False
        # if it is a class defined in some other module forget it to
        # avoid replicating the same macro in different macro files

        # use normcase to treat case insensitivity of paths on
        # certain platforms e.g. Windows
        if os.path.normcase(inspect.getabsfile(macro)) !=\
           os.path.normcase(abs_file):
            return False

    elif callable(macro) and not islambda(macro):
        # if it is a function defined in some other module forget it to
        # avoid replicating the same macro in different macro files

        # use normcase to treat case insensitivity of paths on
        # certain platforms e.g. Windows
        if os.path.normcase(inspect.getabsfile(macro)) !=\
           os.path.normcase(abs_file):
            return False

        if not hasattr(macro, 'macro_data'):
            return False

        args, varargs, keywords, *_ = inspect.getfullargspec(macro)
        if len(args) == 0:
            if logger:
                logger.debug("Could not add macro %s: Needs at least one "
                             "parameter (usually called 'self')",
                             macro.__name__)
            return False
        if keywords is not None:
            if logger:
                logger.debug("Could not add macro %s: Unsupported keyword "
                             "parameters '%s'", macro.__name__, keywords)
            return False
        if varargs and len(args) > 1:
            if logger:
                logger.debug("Could not add macro %s: Unsupported giving "
                             "named parameters '%s' and varargs '%s'",
                             macro.__name__, args, varargs)
            return False
    else:
        return False
    return True


def is_macro(macro, abs_file=None, logger=None):
    try:
        return _is_macro(macro, abs_file=abs_file, logger=logger)
    except Exception:
        return False


def is_flat_list(obj):
    """Check if a given object is a flat list."""
    if not isinstance(obj, list):
        return False
    for item in obj:
        if isinstance(item, list):
            return False
    return True


class MacroManager(MacroServerManager):

    DEFAULT_MACRO_DIRECTORIES = os.path.join(_BASE_DIR, 'macros'),

    def __init__(self, macro_server, macro_path=None):
        MacroServerManager.__init__(self, macro_server)
        if macro_path is not None:
            self.setMacroPath(macro_path)

    def reInit(self):
        if self.is_initialized():
            return

        # dict<str, MacroLibrary>
        # key   - module name (without path and without extension)
        # value - MacroLibrary object representing the module
        self._modules = {}

        # dict<str, <MacroClass>
        # key   - macro name
        # value - MacroClass object representing the macro
        self._macro_dict = {}

        # list<str>
        # elements are absolute paths
        self._macro_path = []

        # list<str>
        # overwritten macros (macros with the same name defined in
        # different modules)
        self._overwritten_macros = []

        # dict<Door, <MacroExecutor>
        # key   - door
        # value - MacroExecutor object for the door
        self._macro_executors = {}

        MacroServerManager.reInit(self)

    def cleanUp(self):
        if self.is_cleaned():
            return

        # if self._modules:
        #    ModuleManager().unloadModules(self._modules.keys())

        self._macro_path = None
        self._macro_dict = None
        self._modules = None
        self._overwritten_macros = None

        MacroServerManager.cleanUp(self)

    def setMacroPath(self, macro_path):
        """Registers a new list of macro directories in this manager.
        Warning: as a consequence all the macro modules will be reloaded.
        This means that if any reference to an old macro object was kept it will
        refer to an old module (which could possibly generate problems of type
        class A != class A)."""
        p = []
        for item in macro_path:
            p.extend(item.split(os.pathsep))

        # filter empty and commented paths
        p = [i for i in p if i and not i.startswith("#")]

        # add basic macro directories
        for macro_dir in self.DEFAULT_MACRO_DIRECTORIES:
            if macro_dir not in p:
                p.append(macro_dir)

        self._macro_path = p

        macro_file_names = self._findMacroLibNames()
        for mod_name, file_name in macro_file_names.items():
            dir_name = os.path.dirname(file_name)
            path = [dir_name]
            try:
                self.reloadMacroLib(mod_name, path)
            except:
                pass

    def getMacroPath(self):
        return self._macro_path

    def _findMacroLibName(self, lib_name, path=None):
        path = path or self.getMacroPath()
        f_name = lib_name
        if not f_name.endswith('.py'):
            f_name += '.py'
        for p in path:
            try:
                elems = os.listdir(p)
                if f_name in elems:
                    return os.path.abspath(os.path.join(p, f_name))
            except:
                self.debug("'%s' is not a valid path" % p)
        return None

    def _findMacroLibNames(self, path=None):
        path = path or self.getMacroPath()
        ret = OrderedDict()
        for p in reversed(path):
            try:
                for f in os.listdir(p):
                    name, ext = os.path.splitext(f)
                    if name.startswith("_"):
                        continue
                    if ext.endswith('py'):
                        ret[name] = os.path.abspath(os.path.join(p, f))
            except:
                self.debug("'%s' is not a valid path" % p)
        return ret

    def _fromNameToFileName(self, lib_name, path=None):
        path = path or self.getMacroPath()[0]
        f_name = lib_name
        if not f_name.endswith('.py'):
            f_name += '.py'

        if os.path.isabs(f_name):
            path, _ = os.path.split(f_name)
            if not path in self.getMacroPath():
                raise Exception("'%s' is not part of the MacroPath" % path)
        else:
            f_name = os.path.join(path, f_name)
        return f_name

    def getOrCreateMacroLib(self, lib_name, macro_name=None):
        """Gets the exiting macro lib or creates a new macro lib file. If
        name is not None, a macro template code for the given macro name is
        appended to the end of the file.

        :param lib_name:
            module name, python file name, or full file name (with path)
        :type lib_name: :obj:`str`
        :param macro_name:
            an optional macro name. If given a macro template code is appended
            to the end of the file (default is None meaning no macro code is
            added)
        :type macro_name: :obj:`str`

        :return:
            a sequence with three items: full_filename, code, line number is 0
            if no macro is created or n representing the first line of code for
            the given macro name.
        :rtype: seq<str, str, int>"""
        # if only given the module name
        try:
            macro_lib = self.getMacroLib(lib_name)
        except UnknownMacroLibrary:
            macro_lib = None

        if macro_name is None:
            line_nb = 0
            if macro_lib is None:
                f_name, code = self.createMacroLib(lib_name), ''
            else:
                f_name = macro_lib.file_path
                f = open(f_name)
                code = f.read()
                f.close()
        else:
            # if given macro name
            if macro_lib is None:
                f_name, code, line_nb = self.createMacro(lib_name, macro_name)
            else:
                macro = macro_lib.get_macro(macro_name)
                if macro is None:
                    f_name, code, line_nb = self.createMacro(
                        lib_name, macro_name)
                else:
                    _, line_nb = macro.code
                    f_name = macro.file_path
                    f = open(f_name)
                    code = f.read()
                    f.close()

        return [f_name, code, line_nb]

    def setMacroLib(self, lib_name, code, auto_reload=True):
        f_name = self._fromNameToFileName(lib_name)
        f = open(f_name, 'w')
        f.write(code)
        f.flush()
        f.close()
        _, name = os.path.split(f_name)
        mod, _ = os.path.splitext(name)
        if auto_reload:
            self.reloadMacroLib(mod)
        return mod

    def createMacroLib(self, lib_name, path=None):
        """Creates a new empty macro library (python module)"""
        f_name = self._fromNameToFileName(lib_name, path)

        if os.path.exists(f_name):
            raise Exception(
                "Unable to create macro lib: '%s' already exists" % f_name)

        f = open(f_name, 'w')
        f.close()
        return f_name

    def createMacro(self, lib_name, macro_name):
        f_name = self._fromNameToFileName(lib_name)

        create = not os.path.exists(f_name)

        template = ''
        if create:
            template += 'from sardana.macroserver.macro import Macro, macro, Type\n\n'
            line_nb = 4
        else:
            template += '\n'
            t = open(f_name, 'rU')
            line_nb = -1
            for line_nb, _ in enumerate(t):
                pass
            line_nb += 3
            t.close()

        f = open(f_name, 'a+')
        f_templ = None
        try:
            dir_name = os.path.realpath(__file__)
            dir_name = os.path.dirname(dir_name)
            template_fname = 'macro_template.txt'
            template_fname = os.path.join(dir_name, template_fname)
            f_templ = open(template_fname, 'r')
            template += f_templ.read()
            f_templ.close()
        except:
            self.debug(
                "Failed to open template macro file. Using simplified template")
            template += MACRO_TEMPLATE
            if f_templ:
                f_templ.close()

        template = template.replace('@macro_name@', macro_name)
        try:
            f.write(template)
            f.flush()
            f.seek(0)
            code = f.read()
        finally:
            f.close()
        return f_name, code, line_nb

    def reloadMacro(self, macro_name, path=None):
        """Reloads the module corresponding to the given macro name

        :raises: MacroServerExceptionList in case the macro is unknown or the
        reload process is not successful

        :param macro_name: macro name
        :param path: a list of absolute path to search for libraries
                     (optional, default=None, means the current MacroPath
                     will be used)"""
        self.reloadMacros([macro_name], path=path)

    def reloadMacros(self, macro_names, path=None):
        """Reloads the modules corresponding to the given macro names

        :raises: MacroServerExceptionList in case the macro(s) are unknown or the
        reload process is not successful

        :param macro_names: a list of macro names
        :param path: a list of absolute path to search for libraries (optional,
                     default=None, means the current MacroPath will be used)"""
        module_names = []
        for macro_name in macro_names:
            module_name = self.getMacro(macro_name).module_name
            module_names.append(module_name)
        self.reloadMacroLibs(module_names, path=path)

    def reloadMacroLibs(self, module_names, path=None):
        """Reloads the given lib(=module) names

        :raises: MacroServerExceptionList in case the reload process is not
        successful for at least one library

        :param module_names: a list of module names
        :param path: a list of absolute path to search for libraries
                     (optional, default=None, means the current MacroPath
                     will be used)"""
        ret = []
        for module_name in module_names:
            m = self.reloadMacroLib(module_name, path=path)
            if m:
                ret.append(m)
        return ret

    def reloadLib(self, module_name, path=None):
        """Reloads the given library(=module) names.

        :raises:
            LibraryError if trying to reload a macro library

        :param module_name: module name
        :param path:
            a list of absolute path to search for libraries [default: None.
            Search in sys.path.]
        :return: the reloaded python module object"""
        if module_name in self._modules:
            raise LibraryError("Cannot use simple " +
                               "reload to reload a Macro Library")

        mod_manager = ModuleManager()
        return mod_manager.reloadModule(module_name, path=None)

    def reloadMacroLib(self, module_name, path=None):
        """Reloads the given library(=module) names.

        :raises:
            LibraryError in case the reload process is not successful

        :param module_name: macro library name (=python module name)
        :param path:
            a list of absolute path to search for libraries [default: None,
            means the current MacroPath will be used]
        :return: the MacroLibrary object for the reloaded macro library"""
        path = path or self.getMacroPath()
        mod_manager = ModuleManager()
        m, exc_info = None, None
        valid, exc_info = mod_manager.isValidModule(module_name, path)
        if not valid:
            params = dict(module=m, name=module_name,
                          macro_server=self.macro_server, exc_info=exc_info)
            return MacroLibrary(**params)

        # if there was previous Macro Library info remove it
        old_macro_lib = self._modules.pop(module_name, None)
        if old_macro_lib is not None:
            for macro in old_macro_lib.get_macros():
                self._macro_dict.pop(macro.name)

        try:
            m = mod_manager.reloadModule(module_name, path)
        except:
            exc_info = sys.exc_info()
        macro_lib = None

        params = dict(module=m, name=module_name,
                      macro_server=self.macro_server, exc_info=exc_info)

        # Dictionary for gathering macros with errors
        macro_errors = {}
        count_correct_macros = 0
        count_incorrect_macros = 0

        if m is None:
            file_name = self._findMacroLibName(module_name)
            if file_name is None:
                if exc_info:
                    msg = format_exception_only_str(*exc_info[:2])
                else:
                    msg = "Error (re)loading macro library '%s'" % module_name
                raise LibraryError(msg, exc_info=exc_info)
            params['file_path'] = file_name
            macro_lib = MacroLibrary(**params)
        else:
            macro_lib = MacroLibrary(**params)
            abs_file = macro_lib.file_path
            _is_macro = functools.partial(is_macro, abs_file=abs_file,
                                          logger=self)
            for _, macro in inspect.getmembers(m, _is_macro):
                try:
                    isoverwritten = False
                    macro_name = macro.__name__
                    if macro_name in self._overwritten_macros:
                        isoverwritten = True
                    elif (macro_name in list(self._macro_dict.keys())
                            and self._macro_dict[macro_name].lib != macro_lib):
                        isoverwritten = True
                        msg = ('Macro "{0}" defined in "{1}" macro library'
                               + ' has been overwritten by "{2}" macro library'
                               )
                        old_lib_name = self._macro_dict[macro_name].lib.name
                        self.debug(msg.format(macro_name, old_lib_name,
                                              macro_lib.name))
                        self._overwritten_macros.append(macro_name)

                    self.addMacro(macro_lib, macro, isoverwritten)
                    count_correct_macros += 1
                except Exception as e:
                    count_incorrect_macros += 1
                    self.error("Error adding macro %s", macro.__name__)
                    self.debug("Details:", exc_info=1)
                    macro_errors[macro.__name__] = str(e)
        try:
            if macro_lib.has_macros():
                self._modules[module_name] = macro_lib
            return macro_lib
        finally:
            if macro_errors:
                msg = ""
                for key, value in macro_errors.items():
                    msg_part = ("\n" + "Error adding macro(s): " + key + "\n"
                                + "It presents an error: \n" + str(value))
                    msg += str(msg_part) + "\n"
                correct_macros = ("%d macro(s) correctly loaded" %
                                  count_correct_macros)
                incorrect_macros = ("%d macro(s) could not be loaded" %
                                    count_incorrect_macros)

                msg = (msg + "\n" + "Summary:" + "\n" + correct_macros
                       + "\n" + incorrect_macros + "\n")

                if count_correct_macros == 0:
                    msg += "\nUse addmaclib to reload the corrected macro(s)\n"
                if count_correct_macros != 0:
                    msg += "\nUse relmaclib to reload the corrected macro(s)\n"
                raise Exception(msg)

    def addMacro(self, macro_lib, macro, isoverwritten=False):
        add = self.addMacroFunction
        if inspect.isclass(macro):
            add = self.addMacroClass
        return add(macro_lib, macro, isoverwritten)

    def addMacroClass(self, macro_lib, klass, isoverwritten=False):
        macro_name = klass.__name__
        action = (macro_lib.has_macro(macro_name) and "Updating") or "Adding"
        self.debug("%s macro class %s" % (action, macro_name))

        params = dict(macro_server=self.macro_server, lib=macro_lib,
                      klass=klass, isoverwritten=isoverwritten)
        macro_class = MacroClass(**params)
        macro_lib.add_macro_class(macro_class)
        self._macro_dict[macro_name] = macro_class

    def addMacroFunction(self, macro_lib, func, isoverwritten=False):
        macro_name = func.__name__
        action = (macro_lib.has_macro(macro_name) and "Updating") or "Adding"
        self.debug("%s macro function %s" % (action, macro_name))

        params = dict(macro_server=self.macro_server, lib=macro_lib,
                      function=func, isoverwritten=isoverwritten)
        macro_function = MacroFunction(**params)
        macro_lib.add_macro_function(macro_function)
        self._macro_dict[macro_name] = macro_function

    def getMacroLibNames(self):
        return sorted(self._modules.keys())

    def getMacroLibs(self, filter=None):
        if filter is None:
            return self._modules
        expr = re.compile(filter, re.IGNORECASE)
        ret = {}
        for name, macro_lib in self._modules.items():
            if expr.match(name) is None:
                continue
            ret[name] = macro_lib
        return ret

    def getMacros(self, filter=None):
        """Returns a :obj:`dict` containing information about macros.

        :param filter:
            a regular expression for macro names [default: None, meaning all
            macros]
        :type filter: :obj:`str`
        :return: a :obj:`dict` containing information about macros
        :rtype:
            :obj:`dict`\<:obj:`str`\, :class:`~sardana.macroserver.msmetamacro.MacroCode`\>"""
        if filter is None:
            return self._macro_dict
        expr = re.compile(filter, re.IGNORECASE)

        ret = {}
        for name, macro in self._macro_dict.items():
            if expr.match(name) is None:
                continue
            ret[name] = macro
        return ret

    def getMacroClasses(self, filter=None):
        """Returns a :obj:`dict` containing information about macro classes.

        :param filter:
            a regular expression for macro names [default: None, meaning all
            macros]
        :type filter: :obj:`str`
        :return: a :obj:`dict` containing information about macro classes
        :rtype:
            :obj:`dict`\<:obj:`str`\, :class:`~sardana.macroserver.msmetamacro.MacroClass`\>"""
        macros = self.getMacros(filter=filter)
        macro_classes = {}
        for name, macro in list(macros.items()):
            if macro.get_type() == ElementType.MacroClass:
                macro_classes[name] = macro
        return macro_classes

    def getMacroFunctions(self, filter=None):
        """Returns a :obj:`dict` containing information about macro functions.

        :param filter:
            a regular expression for macro names [default: None, meaning all
            macros]
        :type filter: :obj:`str`
        :return: a :obj:`dict` containing information about macro functions
        :rtype:
            :obj:`dict`\<:obj:`str`\, :class:`~sardana.macroserver.msmetamacro.MacroFunction`\>"""
        macros = self.getMacros(filter=filter)
        macro_classes = {}
        for name, macro in list(macros.items()):
            if macro.get_type() == ElementType.MacroFunction:
                macro_classes[name] = macro
        return macro_classes

    def getMacroNames(self):
        return sorted(self._macro_dict.keys())

    def getMacro(self, macro_name):
        ret = self._macro_dict.get(macro_name)
        if ret is None:
            raise UnknownMacro("Unknown macro %s" % macro_name)
        return ret

    def getMacroClass(self, macro_name):
        return self.getMacro(macro_name)

    def getMacroFunction(self, macro_name):
        return self.getMacro(macro_name)

    def removeMacro(self, macro_name):
        self._macro_dict.pop(macro_name)

    def getMacroLib(self, name):
        if os.path.isabs(name):
            abs_file_name = name
            for lib in list(self._modules.values()):
                if lib.file_path == abs_file_name:
                    return lib
        elif name.count(os.path.extsep):
            file_name = name
            for lib in list(self._modules.values()):
                if lib.file_name == file_name:
                    return lib
        module_name = name
        ret = self._modules.get(module_name)
        if ret is None:
            raise UnknownMacroLibrary("Unknown macro library %s" % module_name)
        return ret

    def getMacroCode(self, macro_name):
        return self.getMacro(macro_name).code_object

    def getMacroClassCode(self, macro_name):
        return self.getMacroClass(macro_name).klass

    def getMacroFunctionCode(self, macro_name):
        return self.getMacroFunction(macro_name).function

    def getMacroInfo(self, macro_names, format='json'):
        if isinstance(macro_names, str):
            macro_names = [macro_names]
        ret = []
        json_codec = CodecFactory().getCodec(format)
        for macro_name in macro_names:
            macro_meta = self.getMacro(macro_name)
            ret.append(json_codec.encode(('', macro_meta.serialize()))[1])
        return ret

    def _createMacroNode(self, macro_name, macro_params_raw):
        macro = self.getMacro(macro_name)
        params_def = macro.get_parameter()
        macro_params_str = " ".join(macro_params_raw)
        param_parser = ParamParser(params_def)
        # parse string with macro params to the correct list representation
        macro_params = param_parser.parse(macro_params_str)
        return createMacroNode(macro_name, params_def, macro_params)

    def decodeMacroParameters(self, door, raw_params):
        """Decode macro parameters

        :param door: (sardana.macroserver.msdoor.MSDoor) door object
        :param raw_params: (lxml.etree._Element or list) xml element
            representing macro with subelements representing parameters or
            list with macro name followed by parameter values
        """
        if isinstance(raw_params, etree._Element):
            macro_name = raw_params.get("name")
        elif isinstance(raw_params, list):
            # leave only macro parameters in the list
            macro_name = raw_params.pop(0)
        else:
            raise Exception("Wrong format of raw_params object")
        macro_meta = self.getMacro(macro_name)
        params_def = macro_meta.get_parameter()
        type_manager = door.type_manager
        try:
            out_par_list = ParamDecoder(type_manager, params_def, raw_params)
        except WrongParam as out_e:
            # only if raw params are passed as a list e.g. using macro API
            # execMacro("mv", mot01, 0.0) and parameters definition allows to
            # decode it from a flat list we give it a try
            if (is_flat_list(raw_params) and
                    FlatParamDecoder.isPossible(params_def)):
                self.debug("Trying flat parameter decoder due to: %s" % out_e)
                try:
                    out_par_list = FlatParamDecoder(type_manager, params_def,
                                                    raw_params)
                except WrongParam as in_e:
                    msg = ("Either of: %s or %s made it impossible to decode"
                           " parameters" % (out_e, in_e))
                    raise WrongParam(msg)
            else:
                raise out_e
        return macro_meta, raw_params, out_par_list

    def strMacroParamValues(self, par_list):
        """strMacroParamValues(list<string> par_list) -> list<string>

           Creates a short string representantion of the parameter values list.
           Params:
               - par_list: list of strings representing the parameter values.
           Return:
               a list containning an abreviated version of the par_list argument.
        """
        ret = []
        for p in par_list:
            param_str = str(p)
            if len(param_str) > 9:
                param_str = param_str[:9] + "..."
            ret.append(param_str)
        return ret

    def prepareMacro(self, macro_class, par_list,
                     init_opts={}, prepare_opts={}):
        """Creates the macro object and calls its prepare method.
           The return value is a tuple (MacroObject, return value of prepare)
        """
        macro = self.createMacroObj(macro_class, par_list, init_opts=init_opts)
        prepare_result = self.prepareMacroObj(
            macro, par_list, prepare_opts=prepare_opts)
        return macro, prepare_result

    def createMacroObj(self, macro_class, par_list, init_opts={}):
        macro_env = macro_class.env
        macro_name = macro_class.__name__

        environment = init_opts.get('environment')
        executor = init_opts.get('executor')
        door_name = executor.door.name

        r = []
        for env in macro_env:
            if not environment.has_env(env,
                                       macro_name=macro_name,
                                       door_name=door_name):
                r.append(env)
        if r:
            raise MissingEnv("The macro %s requires the following missing "
                             "environment to be defined: %s"
                             % (macro_name, str(r)))

        macro_opts = {
            'no_exec': True,
            'create_thread': True,
            'external_prepare': True
        }

        macro_opts.update(init_opts)
        macroObj = macro_class(*par_list, **macro_opts)
        return macroObj

    def prepareMacroObj(self, macro, par_list, prepare_opts={}):
        return macro.prepare(*par_list, **prepare_opts)

    def createMacroObjFromMeta(self, meta, par_list, init_opts={}):
        code = meta.code_object
        macro_env = code.env or ()

        environment = init_opts.get('environment')
        executor = init_opts.get('executor')
        door_name = executor.door.name
        macro_name = meta.name
        r = []
        for env in macro_env:
            if not environment.has_env(env,
                                       macro_name=macro_name,
                                       door_name=door_name):
                r.append(env)
        if r:
            raise MissingEnv("The macro %s requires the following missing "
                             "environment to be defined: %s"
                             % (macro_name, str(r)))

        macro_opts = dict(no_exec=True, create_thread=True,
                          external_prepare=True)

        macro_opts.update(init_opts)
        if meta.get_type() == ElementType.MacroClass:
            macroObj = meta.macro_class(*par_list, **macro_opts)
        else:
            macro_opts['function'] = code
            macroObj = MacroFunc(*par_list, **macro_opts)
        return macroObj

    def getMacroExecutor(self, door):
        me = self._macro_executors.get(door)
        if me is None:
            self._macro_executors[door] = me = MacroExecutor(door)
        return me


class LogMacroFilter(logging.Filter):

    def __init__(self, param=None):
        self.param = param

    def filter(self, record):
        allow = True
        if record.levelname == "DEBUG":
            if not isinstance(record.msg, str):
                allow = False
                return allow
            if record.msg.find("[START]") != -1:
                msg = record.msg
                start = msg.index("'") + 1
                end = msg.index("->", start)
                msg = msg[start:end]
                msg = msg.replace("(", " ").replace(")", "").replace(
                    "[", "").replace("]", "")
                msg = msg.replace(", ", " ")
                msg = msg.replace(",", " ")
                msg = msg.replace(".*", "")
                while msg.find("  ") != -1:
                    msg = msg.replace("  ", " ")
                if msg[0] == "_":
                    allow = False
                else:
                    msg_split = msg.split(" ")
                    msg = ""
                    for i in range(0, len(msg_split)):
                        if msg_split[i].find(" ") == -1:
                            msg_split[i] = msg_split[i].replace("'", " ")
                        msg = msg + " " + str(msg_split[i])
                    while msg.find("  ") != -1:
                        msg = msg.replace("  ", " ")
                    record.msg = "\n-- " + time.ctime() + "\n" + msg
                    allow = True
            else:
                allow = False
        return allow


class LogMacroManager(Logger):

    """Manage user-oriented macro logging to a file. It is configurable with
    LogMacro, LogMacroMode, LogMacroFormat and LogMacroDir environment
    variables.

    .. note::
        The LogMacroManager class has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including its removal) may occur if
        deemed necessary by the core developers.
    """

    DEFAULT_DIR = os.path.join(os.sep, "tmp")
    DEFAULT_FMT = "%(message)s"
    DEFAULT_MODE = 0

    def __init__(self, macro_obj):
        name = macro_obj.getName() + ".LogMacroManager"
        Logger.__init__(self, name)
        self._macro_obj = macro_obj
        self._file_handler = None
        self._enabled = False

    def getFilterClass(self):
        """Get filter class.

        First look if a custom filter class was set using
        sardanacustomsettings.LOG_MACRO_FILTER variable, if not, silently
        return None (no filter will be applied).

        If the custom filter class was incorrectly set or class is not
        importable warn the user and return None (no filter will be applied).
        """
        filter_class = None
        from sardana import sardanacustomsettings
        try:
            log_macro_filter = getattr(sardanacustomsettings,
                                       "LOG_MACRO_FILTER")
        except AttributeError:
            pass
        else:
            if isinstance(log_macro_filter, str):
                try:
                    module_name, filter_name = log_macro_filter.rsplit('.', 1)
                    __import__(module_name)
                    module = sys.modules[module_name]
                    filter_class = getattr(module, filter_name)
                except Exception:
                    msg = "sardanacustomsettings.LOG_MACRO_FILTER has wrong" \
                          " format or class is not importable." \
                          " No filter will be used."
                    self.warning(msg)
                    self.debug(exc_info=True)
        return filter_class

    def enable(self):
        """Enable macro logging only if the following requirements are
        fulfilled:
            * this is the top-most macro
            * macro logging is enabled by user

        :return: True or False, depending if logging was enabled or not
        :rtype: boolean
        """
        macro_obj = self._macro_obj
        executor = macro_obj.executor
        door = macro_obj.door

        # enable logging only for the top-most macros
        if macro_obj.getParentMacro() is not None:
            return False
        # enable logging only if configured by user
        try:
            enabled = macro_obj.getEnv("LogMacro")
        except UnknownEnv:
            return False
        if not enabled:
            return False

        try:
            logging_mode = macro_obj.getEnv("LogMacroMode")
        except UnknownEnv:
            logging_mode = self.DEFAULT_MODE
        try:
            logging_path = macro_obj.getEnv("LogMacroDir")
        except UnknownEnv:
            logging_path = self.DEFAULT_DIR
            macro_obj.setEnv("LogMacroDir", logging_path)

        door_name = door.name
        # Cleaning name in case alias does not exist
        door_name = door_name.replace(":", "_").replace("/", "_")
        file_name = "session_" + door_name + ".log"
        log_file = os.path.join(logging_path, file_name)

        if logging_mode:
            bck_counts = 100
        else:
            bck_counts = 0

        self._file_handler = file_handler = \
            logging.handlers.RotatingFileHandler(log_file,
                                                 backupCount=bck_counts)
        file_handler.doRollover()

        filter_class = self.getFilterClass()
        if filter_class is not None:
            try:
                filter_ = filter_class()
            except Exception:
                msg = "Not possible to instantiate %s class. No filter will" \
                      " be used." % filter_class
                self.warning(msg)
                self.debug(exc_info=True)
            else:
                file_handler.addFilter(filter_)

        try:
            format_to_set = macro_obj.getEnv("LogMacroFormat")
        except UnknownEnv:
            format_to_set = self.DEFAULT_FMT
        log_format = logging.Formatter(format_to_set)
        file_handler.setFormatter(log_format)
        # attach the same handler to two different loggers due to
        # lack of hierarchy between them (see: sardana-org/sardana#703)
        macro_obj.addLogHandler(file_handler)
        executor.addLogHandler(file_handler)
        self._enabled = True
        return True

    def disable(self):
        """Disable macro logging only if it was enabled before.

        :return: True or False, depending if logging was disabled or not
        :rtype: boolean
        """

        if not self._enabled:
            return False
        macro_obj = self._macro_obj
        executor = macro_obj.executor
        file_handler = self._file_handler
        macro_obj.removeLogHandler(file_handler)
        executor.removeLogHandler(file_handler)

        return True


class MacroExecutor(Logger):

    """ """

    class RunSubXMLHook:

        def __init__(self, me, xml):
            self._me = me
            self._xml = xml

        def __call__(self):
            self._me._runXMLMacro(xml=self._xml)

    def __init__(self, door):
        self._door = door
        self._macro_counter = 0

        # dict<PoolElement, set<Macro>>
        # key PoolElement - reserved object
        # value set<Macro> macros that reserved the object
        self._reserved_objs = {}

        # dict<Macro, seq<PoolElement>>
        # key Macro - macro object
        # value - sequence of reserverd objects by the macro
        self._reserved_macro_objs = {}
        # dict<Macro, seq<PoolElement>>
        # key Macro - macro object
        # value - sequence of reserverd objects by the macro
        #   which were already successfully stopped
        self._stopped_macro_objs = {}

        # reset the stacks
#        self._macro_stack = None
#        self._xml_stack = None
        self._macro_stack = []
        self._xml_stack = []
        self._last_macro = None
        self._abort_thread = None
        self._aborted = False
        self._stop_thread = None
        self._stopped = False
        self._paused = False
        self._released = False
        self._last_macro_status = None
        # threading events for synchronization of stopping/abortting of
        # reserved objects
        self._stop_done = None
        self._abort_done = None

        name = "%s.%s" % (str(door), self.__class__.__name__)
        self._macro_status_codec = CodecFactory().getCodec('json')
        self.call__init__(Logger, name)

    def getDoor(self):
        return self._door

    door = property(getDoor)

    def getMacroServer(self):
        return self.door.macro_server

    macro_server = property(getMacroServer)

    @property
    def macro_manager(self):
        return self.macro_server.macro_manager

    @property
    def macro_pointer(self):
        macro_stack = self._macro_stack
        if not macro_stack:
            return None
        return macro_stack[-1]

    def getGeneralHooks(self):
        """Get data structure containing definition of the general hooks.

        .. note::
        The `general_hooks` has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including its removal) may occur if
        deemed necessary by the core developers.

        .. todo::
        General hooks should reflect the state of configuration at the
        macro/sequence start.
        """

        try:
            return self.door.get_env("_GeneralHooks")["_GeneralHooks"]
        except KeyError:
            return []

    general_hooks = property(getGeneralHooks)

    def getNewMacroID(self):
        self._macro_counter -= 1
        return self._macro_counter

    def _createMacroNode(self, macro_name, macro_params):
        return self.macro_manager._createMacroNode(macro_name, macro_params)

    def _preprocessParameters(self, par_str_list):
        if not par_str_list[0].lstrip().startswith('<'):
            xml_root = xml_seq = etree.Element('sequence')
            macro_name = par_str_list[0]
            macro_params = par_str_list[1:]

            def quote_string(string):
                # if string contains double quotes, use single quotes,
                # otherwise use double quotes
                if re.search('"', string):
                    return "'{}'".format(string)
                else:
                    return '"{}"'.format(string)

            # param parser relies on whitespace separation of parameter values
            # quote string parameter values containing whitespaces
            macro_params_quoted = []
            for param in macro_params:
                if (not re.match(r".*\s+.*", param)  # no white spaces
                        or re.match(r"^'.*\s+.*'$", param)  # already quoted
                        or re.match(r'^".*\s+.*"$', param)):  # already quoted
                    macro_params_quoted.append(param)
                else:
                    macro_params_quoted.append(quote_string(param))
            macro_node = self._createMacroNode(macro_name, macro_params_quoted)
            xml_macro = macro_node.toXml()
            xml_seq.append(xml_macro)
        else:
            xml_root = etree.fromstring(par_str_list[0])

        macro_nodes = xml_root.findall('.//macro')

        # make sure macros exist
        self.__checkXMLSequence(macro_nodes)

        # fill the xml with macro id macro_line
        self.__fillXMLSequence(macro_nodes)

        return xml_root

    def __checkXMLSequence(self, macros):
        for macro in macros:
            name = macro.get('name')
            self.macro_manager.getMacro(name)

    def __fillXMLSequence(self, macros):
        for macro in macros:
            eid = macro.get('id')
            if eid is None:
                eid = str(self.getNewMacroID())
                macro.set('id', eid)

    def __preprocessResult(self, result):
        """decodes the given output from a macro in order to be able to send to
        the result channel as a sequence<str>

        :param out: output value

        :return: the output as a sequence of strings
        """
        if result is None:
            return ()
        if is_non_str_seq(result):
            result = list(map(str, result))
        else:
            result = (str(result),)
        return result

    def _decodeMacroParameters(self, params):
        return self.macro_manager.decodeMacroParameters(self.door, params)

    def _composeMacroLine(self, macro_name, macro_params, macro_id):
        # recursive map to maintain the list objects structure
        params_str_list = recur_map(str, macro_params)
        # plain map to be able to perform join (only strings may be joined)
        params_str_list = list(map(str, params_str_list))
        params_str = ', '.join(params_str_list)
        macro_id = macro_id
        # create macro_line - string representation of macro, its parameters
        # and id
        macro_line = "%s(%s) -> %s" % (macro_name, params_str, macro_id)
        return macro_line

    def _prepareGeneralHooks(self, macro_obj):
        if not isinstance(macro_obj, Hookable):
            return
        general_hooks = self.general_hooks
        if len(general_hooks) == 0:
            return
        for hook_info_raw, hook_places in general_hooks:
            hook_info_tokens = hook_info_raw.split(" ", 1)
            hook_name = hook_info_tokens[0]
            hook_info = [hook_name]
            if len(hook_info_tokens) == 2:
                hook_params_raw = hook_info_tokens[1]
                hook_param_def = self.macro_manager.getMacro(
                    hook_name).get_parameter()
                param_parser = ParamParser(hook_param_def)
                hook_params = param_parser.parse(hook_params_raw)
                hook_info += hook_params
            hook = ExecMacroHook(macro_obj, hook_info)
            macro_obj.appendHook((hook, hook_places))

    def _prepareXMLMacro(self, xml_macro, parent_macro=None):
        macro_meta, _, macro_params = self._decodeMacroParameters(xml_macro)
        macro_name = macro_meta.name
        macro_id = xml_macro.get("id")
        macro_line = self._composeMacroLine(macro_name, macro_params, macro_id)
        init_opts = {
            'id': macro_id,
            'macro_line': macro_line,
            'parent_macro': parent_macro,
        }

        macro_obj = self._createMacroObj(macro_meta, macro_params, init_opts)

        self._prepareGeneralHooks(macro_obj)

        for macro in xml_macro.findall('macro'):
            hook = MacroExecutor.RunSubXMLHook(self, macro)
            hook_hints = macro.findall('hookPlace')
            if hook_hints is None:
                macro_obj.appendHook((hook, []))
            else:
                hook_places = [h.text for h in hook_hints]
                macro_obj.appendHook((hook, hook_places))

        prepare_result = self._prepareMacroObj(macro_obj, macro_params)
        return macro_obj, prepare_result

    def _createMacroObj(self, macro_name_or_meta, pars, init_opts={}):
        macro_meta = macro_name_or_meta
        if isinstance(macro_meta, str):
            macro_meta = self.macro_manager.getMacro(macro_meta)

        macro_opts = {
            'executor': self,
            'environment': self.macro_server
        }
        macro_opts.update(init_opts)
        if 'id' not in macro_opts:
            macro_opts['id'] = str(self.getNewMacroID())

        macroObj = self.macro_manager.createMacroObjFromMeta(macro_meta, pars,
                                                             init_opts=macro_opts)

        return macroObj

    def _prepareMacroObj(self, macro_obj, pars, prepare_opts={}):
        return self.macro_manager.prepareMacroObj(macro_obj, pars,
                                                  prepare_opts=prepare_opts)

    def prepareMacroObj(self, macro_name_or_meta, pars, init_opts={},
                        prepare_opts={}):
        """Prepare a new macro for execution

        :param macro_name_or_meta name: name of the macro to be prepared or
                                        the macro meta itself
        :param pars: list of parameter objects
        :param init_opts: keyword parameters for the macro constructor
        :param prepare_opts: keyword parameters for the macro prepare

        :return: a tuple of two elements: macro object, the result of preparing the macro"""
        macroObj = self._createMacroObj(
            macro_name_or_meta, pars, init_opts=init_opts)
        prepare_result = self._prepareMacroObj(
            macroObj, pars, prepare_opts=prepare_opts)
        return macroObj, prepare_result

    def prepareMacro(self, pars, init_opts={}, prepare_opts={}):
        """Prepare a new macro for execution
           Several different parameter formats are supported:
           1. several parameters:
             1.1 executor.prepareMacro('ascan', 'th', '0', '100', '10', '1.0')
                 executor.prepareMacro('mv', [['th', '0']])
                 executor.prepareMacro('mv', 'th', '0') # backwards compatibility - see note
             1.2 executor.prepareMacro('ascan', 'th', 0, 100, 10, 1.0)
                 executor.prepareMacro('mv', [['th', 0]])
                 executor.prepareMacro('mv', 'th', 0) # backwards compatibility - see note
             1.3 th = self.getObj('th');
                 executor.prepareMacro('ascan', th, 0, 100, 10, 1.0)
                 executor.prepareMacro('mv', [[th, 0]])
                 executor.prepareMacro('mv', th, 0) # backwards compatibility - see note
           2. a sequence of parameters:
              2.1 executor.prepareMacro(['ascan', 'th', '0', '100', '10', '1.0')
                  executor.prepareMacro(['mv', [['th', '0']]])
                  executor.prepareMacro(['mv', 'th', '0']) # backwards compatibility - see note
              2.2 executor.prepareMacro(('ascan', 'th', 0, 100, 10, 1.0))
                  executor.prepareMacro(['mv', [['th', 0]]])
                  executor.prepareMacro(['mv', 'th', 0]) # backwards compatibility - see note
              2.3 th = self.getObj('th');
                  executor.prepareMacro(['ascan', th, 0, 100, 10, 1.0])
                  executor.prepareMacro(['mv', [[th, 0]]])
                  executor.prepareMacro(['mv', th, 0]) # backwards compatibility - see note
           3. a space separated string of parameters (this is not compatible
              with multiple or nested repeat parameters, furthermore the repeat
              parameter must be the last one):
              executor.prepareMacro('ascan th 0 100 10 1.0')
              executor.prepareMacro('mv %s 0' % motor.getName())

        .. note:: From Sardana 2.0 the repeat parameter values must be passed
            as lists of items. An item of a repeat parameter containing more
            than one member is a list. In case when a macro defines only one
            repeat parameter and it is the last parameter, for the backwards
            compatibility reasons, the plain list of items' members is allowed.

        :param pars: the command parameters as explained above
        :param opts: keyword optional parameters for prepare
        :return: a tuple of two elements: macro object, the result of preparing the macro
        """
        par0 = pars[0]
        if len(pars) == 1:
            if is_pure_str(par0):
                # dealing with sth like args = ('ascan th 0 100 10 1.0',)
                pars = par0.split()
                macro_name, macro_params = pars[0], pars[1:]
                macro_node = self._createMacroNode(macro_name, macro_params)
                pars = macro_node.toList()
            elif is_non_str_seq(par0):
                # dealing with sth like args = (['ascan', 'th', '0', '100', '10', '1.0'],)
                # or args = (['mv', [[mot01, 0], [mot02, 0]]])
                pars = par0
        # dealing with sth like args = ('ascan', 'th', '0', '100', '10', '1.0')
        # or args = ('mv', [[mot01, 0], [mot02, 0]])

        # in case parameters were passed as objects cast them to strings
        # but maintain None's to be able to discover missing params
        pars = recur_map(str, pars, keep_none=True)

        meta_macro, _, macro_params = self._decodeMacroParameters(pars)
        macro_name = meta_macro.name
        macro_id = init_opts.get("id")
        if macro_id is None:
            init_opts["id"] = macro_id
        macro_line = self._composeMacroLine(macro_name,
                                            macro_params,
                                            macro_id)

        init_opts['macro_line'] = macro_line

        macro_obj, prepare_result = self.prepareMacroObj(meta_macro,
                                                         macro_params,
                                                         init_opts,
                                                         prepare_opts)

        self._prepareGeneralHooks(macro_obj)

        return macro_obj, prepare_result

    def getRunningMacro(self):
        return self.macro_pointer

    def getLastMacro(self):
        return self._last_macro

    def clearRunningMacro(self):
        """Clear pointer to the running macro.

        ..warning:: Do not call it while the macro is running.

        .. deprecated: Use clearMacroStack() instead.
        """
        self.warning("Deprecated since 3.1.1. Use clearMacroStack() instead.")
        self._macro_stack = []

    def clearMacroStack(self):
        """Clear macro stack

        ..warning:: Do not call it while the macro is running.
        """
        self._macro_stack = []

    def __stopObjects(self):
        """Stops all the reserved objects in the executor"""
        for macro, objs in list(self._reserved_macro_objs.items()):
            if self._aborted:
                break  # someone aborted, no sense to stop anymore
            self._stopped_macro_objs[macro] = stopped_macro_objs = []
            for obj in objs:
                if self._aborted:
                    break  # someone aborted, no sense to stop anymore
                self.output(
                    "Stopping {} reserved by {}".format(obj, macro._name))
                try:
                    obj.stop()
                except AttributeError:
                    pass
                except:
                    self.warning("Unable to stop %s" % obj)
                    self.debug("Details:", exc_info=1)
                else:
                    self.output("{} stopped".format(obj))
                    stopped_macro_objs.append(obj)

    def __abortObjects(self):
        """Aborts all the reserved objects in the executor"""
        for macro, objs in list(self._reserved_macro_objs.items()):
            stopped_macro_objs = self._stopped_macro_objs[macro]
            for obj in objs:
                if obj in stopped_macro_objs:
                    continue
                self.output(
                    "Aborting {} reserved by {}".format(obj, macro._name))
                try:
                    obj.abort()
                except AttributeError:
                    pass
                except:
                    self.warning("Unable to abort %s" % obj)
                    self.debug("Details:", exc_info=1)
                else:
                    self.output("{} aborted".format(obj))

    def _setStopDone(self, _):
        self._stop_done.set()

    def _waitStopDone(self, timeout=None):
        self._stop_done.wait(timeout)

    def _isStopDone(self):
        return self._stop_done.is_set()

    def _setAbortDone(self, _):
        self._abort_done.set()

    def _waitAbortDone(self, timeout=None):
        self._abort_done.wait(timeout)

    def _isAbortDone(self):
        return self._abort_done.is_set()

    def abort(self):
        """**Internal method**. Aborts the macro abruptly."""
        # carefull: Inside this method never call a method that has the
        # mAPI decorator
        self._aborted = True
        if not self._isStopDone():
            Logger.debug(self, "Break stopping...")
            raise_in_thread(ReleaseException, self._stop_thread)
        self.macro_server.add_job(self._abort, self._setAbortDone)

    def release(self):
        """**Internal method**. Release the macro from hang situations

        Hanged situations:
        * hanged process of aborting reserved objects
        * hanged macro on_abort method.
        """
        # carefull: Inside this method never call a method that has the
        # mAPI decorator
        self._released = True
        if self._isAbortDone():
            m = self.getRunningMacro()
            Logger.debug(self, "Break {}.on_abort...".format(m._name))
            raise_in_thread(ReleaseException, m._macro_thread)
        else:
            Logger.debug(self, "Break aborting...")
            raise_in_thread(ReleaseException, self._abort_thread)


    def stop(self):
        self._stopped = True
        self.macro_server.add_job(self._stop, self._setStopDone)

    def _abort(self):
        self._abort_thread = threading.current_thread()
        if self._stopped:
            # stopping did not finish on its own - we are aborting it
            # but need to wait anyway so its thread finishes
            self._waitStopDone()
        m = self.getRunningMacro()
        if m is not None:
            m.abort()
        self.__abortObjects()

    def _stop(self):
        self._stop_thread = threading.current_thread()
        m = self.getRunningMacro()
        if m is not None:
            m.stop()
            if m.isPaused():
                m.resume(cb=self._macroResumed)
        self.__stopObjects()

    def pause(self):
        self._paused = True
        m = self.getRunningMacro()
        if m is not None:
            m.pause(cb=self._macroPaused)

    def _macroPaused(self, m):
        """Calback that is executed when the macro has efectively paused"""
        self.sendMacroStatusPause()
        self.sendState(Macro.Pause)

    def resume(self):
        if not self._paused:
            return
        self._paused = False
        m = self.getRunningMacro()
        if m is not None:
            m.resume(cb=self._macroResumed)

    def _macroResumed(self, m):
        """Callback that is executed when the macro has effectively resumed
        execution after being paused"""
        self.sendMacroStatusResume()
        self.sendState(Macro.Running)

    def run(self, params, asynch=True):
        """Runs the given macro(s)

        :param params: (sequence<str>) can be either a sequence of <macro name> [, <macro_parameter> ]
                       or a sequence with a single element which represents the xml string for a
                       macro script
        :return: (lxml.etree.Element) the xml representation of the running macro
        """
        # dict<PoolElement, set<Macro>>
        # key PoolElement - reserved object
        # value set<Macro> macros that reserved the object
        self._reserved_objs = {}

        # dict<Macro, seq<PoolElement>>
        # key Macro - macro object
        # value - sequence of reserved objects by the macro
        self._reserved_macro_objs = {}

        # reset the stacks
        self._macro_stack = []
        self._xml_stack = []
        self._stop_done = threading.Event()
        self._abort_done = threading.Event()
        self._aborted = False
        self._stopped = False
        self._paused = False
        self._last_macro_status = None

        # convert given parameters into an xml
        self._xml = self._preprocessParameters(params)

        if asynch:
            # start the job of actually running the macro
            self.macro_server.add_job(self.__runXML, self._jobEnded)
            # return the proper xml
            return self._xml
        else:
            self.__runXML()

    def _jobEnded(self, *args, **kw):
        self.debug("Job ended (stopped=%s, aborted=%s)",
                   self._stopped, self._aborted)

    def __runXML(self):
        self.sendState(Macro.Running)
        try:
            self.__runStatelessXML()
            self.sendState(Macro.Finished)
        except (StopException, AbortException):
            self.sendState(Macro.Abort)
        except Exception:
            self.sendState(Macro.Exception)
        finally:
            self._macro_stack = []
            self._xml_stack = []

    def __runStatelessXML(self, xml=None):
        if xml is None:
            xml = self._xml
        node = xml.tag
        if node == 'sequence':
            for xml_macro in xml.findall('macro'):
                self.__runXMLMacro(xml_macro)
        elif node == 'macro':
            self.__runXMLMacro(xml)

    def __runXMLMacro(self, xml):
        assert xml.tag == 'macro'
        parent_macro = self.getRunningMacro()
        try:
            macro_obj, _ = self._prepareXMLMacro(xml, parent_macro)
        except AbortException as ae:
            raise ae
        except Exception as e:
            door = self.door
            door.error("Error: %s", str(e))
            door.debug("Error details:", exc_info=1)
            raise e

        self._xml_stack.append(xml)
        try:
            self.runMacro(macro_obj)
        finally:
            self._xml_stack.pop()

    _runXMLMacro = __runXMLMacro

    def runMacro(self, macro_obj):

        name = macro_obj._getName()
        desc = macro_obj._getDescription()
        door = self.door

        log_macro_manager = LogMacroManager(macro_obj)
        log_macro_manager.enable()

        if self._aborted:
            self.sendMacroStatusAbort()
            raise AbortException("aborted between macros (before %s)" % name)
        elif self._stopped:
            self.sendMacroStatusStop()
            raise StopException("stopped between macros (before %s)" % name)
        macro_exp, tb, result = None, None, None
        try:
            self.debug("[START] runMacro %s" % desc)
            self._macro_stack.append(macro_obj)
            for step in macro_obj.exec_():
                self.sendMacroStatus((step,))
            result = macro_obj.getResult()
            # sending result only if we are the top most macro
            if macro_obj.hasResult() and macro_obj.getParentMacro() is None:
                result_repr = self.__preprocessResult(result)
                door.debug("sending result %s", result_repr)
                self.sendResult(result_repr)
        except AbortException as ae:
            macro_exp = ae
        except StopException as se:
            macro_exp = se
        except MacroServerException as mse:
            exc_info = sys.exc_info()
            macro_exp = mse
            if not mse.traceback:
                mse.traceback = traceback.format_exc()
        except DevFailed as df:
            exc_info = sys.exc_info()
            exp_pars = {'type': df.args[0].reason,
                        'msg': df.args[0].desc,
                        'args': df.args,
                        'traceback': traceback.format_exc()}
            macro_exp = MacroServerException(exp_pars)
        except Exception as err:
            exc_info = sys.exc_info()
            exp_pars = {'type': err.__class__.__name__,
                        'msg': str(err),
                        'args': err.args,
                        'traceback': traceback.format_exc()}
            macro_exp = MacroServerException(exp_pars)

        # make sure the macro's on_abort is called and that a proper macro
        # status is sent
        if self._aborted:
            self._waitAbortDone()
            self.output("Executing {}.on_abort method...".format(name))
            macro_obj._abortOnError()
            self.sendMacroStatusAbort()
        elif self._stopped:
            self._waitStopDone()
            self.output("Executing {}.on_stop method...".format(name))
            macro_obj._stopOnError()
            self.sendMacroStatusStop()

        self.returnObjs(self.macro_pointer)

        # From this point on don't call any method of macro_obj which is part
        # of the mAPI (methods decorated with @mAPI) to avoid throwing an
        # AbortException if an Abort has been performed.
        if macro_exp is not None:
            if not self._stopped and not self._aborted:
                self.sendMacroStatusException(exc_info)
            self.debug("[ENDEX] (%s) runMacro %s" %
                       (macro_exp.__class__.__name__, name))
            if isinstance(macro_exp, MacroServerException):
                if macro_obj.parent_macro is None:
                    door.debug(macro_exp.traceback)
                    msg = ("An error occurred while running {}:\n"
                           "{!r}").format(macro_obj.getName(), macro_exp)
                    door.error(msg)
                    msg = "Hint: in Spock execute `www`to get more details"
                    door.info(msg)
            self._popMacro()
            raise macro_exp
        self.debug("[ END ] runMacro %s" % desc)

        # decide whether to preserve the macro data
        env_var_name = 'PreserveMacroData'
        try:
            preserve_macro_data = macro_obj.getEnv(env_var_name)
        except UnknownEnv:
            preserve_macro_data = True
        if preserve_macro_data:
            self._last_macro = self.macro_pointer
        else:
            self.debug('Macro data will not be preserved. ' +
                       'Set "%s" environment variable ' % env_var_name +
                       'to True in order to change it.')
            self._last_macro = None
        self._popMacro()

        log_macro_manager.disable()

        return result

    def _popMacro(self):
        self._macro_stack.pop()

    def sendState(self, state):
        return self.door.set_state(state)

    def sendStatus(self, status):
        return self.door.set_status(status)

    def sendResult(self, result):
        return self.door.set_result(result)

    def getLastMacroStatus(self):
        return self.macro_pointer._getMacroStatus()

    def sendMacroStatusFinish(self):
        ms = self.getLastMacroStatus()
        if ms is not None:
            ms['state'] = 'finish'

            self.debug("Sending finish event")
            self.sendMacroStatus((ms,))

    def sendMacroStatusStop(self):
        ms = self.getLastMacroStatus()
        if ms is not None:
            ms['state'] = 'stop'

            self.debug("Sending stop event")
            self.sendMacroStatus((ms,))

    def sendMacroStatusAbort(self):
        ms = self.getLastMacroStatus()
        if ms is not None:
            ms['state'] = 'abort'

            self.debug("Sending abort event")
            self.sendMacroStatus((ms,))

    def sendMacroStatusException(self, exc_info):
        ms = self.getLastMacroStatus()
        if ms is not None:
            ms['state'] = 'exception'
            ms['exc_type'] = str(exc_info[0])
            ms['exc_value'] = str(exc_info[1])
            ms['exc_stack'] = traceback.format_exception(*exc_info)
            self.debug("Sending exception event")
            self.sendMacroStatus((ms,))

    def sendMacroStatusPause(self):
        ms = self.getLastMacroStatus()
        if ms is not None and len(ms) > 0:
            ms['state'] = 'pause'
            self.debug("Sending pause event")
            self.sendMacroStatus((ms,))

    def sendMacroStatusResume(self):
        ms = self.getLastMacroStatus()
        if ms is not None and len(ms) > 0:
            ms['state'] = 'resume'
            self.debug("Sending resume event")
            self.sendMacroStatus((ms,))

    def sendMacroStatus(self, data):
        self._last_macro_status = data
        # data = self._macro_status_codec.encode(('', data))
        return self.door.set_macro_status(data)

    def sendRecordData(self, data, codec=None):
        return self.door.set_record_data(data, codec=codec)

    def reserveObj(self, obj, macro_obj, priority=0):
        if obj is None or macro_obj is None:
            return

        # Fill _reserved_macro_objs
        objs = self._reserved_macro_objs[macro_obj] = \
            self._reserved_macro_objs.get(macro_obj, list())
        if obj not in objs:
            if priority:
                objs.insert(0, obj)
            else:
                objs.append(obj)

        # Fill _reserved_objs
        macros = self._reserved_objs[obj] = self._reserved_objs.get(obj, set())
        macros.add(macro_obj)

        # Tell the object that it is reserved by a new macro
        if hasattr(obj, 'reserve'):
            obj.reserve(macro_obj)

    def returnObjs(self, macro_obj):
        """Free the macro reserved objects"""
        if macro_obj is None:
            return
        # remove eventually stopped objects to not keep reference to them
        self._stopped_macro_objs.pop(macro_obj, None)
        objs = self._reserved_macro_objs.get(macro_obj)
        if objs is None:
            return

        # inside returnObj we change the list so we have to iterate with a copy
        for obj in copy.copy(objs):
            self.returnObj(obj, macro_obj)

    def returnObj(self, obj, macro_obj):
        """Free an object reserved by a macro"""
        if obj is None or macro_obj is None:
            return

        if hasattr(obj, 'unreserve'):
            obj.unreserve()
        objs = self._reserved_macro_objs.get(macro_obj)
        if objs is None:
            return
        objs.remove(obj)
        if len(objs) == 0:
            del self._reserved_macro_objs[macro_obj]

        try:
            macros = self._reserved_objs[obj]
            macros.remove(macro_obj)
            if not len(macros):
                del self._reserved_objs[obj]
        except KeyError:
            self.debug("Unexpected KeyError trying to remove reserved object")
