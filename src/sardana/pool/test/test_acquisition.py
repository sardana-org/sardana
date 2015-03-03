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
import datetime
import logging
import numpy
import threading

from taurus.external import unittest
from taurus.test import insertTest
#TODO: import mock using taurus.external

from sardana.pool import AcqTriggerType
from sardana.pool.pooltggeneration import PoolTGGeneration
from sardana.pool.pooltriggergate import TGEventType
from sardana.pool.poolacquisition import PoolContHWAcquisition,\
                                         PoolContSWCTAcquisition
from sardana.sardanathreadpool import get_thread_pool
from sardana.pool.test import (createPoolTGGenerationConfiguration,
                               createCTAcquisitionConfiguration)
from sardana.pool.test import BasePoolTestCase

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

@insertTest(helper_name='continuous_acquisition', offset=0, active_period=0.1,
            passive_period=0.2, repetitions=10, integ_time=0.2)
@insertTest(helper_name='continuous_acquisition', offset=0, active_period=0.001,
            passive_period=0.21, repetitions=10, integ_time=0.1)
@insertTest(helper_name='continuous_acquisition', offset=0, active_period=0.001,
            passive_period=0.15, repetitions=10, integ_time=0.01)
@insertTest(helper_name='continuous_acquisition', offset=0, active_period=0.001,
            passive_period=0.1, repetitions=10, integ_time=0.01)
class AcquisitionTestCase(BasePoolTestCase, unittest.TestCase):
    """Integration test of PoolTGGeneration, PoolContHWAcquisition and 
    PoolContSWCTAcquisition actions. This test plays the role of the 
    PoolAcquisition macro action (it aggregates the sub-actions and assign the 
    elements to corresponding sub-actions) and the PoolMeasurementGroup (it 
    configures the elements and controllers).
    """
    def setUp(self):
        """Create a Controller, TriggerGate and PoolTGGeneration objects from 
        dummy configurations.
        """
        unittest.TestCase.setUp(self)
        BasePoolTestCase.setUp(self)
        
    def event_received(self, *args, **kwargs):
        """Executes a single software triggered acquisition."""
        timestamp = time.time()
        _, event_type, event_id = args
        if event_type == TGEventType.Active:
            t_fmt = '%Y-%m-%d %H:%M:%S.%f'
            t_str = datetime.datetime.fromtimestamp(timestamp).strftime(t_fmt)
            is_acquiring = self.sw_acq.is_running()
            if is_acquiring:
                pass # skipping acquisition cause the previous on is ongoing
            else:                
                args = dict(self.sw_acq_args)
                kwargs = dict(self.sw_acq_kwargs)
                kwargs['idx'] = event_id
                kwargs['synch'] = True
                get_thread_pool().add(self.sw_acq.run, 
                                      None,
                                      *args,
                                      **kwargs)
        
    def continuous_acquisition(self, offset, active_period, passive_period, 
                                                      repetitions, integ_time):
        """Executes measurement running the TGGeneration and Acquisition actions
        according the test parameters. Checks the lengths of the acquired data.
        """
        # obtaining elements created in the BasePoolTestCase.setUp
        tg_ctrl_1 = self.ctrls['_test_tg_ctrl_1']
        tg_1_1 = self.tgs['_test_tg_1_1']
        ct_1_1 = self.cts['_test_ct_1_1']
        ct_2_1 = self.cts['_test_ct_2_1']
        ct_ctrl_1 = self.ctrls['_test_ct_ctrl_1']
        ct_ctrl_2 = self.ctrls['_test_ct_ctrl_2']
        
        # crating configuration for TGGeneration
        tg_cfg = createPoolTGGenerationConfiguration((tg_ctrl_1,), 
                                                     ((tg_1_1,),),)
        # creating TGGeneration action
        # TODO: the main_element should be a measurement group not an element
        self.tggeneration = PoolTGGeneration(tg_1_1)
        self.tggeneration.add_element(tg_1_1)
        self.tggeneration.add_listener(self)
        self.l = AttributeListener()
        ct_1_1._value.add_listener(self.l)
        ct_2_1._value.add_listener(self.l)
        # creating acquisition configurations
        self.hw_acq_cfg = createCTAcquisitionConfiguration((ct_ctrl_1,),
                                                             ((ct_1_1,),),)
        self.sw_acq_cfg = createCTAcquisitionConfiguration((ct_ctrl_2,),
                                                        ((ct_2_1,),),)
        # creating acquisition actions
        self.hw_acq = PoolContHWAcquisition(ct_1_1)
        self.sw_acq = PoolContSWCTAcquisition(ct_2_1)

        self.hw_acq.add_element(ct_1_1)
        self.sw_acq.add_element(ct_2_1)

        jobs_before = get_thread_pool().qsize
        
        self.sw_acq_args = ()
        self.sw_acq_kwargs = {
            'integ_time': integ_time, 
            'config': self.sw_acq_cfg
        }

        ct_ctrl_1.set_ctrl_par('trigger_type', AcqTriggerType.Trigger)

        hw_acq_args = ()
        hw_acq_kwargs = {
            'integ_time': integ_time,
            'repetitions': repetitions,
            'config': self.hw_acq_cfg,
        }                
        self.hw_acq.run(hw_acq_args, **hw_acq_kwargs)       
        tg_args = ()
        tg_kwargs = {
            'offset': offset,
            'active_period': active_period,
            'passive_period': passive_period,
            'repetitions': repetitions,
            'config': tg_cfg
        }
        self.tggeneration.run(*tg_args, **tg_kwargs)
        # waiting for acquisition and tggeneration to finish                
        while self.hw_acq.is_running() or\
              self.sw_acq.is_running() or\
              self.tggeneration.is_running():            
            time.sleep(1)
        table = self.l.get_table()
        # print header
        print table.dtype
        # print acquisition records
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
        BasePoolTestCase.tearDown(self)
        self.tgaction = None
        self.cfg = None        
        unittest.TestCase.tearDown(self)
