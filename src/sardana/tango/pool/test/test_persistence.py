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
import PyTango
from taurus.external import unittest
from taurus.test import insertTest
from sardana.tango.pool.test import BasePoolTestCase
from sardana.tango.core.util import get_free_alias

@insertTest(helper_name='check_elems_presistence', 
            test_method_doc='Test persitance of dummy STG elements',
            cls = 'SoftwareTriggerGateController')
@insertTest(helper_name='check_elems_presistence', 
            test_method_doc='Test persitance of dummy TG elements',
            cls = 'DummyTriggerGateController')
@insertTest(helper_name='check_elems_presistence', 
            test_method_doc='Test persitance of dummy motors elements',
            cls = 'DummyMotorController')
class PersistenceTestCase(BasePoolTestCase, unittest.TestCase):
    """ Test the persistence of the Sardana Tango elements.
    """

    def check_elems_presistence(self, cls):
        """Helper method to test the elements persitence. The actions are:
            - creation of controller and element
            - restart Pool
            - check if element persist
        """
        # Create controller
        self.do_element_cleanup = False
        props = ()
        base_name = "ctrl_persistent_" + cls
        self.ctrl_name = get_free_alias(PyTango.Database(), base_name)
        try:
            ctrl = self.pool.createController(cls, self.ctrl_name, *props)
        except:
            ctrl = None
        msg = 'Impossible to create ctrl: "%s"' % (self.ctrl_name)
        self.assertIsNotNone(ctrl, msg)
        # Create element
        base_name = "elem_persistent_" + cls
        self.elem_name = get_free_alias(PyTango.Database(), base_name)
        axis = 1
        try:
            elem = self.pool.createElement(self.elem_name, ctrl, axis)
        except:
            elem = None
        msg = 'Impossible to create element: "%s"' % (self.elem_name)
        self.assertIsNotNone(ctrl, msg)
        # Restart Pool
        self._starter.stopDs(hard_kill=True)
        self._starter.startDs()
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
                self.pool.DeleteElement(self.elem_name)
            except:
                cleanup_success = False
        try:
            self.pool.DeleteElement(self.ctrl_name)
        except:
            cleanup_success = False        
        BasePoolTestCase.tearDown(self)
        if not cleanup_success:
            raise Exception("Cleanup failed. Database may be left dirty.")           
