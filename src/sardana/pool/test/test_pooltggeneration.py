#!/usr/bin/env python

##############################################################################
##
## This file is part of Sardana
##
## http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
##
## Sardana is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## Sardana is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################
#TODO: import using taurus.external.unittest
from mock import Mock, call

from taurus.external import unittest
from sardana.pool.pooltggeneration import PoolTGGeneration
from sardana.pool.test import (FakePool, createPoolController,
                               createPoolTriggerGate, dummyPoolTGCtrlConf01,
                               dummyTriggerGateConf01, 
                               createPoolTGActionConfiguration) 

class PoolTriggerGateTestCase(unittest.TestCase):
    """Unittest of PoolCounterTimer Class"""

    def setUp(self):
        """Create a Controller, TriggerGate and PoolTGGeneration objects from 
        dummy configurations"""
        unittest.TestCase.setUp(self)
        pool = FakePool()
        
        dummy_tg_ctrl = createPoolController(pool, dummyPoolTGCtrlConf01)
        dummy_tg = createPoolTriggerGate(pool, dummy_tg_ctrl, 
                                                        dummyTriggerGateConf01)
        self.cfg = createPoolTGActionConfiguration((dummy_tg_ctrl,), 
                                        (dummyTriggerGateConf01,),
                                        ((dummy_tg,),),
                                        ((dummyTriggerGateConf01,),))
        
        self.mock_tg_ctrl = Mock(spec=dummy_tg_ctrl.ctrl)
        dummy_tg_ctrl.ctrl = self.mock_tg_ctrl

        self.tgaction = PoolTGGeneration(dummy_tg)

    def test_start_action(self):
        """Verify that the created PoolTGAction start_action starts correctly 
        the involved controller."""
        args = ()
        kwargs = {'config': self.cfg}
        self.tgaction.start_action(*args, **kwargs)
        self.mock_tg_ctrl.assert_has_calls([call.PreStartAll(), 
                                           (call.PreStartOne(1,)),
                                           (call.StartOne(1,)),
                                           (call.StartAll())])
        
    def tearDown(self):
        unittest.TestCase.tearDown(self)
        