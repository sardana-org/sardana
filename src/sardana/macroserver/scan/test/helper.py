"""
Create a stand-alone ScanData object to which we can call addRecord
Do what gscan does for creating the ScanData, without using gscan.

- generate a minimum ScanDataEnvironment
- create a datahandler with a NXScan recorder only
- check if we can call addRecord and that a record is written in the recorder
- Check that we can call addData
"""

__all__ = ['createScanDataEnvironment', 'DummyEventSource']


import time
import datetime
import threading
import numpy
import os

from sardana.macroserver.scan.recorder import DataHandler
from sardana.macroserver.recorders.storage import NXscan_FileRecorder

from sardana.macroserver.scan.scandata import (ScanData, ScanDataEnvironment,
                                               ColumnDesc)


class DummyEventSource(threading.Thread):

    def __init__(self, name, scanData, values, intervals=None):
        threading.Thread.__init__(self, name=name)
        self.scan_data = scanData
        self.values = values
        self.intervals = intervals or numpy.random.rand(len(self.values))

    def run(self):
        i = 0
        for v, t in zip(self.values, self.intervals):
            try:
                idx = list(range(i, i + len(v)))
                i += len(v)
                skip = float('NaN') in v
            except TypeError:  # if v is not a list
                idx = [i]
                i += 1
                v = [v]
                skip = float('NaN') in v
            if skip:
                continue
            time.sleep(t)
            _dict = dict(value=v, index=idx, label=self.name)
            self.scan_data.addData(_dict)

    def get_obj(self):
        return self


def createScanDataEnvironment(columns, scanDir='/tmp/',
                              scanFile='data_nxs.hdf5'):

    serialno = 1
    env = ScanDataEnvironment(
        {'serialno': serialno,
         'user': "USER_NAME",
         'title': "title_macro"})

    env['name'] = "env_name"
    env['estimatedtime'] = -1.0
    env['ScanDir'] = scanDir
    env['ScanFile'] = scanFile
    env['total_scan_intervals'] = -1.0

    today = datetime.datetime.fromtimestamp(time.time())
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
    data_handler = DataHandler()
    file_name = "/tmp/data_nxs.hdf5"
    nx_recorder = NXscan_FileRecorder(filename=file_name,
                                      macro="dscan", overwrite=True)
    data_handler.addRecorder(nx_recorder)
    scan_dir, scan_file = os.path.split(file_name)
    columns = ['ch1', 'ch2']

    env = createScanDataEnvironment(columns, scan_dir, scan_file)
    scan_data = ScanData(environment=env, data_handler=data_handler)

    data1 = [10.0, [6.0, 3.4]]
    data2 = [10.0, None, None, 5]

    srcs = [
        DummyEventSource(columns[0], scan_data, data1),
        DummyEventSource(columns[1], scan_data, data2)
    ]
    scan_data.start()
    for s in srcs:
        s.start()
    for s in srcs:
        s.join()
    scan_data.end()
    # Test read nxs file
    import nxs
    f = nxs.load(file_name)
    m = f['entry1']['measurement']
    ch1 = m['ch1']
    print(ch1.nxdata)

if __name__ == "__main__":
    main()
