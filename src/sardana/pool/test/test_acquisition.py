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
import threading

from taurus.external import unittest
from taurus.test import insertTest
#TODO: import mock using taurus.external

from sardana.pool.pooltggeneration import PoolTGGeneration
from sardana.pool.poolacquisition import PoolAcquisition
from sardana.sardanathreadpool import get_thread_pool
from sardana.pool.test import (FakePool, createPoolController,
                               createPoolTriggerGate, createPoolCounterTimer,
                               createPoolTGGenerationConfiguration,
                               createCTAcquisitionConfiguration,
                               dummyPoolTGCtrlConf01, dummyPoolCTCtrlConf01,
                               dummyCounterTimerConf01, dummyTriggerGateConf01)

class AttributeListener(object):
    
    def __init__(self):
        self.data = {}
        self.data_lock = threading.RLock()
    
    def event_received(self, *args, **kwargs):
        # s - type: sardana.sardanavalue.SardanaValue
        # t - type: sardana.sardanaevent.EventType
        # v - type: sardana.sardanaattribute.SardanaAttribute e.g. 
        #           sardana.pool.poolbasechannel.Value
        s, t, v = args
        # obtaining sardana element e.g. exp. channel (the attribute owner)
        obj = s.get_obj()
        obj_name = obj.name
        # obtaining the SardanaValue corresponding to read value
        sdn_value = v.get_value_obj()
        # value and index pair (ensure they are lists even if they were scalars)       
        value = sdn_value.value
        if numpy.isscalar(value):
            value = [value]
        idx = sdn_value.idx
        if numpy.isscalar(idx):
            idx = [idx]
        
#         print s.name, t, (idx, value)
        
        # filling the measurement records 
        with self.data_lock:
            channel_data = self.data.get(obj_name, [])
            expected_idx = len(channel_data)
            pad = [None] * (idx[0]-expected_idx)        
            channel_data.extend(pad+value)
            self.data[obj_name] = channel_data
            
    def get_table(self):
        '''Construct a table-like array with padded  channel data as columns.
        Return the '''
        with self.data_lock:
            max_len = max([len(d) for d in self.data.values()])
            dtype_spec = []
            table = []
            for k in sorted(self.data.keys()):
                v = self.data[k]
                v.extend([None]*(max_len-len(v)))
                table.append(v)
                dtype_spec.append((k, 'float64'))
            a = numpy.array(zip(*table), dtype=dtype_spec)
            return a

# @insertTest(helper_name='continuous_acquisition', offset=0, active_period=0.1,
#             passive_period=0.2, repetitions=10000, integ_time=0.2)
# @insertTest(helper_name='continuous_acquisition', offset=0, active_period=0.001,
#             passive_period=0.21, repetitions=10000, integ_time=0.1)
# @insertTest(helper_name='continuous_acquisition', offset=0, active_period=0.001,
#             passive_period=0.15, repetitions=1000, integ_time=0.01)
@insertTest(helper_name='continuous_acquisition', offset=0, active_period=0.001,
            passive_period=0.1, repetitions=10, integ_time=0.01)
class AcquisitionTestCase(unittest.TestCase):
    """Integration test of TGGeneration and Acquisition actions."""

    def setUp(self):
        """Create a Controller, TriggerGate and PoolTGGeneration objects from 
        dummy configurations.
        """
        unittest.TestCase.setUp(self)
        pool = FakePool()
        # create TG elements and its controllers
        dummy_tg_ctrl = createPoolController(pool, dummyPoolTGCtrlConf01)
        self.dummy_tg = createPoolTriggerGate(pool, dummy_tg_ctrl, 
                                                        dummyTriggerGateConf01)
        dummy_tg_ctrl.add_element(self.dummy_tg)
        pool.add_element(dummy_tg_ctrl)
        pool.add_element(self.dummy_tg)
        self.tg_cfg = createPoolTGGenerationConfiguration((dummy_tg_ctrl,),
                                        (dummyPoolTGCtrlConf01,),
                                        ((self.dummy_tg,),),
                                        ((dummyTriggerGateConf01,),))
        # create TGGeneration action
        self.tggeneration = PoolTGGeneration(self.dummy_tg)
        self.tggeneration.add_element(self.dummy_tg)
        # create CT elements and its controllers
        dummyPoolCTCtrlConf01['name'] = 'ctrl1'
        dummy_ct_ctrl1 = createPoolController(pool, dummyPoolCTCtrlConf01)
#         dummy_ct_ctrl1.set_log_level(logging.DEBUG)
        dummyPoolCTCtrlConf02 = copy.deepcopy(dummyPoolCTCtrlConf01)
        dummyPoolCTCtrlConf02['id'] = 11
        dummyPoolCTCtrlConf02['name'] = 'ctrl2'
        dummy_ct_ctrl2 = createPoolController(pool, dummyPoolCTCtrlConf02)
#         dummy_ct_ctrl2.set_log_level(logging.DEBUG)
        dummyCounterTimerConf01['name'] = 'ct01'
        self.dummy_ct1 = createPoolCounterTimer(pool, dummy_ct_ctrl1, 
                                                        dummyCounterTimerConf01)
        dummy_ct_ctrl1.add_element(self.dummy_ct1)
        pool.add_element(self.dummy_ct1)
        dummyPoolCTCtrlConf02 = copy.deepcopy(dummyPoolCTCtrlConf01)
        dummyCounterTimerConf02 = copy.deepcopy(dummyCounterTimerConf01)
        dummyCounterTimerConf02['name'] = 'ct02'
        dummyCounterTimerConf02['id'] = 5
        dummyCounterTimerConf02['axis'] = 2
        dummyCounterTimerConf02['enabled'] = True
        self.dummy_ct2 = createPoolCounterTimer(pool, dummy_ct_ctrl2, 
                                                        dummyCounterTimerConf02)
        dummy_ct_ctrl2.add_element(self.dummy_ct2)
        self.dummy_ct2.set_extra_par('triggermode', 'gate')
        pool.add_element(self.dummy_ct2)
        pool.add_element(dummy_ct_ctrl2)
        self.l = AttributeListener()
        self.dummy_ct1._value.add_listener(self.l)
        self.dummy_ct2._value.add_listener(self.l)
        # enabling the channel - normally done when applying the MG conf.
        # see poolmeasurementgroup.PoolMeasurementGroup._build_channel_defaults
        dummyCounterTimerConf01['enabled'] = True
        self.acq_cfg = createCTAcquisitionConfiguration((dummy_ct_ctrl1,),
                                        (dummyPoolCTCtrlConf01,),
                                        ((self.dummy_ct1,),),
                                        ((dummyCounterTimerConf01,),))
        self.cont_acq_cfg = createCTAcquisitionConfiguration((dummy_ct_ctrl2,),
                                        (dummyPoolCTCtrlConf02,),
                                        ((self.dummy_ct2,),),
                                        ((dummyCounterTimerConf02,),))
        self.acquisition = PoolAcquisition(self.dummy_ct1)
#         self.acquisition.setLogLevel(logging.DEBUG)
        self.acquisition.add_element(self.dummy_ct1)
        self.acquisition._cont_acq.add_element(self.dummy_ct2)
#         self.acquisition._cont_acq.set_main_element(self.dummy_ct2)            
        
    def continuous_acquisition(self, offset, active_period, passive_period, 
                                                      repetitions, integ_time):
        """Executes measurement running the TGGeneration and Acquisition actions
        according the test parameters. Checks the lengths of the acquired data.
        """        
        jobs_before = get_thread_pool().qsize
        # configuring tggeneration according to the test parameters 
        self.tggeneration._sw_tggenerator.setOffset(offset)
        self.tggeneration._sw_tggenerator.setActivePeriod(active_period)
        self.tggeneration._sw_tggenerator.setPassivePeriod(passive_period)
        self.tggeneration._sw_tggenerator.setRepetitions(repetitions)
        # add listener to the tggeneration action
        self.tggeneration._sw_tggenerator.add_listener(self.acquisition)
        
        config = {'integ_time': integ_time, 'config': self.acq_cfg}
        self.acquisition.set_config(config)
        self.dummy_ct2.set_extra_par('nroftriggers', repetitions)
        
        config = {'integ_time': integ_time, 'config': self.cont_acq_cfg}        
        # TODO: start using the acquisition action
        self.acquisition._cont_acq.run(*(), **config)        
        args_tg = ()
        kwargs_tg = {'config': self.tg_cfg, 'software': True}
        self.tggeneration.run(*args_tg, **kwargs_tg)
        # waiting for acquisition and tggeneration to finish                
        while self.acquisition.is_running() or self.tggeneration.is_running():            
            time.sleep(1)
        # print the acquisition records
        table = self.l.get_table()
        n_rows = table.shape[0]
        for row in xrange(n_rows):
            print row, table[row]        
        # checking if all the data were acquired 
        for ch_name in table.dtype.names:
            ch_data_len = len(table[ch_name])
            msg = 'length of data for channel %s is %d and should be %d' %\
                                                     (ch_name, ch_data_len, repetitions)
            self.assertEqual(ch_data_len, repetitions, msg)
        # checking if there are no pending jobs
        jobs_after = get_thread_pool().qsize
        msg = ('there are %d jobs pending to be done after the acquisition ' +
                               '(before: %d)') %(jobs_after, jobs_before)
        self.assertEqual(jobs_before, jobs_after, msg)                
        
    def tearDown(self):
        self.tgaction = None
        self.cfg = None
        self.dummy_tg = None
        unittest.TestCase.tearDown(self)