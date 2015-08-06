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
__all__ = ['BaseControllerTestCase', 'TriggerGateControllerTestCase']

import time
import unittest

from sardana import State

class BaseControllerTestCase(object):
    """ Base test case for unit testing arbitrary controllers.
    This class will create a controller instance and define an axis from the
    class member attributes:
        KLASS <type> controller class
        PROPS <dict> properties of the controller
        AXIS <int> number of the axis
    """
    KLASS = None
    PROPS = {}
    AXIS = 1

    def setUp(self):
        if self.KLASS is None:
            raise Exception('Ctrl klass has not been defined')
        name = 'test_ctrl'
        self.ctrl = self.KLASS(name, self.PROPS)
        self.ctrl.AddDevice(self.AXIS)

    def tearDown(self):
        if self.ctrl is not None:
            self.ctrl.DeleteDevice(self.AXIS)

    def axisPar(self, parameter, value):
        axis = self.AXIS
        self.ctrl.SetAxisPar(axis, parameter, value)
        r_value = self.ctrl.GetAxisPar(axis, parameter)
        msg = ('The %s value is %s, and the expected value is %s'
               %(parameter, r_value, value))
        self.assertEqual(value, r_value, msg)


class TriggerGateControllerTestCase(unittest.TestCase, BaseControllerTestCase):

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