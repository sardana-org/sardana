#!/usr/bin/env python

##############################################################################
##
# This file is part of Sardana
##
# http://www.sardana-controls.org/
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

"""Tests for continuous scans (ct-like)"""
import time
import PyTango
import unittest
from sardana.macroserver.macros.test import (RunStopMacroTestCase, testRun,
                                             testStop)
from sardana.pool import AcqSynchType
# TODO: MeasSarTestTestCase is a util, could be moved to base_sartest
# or another utils module.
from sardana.tango.pool.test.test_measurementgroup import MeasSarTestTestCase
from sardana.tango.macroserver.test import BaseMacroServerTestCase


class UtilsForTests():

    def parsingOutputPoints(self, log_output):
        """A helper method to know if points are ordered based on log_output.
        """
        first_data_line = 1
        scan_index = 0
        list_points = []
        for line, in log_output[first_data_line:]:
            # Get a list of elements without white spaces between them
            columns = line.split()

            # Cast index of scan to int (the first element of the list)
            columns[scan_index] = int(columns[scan_index])
            list_points.append(columns[scan_index])
        nb_points = len(list_points)

        ordered_points = 0
        for i in range(len(list_points) - 1):
            if list_points[i + 1] >= list_points[i]:
                ordered_points = 1
            else:
                ordered_points = 0
                break

        return (nb_points, ordered_points)

    def orderPointsData(self, data):
        """A helper method to know if points are ordered based on getData.
        """
        obtained_nb_points_data = len(list(data.keys()))
        ordered_points_data = 0
        for i in range(obtained_nb_points_data - 1):
            if int(list(data.keys())[i + 1]) >= int(list(data.keys())[i]):
                ordered_points_data = 1
            else:
                ordered_points_data = 0
                break
        return ordered_points_data


class ScanctTest(MeasSarTestTestCase, BaseMacroServerTestCase,
                 RunStopMacroTestCase):
    """Base class for the continuous scans (ct-like) tests. Implements
    methods for preparation of the elements and validation of the results.
    """

    utils = UtilsForTests()

    def setUp(self):
        MeasSarTestTestCase.setUp(self)
        properties = {'PoolNames': self.pool_name}
        BaseMacroServerTestCase.setUp(self, properties)
        RunStopMacroTestCase.setUp(self)

    def configure_motors(self, motor_names):
        # TODO: workaround for bug with velocity<base_rate: Sdn#38
        for name in motor_names:
            mot = PyTango.DeviceProxy(name)
            mot.write_attribute('acceleration', 0.1)
            mot.write_attribute('base_rate', 0)
            mot.write_attribute('deceleration', 0.1)

    def configure_mntgrp(self, meas_config):
        # creating MEAS
        self.create_meas(meas_config)
        # Set ActiveMntGrp
        self.macro_executor.run(macro_name='senv',
                                macro_params=['ActiveMntGrp', '_test_mg_1'],
                                sync=True, timeout=1.)

    def check_using_output(self, expected_nb_points):
        # Test data from log_output
        log_output = self.macro_executor.getLog('output')
        (aa, bb) = self.utils.parsingOutputPoints(log_output)
        # ordered_points: (int) obtained number of points.
        obtained_nb_points = aa
        # ordered_points: booleand which indicates if points are ordered.
        ordered_points = bb

        msg = ("The ascanct execution did not return any scan point.\n"
               "Checked using macro output")
        self.assertNotEqual(obtained_nb_points, 0, msg)

        msg = ("The ascanct execution did not return the expected number of "
               "points.\nExpected " + str(expected_nb_points) + " points."
               "\nObtained " + str(obtained_nb_points) + " points."
               "Checked using macro output")
        self.assertEqual(obtained_nb_points, expected_nb_points, msg)

        msg = "Scan points are NOT in good order.\nChecked using macro output"
        self.assertTrue(ordered_points, msg)

    def check_using_data(self, expected_nb_points):
        # Test data from macro (macro_executor.getData())
        data = self.macro_executor.getData()
        order_points_data = self.utils.orderPointsData(data)
        obtained_nb_points_data = len(list(data.keys()))

        msg = ("The ascanct execution did not return any scan point.\n"
               "Checked using macro data.")
        self.assertTrue(len(list(data.keys())) > 0, msg)

        msg = ("The ascanct execution did not return the expected number of "
               "points.\nExpected " + str(expected_nb_points) + " points."
               "\nObtained " + str(obtained_nb_points_data) + " points."
               "\nChecked using macro data.")
        self.assertEqual(obtained_nb_points_data, expected_nb_points, msg)

        msg = ("Scan points are NOT in good order."
               "\nChecked using macro data.")
        self.assertTrue(order_points_data, msg)

    def check_stopped(self):
        self.assertStopped('Macro %s did not stop' % self.macro_name)
        for name in self.expchan_names + self.tg_names:
            channel = PyTango.DeviceProxy(name)
            desired_state = PyTango.DevState.ON
            state = channel.state()
            msg = 'element %s state after stop is %s (should be %s)' % \
                  (name, state, desired_state)
            self.assertEqual(state, desired_state, msg)

    def tearDown(self):
        RunStopMacroTestCase.tearDown(self)
        BaseMacroServerTestCase.tearDown(self)
        MeasSarTestTestCase.tearDown(self)


mg_config1 = {
    "_test_ct_ctrl_1": {
        "synchronizer": "_test_tg_1_1",
        "synchronization": AcqSynchType.Trigger,
        "channels": {
            "_test_ct_1_1": {
                "index": 0
            },
        }
    },
}
mg_config2 = {
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
    },
}
mg_config3 = {
    "_test_ct_ctrl_1": {
        "synchronizer": "software",
        "synchronization": AcqSynchType.Trigger,
        "channels": {
            "_test_ct_1_1": {
                "index": 0
            },
        }
    },
    "_test_ct_ctrl_2": {
        "synchronizer": "_test_tg_1_1",
        "synchronization": AcqSynchType.Trigger,
        "channels": {
            "_test_ct_2_1": {
                "index": 1
            },
        }
    }
}
mg_config4 = {
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
ascanct_params_1 = ['_test_mt_1_1', '0', '10', '100', '0.1']


@testRun(meas_config=mg_config1, macro_params=ascanct_params_1,
         wait_timeout=30)
@testRun(meas_config=mg_config2, macro_params=ascanct_params_1,
         wait_timeout=30)
@testRun(meas_config=mg_config3, macro_params=ascanct_params_1,
         wait_timeout=30)
@testRun(meas_config=mg_config4, macro_params=ascanct_params_1,
         wait_timeout=30)
@testStop(meas_config=mg_config1, macro_params=ascanct_params_1,
          stop_delay=5, wait_timeout=20)
class AscanctTest(ScanctTest, unittest.TestCase):
    """Checks that ascanct works and generates the exact number of records
    by parsing the door output.

    .. todo:: check the macro data instead of the door output
    """
    macro_name = 'ascanct'

    def setUp(self):
        unittest.TestCase.setUp(self)
        ScanctTest.setUp(self)

    def macro_runs(self, meas_config, macro_params, wait_timeout=None):
        motors = [macro_params[0]]
        ScanctTest.configure_motors(self, motors)
        ScanctTest.configure_mntgrp(self, meas_config)
        # Run the ascanct
        self.macro_executor.run(macro_name=self.macro_name,
                                macro_params=macro_params,
                                sync=True, timeout=wait_timeout)
        self.assertFinished('Macro %s did not finish' % self.macro_name)

        expected_nb_points = int(macro_params[3]) + 1
        ScanctTest.check_using_output(self, expected_nb_points)
        ScanctTest.check_using_data(self, expected_nb_points)

    def macro_stops(self, meas_config, macro_params, wait_timeout=None,
                    stop_delay=0.1):
        motors = [macro_params[0]]
        ScanctTest.configure_motors(self, motors)
        ScanctTest.configure_mntgrp(self, meas_config)
        # Run the ascanct
        self.macro_executor.run(macro_name=self.macro_name,
                                macro_params=macro_params,
                                sync=False, timeout=wait_timeout)
        if stop_delay is not None:
            time.sleep(stop_delay)
        self.macro_executor.stop()
        self.macro_executor.wait(timeout=wait_timeout)
        ScanctTest.check_stopped(self)

    def tearDown(self):
        ScanctTest.tearDown(self)
        unittest.TestCase.tearDown(self)


a2scanct_params_1 = ['_test_mt_1_1', '0', '10', '_test_mt_1_2', '0', '20',
                     '100', '0.1']


@testRun(meas_config=mg_config1, macro_params=a2scanct_params_1,
         wait_timeout=30)
class A2scanctTest(ScanctTest, unittest.TestCase):
    """Checks that a2scanct works and generates the exact number of records
    by parsing the door output.

    .. todo:: check the macro data instead of the door output
    """
    macro_name = 'a2scanct'
    MOT1 = 0
    MOT2 = 3

    def setUp(self):
        unittest.TestCase.setUp(self)
        ScanctTest.setUp(self)

    def macro_runs(self, meas_config, macro_params, wait_timeout=None):
        motors = [macro_params[self.MOT1], macro_params[self.MOT2]]
        ScanctTest.configure_motors(self, motors)
        ScanctTest.configure_mntgrp(self, meas_config)
        # Run the ascanct
        self.macro_executor.run(macro_name=self.macro_name,
                                macro_params=macro_params,
                                sync=True, timeout=wait_timeout)
        self.assertFinished('Macro %s did not finish' % self.macro_name)

        expected_nb_points = int(macro_params[6]) + 1
        ScanctTest.check_using_output(self, expected_nb_points)
        ScanctTest.check_using_data(self, expected_nb_points)

    def macro_stops(self, meas_config, macro_params, wait_timeout=None,
                    stop_delay=0.1):
        motors = [macro_params[self.MOT1], macro_params[self.MOT2]]
        ScanctTest.configure_motors(self, motors)
        ScanctTest.configure_mntgrp(self, meas_config)
        # Run the ascanct
        self.macro_executor.run(macro_name=self.macro_name,
                                macro_params=macro_params,
                                sync=False, timeout=wait_timeout)
        if stop_delay is not None:
            time.sleep(stop_delay)
        self.macro_executor.stop()
        self.macro_executor.wait(timeout=wait_timeout)
        ScanctTest.check_stopped(self)

    def tearDown(self):
        ScanctTest.tearDown(self)
        unittest.TestCase.tearDown(self)


meshct_params_1 = ['_test_mt_1_1', '0', '10', '2', '_test_mt_1_2', '0', '20',
                   '2', '0.1']


@testRun(meas_config=mg_config1, macro_params=meshct_params_1,
         wait_timeout=30)
class MeshctTest(ScanctTest, unittest.TestCase):
    """Checks that meshct works and generates the exact number of records
    by parsing the door output.

    .. todo:: check the macro data instead of the door output
    """
    macro_name = 'meshct'
    MOT1 = 0
    MOT2 = 4
    INTERVALS_MOT1 = 3
    INTERVALS_MOT2 = 7

    def setUp(self):
        unittest.TestCase.setUp(self)
        ScanctTest.setUp(self)

    def macro_runs(self, meas_config, macro_params, wait_timeout=None):
        motors = [macro_params[self.MOT1], macro_params[self.MOT2]]
        ScanctTest.configure_motors(self, motors)
        ScanctTest.configure_mntgrp(self, meas_config)
        self.macro_executor.run(macro_name=self.macro_name,
                                macro_params=macro_params,
                                sync=True, timeout=wait_timeout)
        self.assertFinished('Macro %s did not finish' % self.macro_name)

        expected_nb_points = (int(macro_params[self.INTERVALS_MOT1]) + 1) * \
                             (int(macro_params[self.INTERVALS_MOT2]) + 1)
        ScanctTest.check_using_output(self, expected_nb_points)
        ScanctTest.check_using_data(self, expected_nb_points)

    def macro_stops(self, meas_config, macro_params, wait_timeout=None,
                    stop_delay=0.1):
        motors = [macro_params[self.MOT1], macro_params[self.MOT2]]
        ScanctTest.configure_motors(self, motors)
        ScanctTest.configure_mntgrp(self, meas_config)
        self.macro_executor.run(macro_name=self.macro_name,
                                macro_params=macro_params,
                                sync=False, timeout=wait_timeout)
        if stop_delay is not None:
            time.sleep(stop_delay)
        self.macro_executor.stop()
        self.macro_executor.wait(timeout=wait_timeout)
        ScanctTest.check_stopped(self)

    def tearDown(self):
        ScanctTest.tearDown(self)
        unittest.TestCase.tearDown(self)
