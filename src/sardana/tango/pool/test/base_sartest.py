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

import PyTango
from sardana.tango.pool.test import BasePoolTestCase
from sardana.tango.core.util import get_free_alias

__all__ = ['SarTestTestCase']

class SarTestTestCase(BasePoolTestCase):
    """ Base class to setup sardana test environment.
        It creates the controllers defined in cls_list 
        with the given 'n' elements.  
    """
    cls_list = [('DummyMotorController', 5),
                ('DummyCounterTimerController', 5),
                ('SoftwareTriggerGateController', 1), 
                ('DummyTriggerGateController', 1)]
    def setUp(self):
        BasePoolTestCase.setUp(self)

        self.ctrl_list = []
        self.elem_list = []

        for cls, nlem in self.cls_list:
            # Create controller
            props = ()
            base_name = "ctrl_sartest_" + cls 
            ctrl_name = get_free_alias(PyTango.Database(), base_name)  
            try:
                ctrl = self.pool.createController(cls, ctrl_name, *props)
            except:
                print('Impossible to create ctrl: "%s"' % (ctrl_name))
                continue
            self.ctrl_list.append(ctrl_name)
            # Create 5 elemens
            for axis in range(1,nlem+1):
                base_name = "elem_sartest_" + cls
                elem_name = get_free_alias(PyTango.Database(), base_name)
                try:
                    elem = self.pool.createElement(elem_name, ctrl, axis)
                except Exception, e:
                    print('Impossible to create element: "%s"' % (elem_name))
                    print e.__repr__()
                    break
                self.elem_list.append(elem_name)
                

    def tearDown(self):
        """Remove the elements and the controllers
        """
        dirty_elems = []
        dirty_ctrls = []
        for elem_name in self.elem_list:
            try:
                self.pool.DeleteElement(elem_name)
            except:
                dirty_elems.append(elem_name)

        for ctrl_name in self.ctrl_list:
            try:
                self.pool.DeleteElement(ctrl_name)
            except:
                dirty_ctrls.append(ctrl_name)

        if dirty_elems or dirty_ctrls :
            msg = "Cleanup failed. Database may be left dirty." + \
                     "\n\tCtrls : %s\n\tElems : %s" % (dirty_ctrls, dirty_elems)
            raise Exception(msg)

if __name__ == "__main__":
     stc = SarTestTestCase()
     stc.setUp()
     import time
     time.sleep(15)
     stc.tearDown()
