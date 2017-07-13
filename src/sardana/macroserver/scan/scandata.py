#!/usr/bin/env python

##############################################################################
##
# This file is part of Sardana
##
# http://www.sardana-controls.org/
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

"""This is the macro server scan data module"""

__all__ = ["ColumnDesc", "MoveableDesc", "Record", "RecordEnvironment",
           "ScanDataEnvironment", "RecordList", "ScanData", "ScanFactory"]

import copy
import math

from taurus.core.util.singleton import Singleton

from sardana.macroserver.scan.recorder import DataHandler
from threading import RLock


class ColumnDesc(object):
    """The description of a column for a Record"""

    _TYPE_MAP = {"short": "int16",
                 "ushort": "uint16"}
    _shape = []
    _dtype = 'float64'

    def __init__(self, **kwargs):
        """Expected keywords are:

               - name (str, mandatory): unique column name
               - label (str, optional): column label (defaults to name)
               - dtype (str, optional): data type. Defaults to 'float64'
               - shape (seq, optional): data shape. Defaults to []

        Any keyword not in the previous list will be converted to a member of
        the :class:`ColumnDesc`"""
        # enforce that the mandatory arguments are present
        try:
            self.name = kwargs.pop('name')
        except:
            raise TypeError('"name" parameter is mandatory')

        # make sure that at least the required members exist
        self.label = kwargs.pop('label', self.name)
        self.setDtype(kwargs.pop('dtype', self.__class__._dtype))
        self.setShape(kwargs.pop('shape', self.__class__._shape))

        # create members of the ColumnDesc class using the remaining keyword
        # args
        self._extra_kwargs = kwargs
        self.__dict__.update(kwargs)

    def getShape(self):
        return self._shape

    def setShape(self, shape):
        self._shape = self._simplifyShape(shape)

    def getDtype(self):
        return self._dtype

    def setDtype(self, dtype):
        self._dtype = self.tr(dtype)

    shape = property(getShape, setShape)
    dtype = property(getDtype, setDtype)

    @staticmethod
    def _simplifyShape(s):
        '''the idea is to strip the shape of useless "ones" at the beginning.
        For example:

            - () -> ()
            - (1,) -> ()
            - (1,1,1,1) -> ()
            - (2,) -> (2)
            - (1,2) -> (2)
            - (1,2,3) -> (2,3)
            - (2,3) -> (2,3)
            - (1,1,1,2,3) -> (2,3)
            - (3,1,1) -> (3,1,1)
        '''
        s = list(s)
        for i, e in enumerate(s):
            if e > 1:
                return s[i:]
        return []

    def tr(self, dtype):
        return self._TYPE_MAP.get(dtype, dtype)

    def toDict(self):
        '''creates a dictionary representation of the record'''
        d = copy.deepcopy(self._extra_kwargs)
        for k in ['name', 'label', 'dtype', 'shape']:
            d[k] = getattr(self, k)
        return d

    def clone(self):
        return copy.deepcopy(self)
        # return self.__class__(**self.toDict())


class MoveableDesc(ColumnDesc):

    def __init__(self, **kwargs):
        """Expected keywords are:

               - moveable (Moveable, mandatory): moveable object
               - name (str, optional): column name (defaults to moveable name)
               - label (str, optional): column label (defaults to moveable
                 name)
               - dtype (str, optional): data type. Defaults to 'float64'
               - shape (seq, optional): data shape. Defaults to (1,)
               - instrument (Instrument, optional): instrument object.
                 Defaults to moveable instrument"""

        try:
            self.moveable = moveable = kwargs.pop('moveable')
        except KeyError:
            raise TypeError("moveable parameter is mandatory")
        name = moveable.getName()
        kwargs['name'] = kwargs.get('name', name)
        kwargs['label'] = kwargs.get('label', name)
        kwargs['instrument'] = kwargs.get('instrument', moveable.instrument)

        self.min_value = kwargs.get('min_value')
        self.max_value = kwargs.get('max_value')
        self.is_reference = kwargs.get('is_reference')
        ColumnDesc.__init__(self, **kwargs)

    def toDict(self):
        d = ColumnDesc.toDict(self)
        d['min_value'] = self.min_value
        d['max_value'] = self.max_value
        d['is_reference'] = self.is_reference
        return d

    def clone(self):
        return self.__class__(moveable=self.moveable, **self.toDict())


class Record(object):
    """ One record is a set of values measured at the same time.

    The Record.data member will be
    a dictionary containing:
      - 'point_nb' : (int) the point number of the scan
      - for each column of the scan (motor or counter), a key with the
      corresponding column name (str) and the corresponding value
    """

    def __init__(self, data):
        self.recordno = 0
        self.data = data
        self.complete = 0
        self.written = 0

    def setRecordNo(self, recordno):
        self.recordno = recordno

    def setComplete(self):
        self.complete = 1

    def setWritten(self):
        self.written = 1


class RecordEnvironment(dict):
    """  A RecordEnvironment is a set of arbitrary pairs of type
    label/value in the form of a dictionary.
    """
    __needed = ['title', 'labels']  # @TODO: it seems that this has changed
    # now labels are separated in moveables and counters

    def isValid(self):
        """ Check valid environment = all needed keys present """

        if not self.needed:
            return 1

        for ky in self.needed + self.__needed:
            if ky not in self.keys():
                return 0
        else:
            return 1


class ScanDataEnvironment(RecordEnvironment):
    """It describes a recordlist and its environment

    A recordlist environment contains a number of predefined label/value pairs
    Values can be either a string, a numeric value or a list of strings,
    numbers

    title:     mandatory
    labels:    mandatory. label for each of the fields in a record of the
               recordlist
    fielddesc: description of the content of each of the fields in a record.
               Can be used to affect the way the field is saved by the
               recorder. If not present all fields are by default of type
               FLOAT and FORMAT ".8g"
    """
    needed = ['title', 'labels', 'user']


class RecordList(dict):
    """  A RecordList is a set of records: for example a scan.
    It is composed of a environment and a list of records"""

    def __init__(self, datahandler, environ=None, apply_interpolation=False,
                 initial_data=None):

        self.datahandler = datahandler
        self.applyInterpolation = apply_interpolation
        self.initial_data = initial_data
        if environ is None:
            self.environ = RecordEnvironment()
        else:
            self.environ = environ
        self.records = []
        self.rlock = RLock()
        # currentIndex indicates the place in the records list
        # where the next completed record will be written
        self.currentIndex = 0

    # make it pickable
    def __getstate__(self):
        return dict(datahandler=None, environ=None, records=self.records)

    def setEnviron(self, environ):
        self.environ = environ

    def updateEnviron(self, environ):
        self.environ.update(environ)

    def setEnvironValue(self, name, value):
        self.environ[name] = value

    def getEnvironValue(self, name):
        return self.environ[name]

    def getEnviron(self):
        return self.environ

    def start(self):
        self.recordno = 0
        # @TODO: it is necessary only by continuous scan
        # think how to separate this two cases
        self.columnIndexDict = {}
        self.labels = []
        self.refMoveablesLabels = []
        self.channelLabels = []
        self.currentIndex = 0
        self._mylabel = []

        for dataDesc in self.getEnvironValue('datadesc'):
            if isinstance(dataDesc, MoveableDesc):
                self.refMoveablesLabels.append(dataDesc.name)
            else:
                name = dataDesc.name
                if not name in ('point_nb', 'timestamp'):
                    self.channelLabels.append(name)
            self.labels.append(dataDesc.name)
        for label in self.labels:
            self.columnIndexDict[label] = 0
        ####
        self.datahandler.startRecordList(self)

    def initRecord(self):
        '''Init a dummy record and add it to the records list.
        A dummy record has:
           - point_nb of the consecutive record
           - each column initialized with NaN
           - each moveable initialized with None
        '''
        recordno = self.recordno
        if self.initial_data and self.initial_data.has_key(recordno):
            initial_data = self.initial_data.get(recordno)
        else:
            initial_data = dict()
        rc = Record({'point_nb': recordno})
        rc.data['timestamp'] = initial_data.get('timestamp')
        rc.setRecordNo(self.recordno)
        for label in self.channelLabels:
            rc.data[label] = initial_data.get(label, float('NaN'))
        for label in self.refMoveablesLabels:
            rc.data[label] = initial_data.get(label)
        self.records.append(rc)
        self.recordno += 1

    def initRecords(self, nb_records):
        '''Call nb_records times initRecord method
        '''
        for _ in range(nb_records):
            self.initRecord()

    def addRecord(self, record):
        rc = Record(record)
        rc.setRecordNo(self.recordno)
        self.records.append(rc)
        self[self.recordno] = rc
        self.recordno += 1
        self.datahandler.addRecord(self, rc)
        self.currentIndex += 1

    def applyZeroOrderInterpolation(self, record):
        ''' Apply a zero order interpolation to the given record
        '''
        if self.currentIndex > 0:
            data = record.data
            prev_data = self.records[self.currentIndex - 1].data
            for k, v in data.items():
                if v is None:
                    continue
                # numpy arrays (1D or 2D) are valid values and does not require
                # interpolation but provokes TypeError
                try:
                    interpolate = math.isnan(v)
                except TypeError:
                    interpolate = False
                if interpolate:
                    data[k] = prev_data[k]

    def addData(self, data):
        """Adds data to the record list

        :param data: dictionary with two mandatory elements: label - string
                     and data - list of values
        :type data:  dict"""
        with self.rlock:
            label = data['label']
            rawData = data['data']
            idxs = data['index']

            maxIdx = max(idxs)
            recordsLen = len(self.records)
            # Calculate missing records
            missingRecords = recordsLen - (maxIdx + 1)
            # TODO: implement proper handling of timestamps and moveables
            if missingRecords < 0:
                missingRecords = abs(missingRecords)
                self.initRecords(missingRecords)
            for idx, value in zip(idxs, rawData):
                rc = self.records[idx]
                rc.setRecordNo(idx)
                rc.data[label] = value
                self.columnIndexDict[label] = idx + 1
            self.tryToAdd(idx, label)

    def tryToAdd(self, idx, label):
        start = self.currentIndex
        for i in range(start, idx + 1):
            if self.isRecordCompleted(i):
                rc = self.records[i]
                self[self.currentIndex] = rc
                if self.applyInterpolation:
                    self.applyZeroOrderInterpolation(rc)
                self.datahandler.addRecord(self, rc)
                self.currentIndex += 1

    def isRecordCompleted(self, recordno):
        rc = self.records[recordno]
        for label in self.channelLabels:
            if self.columnIndexDict[label] <= self.currentIndex:
                return False
        rc.completed = 1
        return True

    def addRecords(self, records):
        map(self.addRecord, records)

    def end(self):
        start = self.currentIndex
        for i in range(start, len(self.records)):
            rc = self.records[i]
            self[self.currentIndex] = rc
            if self.applyInterpolation:
                self.applyZeroOrderInterpolation(rc)
            self.datahandler.addRecord(self, rc)
            self.currentIndex += 1
        self.datahandler.endRecordList(self)

    def getDataHandler(self):
        return self.datahandler


class ScanData(RecordList):

    def __init__(self, environment=None, data_handler=None,
                 apply_interpolation=False):
        dh = data_handler or DataHandler()
        RecordList.__init__(self, dh, environment, apply_interpolation)


class ScanFactory(Singleton):

    def __init__(self):
        """ Initialization. Nothing to be done here for now."""
        pass

    def init(self, *args):
        """Singleton instance initialization."""
        pass

    def getDataHandler(self):
        return DataHandler()

    def getScanData(self, dh, apply_interpolation=False):
        return ScanData(data_handler=dh,
                        apply_interpolation=apply_interpolation)
