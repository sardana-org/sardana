#!/usr/bin/env python

##############################################################################
##
# This file is part of Sardana
##
# http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
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

from taurus.external import unittest
from taurus.test import insertTest
from sardana.pool.poolsynchronization import PoolSynchronization
from sardana.pool.test.test_acquisition import AcquisitionTestCase
import logging


@insertTest(helper_name='hw_step_acquisition', repetitions=1,
            integ_time=0.4)
class DummyCounterTimerControllerTestCase(AcquisitionTestCase, unittest.TestCase):
    """Integration test.
    """
    chn_ctrl_name = '_test_ct_ctrl_1'
    chn_elem_name1 = '_test_ct_1_1'

    def setUp(self):
        """#Create a Controller, TriggerGate and PoolSynchronization objects from
        #Ni660XTriggerGateController and Ni660XPositionCTCtrl configurations.
        """
        unittest.TestCase.setUp(self)
        AcquisitionTestCase.setUp(self)
        self.channel_names.append(self.chn_elem_name1)

    def tearDown(self):
        AcquisitionTestCase.tearDown(self)
        unittest.TestCase.tearDown(self)
