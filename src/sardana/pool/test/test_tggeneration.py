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

"""This module contains tests for trigger gate generation using a 
given controller"""

__docformat__ = "restructuredtext"

import threading

from taurus.test import insertTest
from taurus.external import unittest

from sardana.pool.pooltggeneration import PoolTGGeneration
from sardana.sardanadefs import State
from sardana.pool.pooldefs import SynchDomain
from sardana.pool.test import (FakePool, createCtrlConf, createElemConf,
                               createPoolController, createPoolTriggerGate,
                               createPoolTGGenerationConfiguration)

class TGGenerationTestCase(object):
    """Base class for integration tests of PoolTGGeneration class and any
    PoolTriggerGateController. Test is parameterized using trigger parameters.

    .. seealso:: :meth:`taurus.test.base.insertTest`"""

    def createElements(self, ctrl_klass, ctrl_lib, ctrl_props):
        # create controller and element
        ctrl_conf = createCtrlConf(self.pool, 'tgctrl01', ctrl_klass,
                                   ctrl_lib, ctrl_props)
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

    def setUp(self):
        """Create a FakePool object.
        """
        self.pool = FakePool()

    def tggeneration(self, ctrl_lib, ctrl_klass, ctrl_props,
                     synchronization):
        """Helper method to verify trigger element states before and after 
        trigger/gate generation.

       :param ctrl_lib: controller library used for the test
       :type ctrl_lib: str
       :param ctrl_klass: controller class used for the test
       :type ctrl_klass: str
       :param offset: temporal offset before beginning the trigger generation
       :type offset: float
       :param active_interval: signal at which triggers will be generated
       :type active_interval: float
       :param passive_interval: temporal passive period between two active periods
       :type passive_interval: float
       :param repetitions: number of generated triggers
       :type repetitions: int
        """

        # create controller and trigger element
        self.createElements(ctrl_klass, ctrl_lib, ctrl_props)

        #create start_action arguments
        args = ()
        kwargs = {'config': self.tg_cfg,
                  'synchronization': synchronization
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

    def stopGeneration(self):
        """Method used to change the controller (mock) state"""
        self.tgaction.stop_action()

    def abort_tggeneration(self, ctrl_lib, ctrl_klass, ctrl_props,
                           synchronization, abort_time):
        """Helper method to verify trigger element states before and after 
        trigger/gate generation when aborting the trigger generation.

       :param ctrl_lib: controller library used for the test
       :type ctrl_lib: str
       :param ctrl_klass: controller class used for the test
       :type ctrl_klass: str
       :param offset: temporal offset before beginning the trigger generation
       :type offset: float
       :param active_interval: signal at which triggers will be generated
       :type active_interval: float
       :param passive_interval: temporal passive period between two active periods
       :type passive_interval: float
       :param repetitions: number of generated triggers
       :type repetitions: int
       :param abort_time: wait this time before stopping the trigger generation.
       :type abort_time: float
        """

        # create controller and trigger element
        self.createElements(ctrl_klass, ctrl_lib, ctrl_props)

        # create start_action arguments
        args = ()
        kwargs = {'config': self.tg_cfg,
                  'synchronization': synchronization
                 }
        # starting action
        self.tgaction.start_action(*args, **kwargs)
        # verifying that the elements involved in action changed its state
        element_state = self.tg_elem.get_state()
        msg = ("State after start_action is '%s'. (Expected: '%s')" % 
                                    (State.get(element_state), "Moving"))
        self.assertEqual(element_state, State.Moving, msg)

        # starting timer (abort_time) stop the trigger generation
        threading.Timer(abort_time, self.stopGeneration).start()

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


synchronization1 = [dict(delay={SynchDomain.Time:(None, 0)},
                         active={SynchDomain.Time:(None, .01)},
                         total={SynchDomain.Time:(None, .02)},
                         repeats=0)
                   ]
synchronization2 = [dict(delay={SynchDomain.Time:(None, 0)},
                         active={SynchDomain.Time:(None, .01)},
                         total={SynchDomain.Time:(None, .02)},
                         repeats=100)
                   ]
@insertTest(helper_name='tggeneration',
            ctrl_lib = 'DummyTriggerGateController',
            ctrl_klass = 'DummyTriggerGateController',
            ctrl_props = {},
            synchronization = synchronization1
            )
@insertTest(helper_name='abort_tggeneration',
            ctrl_lib = 'DummyTriggerGateController',
            ctrl_klass = 'DummyTriggerGateController',
            ctrl_props = {},
            synchronization = synchronization2,
            abort_time=0.5
            )
class DummyTGGenerationTestCase(TGGenerationTestCase, unittest.TestCase):
    """Integration TestCase of TGGeneration with DummyTriggerGateController"""

    def setUp(self):
        unittest.TestCase.setUp(self)
        TGGenerationTestCase.setUp(self)

    def tearDown(self):
        TGGenerationTestCase.tearDown(self)
        unittest.TestCase.tearDown(self)
