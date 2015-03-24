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

from taurus.test import insertTest
from taurus.external import unittest

from sardana.pool.pooltggeneration import PoolTGGeneration
from sardana.sardanadefs import State
from sardana.pool.test import (FakePool, createCtrlConf, createElemConf,
                               createPoolController, createPoolTriggerGate,
                               createPoolTGGenerationConfiguration)

@insertTest(helper_name='tggeneration',
            ctrl_lib = 'DummyTriggerGateController',
            ctrl_klass = 'DummyTriggerGateController',
            offset=0, active_period=0.1, passive_period=0.1, repetitions=3,
            integ_time=0.01)
class TGGenerationTestCase(unittest.TestCase):
    #TODO: use doc. link to insertTest decorator function instead of string
    """Base class for integration tests of PoolTGGeneration class and any
    PoolTriggerGateController. One can parameterize it e.g. choose controller
    class or trigger/gate generation parameters like active or passive period,
    using the insertTest decorator and any of the helper methods."""

    def setUp(self):
        """Create a FakePool object.
        """
        unittest.TestCase.setUp(self)
        self.pool = FakePool()

    def tggeneration(self, ctrl_lib, ctrl_klass, offset, active_period,
                        passive_period, repetitions, integ_time):
        #TODO: document method arguments
        """Helper method to verify trigger element states before and after 
        trigger/gate generation.
        """
        # create controller and element
        ctrl_conf = createCtrlConf(self.pool, 'tgctrl01', ctrl_klass, ctrl_lib)
        elem_conf = createElemConf(self.pool, 1, 'tg01')
        self.tg_ctrl = createPoolController(self.pool, ctrl_conf)
        self.tg_elem = createPoolTriggerGate(self.pool, self.tg_ctrl,
                                                        elem_conf)
        # add controller and elements to containers
        self.tg_ctrl.add_element(self.tg_elem)
        self.pool.add_element(self.tg_ctrl)
        self.pool.add_element(self.tg_elem)
        # create TGGeneration action and its configuration
        self.tg_cfg = createPoolTGGenerationConfiguration((self.tg_ctrl,),
                                                       ((self.tg_elem,),),)
        self.tgaction = PoolTGGeneration(self.tg_elem)
        self.tgaction.add_element(self.tg_elem)
        #create start_action arguments
        args = ()
        kwargs = {'config': self.tg_cfg,
                  'offset': offset,
                  'active_period': active_period,
                  'passive_period': passive_period,
                  'repetitions': repetitions,
                 }
        # starting action
        self.tgaction.start_action(*args, **kwargs)
        # verifying that the elements involved in action changed its state
        element_state = self.tg_elem.get_state()
        msg = ("State after start_action is '%s'. (Expected: '%s')" % 
                                    (State.get(element_state), "Moving"))
        self.assertEqual(element_state, State.Moving, msg)
        # entering action loop
        self.tgaction.action_loop()
        # verifying that the elements involved in action changed its state
        element_state = self.tg_elem.get_state()
        msg = ("State after action_loop shall be different than Moving")
        self.assertNotEqual(element_state, State.Moving, msg)

    def tearDown(self):
        self.tgaction = None
        self.tg_ctrl = None
        self.tg_cfg = None
        self.tg_elem = None
        unittest.TestCase.tearDown(self)