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

__all__ = ['dummyMeasurementGroupConf01',
           'dummyPoolCTCtrlConf01', 'dummyPoolCTCtrlConf02',
           'TangoAttributeCTCtrlConf01', 'TangoAttributeCTCtrlConf02',
           'dummyPoolTGCtrlConf01', 'dummyPoolTGCtrlConf02',
           'dummyCounterTimerConf01', 'dummyCounterTimerConf02',
           'dummyCounterTimerConf03', 'dummyCounterTimerConf04',
           'dummyTriggerGateConf01', 'dummyTriggerGateConf02',
           'dummyTriggerGateConf03', 'dummyTriggerGateConf04',
           'dummyPoolMotorCtrlConf01', 'dummyMotorConf01', 'dummyMotorConf02']


# Pool Measurement Group
'''Minimum configuration to create a Pool MeasurementGroup'''
dummyMeasurementGroupConf01 = {'full_name': 'mntgrp01',
                               'id': None,
                               'name': '',
                               'pool': None,
                               'user_elements': [2]}


# Pool Ctrls
'''Minimum configuration to create a Pool CounterTimer controller'''
dummyPoolCTCtrlConf01 = {'class_info': None,
                         'full_name': 'dctctrl01',
                         'id': 1,
                         'klass': 'DummyCounterTimerController',
                         'lib_info': None,
                         'library': 'DummyCounterTimerController.py',
                         'name': '',
                         'pool': None,
                         'properties': {},
                         'role_ids': '',
                         'type': 'CTExpChannel'}

'''Second minimum configuration to create a Pool CounterTimer controller'''
dummyPoolCTCtrlConf02 = {'class_info': None,
                         'full_name': 'dctctrl02',
                         'id': 2,
                         'klass': 'DummyCounterTimerController',
                         'lib_info': None,
                         'library': 'DummyCounterTimerController.py',
                         'name': '',
                         'pool': None,
                         'properties': {},
                         'role_ids': '',
                         'type': 'CTExpChannel'}

'''Minimum configuration to create a TangoAttributeCTcontroller'''
TangoAttributeCTCtrlConf01 = {'class_info': None,
                              'ctrl_info': '',
                              'full_name': 'tctctrl01',
                              'id': 1,
                              'klass': 'TangoAttrCTController',
                              'lib_info': None,
                              #'library': 'TangoAttrCTCtrl.py',
                              'library': 'TangoAttrCounterTimerController.py',
                              'name': '',
                              'pool': None,
                              'properties': {},
                              'role_ids': '',
                              'type': 'CTExpChannel'}

'''Second minimum configuration to create a TangoAttributeCTcontroller'''
TangoAttributeCTCtrlConf02 = {'class_info': None,
                              'ctrl_info': '',
                              'full_name': 'tctctrl02',
                              'id': 2,
                              'klass': 'TangoAttrCTController',
                              'lib_info': None,
                              #'library': 'TangoAttrCTCtrl.py',
                              'library': 'TangoAttrCounterTimerController.py',
                              'name': '',
                              'pool': None,
                              'properties': {},
                              'role_ids': '',
                              'type': 'CTExpChannel'}

'''Minimum configuration to create a Pool TriggerGate controller'''
dummyPoolTGCtrlConf01 = {'class_info': None,
                         'full_name': 'dtgctrl01',
                         'id': 1,
                         'klass': 'DummyTriggerGateController',
                         'lib_info': None,
                         'library': 'DummyTriggerGateController.py',
                         'name': '',
                         'pool': None,
                         'properties': {},
                         'role_ids': '',
                         'type': 'TGChannel'}

'''Minimum configuration to create a Pool TriggerGate controller'''
dummyPoolTGCtrlConf02 = {'class_info': None,
                         'full_name': 'dtgctrl01',
                         'id': 2,
                         'klass': 'DummyTriggerGateController',
                         'lib_info': None,
                         'library': 'DummyTriggerGateController.py',
                         'name': '',
                         'pool': None,
                         'properties': {},
                         'role_ids': '',
                         'type': 'TGChannel'}

'''Minimum configuration to create a Pool Motor controller'''
dummyPoolMotorCtrlConf01 = {'class_info': None,
                            'full_name': 'dmotctrl01',
                            'id': 1,
                            'klass': 'DummyMotorController',
                            'lib_info': None,
                            'library': 'DummyMotorController.py',
                            'name': '',
                            'pool': None,
                            'properties': {},
                            'role_ids': '',
                            'type': 'Motor'}

# Pool Elements
'''Minimum configuration to create a Pool CounterTimer'''
dummyCounterTimerConf01 = {'axis': 1,
                           'ctrl': None,
                           'full_name': 'dct01',
                           'id': 2,
                           'name': '',
                           'pool': None}

'''Second minimum configuration to create a Pool CounterTimer'''
dummyCounterTimerConf02 = {'axis': 2,
                           'ctrl': None,
                           'full_name': 'dct02',
                           'id': 3,
                           'name': '',
                           'pool': None}

'''Third minimum configuration to create a Pool CounterTimer'''
dummyCounterTimerConf03 = {'axis': 1,
                           'ctrl': None,
                           'full_name': 'dct03',
                           'id': 2,
                           'name': '',
                           'pool': None}

'''Fourth minimum configuration to create a Pool CounterTimer'''
dummyCounterTimerConf04 = {'axis': 2,
                           'ctrl': None,
                           'full_name': 'dct04',
                           'id': 3,
                           'name': '',
                           'pool': None}

'''Minimum configuration to create a Pool TriggerGate'''
dummyTriggerGateConf01 = {'axis': 1,
                          'ctrl': None,
                          'full_name': 'dtg01',
                          'id': 2,
                          'name': '',
                          'pool': None}

'''Second minimum configuration to create a Pool TriggerGate'''
dummyTriggerGateConf02 = {'axis': 2,
                          'ctrl': None,
                          'full_name': 'dtg02',
                          'id': 3,
                          'name': '',
                          'pool': None}

'''Third minimum configuration to create a Pool TriggerGate'''
dummyTriggerGateConf03 = {'axis': 3,
                          'ctrl': None,
                          'full_name': 'dtg03',
                          'id': 4,
                          'name': '',
                          'pool': None}

'''Fourth minimum configuration to create a Pool TriggerGate'''
dummyTriggerGateConf04 = {'axis': 4,
                          'ctrl': None,
                          'full_name': 'dtg04',
                          'id': 5,
                          'name': '',
                          'pool': None}

'''Minimum configuration to create a Pool Motor'''
dummyMotorConf01 = {'axis': 1,
                    'ctrl': None,
                    'full_name': 'dmot01',
                    'id': 1,
                    'name': '',
                    'pool': None}

'''Minimum configuration to create a Pool Motor'''
dummyMotorConf02 = {'axis': 2,
                    'ctrl': None,
                    'full_name': 'dmot02',
                    'id': 1,
                    'name': '',
                    'pool': None}
