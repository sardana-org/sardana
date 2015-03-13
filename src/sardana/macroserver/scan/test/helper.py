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

import time
from datetime import date

from sardana.macroserver.scan.recorder import DataHandler
from sardana.macroserver.scan.recorder.storage import NXscan_FileRecorder

from sardana.macroserver.scan.scandata import (ScanData, ScanDataEnvironment, 
                                               ColumnDesc)

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
    newScanData.start()

    data1 = {'label':'ch1', 'data':[10.0, 6.0, 3.4]}
    data2 = {'label':'ch2', 'data':[9.2, 7.4]}
    data3 = {'label':'ch2', 'data':[1.1]}
    newScanData.addData(data1)
    newScanData.addData(data2)
    newScanData.addData(data3)

    newScanData.end()

if __name__=="__main__":
    main()



