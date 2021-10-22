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

from sardana.util.motion import Motor, MotionPath


@pytest.fixture(scope="module", params=[
    {
        "min_vel": 0,
        "max_vel": 1,
        "accel_time": 0.1,
        "decel_time": 0.1
    },
    {
        "min_vel": 0,
        "max_vel": 2,
        "accel_time": 0.1,
        "decel_time": 0.1
    }])
def motor(request):
    return Motor(**request.param)


def test_motor():
    min_vel = 0
    max_vel = 10
    accel_time = 1
    decel_time = 1
    m = Motor(min_vel, max_vel, accel_time, decel_time)
    assert m.getMinVelocity() == min_vel
    assert m.getMaxVelocity() == max_vel
    assert m.getAccelerationTime() == accel_time
    assert m.getDecelerationTime() == decel_time


def motor01():
    return Motor(min_vel=0, max_vel=1, accel_time=0.1, decel_time=0.1)


def motor02():
    return Motor(min_vel=0, max_vel=1, accel_time=0.001, decel_time=0.001)


def motor03():
    return Motor(min_vel=1, max_vel=2, accel_time=1, decel_time=2)


@pytest.mark.parametrize(
    "motor,start,end,expected_at_max_vel_displacement", [
    (motor01(), 0, 1, 0.9),
    (motor01(), 1, 0, 0.9),
    (motor01(), 0.1, 0, 0),
    (motor02(), 0.1, 0, 0.099),
    (motor03(), 0, 0.25, 0)
    ]
)
def test_motion_path(motor, start, end, expected_at_max_vel_displacement):
    motion_path = MotionPath(motor, start, end)
    motion_path.info()
    assert motion_path.at_max_vel_displacement == expected_at_max_vel_displacement
