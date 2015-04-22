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
import numpy
import threading

from taurus.external import unittest
from taurus.test import insertTest
#TODO: import mock using taurus.external

from sardana.pool import AcqTriggerType
from sardana.pool.pooltggeneration import PoolTGGeneration
from sardana.pool.pooltriggergate import TGEventType
from sardana.pool.poolacquisition import (PoolContHWAcquisition,
                                          PoolContSWCTAcquisition,
                                          PoolCTAcquisition)
from sardana.sardanathreadpool import get_thread_pool
from sardana.pool.test import (createPoolTGGenerationConfiguration,
                               createCTAcquisitionConfiguration,
                               BasePoolTestCase)

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

class AcquisitionTestCase(BasePoolTestCase):
    def setUp(self):
        """Create a Controller, TriggerGate and PoolTGGeneration objects from
        dummy configurations.
        """
        BasePoolTestCase.setUp(self)
        self.l = AttributeListener()
        self.channel_names = []

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

    def createPoolTGGeneration(self, tg_list):
        # TODO: the main_element should be a measurement group not an element
        self.tggeneration = PoolTGGeneration(tg_list[0])
        for tg in tg_list:
            self.tggeneration.add_element(tg)
        self.tggeneration.add_listener(self)

    def hw_continuous_acquisition(self, offset, active_period, passive_period,
                               repetitions, integ_time):
        """Executes measurement running the TGGeneration and Acquisition
        actions according the test parameters. Checks the lengths of the
        acquired data.
        """
        # obtaining elements created in the BasePoolTestCase.setUp
        tg = self.tgs[self.tg_elem_name]
        tg_ctrl = tg.get_controller()
        # crating configuration for TGGeneration
        tg_cfg = createPoolTGGenerationConfiguration((tg_ctrl,),
                                                     ((tg,),))
        # creating TGGeneration action
        self.createPoolTGGeneration([tg])

        channels = []
        for name in self.channel_names:
            channels.append(self.cts[name])

        ct_ctrl = self.ctrls[self.chn_ctrl_name]


        # add_listeners
        self.addListeners(channels)
        # creating acquisition configurations
        self.hw_acq_cfg = createCTAcquisitionConfiguration((ct_ctrl,),
                                                           (channels,))
        # creating acquisition actions
        self.hw_acq = PoolContHWAcquisition(channels[0])
        for channel in channels:
            self.hw_acq.add_element(channel)

        # get the current number of jobs
        jobs_before = get_thread_pool().qsize

        ct_ctrl.set_ctrl_par('trigger_type', AcqTriggerType.Trigger)

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
        while self.hw_acq.is_running() or self.tggeneration.is_running():          
            time.sleep(1)

        self.do_asserts(self.channel_names, repetitions, jobs_before)

    def hw_step_acquisition(self, repetitions, integ_time):
        """Executes measurement running the TGGeneration and Acquisition
        actions according the test parameters. Checks the lengths of the
        acquired data.
        """

        channels = []
        for name in self.channel_names:
            channels.append(self.cts[name])

        ct_ctrl = self.ctrls[self.chn_ctrl_name]

        # creating acquisition configurations
        self.acq_cfg = createCTAcquisitionConfiguration((ct_ctrl,),
                                                        (channels,))
        # creating acquisition actions
        self.ct_acq = PoolCTAcquisition(channels[0])
        for channel in channels:
            self.ct_acq.add_element(channel)

        ct_ctrl.set_ctrl_par('trigger_type', AcqTriggerType.Software)

        ct_acq_args = ()
        ct_acq_kwargs = {
            'integ_time': integ_time,
            'repetitions': repetitions,
            'config': self.acq_cfg,
        }
        self.ct_acq.run(ct_acq_args, **ct_acq_kwargs)
        # waiting for acquisition 
        while self.ct_acq.is_running():
            time.sleep(0.02)

        for channel in channels:
            name = channel.name
            value = channel.value.value
            print 'channel: %s = %s' % (name, value)
            msg = ('Value for channel %s is of type %s, should be <float>' %
                    (name, type(value)))
            self.assertIsInstance(value, float, msg)


    def addListeners(self, chn_list):
        for chn in chn_list:
            chn._value.add_listener(self.l)

    def do_asserts(self, channel_names, repetitions, jobs_before):
        # print acquisition records
        table = self.l.get_table()
        header = table.dtype.names
        print header
        n_rows = table.shape[0]
        for row in xrange(n_rows):
            print row, table[row]
        # checking if all channels produced data
        for channel in channel_names:
            msg = 'data from channel %s were not acquired' % channel
            self.assertIn(channel, header, msg)
        # checking if all the data were acquired
        for ch_name in header:
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
        self.l = None
        self.channel_names = None

@insertTest(helper_name='continuous_acquisition', offset=0, active_period=0.1,
            passive_period=0.2, repetitions=10, integ_time=0.2)
@insertTest(helper_name='continuous_acquisition', offset=0, active_period=0.001,
            passive_period=0.21, repetitions=10, integ_time=0.1)
@insertTest(helper_name='continuous_acquisition', offset=0, active_period=0.001,
            passive_period=0.15, repetitions=10, integ_time=0.01)
@insertTest(helper_name='continuous_acquisition', offset=0, active_period=0.001,
            passive_period=0.1, repetitions=10, integ_time=0.01)
class DummyAcquisitionTestCase(AcquisitionTestCase, unittest.TestCase):
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
        AcquisitionTestCase.setUp(self)

    def continuous_acquisition(self, offset, active_period, passive_period,
                               repetitions, integ_time):
        """Executes measurement running the TGGeneration and Acquisition actions
        according the test parameters. Checks the lengths of the acquired data.
        """
        # obtaining elements created in the BasePoolTestCase.setUp
        tg_1_1 = self.tgs['_test_stg_1_1']
        tg_2_1 = self.tgs['_test_tg_1_1']
        tg_ctrl_1 = tg_1_1.get_controller()
        tg_ctrl_2 = tg_2_1.get_controller()
        ct_1_1 = self.cts['_test_ct_1_1'] # hw synchronized
        ct_2_1 = self.cts['_test_ct_2_1'] # sw synchronized
        ct_ctrl_1 = ct_1_1.get_controller()
        ct_ctrl_2 = ct_2_1.get_controller()
        self.channel_names.append('_test_ct_1_1')
        self.channel_names.append('_test_ct_2_1')
        # crating configuration for TGGeneration
        tg_cfg = createPoolTGGenerationConfiguration((tg_ctrl_1, tg_ctrl_2),
                                                     ((tg_1_1,), (tg_2_1,)))
        # creating TGGeneration action
        self.createPoolTGGeneration([tg_1_1, tg_2_1])
        # add_listeners
        self.addListeners([ct_1_1, ct_2_1])
        # creating acquisition configurations
        self.hw_acq_cfg = createCTAcquisitionConfiguration((ct_ctrl_1,),
                                                             ((ct_1_1,),))
        self.sw_acq_cfg = createCTAcquisitionConfiguration((ct_ctrl_2,),
                                                           ((ct_2_1,),))
        # creating acquisition actions
        self.hw_acq = PoolContHWAcquisition(ct_1_1)
        self.sw_acq = PoolContSWCTAcquisition(ct_2_1)

        self.hw_acq.add_element(ct_1_1)
        self.sw_acq.add_element(ct_2_1)

        # get the current number of jobs
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
        self.do_asserts(self.channel_names, repetitions, jobs_before)

    def tearDown(self):
        AcquisitionTestCase.tearDown(self) 
        unittest.TestCase.tearDown(self)

