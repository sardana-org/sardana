#!/usr/bin/env python

#
#
# This file is part of Sardana
#
# http://www.sardana-controls.org/
#
# Copyright 2019 Brookhaven National Laboratory
#
# Sardana is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sardana is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
#
#

__all__ = ["Suitcase_Recorder"]

__docformat__ = "restructuredtext"

from sardana.macroserver.scan.recorder import BaseFileRecorder

from event_model import compose_run
from suitcase.jsonl import Serializer
import time


class Suitcase_Recorder(BaseFileRecorder):

    """
    Saves data to a nexus file that follows the NXscan application definition
    (This is a pure h5py implementation that does not depend on the nxs module)
    """

    formats = {"suitcase": ".suitcase"}

    supported_dtypes = (
        "float32",
        "float64",
        "int8",
        "int16",
        "int32",
        "int64",
        "uint8",
        "uint16",
        "uint32",
        "uint64",
    )

    def __init__(self, filename=None, **pars):
        super().__init__(**pars)
        # TODO use the filename to select the serializer class
        # TODO respect the file path
        self._serializer = Serializer("/tmp")

    def _startRecordList(self, recordlist):
        special_list = {"starttime", "datadesc", "insturmentlist"}
        env = recordlist.getEnviron()
        metadata = {k: v for k, v in env.items() if k not in special_list}
        for k in ["datadesc", "instrumentlist"]:
            metadata[k] = repr(env[k])
        metadata["scan_id"] = env["serialno"]
        self.run_bundle = compose_run(
            time=env["starttime"].timestamp(), metadata=metadata
        )
        self._serializer("start", self.run_bundle.start_doc)
        data_keys = {}
        self.name_map = {}
        # TODO do a better job mapping the dtypes
        for col in env["datadesc"]:
            data_keys[col.label] = {
                "dtype": "number",
                "shape": col.getShape(),
                "source": f"sardana:{col.name}",
                # "actual_dtype": col.getDtype(),
            }
            self.name_map[col.name] = col.label
        # TODO: can we get any configuration out?
        self.desc_bundle = self.run_bundle.compose_descriptor(
            data_keys=data_keys, name="primary"
        )

        self._serializer("descriptor", self.desc_bundle.descriptor_doc)

    def _writeRecord(self, record):
        ts = time.time()
        data = {self.name_map[k]: v for k, v in record.data.items()}
        timestamps = {self.name_map[k]: ts for k in record.data}
        self._serializer(
            "event", self.desc_bundle.compose_event(data=data, timestamps=timestamps)
        )

    def _endRecordList(self, recordlist):
        env = recordlist.getEnviron()
        stop = self.run_bundle.compose_stop(time=env["endtime"].timestamp())
        self._serializer("stop", stop)
        self._serializer.close()
        self._serializer = None
