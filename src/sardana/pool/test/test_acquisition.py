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
import threading

from taurus.external.unittest import TestCase
from taurus.test import insertTest

from sardana.pool import AcqSynch, AcqMode
from sardana.pool.pooldefs import SynchDomain, SynchParam
from sardana.pool.poolsynchronization import PoolSynchronization
from sardana.pool.poolacquisition import PoolAcquisitionHardware, \
    PoolAcquisitionSoftware, PoolAcquisitionSoftwareStart, \
    get_acq_ctrls, get_timerable_ctrls
from sardana.sardanathreadpool import get_thread_pool
from sardana.pool.test import createControllerConfiguration, \
    createTimerableControllerConfiguration, BasePoolTestCase, FakeElement, \
    AttributeListener


class AcquisitionTestCase(BasePoolTestCase):

    def setUp(self):
        """Create dummy controllers and elements."""
        BasePoolTestCase.setUp(self)
        self.acquisition = None
        self.synchronization = None
        self.data_listener = AttributeListener()
        self.main_element = FakeElement(self.pool)
        self.tg_1_1 = self.tgs['_test_tg_1_1']
        self.tg_ctrl_1 = self.tg_1_1.get_controller()
        self.ct_1_1 = self.cts['_test_ct_1_1']
        self.ct_ctrl_1 = self.ct_1_1.get_controller()
        self.channel_names = ['_test_ct_1_1']

    def create_action(self, class_, elements):
        action = class_(self.main_element)
        for element in elements:
            action.add_element(element)
        return action

    def add_listeners(self, chn_list):
        for chn in chn_list:
            chn.add_listener(self.data_listener)

    def wait_finish(self):
        # waiting for acquisition and synchronization to finish
        while (self.acquisition.is_running()
               or self.synchronization.is_running()):
            time.sleep(.1)

    def do_asserts(self, repetitions, jobs_before):
        # print acquisition records
        table = self.data_listener.get_table()
        header = table.dtype.names
        print header
        n_rows = table.shape[0]
        for row in xrange(n_rows):
            print row, table[row]
        # checking if all channels produced data
        for channel in self.channel_names:
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
        self.data_listener = None
        self.channel_names = None
        self.main_element = None


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
class DummyAcquisitionTestCase(AcquisitionTestCase, TestCase):
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
        TestCase.setUp(self)
        AcquisitionTestCase.setUp(self)

    def event_received(self, *args, **kwargs):
        """Executes a single software triggered acquisition."""
        _, type_, index = args
        name = type_.name
        if name == "active":
            if self.sw_acq_busy.is_set():
                # skipping acquisition cause the previous on is ongoing
                return
            else:
                self.sw_acq_busy.set()
                args = self.sw_acq_args
                kwargs = self.sw_acq_kwargs
                kwargs['index'] = index
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
        tg_1_1 = self.tgs['_test_tg_1_1']
        tg_ctrl_1 = tg_1_1.get_controller()
        ct_1_1 = self.cts['_test_ct_1_1']  # hw synchronized
        ct_2_1 = self.cts['_test_ct_2_1']  # sw synchronized
        ct_ctrl_1 = ct_1_1.get_controller()
        ct_ctrl_1.set_ctrl_par("synchronization", AcqSynch.HardwareTrigger)
        ct_ctrl_2 = ct_2_1.get_controller()
        self.channel_names.append('_test_ct_1_1')
        self.channel_names.append('_test_ct_2_1')

        conf_ct_ctrl_1 = createTimerableControllerConfiguration(ct_ctrl_1,
                                                                [ct_1_1])
        conf_ct_ctrl_2 = createTimerableControllerConfiguration(ct_ctrl_2,
                                                                [ct_2_1])
        hw_ctrls = get_timerable_ctrls([conf_ct_ctrl_1],
                                       acq_mode=AcqMode.Timer)
        sw_ctrls = get_timerable_ctrls([conf_ct_ctrl_2],
                                       acq_mode=AcqMode.Timer)
        sw_master = sw_ctrls[0].master
        conf_tg_ctrl_1 = createControllerConfiguration(tg_ctrl_1, [tg_1_1])
        synch_ctrls = get_acq_ctrls([conf_tg_ctrl_1])
        # creating synchronization action
        self.synchronization = self.create_action(PoolSynchronization,
                                                  [tg_1_1])
        self.synchronization.add_listener(self)
        # add_listeners
        self.add_listeners([ct_1_1, ct_2_1])
        # creating acquisition actions
        self.hw_acq = self.create_action(PoolAcquisitionHardware, [ct_1_1])
        self.sw_acq = self.create_action(PoolAcquisitionSoftware, [ct_2_1])
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
        self.sw_acq_args = (sw_ctrls, integ_time, sw_master)
        self.sw_acq_kwargs = {}

        total_interval = active_interval + passive_interval
        group = {
            SynchParam.Delay: {SynchDomain.Time: offset},
            SynchParam.Active: {SynchDomain.Time: active_interval},
            SynchParam.Total: {SynchDomain.Time: total_interval},
            SynchParam.Repeats: repetitions
        }
        synchronization = [group]
        # get the current number of jobs
        jobs_before = get_thread_pool().qsize
        self.hw_acq.run(hw_ctrls, integ_time, repetitions, 0)
        self.synchronization.run(synch_ctrls, synchronization)
        # waiting for acquisition and synchronization to finish
        while (self.hw_acq.is_running()
               or self.sw_acq.is_running()
               or self.synchronization.is_running()):
            time.sleep(.1)
        self.do_asserts(repetitions, jobs_before)

    def tearDown(self):
        AcquisitionTestCase.tearDown(self)
        TestCase.tearDown(self)


@insertTest(helper_name='acquire', integ_time=0.01, repetitions=10,
            latency_time=0.02)
class AcquisitionSoftwareStartTestCase(AcquisitionTestCase, TestCase):
    """Integration test of PoolSynchronization and PoolAcquisitionHardware"""

    def setUp(self):
        """Create test actors (controllers and elements)"""
        TestCase.setUp(self)
        AcquisitionTestCase.setUp(self)

    def event_received(self, *args, **kwargs):
        """Callback to execute software start acquisition."""
        _, type_, value = args
        name = type_.name
        if name != "start":
            return
        args = self.acq_args
        kwargs = self.acq_kwargs
        get_thread_pool().add(self.acquisition.run, None, *args, **kwargs)

    def acquire(self, integ_time, repetitions, latency_time):
        """Acquire with a dummy C/T synchronized by a hardware start
        trigger from a dummy T/G."""
        self.ct_ctrl_1.set_ctrl_par("synchronization", AcqSynch.SoftwareStart)

        conf_ct_ctrl_1 = createTimerableControllerConfiguration(self.ct_ctrl_1,
                                                                [self.ct_1_1])
        ctrls = get_timerable_ctrls([conf_ct_ctrl_1], AcqMode.Timer)
        master = ctrls[0].master
        # creating synchronization action
        self.synchronization = self.create_action(PoolSynchronization,
                                                  [self.tg_1_1])
        self.synchronization.add_listener(self)
        # add_listeners
        self.add_listeners([self.ct_1_1])
        # creating acquisition actions
        self.acquisition = self.create_action(PoolAcquisitionSoftwareStart,
                                              [self.ct_1_1])

        self.acq_args = (ctrls, integ_time, master, repetitions, 0)
        self.acq_kwargs = {}

        total_interval = integ_time + latency_time
        group = {
            SynchParam.Delay: {SynchDomain.Time: 0},
            SynchParam.Active: {SynchDomain.Time: integ_time},
            SynchParam.Total: {SynchDomain.Time: total_interval},
            SynchParam.Repeats: repetitions
        }
        synchronization = [group]
        # get the current number of jobs
        jobs_before = get_thread_pool().qsize
        self.synchronization.run([], synchronization)
        self.wait_finish()
        self.do_asserts(repetitions, jobs_before)

    def tearDown(self):
        AcquisitionTestCase.tearDown(self)
        TestCase.tearDown(self)


@insertTest(helper_name='acquire', integ_time=0.01, repetitions=10,
            latency_time=0.02)
class AcquisitionHardwareStartTestCase(AcquisitionTestCase, TestCase):
    """Integration test of PoolSynchronization and PoolAcquisitionHardware"""

    def setUp(self):
        """Create test actors (controllers and elements)"""
        TestCase.setUp(self)
        AcquisitionTestCase.setUp(self)

    def acquire(self, integ_time, repetitions, latency_time):
        """Acquire with a dummy C/T synchronized by a hardware start
        trigger from a dummy T/G."""
        self.ct_ctrl_1.set_ctrl_par("synchronization", AcqSynch.HardwareStart)
        conf_ct_ctrl_1 = createTimerableControllerConfiguration(
            self.ct_ctrl_1, [self.ct_1_1])
        ctrls = get_timerable_ctrls([conf_ct_ctrl_1], AcqMode.Timer)
        conf_tg_ctrl_1 = createControllerConfiguration(self.tg_ctrl_1,
                                                       [self.tg_1_1])
        synch_ctrls = get_acq_ctrls([conf_tg_ctrl_1])
        self.synchronization = self.create_action(PoolSynchronization,
                                                  [self.tg_1_1])
        # add data listeners
        self.add_listeners([self.ct_1_1])
        # creating acquisition actions
        self.acquisition = self.create_action(PoolAcquisitionHardware,
                                              [self.ct_1_1])
        self.acq_args = ([conf_ct_ctrl_1], integ_time, repetitions)
        # prepare synchronization description
        total_interval = integ_time + latency_time
        group = {
            SynchParam.Delay: {SynchDomain.Time: 0},
            SynchParam.Active: {SynchDomain.Time: integ_time},
            SynchParam.Total: {SynchDomain.Time: total_interval},
            SynchParam.Repeats: repetitions
        }
        synchronization = [group]
        # get the current number of jobs
        jobs_before = get_thread_pool().qsize
        self.acquisition.run(ctrls, integ_time, repetitions, 0)
        self.synchronization.run(synch_ctrls, synchronization)
        self.wait_finish()
        self.do_asserts(repetitions, jobs_before)

    def tearDown(self):
        AcquisitionTestCase.tearDown(self)
        TestCase.tearDown(self)
