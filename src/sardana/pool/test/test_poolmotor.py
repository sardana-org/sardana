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

import pytest

from sardana import State
from sardana.pool.test import (FakePool, createPoolController,
                               createPoolMotor, dummyPoolMotorCtrlConf01,
                               dummyMotorConf01)


def StateOne_state(self, axis):
    return State.On


def StateOne_state_status(self, axis):
    return State.On, "Status"


def StateOne_state_status_limits(self, axis):
    return State.On, "Status", 0


@pytest.mark.parametrize("mock_StateOne", [StateOne_state,
                                           StateOne_state_status,
                                           StateOne_state_status_limits])
def test_state(monkeypatch, mock_StateOne):
    """Test variants of StateOne return value:
    - state
    - state, status
    - state, status, limit_switches
    """
    pool = FakePool()
    # when SEP19 gets implemented it should be possible to mock directly
    # the imported class
    DummyMotorController = pool.ctrl_manager.getControllerClass(
        "DummyMotorController")
    monkeypatch.setattr(DummyMotorController, "StateOne", mock_StateOne)
    mot_ctrl = createPoolController(pool, dummyPoolMotorCtrlConf01)
    mot = createPoolMotor(pool, mot_ctrl, dummyMotorConf01)
    mot_ctrl.add_element(mot)
    pool.add_element(mot_ctrl)
    pool.add_element(mot)
    assert mot.state == State.On
    assert type(mot.status) == str
    assert mot.limit_switches.value == (False, ) * 3
