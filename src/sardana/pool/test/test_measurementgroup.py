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
import threading
import copy

from taurus.external import unittest
from taurus.test import insertTest

from sardana.sardanathreadpool import get_thread_pool
from sardana.pool import AcqTriggerType, AcqMode
from sardana.pool.test import (BasePoolTestCase, createPoolMeasurementGroup,
                               dummyMeasurementGroupConf01,
                               createMGUserConfiguration)
#TODO Import AttributeListener from the right location.
from sardana.pool.test.test_acquisition import AttributeListener

class BaseAcquisition(object):
    def setUp(self, pool):
        """
        """
        self.pool = pool
        self.pmg = None
        self.attr_listener = None

    def prepare_meas(self, params, config):
        """ Prepare the meas and returns the channel names
        """
        pool = self.pool
        
        # creating mg user configuration and obtaining channel ids
        mg_conf, channel_ids, channel_names = \
                                        createMGUserConfiguration(pool, config)
        conf = copy.deepcopy(dummyMeasurementGroupConf01)        
        conf["name"] = 'mg1'
        conf["full_name"] = 'mg1'
        conf["user_elements"] = channel_ids
        self.pmg = createPoolMeasurementGroup(pool, conf)
        # Add mg to pool
        pool.add_element(self.pmg)
        # setting measurement parameters
        self.pmg.set_acquisition_mode(AcqMode.ContTimer)
        self.pmg.set_offset(params["offset"])
        self.pmg.set_repetitions(params["repetitions"])
        self.pmg.set_integration_time(params["integ_time"])
        # setting measurement configuration - this cleans the action cache!
        self.pmg.set_configuration_from_user(mg_conf) 

        return channel_names

    def prepare_attribute_listener(self):
        self.attr_listener = AttributeListener()        
        ## Add listeners
        attributes = self.pmg.get_user_elements_attribute_sequence()                
        for attr in attributes:
            attr.add_listener(self.attr_listener)

    def remove_attribute_listener(self):
        ## Remove listeners
        attributes = self.pmg.get_user_elements_attribute_sequence()                
        for attr in attributes:
            attr.remove_listener(self.attr_listener)

    def acquire(self, mode):
        """ Run a cont acquisition + asserts
        """
        self.pmg.set_acquisition_mode(mode)
        self.pmg.start_acquisition()   
        acq = self.pmg.acquisition
        # waiting for acquisition 
        while acq.is_running():            
            time.sleep(1)  

    def acq_asserts(self, channel_names, repetitions):
        # printing acquisition records
        table = self.attr_listener.get_table()
        header = table.dtype.names
        print header        
        n_rows = table.shape[0]
        for row in xrange(n_rows):
            print row, table[row]        
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

    def meas_double_acquisition(self, params, config):
        """ Run two acquisition with the same meas in two different mode: 
             - ContTimer
             - Timer
        """ 
        # AcqMode.ContTimer
        channel_names = self.prepare_meas(params, config)     
        repetitions = params["repetitions"]
        self.prepare_attribute_listener()
        self.acquire(AcqMode.ContTimer)
        self.acq_asserts(channel_names, repetitions)
        self.remove_attribute_listener()
        self.acquire(AcqMode.Timer)
        # TODO: implement asserts of Timer acquisition

    def meas_double_acquisition_samemode(self, params, config):
        """ Run two acquisition with the same meas in two different mode: 
             - ContTimer
             - Timer
        """ 
        # AcqMode.ContTimer
        channel_names = self.prepare_meas(params, config)     
        repetitions = params["repetitions"]
        self.prepare_attribute_listener()
        self.acquire(AcqMode.ContTimer)
        self.acq_asserts(channel_names, repetitions)
        self.remove_attribute_listener()
        self.prepare_attribute_listener()
        self.acquire(AcqMode.ContTimer)
        self.acq_asserts(channel_names, repetitions)
        self.remove_attribute_listener()
        # TODO: implement asserts of Timer acquisition

    def consecutive_acquisitions(self, pool, params, second_config):
        # creating mg user configuration and obtaining channel ids
        mg_conf, channel_ids, channel_names = createMGUserConfiguration(pool, second_config)

        # setting mg configuration - this cleans the action cache!
        self.pmg.set_configuration_from_user(mg_conf)        
        repetitions = params["repetitions"]
        self.prepare_attribute_listener()
        self.acquire(AcqMode.ContTimer)
        self.acq_asserts(channel_names, repetitions)

    def meas_cont_acquisition(self, params, config, second_config=None):
        """Executes measurement using the measurement group. 
        Checks the lengths of the acquired data.
        """
        jobs_before = get_thread_pool().qsize
        channel_names = self.prepare_meas(params, config)     
        repetitions = params["repetitions"] 
        self.prepare_attribute_listener()  
        self.acquire(AcqMode.ContTimer)
        self.acq_asserts(channel_names, repetitions)     

        if second_config is not None:
            self.consecutive_acquisitions(self.pool, params, second_config)

        # checking if there are no pending jobs
        jobs_after = get_thread_pool().qsize
        msg = ('there are %d jobs pending to be done after the acquisition ' +
                               '(before: %d)') % (jobs_after, jobs_before)
        self.assertEqual(jobs_before, jobs_after, msg)                

    def stopAcquisition(self):
        """Method used to abort a running acquisition"""
        self.pmg.stop()

    def meas_cont_stop_acquisition(self, params, config):
        """Executes measurement using the measurement group and tests that the 
        acquisition can be stopped.
        """  
        self.prepare_meas(params, config)     
        self.prepare_attribute_listener()
        
        self.pmg.start_acquisition()
        # retrieving the acquisition since it was cleaned when applying mg conf        
        acq = self.pmg.acquisition
        
        # starting timer (0.05 s) which will stop the acquisiton
        threading.Timer(0.2, self.stopAcquisition).start() 
        # waiting for acquisition and tggeneration to be stoped by thread 
        while acq.is_running():
            time.sleep(0.05)
        msg = "acquisition shall NOT be running after stopping it"
        self.assertEqual(acq.is_running(), False, msg) 

        tp = get_thread_pool()
        numBW= tp.getNumOfBusyWorkers()
        msg = "The number of busy workers is not zero; numBW = %s" % (numBW)
        self.assertEqual(numBW, 0, msg)
        # print the acquisition records
        for i, record in enumerate(zip(*self.attr_listener.data.values())):
            print i, record

    def tearDown(self):
        self.attr_listener = None
        self.pmg = None

params_1 = {"offset":0,                
            "repetitions":10, 
            "integ_time":0.01 
}

params_2 = {"offset":0, 
            "repetitions":100, 
            "integ_time":0.01 
}

doc_1 = 'Synchronized acquisition with two channels from the same controller'\
        ' using the same trigger'
config_1 = (
    (('_test_ct_1_1', '_test_tg_1_1', AcqTriggerType.Trigger),
     ('_test_ct_1_2', '_test_tg_1_1', AcqTriggerType.Trigger)),  
)

doc_2 = 'Synchronized acquisition with two channels from different controllers'\
        ' using two different triggers'
config_2 = (
    (('_test_ct_1_1', '_test_tg_1_1', AcqTriggerType.Trigger),),
    (('_test_ct_2_1', '_test_tg_2_1', AcqTriggerType.Trigger),)  
)

doc_3 = 'Use the same trigger in 2 channels of different controllers'
config_3 = [[('_test_ct_1_1', '_test_tg_1_1', AcqTriggerType.Trigger)],
            [('_test_ct_2_1', '_test_tg_1_1', AcqTriggerType.Trigger)]]

doc_4 = 'Acquisition using 2 controllers, with 2 channels in each controller.'
config_4 = [[('_test_ct_1_1', '_test_tg_1_1', AcqTriggerType.Trigger),
             ('_test_ct_1_2', '_test_tg_1_1', AcqTriggerType.Trigger)],
            [('_test_ct_2_1', '_test_tg_1_2', AcqTriggerType.Trigger),
             ('_test_ct_2_2', '_test_tg_1_2', AcqTriggerType.Trigger)]]

doc_5 = 'Use a different trigger in 2 channels of the same controller'
config_5 = [[('_test_ct_1_1', '_test_tg_1_1', AcqTriggerType.Trigger),
             ('_test_ct_1_2', '_test_tg_2_1', AcqTriggerType.Trigger)]]

doc_6 = 'Test using Software Trigger'
config_6 = [[('_test_ct_1_1', '_test_stg_1_1', AcqTriggerType.Trigger)]]

doc_7 = 'Test using both, a Software Trigger and a "Hardware" Trigger'
config_7 = [[('_test_ct_1_1', '_test_tg_1_1', AcqTriggerType.Trigger)],
            [('_test_ct_2_1', '_test_stg_1_1', AcqTriggerType.Trigger)]]

doc_8 = 'Test that the acquisition using triggers can be stopped.'
config_8 = [[('_test_ct_1_1', '_test_tg_1_1', AcqTriggerType.Trigger),
             ('_test_ct_1_2', '_test_stg_1_1', AcqTriggerType.Trigger)]] 


doc_11 = 'Acquisition using 2 controllers, with 2 channels in each controller.'
config_11 = [[('_test_ct_1_1', '_test_tg_1_1', AcqTriggerType.Trigger),
             ('_test_ct_1_2', '_test_tg_1_1', AcqTriggerType.Trigger)],
            [('_test_ct_2_1', '_test_stg_1_1', AcqTriggerType.Trigger),
             ('_test_ct_2_2', '_test_stg_1_1', AcqTriggerType.Trigger)]] 

doc_9 = 'Test two consecutive synchronous acquisitions with different'\
        ' configuration.'

doc_10 = 'Test synchronous acquisition followed by asynchronous'\
        ' acquisition using the same configuration.'

@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_1,
            params=params_1, config=config_1)
@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_2,
            params=params_1, config=config_2)
@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_3,
            params=params_1, config=config_3)
@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_4,
            params=params_1, config=config_4)
@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_5,
            params=params_1, config=config_5)
@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_6,
            params=params_1, config=config_6)
@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_7,
            params=params_1, config=config_7)
@insertTest(helper_name='meas_cont_stop_acquisition', test_method_doc=doc_8,
            params=params_2, config=config_8) 
@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_9,
            params=params_1, config=config_1, second_config=config_7)
@insertTest(helper_name='meas_double_acquisition', test_method_doc=doc_10,
            params=params_2, config=config_8)
@insertTest(helper_name='meas_double_acquisition', test_method_doc=doc_10,
            params=params_1, config=config_4)
@insertTest(helper_name='meas_double_acquisition_samemode', test_method_doc=doc_11,
            params=params_2, config=config_11)
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
