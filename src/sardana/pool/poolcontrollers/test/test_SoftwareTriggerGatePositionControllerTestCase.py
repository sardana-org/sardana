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
from sardana.pool.pooldefs import SynchDomain, SynchParam
from sardana.pool.poolcontrollers.test import (TriggerGateControllerTestCase,
                                               PositionGenerator,
                                               TriggerGateReceiver)
from sardana.pool.poolcontrollers.SoftwareTriggerGatePositionController import\
                                        SoftwareTriggerGatePositionController

synchronization1 = [{SynchParam.Delay: {SynchDomain.Position: 0},
                     SynchParam.Initial: {SynchDomain.Position: 0},
                     SynchParam.Active: {SynchDomain.Position: .1},
                     SynchParam.Total: {SynchDomain.Position: 1},
                     SynchParam.Repeats: 10}]

synchronization2 = [{SynchParam.Delay: {SynchDomain.Position: 0},
                     SynchParam.Initial: {SynchDomain.Position: 0},
                     SynchParam.Active: {SynchDomain.Position: -1},
                     SynchParam.Total: {SynchDomain.Position: -1.1},
                     SynchParam.Repeats: 10}]

@insertTest(helper_name='generation', configuration=synchronization1)
@insertTest(helper_name='abort', configuration=synchronization2, abort=0.5)
class SoftwareTriggerGatePositionControllerTestCase(TriggerGateControllerTestCase):
    KLASS = SoftwareTriggerGatePositionController

    def post_configuration_hook(self):
        # Configure and run the position generator
        start_pos = 0
        end_pos = 10
        period = 0.01
        self.generator = PositionGenerator(start_pos, end_pos, period)
        # create and add listeners
        self._device = self.ctrl.GetDevice(self.AXIS)
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
        conf = self.ctrl.GetConfiguration(self.AXIS)
        repetitions = 0
        for group in conf:
            repetitions += group[SynchParam.Repeats]
        msg = ('Received triggers: %d does not correspond to generated: %d' %\
               (received_triggers, repetitions))
        if not self.isAborted:
            self.assertEqual(received_triggers, repetitions, msg)
