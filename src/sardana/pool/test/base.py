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

from sardana.pool.test import (FakePool, createPoolController, createCtrlConf,
                               createPoolCounterTimer, createPoolTriggerGate,
                               createElemConf)

class BasePoolTestCase(object):
    """Base pool test for setting the environment."""

    def setUp(self):
        """Create a collection of controllers and elements.
        """
        self.nctctrls = self.ntgctrls = 4
        self.nctelems = self.ntgelems = 5  
        unittest.TestCase.setUp(self)
        self.pool = FakePool()
        self.ctrls = {}
        self.cts = {}
        self.tgs = {}
        # Create nctctrls CT ctrls
        for ctrl in range(1, self.nctctrls + 1):
            name = '__test_ct_ctrl_%s' %ctrl
            c_cfg = createCtrlConf(self.pool, name, 
                        'DummyCounterTimerController', 
                        'DummyCounterTimerController.py')
            ctrl_obj = createPoolController(self.pool, c_cfg)
            self.ctrls[name] = ctrl_obj
            self.pool.add_element(ctrl_obj)
            # Create nelems CT elements for each ctrl
            for elem in range(1, self.nctelems + 1):
                name = '__test_ct_%s_%s' %(ctrl, elem)
                e_cfg = createElemConf(self.pool, elem, name)
                elem_obj = createPoolCounterTimer(self.pool, ctrl_obj, e_cfg)
                ctrl_obj.add_element(elem_obj)
                # CT elements
                self.cts[name] = elem_obj
                self.pool.add_element(elem_obj)
        # Create ntgctrls TG ctrls
        for ctrl in range(1, self.ntgctrls + 1):
            name = '__test_tg_ctrl_%s' %ctrl
            c_cfg = createCtrlConf(self.pool, name,
                        'DummyTriggerGateController', 
                        'DummyTriggerGateController.py')
            ctrl_obj = createPoolController(self.pool, c_cfg)
            self.ctrls[name] = ctrl_obj
            self.pool.add_element(ctrl_obj)
            # Create nelems CT elements for each ctrl
            for elem in range(1, self.ntgelems + 1):
                name = '__test_tg_%s_%s' %(ctrl, elem)
                e_cfg = createElemConf(self.pool, elem, name)
                elem_obj = createPoolTriggerGate(self.pool, ctrl_obj, e_cfg)
                ctrl_obj.add_element(elem_obj)
                # TG elements
                self.tgs[name] = elem_obj
                self.pool.add_element(elem_obj)
        # Check the elements creation 
        cts = len(self.cts.keys())
        tgs = len(self.tgs.keys()) 
        msg = 'Something happened during the creation of CT elements.\n' + \
              'Expected %s and there are %s, %s' % \
              (self.nctelems, cts, self.cts.keys())
        if cts != self.nctelems * self.nctctrls:
            raise Exception(msg)
        msg = 'Something happened during the creation of TG elements.\n' + \
              'Expected %s and there are %s, %s' % \
              (self.ntgelems, tgs, self.tgs.keys())
        if tgs != self.ntgelems * self.ntgctrls:
            raise Exception(msg)

    def tearDown(self):
        self.pool = None
        self.ctrls = None
        self.cts = None
        self.tgs = None
        unittest.TestCase.tearDown(self)

