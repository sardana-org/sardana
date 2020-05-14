#!/usr/bin/env python

##############################################################################
##
# This file is part of Sardana
##
# http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
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

import math
import os
import unittest
from taurus.test import insertTest
from sardana.macroserver.scan.scandata import ScanData
from sardana.macroserver.scan.recorder import DataHandler
from sardana.macroserver.recorders.storage import NXscan_FileRecorder
from sardana.macroserver.scan.test.helper import (createScanDataEnvironment,
                                                  DummyEventSource)

data = {
    'ch1': [10., float('Nan'), 12., [float('Nan')] * 3, 16.],
    'ch2': [20., 21., [22., 23., 24.], float('Nan'), [26.]],
    'ch3': [float('Nan'), float('Nan'), 32., 33., 34., 35., 36.]
}

data1 = {
    'ch1': [10., float('Nan'), 12., [float('Nan')] * 3, 16.],
    'ch2': [20., 21., [22., 23., 24.], float('Nan'), [26.]],
    'ch3': [float('Nan'), float('Nan'), 32., 33., 34., 35.]
}

data3 = {
    'ch1': [10., float('Nan'), 12., [float('Nan')] * 3, 16.],
    'ch2': [20., 21., [22., 23., 24.], float('Nan'), [26.]]
}


@insertTest(helper_name='recorddata', data=data1, apply_interpolation=False)
@insertTest(helper_name='recorddata', data=data, apply_interpolation=False)
@insertTest(helper_name='zeroOrderInterpolation', data=data3,
            apply_interpolation=True)
class ScanDataTestCase(unittest.TestCase):
    """Use ScanData, DataHandler and ScanDataEnvironment in order to record
    data and verify that the stored data in the NeXus file corresponds with
    the initial data that has been sent for storage.
    """

    def setUp(self):
        """SetUp
        """
        try:
            import nxs
            self.nxs = nxs
        except ImportError:
            self.skipTest("nxs module is not available")
        # In real world addData are always called sequentially.
        # This test was developed assuming that these may arrive in
        # parallel and that addData would protect the critical section, this
        # is no more the case.
        self.skipTest("this test wrongly assumes that data may arrive in "
                      "parallel")

        unittest.TestCase.setUp(self)
        self.data_handler = DataHandler()
        self.file_name = "/tmp/data_nxs.hdf5"
        nx_recorder = NXscan_FileRecorder(filename=self.file_name,
                                          macro="dscan", overwrite=True)
        self.data_handler.addRecorder(nx_recorder)

    def prepareScandData(self, data, apply_interpolation=False):
        scan_dir, scan_file = os.path.split(self.file_name)
        env = createScanDataEnvironment(list(data.keys()), scan_dir, scan_file)
        self.scan_data = ScanData(environment=env,
                                  data_handler=self.data_handler,
                                  apply_interpolation=apply_interpolation)
        self.srcs = []
        self.inputs = {}
        max_len = -1
        for name, dat in list(data.items()):
            des = DummyEventSource(name, self.scan_data, dat, [0] * len(dat))
            self.srcs.append(des)
            input_list = []
            for e in dat:
                if isinstance(e, list):
                    input_list.extend(e)
                else:
                    input_list.append(e)
            self.inputs[name] = input_list
            len_il = len(input_list)
            if max_len < len_il:
                max_len = len_il
        # Pading the list to fill it with float('Nan')
        for name, dat in list(self.inputs.items()):
            diff = max_len - len(dat)
            self.inputs[name] = dat + [float('Nan')] * diff

    def recorddata(self, data, apply_interpolation):
        """Verify that the data sent for storage is equal
           to the actual data present in the created NeXus file.
        """
        self.prepareScandData(data, apply_interpolation)
        # Fill the recoder
        self.scan_data.start()
        for s in self.srcs:
            s.start()
        for s in self.srcs:
            s.join()
        self.scan_data.end()
        # Test the generated nxs file
        f = self.nxs.load(self.file_name)
        m = f['entry1']['measurement']
        for chn in list(data.keys()):
            chn_data = m[chn].nxdata
            # check the data element by element
            for i in range(len(chn_data)):
                msg = ('%s: input data is not equal to stored data. '
                       'Expected: %s , Read: %s' %
                       (chn, self.inputs[chn][i], chn_data[i]))
                if math.isnan(chn_data[i]) and \
                        math.isnan(self.inputs[chn][i]):
                    continue
                self.assertEqual(chn_data[i], self.inputs[chn][i], msg)

    def zeroOrderInterpolation(self, data, apply_interpolation):
        """Verify that the data write in the NeXus file has been
           modified using a zero order interpolation.
        """
        self.prepareScandData(data, apply_interpolation)
        # Fill the recoder
        self.scan_data.start()
        for s in self.srcs:
            s.start()
        for s in self.srcs:
            s.join()
        self.scan_data.end()
        # Test the generated nxs file
        f = self.nxs.load(self.file_name)
        m = f['entry1']['measurement']
        for chn in list(data.keys()):
            chn_data = m[chn].nxdata
            # check the interpolations
            for i in range(len(chn_data)):
                msg = '%s[%s]: has a "Nan" value.' % (chn, i)
                if math.isnan(self.inputs[chn][i]):
                    self.assertFalse(math.isnan(chn_data[i]), msg)
                    if i > 0:
                        msg = ('%s[%s]: data has not been interpolated '
                               'properly. Expected: %s , Read: %s' %
                               (chn, i, chn_data[i], chn_data[i - 1]))
                        self.assertEqual(chn_data[i - 1], chn_data[i], msg)

    def tearDown(self):
        unittest.TestCase.tearDown(self)
