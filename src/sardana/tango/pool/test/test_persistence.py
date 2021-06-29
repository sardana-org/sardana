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
import os

import PyTango
import unittest
from taurus.test import insertTest
from sardana.tango.pool.test import BasePoolTestCase
from sardana.tango.core.util import get_free_alias

info1 = ('Motor', 'DummyMotorController', 'DummyMotorController')
info2 = ('TriggerGate', 'DummyTriggerGateController',
         'DummyTriggerGateController')


@insertTest(helper_name='check_elems_presistence',
            test_method_doc='Test persistence of dummy Motor elements',
            info=info1)
@insertTest(helper_name='check_elems_presistence',
            test_method_doc='Test persistence of dummy TriggerGate elements',
            info=info2)
class PersistenceTestCase(BasePoolTestCase, unittest.TestCase):
    """ Test the persistence of the Sardana Tango elements.
    """

    def check_elems_presistence(self, info):
        """Helper method to test the elements persistence. The actions are:
            - creation of controller and element
            - restart Pool
            - check if element persist

        :param info: information about controller (type, library, class)
        :type info: tuple<str>
        """
        # Create controller
        self.do_element_cleanup = False
        sar_type, lib, cls = info
        base_name = "ctrl_persistent_" + cls
        self.ctrl_name = get_free_alias(PyTango.Database(), base_name)
        self.pool.CreateController([sar_type, lib, cls, self.ctrl_name])

        # Create element
        base_name = "elem_persistent_" + cls
        self.elem_name = get_free_alias(PyTango.Database(), base_name)
        axis = 1
        self.pool.CreateElement([sar_type, self.ctrl_name, str(axis),
                                 self.elem_name])
        # Restart Pool
        self._starter.stopDs(hard_kill=True)
        self._starter.startDs(wait_seconds=20)
        # Check if the element exists
        try:
            obj = PyTango.DeviceProxy(self.elem_name)
            # the element is persistent, cleanup is necessary
            self.do_element_cleanup = True
        except:
            obj = None
        msg = 'The element "%s" does not exist after restarting the Pool' %\
            (self.elem_name)
        self.assertIsNotNone(obj, msg)

    def tearDown(self):
        """Remove the elements and the controllers
        """
        cleanup_success = True
        if self.do_element_cleanup:
            try:
                if os.name != "nt":
                    self.pool.DeleteElement(self.elem_name)
            except:
                cleanup_success = False
        try:
            if os.name != "nt":
                self.pool.DeleteElement(self.ctrl_name)
        except:
            cleanup_success = False
        BasePoolTestCase.tearDown(self)
        if not cleanup_success:
            raise Exception("Cleanup failed. Database may be left dirty.")
