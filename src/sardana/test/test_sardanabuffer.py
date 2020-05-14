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

from unittest import TestCase

from sardana.sardanabuffer import SardanaBuffer


class TestPersistentBuffer(TestCase):
    """Unit tests for Buffer class"""

    def setUp(self):
        self.buffer = SardanaBuffer(persistent=True)
        self.buffer.extend([1, 2, 3])

    def test_extend(self):
        """Test extend method with a simple case of a list."""
        chunk = [4, 5, 6]
        self.buffer.extend(chunk)
        self.assertEqual(self.buffer.get_value(0), 1)
        self.assertEqual(self.buffer.get_value(5), 6)
        self.assertEqual(len(self.buffer), 6)
        self.assertEqual(len(self.buffer.last_chunk), 3)

    def test_append(self):
        """Test if append correctly fills the last_chunk as well as permanently
        adds the value to the buffer.
        """
        self.buffer.append(1)
        self.assertEqual(len(self.buffer), 4)
        self.assertEqual(len(self.buffer.last_chunk), 1)
