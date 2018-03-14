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

__all__ = ['FakePool', 'FakeElement']

from sardana.pool.poolcontrollermanager import ControllerManager


class FakePool(object):
    ''' Fake class to simulate the behavior of the Pool class
    '''
    acq_loop_sleep_time = 0.1
    acq_loop_states_per_value = 10
    motion_loop_sleep_time = 0.1
    motion_loop_states_per_position = 10
    drift_correction = True

    def __init__(self, poolpath=[], loglevel=None):
        self.ctrl_manager = ControllerManager()
        if loglevel:
            self.ctrl_manager.setLogLevel(loglevel)
        self.ctrl_manager.set_pool(self)
        self.ctrl_manager.setControllerPath(poolpath)
        self.elements = {}
        self.elements_by_full_name = {}
        self._freeId = 1

    def add_element(self, element):
        self.elements[element.id] = element
        self.elements_by_full_name[element.full_name] = element

    def get_element(self, id):
        return self.elements[id]

    def get_element_by_full_name(self, full_name):
        return self.elements_by_full_name[full_name]

    def get_free_id(self):
        while True:
            try:
                self.get_element(self._freeId)
                self._freeId += 1
            except KeyError:
                return self._freeId

    def get_free_name(self, base_name):
        num = 1
        while True:
            try:
                self.get_element_by_full_name(base_name + "%s" % num)
                num += 1
            except KeyError:
                return base_name + "%s" % num

    def get_manager(self):
        return self.ctrl_manager

    def cleanup(self):
        self.ctrl_manager.cleanUp()
        self.ctrl_manager.reInit()
        self.elements = {}
        self.elements_by_full_name = {}

# TODO: this should be a mock


class FakeElement(object):
    '''Fake pool element'''

    def __init__(self, pool, name="FakeElement"):
        self.pool = pool
        self.name = name

    def on_element_changed(self, *args, **kwargs):
        pass
