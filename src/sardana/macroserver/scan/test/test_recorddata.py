#!/usr/bin/env python

##############################################################################
##
## This file is part of Sardana
##
## http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
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

import nxs
import math
import os
import numpy
from taurus.external import unittest
from taurus.test import insertTest
from sardana.macroserver.scan.scandata import ScanData
from sardana.macroserver.scan.recorder import DataHandler
from sardana.macroserver.scan.recorder.storage import NXscan_FileRecorder
from sardana.macroserver.scan.test.helper import (createScanDataEnvironment,
                                                  DummyEventSource)

data = {
    'ch1':[0, None, 2, None, 4, [5, 6, 7]],
    'ch2':[0, 1, None, 4, [5, 6], 7]
    }

@insertTest(helper_name='recorddata', data=data)
class ScanDataTestCase(unittest.TestCase):
    """Use ScanData, DataHandler and ScanDataEnvironment in order to record
    data and verify that the stored data in the NeXus file corresponds with
    the initial data that has been sent for storage.
    """
    def setUp(self):
        """SetUp
        """
        unittest.TestCase.setUp(self)
        self.data_handler = DataHandler()
        self.file_name = "/tmp/data_nxs.hdf5"
        NXrecorder = NXscan_FileRecorder(filename=self.file_name, 
                                             macro="dscan", overwrite=True)
        self.data_handler.addRecorder(NXrecorder)

    def prepareScandData(self, data):
        scan_dir, scan_file = os.path.split(self.file_name)
        env = createScanDataEnvironment(data.keys(), scan_dir, scan_file)
        self.scan_data = ScanData(environment=env,
                                 data_handler=self.data_handler)
        self.srcs = []
        self.inputs = {}
        max_len = -1
        for name, dat in data.items():
            des = DummyEventSource(name, self.scan_data, dat)
            self.srcs.append(des)
            input_list = []
            for e in dat:
                if type(e) is list:
                    input_list.extend(e)
                else:
                    input_list.append(e)
            self.inputs[name] = input_list
            len_il = len(input_list)
            if max_len < len_il:
                max_len = len_il
        # Pading the list to fill it with none
        for name, dat in self.inputs.items():
            diff = max_len - len(dat)
            self.inputs[name] = dat + [None]*diff

    def recorddata(self, data):
        """Verify that the data sent for storage is equal 
           to the actual data present in the created NeXus file.
        """
        self.prepareScandData(data)
        # Fill the recoder
        self.scan_data.start()
        for s in self.srcs:
            s.start()
        for s in self.srcs:
            s.join()
        self.scan_data.end()
        # Test the generated nxs file
        f = nxs.load(self.file_name)
        m = f['entry1']['measurement']
        for chn in data.keys():
            chn_data = m[chn].nxdata
            #check the data element by element
            msg = ('%s: input data is not equal to stored data. '
                   'Expected: %s , Read: %s' %\
                   (chn, self.inputs[chn], chn_data))
            self.assertEqual(chn_data, self.inputs[chn], msg)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

