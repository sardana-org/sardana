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

"""This module is part of the Python Pool library. It defines the class which
controls finding, loading/unloading of device pool controller plug-ins."""

__all__ = ["ControllerManager"]

__docformat__ = 'restructuredtext'

import os
import re
import sys
import copy
import types
import inspect

from collections import OrderedDict

from taurus.core import ManagerState
from taurus.core.util.log import Logger
from taurus.core.util.singleton import Singleton

from sardana.sardanamodulemanager import ModuleManager
from sardana.pool import controller
from sardana.pool.poolexception import UnknownController
from sardana.pool.poolmetacontroller import ControllerLibrary, ControllerClass

CONTROLLER_TEMPLATE = '''

class @controller_name@(MotorController):
    """This class representes a Sardana motor controller."""

    ctrl_features = []
    MaxDevice = 1024

    ctrl_properties = {}
    ctrl_attributes = {}
    axis_attributes = {}

    def __init__(self, inst, props, *args, **kwargs):
        MotorController.__init__(self, inst, props, *args, **kwargs)

'''


class ControllerManager(Singleton, Logger):
    """The singleton class responsible for managing controller plug-ins."""

    DEFAULT_CONTROLLER_DIRECTORIES = 'poolcontrollers',

    def __init__(self):
        """Initialization. Nothing to be done here for now."""
        pass

    def init(self, *args, **kwargs):
        """Singleton instance initialization.

        Parameters
        ----------
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        name = self.__class__.__name__
        self._state = ManagerState.UNINITIALIZED
        self.call__init__(Logger, name)
        self._pool = None
        self.reInit()

    def reInit(self):
        """Singleton re-initialization."""
        if self._state == ManagerState.INITED:
            return

        #: dict<str, metacontroller.ControllerLibray>
        #: key   - module name (without path and without extension)
        #: value - ControllerLibrary object representing the module
        self._modules = {}

        #: dict<str, <metacontroller.ControllerClass>
        #: key   - controller name
        #: value - ControllerClass object representing the controller
        self._controller_dict = {}

        #: list<str>
        #: elements are absolute paths
        self._controller_path = []

        l = []
        for _, klass in inspect.getmembers(controller, inspect.isclass):
            if not issubclass(klass, controller.Controller):
                continue
            l.append(klass)
        self._base_classes = l

        self._state = ManagerState.INITED

    def cleanUp(self):
        """Singleton clean up."""
        if self._state == ManagerState.CLEANED:
            return

        # if self._modules:
        #    ModuleManager().unloadModules(self._modules.keys())

        self._controller_path = None
        self._controller_dict = None
        self._modules = None

        self._state = ManagerState.CLEANED

    def set_pool(self, pool):
        """

        Parameters
        ----------
        pool :
            

        Returns
        -------

        """
        self._pool = pool

    def get_pool(self):
        """ """
        return self._pool

    def setControllerPath(self, controller_path, reload=True):
        """Registers a new list of controller directories in this manager.

        Parameters
        ----------
        seq :
            str> controller_path: a sequence of absolute paths where this
            manager should look for controllers
            
            .. warning::
            as a consequence all the controller modules will be reloaded.
            This means that if any reference to an old controller object was
            kept it will refer to an old module (which could possibly generate
            problems of type class A != class A)
        controller_path :
            
        reload :
             (Default value = True)

        Returns
        -------

        """
        p = []
        for item in controller_path:
            p.extend(item.split(os.pathsep))

        # filter empty and commented paths
        p = [i for i in p if i and not i.startswith("#")]

        # add basic dummy controller directory(ies)
        pool_dir = os.path.dirname(os.path.abspath(__file__))
        for ctrl_dir in self.DEFAULT_CONTROLLER_DIRECTORIES:
            ctrl_dir = os.path.join(pool_dir, ctrl_dir)
            if ctrl_dir not in p:
                p.append(ctrl_dir)

        self._controller_path = p

        controller_file_names = self._findControllerLibNames()

        for mod_name, file_name in controller_file_names.items():
            dir_name = os.path.dirname(file_name)
            path = [dir_name]
            try:
                self.reloadControllerLib(mod_name, path, reload=reload)
            except Exception:
                pass

    def getControllerPath(self):
        """Returns the current sequence of absolute paths used to look for
        controllers.

        Parameters
        ----------

        Returns
        -------
        seq<str>
            sequence of absolute paths

        """
        return self._controller_path

    def _findControllerLibNames(self, path=None):
        """internal method

        Parameters
        ----------
        path :
             (Default value = None)

        Returns
        -------

        """
        path = path or self.getControllerPath()
        ret = OrderedDict()
        for p in reversed(path):
            try:
                for f in os.listdir(p):
                    name, ext = os.path.splitext(f)
                    if not name[0].isalpha():
                        continue
                    if ext.endswith('py'):
                        ret[name] = os.path.abspath(os.path.join(p, f))
            except:
                self.debug("'%s' is not a valid path" % p)
        return ret

    def _fromNameToFileName(self, lib_name, path=None):
        """internal method

        Parameters
        ----------
        lib_name :
            
        path :
             (Default value = None)

        Returns
        -------

        """
        path = path or self.getControllerPath()[0]
        f_name = lib_name
        if not f_name.endswith('.py'):
            f_name += '.py'

        if os.path.isabs(f_name):
            path, _ = os.path.split(f_name)
            if not path in self.getControllerPath():
                raise Exception("'%s' is not part of the PoolPath" % path)
        else:
            f_name = os.path.join(path, f_name)
        return f_name

    def getOrCreateControllerLib(self, lib_name, controller_name=None):
        """Gets the exiting controller lib or creates a new controller lib file.
        If name is not None, a controller template code for the given
        controller name is appended to the end of the file.

        Parameters
        ----------
        lib_name :
            
        controller_name :
             (Default value = None)

        Returns
        -------
        tuple<str, str, int>
            a sequence with three items: full_filename, code, line number
            line number is 0 if no controller is created or n representing
            the first line of code for the given controller name.

        """
        # if only given the module name
        controller_lib = self.getControllerLib(lib_name)

        if controller_name is None:
            line_nb = 0
            if controller_lib is None:
                f_name, code = self.createControllerLib(lib_name), ''
            else:
                f_name = controller_lib.get_file_name()
                f = open(f_name)
                code = f.read()
                f.close()
        else:
            # if given controller name
            if controller_lib is None:
                f_name, code, line_nb = self.createController(
                    lib_name, controller_name)
            else:
                controller = controller_lib.get_controller(controller_name)
                if controller is None:
                    f_name, code, line_nb = self.createController(
                        lib_name, controller_name)
                else:
                    _, line_nb = controller.getCode()
                    f_name = controller.getFileName()
                    f = open(f_name)
                    code = f.read()
                    f.close()

        return [f_name, code, line_nb]

    def setControllerLib(self, lib_name, code):
        """Creates a new controller library file with the given name and code.
        The new module is imported and becomes imediately available.

        Parameters
        ----------
        lib_name :
            
        code :
            

        Returns
        -------

        """
        f_name = self._fromNameToFileName(lib_name)
        f = open(f_name, 'w')
        f.write(code)
        f.flush()
        f.close()
        _, name = os.path.split(f_name)
        mod, _ = os.path.splitext(name)
        self.reloadControllerLib(mod)

    def createControllerLib(self, lib_name, path=None):
        """Creates a new empty controller library (python module)

        Parameters
        ----------
        lib_name :
            
        path :
             (Default value = None)

        Returns
        -------

        """
        f_name = self._fromNameToFileName(lib_name, path)

        if os.path.exists(f_name):
            raise Exception(
                "Unable to create controller lib: '%s' already exists" % f_name)

        f = open(f_name, 'w')
        f.close()
        return f_name

    def createController(self, lib_name, controller_name):
        """Creates a new controller

        Parameters
        ----------
        lib_name :
            
        controller_name :
            

        Returns
        -------

        """
        f_name = self._fromNameToFileName(lib_name)

        create = not os.path.exists(f_name)

        template = ''
        if create:
            template += 'from sardana.pool.controller import *\n\n'
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
        try:
            dir_name = os.path.realpath(__file__)
            dir_name = os.path.dirname(dir_name)
            template_fname = 'controller_template.txt'
            template_fname = os.path.join(dir_name, template_fname)
            f_templ = open(template_fname, 'r')
            template += f_templ.read()
            f_templ.close()
        except:
            self.debug(
                "Failed to open template controller file. Using simplified template")
            template += CONTROLLER_TEMPLATE
            if f_templ:
                f_templ.close()

        template = template.replace('@controller_name@', controller_name)
        try:
            f.write(template)
            f.flush()
            f.seek(0)
            code = f.read()
        finally:
            f.close()
        return f_name, code, line_nb

    def reloadController(self, controller_name, path=None):
        """Reloads the module corresponding to the given controller name

        Parameters
        ----------
        controller_name : obj:`str`
            controller class name
        seq :
            str> path: a list of absolute path to search for libraries
            [default: None, meaning the current ControllerPath
            will be used
        path :
             (Default value = None)

        Returns
        -------

        """
        self.reloadControllers([controller_name], path=path)

    def reloadControllers(self, controller_names, path=None):
        """Reloads the modules corresponding to the given controller names

        Parameters
        ----------
        seq :
            str> controller_names: a list of controller class names
        seq :
            str> path: a list of absolute path to search for libraries
            [default: None, meaning the current ControllerPath
            will be used
        controller_names :
            
        path :
             (Default value = None)

        Returns
        -------

        """
        module_names = []
        for controller_name in controller_names:
            module_name = self.getControllerMetaClass(
                controller_name).get_module_name()
            module_names.append(module_name)
        self.reloadControllerLibs(module_names, path=path)

    def reloadControllerLibs(self, module_names, path=None, reload=True):
        """Reloads the given library(=module) names

        Parameters
        ----------
        seq :
            str> module_names: a list of module names
        seq :
            str> path: a list of absolute path to search for libraries
            [default: None, meaning the current ControllerPath
            will be used
        module_names :
            
        path :
             (Default value = None)
        reload :
             (Default value = True)

        Returns
        -------

        """
        ret = []
        for module_name in module_names:
            try:
                m = self.reloadControllerLib(module_name, path, reload=reload)
                if m:
                    ret.append(m)
            except:
                self.info("Failed to reload controller library %s", module_name)
                self.debug("Failed to reload controller library %s details",
                           module_name, exc_info=1)

        return ret

    def reloadControllerLib(self, module_name, path=None, reload=True):
        """Reloads the given library(=module) names

        Parameters
        ----------
        module_name : obj:`str`
            controller library name (=python module name)
        seq :
            str> path: a list of absolute path to search for libraries
            [default: None, meaning the current ControllerPath
            will be used]
        path :
             (Default value = None)
        reload :
             (Default value = True)

        Returns
        -------
        sardana.pool.poolmetacontroller.ControllerLibrary
            the ControllerLib object for the reloaded controller lib

        """
        path = path or self.getControllerPath()
        # reverse the path order:
        # more priority elements last. This way if there are repeated elements
        # they first ones (lower priority) will be overwritten by the last ones
        if path:
            path = copy.copy(path)
            path.reverse()

        # if there was previous Controller Lib info remove it
        if module_name in self._modules:
            self._modules.pop(module_name)

        m, exc_info = None, None
        try:
            m = ModuleManager().reloadModule(module_name, path, reload=reload)
        except:
            exc_info = sys.exc_info()

        controller_lib = None
        params = dict(module=m, name=module_name, pool=self.get_pool())
        if m is None or exc_info is not None:
            params['exc_info'] = exc_info
            controller_lib = ControllerLibrary(**params)
            self._modules[module_name] = controller_lib
        else:
            controller_lib = ControllerLibrary(**params)
            lib_contains_controllers = False
            abs_file = controller_lib.file_path
            for _, klass in inspect.getmembers(m, inspect.isclass):
                if issubclass(klass, controller.Controller):
                    # if it is a class defined in some other class forget it to
                    # avoid replicating the same controller in different
                    # controller files
                    # use normcase to treat case insensitivity of paths on
                    # certain platforms e.g. Windows
                    if os.path.normcase(inspect.getabsfile(klass)) !=\
                       os.path.normcase(abs_file):
                        continue
                    lib_contains_controllers = True
                    self.addController(controller_lib, klass)

            if lib_contains_controllers:
                self._modules[module_name] = controller_lib

        return controller_lib

    def addController(self, controller_lib, klass):
        """Adds a new controller class

        Parameters
        ----------
        controller_lib :
            
        klass :
            

        Returns
        -------

        """
        controller_name = klass.__name__
        exists = controller_lib.has_controller(controller_name)
        if exists:
            action = "Updating"
        else:
            action = "Adding"

        self.debug("%s controller %s" % (action, controller_name))

        try:
            controller_class = ControllerClass(pool=self.get_pool(),
                                               lib=controller_lib, klass=klass)
            #self._setControllerTypes(klass, controller_class)
            controller_lib.add_controller(controller_class)
            self._controller_dict[controller_name] = controller_class

        except:
            self.warning("Failed to add controller class %s", controller_name,
                         exc_info=1)

        if exists:
            action = "Updated"
        else:
            action = "Added"
        self.debug("%s controller %s" % (action, controller_name))

    def getControllerNames(self):
        """ """
        return sorted(self._controller_dict.keys())

    def getControllerLibNames(self):
        """ """
        return sorted(self._modules.keys())

    def getControllerLibs(self, filter=None):
        """

        Parameters
        ----------
        filter :
             (Default value = None)

        Returns
        -------

        """
        ret, expr = [], None
        if filter is not None:
            expr = re.compile(filter, re.IGNORECASE)
        for name, lib in self._modules.items():
            if lib.has_errors() or (expr is not None and expr.match(name) is None):
                continue
            ret.append(lib)
        ret.sort()
        return ret

    def getControllers(self, filter=None):
        """

        Parameters
        ----------
        filter :
             (Default value = None)

        Returns
        -------

        """
        if filter is None:
            return sorted(self._controller_dict.values())
        expr = re.compile(filter, re.IGNORECASE)

        ret = sorted([kls for n, kls in self._controller_dict.items()
                      if not expr.match(n) is None])
        return ret

    def getControllerMetaClass(self, controller_name):
        """

        Parameters
        ----------
        controller_name :
            

        Returns
        -------

        """
        ret = self._controller_dict.get(controller_name)
        if ret is None:
            raise UnknownController("Unknown controller %s" % controller_name)
        return ret

    def getControllerMetaClasses(self, controller_names):
        """

        Parameters
        ----------
        controller_names :
            

        Returns
        -------

        """
        ret = {}
        for name in controller_names:
            ret[name] = self._controller_dict.get(name)
        return ret

    def getControllerLib(self, name):
        """

        Parameters
        ----------
        name :
            

        Returns
        -------

        """
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
        return self._modules.get(module_name)

    def getControllerClass(self, controller_name):
        """

        Parameters
        ----------
        controller_name :
            

        Returns
        -------

        """
        return self.getControllerMetaClass(controller_name).klass

    def _getPlainControllerInfo(self, controller_names):
        """

        Parameters
        ----------
        controller_names :
            

        Returns
        -------

        """
        ret = []
        for controller_name in controller_names:
            controller_class = self.getControllerMetaClass(controller_name)
            if controller_class is not None:
                ret += controller_class.getInfo()
        return ret

    def decodeControllerParameters(self, in_par_list):
        """

        Parameters
        ----------
        in_par_list :
            

        Returns
        -------

        """
        if len(in_par_list) == 0:
            raise RuntimeError('Controller name not specified')
        controller_name_or_klass = in_par_list[0]
        controller_class = controller_name_or_klass
        if isinstance(controller_class, str):
            controller_class = self.getControllerClass(controller_class)
        if controller_class is None:
            raise UnknownController("Unknown controller %s" %
                                    controller_name_or_klass)
        from sardana.macroserver.msparameter import ParamDecoder
        out_par_list = ParamDecoder(controller_class, in_par_list)
        return controller_class, in_par_list, out_par_list

    def strControllerParamValues(self, par_list):
        """Creates a short string representation of the parameter values list.

        Parameters
        ----------
        par_list : list: list<str>
            list of strings representing the parameter values.

        Returns
        -------
        list<str>
            a list containning an abreviated version of the par_list
            argument.

        """
        ret = []
        for p in par_list:
            param_str = str(p)
            if len(param_str) > 9:
                param_str = param_str[:9] + "..."
            ret.append(param_str)
        return ret
