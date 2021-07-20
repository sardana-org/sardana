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
import taurus

from sardana.tango.pool.test import BasePoolTestCase


__all__ = ['SarTestTestCase']


def _cleanup_device(dev_name):
    factory = taurus.Factory()
    device = taurus.Device(dev_name)
    # tango_alias_devs contains any names in which we have referred
    # to the device, could be alias, short name, etc. pop all of them
    for k, v in list(factory.tango_alias_devs.items()):
        if v is device:
            factory.tango_alias_devs.pop(k)
    full_name = device.getFullName()
    if full_name in factory.tango_devs:
        factory.tango_devs.pop(full_name)
    device.cleanUp()


class SarTestTestCase(BasePoolTestCase):
    """ Base class to setup sardana test environment.
        It creates the controllers defined in cls_list and pseudo_cls_list
        with the given 'n' elements.

        - cls_list is a list of tuples: (ctrl_class, prefix, subfix, num_elem)

        The ctrls name and elements name will be hardcode following
        the next structure:

        - The ctrl_name will be prefix + _ctrl_ + postfix.
        - The elem_name will be prefix + _ + postfix + _ + axis
    """
    # TODO: Formating PEP8
    cls_list = [
        ('Motor', 'DummyMotorController', 'DummyMotorController', '_test_mt', '1', 5),
        ('CTExpChannel', 'DummyCounterTimerController',
         'DummyCounterTimerController', '_test_ct', '1', 5),
        ('CTExpChannel', 'DummyCounterTimerController',
         'DummyCounterTimerController', '_test_ct', '2', 5),
        ('ZeroDExpChannel', 'DummyZeroDController',
         'DummyZeroDController', '_test_0d', '1', 5),
        ('ZeroDExpChannel', 'DummyZeroDController',
         'DummyZeroDController', '_test_0d', '2', 5),
        ('OneDExpChannel', 'DummyOneDController',
         'DummyOneDController', '_test_1d', '1', 5),
        ('OneDExpChannel', 'DummyOneDController',
         'DummyOneDController', '_test_1d', '2', 5),
        ('TwoDExpChannel', 'DummyTwoDController',
         'DummyTwoDController', '_test_2d', '1', 5),
        ('TwoDExpChannel', 'DummyTwoDController',
         'DummyTwoDController', '_test_2d', '2', 5),
        ('TriggerGate', 'DummyTriggerGateController',
         'DummyTriggerGateController', '_test_tg', '1', 5)
    ]

    pseudo_cls_list = [
        ('PseudoCounter', 'IoverI0',
         'IoverI0', '_test_pc', '1', "I=_test_ct_1_2", "I0=_test_ct_1_1",
         "IoverI0=_test_pc_1_1")
    ]

    def setUp(self, pool_properties=None):
        BasePoolTestCase.setUp(self, pool_properties)

        self.ctrl_list = []
        self.elem_list = []
        self.pseudo_ctrl_list = []
        self.pseudo_elem_list = []
        try:
            # physical controllers and elements
            for sar_type, lib, cls, prefix, postfix, nelem in self.cls_list:
                # create controller
                ctrl_name = prefix + "_ctrl_%s" % (postfix)
                try:
                    self.pool.CreateController([sar_type, lib, cls, ctrl_name])
                    if cls in ("DummyCounterTimerController",
                               "DummyTwoDController"):
                        ctrl = PyTango.DeviceProxy(ctrl_name)
                        # use the first trigger/gate element by default
                        ctrl.write_attribute("Synchronizer", "_test_tg_1_1")
                except Exception as e:
                    print(e)
                    msg = 'Impossible to create ctrl: "%s"' % (ctrl_name)
                    raise Exception('Aborting SartestTestCase: %s' % (msg))
                self.ctrl_list.append(ctrl_name)
                # create elements
                for axis in range(1, nelem + 1):
                    elem_name = prefix + "_" + postfix + '_%s' % (axis)
                    try:
                        self.pool.createElement(
                            [sar_type, ctrl_name, str(axis), elem_name])
                    except Exception as e:
                        print(e)
                        msg = 'Impossible to create element: "%s"' % (
                            elem_name)
                        raise Exception('Aborting SartestTestCase: %s' % (msg))
                    self.elem_list.append(elem_name)
            # pseudo controllers and elements
            for pseudo in self.pseudo_cls_list:
                sar_type, lib, cls, prefix, postfix = pseudo[0:5]
                roles = pseudo[5:]
                # Create controller
                ctrl_name = prefix + "_ctrl_%s" % (postfix)
                argin = [sar_type, lib, cls, ctrl_name]
                argin.extend(roles)
                try:
                    self.pool.CreateController(argin)
                except Exception as e:
                    print(e)
                    msg = 'Impossible to create ctrl: "%s"' % (ctrl_name)
                    raise Exception('Aborting SartestTestCase: %s' % (msg))
                self.pseudo_ctrl_list.append(ctrl_name)
                for role in roles:
                    elem = role.split("=")[1]
                    if elem not in self.elem_list:
                        self.pseudo_elem_list.append(elem)
        except Exception as e:
            # force tearDown in order to eliminate the Pool
            BasePoolTestCase.tearDown(self)
            print(e)

    def _delete_elem(self, elem_name):
        # Cleanup eventual taurus devices. This is especially important
        # if the sardana-taurus extensions are in use since this
        # devices are created and destroyed within the testsuite.
        # Persisting taurus device may react on API_EventTimeouts, enabled
        # polling, etc.
        if elem_name in self.f.tango_alias_devs:
            _cleanup_device(elem_name)
        try:
            if os.name != "nt":
                self.pool.DeleteElement(elem_name)
                print(elem_name)
        except Exception as e:
            print(e)
            self.dirty_elems.append(elem_name)

    def _delete_ctrl(self, ctrl_name):
        # Cleanup eventual taurus devices. This is especially important
        # if the sardana-taurus extensions are in use since this
        # devices are created and destroyed within the testsuite.
        # Persisting taurus device may react on API_EventTimeouts, enabled
        # polling, etc.
        if ctrl_name in self.f.tango_alias_devs:
            _cleanup_device(ctrl_name)
        try:
            if os.name != "nt":
                self.pool.DeleteElement(ctrl_name)
                print(ctrl_name)
        except:
            self.dirty_ctrls.append(ctrl_name)

    def tearDown(self):
        """Remove the elements and the controllers
        """
        self.dirty_elems = []
        self.dirty_ctrls = []
        self.f = taurus.Factory()
        for elem_name in self.pseudo_elem_list:
            self._delete_elem(elem_name)
        for ctrl_name in self.pseudo_ctrl_list:
            self._delete_ctrl(ctrl_name)
        for elem_name in self.elem_list:
            self._delete_elem(elem_name)
        for ctrl_name in self.ctrl_list:
            self._delete_ctrl(ctrl_name)
        _cleanup_device(self.pool_name)

        BasePoolTestCase.tearDown(self)

        if self.dirty_elems or self.dirty_ctrls:
            msg = "Cleanup failed. Database may be left dirty." + \
                "\n\tCtrls : %s\n\tElems : %s" % (self.dirty_ctrls, self.dirty_elems)
            raise Exception(msg)


if __name__ == "__main__":
    stc = SarTestTestCase()
    stc.setUp()
    import time
    time.sleep(15)
    stc.tearDown()
