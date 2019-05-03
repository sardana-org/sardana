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

"""This module contains tests for HDF5 recorders."""

import os
import tempfile
from datetime import datetime

import h5py
import numpy
from taurus.external.unittest import TestCase, expectedFailure

from sardana.macroserver.scan import ColumnDesc
from sardana.macroserver.recorders.h5storage import NXscanH5_FileRecorder

COL1_NAME = "col1"


class RecordList(dict):

    def __init__(self, env):
        self._env = env

    def getEnviron(self):
        return self._env


class Record(object):

    def __init__(self, data, recordno=0):
        self.data = data
        self.recordno = recordno


class TestNXscanH5_FileRecorder(TestCase):

    def setUp(self):
        self.dir_name = tempfile.gettempdir()
        self.path = os.path.join(self.dir_name, "test.h5")
        try:
            os.remove(self.path)  # remove file just in case
        except OSError:
            pass

        self.env = {
            "serialno": 0,
            "starttime": None,
            "title": "test",
            "user": "user",
            "datadesc": None,
            "endtime": None
        }
        self.record_list = RecordList(self.env)

    def test_dtype_float64(self):
        """Test creation of dataset with float64 data type"""
        nb_records = 1
        # create description of channel data
        data_desc = [
            ColumnDesc(name=COL1_NAME, dtype="float64", shape=tuple())
        ]
        self.env["datadesc"] = data_desc

        # simulate sardana scan
        recorder = NXscanH5_FileRecorder(filename=self.path)
        self.env["starttime"] = datetime.now()
        recorder._startRecordList(self.record_list)
        for i in range(nb_records):
            record = Record({COL1_NAME: 0.1}, i)
            recorder._writeRecord(record)
        self.env["endtime"] = datetime.now()
        recorder._endRecordList(self.record_list)

        # assert if reading datasets from the sardana file access to the
        # dataset of the partial files
        file_ = h5py.File(self.path)
        for i in range(nb_records):
            expected_data = 0.1
            data = file_["entry0"]["measurement"][COL1_NAME][i]
            msg = "data does not match"
            self.assertEqual(data, expected_data, msg)

    def test_dtype_str(self):
        """Test creation of dataset with str data type"""
        nb_records = 1
        # create description of channel data
        data_desc = [
            ColumnDesc(name=COL1_NAME, dtype="str", shape=tuple())
        ]
        self.env["datadesc"] = data_desc

        # simulate sardana scan
        recorder = NXscanH5_FileRecorder(filename=self.path)
        self.env["starttime"] = datetime.now()
        recorder._startRecordList(self.record_list)
        for i in range(nb_records):
            record = Record({COL1_NAME: "file:///tmp/test.edf"}, i)
            recorder._writeRecord(record)
        self.env["endtime"] = datetime.now()
        recorder._endRecordList(self.record_list)

        # assert if reading datasets from the sardana file access to the
        # dataset of the partial files
        file_ = h5py.File(self.path)
        for i in range(nb_records):
            expected_data = "file:///tmp/test.edf"
            data = file_["entry0"]["measurement"][COL1_NAME][i]
            msg = "data does not match"
            self.assertEqual(data, expected_data, msg)

    @expectedFailure
    def test_VDS(self):
        """Test creation of VDS when channel reports URIs (str) of h5file
        scheme in a simulated sardana scan (3 points).
        """
        try:
            h5py.VirtualLayout
        except AttributeError:
            self.skipTest("VDS not available in this version of h5py")
        nb_records = 3
        # create partial files
        part_file_name_pattern = "test_vds_part{0}.h5"
        part_file_paths = []
        for i in range(nb_records):
            path = os.path.join(self.dir_name,
                                part_file_name_pattern.format(i))
            part_file_paths.append(path)
            part_file = h5py.File(path, "w")
            img = numpy.array([[i, i], [i, i]])
            part_file.create_dataset("dataset", data=img)
            part_file.flush()
            part_file.close()
        try:
            # create description of channel data
            data_desc = [
                ColumnDesc(name=COL1_NAME, dtype="str", shape=tuple())
            ]
            self.env["datadesc"] = data_desc

            # simulate sardana scan
            recorder = NXscanH5_FileRecorder(filename=self.path)
            self.env["starttime"] = datetime.now()
            recorder._startRecordList(self.record_list)
            for i in range(nb_records):
                ref = "h5file://" + part_file_paths[i]
                record = Record({COL1_NAME: ref}, i)
                recorder._writeRecord(record)
            self.env["endtime"] = datetime.now()
            recorder._endRecordList(self.record_list)

            # assert if reading datasets from the sardana file access to the
            # dataset of the partial files
            file_ = h5py.File(self.path)
            for i in range(nb_records):
                expected_img = numpy.array([[i, i], [i, i]])
                img = file_["entry0"]["measurement"][COL1_NAME][i]
                msg = "VDS extracted image does not match"
                # TODO: check if this assert works well
                numpy.testing.assert_array_equal(img, expected_img, msg)
        finally:
            # remove partial files
            for path in part_file_paths:
                os.remove(path)

    def tearDown(self):
        try:
            os.remove(self.path)
        except OSError:
            pass
