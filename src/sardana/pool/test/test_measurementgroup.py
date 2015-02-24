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
import copy
import logging
import numpy

from taurus.external import unittest
from taurus.test import insertTest
#TODO: import mock using taurus.external

from sardana.sardanathreadpool import get_thread_pool
from sardana.pool.test import (FakePool, createPoolMeasurementGroup,
                               createMGConfiguration,
                               dummyMeasurementGroupConf01,
                               createPoolController,
                               createPoolTriggerGate, createPoolCounterTimer,
                               dummyPoolTGCtrlConf01, dummyPoolCTCtrlConf01,
                               dummyCounterTimerConf01, dummyTriggerGateConf01)

#TODO Import AttributeListener from the right location.
from sardana.pool.test.test_acquisition import AttributeListener
        

mg_params = { "offset":0, 
              "active_period":0.001,
              "passive_period":0.15, 
              "repetitions":10, 
              "integ_time":0.01 }    



@insertTest(helper_name='meas_cont_acquisition', params=mg_params)
class AcquisitionTestCase(unittest.TestCase):
    """Integration test of TGGeneration and Acquisition actions."""

    def setUp(self):
        """Create a Controller, TriggerGate and PoolTGGeneration objects from 
        dummy configurations.
        """
        unittest.TestCase.setUp(self)
        pool = FakePool()

        # create CT ctrl1 and ct01
        dummyPoolCTCtrlConf01['name'] = 'ct_ctrl1'
        dummyPoolCTCtrlConf01['full_name'] = 'ct_ctrl1'
        dummy_ct_ctrl1 = createPoolController(pool, dummyPoolCTCtrlConf01)
        dummyCounterTimerConf01['id'] = 99
        dummyCounterTimerConf01['name'] = 'ct01'
        dummyCounterTimerConf01['full_name'] = 'ct01'
        self.dummy_ct1 = createPoolCounterTimer(pool, dummy_ct_ctrl1, 
                                                       dummyCounterTimerConf01)
        dummy_ct_ctrl1.add_element(self.dummy_ct1)
        # create CT ctrl2 and ct02 
        dummyPoolCTCtrlConf02 = copy.deepcopy(dummyPoolCTCtrlConf01)
        dummyPoolCTCtrlConf02['id'] = 11
        dummyPoolCTCtrlConf02['name'] = 'ct_ctrl2'
        dummyPoolCTCtrlConf02['full_name'] = 'ct_ctrl2'
        dummy_ct_ctrl2 = createPoolController(pool, dummyPoolCTCtrlConf02)
        dummyCounterTimerConf02 = copy.deepcopy(dummyCounterTimerConf01)
        dummyCounterTimerConf02['name'] = 'ct02'
        dummyCounterTimerConf02['full_name'] = 'ct02'
        dummyCounterTimerConf02['id'] = 12       
        self.dummy_ct2 = createPoolCounterTimer(pool, dummy_ct_ctrl2,
                                                       dummyCounterTimerConf02)
        dummy_ct_ctrl2.add_element(self.dummy_ct2)
        # create TG ctrl1 and tg01
        dummyPoolTGCtrlConf01['name'] = 'tg_ctrl1'  
        dummyPoolTGCtrlConf01['full_name'] = 'tg_ctrl1'
        dummy_tg_ctrl1 = createPoolController(pool, dummyPoolTGCtrlConf01)
        dummyTriggerGateConf01['name'] = 'tg01'
        dummyTriggerGateConf01['full_name'] = 'tg01'
        dummy_tg1 = createPoolTriggerGate(pool, dummy_tg_ctrl1, 
                                                        dummyTriggerGateConf01)
        dummy_tg_ctrl1.add_element(dummy_tg1)
        # add elements to pool        
        pool.add_element(dummy_ct_ctrl1)
        pool.add_element(dummy_ct_ctrl2)
        pool.add_element(dummy_tg_ctrl1)
        pool.add_element(self.dummy_ct1)
        pool.add_element(self.dummy_ct2)
        pool.add_element(dummy_tg1)
        # Subscribe to ... 
        self.attr_listener = AttributeListener()
        dummyMeasurementGroupConf01["name"] = 'mg1'
        dummyMeasurementGroupConf01["full_name"] = 'mg1'
        
        user_elements = [self.dummy_ct1.id, self.dummy_ct2.id]
        dummyMeasurementGroupConf01["user_elements"] = user_elements     
        self.pmg = createPoolMeasurementGroup(pool, dummyMeasurementGroupConf01)
        # Add mg to pool
        pool.add_element(self.pmg)
        ## Add listeners
        attr_elements = self.pmg.get_user_elements_attribute_sequence()
        # create mg configuration
        ctrls = (dummy_ct_ctrl1, dummy_ct_ctrl2)
        ctrls_conf = (dummyPoolCTCtrlConf01, dummyPoolCTCtrlConf02)
        ctrl_channels = ((self.dummy_ct1,), (self.dummy_ct2,))
        ctrl_channels_conf = ((dummyCounterTimerConf01,),
                              (dummyCounterTimerConf02,))
        ctrl_trigger_elements = (('sw_time',), (dummy_tg1,))
        ctrl_trigger_modes = (('trigger',), ('trigger',))
        self.mg_conf = createMGConfiguration(ctrls, ctrls_conf, ctrl_channels,
                  ctrl_channels_conf, ctrl_trigger_elements, ctrl_trigger_modes)
                
        for attr in attr_elements:
            attr.add_listener(self.attr_listener)


    def meas_cont_acquisition(self, params):
        """Executes measurement using the measurement group. 
        Checks the lengths of the acquired data.
        """    
        offset = params["offset"]
        active_period = params["active_period"]
        passive_period = params["passive_period"] 
        repetitions = params["repetitions"]
        integ_time = params["integ_time"]
    
        jobs_before = get_thread_pool().qsize
        
        self.pmg.set_integration_time(integ_time)
        self.pmg.set_configuration(config=self.mg_conf)
        self.pmg._action_cache = self.pmg._fill_action_cache(None)
        # TODO: add elements to action when applying configuration
#         self.pmg.acquisition._cont_ct_acq.add_element(self.dummy_ct1)
#         self.pmg.acquisition._cont_acq.add_element(self.dummy_ct2)
        
        self.pmg.start_acquisition(continuous=True)

        # waiting for acquisition and tggeneration to finish
        acq = self.pmg.acquisition
        tgg = self.pmg.tggeneration                
        while acq.is_running or tgg.is_running():            
            time.sleep(1)
        # print the acquisition records
        for i, record in enumerate(zip(*self.attr_listener.data.values())):
            print i, record
        # checking if all the data were acquired 
        for ch, data in self.attr_listener.data.items():
            acq_data = len(data)
            msg = 'length of data for channel %s is %d and should be %d' %\
                                                     (ch, acq_data, repetitions)
            self.assertEqual(acq_data, repetitions, msg)
        # checking if there are no pending jobs
        jobs_after = get_thread_pool().qsize
        msg = ('there are %d jobs pending to be done after the acquisition ' +
                               '(before: %d)') %(jobs_after, jobs_before)
        self.assertEqual(jobs_before, jobs_after, msg)                
        
    def tearDown(self):
        self.attr_listener = None
        self.pmg = None
        unittest.TestCase.tearDown(self)
