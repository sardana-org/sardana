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

import time
import threading
import numpy

import unittest

from sardana import State
from sardana.pool.poolcontrollers.DummyMotorController import Motion
from sardana.pool.pooldefs import SynchParam
from sardana.sardanaattribute import SardanaAttribute
from taurus.core.util.log import Logger

__all__ = ['BaseControllerTestCase', 'TriggerGateControllerTestCase',
           'PositionGenerator', 'TriggerGateReceiver']

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
    DEBUG = False

    def setUp(self):
        self.logger = Logger('BaseControllerTestCase')
        if self.DEBUG:
            self.logger.setLogLevel(Logger.Debug)

        if self.KLASS is None:
            raise Exception('Ctrl klass has not been defined')
        name = 'test_ctrl'
        self.ctrl = self.KLASS(name, self.PROPS)
        self.pre_AddDevice_hook()
        self.ctrl.AddDevice(self.AXIS)

    def tearDown(self):
        if self.ctrl is not None:
            self.ctrl.DeleteDevice(self.AXIS)

    def axisPar(self, name, value, expected_value=None):
        """ Helper for test the SetAxisPar & GetaxisPar methods
        """
        axis = self.AXIS
        if expected_value is None:
            expected_value = value
        self.ctrl.SetAxisPar(axis, name, value)
        r_value = self.ctrl.GetAxisPar(axis, name)
        msg = ('The %s value is %s, and the expected value is %s'
               % (name, r_value, expected_value))
        self.assertEqual(r_value, expected_value, msg)

    def stateOne(self, expected_state=State.On):
        """ Helper for test the stateOne method
        """
        sta, status = self.ctrl.StateOne(self.AXIS)
        msg = ('The current state of axis(%d) is %d when expected, %d'
               % (self.AXIS, sta, expected_state))
        self.assertEqual(sta, expected_state, msg)

    def start_action(self, configuration):
        """ This method set the axis parameters and pre start the axis.
        """
        for key, value in list(configuration.items()):
            self.axisPar(key, value)
        self.ctrl.SynchOne(configuration)

    def pre_AddDevice_hook(self):
        pass


class TriggerGateControllerTestCase(unittest.TestCase, BaseControllerTestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        BaseControllerTestCase.setUp(self)
        self.isAborted = False

    def tearDown(self):
        BaseControllerTestCase.tearDown(self)
        unittest.TestCase.tearDown(self)

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
        self.configuration = configuration
        repetitions = 0
        for group in configuration:
            repetitions += group[SynchParam.Repeats]
        # store repeats for the assers against received triggers
        self.repetitions = repetitions
        self.ctrl.SynchOne(self.AXIS, configuration)
        # execute Hook
        self.post_configuration_hook()
        # PreStartOne the axis
        self.ctrl.PreStartOne(self.AXIS)
        self.ctrl.StartOne(self.AXIS)
        while self.ctrl.StateOne(self.AXIS)[0] == State.Moving:
            time.sleep(0.001)
        self.post_generation_hook()
        state, status = self.ctrl.StateOne(self.AXIS)
        msg = ('The axis %d is not Stopped, its status is %s'
               % (self.AXIS, status))
        self.assertEqual(state, State.get('On'), msg)

    def abort(self, configuration, abort):
        """ Helper for test the abort
        """
        self.configuration = configuration
        self.ctrl.SynchOne(self.AXIS, configuration)
        self.post_configuration_hook()
        # PreStartOne the axis
        self.ctrl.PreStartOne(self.AXIS)
        self.ctrl.StartOne(self.AXIS)
        while self.ctrl.StateOne(self.AXIS)[0] == State.Moving:
            time.sleep(abort)
            self.ctrl.AbortOne(self.AXIS)
        self.isAborted = True
        self.post_generation_hook()
        state, status = self.ctrl.StateOne(self.AXIS)
        msg = ('The axis %d is not Stopped, its status is %s'
               % (self.AXIS, status))
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


class TriggerGateReceiver(object):
    '''Software TriggerGateReceiver which captures timestamps whenever an event
    comes. Provides useful methods for calculating the event generation
    performance
    '''
    # TODO: add more jitter measurements e.g. drift

    def __init__(self):
        self.active_events = {}
        self.passive_events = {}

    def getCount(self):
        count = len(list(self.passive_events.keys()))
        return count

    count = property(getCount)

    def event_received(self, *args, **kwargs):
        # store also a timestamp of the start event when it will be implemented
        timestamp = time.time()
        _, type_, value = args
        name = type.name
        if name == "active":
            self.active_events[value] = timestamp
        elif name == "passive":
            self.passive_events[value] = timestamp
        else:
            raise ValueError('Unknown EventType')

    def calc_characteristics(self):
        # TODO: refactor the characteristics calculation method to use numpy
        i = 0
        count = self.count
        characteristics = {}
        # there is no active event ending the last passive period, that's why
        # calculate characteristics until (count - 1)
        while i < (count - 1):
            t1 = self.active_events[i]
            t2 = self.passive_events[i]
            t3 = self.active_events[i + 1]
            active_period = t2 - t1
            passive_period = t3 - t2
            characteristics[i] = (active_period, passive_period)
            i += 1
        return characteristics

    def calc_cycletocycle(self):
        '''Calculate the cycle-to-cycle jitter characteristics: mean, std and max.
        Cycle-to-cycle jitter is a difference between a cycle period and a cycle
        period before it. To calculate one cycle-to-cycle jitter one needs
        exactly 3 active events:

        c2c_jitter_1 = cycle_2 - cycle_1
        cycle_2 = active_3 - active_2
        cycle_1 = active_2 - active_1
        '''
        i = 0
        count = self.count
        periods = []
        mean_c2c, std_c2c, max_c2c = 0, 0, 0
        # there is no active event ending the last passive period, that's why
        # calculate characteristics until (count - 1)
        while i < (count - 1):
            t1 = self.active_events[i]
            t2 = self.active_events[i + 1]
            period = t2 - t1
            periods.append(period)
            i += 1
        if len(periods) > 0:
            periods_array = numpy.array(periods)
            print(periods_array)
            c2c = numpy.diff(periods_array)
            mean_c2c = c2c.mean()
            std_c2c = c2c.std()
            max_c2c = c2c.max()
        return mean_c2c, std_c2c, max_c2c
