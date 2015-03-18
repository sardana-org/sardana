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
import numpy
from taurus.external import unittest
from sardana.macroserver.scan.scandata import ScanData
from sardana.macroserver.scan.recorder import DataHandler
from sardana.macroserver.scan.recorder.storage import NXscan_FileRecorder
from sardana.macroserver.scan.test.helper import (createScanDataEnvironment,
                                                               DummyEventSource)
from taurus.test import insertTest

data1 = [
            {'label':'ch1', 'data':[10.0, 6.0, 3.4], 'index':[1, 2, 3]},
            {'label':'ch1', 'data':[10.0, 6.0, 3.4], 'index':[6, 7, 8]}
]
data2 = [
            {'label':'ch2', 'data':[9.2, 7.4], 'index':[1, 3]},
            {'label':'ch2', 'data':[1.1], 'index':[2]},
            {'label':'ch2', 'data':[10.0, 3.4], 'index':[4, 7]}
]

@insertTest(helper_name='recorddata', ldata=[data1, data2])
class ScanDataTestCase(unittest.TestCase):
    """Use ScanData, DataHandler and ScanDataEnvironment in order to record
    data and verify that the stored data in the NeXus file corresponds with
    the initial data that has been sent for storage.
    """

    def setUp(self):
        """SetUp
        """
        unittest.TestCase.setUp(self)
        self.DH = DataHandler()
        self.file_name = "/tmp/data_nxs.hdf5"
        NXrecorder = NXscan_FileRecorder(filename=self.file_name, 
                                             macro="dscan", overwrite=True)
        self.DH.addRecorder(NXrecorder)

    def prepareScandData(self, ldata):
        ScanDir = '/tmp/'
        ScanFile = 'data_nxs.hdf5'
        self.input_chns = [d[0]['label'] for d in ldata]
        env = createScanDataEnvironment(self.input_chns, ScanDir, ScanFile)
        self.scanData = ScanData(environment=env, data_handler=self.DH)

        self.srcs = []
        self.inputs = []
        self.max_index = -1
        for data in ldata:
            name = '_s_%s_' % d[0]['label']
            des = DummyEventSource(name, self.scanData, data)
            self.srcs.append(des)
            # Prepare the input
            data_input = dict(label='', data=[], index=[])
            for chuck in data:
                data_input['label'] = chuck['label']
                data_input['data'] += chuck['data']
                data_input['index'] += chuck['index']
                _max = max(data_input['index'])
                if self.max_index < _max:
                    self.max_index = _max
            self.inputs.append(data_input)
        # generate the final table
        self.table = []
        for input in self.inputs:
            v = numpy.array([numpy.nan]*self.max_index)
            for i in range(len(input['index'])):
                index = input['index'][i] - 1
                data = input['data'][i]
                v[index] = data
            self.table.append(v)

    def recorddata(self, ldata):
        """Verify that the data sent for storage is equal 
           to the actual data present in the created NeXus file.
        """
        self.prepareScandData(ldata)
        # Fill the recoder
        self.scanData.start()
        for s in self.srcs:
            s.start()
        for s in self.srcs:
            s.join()
        self.scanData.end()
        # Test the generated nxs file
        nxsfile = nxs.open(self.file_name,'r')
        nxsfile.opengroup('entry1')    
        nxsfile.opengroup('measurement')
        chn = 0
        chn_names = []
        for entry in nxsfile.getentries():
            if (entry != "pre_scan_snapshot" and entry != "Pt_No"):
                inputdata = self.table[chn]
                nxsfile.opendata(entry)
                datastored = nxsfile.getdata()
                datastored_length = len(datastored)
                msg = ("For %s: the input data length is not "
                                          "equal to stored data length" % entry)
                self.assertEqual(datastored_length, self.max_index, msg)

                for i in range(len(datastored)):
                    msg = ('%s: input data is not equal to stored data. '
                                            'Expected: %s , Read: %s' %\
                                                 (entry, inputdata, datastored))
                    self.assertEqual(inputdata[i], datastored[i], msg)
                nxsfile.closedata()
                chn += 1
                chn_names.append(entry)

        msg = ('The number of read channels is not equal to input channels '
                                   'Input channels: %s, Read channels %s' %\
                                                   (self.input_chns, chn_names))
        self.assertEqual(chn, len(self.input_chns), msg)
        nxsfile.closegroup()
        nxsfile.closegroup()
        nxsfile.close()

    def tearDown(self):
        unittest.TestCase.tearDown(self)

