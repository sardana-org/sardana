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

"""This module is part of the Python Pool library. It defines the base classes
for moveables"""

__all__ = ["PositionBuffer", "PoolBaseMoveable"]

__docformat__ = 'restructuredtext'

from sardana.sardanabuffer import SardanaBuffer
from sardana.pool.poolelement import PoolElement


class PositionBuffer(SardanaBuffer):
    pass


class PoolBaseMoveable(PoolElement):

    def __init__(self, **kwargs):
        PoolElement.__init__(self, **kwargs)
        self._position_buffer = PositionBuffer(self, listeners=self.on_change)

    # -------------------------------------------------------------------------
    # Event forwarding
    # -------------------------------------------------------------------------

    def on_change(self, evt_src, evt_type, evt_value):
        # forward all events coming from attributes to the listeners
        self.fire_event(evt_type, evt_value)

    def get_position_buffer(self):
        """Returns the position buffer object for this motor

        :return: the position buffer
        :rtype: :class:`~sardana.sardanaattribute.SardanaBuffer`"""
        return self._position_buffer

    def append_position_buffer(self, position, idx=None, propagate=1):
        """Extend position buffer with new positions assigning them consecutive
        indexes starting with idx. If idx is omitted, then the new position
        will be added right after the last position in the buffer.

        :param position:
            position to be added to the buffer
        :type position:
            :class:`~sardana.sardanavalue.SardanaValue`
        :param propagate:
            0 for not propagating, 1 to propagate, 2 propagate with priority
        :type propagate: int
        """
        pos_buffer = self._position_buffer
        pos_buffer.append(position, idx)
        return pos_buffer

    def clear_position_buffer(self):
        pos_buffer = self._position_buffer
        pos_buffer.clear()

    position_buffer = property(get_position_buffer,
                               doc="motor position buffer")
