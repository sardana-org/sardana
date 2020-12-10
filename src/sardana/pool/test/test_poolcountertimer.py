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

import pytest
import unittest

from sardana import State
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


def StateOne_state(self, axis):
    return State.On


def StateOne_state_status(self, axis):
    return State.On, "Status"


@pytest.mark.parametrize("mock_StateOne", [StateOne_state,
                                           StateOne_state_status])
def test_state(monkeypatch, mock_StateOne):
    """Test variants of StateOne return value:
    - state
    - state, status
    """
    pool = FakePool()
    # when SEP19 gets implemented it should be possible to mock directly
    # the imported class
    DummyCounterTimerController = pool.ctrl_manager.getControllerClass(
        "DummyCounterTimerController")
    monkeypatch.setattr(DummyCounterTimerController, "StateOne",
                        mock_StateOne)
    ct_ctrl = createPoolController(pool, dummyPoolCTCtrlConf01)
    ct = createPoolCounterTimer(pool, ct_ctrl, dummyCounterTimerConf01)
    ct_ctrl.add_element(ct)
    pool.add_element(ct_ctrl)
    pool.add_element(ct)
    assert ct.state == State.On
    assert type(ct.status) == str
