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
import copy

import unittest
from taurus.test import insertTest

from sardana.sardanathreadpool import get_thread_pool
from sardana.pool import AcqSynchType, AcqMode
from sardana.pool.pooldefs import SynchDomain, SynchParam
from sardana.pool.test import BasePoolTestCase, createPoolMeasurementGroup,\
    dummyMeasurementGroupConf01, createMGUserConfiguration, AttributeListener


class BaseAcquisition(object):

    def setUp(self, pool):
        self.pool = pool
        self.pmg = None
        self.attr_listener = None

    def prepare_meas(self, config):
        """ Prepare measurement group and returns the channel names"""
        pool = self.pool
        # creating mg user configuration and obtaining channel ids
        mg_conf, channel_ids, channel_names = \
            createMGUserConfiguration(pool, config)
        conf = copy.deepcopy(dummyMeasurementGroupConf01)
        conf["name"] = 'mg1'
        conf["full_name"] = 'mg1'
        conf["user_elements"] = channel_ids
        self.pmg = createPoolMeasurementGroup(pool, conf)
        pool.add_element(self.pmg)
        self.pmg.set_configuration_from_user(mg_conf)
        return channel_names

    def prepare_attribute_listener(self):
        self.attr_listener = AttributeListener()
        # Add data listener
        attributes = self.pmg.get_user_elements()
        for attr in attributes:
            attr.add_listener(self.attr_listener)

    def remove_attribute_listener(self):
        # Remove data listener
        attributes = self.pmg.get_user_elements()
        for attr in attributes:
            attr.remove_listener(self.attr_listener)

    def acquire(self):
        """ Run acquisition
        """
        self.pmg.prepare()
        self.pmg.start_acquisition()
        acq = self.pmg.acquisition
        while acq.is_running():
            time.sleep(.1)

    def acq_asserts(self, channel_names, repetitions):
        # printing acquisition records
        table = self.attr_listener.get_table()
        header = table.dtype.names
        print(header)
        n_rows = table.shape[0]
        for row in range(n_rows):
            print(row, table[row])
        # checking if any of data was acquired
        self.assertTrue(self.attr_listener.data, 'no data were acquired')
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

    def meas_double_acquisition(self, config, synch_description,
                                moveable=None):
        """ Run two acquisition with the same measurement group, first with
        multiple repetitions and then one repetition.
        """
        channel_names = self.prepare_meas(config)
        # setting measurement parameters
        self.pmg.set_synch_description(synch_description)
        self.pmg.set_moveable(moveable, to_fqdn=False)
        repetitions = 0
        for group in synch_description:
            repetitions += group[SynchParam.Repeats]
        self.prepare_attribute_listener()
        self.acquire()
        self.acq_asserts(channel_names, repetitions)
        self.remove_attribute_listener()
        synch_description = [{SynchParam.Delay: {SynchDomain.Time: 0},
                              SynchParam.Active: {SynchDomain.Time: 0.1},
                              SynchParam.Total: {SynchDomain.Time: 0.2},
                              SynchParam.Repeats: 1}]
        self.pmg.synch_description = synch_description
        self.acquire()
        # TODO: implement asserts of Timer acquisition

    def meas_double_acquisition_samemode(self, config, synch_description,
                                         moveable=None):
        """ Run two acquisition with the same measurement group.
        """
        channel_names = self.prepare_meas(config)
        self.pmg.set_synch_description(synch_description)
        self.pmg.set_moveable(moveable, to_fqdn=False)
        repetitions = 0
        for group in synch_description:
            repetitions += group[SynchParam.Repeats]
        self.prepare_attribute_listener()
        self.acquire()
        self.acq_asserts(channel_names, repetitions)
        self.remove_attribute_listener()
        self.prepare_attribute_listener()
        self.acquire()
        self.acq_asserts(channel_names, repetitions)
        self.remove_attribute_listener()
        # TODO: implement asserts of Timer acquisition

    def consecutive_acquisitions(self, pool, config, synch_description):
        # creating mg user configuration and obtaining channel ids
        mg_conf, channel_ids, channel_names = createMGUserConfiguration(
            pool, config)

        # setting mg configuration - this cleans the action cache!
        self.pmg.set_configuration_from_user(mg_conf)
        repetitions = 0
        for group in synch_description:
            repetitions += group[SynchParam.Repeats]
        self.prepare_attribute_listener()
        self.acquire()
        self.acq_asserts(channel_names, repetitions)

    def meas_cont_acquisition(self, config, synch_description, moveable=None,
                              second_config=None):
        """Executes measurement using the measurement group.
        Checks the lengths of the acquired data.
        """
        jobs_before = get_thread_pool().qsize
        channel_names = self.prepare_meas(config)
        self.pmg.set_synch_description(synch_description)
        self.pmg.set_moveable(moveable, to_fqdn=False)
        repetitions = 0
        for group in synch_description:
            repetitions += group[SynchParam.Repeats]
        self.prepare_attribute_listener()
        self.acquire()
        self.acq_asserts(channel_names, repetitions)

        if second_config is not None:
            self.consecutive_acquisitions(
                self.pool, second_config, synch_description)

        # checking if there are no pending jobs
        jobs_after = get_thread_pool().qsize
        msg = ('there are %d jobs pending to be done after the acquisition ' +
               '(before: %d)') % (jobs_after, jobs_before)
        self.assertEqual(jobs_before, jobs_after, msg)

    def stop_acquisition(self):
        """Method used to abort a running acquisition"""
        self.pmg.stop()

    def meas_cont_stop_acquisition(self, config, synch_description,
                                   moveable=None):
        """Executes measurement using the measurement group and tests that the
        acquisition can be stopped.
        """
        self.prepare_meas(config)
        self.pmg.synch_description = synch_description
        self.pmg.set_moveable(moveable, to_fqdn=False)
        self.prepare_attribute_listener()

        self.pmg.prepare()
        self.pmg.start_acquisition()
        # retrieving the acquisition since it was cleaned when applying mg conf
        acq = self.pmg.acquisition

        # starting timer (0.05 s) which will stop the acquisiton
        threading.Timer(0.2, self.stop_acquisition).start()
        # waiting for acquisition and tggeneration to be stoped by thread
        while acq.is_running():
            time.sleep(0.05)
        msg = "acquisition shall NOT be running after stopping it"
        self.assertEqual(acq.is_running(), False, msg)

        tp = get_thread_pool()
        numBW = tp.getNumOfBusyWorkers()
        msg = "The number of busy workers is not zero; numBW = %s" % (numBW)
        self.assertEqual(numBW, 0, msg)
        # print the acquisition records
        for i, record in \
                enumerate(zip(*list(self.attr_listener.data.values()))):
            print(i, record)

    def meas_contpos_acquisition(self, config, synch_description, moveable,
                                 second_config=None):
        # TODO: this code is ready only for one group configuration
        initial = \
            synch_description[0][SynchParam.Initial][SynchDomain.Position]
        total = synch_description[0][SynchParam.Total][SynchDomain.Position]
        repeats = synch_description[0][SynchParam.Repeats]
        position = initial + total * repeats
        mot = self.mots[moveable]
        mot.set_base_rate(0)
        mot.set_acceleration(0.1)
        mot.set_velocity(0.5)
        channel_names = self.prepare_meas(config)
        self.pmg.synch_description = synch_description
        self.pmg.set_moveable(moveable, to_fqdn=False)
        repetitions = 0
        for group in synch_description:
            repetitions += group[SynchParam.Repeats]
        self.prepare_attribute_listener()
        self.pmg.prepare()
        self.pmg.start_acquisition()
        mot.set_position(position)
        acq = self.pmg.acquisition
        # waiting for acquisition
        while acq.is_running():
            time.sleep(0.1)
        # time.sleep(3)
        self.acq_asserts(channel_names, repetitions)

    def tearDown(self):
        self.attr_listener = None
        self.pmg = None


synch_description1 = [{SynchParam.Delay: {SynchDomain.Time: 0},
                       SynchParam.Active: {SynchDomain.Time: .01},
                       SynchParam.Total: {SynchDomain.Time: .02},
                       SynchParam.Repeats: 10}]

synch_description2 = [{SynchParam.Delay: {SynchDomain.Time: 0},
                       SynchParam.Active: {SynchDomain.Time: .01},
                       SynchParam.Total: {SynchDomain.Time: .02},
                       SynchParam.Repeats: 100}]

synch_description3 = [{SynchParam.Delay: {SynchDomain.Time: .1},
                       SynchParam.Initial: {SynchDomain.Position: 0},
                       SynchParam.Active: {SynchDomain.Position: .1,
                                         SynchDomain.Time: .01, },
                       SynchParam.Total: {SynchDomain.Position: .2,
                                        SynchDomain.Time: .1},
                       SynchParam.Repeats: 10}]

synch_description4 = [{SynchParam.Delay: {SynchDomain.Time: 0.1},
                       SynchParam.Initial: {SynchDomain.Position: 0},
                       SynchParam.Active: {SynchDomain.Position: -.1,
                                           SynchDomain.Time: .01, },
                       SynchParam.Total: {SynchDomain.Position: -.2,
                                          SynchDomain.Time: .1},
                       SynchParam.Repeats: 10}]

doc_1 = 'Synchronized acquisition with two channels from the same controller'\
        ' using the same trigger'
config_1 = (
    (('_test_ct_1_1', '_test_tg_1_1', AcqSynchType.Trigger),
     ('_test_ct_1_2', '_test_tg_1_1', AcqSynchType.Trigger)),
)

doc_2 = 'Synchronized acquisition with two channels from different controllers'\
        ' using two different triggers'
config_2 = (
    (('_test_ct_1_1', '_test_tg_1_1', AcqSynchType.Trigger),),
    (('_test_ct_2_1', '_test_tg_2_1', AcqSynchType.Trigger),)
)

doc_3 = 'Use the same trigger in 2 channels of different controllers'
config_3 = [[('_test_ct_1_1', '_test_tg_1_1', AcqSynchType.Trigger)],
            [('_test_ct_2_1', '_test_tg_1_1', AcqSynchType.Trigger)]]

doc_4 = 'Acquisition using 2 controllers, with 2 channels in each controller.'
config_4 = [[('_test_ct_1_1', '_test_tg_1_1', AcqSynchType.Trigger),
             ('_test_ct_1_2', '_test_tg_1_1', AcqSynchType.Trigger)],
            [('_test_ct_2_1', '_test_tg_1_2', AcqSynchType.Trigger),
             ('_test_ct_2_2', '_test_tg_1_2', AcqSynchType.Trigger)]]

doc_5 = 'Use a different trigger in 2 channels of the same controller'
config_5 = [[('_test_ct_1_1', '_test_tg_1_1', AcqSynchType.Trigger),
             ('_test_ct_1_2', '_test_tg_2_1', AcqSynchType.Trigger)]]

doc_6 = 'Test using Software Trigger'
config_6 = [[('_test_ct_1_1', 'software', AcqSynchType.Trigger)]]

doc_7 = 'Test using both, a Software Trigger and a "Hardware" Trigger'
config_7 = [[('_test_ct_1_1', '_test_tg_1_1', AcqSynchType.Trigger)],
            [('_test_ct_2_1', 'software', AcqSynchType.Trigger)]]

doc_8 = 'Test that the acquisition using triggers can be stopped.'

doc_11 = 'Acquisition using 2 controllers, with 2 channels in each controller.'
config_11 = [[('_test_ct_1_1', '_test_tg_1_1', AcqSynchType.Trigger),
              ('_test_ct_1_2', '_test_tg_1_1', AcqSynchType.Trigger)],
             [('_test_ct_2_1', 'software', AcqSynchType.Trigger),
              ('_test_ct_2_2', 'software', AcqSynchType.Trigger)]]

doc_9 = 'Test two consecutive synchronous acquisitions with different'\
        ' configuration.'

doc_10 = 'Test synchronous acquisition followed by asynchronous'\
    ' acquisition using the same configuration.'

doc_12 = 'Acquisition using 2 controllers, with 2 channels in each controller.'
config_12 = [[('_test_ct_1_1', 'software', AcqSynchType.Trigger),
              ('_test_ct_1_2', 'software', AcqSynchType.Trigger)],
             [('_test_ct_2_1', 'software', AcqSynchType.Trigger),
              ('_test_ct_2_2', 'software', AcqSynchType.Trigger)]]

doc_13 = 'Test acquisition of zerod using software gate.'
config_13 = [[('_test_ct_1_1', '_test_tg_1_1', AcqSynchType.Trigger), ],
             [('_test_ct_2_1', 'software', AcqSynchType.Trigger), ],
             [('_test_0d_1_1', 'software', AcqSynchType.Gate), ]]

doc_14 = 'Acquisition using 2 controllers, with 2 channels in each '\
         + 'controller, using software and hardware start synchronization'

config_14 = [[('_test_ct_1_1', 'software', AcqSynchType.Start),
              ('_test_ct_1_2', 'software', AcqSynchType.Start)],
             [('_test_ct_2_1', '_test_tg_1_1', AcqSynchType.Start),
              ('_test_ct_2_2', '_test_tg_1_1', AcqSynchType.Start)]]

doc_15 = 'Acquisition using with 1 2D channel using software synchronization'

config_15 = [[('_test_2d_1_1', 'software', AcqSynchType.Trigger)]]


# TODO: listener is not ready to handle 2D
# @insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_15,
#             config=config_15, synch_description=synch_description1)
@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_14,
            config=config_14, synch_description=synch_description1)
@insertTest(helper_name='meas_contpos_acquisition', test_method_doc=doc_12,
            config=config_12, synch_description=synch_description4,
            moveable="_test_mot_1_1")
@insertTest(helper_name='meas_contpos_acquisition', test_method_doc=doc_12,
            config=config_12, synch_description=synch_description3,
            moveable="_test_mot_1_1")
@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_1,
            config=config_1, synch_description=synch_description1)
@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_2,
            config=config_2, synch_description=synch_description1)
@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_3,
            config=config_3, synch_description=synch_description1)
@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_4,
            config=config_4, synch_description=synch_description1)
@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_5,
            config=config_5, synch_description=synch_description1)
# TODO: implement dedicated asserts/test for only software synchronized
#       acquisition.
#       Until this TODO gets implemented we comment the test since it may
#       fail (last acquisitions may not be executed - the previous one could
#       still be in progress, so the shape of data will not correspond to the
#       number of repetitions
# @insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_6,
#             params=params_1, config=config_6)
@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_7,
            config=config_7, synch_description=synch_description1)
@insertTest(helper_name='meas_cont_stop_acquisition', test_method_doc=doc_8,
            config=config_7, synch_description=synch_description2)
@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_9,
            config=config_1, second_config=config_7,
            synch_description=synch_description1)
@insertTest(helper_name='meas_double_acquisition', test_method_doc=doc_10,
            config=config_7, synch_description=synch_description2)
@insertTest(helper_name='meas_double_acquisition', test_method_doc=doc_10,
            config=config_4, synch_description=synch_description1)
@insertTest(helper_name='meas_double_acquisition_samemode', test_method_doc=doc_11,
            config=config_11, synch_description=synch_description2)
@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_9,
            config=config_1, second_config=config_7,
            synch_description=synch_description1)
@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_13,
            config=config_13,
            synch_description=synch_description1)
class AcquisitionTestCase(BasePoolTestCase, BaseAcquisition, unittest.TestCase):
    """Integration test of TGGeneration and Acquisition actions."""

    def setUp(self):
        """
        """
        BasePoolTestCase.setUp(self)
        BaseAcquisition.setUp(self, self.pool)
        unittest.TestCase.setUp(self)

    def tearDown(self):
        BasePoolTestCase.tearDown(self)
        BaseAcquisition.tearDown(self)
        unittest.TestCase.tearDown(self)
