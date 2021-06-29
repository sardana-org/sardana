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

import copy
import json
import os
import time
import atexit
import threading

# TODO: decide what to use: taurus or PyTango
import PyTango
from PyTango import DeviceProxy
import unittest
from taurus.test import insertTest
from taurus.core.util import CodecFactory
from taurus.core.tango.tangovalidator import TangoDeviceNameValidator

from sardana import sardanacustomsettings
from sardana.pool import AcqSynchType, SynchDomain, SynchParam
from sardana.tango.pool.test import SarTestTestCase

from sardana.pool.test.util import AttributeListener


def _get_full_name(device_proxy, logger=None):
    """Obtain Sardana full name as it is used by the server."""
    db = PyTango.Database()
    if db.get_from_env_var():
        db_name = PyTango.ApiUtil.get_env_var("TANGO_HOST")
    else:
        host = device_proxy.get_db_host()  # this is FQDN
        port = device_proxy.get_db_port()
        db_name = host + ":" + port
    full_name = "//" + db_name + "/" + device_proxy.name()
    full_name, _, _ = TangoDeviceNameValidator().getNames(full_name)
    return full_name


class TangoAttributeListener(AttributeListener):

    def __init__(self, data_key="value"):
        AttributeListener.__init__(self)
        codec_name = getattr(sardanacustomsettings, "VALUE_BUFFER_CODEC")
        self._codec = CodecFactory().getCodec(codec_name)
        self._data_key = data_key

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
            _, _value = self._codec.decode(event.attr_value.value)
            value = _value.get("value") or _value.get("value_ref")
            idx = _value['index']
            dev = event.device
            obj_fullname = _get_full_name(dev)
            # filling the measurement records
            with self.data_lock:
                channel_data = self.data.get(obj_fullname, [])
                expected_idx = len(channel_data)
                pad = [None] * (idx[0] - expected_idx)
                channel_data.extend(pad + value)
                self.data[obj_fullname] = channel_data
        except Exception as e:
            print(e)
            raise Exception('"data" event callback failed')


class MeasSarTestTestCase(SarTestTestCase):
    """ Helper class to setup the need environmet for execute """

    _api_util_cleanup_registered = False

    def setUp(self, pool_properties=None):
        SarTestTestCase.setUp(self, pool_properties)
        self.event_ids = {}
        self.mg_name = '_test_mg_1'
        if not MeasSarTestTestCase._api_util_cleanup_registered:
            # remove whenever PyTango#390 gets fixed
            atexit.register(PyTango.ApiUtil.cleanup)
            MeasSarTestTestCase._api_util_cleanup_registered = True


    def create_meas(self, config):
        """ Create a meas with the given configuration
        """
        # creating mg
        config = copy.deepcopy(config)
        self.expchan_names = []
        self.tg_names = []
        ordered_chns = [None] * 10
        for ctrl_name, ctrl_config in list(config.items()):
            channels = ctrl_config["channels"]
            for chn, chn_config in list(channels.items()):
                index = chn_config["index"]
                ordered_chns[index] = chn
        self.expchan_names = [chn for chn in ordered_chns if chn is not None]
        self.pool.CreateMeasurementGroup([self.mg_name] + self.expchan_names)

        for ctrl_name in list(config.keys()):
            ctrl_config = config.pop(ctrl_name)
            channels = ctrl_config["channels"]
            for chn_name in list(channels.keys()):
                chn_config = channels.pop(chn_name)
                chn_full_name = _get_full_name(DeviceProxy(chn_name))
                channels[chn_full_name] = chn_config
            ctrl_full_name = _get_full_name(DeviceProxy(ctrl_name))
            synchronizer = ctrl_config.get("synchronizer")
            if synchronizer is not None and synchronizer != "software":
                self.tg_names.append(synchronizer)
                synchronizer = _get_full_name(DeviceProxy(synchronizer))
                ctrl_config["synchronizer"] = synchronizer
            config[ctrl_full_name] = ctrl_config

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
            ctrl_config = cfg['controllers'][ctrl]
            ctrl_test_config = config[ctrl]
            channels = ctrl_config['channels']
            channels_test = ctrl_test_config.pop("channels")
            for chn, chn_config in list(channels.items()):
                chn_test_config = channels_test[chn]
                chn_config.update(chn_test_config)
            ctrl_config.update(ctrl_test_config)

        # Write the built configuration
        self.meas.write_attribute('configuration', json.dumps(cfg))

    def prepare_meas(self, params):
        """ Set the measurement group parameters
        """
        synch_description = params["synch_description"]
        codec = CodecFactory().getCodec('json')
        data = codec.encode(('', synch_description))
        self.meas.write_attribute('SynchDescription', data[1])

    def _add_attribute_listener(self, config):
        self.attr_listener = TangoAttributeListener()
        chn_names = []
        for ctrl_config in list(config.values()):
            for chn, chn_config in list(ctrl_config["channels"].items()):
                if chn_config.get("value_ref_enabled", False):
                    buffer_attr = "ValueRefBuffer"
                else:
                    buffer_attr = "ValueBuffer"
                dev = PyTango.DeviceProxy(chn)
                ch_fullname = _get_full_name(dev)
                event_id = dev.subscribe_event(buffer_attr,
                                               PyTango.EventType.CHANGE_EVENT,
                                               self.attr_listener)
                self.event_ids[dev] = event_id
                chn_names.append(ch_fullname)
        return chn_names

    def _acq_asserts(self, channel_names, repetitions):
        """ Do the asserts after an acquisition
        """
        # printing acquisition records
        table = self.attr_listener.get_table()
        header = table.dtype.names
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
        chn_names = self._add_attribute_listener(config)
        # Do acquisition
        self.meas.write_attribute("NbStarts", 1)
        self.meas.Prepare()
        self.meas.Start()
        while self.meas.State() == PyTango.DevState.MOVING:
            print("Acquiring...")
            time.sleep(0.1)
        time.sleep(1)
        repetitions = params['synch_description'][0][SynchParam.Repeats]
        self._acq_asserts(chn_names, repetitions)

    def push_event(self, event):
        value = event.attr_value.value
        self.meas_state = value
        if value == PyTango.DevState.MOVING:
            self.meas_started = True
        elif self.meas_started and value == PyTango.DevState.ON:
            self.meas_finished.set()

    def stop_meas_cont_acquisition(self, params, config):
        '''Helper method to do measurement and stop it'''
        self.create_meas(config)
        self.prepare_meas(params)
        self.meas_state = None
        self.meas_started = False
        self.meas_finished = threading.Event()
        chn_names = self._add_attribute_listener(config)
        # Do measurement
        id_ = self.meas.subscribe_event("State",
                                        PyTango.EventType.CHANGE_EVENT,
                                        self.push_event)
        try:
            # starting timer (0.2 s) which will stop the measurement group
            self.meas.write_attribute("NbStarts", 1)
            self.meas.Prepare()
            self.meas.Start()
            threading.Timer(0.2, self.stopMeas).start()
            self.assertTrue(self.meas_finished.wait(5), "mg has not stopped")
        finally:
            self.meas.unsubscribe_event(id_)
        desired_state = PyTango.DevState.ON
        msg = 'mg state after stop is %s (should be %s)' %\
            (self.meas_state, desired_state)
        self.assertEqual(self.meas_state, desired_state, msg)
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
        for channel, event_id in list(self.event_ids.items()):
            channel.unsubscribe_event(event_id)
        try:
            # Delete the meas
            if os.name != "nt":
                self.pool.DeleteElement(self.mg_name)
        except Exception as e:
            print('Impossible to delete MeasurementGroup: %s' %
                  self.mg_name)
            print(e)
        SarTestTestCase.tearDown(self)


synch_description1 = [{SynchParam.Delay: {SynchDomain.Time: 0},
                     SynchParam.Active: {SynchDomain.Time: .01},
                     SynchParam.Total: {SynchDomain.Time: .02},
                     SynchParam.Repeats: 10}]

params_1 = {
    "synch_description": synch_description1,
    "integ_time": 0.1,
    "name": '_exp_01'
}

synch_description2 = [{SynchParam.Delay: {SynchDomain.Time: 0},
                       SynchParam.Active: {SynchDomain.Time: 0.1},
                       SynchParam.Total: {SynchDomain.Time: 0.15},
                       SynchParam.Repeats: 10}]

params_2 = {
    "synch_description": synch_description2,
    "integ_time": 0.1,
    "name": '_exp_01'
}
doc_1 = 'Synchronized acquisition with two channels from the same controller'\
        ' using hardware trigger'
config_1 = {
    "_test_ct_ctrl_1": {
        "synchronizer": "_test_tg_1_1",
        "synchronization": AcqSynchType.Trigger,
        "channels": {
            "_test_ct_1_1": {
                "index": 0
            },
            "_test_ct_1_2": {
                "index": 1
            }
        }
    }
}

doc_2 = 'Synchronized acquisition with two channels from the same controller'\
        ' using software trigger'
config_2 = {
    "_test_ct_ctrl_1": {
        "synchronizer": "software",
        "synchronization": AcqSynchType.Trigger,
        "channels": {
            "_test_ct_1_1": {
                "index": 0
            },
            "_test_ct_1_2": {
                "index": 1
            }
        }
    }
}
doc_3 = 'Synchronized acquisition with four channels from two different'\
        'controllers using hardware and software triggers'
config_3 = {
    "_test_ct_ctrl_1": {
        "synchronizer": "software",
        "synchronization": AcqSynchType.Trigger,
        "channels": {
            "_test_ct_1_1": {
                "index": 0
            },
            "_test_ct_1_2": {
                "index": 1
            }
        }
    },
    "_test_ct_ctrl_2": {
        "synchronizer": "_test_tg_1_1",
        "synchronization": AcqSynchType.Trigger,
        "channels": {
            "_test_ct_2_1": {
                "index": 2
            },
            "_test_ct_2_2": {
                "index": 3
            }
        }
    },
}
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
            params=params_2, config=config_1)
@insertTest(helper_name='stop_meas_cont_acquisition', test_method_doc=doc_5,
            params=params_2, config=config_2)
@insertTest(helper_name='stop_meas_cont_acquisition', test_method_doc=doc_6,
            params=params_2, config=config_3)
class TangoAcquisitionTestCase(MeasSarTestTestCase, unittest.TestCase):
    """Integration test of TGGeneration and Acquisition actions."""

    pass


config_5 = {
    "_test_2d_ctrl_1": {
        "synchronizer": "_test_tg_1_1",
        "synchronization": AcqSynchType.Trigger,
        "channels": {
            "_test_2d_1_1": {
                "index": 1}
        },
    },
    "_test_roi_ctrl_1": {
        "channels": {
            "_test_roi_q1": {
                "index": 2
            }
        }
    }
}


@insertTest(helper_name='meas_cont_acquisition', test_method_doc="TODO",
            params=params_1, config=config_5)
class TangoAcquisition2DandPCTestCase(MeasSarTestTestCase, unittest.TestCase):

    pseudo_cls_list = (
        list(SarTestTestCase.pseudo_cls_list)
        + [("PseudoCounter", "ROI", "TwoDROI", "_test_roi", "1",
            "2D=_test_2d_1_1", "Q1=_test_roi_q1",)]
    )

    def setUp(self):
        ctrls_test_path = '../../../pool/test/res/controllers'
        source = os.path.join(os.path.dirname(__file__), ctrls_test_path)
        path = os.path.abspath(source)
        pool_properties = {'PoolPath': [path]}
        MeasSarTestTestCase.setUp(self, pool_properties)


config_6 = {
    "_test_2d_ctrl_1": {
        "synchronizer": "_test_tg_1_1",
        "synchronization": AcqSynchType.Trigger,
        "channels": {
            "_test_2d_1_1": {
                "index": 1,
                "value_ref_enabled": True
            }
        },
    },
    "_test_roi_ctrl_1": {
        "channels": {
            "_test_roi_q1": {
                "index": 2
            }
        }
    }
}


@insertTest(helper_name='meas_cont_acquisition', test_method_doc="TODO",
            params=params_1, config=config_6)
class TangoAcquisition2DRefAndPCTestCase(MeasSarTestTestCase,
                                         unittest.TestCase):

    pseudo_cls_list = (
        list(SarTestTestCase.pseudo_cls_list)
        + [("PseudoCounter", "ROI", "TwoDROI", "_test_roi", "1",
            "2D=_test_2d_1_1", "Q1=_test_roi_q1",)]
    )

    def setUp(self):
        ctrls_test_path = '../../../pool/test/res/controllers'
        source = os.path.join(os.path.dirname(__file__), ctrls_test_path)
        path = os.path.abspath(source)
        pool_properties = {'PoolPath': [path]}
        MeasSarTestTestCase.setUp(self, pool_properties)
