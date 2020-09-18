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

__all__ = ['AttributeListener']

import numpy
import threading


class AttributeListener(object):

    def __init__(self, dtype=object, attr_name="valuebuffer"):
        self.data = {}
        self.dtype = dtype
        self.attr_name = attr_name
        self.data_lock = threading.RLock()

    def event_received(self, *args, **kwargs):
        # s - type: sardana.sardanavalue.SardanaValue
        # t - type: sardana.sardanaevent.EventType
        # v - type: sardana.sardanaattribute.SardanaAttribute e.g.
        #           sardana.pool.poolbasechannel.Value
        s, t, v = args
        if t.name.lower() != self.attr_name:
            return
        # obtaining sardana element e.g. exp. channel (the attribute owner)
        obj_name = s.name
        # obtaining the SardanaValue(s) either from the value_chunk (in case
        # of buffered attributes) or from the value in case of normal
        # attributes
        chunk = v
        idx = list(chunk.keys())
        value = [sardana_value.value for sardana_value in list(chunk.values())]
        # filling the measurement records
        with self.data_lock:
            channel_data = self.data.get(obj_name, [])
            expected_idx = len(channel_data)
            pad = [None] * (idx[0] - expected_idx)
            channel_data.extend(pad + value)
            self.data[obj_name] = channel_data

    def get_table(self):
        '''Construct a table-like array with padded  channel data as columns.
        Return the '''
        with self.data_lock:
            max_len = max([len(d) for d in list(self.data.values())])
            dtype_spec = []
            table = []
            for k in sorted(self.data.keys()):
                v = self.data[k]
                v.extend([None] * (max_len - len(v)))
                table.append(v)
                dtype_spec.append((k, self.dtype))
            a = numpy.array(list(zip(*table)), dtype=dtype_spec)
            return a
