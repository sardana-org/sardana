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
import time
import thread

from taurus.external import unittest
from sardana.pool.controller import TriggerGateController
from sardana.pool.pooltggeneration import PoolTGGeneration
from sardana.sardanadefs import State
from sardana.pool.test import (FakePool, createPoolController,
                               createPoolTriggerGate, dummyPoolTGCtrlConf01,
                               dummyTriggerGateConf01, 
                               createPoolTGActionConfiguration) 

class PoolTriggerGateTestCase(unittest.TestCase):
    """Unittest of PoolTGGeneration Class"""

    def setUp(self):
        """Create a Controller, TriggerGate and PoolTGGeneration objects from 
        dummy configurations"""
        unittest.TestCase.setUp(self)
        pool = FakePool()

        dummy_tg_ctrl = createPoolController(pool, dummyPoolTGCtrlConf01)
        self.dummy_tg = createPoolTriggerGate(pool, dummy_tg_ctrl, 
                                                        dummyTriggerGateConf01)
        dummy_tg_ctrl.add_element(self.dummy_tg)
        pool.add_element(dummy_tg_ctrl)
        pool.add_element(self.dummy_tg)
        self.cfg = createPoolTGActionConfiguration((dummy_tg_ctrl,), 
                                        (dummyTriggerGateConf01,),
                                        ((self.dummy_tg,),),
                                        ((dummyTriggerGateConf01,),))
        
        # Create mock and define its functions
        ctrl_methods = ['PreStartAll', 'StartAll', 'PreStartOne', 'StartOne',
                        'PreStateAll', 'StateAll', 'PreStateOne', 'StateOne']
        self.mock_tg_ctrl = Mock(spec=ctrl_methods)
        self.mock_tg_ctrl.StateOne.return_value = State.Moving
        dummy_tg_ctrl.ctrl = self.mock_tg_ctrl
        self.tgaction = PoolTGGeneration(self.dummy_tg)
        self.tgaction.add_element(self.dummy_tg)
        
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
                
    def delaySetState(self, threadName, delay):
        time.sleep(delay)
        self.mock_tg_ctrl.StateOne.return_value = State.On
        ret = self.mock_tg_ctrl.StateOne()
     
    def test_action_loop(self):
        """Verify trigger element states before and after action_loop."""
 
        args = ()
        kwargs = {'config': self.cfg}
        self.tgaction.start_action(*args, **kwargs)
        state_after_start_action = self.dummy_tg.state
        msg = ("State after start_action is '%s'. (Expected: '%s')" % 
                              (State.get(state_after_start_action), "Moving"))
        self.assertEqual(self.dummy_tg.state, State.Moving, msg)       
     
        try:
           thread.start_new_thread(self.delaySetState, ("ThreadDelay", 1,))
        except:
           print "Error: unable to start thread"

        self.tgaction.action_loop()
   
        self.mock_tg_ctrl.assert_has_calls([call.PreStateAll(),
                                            call.PreStateOne(1,),
                                            call.StateAll(), 
                                            call.StateOne(1,)])
        
        state_after_action_loop = self.dummy_tg.state
        msg = ("State after action_loop is '%s'. (Expected: '%s')" % 
                                   (State.get(state_after_action_loop), "On"))
        self.assertEqual(self.dummy_tg.state, State.On, msg)    

    def tearDown(self):
        self.tgaction = None
        self.mock_tg_ctrl = None
        self.cfg = None
        self.dummy_tg = None
        unittest.TestCase.tearDown(self)

