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
import threading

import unittest

from sardana.pool.poolsynchronization import PoolSynchronization
from sardana.pool.poolacquisition import get_acq_ctrls
from sardana.sardanadefs import State
from sardana.pool.test import FakePool, createPoolController, \
    createPoolTriggerGate, dummyPoolTGCtrlConf01, dummyTriggerGateConf01, \
    createControllerConfiguration


class PoolTriggerGateTestCase(unittest.TestCase):
    """Unittest of PoolSynchronization class"""

    def setUp(self):
        """Create a Controller, TriggerGate and PoolSynchronization objects from
        dummy configurations
        """
        unittest.TestCase.setUp(self)
        try:
            from mock import Mock
        except ImportError:
            self.skipTest("mock module is not available")
        pool = FakePool()
        dummy_tg_ctrl = createPoolController(pool, dummyPoolTGCtrlConf01)
        self.dummy_tg = createPoolTriggerGate(pool, dummy_tg_ctrl,
                                              dummyTriggerGateConf01)
        dummy_tg_ctrl.add_element(self.dummy_tg)
        pool.add_element(dummy_tg_ctrl)
        pool.add_element(self.dummy_tg)
        self.conf_ctrl = createControllerConfiguration(dummy_tg_ctrl,
                                                       [self.dummy_tg])

        self.ctrls = get_acq_ctrls([self.conf_ctrl])
        # self.cfg = createPoolSynchronizationConfiguration((dummy_tg_ctrl,),
        #                                                   ((self.dummy_tg,),),)
        # Create mock and define its functions
        ctrl_methods = ['PreStartAll', 'StartAll', 'PreStartOne', 'StartOne',
                        'PreStateAll', 'StateAll', 'PreStateOne', 'StateOne',
                        'PreSynchAll', 'PreSynchOne', 'SynchOne', 'SynchAll']
        self.mock_tg_ctrl = Mock(spec=ctrl_methods)
        self.mock_tg_ctrl.StateOne.return_value = (State.Moving, 'triggering')

        dummy_tg_ctrl.ctrl = self.mock_tg_ctrl
        self.tgaction = PoolSynchronization(self.dummy_tg)
        self.tgaction.add_element(self.dummy_tg)

    def stopGeneration(self):
        """Method used to change the controller (mock) state"""
        self.mock_tg_ctrl.StateOne.return_value = (State.On, 'On')

    def test_tggeneration(self):
        """Verify trigger element states before and after action_loop."""
        from mock import call, MagicMock
        # starting action
        synchronization = MagicMock()
        self.tgaction.start_action(self.ctrls, synchronization)
        # verifying that the action correctly started the involved controller
        self.mock_tg_ctrl.assert_has_calls([call.PreStartAll(),
                                            (call.PreStartOne(1,)),
                                            (call.StartOne(1,)),
                                            (call.StartAll())])
        # verifying that the elements involved in action changed its state
        element_state = self.dummy_tg.get_state()
        msg = ("State after start_action is '%s'. (Expected: '%s')" %
               (State.get(element_state), "Moving"))
        self.assertEqual(element_state, State.Moving, msg)
        # starting timer (1 s) which will change the controller state
        threading.Timer(1, self.stopGeneration).start()
        # entering action loop
        self.tgaction.action_loop()
        # verifying that the action checked the controller states
        self.mock_tg_ctrl.assert_has_calls([call.PreStateAll(),
                                            call.PreStateOne(1,),
                                            call.StateAll(),
                                            call.StateOne(1,)])
        # verifying that the elements involved in action changed its state
        element_state = self.dummy_tg.get_state()
        msg = ("State after action_loop shall be different than Moving")
        self.assertNotEqual(element_state, State.Moving, msg)

    def tearDown(self):
        self.tgaction = None
        self.mock_tg_ctrl = None
        self.cfg = None
        self.dummy_tg = None
        unittest.TestCase.tearDown(self)
