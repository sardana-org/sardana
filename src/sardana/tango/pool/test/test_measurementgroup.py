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
            channels = cfg['controllers'][ctrl]['units']['0']['channels']
            for chn in channels:
                name = channels[chn]['name']
                tg_elem, acqType = exp_dict[name]
                tg_dev = taurus.Device(tg_elem)
                tg_elem_full_name = tg_dev.getFullName()
                channels[chn]['trigger_element'] = tg_elem_full_name
                channels[chn]['trigger_type'] = acqType

        # setting measurement parameters
        self.meas.write_attribute('configuration', json.dumps(cfg))
        self.meas.write_attribute('acquisitionmode', params["mode"])
        self.meas.write_attribute('offset', params["offset"])
        self.meas.write_attribute('repetitions', params["repetitions"])
        self.meas.write_attribute('integrationtime', params["integ_time"])

    def meas_cont_acquisition(self, params, config):
        self.prepare_meas(params, config)
        # TODO: substitute it with AttributeListener and asserts
        # Subscribe to events
        cb = PyTango.utils.EventCallBack()
        for ctrl in config:
            for ch_tg in ctrl:
                channel = ch_tg[0]
                channel_dev = PyTango.DeviceProxy(channel)
                channel_dev.subscribe_event('data', 
                                            PyTango.EventType.CHANGE_EVENT, cb)
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


