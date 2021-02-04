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

from sardana.pool.test.base import BasePoolTestCase


class PseudoCounterTestCase(BasePoolTestCase, TestCase):
    """TestCase with PseudoCounter integration tests."""

    def setUp(self):
        """Create IoverI0 pseudo counter based on two dummy counters"""
        BasePoolTestCase.setUp(self)
        ctctrl = self.createController("ctctrl1",
                                       "DummyCounterTimerController",
                                       "DummyCounterTimerController")
        ct1 = self.ct1 = self.createCTElement(ctctrl, "ct1", 1)
        ct2 = self.ct2 = self.createCTElement(ctctrl, "ct2", 2)
        pcctrl = self.createController("pcctrl1", "IoverI0", "IoverI0")
        self.pc = self.createPCElement(pcctrl, "pc1", 1, (ct1.id, ct2.id))

    def test_pseudocounter_calc_buffer(self):
        """Simulate acquisition by filling the value buffer of the counters
        and test that the last_value_chunk of the pseudo counter is correctly
        filled.
        """
        pc_value_buffer = self.pc.get_value_buffer()
        self.ct1.extend_value_buffer([1., 2., 3.])
        self.ct2.append_value_buffer(10.)
        self.assertEqual(len(pc_value_buffer.last_chunk), 1)
        self.assertEqual(pc_value_buffer.last_chunk[0].value, 0.1)
        self.ct1.extend_value_buffer([4., 5., 6.])
        self.ct2.append_value_buffer(10., idx=3)
        self.assertEqual(len(pc_value_buffer.last_chunk), 1)
        self.assertEqual(pc_value_buffer.last_chunk[3].value, 0.4)
        self.ct2.append_value_buffer(10., idx=5)
        self.assertEqual(len(pc_value_buffer.last_chunk), 1)
        self.assertEqual(pc_value_buffer.last_chunk[5].value, 0.6)
        self.ct1.extend_value_buffer([7., 8.])
        self.ct1.extend_value_buffer([9.])
        self.ct1.extend_value_buffer([10.])
        self.ct2.append_value_buffer(10., idx=8)
        self.assertEqual(len(pc_value_buffer.last_chunk), 1)
        self.assertEqual(pc_value_buffer.last_chunk[8].value, 0.9)
        self.ct2.append_value_buffer(10., idx=9)
        self.assertEqual(len(pc_value_buffer.last_chunk), 1)
        self.assertEqual(pc_value_buffer.last_chunk[9].value, 1)
