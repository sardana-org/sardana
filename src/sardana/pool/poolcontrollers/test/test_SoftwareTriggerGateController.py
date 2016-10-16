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
from sardana.pool.pooldefs import SynchDomain, SynchParam

from sardana.pool.test import (FakePool, createPoolController,
                               createPoolTriggerGate, softwarePoolTGCtrlConf01,
                               dummyTriggerGateConf01, 
                               createPoolTGGenerationConfiguration)

from sardana.pool.poolcontrollers.test import (TriggerGateControllerTestCase,
                                               PositionGenerator,
                                               TriggerGateReceiver)
from sardana.pool.poolcontrollers.SoftwareTriggerGateController import\
                                                  SoftwareTriggerGateController

synchronization1 = [{SynchParam.Delay: {SynchDomain.Time: 0},
                     SynchParam.Active: {SynchDomain.Time: .03},
                     SynchParam.Total: {SynchDomain.Time: .1},
                     SynchParam.Repeats: 0}
                    ]
synchronization2 = [{SynchParam.Delay: {SynchDomain.Time: 0.1},
                     SynchParam.Active: {SynchDomain.Time: .02},
                     SynchParam.Total: {SynchDomain.Time: .04},
                     SynchParam.Repeats: 10}
                    ]
synchronization3 = [{SynchParam.Delay: {SynchDomain.Position: 0},
                     SynchParam.Initial: {SynchDomain.Position: 0},
                     SynchParam.Active: {SynchDomain.Position: .1},
                     SynchParam.Total: {SynchDomain.Position: 1},
                     SynchParam.Repeats: 10}
                    ]
synchronization4 = [{SynchParam.Delay: {SynchDomain.Time: .1},
                     SynchParam.Initial: {SynchDomain.Position: 0},
                     SynchParam.Active: {SynchDomain.Time: 0.1},
                     SynchParam.Total: {SynchDomain.Position: -1,
                                        SynchDomain.Time: 0.1},
                     SynchParam.Repeats: 10}
                    ]

@insertTest(helper_name='generation',  configuration=synchronization1)
@insertTest(helper_name='abort', configuration=synchronization2, abort=.1)
class SoftwareTriggerGateControllerTestCase(TriggerGateControllerTestCase):
    KLASS = SoftwareTriggerGateController


@insertTest(helper_name='generation', configuration=synchronization3,
            passive_domain=SynchDomain.Position)
@insertTest(helper_name='abort', configuration=synchronization4, abort=1)
class SoftwareTriggerGatePositionControllerTestCase(TriggerGateControllerTestCase):
    KLASS = SoftwareTriggerGateController

    def post_configuration_hook(self):
        # Configure and run the position generator
        configuration = self.configuration[0]
        repeat = configuration[SynchParam.Repeats]
        # store repeats for the asserts against received triggers
        self.repetitions = repeat
        initial = configuration[SynchParam.Initial][SynchDomain.Position]
        total = configuration[SynchParam.Total][SynchDomain.Position]
        final = initial + repeat * total
        if total < 0:
            initial += 1
            final -= 1
        else:
            initial -= 1
            final += 1
        period = 0.01
        self.generator = PositionGenerator(initial, final, period)
        # create and add listeners
        self._device = self.ctrl.tg[self.AXIS - 1]
        self.tg_receiver = TriggerGateReceiver()

        self.generator.add_listener(self._device)
        self.ctrl.add_listener(self.AXIS, self.tg_receiver)
        # run PositionGenerator
        self.generator.start()

    def post_generation_hook(self):
        # remove listener
        self.ctrl.remove_listener(self.AXIS, self.tg_receiver)
        self.generator.remove_listener(self._device)
        # testing number of received triggers
        received_triggers = self.tg_receiver.count
        msg = ('Received triggers: %d does not correspond to generated: %d' %\
               (received_triggers, self.repetitions))
        if not self.isAborted:
            self.assertEqual(received_triggers, self.repetitions, msg)


@insertTest(helper_name='generation', synchronization=synchronization1,
            active_domain=SynchDomain.Time)
@insertTest(helper_name='generation', synchronization=synchronization2,
            active_domain=SynchDomain.Time)
class PoolSoftwareTriggerGateTestCase(unittest.TestCase):
    """Parameterizable integration test of the PoolTGGeneration action and
    the SoftwareTriggerGateController.

    Using insertTest decorator, one can add tests of a particular trigger/gate
    characteristic.
    """

    def setUp(self):
        """Create a Controller, TriggerGate and PoolTGGeneration objects from
        dummy configurations
        """
        unittest.TestCase.setUp(self)
        pool = FakePool()

        self.sw_tg_ctrl = createPoolController(pool, softwarePoolTGCtrlConf01)
        self.sw_tg = createPoolTriggerGate(pool, self.sw_tg_ctrl,
                                              dummyTriggerGateConf01)
        # marrying the element with the controller
        self.sw_tg_ctrl.add_element(self.sw_tg)

        # TODO: at the moment of writing this test, the configuration of
        # TGGenerationAction s
        self.cfg = createPoolTGGenerationConfiguration((self.sw_tg_ctrl,),
                                                       ((self.sw_tg,),))

        # marrying the element with the action
        self.tg_action = PoolTGGeneration(self.sw_tg)
        self.tg_action.add_element(self.sw_tg)

        # creating a dummy trigger gate receiver, it will serve to determine if
        # the triggers were correctly generated
        # TODO: For the moment the insertion of the receiver is very "nasty"
        # refactor it, whenever a correct EventChannel mechanism is
        self.tg_receiver = TriggerGateReceiver()

        self.tg_action.add_listener(self.tg_receiver)

    def generation(self, synchronization, active_domain=None,
                   passive_domain=None):
        """Verify that the created PoolTGAction start_action starts correctly
        the involved controller."""
        axis = dummyTriggerGateConf01["axis"]
        if active_domain:
            self.sw_tg_ctrl.set_axis_attr(axis, "active_domain", active_domain)
        if passive_domain:
            self.sw_tg_ctrl.set_axis_attr(axis, "passive_domain", passive_domain)
        args = ()
        kwargs = {'config': self.cfg,
                  'synchronization': synchronization
                 }
        self.tg_action.start_action(*args, **kwargs)
        self.tg_action.action_loop()

        # obtaining parameters for further comparison with the results
        synchronization = synchronization[0] # prepared for just one group
        repetitions = synchronization[SynchParam.Repeats]
        active_interval = synchronization[SynchParam.Active][SynchDomain.Time]
        total_interval = synchronization[SynchParam.Total][SynchDomain.Time]
        passive_interval = total_interval - active_interval

        # testing number of received triggers
        received_triggers = self.tg_receiver.count
        msg = ('Received triggers: %d does not correspond to generated: %d' %\
               (received_triggers, repetitions))
        self.assertEqual(received_triggers, repetitions, msg)

        # testing cycle-to-cycle jitter
        c2c_mean_limit = 0.0006
        c2c_std_limit = 0.00001
        c2c_max_limit = 0.00001
        c2c_mean, c2c_std, c2c_max = self.tg_receiver.calc_cycletocycle()
        msg = 'Mean cycle-to-cycle jitter (%f) is higher than limit (%f)' %\
                                                    (c2c_mean, c2c_mean_limit)
        self.assertLess(c2c_mean, c2c_mean_limit, msg)
        msg = 'Std cycle-to-cycle jitter (%f) is higher than limit (%f)' %\
                                                      (c2c_std, c2c_std_limit)
        self.assertLess(c2c_mean, c2c_mean_limit, msg)
        msg = 'Max cycle-to-cycle jitter (%f) is higher than limit (%f)' %\
                                                      (c2c_max, c2c_max_limit)
        self.assertLess(c2c_mean, c2c_mean_limit, msg)

        # testing characteristics
        characteristics = self.tg_receiver.calc_characteristics()
        i = 1

        while i < (repetitions - 1):
            intervals = characteristics[i]
            measured_active_interval = intervals[0]
            measured_passive_interval = intervals[1]
            msg = ('Measured active interval: %f does not correspond to ' +\
                   'generated: %f' ) % (measured_active_interval,
                                        active_interval)
            self.assertAlmostEqual(measured_active_interval, active_interval,
                                   delta=.002, msg=msg)
            msg = ('Measured passive interval: %f does not correspond to ' +\
                   'generated: %f') % (measured_passive_interval,
                                       passive_interval)
            self.assertAlmostEqual(measured_passive_interval, passive_interval,
                                   delta=.002, msg=msg)
            i += 1

    def tearDown(self):
        unittest.TestCase.tearDown(self)