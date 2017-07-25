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


import uuid
import numpy

from taurus import Device
from taurus.external.unittest import TestCase
from taurus.test.base import insertTest
from sardana.sardanautils import is_number, is_non_str_seq
from sardana.taurus.core.tango.sardana.pool import registerExtensions
from sardana.tango.pool.test.base_sartest import SarTestTestCase


def is_numerical(obj):
    if is_number(obj):
        return True
    if is_non_str_seq(obj) or isinstance(obj, numpy.ndarray):
        if is_number(obj[0]):
            return True
        elif is_non_str_seq(obj[0]) or isinstance(obj, numpy.ndarray):
            if is_number(obj[0][0]):
                return True
    return False


@insertTest(helper_name="count", test_method_doc="count with PC",
            elements=["_test_ct_1_1", "_test_ct_1_2", "_test_pc_1_1"])
@insertTest(helper_name="count", test_method_doc="count with Tango attribute",
            elements=["_test_ct_1_1", "_test_mt_1_1/position"])
@insertTest(helper_name="count", test_method_doc="count with 2D",
            elements=["_test_ct_1_1", "_test_2d_1_1"])
@insertTest(helper_name="count", test_method_doc="count with 1D",
            elements=["_test_ct_1_1", "_test_1d_1_1"])
@insertTest(helper_name="count", test_method_doc="count with 0D",
            elements=["_test_ct_1_1", "_test_0d_1_1"])
@insertTest(helper_name="count", test_method_doc="count with CT",
            elements=["_test_ct_1_1"])
class TestMeasurementGroup(SarTestTestCase, TestCase):

    def setUp(self):
        SarTestTestCase.setUp(self)
        self.mg_name = str(uuid.uuid1())
        registerExtensions()

    def count(self, elements):
        argin = [self.mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)
        try:
            self.mg = Device(self.mg_name)
            _, values = self.mg.count(1)
            for channel, value in values.iteritems():
                msg = "Value for %s is not numerical" % channel
                self.assertTrue(is_numerical(value), msg)
        finally:
            self.pool.DeleteElement(self.mg_name)

    def tearDown(self):
        SarTestTestCase.tearDown(self)
