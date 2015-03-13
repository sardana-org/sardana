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
from taurus.external import unittest
from sardana.macroserver.scan.scandata import ScanData
from sardana.macroserver.scan.recorder import DataHandler
from sardana.macroserver.scan.recorder.storage import NXscan_FileRecorder
from sardana.macroserver.scan.test.helper import createScanDataEnvironment
from copy import deepcopy

class RecordDataTestCase(unittest.TestCase):
    """Use ScanData, DataHandler and ScanDataEnvironment in order to record
    data and verify that the stored data in the NeXus file corresponds with
    the initial data that has been sent for storage.
    """

    def setUp(self):
        """SetUp
        """
        unittest.TestCase.setUp(self)

        DH = DataHandler()
        self.file_name = "/tmp/data_nxs.hdf5"
        NXrecorder = NXscan_FileRecorder(filename=self.file_name, 
                                             macro="dscan", overwrite=True)
        DH.addRecorder(NXrecorder)

        columns = ['ch1', 'ch2']
        ScanDir = '/tmp/'
        ScanFile = 'data_nxs.hdf5'
        env = createScanDataEnvironment(columns, ScanDir, ScanFile)

        testScanData = ScanData(environment=env, data_handler=DH)
        testScanData.start()

        data1_initial = {'label':'ch1', 'data':[10.0, 6.0, 3.4]}
        data2_initial = {'label':'ch2', 'data':[9.2, 7.4]}
        data3_initial = {'label':'ch2', 'data':[1.1]}

        testScanData.addData(data1_initial)
        testScanData.addData(data2_initial)
        testScanData.addData(data3_initial)

        testScanData.end()

        data_ch1_input = deepcopy(data1_initial)
        data_ch2_input = deepcopy(data2_initial)
        data_ch2_input['data'] = data2_initial['data'] + data3_initial['data']
        self.inputs = [data_ch1_input, data_ch2_input]
          
    def test_recorddata(self):
        """Verify that the data sent for storage is equal 
           to the actual data present in the created NeXus file.
        """

        nxsfile = nxs.open(self.file_name,'r')
        nxsfile.opengroup('entry1')    
        nxsfile.opengroup('measurement')

        lengths_data = []
        for i in range(len(self.inputs)):
            lengths_data.append(len(self.inputs[i]['data']))
        min_inputdata_length = min(lengths_data)

        c = 0
        for entry in nxsfile.getentries():
            if (entry!="pre_scan_snapshot" and entry!="Pt_No"):
                input_data = self.inputs[c]['data']
                print(input_data)
                nxsfile.opendata(entry)
                datastored = nxsfile.getdata()
                datastored_length = len(datastored)
                msg = ("For %s: data sent length is not " 
                       "equal to stored data length" % entry)

                self.assertEqual(datastored_length, min_inputdata_length, msg)

                for i in range(min_inputdata_length):
                    self.assertEqual(input_data[i], datastored[i], msg)
                
                nxsfile.closedata()
                c = c+1

        nxsfile.closegroup()
        nxsfile.closegroup()
        nxsfile.close()

    def tearDown(self):
        unittest.TestCase.tearDown(self)

