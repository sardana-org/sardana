#!/usr/bin/env python

##############################################################################
##
## This file is part of Sardana
##
## http://www.sardana-controls.org/
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
##
## Sardana is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## Sardana is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################

"""This module contains the class definition for the MacroServer macro
manager"""

__all__ = ["RecorderManager"]

__docformat__ = 'restructuredtext'

import os
import sys
import copy
import inspect

from taurus.external.ordereddict import OrderedDict

from sardana import sardanacustomsettings
from sardana.sardanaexception import format_exception_only_str
from sardana.sardanamodulemanager import ModuleManager
from sardana.macroserver.msmanager import MacroServerManager
from sardana.macroserver.scan.recorder import DataRecorder
from sardana.macroserver.msmetarecorder import RecorderLibrary, \
    RecorderClass
from sardana.macroserver.msexception import UnknownRecorder, LibraryError

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class RecorderManager(MacroServerManager):

    DEFAULT_RECORDER_DIRECTORIES = os.path.join(_BASE_DIR, 'recorders'),

    def __init__(self, macro_server, recorder_path=None):
        MacroServerManager.__init__(self, macro_server)
        if recorder_path is not None:
            self.setRecorderPath(recorder_path)

    def reInit(self):
        if self.is_initialized():
            return

        # dict<str, RecorderLibrary>
        # key   - module name (without path and without extension)
        # value - RecorderLibrary object representing the module
        self._modules = {}

        #: dict<str, <metarecorder.RecorderClass>
        #: key   - recorder name
        #: value - RecorderClass object representing the recorder
        self._recorder_dict = {}

        # list<str>
        # elements are absolute paths
        self._recorder_path = []

        # custom map (per installation) allowing to avoid
        # recorder class ambiguity problems (using extension filter)
        #: dict<str, str>
        #: key   - scan file extension
        #: value - recorder name
        self._custom_scan_recorder_map = getattr(sardanacustomsettings,
                                                 "SCAN_RECORDER_MAP",
                                                 None)
        #: dict<str, str>
        #: key   - scan file extension
        #: value - list with recorder name(s)
        self._scan_recorder_map = {}

        MacroServerManager.reInit(self)

    def cleanUp(self):
        if self.is_cleaned():
            return

        if self._modules:
            for _, types_dict in self._modules.items():
                for type_name in types_dict:
                    Type.removeType(type_name)

        self._recorder_path = None
        self._modules = None
        MacroServerManager.cleanUp(self)

    def setScanRecorderMap(self, recorder_map):
        """Registers a new map of recorders in this manager.
        """
        self._scan_recorder_map = dict(recorder_map)

    def setRecorderPath(self, recorder_path):
        """Registers a new list of recorder directories in this manager.
        """
        _recorder_path = []
        for paths in recorder_path:
            splited_paths = paths.split(":")
            for path in splited_paths:
                # filter empty and commented paths
                if not path.startswith("#"):
                    _recorder_path.append(path)

        for recorder_dir in self.DEFAULT_RECORDER_DIRECTORIES:
            if recorder_dir not in _recorder_path:
                _recorder_path.append(recorder_dir)

        self._recorder_path = _recorder_path

        recorder_file_names = self._findRecorderLibNames(
            _recorder_path)

        for mod_name, file_name in recorder_file_names.iteritems():
            dir_name = os.path.dirname(file_name)
            path = [dir_name]
            try:
                self.reloadRecorderLib(mod_name, path)
            except:
                pass
        pass

    def getRecorderPath(self):
        return self._recorder_path

    def getRecorderMetaClass(self, recorder_name):
        """ Return the Recorder class for the given class name.
        :param klass_name: Name of the recorder class.
        :type klass_name: str
        :return:  a :obj:`class` class of recorder or None if it does not exist
        :rtype:
            :obj:`class:`~sardana.macroserver.msmetarecorder.RecorderClass`\>
        """
        ret = self._recorder_dict.get(recorder_name)
        if ret is None:
            raise UnknownRecorder("Unknown recorder %s" % recorder_name)
        return ret

    def getRecorderMetaClasses(self, filter=None, extension=None):
        """ Returns a :obj:`dict` containing information about recorder classes.

        :param filter: a klass of a valid type of Recorder
        :type filter: obj
        :param filter: a scan file extension
        :type filter: str
        :return: a :obj:`dict` containing information about recorder classes
        :rtype:
            :obj:`dict`\<:obj:`str`\,
            :class:`~sardana.macroserver.msmetarecorder.RecorderClass`\>
        """
        if filter is None:
            filter = DataRecorder
        ret = {}
        for name, klass in self._recorder_dict.items():
            if issubclass(klass.recorder_class, filter):
                if extension:
                    if self._custom_scan_recorder_map:
                        _map = self._custom_scan_recorder_map
                        name = _map.get(extension, None)
                        if name:
                            klass = self.getRecorderMetaClass(name)
                            ret[name] = klass
                    else:
                        _map = self._scan_recorder_map
                        if (extension in _map.keys() and
                            klass in _map[extension]):
                            ret[name] = klass
                else:
                    ret[name] = klass
        return ret

    def getRecorderClasses(self, filter=None, extension=None):
        """ Returns a :obj:`dict` containing information about recorder classes.
        :param filter: a klass of a valid type of Recorder
        :type filter: obj
        :param filter: a scan file extension
        :type filter: str
        :return: a :obj:`dict` containing information about recorder classes
        :rtype:
            :obj:`dict`\<:obj:`str`\, :class:`DataRecorder`\>
        """
        if filter is None:
            filter = DataRecorder
        meta_klasses = self.getRecorderMetaClasses(filter=filter,
                                                   extension=extension)
        return dict((key, value.klass)
                    for (key, value) in meta_klasses.items())

    def getRecorderClass(self, klass_name):
        """ Return the Recorder class for the given class name.
        :param klass_name: Name of the recorder class.
        :type klass_name: str
        :return:  a :obj:`class` class of recorder or None if it does not exist
        :rtype:
            :obj:`class:`DataRecorder`\>
        """
        meta_klass = self.getRecorderMetaClass(klass_name)
        return meta_klass.klass

    def _findRecorderLibName(self, lib_name, path=None):
        path = path or self.getRecorderPath()
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

    def _findRecorderLibNames(self, recorder_path=None):
        path = recorder_path or self.getRecorderPath()
        ret = OrderedDict()
        for p in reversed(path):
            try:
                for fdir in os.listdir(p):
                    name, ext = os.path.splitext(fdir)
                    if name.startswith("_"):
                        continue
                    if ext.endswith('.py'):
                        full_path = os.path.abspath(os.path.join(p, fdir))
                        ret[name] = full_path
            except:
                self.debug("'%s' is not a valid path" % p)
        return ret

    def reloadRecorderLib(self, module_name, path=None):
        """Reloads the given library(=module) names.

        :param module_name: recorder library name (=python module name)
        :param path:
            a list of absolute path to search for libraries [default: None,
            means the current RecorderPath will be used]"""
        path = path or self.getRecorderPath()
        # reverse the path order:
        # more priority elements last. This way if there are repeated elements
        # they first ones (lower priority) will be overwritten by the last ones
        if path:
            path = copy.copy(path)
            path.reverse()

        # if there was previous Recorder Library info remove it
        old_recorder_lib = self._modules.pop(module_name, None)
        if old_recorder_lib is not None:
            for recorder in old_recorder_lib.get_recorders():
                self._recorder_dict.pop(recorder.name)
                # remove recorders from the map
                for _, recorders in self._scan_recorder_map.iteritems():
                    try:
                        recorders.remove(recorder)
                    except:
                        pass

        mod_manager = ModuleManager()
        m, exc_info = None, None
        try:
            m = mod_manager.reloadModule(
                module_name, path, reload=reload)
        except:
            exc_info = sys.exc_info()

        params = dict(module=m, name=module_name,
                      macro_server=self.macro_server, exc_info=exc_info)
        if m is None:
            file_name = self._findRecorderLibName(module_name)
            if file_name is None:
                if exc_info:
                    msg = format_exception_only_str(*exc_info[:2])
                else:
                    msg = "Error (re)loading recorder library '%s'" \
                        % module_name
                raise LibraryError(msg, exc_info=exc_info)
            params['file_path'] = file_name
            recorder_lib = RecorderLibrary(**params)
            self._modules[module_name] = recorder_lib
        else:
            recorder_lib = RecorderLibrary(**params)
            lib_contains_recorders = False
            abs_file = recorder_lib.file_path
            for _, klass in inspect.getmembers(m, inspect.isclass):
                if issubclass(klass, DataRecorder):
                    # if it is a class defined in some other class forget it to
                    # avoid replicating the same recorder in different
                    # recorder files
                    # use normcase to treat case insensitivity of paths on
                    # certain platforms e.g. Windows
                    if os.path.normcase(inspect.getabsfile(klass)) !=\
                       os.path.normcase(abs_file):
                        continue
                    lib_contains_recorders = True
                    self.addRecorder(recorder_lib, klass)
            if lib_contains_recorders:
                self._modules[module_name] = recorder_lib

        return recorder_lib

    def addRecorder(self, recorder_lib, klass):
        """Adds a new recorder class
        """
        recorder_name = klass.__name__
        exists = recorder_lib.has_recorder(recorder_name)
        if exists:
            action = "Updating"
        else:
            action = "Adding"

        self.debug("%s recorder %s" % (action, recorder_name))

        try:
            recorder_class = RecorderClass(lib=recorder_lib, klass=klass,
                                           macro_server=self.macro_server)
            recorder_lib.add_recorder(recorder_class)
            self._recorder_dict[recorder_name] = recorder_class
            if hasattr(klass, "formats"):
                self._addRecorderToMap(recorder_class)
        except:
            self.warning("Failed to add recorder class %s", recorder_name,
                         exc_info=1)

        if exists:
            action = "Updated"
        else:
            action = "Added"
        self.debug("%s recorder %s" % (action, recorder_name))

    def _addRecorderToMap(self, recorder_class):
        klass = recorder_class.klass
        for ext in klass.formats.values():
            recorders = self._scan_recorder_map.get(ext, [])
            if len(recorders) == 0:
                recorders.append(recorder_class)
            else:
                recorder_from_map = recorders[-1]  # it could be any recorder
                # recorders are on the same priority level (located in the same
                # directory) - just append it to the list
                if recorder_from_map.lib.path == recorder_class.lib.path:
                    recorders.append(recorder_class)
                # new recorder comes from another directory (it must be of
                # higher priority) - forget about others and create new list
                else:
                    recorders = [recorder_class]
            self._scan_recorder_map[ext] = recorders
