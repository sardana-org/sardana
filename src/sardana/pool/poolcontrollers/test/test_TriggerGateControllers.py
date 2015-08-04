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

import time
from taurus.external import unittest
from taurus.test.base import insertTest
from sardana import State
from sardana.pool.poolcontrollers.test.base import BaseControllerTestCase
from sardana.pool.poolcontrollers.SoftwareTriggerGateController import SoftwareTriggerGateController


class TriggerGateBaseControllerTestCase(unittest.TestCase,
                                        BaseControllerTestCase):
    KLASS = None
    NAME = ''
    CONF = {}
    BaseControllerTestCase.CONF.update(CONF)
    AXIS = 1

    def setUp(self):
        unittest.TestCase.setUp(self)
        BaseControllerTestCase.setUp(self)

    def tearDown(self):
        BaseControllerTestCase.tearDown(self)
        unittest.TestCase.tearDown(self)

    def pregeneration(self, offset, active, passive, repetitions):
        """Method to configurate the trigger/gate controller.
        Set the axis parameters and pre start the axis.
        """
        # Configuration
        self.axisPar('offset', offset)
        self.axisPar('active_interval', active)
        self.axisPar('passive_interval', passive)
        self.axisPar('repetitions', repetitions)
        # Pre Start the axis
        self.ctrl.PreStartOne(self.AXIS)

    def generation(self, offset, active, passive, repetitions):
        """ Helper for test a simple generation
        """
        self.pregeneration(offset, active, passive, repetitions)
        self.ctrl.StartOne(self.AXIS)
        while self.ctrl.StateOne(self.AXIS)[0] == State.Moving:
            time.sleep(active)
        state, status = self.ctrl.StateOne(self.AXIS)
        msg = ('The axis %d is not Stopped, its status is %s'
               %(self.AXIS, status))
        self.assertEqual(state, State.get('On'), msg)

    def abort(self, offset, active, passive, repetitions, abort):
        """ Helper for test the abort
        """
        self.pregeneration(offset, active, passive, repetitions)
        self.ctrl.StartOne(self.AXIS)
        while self.ctrl.StateOne(self.AXIS)[0] == State.Moving:
            time.sleep(abort)
            self.ctrl.AbortOne(self.AXIS)
        state, status = self.ctrl.StateOne(self.AXIS)
        msg = ('The axis %d is not Stopped, its status is %s'
               %(self.AXIS, status))
        self.assertEqual(state, State.get('On'), msg)

@insertTest(helper_name='generation', offset=0, active=.1, passive=.1,
            repetitions=10)
@insertTest(helper_name='abort', offset=0, active=.1, passive=.1,
            repetitions=10, abort=.1)
class SoftwareTriggerGateControllerTestCase(TriggerGateBaseControllerTestCase):
    KLASS = SoftwareTriggerGateController
    NAME = 'stg_ctrl'
    CONF = {}
    TriggerGateBaseControllerTestCase.CONF.update(CONF)