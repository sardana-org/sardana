#!/usr/bin/env python
"""Tests for scan macros"""
import time
import PyTango
from taurus.external import unittest
from sardana.macroserver.macros.test import (RunStopMacroTestCase, testRun,
                                             testStop)
from sardana.pool import AcqSynchType
# TODO: MeasSarTestTestCase is a util, could be moved to base_sartest or another
# utils module.
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
            l = line.split()

            # Cast index of scan to int (the first element of the list)
            l[scan_index] = int(l[scan_index])
            list_points.append(l[scan_index])
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
        obtained_nb_points_data = len(data.keys())
        ordered_points_data = 0
        for i in range(obtained_nb_points_data - 1):
            if int(data.keys()[i + 1]) >= int(data.keys()[i]):
                ordered_points_data = 1
            else:
                ordered_points_data = 0
                break
        return ordered_points_data

mg_config1 = [[('_test_ct_1_1', '_test_tg_1_1', AcqSynchType.Trigger)]]
mg_config2 = [[('_test_ct_1_1', '_test_tg_1_1', AcqSynchType.Trigger),
               ('_test_ct_1_2', '_test_tg_1_1', AcqSynchType.Trigger)]
              ]
mg_config3 = [[('_test_ct_1_1', 'software', AcqSynchType.Trigger)],
              [('_test_ct_2_1', '_test_tg_1_1', AcqSynchType.Trigger)]
              ]
mg_config4 = [[('_test_ct_1_1', 'software', AcqSynchType.Trigger)],
              [('_test_ct_2_1', 'software', AcqSynchType.Trigger)]
              ]
macro_params_1 = ['_test_mt_1_1', '0', '10', '100', '0.1']


@testRun(meas_config=mg_config1, macro_params=macro_params_1,
         wait_timeout=30)
@testRun(meas_config=mg_config2, macro_params=macro_params_1,
         wait_timeout=30)
@testRun(meas_config=mg_config3, macro_params=macro_params_1,
         wait_timeout=30)
@testRun(meas_config=mg_config4, macro_params=macro_params_1,
         wait_timeout=30)
@testStop(meas_config=mg_config1, macro_params=macro_params_1,
          stop_delay=5, wait_timeout=20)
class AscanctTest(MeasSarTestTestCase, BaseMacroServerTestCase,
                  RunStopMacroTestCase, unittest.TestCase):
    """Checks that ascanct works and generates the exact number of records
    by parsing the door output.

    .. todo:: check the macro data instead of the door output
    """
    macro_name = 'ascanct'

    utils = UtilsForTests()

    def setUp(self):
        unittest.TestCase.setUp(self)
        MeasSarTestTestCase.setUp(self)
        BaseMacroServerTestCase.setUp(self, self.pool_name)
        RunStopMacroTestCase.setUp(self)

    def macro_runs(self, meas_config, macro_params, wait_timeout=float("inf")):
        # TODO: workaround for bug with velocity<base_rate: Sdn#38
        mot = PyTango.DeviceProxy(macro_params[0])
        mot.write_attribute('acceleration', 0.1)
        mot.write_attribute('base_rate', 0)
        mot.write_attribute('deceleration', 0.1)
        # creating MEAS
        self.create_meas(meas_config)
        # Set ActiveMntGrp
        self.macro_executor.run(macro_name='senv',
                                macro_params=['ActiveMntGrp', '_test_mg_1'],
                                sync=True, timeout=wait_timeout)
        # Run the ascanct
        self.macro_executor.run(macro_name=self.macro_name,
                                macro_params=macro_params,
                                sync=True, timeout=wait_timeout)
        self.assertFinished('Macro %s did not finish' % self.macro_name)

        # Checking that the required number of scan points is present.
        expected_nb_points = int(macro_params[3]) + 1

        # Test data from log_output (macro_executor.getLog('output'))
        log_output = self.macro_executor.getLog('output')
        (aa, bb) = self.utils.parsingOutputPoints(log_output)
        # ordered_points: (int) obtained number of points.
        obtained_nb_points = aa
        # ordered_points: booleand which indicates if points are ordered.
        ordered_points = bb

        self.assertNotEqual(obtained_nb_points, 0,
                            "The ascanct execution did not return any scan point.\n"
                            + "Checked using log_output")

        self.assertEqual(obtained_nb_points, expected_nb_points,
                         "The ascanct execution did not return the expected number of " +
                         " points.\n Expected " + str(expected_nb_points) + " points." +
                         "\n Obtained " + str(obtained_nb_points) + " points."
                         + "Checked using log_output")

        self.assertTrue(ordered_points, "Scan points are NOT in good order.\n"
                        + "Checked using log_output")

        # Test data from macro (macro_executor.getData())
        data = self.macro_executor.getData()
        order_points_data = self.utils.orderPointsData(data)

        self.assertTrue(len(data.keys()) > 0,
                        "The ascanct execution did not return any scan point.\n"
                        + "Checked using macro_executor.getData()")

        obtained_nb_points_data = len(data.keys())
        self.assertEqual(int(obtained_nb_points_data), int(expected_nb_points),
                         "The ascanct execution did not return the expected number of " +
                         " points.\n Expected " + str(expected_nb_points) + " points." +
                         "\n Obtained " + str(obtained_nb_points_data) + " points." +
                         "\nChecked using macro_executor.getData()")

        self.assertTrue(order_points_data, "Scan points are NOT in good order."
                        + "\nChecked using  macro_executor.getData().")

    def macro_stops(self, meas_config, macro_params, wait_timeout=float("inf"),
                    stop_delay=0.1):
        # TODO: workaround for bug with velocity<base_rate: Sdn#38
        mot = PyTango.DeviceProxy(macro_params[0])
        mot.write_attribute('acceleration', 0.1)
        mot.write_attribute('base_rate', 0)
        mot.write_attribute('deceleration', 0.1)
        # creating MEAS
        self.create_meas(meas_config)
        # Set ActiveMntGrp
        self.macro_executor.run(macro_name='senv',
                                macro_params=['ActiveMntGrp', '_test_mg_1'],
                                sync=True, timeout=wait_timeout)
        # Run the ascanct
        self.macro_executor.run(macro_name=self.macro_name,
                                macro_params=macro_params,
                                sync=False, timeout=wait_timeout)
        if stop_delay is not None:
            time.sleep(stop_delay)
        self.macro_executor.stop()
        self.macro_executor.wait(timeout=wait_timeout)
        self.assertStopped('Macro %s did not stop' % self.macro_name)
        for name in self.expchan_names + self.tg_names:
            channel = PyTango.DeviceProxy(name)
            desired_state = PyTango.DevState.ON
            state = channel.state()
            msg = 'element %s state after stop is %s (should be %s)' %\
                (name, state, desired_state)
            self.assertEqual(state, desired_state, msg)

    def tearDown(self):
        BaseMacroServerTestCase.tearDown(self)
        MeasSarTestTestCase.tearDown(self)
        RunStopMacroTestCase.tearDown(self)
        unittest.TestCase.tearDown(self)
