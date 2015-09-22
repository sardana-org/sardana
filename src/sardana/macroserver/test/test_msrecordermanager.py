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

import os

from taurus.external import unittest
from taurus.test import insertTest

from sardana.macroserver.macroserver import MacroServer
from sardana.macroserver.scan.recorder import DataRecorder
from sardana.macroserver.scan.recorder.storage import FileRecorder


_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_FAKE_RECORDER_DIR = os.path.join(_TEST_DIR, 'res')


@insertTest(helper_name='getRecorderClass', klass_name="JsonRecorder")
@insertTest(helper_name='getRecorderClass', klass_name="FIO_FileRecorder")
@insertTest(helper_name='getRecorderClass', klass_name="FakeScanRecorder",
            extra_paths=[_FAKE_RECORDER_DIR])
@insertTest(helper_name='getRecorderClasses', filter=FileRecorder,
            extra_paths=[_FAKE_RECORDER_DIR], extra_recorders=1)
@insertTest(helper_name='getRecorderClasses', extra_paths=[_FAKE_RECORDER_DIR],
            extra_recorders=1)
@insertTest(helper_name='getRecorderPath',
            recorder_path=["/tmp/foo", "#/tmp/foo2"], expected_num_path=2)
@insertTest(helper_name='getRecorderPath', recorder_path=["/tmp/foo:/tmp/foo2"],
            expected_num_path=3)
@insertTest(helper_name='getRecorderPath', recorder_path=["/tmp/foo"],
            expected_num_path=2)
@insertTest(helper_name='getRecorderPath')
class RecorderManagerTest(unittest.TestCase):
    # Just an hardcode fullname for create an instance of MacroServer.
    # This macroserver does not need to be defined.
    ms_fullname = "macroserver/demo1/1"

    def setUp(self):
        name = self.ms_fullname.split("/")[1]
        self._macro_server = MacroServer(self.ms_fullname, name, macro_path=[],
                                    recorder_path=[])
        self.manager = self._macro_server.recorder_manager

    def tearDown(self):
        pass

    def _updateRecorderManager(self, recorder_path):
        """Helper for update the sardana recorder manager
        """
        self.manager.setRecorderPath(recorder_path)

    def getRecorderPath(self, recorder_path=[], expected_num_path=1):
        """Helper for test the number of reading recorder paths.
        The number of reading path sould be len(recorder_path) + 1
        """
        if recorder_path is not []:
            self._updateRecorderManager(recorder_path)
        # Get the list of recorder path(s)
        paths = self.manager.getRecorderPath()
        num_paths = len(paths)
        msg = "The number of paths do not concur, read %d, expected %d" %\
              (num_paths, expected_num_path)
        self.assertEqual(num_paths, expected_num_path, msg)

    def getRecorderClasses(self, filter=DataRecorder, extra_paths=None,
                           extra_recorders=0):
        """Helper for test getRecorderClasses method of the record Manager.
        """
        # Use default recorders paths
        self.manager.setRecorderPath([])
        default_recorder_klass = self.manager.getRecorderClasses(filter)
        # Add extra recorders paths
        if extra_paths is not None:
            self.manager.setRecorderPath(extra_paths)
        recorder_klass = self.manager.getRecorderClasses(filter)
        n_default_recorders = len(default_recorder_klass)
        n_recorders = len(recorder_klass)
        total_recorders = n_default_recorders + extra_recorders
        msg = "Number of recorder classes do not concur, expected %d, get %d" %\
              (total_recorders, n_recorders)
        self.assertEqual(total_recorders, n_recorders, msg)

    def getRecorderClass(self, klass_name, extra_paths=[]):
        """Helper for test getRecorderClass method of the record Manager.
        """
        self.manager.setRecorderPath(extra_paths)
        klass = self.manager.getRecorderClass(klass_name)
        msg = "Recoder manager does not found the class %s" %(klass_name)
        self.assertNotEqual(klass, None, msg)
        _name = klass.__name__
        msg = "The class %s is not subclass of DataRecorder" %(_name)
        self.assertTrue(issubclass(klass, DataRecorder), msg)
        msg = "The class name giveb by the recorder manager is different." +\
              "Expected %s, get %s" %(klass_name, _name)
        self.assertEqual(_name, klass_name, msg)