"""
Create a stand-alone ScanData object to which we can call addRecord
Do what gscan does for creating the ScanData, without using gscan.

- generate a minimum ScanDataEnvironment
- create a datahandler with a NXScan recorder only
- check if we can call addRecord and that a record is written in the recorder
- Check that we can call addData
"""

__all__ = ['createScanDataEnvironment']


import time
from datetime import date

from sardana.macroserver.scan.recorder import DataHandler
from sardana.macroserver.scan.recorder.storage import NXscan_FileRecorder

from sardana.macroserver.scan.scandata import (ScanData, ScanDataEnvironment, 
                                               ColumnDesc)

import threading
import numpy


class DummyEventSource(threading.Thread):

    def __init__(self, name, scanData, values, intervals=None):
        threading.Thread.__init__(self, name=name)
        self.scan_data = scanData
        self.values = values
        self.intervals = intervals or numpy.random.rand(len(self.values))

    def run(self):
        i = 0
        for v,t in zip(self.values, self.intervals):
            time.sleep(t)
            self.scan_data.addData(v)

    def get_obj(self):
        return self

def createScanDataEnvironment(columns, ScanDir='/tmp/', 
                                            ScanFile='data_nxs.hdf5'):

    serialno = 1
    env = ScanDataEnvironment(
            { 'serialno' : serialno,
                  'user' : "USER_NAME",
                 'title' : "title_macro" } )
    
    env['name'] = "env_name"
    env['estimatedtime'] = -1.0
    env['ScanDir'] = ScanDir
    env['ScanFile'] = ScanFile
    env['total_scan_intervals'] = -1.0

    today = date.today()
    env['datetime'] = today
    env['starttime'] = today
    env['endtime'] = today

    # Initialize the data_desc list (and add the point number column)
    data_desc = []
    column_master = ColumnDesc(name='point_nb', 
                               label='#Pt No', dtype='int64')
    data_desc.append(column_master)

    for i in range(len(columns)):
        col = columns[i]
        column = ColumnDesc(name=col, label=col, dtype='float64')
        data_desc.append(column)

    env['datadesc'] = data_desc
    return env


def main():
    DH = DataHandler()
    file_name = "/tmp/data_nxs.hdf5"
    NXrecorder = NXscan_FileRecorder(filename=file_name, 
                                         macro="dscan", overwrite=True)
    DH.addRecorder(NXrecorder)

    columns = ['ch1', 'ch2']
    ScanDir = '/tmp/'
    ScanFile = 'data_nxs.hdf5'
    
    env = createScanDataEnvironment(columns, ScanDir, ScanFile)
    newScanData = ScanData(environment=env, data_handler=DH)


    data1 = [
        {'label':'ch1', 'data':[10.0, 6.0, 3.4]},
        {'label':'ch1', 'data':[10.0, 6.0, 3.4]},
        {'label':'ch1', 'data':[10.0, 3.4]},
        {'label':'ch1', 'data':[10.0, 6.0, 3.4]},
        {'label':'ch1', 'data':[10.0, 3.4]}
    ]
    data2 = [
        {'label':'ch2', 'data':[9.2, 7.4]},
        {'label':'ch2', 'data':[1.1]}
    ]
    srcs = [
            DummyEventSource('s1', newScanData, data1),
            DummyEventSource('s2', newScanData, data2)
            ]
    newScanData.start()
    for s in srcs:
        s.start()
    for s in srcs:
        s.join()

    newScanData.end()

if __name__=="__main__":
    main()

