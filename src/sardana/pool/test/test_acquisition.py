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
import time
import datetime
import numpy
import threading

from taurus.external import unittest
from taurus.test import insertTest

from sardana.pool import AcqSynch
from sardana.pool.pooldefs import SynchDomain, SynchParam
from sardana.pool.poolsynchronization import PoolSynchronization
from sardana.pool.poolacquisition import (PoolAcquisitionHardware,
                                          PoolAcquisitionSoftware,
                                          PoolCTAcquisition)
from sardana.sardanautils import is_non_str_seq
from sardana.sardanathreadpool import get_thread_pool
from sardana.pool.test import (createPoolSynchronizationConfiguration,
                               createCTAcquisitionConfiguration,
                               BasePoolTestCase, FakeElement)


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
        if t.name.lower() != "valuebuffer":
            return
        # obtaining sardana element e.g. exp. channel (the attribute owner)
        obj_name = s.name
        # obtaining the SardanaValue(s) either from the value_chunk (in case
        # of buffered attributes) or from the value in case of normal
        # attributes
        chunk = v
        idx = chunk.keys()
        value = [sardana_value.value for sardana_value in chunk.values()]
        # filling the measurement records
        with self.data_lock:
            channel_data = self.data.get(obj_name, [])
            expected_idx = len(channel_data)
            pad = [None] * (idx[0] - expected_idx)
            channel_data.extend(pad + value)
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
                v.extend([None] * (max_len - len(v)))
                table.append(v)
                dtype_spec.append((k, 'float64'))
            a = numpy.array(zip(*table), dtype=dtype_spec)
            return a


class AcquisitionTestCase(BasePoolTestCase):

    def setUp(self):
        """Create a Controller, TriggerGate and PoolSynchronization objects from
        dummy configurations.
        """
        BasePoolTestCase.setUp(self)
        self.l = AttributeListener()
        self.channel_names = []

    def createPoolSynchronization(self, tg_list):
        self.main_element = FakeElement(self.pool)
        self.tggeneration = PoolSynchronization(self.main_element)
        for tg in tg_list:
            self.tggeneration.add_element(tg)
        self.tggeneration.add_listener(self)

    def hw_continuous_acquisition(self, offset, active_interval,
                                  passive_interval, repetitions, integ_time):
        """Executes measurement running the TGGeneration and Acquisition
        actions according the test parameters. Checks the lengths of the
        acquired data.
        """
        # obtaining elements created in the BasePoolTestCase.setUp
        tg = self.tgs[self.tg_elem_name]
        tg_ctrl = tg.get_controller()
        # crating configuration for TGGeneration
        tg_cfg = createPoolSynchronizationConfiguration((tg_ctrl,),
                                                        ((tg,),))
        # creating PoolSynchronization action
        self.createPoolSynchronization([tg])

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
        self.hw_acq = PoolAcquisitionHardware(channels[0])
        for channel in channels:
            self.hw_acq.add_element(channel)

        # get the current number of jobs
        jobs_before = get_thread_pool().qsize

        ct_ctrl.set_ctrl_par('synchronization', AcqSynch.HardwareTrigger)

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
            'active_interval': active_interval,
            'passive_interval': passive_interval,
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
        main_element = FakeElement(self.pool)
        self.ct_acq = PoolAcquisitionSoftware(main_element)
        for channel in channels:
            self.ct_acq.add_element(channel)

        ct_ctrl.set_ctrl_par('synchronization', AcqSynch.SoftwareTrigger)

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
            chn.add_listener(self.l)

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
               '(before: %d)') % (jobs_after, jobs_before)
        self.assertEqual(jobs_before, jobs_after, msg)

    def tearDown(self):
        BasePoolTestCase.tearDown(self)
        self.l = None
        self.channel_names = None


@insertTest(helper_name='continuous_acquisition', offset=0, active_interval=0.1,
            passive_interval=0.2, repetitions=10, integ_time=0.2)
@insertTest(helper_name='continuous_acquisition', offset=0,
            active_interval=0.001, passive_interval=0.21, repetitions=10,
            integ_time=0.1)
@insertTest(helper_name='continuous_acquisition', offset=0,
            active_interval=0.001, passive_interval=0.15, repetitions=10,
            integ_time=0.01)
@insertTest(helper_name='continuous_acquisition', offset=0,
            active_interval=0.001, passive_interval=0.1, repetitions=10,
            integ_time=0.01)
class DummyAcquisitionTestCase(AcquisitionTestCase, unittest.TestCase):
    """Integration test of PoolSynchronization, PoolAcquisitionHardware and
    PoolAcquisitionSoftware actions. This test plays the role of the
    PoolAcquisition macro action (it aggregates the sub-actions and assign the
    elements to corresponding sub-actions) and the PoolMeasurementGroup (it
    configures the elements and controllers).
    """

    def setUp(self):
        """Create a Controller, TriggerGate and PoolSynchronization objects from
        dummy configurations.
        """
        unittest.TestCase.setUp(self)
        AcquisitionTestCase.setUp(self)

    def event_received(self, *args, **kwargs):
        """Executes a single software triggered acquisition."""
        _, type_, value = args
        name = type_.name
        if name == "active":
            if self.sw_acq_busy.is_set():
                # skipping acquisition cause the previous on is ongoing
                return
            else:
                self.sw_acq_busy.set()
                args = dict(self.sw_acq_args)
                kwargs = dict(self.sw_acq_kwargs)
                kwargs['idx'] = value
                get_thread_pool().add(self.sw_acq.run,
                                      None,
                                      *args,
                                      **kwargs)

    def continuous_acquisition(self, offset, active_interval, passive_interval,
                               repetitions, integ_time):
        """Executes measurement running the TGGeneration and Acquisition actions
        according the test parameters. Checks the lengths of the acquired data.
        """
        # obtaining elements created in the BasePoolTestCase.setUp
        tg_2_1 = self.tgs['_test_tg_1_1']
        tg_ctrl_2 = tg_2_1.get_controller()
        ct_1_1 = self.cts['_test_ct_1_1']  # hw synchronized
        ct_2_1 = self.cts['_test_ct_2_1']  # sw synchronized
        ct_ctrl_1 = ct_1_1.get_controller()
        ct_ctrl_2 = ct_2_1.get_controller()
        self.channel_names.append('_test_ct_1_1')
        self.channel_names.append('_test_ct_2_1')
        # crating configuration for TGGeneration
        tg_cfg = createPoolSynchronizationConfiguration((tg_ctrl_2,),
                                                        ((tg_2_1,),))
        # creating TGGeneration action
        self.createPoolSynchronization([tg_2_1])
        # add_listeners
        self.addListeners([ct_1_1, ct_2_1])
        # creating acquisition configurations
        self.hw_acq_cfg = createCTAcquisitionConfiguration((ct_ctrl_1,),
                                                           ((ct_1_1,),))
        self.sw_acq_cfg = createCTAcquisitionConfiguration((ct_ctrl_2,),
                                                           ((ct_2_1,),))
        # creating acquisition actions
        self.hw_acq = PoolAcquisitionHardware(ct_1_1)
        self.sw_acq = PoolAcquisitionSoftware(ct_2_1)
        # Since we deposit the software acquisition action on the PoolThread's
        # queue we can not rely on the action's state - one may still wait
        # in the queue (its state has not changed to running yet) and we would
        # be depositing another one. This way we may be starting multiple
        # times the same action (with the same elements involved), what results
        # in "already involved in operation" errors.
        # Use an external Event flag to mark if we have any software
        # acquisition action pending.
        self.sw_acq_busy = threading.Event()
        self.sw_acq.add_finish_hook(self.sw_acq_busy.clear)

        self.hw_acq.add_element(ct_1_1)
        self.sw_acq.add_element(ct_2_1)

        # get the current number of jobs
        jobs_before = get_thread_pool().qsize

        self.sw_acq_args = ()
        self.sw_acq_kwargs = {
            'synch': True,
            'integ_time': integ_time,
            'repetitions': 1,
            'config': self.sw_acq_cfg
        }
        ct_ctrl_1.set_ctrl_par('synchronization', AcqSynch.HardwareTrigger)
        hw_acq_args = ()
        hw_acq_kwargs = {
            'integ_time': integ_time,
            'repetitions': repetitions,
            'config': self.hw_acq_cfg,
        }
        self.hw_acq.run(*hw_acq_args, **hw_acq_kwargs)
        tg_args = ()
        total_interval = active_interval + passive_interval
        synchronization = [{SynchParam.Delay: {SynchDomain.Time: offset},
                            SynchParam.Active: {SynchDomain.Time: active_interval},
                            SynchParam.Total: {SynchDomain.Time: total_interval},
                            SynchParam.Repeats: repetitions}]
        tg_kwargs = {
            'config': tg_cfg,
            'synchronization': synchronization
        }
        self.tggeneration.run(*tg_args, **tg_kwargs)
        # waiting for acquisition and tggeneration to finish
        while (self.hw_acq.is_running() or
               self.sw_acq.is_running() or
               self.tggeneration.is_running()):
            time.sleep(1)
        self.do_asserts(self.channel_names, repetitions, jobs_before)

    def tearDown(self):
        AcquisitionTestCase.tearDown(self)
        unittest.TestCase.tearDown(self)
