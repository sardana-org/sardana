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
import taurus
from taurus.external import unittest
from taurus.test import insertTest
from sardana.pool import AcqTriggerType
from sardana.tango.pool.test import SarTestTestCase

# TODO: It will be moved
from sardana.pool.test.test_acquisition import AttributeListener
from taurus.core import TaurusEventType

class TangoAttributeListener(AttributeListener):

    def eventReceived(self, *args, **kwargs):
        self.event_received(*args, **kwargs)

    def event_received(self, *args, **kwargs):
        try:
            event_src, event_type, event_value = args
            if event_type == TaurusEventType.Error:
                for err in event_value:
                    if err.reason == 'UnsupportedFeature':
                        # when subscribing for events, Tango does one
                        # readout of the attribute. However the Data
                        # attribute is not fereseen for readout, it is
                        # just the event communication channel.
                        # Ignoring this exception..
                        pass
                    else:
                        raise err
            elif event_type == TaurusEventType.Change:
                _value = json.loads(event_value.value)
                # TODO _value will be  a dictionary
                # value = _value['data']
                # idx = _value['index']
                obj_name = event_src.getParentObj().getFullName()
                # TODO remove the simulation
                value = _value
                index = len(self.data.get(obj_name, []))
                idx = [i for i in range(index, len(value)+index)]
                # filling the measurement records
                with self.data_lock:
                    channel_data = self.data.get(obj_name, [])
                    expected_idx = len(channel_data)
                    pad = [None] * (idx[0]-expected_idx)
                    channel_data.extend(pad+value)
                    self.data[obj_name] = channel_data
        except Exception, e:
            raise Exception('"data" event callback failed')

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

@insertTest(helper_name='meas_cont_acquisition', test_method_doc=doc_1,
            params=params_1, config=config_1)
class TangoAcquisitionTestCase(SarTestTestCase, unittest.TestCase):
    """Integration test of TGGeneration and Acquisition actions."""

    def setUp(self):
        SarTestTestCase.setUp(self)
        unittest.TestCase.setUp(self)

    def prepare_meas(self, params, config):
        """ Prepare the meas and returns the channel names
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
                tg_dev = taurus.Device(tg_elem)
                tg_elem_full_name = tg_dev.getFullName()
                channels[chn]['trigger_element'] = tg_elem_full_name
                channels[chn]['trigger_type'] = acqType
                units['trigger_type'] = acqType

        # setting measurement parameters
        self.meas.write_attribute('configuration', json.dumps(cfg))
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
                attr_data = taurus.Attribute(channel+'/data')
                ch_fullname = attr_data.getParent().getFullName()
                chn_names.append(ch_fullname)
                attr_data.addListener(self.attr_listener)
        return chn_names

    def meas_cont_acquisition(self, params, config):
        self.prepare_meas(params, config)
        self.attr_listener = TangoAttributeListener()
        chn_names = self._add_attribute_listener(config)
        # Do acquisition
        self.meas.Start()
        while self.meas.State() == PyTango.DevState.MOVING:
            print "Acquiring..."
            time.sleep(0.1)

    def tearDown(self):
        try:
            # Delete the meas
            self.pool.DeleteElement(self.name)
        except:
            print('Impossible to delete MeasurementGroup: %s' % (self.name))
        unittest.TestCase.tearDown(self)
        SarTestTestCase.tearDown(self)


