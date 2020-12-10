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

import numpy

from unittest import TestCase, mock
from taurus.test import insertTest

from sardana.sardanautils import is_number, is_pure_str
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

    CHANNEL_NAME = None  # Override this!
    SYNCHRONIZATION = None  # Override this!

    def setUp(self):
        """Create dummy controllers and elements."""
        BasePoolTestCase.setUp(self)
        self.acquisition = None
        self.synchronization = None
        self.data_listener = AttributeListener()
        self.main_element = FakeElement(self.pool)
        self.tg = self.tgs['_test_tg_1_1']
        self.tg_ctrl = self.tg.get_controller()
        self.channel = self.exp_channels[self.CHANNEL_NAME]
        self.channel_ctrl = self.channel.get_controller()
        self.channel_names = [self.CHANNEL_NAME]

    def create_action(self, class_, elements):
        action = class_(self.main_element)
        for element in elements:
            action.add_element(element)
        return action

    def add_listeners(self, chn_list):
        for chn in chn_list:
            chn.add_listener(self.data_listener)

    def _prepare(self, integ_time, repetitions, latency_time, nb_starts):
        pass

    def prepare(self, integ_time, repetitions, latency_time, nb_starts):
        self.channel_ctrl.set_ctrl_par("synchronization",
                                       self.SYNCHRONIZATION)
        self._prepare(integ_time, repetitions, latency_time, nb_starts)
        self.channel_ctrl.ctrl.PrepareOne(self.channel.axis, integ_time,
                                          repetitions, latency_time,
                                          nb_starts)

    def wait_finish(self):
        # waiting for acquisition and synchronization to finish
        while (self.acquisition._is_busy()
               or self.synchronization.is_running()):
            time.sleep(.1)

    def do_asserts(self, repetitions, jobs_before, strict=True):
        table = self.data_listener.get_table()
        header = table.dtype.names
        # checking if all channels produced data
        for channel in self.channel_names:
            msg = 'data from channel %s were not acquired' % channel
            self.assertIn(channel, header, msg)
        # checking if data were acquired
        for ch_name in header:
            ch_data_len = len(table[ch_name])
            if strict:
                msg = ('length of data for channel %s is %d and should be '
                       '%d' % (ch_name, ch_data_len, repetitions))
                self.assertEqual(repetitions, ch_data_len, msg)
            else:
                msg = ('length of data for channel %s is %d and should <= '
                       '%d' % (ch_name, ch_data_len, repetitions))
                self.assertGreaterEqual(repetitions, ch_data_len, msg)
            for value in table[ch_name]:
                if (isinstance(value, numpy.ndarray)
                        or is_number(value)
                        or is_pure_str(value)):
                    break
            else:
                raise AssertionError('channel %s does not report any '
                                     'valid data')
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

    CHANNEL_NAME = "_test_ct_1_1"

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
            if self.sw_acq._is_busy():
                # skipping acquisition cause the previous on is ongoing
                return
            else:
                self.sw_acq._set_busy()
                args = self.sw_acq_args
                kwargs = self.sw_acq_kwargs
                kwargs['index'] = index
                get_thread_pool().add(self.sw_acq.run,
                                      self.sw_acq._set_ready,
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
        self.sw_acq_args = (sw_ctrls, integ_time, sw_master)
        self.sw_acq_kwargs = dict(synch=True)

        total_interval = active_interval + passive_interval
        group = {
            SynchParam.Delay: {SynchDomain.Time: offset},
            SynchParam.Active: {SynchDomain.Time: active_interval},
            SynchParam.Total: {SynchDomain.Time: total_interval},
            SynchParam.Repeats: repetitions
        }
        synch_description = [group]
        # get the current number of jobs
        jobs_before = get_thread_pool().qsize
        self.hw_acq.run(hw_ctrls, integ_time, repetitions, 0)
        self.synchronization.run(synch_ctrls, synch_description)
        # waiting for acquisition and synchronization to finish
        while (self.hw_acq.is_running()
               or self.sw_acq._is_busy()
               or self.synchronization.is_running()):
            time.sleep(.1)
        self.do_asserts(repetitions, jobs_before)

    def tearDown(self):
        AcquisitionTestCase.tearDown(self)
        TestCase.tearDown(self)


class BaseAcquisitionSoftwareTestCase(AcquisitionTestCase):
    """Base class for integration tests of PoolSynchronization and
    PoolAcquisitionSoftware"""

    def setUp(self):
        """Create test actors (controllers and elements)"""
        TestCase.setUp(self)
        AcquisitionTestCase.setUp(self)

    def event_received(self, *args, **kwargs):
        """Callback to execute software start acquisition."""
        _, type_, value = args
        name = type_.name
        if name == "active":
            if self.acquisition._is_busy():
                # skipping acquisition cause the previous on is ongoing
                return
            else:
                self.acquisition._set_busy()
                acq_args = list(self.acq_args)
                acq_kwargs = self.acq_kwargs
                index = value
                acq_args[3] = index
                get_thread_pool().add(self.acquisition.run,
                                      self.acquisition._set_ready,
                                      *acq_args,
                                      **acq_kwargs)

    def acquire(self, integ_time, repetitions, latency_time):
        """Acquire with a dummy C/T synchronized by a hardware start
        trigger from a dummy T/G."""
        self.prepare(integ_time, repetitions, latency_time, 1)
        conf_ct_ctrl_1 = createTimerableControllerConfiguration(
            self.channel_ctrl, [self.channel])
        ctrls = get_timerable_ctrls([conf_ct_ctrl_1], AcqMode.Timer)
        master = ctrls[0].master
        # creating synchronization action
        self.synchronization = self.create_action(PoolSynchronization,
                                                  [self.tg])
        self.synchronization.add_listener(self)
        # add_listeners
        self.add_listeners([self.channel])
        # creating acquisition actions
        self.acquisition = self.create_action(PoolAcquisitionSoftware,
                                              [self.channel])
        self.acq_args = (ctrls, integ_time, master, None)
        self.acq_kwargs = dict(synch=True)

        total_interval = integ_time + latency_time
        group = {
            SynchParam.Delay: {SynchDomain.Time: 0},
            SynchParam.Active: {SynchDomain.Time: integ_time},
            SynchParam.Total: {SynchDomain.Time: total_interval},
            SynchParam.Repeats: repetitions
        }
        synch_description = [group]
        # get the current number of jobs
        jobs_before = get_thread_pool().qsize
        self.synchronization.run([], synch_description)
        self.wait_finish()
        self.do_asserts(repetitions, jobs_before, strict=False)

    def tearDown(self):
        AcquisitionTestCase.tearDown(self)
        TestCase.tearDown(self)


class BaseAcquisitionSoftwareStartTestCase(AcquisitionTestCase):
    """Base class for integration tests of PoolSynchronization and
    PoolAcquisitionSoftwareStart"""

    SYNCHRONIZATION = AcqSynch.SoftwareStart

    def setUp(self):
        """Create test actors (controllers and elements)"""
        AcquisitionTestCase.setUp(self)

    def event_received(self, *args, **kwargs):
        """Callback to execute software start acquisition."""
        _, type_, value = args
        name = type_.name
        if name == "start":
            self.acquisition._set_busy()
            get_thread_pool().add(self.acquisition.run,
                                  self.acquisition._set_ready,
                                  *self.acq_args,
                                  **self.acq_kwargs)

    def acquire(self, integ_time, repetitions, latency_time):
        """Acquire with a dummy C/T synchronized by a hardware start
        trigger from a dummy T/G."""
        self.prepare(integ_time, repetitions, latency_time, 1)
        conf_ct_ctrl_1 = createTimerableControllerConfiguration(
            self.channel_ctrl, [self.channel])
        ctrls = get_timerable_ctrls([conf_ct_ctrl_1], AcqMode.Timer)
        master = ctrls[0].master
        # creating synchronization action
        self.synchronization = self.create_action(PoolSynchronization,
                                                  [self.tg])
        self.synchronization.add_listener(self)
        # add_listeners
        self.add_listeners([self.channel])
        # creating acquisition actions
        self.acquisition = self.create_action(PoolAcquisitionSoftwareStart,
                                              [self.channel])
        self.acq_args = (ctrls, integ_time, master, repetitions, latency_time)
        self.acq_kwargs = dict(synch=True)

        total_interval = integ_time + latency_time
        group = {
            SynchParam.Delay: {SynchDomain.Time: 0},
            SynchParam.Active: {SynchDomain.Time: integ_time},
            SynchParam.Total: {SynchDomain.Time: total_interval},
            SynchParam.Repeats: repetitions
        }
        synch_description = [group]
        # get the current number of jobs
        jobs_before = get_thread_pool().qsize
        self.synchronization.run([], synch_description)
        self.wait_finish()
        self.do_asserts(repetitions, jobs_before, strict=False)

    def tearDown(self):
        AcquisitionTestCase.tearDown(self)


class BaseAcquisitionHardwareTestCase(AcquisitionTestCase):
    """Integration test of PoolSynchronization and PoolAcquisitionHardware"""

    def setUp(self):
        """Create test actors (controllers and elements)"""
        TestCase.setUp(self)
        AcquisitionTestCase.setUp(self)

    def acquire(self, integ_time, repetitions, latency_time):
        """Acquire with a dummy C/T synchronized by a hardware start
        trigger from a dummy T/G."""
        self.prepare(integ_time, repetitions, latency_time, 1)
        conf_ct_ctrl_1 = createTimerableControllerConfiguration(
            self.channel_ctrl, [self.channel])
        ctrls = get_timerable_ctrls([conf_ct_ctrl_1], AcqMode.Timer)
        conf_tg_ctrl_1 = createControllerConfiguration(self.tg_ctrl,
                                                       [self.tg])
        synch_ctrls = get_acq_ctrls([conf_tg_ctrl_1])
        self.synchronization = self.create_action(PoolSynchronization,
                                                  [self.tg])
        # add data listeners
        self.add_listeners([self.channel])
        # creating acquisition actions
        self.acquisition = self.create_action(PoolAcquisitionHardware,
                                              [self.channel])
        self.acq_args = ([conf_ct_ctrl_1], integ_time, repetitions)
        # prepare synchronization description
        total_interval = integ_time + latency_time
        group = {
            SynchParam.Delay: {SynchDomain.Time: 0},
            SynchParam.Active: {SynchDomain.Time: integ_time},
            SynchParam.Total: {SynchDomain.Time: total_interval},
            SynchParam.Repeats: repetitions
        }
        synch_description = [group]
        # get the current number of jobs
        jobs_before = get_thread_pool().qsize
        self.acquisition.run(ctrls, integ_time, repetitions, 0)
        self.synchronization.run(synch_ctrls, synch_description)
        self.wait_finish()
        self.do_asserts(repetitions, jobs_before)

    def wait_finish(self):
        # waiting for acquisition and synchronization to finish
        while (self.acquisition.is_running()
               or self.synchronization.is_running()):
            time.sleep(.1)

    def tearDown(self):
        AcquisitionTestCase.tearDown(self)
        TestCase.tearDown(self)


@insertTest(helper_name='acquire', integ_time=0.01, repetitions=10,
            latency_time=0.02)
class AcquisitionCTSoftwareTriggerTestCase(BaseAcquisitionSoftwareTestCase,
                                           TestCase):
    """Integration test of PoolSynchronization and PoolAcquisitionSoftware
    with dummy CT channel synchronized by software trigger."""

    CHANNEL_NAME = "_test_ct_1_1"
    SYNCHRONIZATION = AcqSynch.SoftwareTrigger


@insertTest(helper_name='acquire', integ_time=0.01, repetitions=10,
            latency_time=0.02)
class Acquisition2DSoftwareTriggerTestCase(BaseAcquisitionSoftwareTestCase,
                                           TestCase):
    """Integration test of PoolSynchronization and PoolAcquisitionSoftware
    with dummy 2D channel synchronized by software trigger."""

    CHANNEL_NAME = "_test_2d_1_1"
    SYNCHRONIZATION = AcqSynch.SoftwareTrigger

    def setUp(self):
        """Create test actors (controllers and elements)"""
        TestCase.setUp(self)
        BaseAcquisitionSoftwareTestCase.setUp(self)
        self.data_listener = AttributeListener(dtype=object,
                                               attr_name="valuebuffer")


@insertTest(helper_name='acquire', integ_time=0.01, repetitions=10,
            latency_time=0.1)
class Acquisition2DSoftwareTriggerRefTestCase(BaseAcquisitionSoftwareTestCase,
                                              TestCase):
    """Integration test of PoolSynchronization and PoolAcquisitionHardware
    with dummy 2D channel synchronized by software trigger and configured to
    report value reference.
    """
    CHANNEL_NAME = "_test_2d_1_1"
    SYNCHRONIZATION = AcqSynch.SoftwareTrigger

    def setUp(self):
        """Create test actors (controllers and elements)"""
        TestCase.setUp(self)
        BaseAcquisitionSoftwareTestCase.setUp(self)
        self.data_listener = AttributeListener(dtype=object,
                                               attr_name="valuerefbuffer")

    def _prepare(self, integ_time, repetitions, latency_time, nb_starts):
        self.channel.value_ref_enabled = True
        axis = self.channel.axis
        self.channel_ctrl.set_axis_par(axis, "value_ref_enabled", True)


@insertTest(helper_name='acquire', integ_time=0.01, repetitions=10,
            latency_time=0.1)
class AcquisitionCTSoftwareStartTestCase(
        BaseAcquisitionSoftwareStartTestCase, TestCase):
    """Integration test of PoolSynchronization and PoolAcquisitionHardware
    with dummy CT channel synchronized by software start.
    """

    CHANNEL_NAME = "_test_ct_1_1"

    def setUp(self):
        """Create test actors (controllers and elements)"""
        TestCase.setUp(self)
        BaseAcquisitionSoftwareStartTestCase.setUp(self)
        self.data_listener = AttributeListener(dtype=object,
                                               attr_name="valuebuffer")


@insertTest(helper_name='acquire', integ_time=0.01, repetitions=10,
            latency_time=0.1)
class Acquisition2DSoftwareStartTestCase(
        BaseAcquisitionSoftwareStartTestCase, TestCase):
    """Integration test of PoolSynchronization and PoolAcquisitionHardware
    with dummy 2D channel synchronized by software start.
    """

    CHANNEL_NAME = "_test_2d_1_1"

    def setUp(self):
        """Create test actors (controllers and elements)"""
        TestCase.setUp(self)
        BaseAcquisitionSoftwareStartTestCase.setUp(self)
        self.data_listener = AttributeListener(dtype=object,
                                               attr_name="valuebuffer")

    def _prepare(self, integ_time, repetitions, latency_time, nb_starts):
        axis = self.channel.axis
        self.channel_ctrl.set_axis_par(axis, "value_ref_enabled", False)
        self.channel.value_ref_enabled = False


@insertTest(helper_name='acquire', integ_time=0.01, repetitions=10,
            latency_time=0.1)
class Acquisition2DSoftwareStartRefTestCase(
        BaseAcquisitionSoftwareStartTestCase, TestCase):
    """Integration test of PoolSynchronization and PoolAcquisitionHardware
    with dummy 2D channel synchronized by software start and configured to
    report value reference.
    """
    CHANNEL_NAME = "_test_2d_1_1"

    def setUp(self):
        """Create test actors (controllers and elements)"""
        TestCase.setUp(self)
        BaseAcquisitionSoftwareStartTestCase.setUp(self)
        self.data_listener = AttributeListener(dtype=object,
                                               attr_name="valuerefbuffer")

    def _prepare(self, integ_time, repetitions, latency_time, nb_starts):
        self.channel.value_ref_enabled = True
        axis = self.channel.axis
        self.channel_ctrl.set_axis_par(axis, "value_ref_enabled", True)


@insertTest(helper_name='acquire', integ_time=0.01, repetitions=10,
            latency_time=0.02)
class AcquisitionCTHardwareStartTestCase(BaseAcquisitionHardwareTestCase,
                                         TestCase):
    """Integration test of PoolSynchronization and PoolAcquisitionHardware
    with dummy CT channel synchronized by hardware start.
    """
    CHANNEL_NAME = "_test_ct_1_1"
    SYNCHRONIZATION = AcqSynch.HardwareStart

    def setUp(self):
        """Create test actors (controllers and elements)"""
        TestCase.setUp(self)
        AcquisitionTestCase.setUp(self)
        self.data_listener = AttributeListener(dtype=object,
                                               attr_name="valuebuffer")


@insertTest(helper_name='acquire', integ_time=0.01, repetitions=10,
            latency_time=0.02)
class Acquisition2DHardwareStartTestCase(BaseAcquisitionHardwareTestCase,
                                         TestCase):
    """Integration test of PoolSynchronization and PoolAcquisitionHardware
    with dummy 2D channel synchronized by hardware start.
    """
    CHANNEL_NAME = "_test_2d_1_1"
    SYNCHRONIZATION = AcqSynch.HardwareStart

    def setUp(self):
        """Create test actors (controllers and elements)"""
        TestCase.setUp(self)
        BaseAcquisitionHardwareTestCase.setUp(self)
        self.data_listener = AttributeListener(dtype=object,
                                               attr_name="valuebuffer")

    def acquire(self, integ_time, repetitions, latency_time):
        ctrl = self.channel_ctrl.ctrl
        with mock.patch.object(ctrl, "ReadOne",
                               wraps=ctrl.ReadOne) as mock_ReadOne:
            BaseAcquisitionHardwareTestCase.acquire(self, integ_time,
                                                    repetitions, latency_time)
            assert mock_ReadOne.call_count > 1


@insertTest(helper_name='acquire', integ_time=0.01, repetitions=10,
            latency_time=0.02)
class Acquisition2DHardwareStartRefTestCase(
        BaseAcquisitionHardwareTestCase, TestCase):
    """Integration test of PoolSynchronization and PoolAcquisitionHardware
    with dummy 2D channel synchronized by hardware start and configured to
    report value reference.
    """
    CHANNEL_NAME = "_test_2d_1_1"
    SYNCHRONIZATION = AcqSynch.HardwareStart

    def setUp(self):
        """Create test actors (controllers and elements)"""
        TestCase.setUp(self)
        BaseAcquisitionHardwareTestCase.setUp(self)
        self.channel_ctrl.set_log_level(10)
        self.data_listener = AttributeListener(dtype=object,
                                               attr_name="valuerefbuffer")

    def _prepare(self, integ_time, repetitions, latency_time, nb_starts):
        self.channel.value_ref_enabled = True
        axis = self.channel.axis
        self.channel_ctrl.set_axis_par(axis, "value_ref_enabled", True)

    def acquire(self, integ_time, repetitions, latency_time):
        ctrl = self.channel_ctrl.ctrl
        with mock.patch.object(ctrl, "RefOne",
                               wraps=ctrl.RefOne) as mock_RefOne:
            BaseAcquisitionHardwareTestCase.acquire(self, integ_time,
                                                    repetitions, latency_time)
            assert mock_RefOne.call_count > 1


@insertTest(helper_name='acquire', integ_time=0.01, repetitions=10,
            latency_time=0.02)
class AcquisitionCTHardwareTriggerTestCase(BaseAcquisitionHardwareTestCase,
                                           TestCase):
    """Integration test of PoolSynchronization and PoolAcquisitionHardware
    with dummy CT channel synchronized by hardware trigger."""

    CHANNEL_NAME = "_test_ct_1_1"
    SYNCHRONIZATION = AcqSynch.HardwareTrigger

    def setUp(self):
        """Create test actors (controllers and elements)"""
        TestCase.setUp(self)
        BaseAcquisitionHardwareTestCase.setUp(self)
        self.data_listener = AttributeListener(dtype=object,
                                               attr_name="valuebuffer")

    def acquire(self, integ_time, repetitions, latency_time):
        ctrl = self.channel_ctrl.ctrl
        with mock.patch.object(ctrl, "ReadOne",
                               wraps=ctrl.ReadOne) as mock_ReadOne:
            BaseAcquisitionHardwareTestCase.acquire(self, integ_time,
                                                    repetitions, latency_time)
            assert mock_ReadOne.call_count > 1


@insertTest(helper_name='acquire', integ_time=0.01, repetitions=10,
            latency_time=0.02)
class Acquisition2DHardwareTriggerTestCase(BaseAcquisitionHardwareTestCase,
                                           TestCase):
    """Integration test of PoolSynchronization and PoolAcquisitionHardware
    with dummy 2D channel synchronized by hardware trigger."""

    CHANNEL_NAME = "_test_2d_1_1"
    SYNCHRONIZATION = AcqSynch.HardwareTrigger

    def setUp(self):
        """Create test actors (controllers and elements)"""
        TestCase.setUp(self)
        BaseAcquisitionHardwareTestCase.setUp(self)
        self.data_listener = AttributeListener(dtype=object,
                                               attr_name="valuebuffer")

    def acquire(self, integ_time, repetitions, latency_time):
        ctrl = self.channel_ctrl.ctrl
        with mock.patch.object(ctrl, "ReadOne",
                               wraps=ctrl.ReadOne) as mock_ReadOne:
            BaseAcquisitionHardwareTestCase.acquire(self, integ_time,
                                                    repetitions, latency_time)
            assert mock_ReadOne.call_count > 1


@insertTest(helper_name='acquire', integ_time=0.01, repetitions=10,
            latency_time=0.02)
class Acquisition2DHardwareTriggerRefTestCase(BaseAcquisitionHardwareTestCase,
                                              TestCase):
    """Integration test of PoolSynchronization and PoolAcquisitionHardware
    with dummy 2D channel synchronized by hardware trigger and configured to
    report value reference.
    """
    CHANNEL_NAME = "_test_2d_1_1"
    SYNCHRONIZATION = AcqSynch.HardwareTrigger

    def setUp(self):
        """Create test actors (controllers and elements)"""
        TestCase.setUp(self)
        BaseAcquisitionHardwareTestCase.setUp(self)
        self.data_listener = AttributeListener(dtype=object,
                                               attr_name="valuerefbuffer")

    def _prepare(self, integ_time, repetitions, latency_time, nb_starts):
        self.channel.value_ref_enabled = True
        axis = self.channel.axis
        self.channel_ctrl.set_axis_par(axis, "value_ref_enabled", True)

    def acquire(self, integ_time, repetitions, latency_time):
        ctrl = self.channel_ctrl.ctrl
        with mock.patch.object(ctrl, "RefOne",
                               wraps=ctrl.RefOne) as mock_RefOne:
            BaseAcquisitionHardwareTestCase.acquire(self, integ_time,
                                                    repetitions, latency_time)
            assert mock_RefOne.call_count > 1


@insertTest(helper_name='acquire', integ_time=0.01, repetitions=10,
            latency_time=0.02)
class AcquisitionCTHardwareGateTestCase(BaseAcquisitionHardwareTestCase,
                                        TestCase):
    """Integration test of PoolSynchronization and PoolAcquisitionHardware
    with dummy CT channel synchronized by hardware gate."""

    CHANNEL_NAME = "_test_ct_1_1"
    SYNCHRONIZATION = AcqSynch.HardwareGate

    def setUp(self):
        """Create test actors (controllers and elements)"""
        TestCase.setUp(self)
        BaseAcquisitionHardwareTestCase.setUp(self)
        self.data_listener = AttributeListener(dtype=object,
                                               attr_name="valuebuffer")


@insertTest(helper_name='acquire', integ_time=0.01, repetitions=10,
            latency_time=0.02)
class Acquisition2DHardwareGateTestCase(BaseAcquisitionHardwareTestCase,
                                        TestCase):
    """Integration test of PoolSynchronization and PoolAcquisitionHardware
    with dummy 2D channel synchronized by hardware gate."""

    CHANNEL_NAME = "_test_2d_1_1"
    SYNCHRONIZATION = AcqSynch.HardwareGate

    def setUp(self):
        """Create test actors (controllers and elements)"""
        TestCase.setUp(self)
        BaseAcquisitionHardwareTestCase.setUp(self)
        self.data_listener = AttributeListener(dtype=object,
                                               attr_name="valuebuffer")


@insertTest(helper_name='acquire', integ_time=0.01, repetitions=10,
            latency_time=0.02)
class Acquisition2DHardwareGateRefTestCase(BaseAcquisitionHardwareTestCase,
                                           TestCase):
    """Integration test of PoolSynchronization and PoolAcquisitionHardware
    with dummy 2D channel synchronized by hardware gate and configured to
    report value reference.
    """
    CHANNEL_NAME = "_test_2d_1_1"
    SYNCHRONIZATION = AcqSynch.HardwareGate

    def setUp(self):
        """Create test actors (controllers and elements)"""
        TestCase.setUp(self)
        BaseAcquisitionHardwareTestCase.setUp(self)
        self.data_listener = AttributeListener(dtype=object,
                                               attr_name="valuerefbuffer")

    def _prepare(self, integ_time, repetitions, latency_time, nb_starts):
        self.channel.value_ref_enabled = True
        axis = self.channel.axis
        self.channel_ctrl.set_axis_par(axis, "value_ref_enabled", True)
