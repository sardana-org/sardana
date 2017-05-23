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

from mock import MagicMock

from taurus.external.unittest import TestCase

from sardana.sardanaattribute import BufferedAttribute
from sardana.pool.poolpseudocounter import Value


class TestBufferedAttribute(TestCase):
    """Unit tests for BufferedAttribute class"""

    def setUp(self):
        self.element = MagicMock()
        self.attr = BufferedAttribute(self.element)

    def test_append_value_buffer(self):
        """Test if append_value_buffer correctly fills the last_value_chunk
        as well as permanently adds the value to the value_buffer (a buffered
        attribute listener was added previously in order to provoke a
        persistent append).
        """
        self.attr.obj.has_pseudo_elements = MagicMock(return_value=True)
        self.attr.append_value_buffer(1)
        self.assertIs(len(self.attr.value_buffer), 1)
        self.assertIs(len(self.attr.last_value_chunk), 1)

    def test_extend_value_buffer(self):
        """Test if extend_value_buffer correctly fills the last_value_chunk
        as well as permanently adds the value to the value_buffer (a buffered
        attribute listener was added previously in order to provoke a
        persistent append).
        """
        self.attr.obj.has_pseudo_elements = MagicMock(return_value=True)
        self.attr.extend_value_buffer([1, 2, 3])
        self.assertIs(len(self.attr.value_buffer), 3)
        self.assertIs(len(self.attr.last_value_chunk), 3)

    def test_extend_value_buffer_no_pseudo_elements(self):
        """Test if extend_value_buffer correctly fills the last_value_chunk
        but does not add the value to the value_buffer (no pseudo elements
        are based on this channel so a non-persistent append should take
        place).
        """
        self.element.has_pseudo_elements = MagicMock(return_value=False)
        self.attr.extend_value_buffer([1, 2, 3])
        self.assertIs(len(self.attr.last_value_chunk), 3)
        self.assertIs(len(self.attr.value_buffer), 0)

    def test_is_value_necessary(self):
        """Test if is_value_required is able to recognize that there is no
        listener waiting for a given value.
        """
        pc_value = Value(MagicMock())
        self.attr.add_listener(pc_value.on_change)
        # imitate that the listener already has a 0th element
        pc_value.value_buffer._next_idx = 1
        self.assertFalse(self.attr.is_value_required(0))
