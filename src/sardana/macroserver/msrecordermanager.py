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
import copy

from sardana.sardanamodulemanager import ModuleManager
from sardana.macroserver.msmanager import MacroServerManager
from sardana.macroserver.scan.recorder import DataRecorder

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class RecorderManager(MacroServerManager):

    DEFAULT_RECORDER_DIRECTORIES = os.path.join(
        _BASE_DIR, 'scan', 'recorder'),

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

        # list<str>
        # elements are absolute paths
        self._recorder_path = []

        MacroServerManager.reInit(self)

    def cleanUp(self):
        if self.is_cleaned():
            return

        self._recorder_path = None
        self._modules = None
        MacroServerManager.cleanUp(self)

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
        # add basic recorder directories
        for recorder_dir in self.DEFAULT_RECORDER_DIRECTORIES:
            if not recorder_dir in recorder_path:
                _recorder_path.append(recorder_dir)

        self._recorder_path = _recorder_path

        recorder_file_names = self._findRecorderLibNames(_recorder_path)
        for mod_name, file_name in recorder_file_names.iteritems():
            dir_name = os.path.dirname(file_name)
            path = [dir_name]
            try:
                self.loadRecorderLib(mod_name, path)
            except:
                pass

    def getRecorderPath(self):
        return self._recorder_path

    def _findRecorderLibNames(self, recorder_path=None):
        paths = recorder_path or self.getRecorderPath()
        ret = {}
        for path in reversed(paths):
            try:
                for dir in os.listdir(path):
                    name, ext = os.path.splitext(dir)
                    if name.startswith("_"):
                        continue
                    if ext.endswith('.py'):
                        full_path = os.path.abspath(os.path.join(path, dir))
                        ret[name] = full_path
            except:
                self.debug("'%s' is not a valid path" % path)
        return ret

    def loadRecorderLib(self, module_name, path=None):
        """Loads the given library(=module) names.

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

        if module_name in self._modules:
            return None

        mod_manager = ModuleManager()
        try:
            self._modules[module_name] = mod_manager.loadModule(module_name,
                                                                path)
        except:
            self.error("Error adding recorder %s", module_name)
            self.debug("Details:", exc_info=1)

    def getRecorderClasses(self, filter=DataRecorder):
        """ Returns a :obj:`dict` containing information about recorder classes.

        :param filter: a klass of a valid type of Recorder
        :type filter: obj

        :return: a :obj:`dict` containing information about recorder classes
        :rtype:
            :obj:`dict`\<:obj:`str`\, :class:`DataRecorder`\>
        """
        recorder_klasses = {}
        # TODO This is a template
        #
        # TODO get all classes from the _recorder_path and filter them.
        #if issubclass(klass, filter):
        #    recorder_klasses[name] = klass
        return recorder_klasses

    def getRecorderClass(self, klass_name):
        """ Return the Recorder class for the given class name.
        :param klass_name: Name of the recorder class.
        :type klass_name: str
        :return:  a :obj:`class` class of recorder or None if it does not exist
        :rtype:
            :obj:`class:`DataRecorder`\>
        """
        recorder_klasses = self.getRecorderClasses()
        return recorder_klasses.get(klass_name, None)
