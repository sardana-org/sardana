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

import os
import uuid
from unittest import TestCase

from tango import DevState
from taurus import Device
from taurus.test.base import insertTest

from .test_pool import is_numerical
from sardana.pool.pooldefs import AcqSynchType
from sardana.taurus.core.tango.sardana.pool import registerExtensions
from sardana.tango.pool.test.base_sartest import SarTestTestCase


@insertTest(helper_name="stress_count",
            test_method_doc="stress count with CT (hardware trigger) and 0D",
            elements=["_test_ct_1_1", "_test_0d_1_1"], repeats=100,
            synchronizer="_test_tg_1_1", synchronization=AcqSynchType.Trigger)
@insertTest(helper_name="stress_count",
            test_method_doc="stress count with CT (software trigger) and 0D",
            elements=["_test_ct_1_1", "_test_0d_1_1"], repeats=100,
            synchronizer="software", synchronization=AcqSynchType.Trigger)
@insertTest(helper_name="stress_count",
            test_method_doc="stress count with CT (hardware start)",
            elements=["_test_ct_1_1"], repeats=100,
            synchronizer="_test_tg_1_1", synchronization=AcqSynchType.Start)
@insertTest(helper_name="stress_count",
            test_method_doc="stress count with CT (software start)",
            elements=["_test_ct_1_1"], repeats=100,
            synchronizer="software", synchronization=AcqSynchType.Start)
@insertTest(helper_name="stress_count",
            test_method_doc="stress count with CT (hardware trigger)",
            elements=["_test_ct_1_1"], repeats=100,
            synchronizer="_test_tg_1_1", synchronization=AcqSynchType.Trigger)
@insertTest(helper_name="stress_count",
            test_method_doc="count with CT (software trigger)",
            elements=["_test_ct_1_1"], repeats=100,
            synchronizer="software", synchronization=AcqSynchType.Trigger)
class TestStressMeasurementGroup(SarTestTestCase, TestCase):

    def setUp(self):
        SarTestTestCase.setUp(self)
        registerExtensions()

    def stress_count(self, elements, repeats, synchronizer, synchronization):
        if (elements == ["_test_ct_1_1", "_test_0d_1_1"]
                and synchronizer == "_test_tg_1_1"
                and synchronization == AcqSynchType.Trigger
                and os.name == "nt"):
            self.skipTest("fails on Windows")
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)
        try:
            mg = Device(mg_name)
            mg.setSynchronizer(synchronizer, elements[0], apply=False)
            mg.setSynchronization(synchronization, elements[0])
            for i in range(repeats):
                state, values = mg.count(.001)
                self.assertEqual(state, DevState.ON,
                                 "wrong state after measurement {}".format(i))
                for channel_name, value in values.items():
                    msg = ("Value {} for {} is not numerical in "
                           "measurement {}").format(value, channel_name, i)
                    self.assertTrue(is_numerical(value), msg)
        finally:
            mg.cleanUp()
            if os.name != "nt":
                self.pool.DeleteElement(mg_name)

    def tearDown(self):
        SarTestTestCase.tearDown(self)
