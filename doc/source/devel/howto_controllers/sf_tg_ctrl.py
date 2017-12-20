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

"""This file contains the code for an hypothetical Springfield trigger/gate
controller used in documentation"""

import time

import springfieldlib

from sardana import State
from sardana.pool.controller import TriggerGateController


class SpringfieldBaseTriggerGateController(TriggerGateController):
    """The most basic controller intended from demonstration purposes only.
    This is the absolute minimum you have to implement to set a proper trigger
    controller able to get a trigger value, get a trigger state and do an
    acquisition.

    This example is so basic that it is not even directly described in the
    documentation"""

    def __init__(self, inst, props, *args, **kwargs):
        """Constructor"""
        super(SpringfieldBaseTriggerGateController, self).__init__(
            inst, props, *args, **kwargs)
        self.springfield = springfieldlib.SpringfieldTriggerHW()

    def StateOne(self, axis):
        """Get the specified trigger state"""
        springfield = self.springfield
        state = springfield.getState(axis)
        if state == 1:
            return State.On, "Trigger is stopped"
        elif state == 2:
            return State.Moving, "Trigger is running"
        elif state == 3:
            return State.Fault, "Trigger has an error"

    def StartOne(self, axis, value=None):
        """acquire the specified trigger"""
        self.springfield.StartChannel(axis)

    def SynchOne(self, axis, synchronization):
        self.springfield.SynchChannel(axis, synchronization)

    def StopOne(self, axis):
        """Stop the specified trigger"""
        self.springfield.stop(axis)


from sardana import DataAccess
from sardana.pool.controller import Type, Description, DefaultValue, Access, FGet, FSet


class SpringfieldTriggerGateController(TriggerGateController):

    def __init__(self, inst, props, *args, **kwargs):
        super(SpringfieldTriggerGateController, self).__init__(
            inst, props, *args, **kwargs)

        # initialize hardware communication
        self.springfield = springfieldlib.SpringfieldTriggerHW()

        # do some initialization
        self._triggers = {}

    def AddDevice(self, axis):
        self._triggers[axis] = True

    def DeleteDevice(self, axis):
        del self._triggers[axis]

    StateMap = {
        1: State.On,
        2: State.Moving,
        3: State.Fault,
    }

    def StateOne(self, axis):
        springfield = self.springfield
        state = self.StateMap[springfield.getState(axis)]
        status = springfield.getStatus(axis)
        return state, status

    def SynchOne(self, axis, synchronization):
        self.springfield.SynchChannel(axis, synchronization)

    def StartOne(self, axis, position):
        self.springfield.StartChennel(axis, position)

    def StopOne(self, axis):
        self.springfield.stop(axis)

    def AbortOne(self, axis):
        self.springfield.abort(axis)
