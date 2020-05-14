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

__all__ = ["BasePoolTestCase"]

import logging

from sardana.pool.test import (FakePool, createPoolController, createCtrlConf,
                               createPoolCounterTimer, createPoolTriggerGate,
                               createPoolMotor, createElemConf,
                               createPoolZeroDExpChannel,
                               createPoolTwoDExpChannel,
                               createPoolPseudoCounter, createPoolPseudoMotor)


class BasePoolTestCase(object):
    """Base pool test for setting the environment."""

    POOLPATH = []
    LOGLEVEL = logging.WARNING

    def createController(self, name, klass, lib, props={}):
        c_cfg = createCtrlConf(self.pool, name, klass, lib, props)
        ctrl_obj = createPoolController(self.pool, c_cfg)
        self.ctrls[name] = ctrl_obj
        self.pool.add_element(ctrl_obj)
        return ctrl_obj

    def createCTElement(self, ctrl_obj, name, axis):
        e_cfg = createElemConf(self.pool, axis, name)
        elem_obj = createPoolCounterTimer(self.pool, ctrl_obj, e_cfg)
        ctrl_obj.add_element(elem_obj)
        # CT elements
        self.cts[name] = elem_obj
        self.pool.add_element(elem_obj)
        return elem_obj

    def createZeroDElement(self, ctrl_obj, name, axis):
        e_cfg = createElemConf(self.pool, axis, name)
        elem_obj = createPoolZeroDExpChannel(self.pool, ctrl_obj, e_cfg)
        ctrl_obj.add_element(elem_obj)
        # ZeroD elements
        self.zerods[name] = elem_obj
        self.pool.add_element(elem_obj)
        return elem_obj

    def createTwoDElement(self, ctrl_obj, name, axis):
        e_cfg = createElemConf(self.pool, axis, name)
        elem_obj = createPoolTwoDExpChannel(self.pool, ctrl_obj, e_cfg)
        ctrl_obj.add_element(elem_obj)
        # TwoD elements
        self.twods[name] = elem_obj
        self.pool.add_element(elem_obj)
        return elem_obj

    def createTGElement(self, ctrl_obj, name, axis):
        e_cfg = createElemConf(self.pool, axis, name)
        elem_obj = createPoolTriggerGate(self.pool, ctrl_obj, e_cfg)
        ctrl_obj.add_element(elem_obj)
        # TG elements
        self.tgs[name] = elem_obj
        self.pool.add_element(elem_obj)
        return elem_obj

    def createMotorElement(self, ctrl_obj, name, axis):
        e_cfg = createElemConf(self.pool, axis, name)
        elem_obj = createPoolMotor(self.pool, ctrl_obj, e_cfg)
        ctrl_obj.add_element(elem_obj)
        # MOT elements
        self.mots[name] = elem_obj
        self.pool.add_element(elem_obj)
        return elem_obj

    def createPCElement(self, ctrl_obj, name, axis, elements=[]):
        e_cfg = createElemConf(self.pool, axis, name)
        elem_obj = createPoolPseudoCounter(self.pool, ctrl_obj, e_cfg,
                                           elements)
        ctrl_obj.add_element(elem_obj)
        self.pcs[name] = elem_obj
        self.pool.add_element(elem_obj)
        return elem_obj

    def createPMElement(self, ctrl_obj, name, axis, elements=[]):
        e_cfg = createElemConf(self.pool, axis, name)
        elem_obj = createPoolPseudoMotor(self.pool, ctrl_obj, e_cfg,
                                         elements)
        ctrl_obj.add_element(elem_obj)
        self.pms[name] = elem_obj
        self.pool.add_element(elem_obj)
        return elem_obj

    def setUp(self):
        """Create a collection of controllers and elements.
        """
        self.nctctrls = self.nzerodctrls = self.ntgctrls = self.nmotctrls = 4
        # dummy controller generates an array of zeros (1024x1024) for each
        # axis, many axes may increase the memory consumption of testsuite
        self.ntwodctrls = 1
        self.nctelems = self.nzerodelems = self.ntgelems = self.nmotelems = 5
        # dummy controller generates an array of zeros (1024x1024) for each
        # axis, many axes may increase the memory consumption of testsuite
        self.ntwodelems = 1
        self.pool = FakePool(self.POOLPATH, self.LOGLEVEL)
        # Use debug mode

        self.ctrls = {}
        self.cts = {}
        self.zerods = {}
        self.twods = {}
        self.tgs = {}
        self.mots = {}
        self.pcs = {}
        self.pms = {}
        self.exp_channels = {}
        # Create nctctrls CT ctrls
        for ctrl in range(1, self.nctctrls + 1):
            name = '_test_ct_ctrl_%s' % ctrl
            ctrl_obj = self.createController(name,
                                             'DummyCounterTimerController',
                                             'DummyCounterTimerController.py')
            # use the first trigger/gate element by default
            ctrl_obj.set_ctrl_attr("synchronizer", "_test_tg_1_1")
            # Create nctelems CT elements for each ctrl
            for axis in range(1, self.nctelems + 1):
                name = '_test_ct_%s_%s' % (ctrl, axis)
                self.createCTElement(ctrl_obj, name, axis)
        self.exp_channels.update(self.cts)
        # Create nzerodctrls ZeroD ctrls
        for ctrl in range(1, self.nzerodctrls + 1):
            name = '_test_0d_ctrl_%s' % ctrl
            ctrl_obj = self.createController(name,
                                             'DummyZeroDController',
                                             'DummyZeroDController.py')
            # Create nzerodelems ZeroD elements for each ctrl
            for axis in range(1, self.nzerodelems + 1):
                name = '_test_0d_%s_%s' % (ctrl, axis)
                self.createZeroDElement(ctrl_obj, name, axis)
        self.exp_channels.update(self.zerods)
        # Create ntwodctrls TwoD ctrls
        for ctrl in range(1, self.ntwodctrls + 1):
            name = '_test_2d_ctrl_%s' % ctrl
            ctrl_obj = self.createController(name,
                                             'DummyTwoDController',
                                             'DummyTwoDController.py')
            # use the first trigger/gate element by default
            ctrl_obj.set_ctrl_attr("synchronizer", "_test_tg_1_1")
            # Create ntwodelems TwoD elements for each ctrl
            for axis in range(1, self.ntwodelems + 1):
                name = '_test_2d_%s_%s' % (ctrl, axis)
                self.createTwoDElement(ctrl_obj, name, axis)
        self.exp_channels.update(self.twods)
        # Create ntgctrls TG ctrls
        for ctrl in range(1, self.ntgctrls + 1):
            name = '_test_tg_ctrl_%s' % ctrl
            ctrl_obj = self.createController(name,
                                             'DummyTriggerGateController',
                                             'DummyTriggerGateController.py')
            # Create ntgelems TG elements for each ctrl
            for axis in range(1, self.ntgelems + 1):
                name = '_test_tg_%s_%s' % (ctrl, axis)
                self.createTGElement(ctrl_obj, name, axis)
        # Create nmotctrls MOT ctrls
        for ctrl in range(1, self.nmotctrls + 1):
            name = '_test_mot_ctrl_%s' % ctrl
            ctrl_obj = self.createController(name,
                                             'DummyMotorController',
                                             'DummyMotorController.py')
            # Create nmotelems MOT elements for each ctrl
            for axis in range(1, self.nmotelems + 1):
                name = '_test_mot_%s_%s' % (ctrl, axis)
                self.createMotorElement(ctrl_obj, name, axis)

        # Check the elements creation
        cts = len(list(self.cts.keys()))
        tgs = len(list(self.tgs.keys()))
        mots = len(list(self.mots.keys()))

        expected_cts = self.nctelems * self.nctctrls
        msg = 'Something happened during the creation of CT elements.\n' + \
              'Expected %s and there are %s, %s' % \
              (expected_cts, cts, list(self.cts.keys()))
        if cts != expected_cts:
            raise Exception(msg)
        expected_tgs = self.ntgelems * self.ntgctrls
        msg = 'Something happened during the creation of TG elements.\n' + \
              'Expected %s and there are %s, %s' % \
              (expected_tgs, tgs, list(self.tgs.keys()))
        if tgs != expected_tgs:
            raise Exception(msg)
        expected_mots = self.nmotelems * self.nmotctrls
        msg = 'Something happened during the creation of MOT elements.\n' + \
              'Expected %s and there are %s, %s' % \
              (self.nmotelems, mots, list(self.mots.keys()))
        if mots != expected_mots:
            raise Exception(msg)

    def tearDown(self):
        self.pool.cleanup()
        self.pool = None
        self.ctrls = None
        self.cts = None
        self.tgs = None
