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

"""This module is part Sardana Python library. It defines the base clases
for Sardana buffers"""

from __future__ import absolute_import

import weakref

from taurus.external.ordereddict import OrderedDict

from .sardanavalue import SardanaValue
from .sardanaevent import EventGenerator, EventType
from .sardanaexception import SardanaException


class LateValueException(SardanaException):
    """Exception indicating that a given value is not present in the buffer and
    will not arrive yet (newer value(s) were already added to the buffer).
    """
    pass


class EarlyValueException(SardanaException):
    """Exception indicating that a given value is not present in the buffer but
    there is still a chance that it will arrive (no newer values were added to
    the buffer yet.)
    """
    pass


class SardanaBuffer(EventGenerator):
    """Buffer for objects which are identified by an unique idx and are ordered
    """

    def __init__(self, obj=None, name=None, persistent=False, **kwargs):
        """Construct SardanaBuffer object

        :param name: object name
        :type name: str
        :param persistent: whether objects should stay in the buffer until
            being explicitly removed (True) or just until firing next event
            (False)
        :type persistent: bool
        """
        super(SardanaBuffer, self).__init__(**kwargs)
        if obj is not None:
            obj = weakref.ref(obj)
        self._obj = obj
        self.name = name or self.__class__.__name__
        self._persistent = persistent
        self._buffer = OrderedDict()
        self._next_idx = 0
        self._last_chunk = None

    def __len__(self):
        return self._buffer.__len__()

    def get_obj(self):
        """Returns the object which *owns* this buffer

        :return: the object which *owns* this buffer
        :rtype: obj"""
        return self._get_obj()

    def _get_obj(self):
        obj = self._obj
        if obj is not None:
            obj = obj()
        return obj

    def get_value(self, idx):
        return self.get_value_obj(idx).value

    def get_value_obj(self, idx):
        try:
            return self._buffer[idx]
        except KeyError:
            msg = "value with %s index is not in buffer"
            if self.next_idx > idx:
                raise LateValueException(msg)
            else:
                raise EarlyValueException(msg)

    def remove(self, idx):
        try:
            return self._buffer.pop(idx)
        except KeyError:
            msg = "value with %s index is not in buffer"
            raise KeyError(msg)

    def append(self, value, idx=None):
        """Append a single value at the end of the buffer with a given index.

        :param value: value to be appended to the buffer
        :type param: SardanaValue or any object
        :param idx: at which index append the value, None means append at the
            end of the buffer
        :type idx: int
        :param persistent: whether value should be added to a persistent
            buffer or just as a last chunk
        :type param: bool
        """
        if idx is None:
            idx = self._next_idx
        self._last_chunk = OrderedDict()
        if not isinstance(value, SardanaValue):
            value = SardanaValue(value)
        self._last_chunk[idx] = value
        if self._persistent:
            self._buffer[idx] = value
        self._next_idx = idx + 1
        self.fire_add_event()

    def extend(self, values, initial_idx=None):
        """Extend buffer with a list of objects assigning them consecutive
        indexes.

        :param objs: objects that extend the buffer
        :type param: list<object>
        :param initial_idx: at which index append the first object,
            the rest of them will be assigned the next consecutive indexes,
            None means assign at the end of the buffer
        :type idx: int
        """
        if initial_idx is None:
            initial_idx = self._next_idx
        self._last_chunk = OrderedDict()
        for idx, value in enumerate(values, initial_idx):
            if not isinstance(value, SardanaValue):
                value = SardanaValue(value)
            self._last_chunk[idx] = value
            if self._persistent:
                self._buffer[idx] = value
        self._next_idx = idx + 1
        self.fire_add_event()

    def fire_add_event(self, propagate=1):
        """Fires an event to the listeners of the object which owns this
        buffer.

        :param propagate:
            0 for not propagating, 1 to propagate, 2 propagate with priority
        :type propagate: int"""
        evt_type = EventType(self.name, priority=propagate)
        self.fire_event(evt_type, self.last_chunk)

    def reset(self):
        self._next_idx = 0
        self._buffer = OrderedDict()

    def get_last_chunk(self):
        return self._last_chunk

    def get_next_idx(self):
        return self._next_idx

    obj = property(get_obj, "container object for this buffer")
    last_chunk = property(get_last_chunk,
        doc="chunk with last value(s) added to this buffer")
    next_idx = property(get_next_idx,
        doc="index that will be automatically assigned to the next value "\
            "added to this buffer (if not explicitly assigned by the user)")
