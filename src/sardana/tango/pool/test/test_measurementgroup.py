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
import json
# TODO: decide what to use: taurus or PyTango
import PyTango
from taurus.external import unittest
from taurus.test import insertTest
from sardana.pool import AcqTriggerType
from sardana.tango.pool.test import SarTestTestCase

# TODO: It will be moved
from sardana.pool.test.test_acquisition import AttributeListener

class TangoAttributeListener(AttributeListener):

    def push_event(self, *args, **kwargs):
        self.event_received(*args, **kwargs)

    def event_received(self, *args, **kwargs):
        try:
            event = args[0]
            if event.err:
                for err in event.errors:
                    if err.reason == 'UnsupportedFeature':
                        # when subscribing for events, Tango does one
                        # readout of the attribute. However the Data
                        # attribute is not fereseen for readout, it is
                        # just the event communication channel.
                        # Ignoring this exception..
                        return
                    else:
                        raise err
            _value = json.loads(event.attr_value.value)
            value = _value['data']
            idx = _value['index']
            dev = event.device
            obj_fullname = '%s:%s/%s' % (dev.get_db_host().split('.')[0], 
                                        dev.get_db_port(),
                                        dev.name())
            # filling the measurement records
            with self.data_lock:
                channel_data = self.data.get(obj_fullname, [])
                expected_idx = len(channel_data)
                pad = [None] * (idx[0]-expected_idx)
                channel_data.extend(pad+value)
                self.data[obj_fullname] = channel_data
        except Exception, e:
            print e
            raise Exception('"data" event callback failed')

class MeasSarTestTestCase(SarTestTestCase):
    """ Helper class to setup the need environmet for execute """

    def setUp(self):
        SarTestTestCase.setUp(self)
        self.event_ids = {}

    def create_meas(self, config):
        """ Create a meas with the given configuration
        """
        # creating mg 
        self.name = '_test_mg_1'
        exp_chns = []
        exp_dict = {}
        for ctrl in config:
            for elem_tuple in ctrl:
                exp_chn, tg_elem, AcqTGType = elem_tuple
                exp_chns.append(exp_chn)
                exp_dict[exp_chn] = (tg_elem, AcqTGType )

        self.pool.CreateMeasurementGroup([self.name] + exp_chns)

        try:
            self.meas = PyTango.DeviceProxy(self.name)
        except:
            raise Exception('Could not create the MeasurementGroup: %s' %\
                                                                   (self.name))

        # When measurement group gets created it fills the configuration with 
        # the default values. Reusing read configuration in order to set test 
        # parameters.
        jcfg = self.meas.read_attribute('configuration').value
        cfg = json.loads(jcfg)
        for ctrl in cfg['controllers']:
            units =  cfg['controllers'][ctrl]['units']['0']
            channels = units['channels']
            for chn in channels:
                name = channels[chn]['name']
                tg_elem, acqType = exp_dict[name]
                tg_dev = PyTango.DeviceProxy(tg_elem)
                tg_fullname = '%s:%s/%s' % (tg_dev.get_db_host().split('.')[0], 
                                            tg_dev.get_db_port(),
                                            tg_dev.name())
                channels[chn]['trigger_element'] = tg_fullname
                channels[chn]['trigger_type'] = acqType
                units['trigger_type'] = acqType

        # Write the built configuration
        self.meas.write_attribute('configuration', json.dumps(cfg))

    def prepare_meas(self, params):
        """ Set the measurement group parameters
        """
        self.meas.write_attribute('acquisitionmode', params["mode"])
        self.meas.write_attribute('offset', params["offset"])
        self.meas.write_attribute('repetitions', params["repetitions"])
        self.meas.write_attribute('integrationtime', params["integ_time"])

    def _add_attribute_listener(self, config):
        # Subscribe to events
        chn_names = []
        for ctrl in config:
            for ch_tg in ctrl:
                channel = ch_tg[0]
                dev = PyTango.DeviceProxy(channel)
                ch_fullname = '%s:%s/%s' % (dev.get_db_host().split('.')[0], 
                                            dev.get_db_port(),
                                            dev.name())
                event_id = dev.subscribe_event('Data', 
                                               PyTango.EventType.CHANGE_EVENT, 
                                               self.attr_listener)
                self.event_ids[dev] = event_id
                chn_names.append(ch_fullname)
        return chn_names

    def tearDown(self):
        for channel, event_id in self.event_ids.items():
            channel.unsubscribe_event(event_id)
        try:
            # Delete the meas
            self.pool.DeleteElement(self.name)
        except:
            print('Impossible to delete MeasurementGroup: %s' % (self.name))
        SarTestTestCase.tearDown(self)

params_1 = {
    "offset": 0,
    "repetitions": 100,
    "integ_time": 0.01,
    "name": '_exp_01',
    "mode": "ContTimer"
}
doc_1 = 'Synchronized acquisition with two channels from the same controller'\
        ' using the same trigger'
config_1 = (
    (('_test_ct_1_1', '_test_tg_1_1', AcqTriggerType.Trigger),
     ('_test_ct_1_2', '_test_tg_1_1', AcqTriggerType.Trigger)),
)

doc_2 = 'Synchronized acquisition with two channels from the same controller'\
        ' using the software trigger'
config_2 = (
    (('_test_ct_1_1', '_test_stg_1_1', AcqTriggerType.Trigger),
     ('_test_ct_1_2', '_test_stg_1_1', AcqTriggerType.Trigger)),
)

doc_3 = 'Synchronized acquisition with two channels from the same controller'\
        ' using the software trigger'
config_3 = (
    (('_test_ct_1_1', '_test_stg_1_1', AcqTriggerType.Trigger),
     ('_test_ct_1_2', '_test_stg_1_1', AcqTriggerType.Trigger)),
    (('_test_ct_2_1', '_test_tg_1_1', AcqTriggerType.Trigger),
     ('_test_ct_2_2', '_test_tg_1_1', AcqTriggerType.Trigger)),
)

@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_1,
            params=params_1, config=config_1)
@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_2,
            params=params_1, config=config_2)
@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_3,
            params=params_1, config=config_3)
class TangoAcquisitionTestCase(MeasSarTestTestCase, unittest.TestCase):
    """Integration test of TGGeneration and Acquisition actions."""

    def setUp(self):
        MeasSarTestTestCase.setUp(self)
        unittest.TestCase.setUp(self)

    def _acq_asserts(self, channel_names, repetitions):
        """ Do the asserts after an acquisition
        """
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

    def meas_cont_acquisition(self, params, config):
        """ Helper method to do a continous acquisition
        """
        self.create_meas(config)
        self.prepare_meas(params)
        self.attr_listener = TangoAttributeListener()
        chn_names = self._add_attribute_listener(config)
        # Do acquisition
        self.meas.Start()
        while self.meas.State() == PyTango.DevState.MOVING:
            print "Acquiring..."
            time.sleep(0.1)
        self._acq_asserts(chn_names, params["repetitions"])

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        MeasSarTestTestCase.tearDown(self)
