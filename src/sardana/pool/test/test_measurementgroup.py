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

from taurus.external import unittest
from taurus.test import insertTest

from sardana.sardanathreadpool import get_thread_pool
from sardana.pool import AcqTriggerType
from sardana.pool.test import (BasePoolTestCase, createPoolMeasurementGroup,
                               dummyMeasurementGroupConf01,
                               createMGUserConfiguration)
#TODO Import AttributeListener from the right location.
from sardana.pool.test.test_acquisition import AttributeListener
        

params_1 = { "offset":0, 
              "active_period":0.001,
              "passive_period":0.15, 
              "repetitions":100, 
              "integ_time":0.01 
}

doc_1 = 'Synchronized acquisition with two channels from the same controller'\
        ' which use the same trigger'
config_1 = (
    (('_test_ct_1_1', '_test_tg_1_1', AcqTriggerType.Trigger),
     ('_test_ct_1_2', '_test_tg_1_1', AcqTriggerType.Trigger)),  
)
doc_2 = 'Synchronized acquisition with two channels from different controllers'\
        ' uses two different triggers'
config_2 = (
    (('_test_ct_1_1', '_test_tg_1_1', AcqTriggerType.Trigger),),
    (('_test_ct_2_1', '_test_tg_2_1', AcqTriggerType.Trigger),)  
)

@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_1,
            params=params_1, config=config_1)
@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_2,
            params=params_1, config=config_2)
class AcquisitionTestCase(BasePoolTestCase, unittest.TestCase):
    """Integration test of TGGeneration and Acquisition actions."""

    def setUp(self):
        """
        """
        BasePoolTestCase.setUp(self)
        unittest.TestCase.setUp(self)

    def meas_cont_acquisition(self, params, config):
        """Executes measurement using the measurement group. 
        Checks the lengths of the acquired data.
        """    
        offset = params["offset"]
        active_period = params["active_period"]
        passive_period = params["passive_period"] 
        repetitions = params["repetitions"]
        integ_time = params["integ_time"]
    
        jobs_before = get_thread_pool().qsize
        
        pool = self.pool
        
        dummyMeasurementGroupConf01["name"] = 'mg1'
        dummyMeasurementGroupConf01["full_name"] = 'mg1'

        # creating mg user configuration and obtaining channel ids
        (mg_conf, channel_ids) = createMGUserConfiguration(pool, config)
        dummyMeasurementGroupConf01["user_elements"] = channel_ids
        
        pmg = createPoolMeasurementGroup(pool, dummyMeasurementGroupConf01)
        # TODO: it should be possible execute test without the use of actions         
        tgg = pmg.tggeneration        
        # Add mg to pool
        pool.add_element(pmg)
                                
        pmg.set_integration_time(integ_time)

        # setting mg configuration - this cleans the action cache!
        pmg.set_configuration_from_user(mg_conf)        
        # setting parameters to the software tg generator
        tgg._sw_tggenerator.setOffset(offset)
        tgg._sw_tggenerator.setActivePeriod(active_period)
        tgg._sw_tggenerator.setPassivePeriod(passive_period)
        tgg._sw_tggenerator.setRepetitions(repetitions)

        
        for ctrl_links in config:
            for link in ctrl_links:
                channel_name = link[0]
                channel = self.cts[channel_name]
                channel.set_extra_par('nroftriggers', repetitions)
        attr_listener = AttributeListener()        
        ## Add listeners
        attributes = pmg.get_user_elements_attribute_sequence()                
        for attr in attributes:
            attr.add_listener(attr_listener)

        pmg.start_acquisition(continuous=True)
        # retrieving the acquisition since it was cleaned when applying mg conf        
        acq = pmg.acquisition
        # waiting for acquisition and tggeneration to finish        
        while acq.is_running() or tgg.is_running():            
            time.sleep(1)        
        # print the acquisition records
        for i, record in enumerate(zip(*attr_listener.data.values())):
            print i, record
        # checking if any of data was acquired        
        self.assertTrue(attr_listener.data, 'No data were acquired')            
        # checking if all the data were acquired
        for ch, data in attr_listener.data.items():
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
