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

"""Tests Read Position from Sardana using PyTango"""
import os

import PyTango
import unittest
from sardana.tango.pool.test import BasePoolTestCase
from sardana.tango.core.util import get_free_alias
import numbers


class ReadMotorPositionOutsideLim(BasePoolTestCase, unittest.TestCase):
    """TestCase class for testing that read position is possible when
    motor is out of SW limits. Verify that position has a numeric type.
    """

    def setUp(self):
        """Create dummy motor controller and dummy motor element
        """
        super(ReadMotorPositionOutsideLim, self).setUp()
        sar_type = 'Motor'
        lib = 'DummyMotorController'
        cls = 'DummyMotorController'
        self.ctrl_name = get_free_alias(PyTango.Database(), "readposctrl")
        self.pool.CreateController([sar_type, lib, cls, self.ctrl_name])
        self.elem_name = get_free_alias(PyTango.Database(), "mot_test")
        axis = 1
        self.pool.CreateElement([sar_type, self.ctrl_name, str(axis),
                                 self.elem_name])
        self.elem = PyTango.DeviceProxy(self.elem_name)
        self.elem.DefinePosition(0)

    def test_read_position_outside_sw_lim(self):
        """Test bug #238: reading position when motor is out of SW lims.
        Verify that position has a numeric type."""
        pc = self.elem.get_attribute_config("position")
        pc.min_value = "1"
        pc.max_value = "2"
        self.elem.set_attribute_config(pc)
        try:
            posread = self.elem.read_attribute('position').value
        except Exception as e_read:
            msg = ("Position cannot be read. Exception: %s" % e_read)
            self.fail(msg)
        msg = ("Position is not a number")
        self.assertIsInstance(posread, numbers.Number, msg)

    def tearDown(self):
        """Remove motor element and motor controller
        """
        if os.name != "nt":
            self.pool.DeleteElement(self.elem_name)
            self.pool.DeleteElement(self.ctrl_name)
        super(ReadMotorPositionOutsideLim, self).tearDown()
