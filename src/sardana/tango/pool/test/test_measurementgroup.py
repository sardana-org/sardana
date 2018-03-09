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
import json
# TODO: decide what to use: taurus or PyTango
import PyTango
from taurus.external import unittest
from taurus.test import insertTest
from taurus.core.util import CodecFactory
from sardana.pool import AcqSynchType, SynchDomain, SynchParam
from sardana.tango.pool.test import SarTestTestCase

# TODO: It will be moved
from sardana.pool.test.test_acquisition import AttributeListener


def _to_fqdn(name, logger=None):
    full_name = name
    # try to use Taurus 4 to retrieve FQDN
    try:
        from taurus.core.tango.tangovalidator import TangoDeviceNameValidator
        full_name, _, _ = TangoDeviceNameValidator().getNames(name)
    # if Taurus3 in use just continue
    except ImportError:
        pass
    if full_name != name and logger:
        msg = ("PQDN full name is deprecated in favor of FQDN full name."
               " Re-apply configuration in order to upgrade.")
        logger.warning(msg)
    return full_name


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
            obj_fullname = '%s:%s/%s' % (dev.get_db_host(),
                                         dev.get_db_port(),
                                         dev.name())
            obj_fullname = _to_fqdn(obj_fullname)
            # filling the measurement records
            with self.data_lock:
                channel_data = self.data.get(obj_fullname, [])
                expected_idx = len(channel_data)
                pad = [None] * (idx[0] - expected_idx)
                channel_data.extend(pad + value)
                self.data[obj_fullname] = channel_data
        except Exception, e:
            print e
            raise Exception('"data" event callback failed')


class MeasSarTestTestCase(SarTestTestCase):
    """ Helper class to setup the need environmet for execute """

    def setUp(self):
        SarTestTestCase.setUp(self)
        self.event_ids = {}
        self.mg_name = '_test_mg_1'

    def create_meas(self, config):
        """ Create a meas with the given configuration
        """
        # creating mg
        self.expchan_names = []
        self.tg_names = []
        exp_dict = {}
        for ctrl in config:
            for elem_tuple in ctrl:
                exp_chn, synchronizer, synchronization = elem_tuple
                self.expchan_names.append(exp_chn)
                exp_dict[exp_chn] = (synchronizer, synchronization)

        self.pool.CreateMeasurementGroup([self.mg_name] + self.expchan_names)

        try:
            self.meas = PyTango.DeviceProxy(self.mg_name)
        except:
            raise Exception('Could not create the MeasurementGroup: %s' %
                            (self.mg_name))

        # When measurement group gets created it fills the configuration with
        # the default values. Reusing read configuration in order to set test
        # parameters.
        jcfg = self.meas.read_attribute('configuration').value
        cfg = json.loads(jcfg)
        for ctrl in cfg['controllers']:
            ctrl_data = cfg['controllers'][ctrl]
            channels = ctrl_data['channels']
            for chn in channels:
                name = channels[chn]['name']
                synchronizer, synchronization = exp_dict[name]
                if synchronizer != 'software':
                    synchronizer_dev = PyTango.DeviceProxy(synchronizer)
                    synchronizer = '%s:%s/%s' % (
                        synchronizer_dev.get_db_host(),
                        synchronizer_dev.get_db_port(),
                        synchronizer_dev.name())
                    synchronizer = _to_fqdn(synchronizer)
                ctrl_data['synchronizer'] = synchronizer
                ctrl_data['synchronization'] = synchronization
                self.tg_names.append(synchronizer)

        # Write the built configuration
        self.meas.write_attribute('configuration', json.dumps(cfg))

    def prepare_meas(self, params):
        """ Set the measurement group parameters
        """
        synchronization = params["synchronization"]
        codec = CodecFactory().getCodec('json')
        data = codec.encode(('', synchronization))
        self.meas.write_attribute('synchronization', data[1])

    def _add_attribute_listener(self, config):
        # Subscribe to events
        chn_names = []
        for ctrl in config:
            for ch_tg in ctrl:
                channel = ch_tg[0]
                dev = PyTango.DeviceProxy(channel)
                ch_fullname = '%s:%s/%s' % (dev.get_db_host(),
                                            dev.get_db_port(),
                                            dev.name())
                ch_fullname = _to_fqdn(ch_fullname)
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
            self.pool.DeleteElement(self.mg_name)
        except Exception, e:
            print('Impossible to delete MeasurementGroup: %s' % (self.mg_name))
            print e
        SarTestTestCase.tearDown(self)

synchronization1 = [{SynchParam.Delay: {SynchDomain.Time: 0},
                     SynchParam.Active: {SynchDomain.Time: .01},
                     SynchParam.Total: {SynchDomain.Time: .02},
                     SynchParam.Repeats: 10}]

params_1 = {
    "synchronization": synchronization1,
    "integ_time": 0.01,
    "name": '_exp_01'
}
doc_1 = 'Synchronized acquisition with two channels from the same controller'\
        ' using hardware trigger'
config_1 = (
    (('_test_ct_1_1', '_test_tg_1_1', AcqSynchType.Trigger),
     ('_test_ct_1_2', '_test_tg_1_1', AcqSynchType.Trigger)),
)
doc_2 = 'Synchronized acquisition with two channels from the same controller'\
        ' using software trigger'
config_2 = (
    (('_test_ct_1_1', 'software', AcqSynchType.Trigger),
     ('_test_ct_1_2', 'software', AcqSynchType.Trigger)),
)
doc_3 = 'Synchronized acquisition with four channels from two different'\
        'controllers using hardware and software triggers'
config_3 = (
    (('_test_ct_1_1', 'software', AcqSynchType.Trigger),
     ('_test_ct_1_2', 'software', AcqSynchType.Trigger)),
    (('_test_ct_2_1', '_test_tg_1_1', AcqSynchType.Trigger),
     ('_test_ct_2_2', '_test_tg_1_1', AcqSynchType.Trigger)),
)
doc_4 = 'Stop of the synchronized acquisition with two channels from the same'\
        ' controller using hardware trigger'
doc_5 = 'Stop of the synchronized acquisition with two channels from the same'\
        ' controller using software trigger'
doc_6 = 'Stop of the synchronized acquisition with four channels from two'\
        ' different controllers using hardware and software triggers'


@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_1,
            params=params_1, config=config_1)
# TODO: implement dedicated asserts/test for only software synchronized
#       acquisition.
#       Until this TODO gets implemented we comment the test since it may
#       fail (last acquisitions may not be executed - the previous one could
#       still be in progress, so the shape of data will not correspond to the
#       number of repetitions
# @insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_2,
#             params=params_1, config=config_2)
@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_3,
            params=params_1, config=config_3)
@insertTest(helper_name='stop_meas_cont_acquisition', test_method_doc=doc_4,
            params=params_1, config=config_1)
@insertTest(helper_name='stop_meas_cont_acquisition', test_method_doc=doc_5,
            params=params_1, config=config_2)
@insertTest(helper_name='stop_meas_cont_acquisition', test_method_doc=doc_6,
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
        repetitions = params['synchronization'][0][SynchParam.Repeats]
        self._acq_asserts(chn_names, repetitions)

    def stop_meas_cont_acquisition(self, params, config):
        '''Helper method to do measurement and stop it'''
        self.create_meas(config)
        self.prepare_meas(params)
        self.attr_listener = TangoAttributeListener()
        chn_names = self._add_attribute_listener(config)
        # Do measurement
        self.meas.Start()
        # starting timer (0.2 s) which will stop the measurement group
        threading.Timer(0.2, self.stopMeas).start()
        while self.meas.State() == PyTango.DevState.MOVING:
            print "Acquiring..."
            time.sleep(0.1)
        state = self.meas.State()
        desired_state = PyTango.DevState.ON
        msg = 'mg state after stop is %s (should be %s)' %\
            (state, desired_state)
        self.assertEqual(state, desired_state, msg)
        for name in chn_names:
            channel = PyTango.DeviceProxy(name)
            state = channel.state()
            msg = 'channel %s state after stop is %s (should be %s)' %\
                (name, state, desired_state)
            self.assertEqual(state, desired_state, msg)

    def stopMeas(self):
        '''Method used to stop measreument group'''
        self.meas.stop()

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        MeasSarTestTestCase.tearDown(self)
