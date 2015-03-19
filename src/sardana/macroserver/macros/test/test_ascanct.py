#!/usr/bin/env python
"""Tests for scan macros"""

from taurus.external import unittest
from sardana.macroserver.macros.test import (RunStopMacroTestCase, testRun, 
                                                        testStop, SarDemoEnv)
from sardana.pool import AcqTriggerType
from sardana.pool.test import (createPoolMeasurementGroup,
                               dummyMeasurementGroupConf01,
                               createMGUserConfiguration)
#TODO: MeasSarTestTestCase is a util, could be moved to base_sartest or another
# utils module.
from sardana.tango.pool.test.test_measurementgroup import MeasSarTestTestCase
from sardana.tango.macroserver.test import BaseMacroServerTestCase

#get handy motor names from sardemo
try:
    _MOTORS = SarDemoEnv().getMotors()
    _m1, _m2 = _MOTORS[:2]
except RuntimeError:
    import taurus
    from sardana import sardanacustomsettings
    door_name = getattr(sardanacustomsettings, 'UNITTEST_DOOR_NAME',
                        'UNDEFINED')
    taurus.warning("The door %s is not running. " % (door_name) +
                   "Ignore this message if you are building the documentation")
    _m1 = _m2 = 'motor_not_defined'
except Exception, e:
    import taurus
    taurus.debug(e)
    taurus.warning("It was not possible to retrieve the motor names. " +
                 "Ignore this message if you are building the documentation.")
    _m1 = _m2 = 'motor_not_defined'


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
        for i in range(len(list_points)-1):    
            if list_points[i+1] >= list_points[i]:
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
        for i in range(obtained_nb_points_data-1):
            if int(data.keys()[i+1]) >= int(data.keys()[i]):
                ordered_points_data = 1
            else:    
                ordered_points_data = 0
                break     
        return ordered_points_data

#TODO Decide what we do with old AscanctTest test (Move or delete)
"""
# Test for checking that the required number of points is present.
@testRun(macro_params=[_m1, '0', '10', '10', '0.1'], wait_timeout=float("inf"))
class AscanctTest(RunStopMacroTestCase, unittest.TestCase):
    macro_name = 'ascanct'
    macro_params=[_m1, '0', '10', '10', '0.1']

    utils = UtilsForTests()

    def macro_runs(self, macro_params, wait_timeout=float("inf")):
        Checking that the required number of scan points is present.
        self.macro_executor.run(macro_name=self.macro_name,
                                macro_params=macro_params,
                                sync=True, timeout=wait_timeout)
        self.assertFinished('Macro %s did not finish' % self.macro_name)

        expected_nb_points = macro_params[3]
            
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

        self.assertEqual(int(obtained_nb_points), int(expected_nb_points), 
          "The ascanct execution did not return the expected number of " + 
          " points.\n Expected " + str(expected_nb_points) + " points." + 
          "\n Obtained " + str(obtained_nb_points) + " points." 
           + "Checked using log_output")

        self.assertTrue(ordered_points, "Scan points are NOT in good order.\n"
                                         + "Checked using log_output")

        # Test data from macro (macro_executor.getData())
        data = self.macro_executor.getData() 
        order_points_data = self.utils.orderPointsData(data)

        self.assertTrue(len(data.keys())>0,
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

"""

# Test for checking that the required number of points is present by doing 
# an ascanct with a trigger device.
# Test for checking that the required number of points is present.
mg_config1 = [[('_test_ct_1_1', '_test_tg_1_1', AcqTriggerType.Trigger)]]
macro_params_1 = ['_test_mt_1_1', '0', '10', '10', '0.1']

@testRun(meas_config=mg_config1, macro_params=macro_params_1, 
         wait_timeout=float("inf"))
class AscanctTest(MeasSarTestTestCase, BaseMacroServerTestCase,
                  RunStopMacroTestCase, unittest.TestCase):
    macro_name = 'ascanct'

    utils = UtilsForTests()
    # TODO remove it; It will generate by SCAN framework
    params_1 = {
        "offset": 0,
        "repetitions": 100,
        "integ_time": 0.01,
        "name": '_exp_01',
        "mode": "ContTimer"
    }

    def setUp(self):
        unittest.TestCase.setUp(self)
        MeasSarTestTestCase.setUp(self)
        BaseMacroServerTestCase.setUp(self, self.pool_name)
        RunStopMacroTestCase.setUp(self)

    def macro_runs(self, meas_config, macro_params, wait_timeout=float("inf")):
        
        # creating MEAS
        self.create_meas(meas_config)
        # TODO remove it
        self.prepare_meas(self.params_1)
        # Set ActiveMntGrp
        self.macro_executor.run(macro_name='senv',
                                macro_params=['ActiveMntGrp', '_test_mg_1'],
                                sync=True, timeout=wait_timeout)
        # Run the ascanct
        self.macro_executor.run(macro_name=self.macro_name,
                                macro_params=macro_params,
                                sync=True, timeout=wait_timeout)
        self.assertFinished('Macro %s did not finish' % self.macro_name)

        #Checking that the required number of scan points is present.
        expected_nb_points = macro_params[3]
            
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

        self.assertEqual(int(obtained_nb_points), int(expected_nb_points), 
          "The ascanct execution did not return the expected number of " + 
          " points.\n Expected " + str(expected_nb_points) + " points." + 
          "\n Obtained " + str(obtained_nb_points) + " points." 
           + "Checked using log_output")

        self.assertTrue(ordered_points, "Scan points are NOT in good order.\n"
                                         + "Checked using log_output")

        # Test data from macro (macro_executor.getData())
        data = self.macro_executor.getData() 
        order_points_data = self.utils.orderPointsData(data)

        self.assertTrue(len(data.keys())>0,
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

    def tearDown(self):
        BaseMacroServerTestCase.tearDown(self)
        MeasSarTestTestCase.tearDown(self)
        RunStopMacroTestCase.tearDown(self)
        unittest.TestCase.tearDown(self)


