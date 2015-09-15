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
from sardana.pool.pooldefs import SynchDomain

from sardana.pool.test import (FakePool, createPoolController,
                               createPoolTriggerGate, softwarePoolTGCtrlConf01,
                               dummyTriggerGateConf01, 
                               createPoolTGGenerationConfiguration)

from sardana.pool.poolcontrollers.test import (TriggerGateControllerTestCase,
                                               TriggerGateReceiver)
from sardana.pool.poolcontrollers.SoftwareTriggerGateController import\
                                                  SoftwareTriggerGateController

synchronization1 = [dict(delay={SynchDomain.Time:(None, 0)},
                         active={SynchDomain.Time:(None, .03)},
                         total={SynchDomain.Time:(None, .1)},
                         repeats=0)
                    ]
synchronization2 = [dict(delay={SynchDomain.Time:(None, 0)},
                         active={SynchDomain.Time:(None, .01)},
                         total={SynchDomain.Time:(None, .02)},
                         repeats=10)
                    ]
synchronization3 = [dict(delay={SynchDomain.Time:(None, 0)},
                         active={SynchDomain.Time:(None, .1)},
                         total={SynchDomain.Time:(None, .1)},
                         repeats=0)
                    ]
synchronization4 = [dict(delay={SynchDomain.Time:(None, 0)},
                         active={SynchDomain.Time:(None, .1)},
                         total={SynchDomain.Time:(None, .15)},
                         repeats=3)
                    ]

@insertTest(helper_name='generation',  configuration=synchronization1)
@insertTest(helper_name='abort', configuration=synchronization2, abort=.1)
class SoftwareTriggerGateControllerTestCase(TriggerGateControllerTestCase):
    KLASS = SoftwareTriggerGateController

@insertTest(helper_name='generation', offset=0, active_interval=.1,
                                              passive_interval=.1, repetitions=0)
@insertTest(helper_name='generation', offset=0, active_interval=.01,
                                              passive_interval=.01, repetitions=10)
@insertTest(helper_name='generation', offset=0, active_interval=.01,
                                             passive_interval=.02, repetitions=10)
@insertTest(helper_name='generation', offset=0, active_interval=0.1,
                                             passive_interval=0.05, repetitions=3)
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

        sw_tg_ctrl = createPoolController(pool, softwarePoolTGCtrlConf01)
        self.sw_tg = createPoolTriggerGate(pool, sw_tg_ctrl,
                                              dummyTriggerGateConf01)
        # marrying the element with the controller
        sw_tg_ctrl.add_element(self.sw_tg)

        # TODO: at the moment of writing this test, the configuration of
        # TGGenerationAction s
        self.cfg = createPoolTGGenerationConfiguration((sw_tg_ctrl,),
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

    def generation(self, offset, active_interval, passive_interval, repetitions):
        """Verify that the created PoolTGAction start_action starts correctly
        the involved controller."""
        args = ()
        # composing synchronization configuration
        total_interval = active_interval + passive_interval
        synchronization = [dict(delay={SynchDomain.Time:(None, offset)},
                                active={SynchDomain.Time:(None, active_interval)},
                                total={SynchDomain.Time:(None, total_interval)},
                                repeats=repetitions)
                           ]
        kwargs = {'config': self.cfg,
                  'synchronization': synchronization
                 }
        self.tg_action.start_action(*args, **kwargs)
        self.tg_action.action_loop()

        # testing number of received triggers
        received_triggers = self.tg_receiver.count
        msg = ('Received triggers: %d does not correspond to generated: %d' %\
               (received_triggers, repetitions))
        self.assertEqual(received_triggers, repetitions, msg)

        # testing cycle-to-cycle jitter
        c2c_mean_limit = 0.0005
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
        i = 0
        while i < (repetitions - 1):
            intervals = characteristics[i]
            measured_active_interval = intervals[0]
            measured_passive_interval = intervals[1]
            msg = ('Measured active interval: %f does not correspond to ' +\
                   'generated: %f' ) % (measured_active_interval, active_interval)
            self.assertAlmostEqual(measured_active_interval, active_interval,
                                   delta=.002, msg=msg)
            msg = ('Measured passive interval: %f does not correspond to ' +\
                   'generated: %f') % (measured_passive_interval, passive_interval)
            self.assertAlmostEqual(measured_passive_interval, passive_interval,
                                   delta=.002, msg=msg)
            i += 1

    def tearDown(self):
        unittest.TestCase.tearDown(self)