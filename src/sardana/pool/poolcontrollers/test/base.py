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
__all__ = ['BaseControllerTestCase', 'TriggerGateControllerTestCase',
           'PositionGenerator']

import time, threading
import unittest

from sardana import State
from sardana.pool.poolcontrollers.DummyMotorController import Motion
from sardana.sardanaattribute import SardanaAttribute

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

    def axisPar(self, name, value, expected_value=None):
        axis = self.AXIS
        if expected_value is None:
            expected_value = value
        self.ctrl.SetAxisPar(axis, name, value)
        r_value = self.ctrl.GetAxisPar(axis, name)
        msg = ('The %s value is %s, and the expected value is %s'
               %(name, r_value, expected_value))
        self.assertEqual(r_value, expected_value, msg)


class TriggerGateControllerTestCase(unittest.TestCase, BaseControllerTestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        BaseControllerTestCase.setUp(self)

    def tearDown(self):
        BaseControllerTestCase.tearDown(self)
        unittest.TestCase.tearDown(self)

    def pregeneration(self, configuration):
        """Method to configurate the trigger/gate controller.
        Set the axis parameters and pre start the axis.
        """
        # Configuration
        for key, value in configuration.items():
            self.axisPar(key, value)

        # Pre Start the axis
        self.ctrl.PreStartOne(self.AXIS)

    def post_configuration_hook(self):
        ''' Hook for post configure actions
        '''
        pass

    def post_generation_hook(self):
        ''' Hook for post generation actions
        '''
        pass

    def generation(self, configuration):
        """ Helper for test a simple generation
        """
        self.pregeneration(configuration)
        # execute Hook
        self.post_configuration_hook()
        self.ctrl.StartOne(self.AXIS)
        while self.ctrl.StateOne(self.AXIS)[0] == State.Moving:
            time.sleep(configuration.get('active_interval'))
        self.post_generation_hook()
        state, status = self.ctrl.StateOne(self.AXIS)
        msg = ('The axis %d is not Stopped, its status is %s'
               %(self.AXIS, status))
        self.assertEqual(state, State.get('On'), msg)

    def abort(self, configuration, abort):
        """ Helper for test the abort
        """
        self.pregeneration(configuration)
        self.post_configuration_hook()
        self.ctrl.StartOne(self.AXIS)
        while self.ctrl.StateOne(self.AXIS)[0] == State.Moving:
            time.sleep(abort)
            self.ctrl.AbortOne(self.AXIS)
        self.post_generation_hook()
        state, status = self.ctrl.StateOne(self.AXIS)
        msg = ('The axis %d is not Stopped, its status is %s'
               %(self.AXIS, status))
        self.assertEqual(state, State.get('On'), msg)

class PositionGenerator(threading.Thread):
    """ It is a position generator. A Sardana Motion class is used for simulate
    the motor. The attribute value has the current user position of the motor.
    """
    def __init__(self, start_pos, end_pos, period):
        """
        :param start_pos: start position for the motion
        :param end_pos: end position for the motion
        :param period: nap time between fireevents
        :return:
        """
        threading.Thread.__init__(self)
        self.motor = Motion()
        self.motor.setMinVelocity(0)
        self.motor.setMaxVelocity(10)
        self.motor.setAccelerationTime(1)
        self.motor.setDecelerationTime(1)
        self.motor.setCurrentPosition(0)
        self._start_pos = start_pos
        self._end_pos = end_pos
        self._period = period
        self.value = SardanaAttribute(self, name='Position',
                                      initial_value=0)

    def run(self):
        """
        Start the motion and update the SardanaAttribute value with the current
        position of the motion between every nap period
        """
        self.motor.startMotion(self._start_pos, self._end_pos)
        while self.motor.isInMotion():
            value = self.motor.getCurrentUserPosition()
            self.value.set_value(value, timestamp=time.time(), propagate=1)
            time.sleep(self._period)
        value = self.motor.getCurrentUserPosition()
        self.value.set_value(value, timestamp=time.time(), propagate=1)

    def getMotor(self):
        """ Get the motion object
        """
        return self.motor

    def setStartPos(self, pos):
        """ Update start position
        """
        self._start_pos = pos
        self.value.set_value(pos)

    def setEndPos(self, pos):
        """ Update end position
        """
        self._end_pos = pos

    def setPeriod(self, time):
        """ Update the nap time
        """
        self._end_pos = time

    def add_listener(self, listener):
        self.value.add_listener(listener)

    def remove_listener(self, listener):
         self.value.remove_listener(listener)
