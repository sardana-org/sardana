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

        - cls_list is a list of tuples: (ctrl_class, prefix, subfix, num_elem)

        The ctrls name and elements name will be hardcode following
        the next structure:

        - The ctrl_name will be prefix + _ctrl_ + postfix.
        - The elem_name will be prefix + _ + postfix + _ + axis
    """
    cls_list = [('DummyMotorController', '_test_mt', '1', 5),
                ('DummyCounterTimerController', '_test_ct', '1', 5),
                ('DummyCounterTimerController', '_test_ct', '2', 5),
                ('SoftwareTriggerGateController', '_test_stg', '1', 5),
                ('SoftwareTriggerGateController', '_test_stg', '2', 5),
                ('DummyTriggerGateController', '_test_tg', '1', 5),
                ('DummyTriggerGateController', '_test_tg', '2', 5)]

    def setUp(self):
        BasePoolTestCase.setUp(self)

        self.ctrl_list = []
        self.elem_list = []

        for cls, prefix, postfix, nelem in self.cls_list:
            # Create controller
            props = ()
            ctrl_name = prefix + "_ctrl_%s" % (postfix)
            try:
                ctrl = self.pool.createController(cls, ctrl_name, *props)
            except:
                msg = 'Impossible to create ctrl: "%s"' % (ctrl_name)
                raise Exception('Aborting SartestTesCase: %s' % (msg))
            self.ctrl_list.append(ctrl_name)
            # Create 5 elemens
            for axis in range(1,nelem+1):
                elem_name = prefix + "_" + postfix + '_%s' % (axis)
                try:
                    elem = self.pool.createElement(elem_name, ctrl, axis)
                except Exception, e:
                    msg = 'Impossible to create element: "%s"' % (elem_name)
                    raise Exception('Aborting SartestTesCase: %s' % (msg))
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

        BasePoolTestCase.tearDown(self) 

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
