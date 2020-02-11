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

"""This module contains tests for trigger gate generation using a
given controller"""

import threading

from taurus.test import insertTest
import unittest

from sardana.pool.poolsynchronization import PoolSynchronization
from sardana.pool.poolacquisition import get_acq_ctrls
from sardana.sardanadefs import State
from sardana.pool.pooldefs import SynchDomain, SynchParam
from sardana.pool.test import FakePool, createCtrlConf, createElemConf, \
    createPoolController, createPoolTriggerGate, \
    createControllerConfiguration

__docformat__ = "restructuredtext"


class SynchronizationTestCase(object):
    """Base class for integration tests of PoolSynchronization class and any
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
        # create Synchronization action and its configuration
        self.conf_ctrl = createControllerConfiguration(self.tg_ctrl,
                                                       [self.tg_elem])
        self.ctrls = get_acq_ctrls([self.conf_ctrl])
        self.tgaction = PoolSynchronization(self.tg_elem)
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
       :type ctrl_lib: :obj:`str`
       :param ctrl_klass: controller class used for the test
       :type ctrl_klass: :obj:`str`
       :param offset: temporal offset before beginning the trigger generation
       :type offset: float
       :param active_interval: signal at which triggers will be generated
       :type active_interval: float
       :param passive_interval: temporal passive period between two active
                                periods
       :type passive_interval: float
       :param repetitions: number of generated triggers
       :type repetitions: int
        """

        # create controller and trigger element
        self.createElements(ctrl_klass, ctrl_lib, ctrl_props)

        # create start_action arguments
        args = (self.ctrls, synchronization)
        kwargs = {}
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
       :type ctrl_lib: :obj:`str`
       :param ctrl_klass: controller class used for the test
       :type ctrl_klass: :obj:`str`
       :param offset: temporal offset before beginning the trigger generation
       :type offset: float
       :param active_interval: signal at which triggers will be generated
       :type active_interval: float
       :param passive_interval: temporal passive period between two active
                                periods
       :type passive_interval: float
       :param repetitions: number of generated triggers
       :type repetitions: int
       :param abort_time: wait this time before stopping the trigger generation
       :type abort_time: float
        """

        # create controller and trigger element
        self.createElements(ctrl_klass, ctrl_lib, ctrl_props)

        # create start_action arguments
        args = (self.ctrls, synchronization)
        kwargs = {}
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


synchronization1 = [{SynchParam.Delay: {SynchDomain.Time: 0},
                     SynchParam.Active: {SynchDomain.Time: .01},
                     SynchParam.Total: {SynchDomain.Time: .02},
                     SynchParam.Repeats: 0}]

synchronization2 = [{SynchParam.Delay: {SynchDomain.Time: 0},
                     SynchParam.Active: {SynchDomain.Time: .01},
                     SynchParam.Total: {SynchDomain.Time: .02},
                     SynchParam.Repeats: 100}]


@insertTest(helper_name='tggeneration',
            ctrl_lib='DummyTriggerGateController',
            ctrl_klass='DummyTriggerGateController',
            ctrl_props={},
            synchronization=synchronization1
            )
@insertTest(helper_name='abort_tggeneration',
            ctrl_lib='DummyTriggerGateController',
            ctrl_klass='DummyTriggerGateController',
            ctrl_props={},
            synchronization=synchronization2,
            abort_time=0.5
            )
class DummySynchronizationTestCase(SynchronizationTestCase, unittest.TestCase):
    """Integration TestCase of Synchronization with \
       DummyTriggerGateController"""

    def setUp(self):
        unittest.TestCase.setUp(self)
        SynchronizationTestCase.setUp(self)

    def tearDown(self):
        SynchronizationTestCase.tearDown(self)
        unittest.TestCase.tearDown(self)
