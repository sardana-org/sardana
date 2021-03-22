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
import contextlib
import multiprocessing
from datetime import datetime

import h5py
import numpy
import pytest
from unittest import TestCase

from sardana.macroserver.scan import ColumnDesc
from sardana.macroserver.recorders.h5storage import NXscanH5_FileRecorder
from sardana.macroserver.recorders.h5util import _h5_file_handler


@contextlib.contextmanager
def h5_write_session(fname, swmr_mode=False):
    """Context manager for HDF5 file write session.

    Maintains HDF5 file opened for the context lifetime.
    It optionally can open the file as SWRM writer.

    :param fname: Path of the file to be opened
    :type fname: str
    :param swmr_mode: Use SWMR write mode
    :type swmr_mode: bool
    """
    fd = _h5_file_handler.open_file(fname, swmr_mode)
    try:
        yield fd
    finally:
        _h5_file_handler.close_file(fname)


COL1_NAME = "col1"

ENV = {
    "serialno": 0,
    "starttime": None,
    "title": "test",
    "user": "user",
    "datadesc": None,
    "endtime": None
}

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

        self.env = ENV
        self.record_list = RecordList(self.env)

    def test_dtype_float64(self):
        """Test creation of dataset with float64 data type"""
        nb_records = 1
        # create description of channel data
        data_desc = [
            ColumnDesc(name=COL1_NAME, label=COL1_NAME, dtype="float64",
                       shape=tuple())
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

    def test_value_ref(self):
        """Test creation of dataset with str data type"""
        nb_records = 1
        # create description of channel data
        data_desc = [
            ColumnDesc(name=COL1_NAME, label=COL1_NAME, dtype="float64",
                       shape=(1024, 1024), value_ref_enabled=True)
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
            dataset = "dataset"
            part_file.create_dataset(dataset, data=img)
            part_file.flush()
            part_file.close()
        try:
            # create description of channel data
            data_desc = [
                ColumnDesc(name=COL1_NAME, label=COL1_NAME, dtype="float64",
                           shape=(2, 2), value_ref_enabled=True)
            ]
            self.env["datadesc"] = data_desc

            # simulate sardana scan
            recorder = NXscanH5_FileRecorder(filename=self.path)
            self.env["starttime"] = datetime.now()
            recorder._startRecordList(self.record_list)
            for i in range(nb_records):
                ref = "h5file://" + part_file_paths[i] + "::" + dataset
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


@pytest.fixture
def recorder(tmpdir):
    path = str(tmpdir / "file.h5")
    return NXscanH5_FileRecorder(filename=path)


@pytest.mark.parametrize("custom_data", ["str_custom_data", 8, True])
def test_addCustomData(recorder, custom_data):
    name = "custom_data_name"
    recorder.addCustomData(custom_data, name)
    with h5py.File(recorder.filename) as fd:
        assert fd["entry"]["custom_data"][name].value == custom_data


def test_swmr(tmpdir):

    def scan(path, serialno=0):
        env = ENV.copy()
        env["serialno"] = serialno
        record_list = RecordList(env)
        nb_records = 2
        # create description of channel data
        data_desc = [
            ColumnDesc(name=COL1_NAME,
                       label=COL1_NAME,
                       dtype="float64",
                       shape=())
        ]
        env["datadesc"] = data_desc
        # simulate sardana scan
        recorder = NXscanH5_FileRecorder(filename=path)
        env["starttime"] = datetime.now()
        recorder._startRecordList(record_list)
        for i in range(nb_records):
            record = Record({COL1_NAME: 0.1}, i)
            recorder._writeRecord(record)
        env["endtime"] = datetime.now()
        recorder._endRecordList(record_list)

    def read_file(path, event):
        with h5py.File(path, mode="r"):
            event.set()
            event.wait()

    path = str(tmpdir / "file.h5")
    event = multiprocessing.Event()
    reader = multiprocessing.Process(target=read_file, args=(path, event))
    with h5_write_session(path):
        scan(path, serialno=0)
        reader.start()
        event.wait()
        event.clear()
        try:
            scan(path, serialno=1)
        finally:
            event.set()
            reader.join()
