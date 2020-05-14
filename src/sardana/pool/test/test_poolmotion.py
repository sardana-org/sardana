#!/usr/bin/env python

##############################################################################
##
# This file is part of Sardana
##
# http://www.sardana-controls.org/
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

import unittest

from sardana.pool.poolmotion import PoolMotion
from sardana.sardanadefs import State
from sardana.pool.test import (FakePool, createPoolController,
                               createPoolMotor, dummyPoolMotorCtrlConf01,
                               dummyMotorConf01, dummyMotorConf02)


class PoolMotionTestCase(unittest.TestCase):
    """Unittest of PoolMotion class"""

    def setUp(self):
        """Create a Controller, and Motor objects from dummy configurations """
        unittest.TestCase.setUp(self)
        try:
            from mock import Mock
        except ImportError:
            self.skipTest("mock module is not available")
        pool = FakePool()
        dummy_mot_ctrl = createPoolController(pool, dummyPoolMotorCtrlConf01)
        self.dummy_mot = createPoolMotor(pool, dummy_mot_ctrl,
                                         dummyMotorConf01)
        self.dummy_mot2 = createPoolMotor(pool, dummy_mot_ctrl,
                                          dummyMotorConf02)
        dummy_mot_ctrl.add_element(self.dummy_mot)
        pool.add_element(dummy_mot_ctrl)
        pool.add_element(self.dummy_mot)
        pool.add_element(self.dummy_mot2)

        # {moveable: (position, dial_position,
        #             do_backlash, backlash, instability_time=None)}
        self.items = {self.dummy_mot: (0, 0, False, 0),
                      self.dummy_mot2: (0, 0, False, 0)}
        # Create mock and define its functions
        ctrl_methods = ['PreStartAll', 'StartAll', 'PreStartOne', 'StartOne',
                        'PreStateAll', 'StateAll', 'PreStateOne', 'StateOne',
                        'PreReadAll', 'PreReadOne', 'ReadOne', 'ReadAll',
                        'PreStopAll', 'StopAll', 'PreStopOne', 'StopOne',
                        'PreAbortAll', 'AbortAll', 'PreAbortOne', 'AbortOne']
        self.mock_mot_ctrl = Mock(spec=ctrl_methods)
        self.mock_mot_ctrl.StateOne.return_value = (State.Moving, 'moving')

        dummy_mot_ctrl.ctrl = self.mock_mot_ctrl
        self.motionaction = PoolMotion(self.dummy_mot)
        self.motionaction.add_element(self.dummy_mot)
        self.motionaction.add_element(self.dummy_mot2)

    def stopMotion(self):
        """Method used to change the controller (mock) state"""
        self.dummy_mot.stop()

    def test_stop(self):
        """Verify motion stop call chain."""
        from mock import call
        args = ()
        kwargs = {'items': self.items}
        # starting action
        self.motionaction.start_action(*args, **kwargs)
        # stopping the motion
        # self.stopMotion()
        args = ()
        kwargs = {'items': self.items}
        self.motionaction.stop_action(*args, **kwargs)

        # verifying that the stop has called all the controller methods chain
        self.mock_mot_ctrl.assert_has_calls([call.PreStopAll(),
                                             call.PreStopOne(1,),
                                             call.StopOne(1,),
                                             call.PreStopOne(2,),
                                             call.StopOne(2,),
                                             call.StopAll()])

    def test_abort(self):
        """Verify motion abort call chain."""
        from mock import call
        args = ()
        kwargs = {'items': self.items}
        # starting action
        self.motionaction.start_action(*args, **kwargs)
        args = ()
        kwargs = {'items': self.items}
        self.motionaction.abort_action(*args, **kwargs)

        # verifying that the abort has called all the controller methods chain
        self.mock_mot_ctrl.assert_has_calls([call.PreAbortAll(),
                                             call.PreAbortOne(1,),
                                             call.AbortOne(1,),
                                             call.PreAbortOne(2,),
                                             call.AbortOne(2,),
                                             call.AbortAll()])

    def tearDown(self):
        self.motionaction = None
        self.mock_mot_ctrl = None
        self.cfg = None
        self.dummy_mot = None
        unittest.TestCase.tearDown(self)
