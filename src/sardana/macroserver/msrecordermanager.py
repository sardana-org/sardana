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

from sardana import sardanacustomsettings
from sardana.sardanamodulemanager import ModuleManager
from sardana.macroserver.msmanager import MacroServerManager
from sardana.macroserver.scan.recorder import DataRecorder
from sardana.macroserver.msmetarecorder import RecorderLibrary, \
    RecorderClass
from sardana.macroserver.msexception import UnknownRecorder
from sardana.macroserver.scan.recorder.storage import BaseFileRecorder

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class RecorderManager(MacroServerManager):

    DEFAULT_RECORDER_DIRECTORIES = os.path.join(
        _BASE_DIR, 'scan', 'recorder'),

    _DEFAULT_FILE_RECORDER_MAP = {
        '.h5': 'NXscan_FileRecorder',
        '.h4': 'NXscan_FileRecorder',
        '.xml': 'NXscan_FileRecorder',
        '.spec': 'SPEC_FileRecorder',
        '.fio': 'FIO_FileRecorder'}

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

        scan_recorder_map = getattr(sardanacustomsettings, "SCAN_RECORDER_MAP",
                            self._DEFAULT_FILE_RECORDER_MAP)
        #: dict<str, str>
        #: key   - scan file extension
        #: value - recorder name
        self._scan_recorder_map = dict(scan_recorder_map)

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
        # add external recorder directories
        _external_recorder_path = []
        for paths in recorder_path:
            splited_paths = paths.split(":")
            for path in splited_paths:
                # filter empty and commented paths
                if not path.startswith("#"):
                    _external_recorder_path.append(path)

        self._recorder_path = _external_recorder_path

        recorder_file_names = self._findRecorderLibNames(
            _external_recorder_path)

        for mod_name, file_name in recorder_file_names.iteritems():
            dir_name = os.path.dirname(file_name)
            path = [dir_name]
            try:
                self.reloadRecorderLib(mod_name, path,
                                       reload=False, add_ext=True)
            except:
                pass

        # add basic recorder directories
        _basic_recorder_path = []
        for recorder_dir in self.DEFAULT_RECORDER_DIRECTORIES:
            if recorder_dir not in recorder_path:
                _basic_recorder_path.append(recorder_dir)

        recorder_file_names = self._findRecorderLibNames(
            _basic_recorder_path)
        self._recorder_path.append(_basic_recorder_path)
        for mod_name, file_name in recorder_file_names.iteritems():
            dir_name = os.path.dirname(file_name)
            path = [dir_name]
            try:
                self.reloadRecorderLib(mod_name, path, reload=False)
            except:
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

    def getRecorderMetaClasses(self, filter=DataRecorder, extension=None):
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
        ret = {}
        for name, klass in self._recorder_dict.items():
            if issubclass(klass.recorder_class, filter):
                if not extension:
                    ret[name] = klass
                elif extension in self._scan_recorder_map.keys() and \
                        self._scan_recorder_map[extension] == name:
                        ret[name] = klass

        return ret

    def getRecorderClasses(self, filter=DataRecorder, extension=None):
        """ Returns a :obj:`dict` containing information about recorder classes.
        :param filter: a klass of a valid type of Recorder
        :type filter: obj
        :param filter: a scan file extension
        :type filter: str
        :return: a :obj:`dict` containing information about recorder classes
        :rtype:
            :obj:`dict`\<:obj:`str`\, :class:`DataRecorder`\>
        """
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

    def _findModuleName(self, path, name):
        mod_name = ""
        path_list = path.split(os.sep)
        path_list.append(name)
        while path_list:
            if mod_name:
                mod_name = "." + mod_name
            mod_name = path_list[-1] + mod_name
            path_list[-1] = "__init__.py"
            jpath = os.path.join(*path_list)
            if not path_list[0]:
                jpath = os.sep + jpath
            if not os.path.isfile(jpath):
                break
            path_list.pop()
        return mod_name

    def _findRecorderLibNames(self, recorder_path=None):
        paths = recorder_path or self.getRecorderPath()
        ret = {}
        for path in reversed(paths):
            try:
                for fdir in os.listdir(path):
                    name, ext = os.path.splitext(fdir)
                    if name.startswith("_"):
                        continue
                    if ext.endswith('.py'):
                        module_name = self._findModuleName(path, name)
                        full_path = os.path.abspath(os.path.join(path, fdir))
                        ret[module_name] = full_path
            except:
                self.debug("'%s' is not a valid path" % path)
        return ret

    def reloadRecorderLib(self, module_name, path=None, reload=True,
                          add_ext=False):
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

        # if there was previous Recorder Lib info remove it
        if module_name in self._modules.keys():
            self._modules.pop(module_name)

        if module_name in self._modules:
            return None

        mod_manager = ModuleManager()
        m, exc_info = None, None
        try:
            m = mod_manager.reloadModule(
                module_name, path, reload=reload)
        except:
            self.error("Error adding recorder %s", module_name)
            self.debug("Details:", exc_info=1)
            exc_info = sys.exc_info()
        params = dict(module=m, name=module_name,
                      macro_server=self.macro_server)
        if m is None or exc_info is not None:
            params['exc_info'] = exc_info
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
                    self.addRecorder(recorder_lib, klass, add_ext=add_ext)
            if lib_contains_recorders:
                self._modules[module_name] = recorder_lib

        return recorder_lib

    def addRecorder(self, recorder_lib, klass, add_ext=False):
        """Adds a new recorder class"""
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
            #self._setRecorderTypes(klass, recorder_class)
            recorder_lib.add_recorder(recorder_class)
            self._recorder_dict[recorder_name] = recorder_class
            if add_ext and hasattr(klass, "formats"):
                for ext in klass.formats.values():
                    self._scan_recorder_map[ext] = recorder_name

        except:
            self.warning("Failed to add recorder class %s", recorder_name,
                         exc_info=1)

        if exists:
            action = "Updated"
        else:
            action = "Added"
        self.debug("%s recorder %s" % (action, recorder_name))
