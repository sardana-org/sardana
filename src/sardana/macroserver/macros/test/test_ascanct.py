#!/usr/bin/env python
"""Tests for scan macros"""

from taurus.external import unittest
import unittest
from sardana.macroserver.macros.test import (RunStopMacroTestCase, testRun, 
                                                        testStop, SarDemoEnv)

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
        """A helper method to parse log output of an executed scan macro.
        :params log_output: (seq<str>) Result of macro_executor.getLog('output')
        (see description in :class:`.BaseMacroExecutor`).

        :return: (seq<number>) The numeric data of a scan.
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
            if list_points[i+1]>=list_points[i]:
                ordered_points=1
            else:    
                ordered_points=0
                break                

        return (nb_points, ordered_points)


# Test for checking that the required number of points is present.
@testRun(macro_params=[_m1, '0', '10', '10', '0.1'], wait_timeout=float("inf"))
class AscanctTest(RunStopMacroTestCase, unittest.TestCase):
    macro_name = 'ascanct'
    macro_params=[_m1, '0', '10', '10', '0.1']

    utils = UtilsForTests()

    def macro_runs(self, macro_params, wait_timeout=float("inf")):
        """Checking that the required number of scan points is present."""
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
                        "The ascanct execution did not return any scan point.")

        self.assertEqual(int(obtained_nb_points), int(expected_nb_points), 
          "The ascanct execution did not return the expected number of " + 
          " points.\n Expected " + str(expected_nb_points) + " points." + 
          "\n Obtained " + str(obtained_nb_points) + " points." )

        self.assertTrue(ordered_points, "Scan points are NOT in good order.")




