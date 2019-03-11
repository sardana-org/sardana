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

import time

from taurus.external import unittest

from sardana.pool.poolcountertimer import PoolCounterTimer
from sardana.pool.test import (FakePool, createPoolController,
                               createPoolCounterTimer, dummyCounterTimerConf01,
                               dummyPoolCTCtrlConf01)


class PoolCounterTimerTestCase(unittest.TestCase):
    """Unittest of PoolCounterTimer Class"""

    def setUp(self):
        """Create a Controller and a CounterTimer element"""
        pool = FakePool()

        pc = createPoolController(pool, dummyPoolCTCtrlConf01)
        self.pct = createPoolCounterTimer(pool, pc, dummyCounterTimerConf01)

    def test_init(self):
        """Verify that the created CounterTimer is a PoolCounterTimer
        instance."""
        msg = 'PoolCounterTimer constructor does not create ' +\
              'PoolCounterTimer instance'
        self.assertIsInstance(self.pct, PoolCounterTimer, msg)

    def test_acquisition(self):
        self.pct.integration_time = 0.1
        self.pct.start_acquisition()
        while self.pct.acquisition.is_running():
            time.sleep(0.01)
        msg = "wrong value after acquisition"
        self.assertEqual(self.pct.value.value, 0.1, msg)

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        self.pct = None
