import os
import uuid
import unittest
from taurus import Device
from taurus.core.tango.tangovalidator import TangoDeviceNameValidator
from sardana.pool import AcqSynchType
from sardana.taurus.core.tango.sardana.pool import registerExtensions
from sardana.tango.pool.test.base_sartest import SarTestTestCase


class TestMeasurementGroupConfiguration(SarTestTestCase, unittest.TestCase):

    def setUp(self):
        SarTestTestCase.setUp(self)
        registerExtensions()

    def tearDown(self):
        SarTestTestCase.tearDown(self)

    def _assertResult(self, result, channels, expected_value):
        expected_channels = list(channels)
        for channel, value in result.items():
            msg = "unexpected key: {}".format(channel)
            self.assertIn(channel, expected_channels, msg)
            expected_channels.remove(channel)
            self.assertEqual(value, expected_value)
        msg = "{} are missing".format(expected_channels)
        self.assertEqual(len(expected_channels), 0, msg)

    def _assertMultipleResults(self, result, channels, expected_values):
        expected_channels = list(channels)
        for (channel, value), expected_value in zip(result.items(),
                                                    expected_values):
            msg = "unexpected key: {}".format(channel)
            self.assertIn(channel, expected_channels, msg)
            expected_channels.remove(channel)
            self.assertEqual(value, expected_value)
        msg = "{} are missing".format(expected_channels)
        self.assertEqual(len(expected_channels), 0, msg)

    def test_enabled(self, elements=["_test_ct_1_1", "_test_ct_1_2",
                                     "_test_2d_1_3",
                                     "_test_mt_1_3/position"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)
        try:
            mg = Device(mg_name)

            # Check initial state of all kind of channels, nonexistent
            # channels for the feature return None as result.
            result = mg.getEnabled(*elements)
            expected = [True] * len(elements)
            self._assertMultipleResults(result, elements, expected)

            # Test every possible combination of setting values
            # Check that changing one channel doesn't affect the other
            mg.setEnabled(False, *elements)
            result = mg.getEnabled(*elements)
            expected = [False] * len(elements)
            self._assertMultipleResults(result, elements, expected)
            mg.setEnabled(True, elements[0])
            result = mg.getEnabled(*elements)
            expected = [False] * len(elements)
            expected[0] = True
            self._assertMultipleResults(result, elements, expected)
            mg.setEnabled(False, *elements)
            resutl = mg.getEnabled(*elements)
            self._assertResult(resutl, elements, False)

            # Redefine elements to ony use existing values
            elements = ["_test_ct_1_1", "_test_ct_1_2"]

            # Set values using the controller instead of channels
            mg.setEnabled(True, "_test_ct_ctrl_1")
            resutl = mg.getEnabled(*elements)
            self._assertResult(resutl, elements, True)

            # Get values by controller
            mg.setEnabled(False, *elements)
            resutl = mg.getEnabled("_test_ct_ctrl_1")
            self._assertResult(resutl, elements, False)

            # Check ret_full_name
            v = TangoDeviceNameValidator()
            full_names = [v.getNames(element)[0] for element in elements]
            resutl = mg.getEnabled(*full_names)
            self._assertResult(resutl, elements, False)
            mg.setEnabled(True, *full_names)
            resutl = mg.getEnabled(*elements, ret_full_name=True)
            self._assertResult(resutl, full_names, True)
        finally:
            mg.cleanUp()
            if os.name != "nt":
                self.pool.DeleteElement(mg_name)

    def test_output(self, elements=["_test_ct_1_1", "_test_ct_1_2",
                                    "_test_2d_1_3",
                                    "_test_mt_1_3/position"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)

        try:
            mg = Device(mg_name)

            # Check initial state of all kind of channels, nonexistent
            # channels for the feature return None as result.
            enabled = mg.getOutput(*elements)
            expected = [True] * len(elements)
            self._assertMultipleResults(enabled, elements, expected)

            # Test every possible combination of setting values
            # Check that changing one channel doesn't affect the other
            mg.setOutput(False, *elements)
            is_output = mg.getOutput(*elements)
            self._assertResult(is_output, elements, False)
            mg.setOutput(True, elements[0])
            result = mg.getOutput(*elements)
            expected = [False] * len(elements)
            expected[0] = True
            self._assertMultipleResults(result, elements, expected)
            mg.setOutput(False, *elements)
            is_output = mg.getOutput(*elements)
            self._assertResult(is_output, elements, False)

            # Redefine elements to ony use existing values
            elements = ["_test_ct_1_1", "_test_ct_1_2"]

            # Set values using the controller instead of channels
            mg.setOutput(True, "_test_ct_ctrl_1")
            is_output = mg.getOutput(*elements)
            self._assertResult(is_output, elements, True)

            # Get values by controller
            mg.setOutput(False, *elements)
            is_output = mg.getOutput("_test_ct_ctrl_1")
            self._assertResult(is_output, elements, False)

            # Check ret_full_name
            v = TangoDeviceNameValidator()
            full_names = [v.getNames(element)[0] for element in elements]
            is_output = mg.getOutput(*full_names)
            self._assertResult(is_output, elements, False)
            mg.setOutput(True, *full_names)
            is_output = mg.getOutput(*elements, ret_full_name=True)
            self._assertResult(is_output, full_names, True)
        finally:
            mg.cleanUp()
            if os.name != "nt":
                self.pool.DeleteElement(mg_name)

    def test_PlotType(self, elements=["_test_ct_1_1", "_test_ct_1_2",
                                      "_test_ct_1_3", "_test_2d_1_3",
                                      "_test_mt_1_3/position"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)

        try:
            mg = Device(mg_name)
            plottype = mg.getPlotType()
            self._assertResult(plottype, elements, 0)
            mg.setPlotType("Image", elements[0])
            mg.setPlotType("Spectrum", elements[1])
            mg.setPlotType("No", elements[2])
            mg.setPlotType("Image", elements[3])
            mg.setPlotType("Image", elements[4])
            plottype = mg.getPlotType()
            expected_values = [2, 1, 0, 2, 2]
            self._assertMultipleResults(plottype, elements, expected_values)
            with self.assertRaises(ValueError):
                mg.setPlotType("asdf", elements[2])

            # Redefine elements
            elements = ["_test_ct_1_1", "_test_ct_1_2", "_test_ct_1_3"]

            # Set values using the controller instead of channels
            mg.setPlotType("Image", "_test_ct_ctrl_1")
            plottype = mg.getPlotType(*elements)
            self._assertResult(plottype, elements, 2)

            # Get values by controller
            mg.setPlotType("Spectrum", *elements)
            plottype = mg.getPlotType("_test_ct_ctrl_1")
            self._assertResult(plottype, elements, 1)

            # Check ret_full_name
            v = TangoDeviceNameValidator()
            full_names = [v.getNames(element)[0] for element in elements]
            plottype = mg.getPlotType(*full_names)
            self._assertResult(plottype, elements, 1)
            mg.setPlotType("Image", *full_names)
            plottype = mg.getPlotType(*elements, ret_full_name=True)
            self._assertResult(plottype, full_names, 2)

        finally:
            mg.cleanUp()
            if os.name != "nt":
                self.pool.DeleteElement(mg_name)

    def test_PlotAxes(self, elements=["_test_ct_1_1", "_test_ct_1_2",
                                      "_test_ct_1_3", "_test_2d_1_3",
                                      "_test_mt_1_3/position"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)

        try:
            mg = Device(mg_name)
            mg.setPlotType("Image", elements[0])
            mg.setPlotType("Spectrum", elements[1])
            mg.setPlotType("No", elements[2])
            mg.setPlotType("Image", elements[3])
            mg.setPlotType("Image", elements[4])
            result = mg.getPlotAxes()
            self._assertResult(result, elements, [])

            mg.setPlotAxes(["<idx>", "<idx>"], elements[0])
            mg.setPlotAxes(["<mov>"], elements[1])
            with self.assertRaises(Exception):
                mg.setPlotAxes(['<mov>'], elements[2])
            mg.setPlotAxes(["<idx>", "<idx>"], elements[3])
            mg.setPlotAxes(["<idx>", "<idx>"], elements[4])

            result = mg.getPlotAxes()
            expected_result = [['<idx>', '<idx>'], ['<mov>'], [],
                               ['<idx>', '<idx>'], ['<idx>', '<idx>']]
            self._assertMultipleResults(result, elements, expected_result)

            mg.setPlotAxes(["<mov>", "<idx>"], elements[0])
            mg.setPlotAxes(["<idx>"], elements[1])
            result = mg.getPlotAxes()
            expected_result = [['<mov>', '<idx>'], ['<idx>'], [],
                               ['<idx>', '<idx>'], ['<idx>', '<idx>']]
            self._assertMultipleResults(result, elements, expected_result)

            mg.setPlotAxes(["<mov>", "<mov>"], elements[0])
            result = mg.getPlotAxes()
            expected_result = [['<mov>', '<mov>'], ['<idx>'], [],
                               ['<idx>', '<idx>'], ['<idx>', '<idx>']]
            self._assertMultipleResults(result, elements, expected_result)

            with self.assertRaises(RuntimeError):
                mg.setPlotAxes(["<mov>"], elements[2])
            with self.assertRaises(ValueError):
                mg.setPlotAxes(["<mov>", "<idx>"], elements[1])
            with self.assertRaises(ValueError):
                mg.setPlotAxes(["<mov>"], elements[0])

            elements = ["_test_ct_1_1", "_test_ct_1_2", "_test_ct_1_3"]
            # Set values using the controller instead of channels
            with self.assertRaises(Exception):
                mg.setPlotAxes(["<mov>"], "_test_ct_ctrl_1")
            # TODO get method by controller doesn't give the order
            # Get values by controller
            result = mg.getPlotAxes("_test_ct_ctrl_1")
            expected_result = [['<mov>', '<mov>'], ['<idx>'], []]
            self._assertMultipleResults(result, elements, expected_result)

            # Check ret_full_name
            v = TangoDeviceNameValidator()
            full_names = [v.getNames(element)[0] for element in elements]
            result = mg.getPlotAxes(*full_names)
            expected_result = [['<mov>', '<mov>'], ['<idx>'], []]
            self._assertMultipleResults(result, elements, expected_result)
            mg.setPlotAxes(["<idx>", "<idx>"], full_names[0])
            mg.setPlotAxes(["<mov>"], full_names[1])
            result = mg.getPlotAxes(*elements, ret_full_name=True)
            expected_result = [['<idx>', '<idx>'], ['<mov>'], []]
            self._assertMultipleResults(result, full_names, expected_result)
        finally:
            mg.cleanUp()
            if os.name != "nt":
                self.pool.DeleteElement(mg_name)

    def test_Timer(self, elements=["_test_ct_1_1", "_test_ct_1_2",
                                   "_test_ct_1_3",
                                   "_test_mt_1_3/position"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)
        try:
            mg = Device(mg_name)

            result = mg.getTimer("_test_mt_1_3/position")
            if os.name != "nt":
                with self.assertRaises(Exception):
                    mg.setTimer("_test_mt_1_3/position")
            self._assertResult(result,  ["_test_mt_1_3/position"], None)
            mg.setTimer('_test_ct_1_3')
            result = mg.getTimer(*elements)
            expected = ['_test_ct_1_3', '_test_ct_1_3', '_test_ct_1_3', None]
            self._assertMultipleResults(result, elements, expected)

            mg.setTimer('_test_ct_1_2')
            result = mg.getTimer(*elements)
            expected = ['_test_ct_1_2', '_test_ct_1_2', '_test_ct_1_2', None]
            self._assertMultipleResults(result, elements, expected)

            result = mg.getTimer(*elements, ret_by_ctrl=True)
            self._assertMultipleResults(result,
                                        ['_test_ct_ctrl_1', '__tango__'],
                                        ['_test_ct_1_2', None])

            # Check ret_full_name
            v = TangoDeviceNameValidator()
            counters = ["_test_ct_1_1", "_test_ct_1_2", "_test_ct_1_3"]
            full_names = [v.getNames(counter)[0] for counter in counters]
            mg.setTimer(v.getNames('_test_ct_1_1')[0])
            result = mg.getTimer()
            expected = ['_test_ct_1_1', '_test_ct_1_1', '_test_ct_1_1', None]
            self._assertMultipleResults(result, elements, expected)
            # TODO ret_full_name gives controler name
            mg.setTimer("_test_ct_1_2")
            result = mg.getTimer(*counters, ret_full_name=True)
            self._assertResult(result, full_names, "_test_ct_1_2")
        finally:
            mg.cleanUp()
            if os.name != "nt":
                self.pool.DeleteElement(mg_name)

    def test_Monitor(self, elements=["_test_ct_1_1", "_test_ct_1_2",
                                     "_test_ct_1_3", "_test_2d_1_1",
                                     '_test_2d_1_2',
                                     "_test_mt_1_3/position"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)
        try:
            mg = Device(mg_name)

            if os.name != "nt":
                with self.assertRaises(Exception):
                    mg.setMonitor("_test_mt_1_3/position")

            mg.setMonitor('_test_2d_1_2')
            mg.setMonitor("_test_ct_1_3")
            expected = ["_test_ct_1_3", "_test_ct_1_3", "_test_ct_1_3",
                        "_test_2d_1_2", '_test_2d_1_2', None]
            result = mg.getMonitor()
            self._assertMultipleResults(result, elements, expected)

            expected = ["_test_ct_1_3", '_test_2d_1_2', None]
            result = mg.getMonitor(ret_by_ctrl=True)
            ctrls = ['_test_ct_ctrl_1', '_test_2d_ctrl_1', '__tango__']
            self._assertMultipleResults(result, ctrls, expected)

            # Check ret_full_name
            v = TangoDeviceNameValidator()
            counters = ["_test_ct_1_1", "_test_ct_1_2", "_test_ct_1_3",
                        '_test_2d_1_1', '_test_2d_1_2']
            full_names = [v.getNames(counter)[0] for counter in counters]
            mg.setMonitor(v.getNames('_test_ct_1_1')[0])
            mg.setMonitor(v.getNames('_test_2d_1_2')[0])

            result = mg.getMonitor(*counters, ret_full_name=True)
            expected = ["_test_ct_1_1", "_test_ct_1_1", "_test_ct_1_1",
                        "_test_2d_1_2", '_test_2d_1_2']
            self._assertMultipleResults(result, full_names, expected)
        finally:
            mg.cleanUp()
            if os.name != "nt":
                self.pool.DeleteElement(mg_name)

    def test_Synchronizer(self, elements=["_test_ct_1_1", "_test_ct_1_2",
                                          "_test_ct_1_3", "_test_2d_1_1",
                                          "_test_mt_1_3/position"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)
        try:
            mg = Device(mg_name)
            result = mg.getSynchronizer()
            expected = ['software', 'software', 'software', 'software', None]
            self._assertMultipleResults(result, elements, expected)

            if os.name != "nt":
                with self.assertRaises(Exception):
                    mg.setSynchronizer('_test_tg_1_2', "_test_mt_1_3/position")

            mg.setSynchronizer('_test_tg_1_2', "_test_ct_ctrl_1",
                               "_test_2d_ctrl_1")

            expected = ['_test_tg_1_2', '_test_tg_1_2', '_test_tg_1_2',
                        '_test_tg_1_2', None]
            result = mg.getSynchronizer()
            self._assertMultipleResults(result, elements, expected)

            mg.setSynchronizer('software', "_test_ct_ctrl_1",
                               "_test_2d_ctrl_1")
            result = mg.getSynchronizer()
            expected = ['software', 'software', 'software', 'software', None]
            self._assertMultipleResults(result, elements, expected)

            with self.assertRaises(Exception):
                mg.setSynchronizer('asdf', "_test_ct_ctrl_1",
                                   "_test_2d_ctrl_1")

            # Check ret_full_name
            v = TangoDeviceNameValidator()
            counters = ["_test_ct_1_1", "_test_ct_1_2", "_test_ct_1_3",
                        '_test_2d_1_1']
            full_names = [v.getNames(counter)[0] for counter in counters]
            mg.setSynchronizer('_test_tg_1_2', "_test_ct_ctrl_1",
                               "_test_2d_ctrl_1")

            result = mg.getSynchronizer(*counters, ret_full_name=True)

            self._assertResult(result, full_names, '_test_tg_1_2')

        finally:
            mg.cleanUp()
            if os.name != "nt":
                self.pool.DeleteElement(mg_name)

    def test_Synchronization(self, elements=["_test_ct_1_1", "_test_ct_1_2",
                                             "_test_ct_1_3", "_test_2d_1_1",
                                             "_test_mt_1_3/position"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)
        try:
            mg = Device(mg_name)
            result = mg.getSynchronization()
            expected = [AcqSynchType.Trigger, AcqSynchType.Trigger,
                        AcqSynchType.Trigger, AcqSynchType.Trigger, None]
            self._assertMultipleResults(result, elements, expected)
            # TODO: maybe we should raise an exception here?
            # with self.assertRaises(Exception):
            #     mg.setSynchronization(AcqSynchType.Trigger,
            #                           "_test_mt_1_3/position")

            mg.setSynchronization(AcqSynchType.Gate, "_test_ct_ctrl_1",
                                  "_test_2d_ctrl_1")

            expected = [AcqSynchType.Gate, AcqSynchType.Gate,
                        AcqSynchType.Gate, AcqSynchType.Gate, None]
            result = mg.getSynchronization()
            self._assertMultipleResults(result, elements, expected)

            mg.setSynchronization(AcqSynchType.Start, "_test_ct_ctrl_1",
                                  "_test_2d_ctrl_1")
            result = mg.getSynchronization()
            expected = [AcqSynchType.Start, AcqSynchType.Start,
                        AcqSynchType.Start, AcqSynchType.Start, None]
            self._assertMultipleResults(result, elements, expected)

            with self.assertRaises(Exception):
                mg.setSynchronization('asdf', "_test_ct_ctrl_1",
                                      "_test_2d_ctrl_1")

            # Check ret_full_name
            v = TangoDeviceNameValidator()
            counters = ["_test_ct_1_1", "_test_ct_1_2", "_test_ct_1_3",
                        '_test_2d_1_1']
            full_names = [v.getNames(counter)[0] for counter in counters]
            mg.setSynchronization(AcqSynchType.Trigger, "_test_ct_ctrl_1",
                                  "_test_2d_ctrl_1")

            result = mg.getSynchronization(*counters, ret_full_name=True)

            self._assertResult(result, full_names, AcqSynchType.Trigger)

        finally:
            mg.cleanUp()
            if os.name != "nt":
                self.pool.DeleteElement(mg_name)

    def test_ValueRefEnabled(self, elements=["_test_2d_1_1", "_test_2d_1_2",
                                             "_test_ct_1_3",
                                             "_test_mt_1_3/position"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)
        try:
            mg = Device(mg_name)

            # Check initial state of all kind of channels, nonexistent
            # channels for the feature return None as result.
            enabled = mg.getValueRefEnabled(*elements)
            expected = [False, False, None, None]
            self._assertMultipleResults(enabled, elements, expected)

            # Check if the nonexistent channels raise error if trying to set
            with self.assertRaises(Exception):
                mg.setValueRefEnabled(True, *elements[-2])
            with self.assertRaises(Exception):
                mg.setValueRefEnabled(True, *elements[-1])

            # Redefine elements to ony use existing values
            elements = ["_test_2d_1_1", "_test_2d_1_2"]

            # Test every possible combination of setting values
            # Check that changing one channel doesn't affect the other
            mg.setValueRefEnabled(True, *elements)
            enabled = mg.getValueRefEnabled(*elements)
            self._assertResult(enabled, elements, True)
            mg.setValueRefEnabled(False, elements[0])
            result = mg.getValueRefEnabled(*elements)
            expected = [True] * len(elements)
            expected[0] = False
            self._assertMultipleResults(result, elements, expected)
            mg.setValueRefEnabled(True, *elements)
            enabled = mg.getValueRefEnabled(*elements)
            self._assertResult(enabled, elements, True)

            # Set values using the controller instead of channels
            mg.setValueRefEnabled(True, "_test_2d_ctrl_1")
            enabled = mg.getValueRefEnabled(*elements)
            self._assertResult(enabled, elements, True)

            # Get values by controller
            mg.setValueRefEnabled(False, *elements)
            enabled = mg.getValueRefEnabled("_test_2d_ctrl_1")
            self._assertResult(enabled, elements, False)

            # Check ret_full_name
            v = TangoDeviceNameValidator()
            full_names = [v.getNames(element)[0] for element in elements]
            enabled = mg.getValueRefEnabled(*full_names)
            self._assertResult(enabled, elements, False)
            mg.setValueRefEnabled(True, *full_names)
            enabled = mg.getValueRefEnabled(*elements, ret_full_name=True)
            self._assertResult(enabled, full_names, True)
        finally:
            mg.cleanUp()
            if os.name != "nt":
                self.pool.DeleteElement(mg_name)

    def test_ValueRefPattern(self, elements=["_test_2d_1_1", "_test_2d_1_2",
                                             "_test_ct_1_3",
                                             "_test_mt_1_3/position"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)
        try:
            mg = Device(mg_name)

            # Check initial state of all kind of channels, nonexistent
            # channels for the feature return None as result.
            pattern = mg.getValueRefPattern(*elements)
            expected = ['', '', None, None]
            self._assertMultipleResults(pattern, elements, expected)

            # Check if the nonexistent channels raise error if trying to set
            with self.assertRaises(Exception):
                mg.setValueRefPattern('/tmp/test_foo.txt', *elements[-2])
            with self.assertRaises(Exception):
                mg.setValueRefPattern('/tmp/test_foo.txt', *elements[-1])

            # Redefine elements to ony use existing values
            elements = ["_test_2d_1_1", "_test_2d_1_2"]

            # Test every possible combination of setting values
            # Check that changing one channel doesn't affect the other
            mg.setValueRefPattern('/tmp/test_foo.txt', *elements)
            pattern = mg.getValueRefPattern(*elements)
            self._assertResult(pattern, elements, '/tmp/test_foo.txt')

            # Set values using the controller instead of channels
            mg.setValueRefPattern('/tmp/test_foo2.txt', "_test_2d_ctrl_1")
            pattern = mg.getValueRefPattern(*elements)
            self._assertResult(pattern, elements, '/tmp/test_foo2.txt')

            # Get values by controller
            mg.setValueRefPattern('/tmp/test_foo.txt', *elements)
            pattern = mg.getValueRefPattern("_test_2d_ctrl_1")
            self._assertResult(pattern, elements, '/tmp/test_foo.txt')

            # Check ret_full_name
            v = TangoDeviceNameValidator()
            full_names = [v.getNames(element)[0] for element in elements]
            pattern = mg.getValueRefPattern(*full_names)
            self._assertResult(pattern, elements, '/tmp/test_foo.txt')
            mg.setValueRefPattern('/tmp/test_foo2.txt', *full_names)
            pattern = mg.getValueRefPattern(*elements, ret_full_name=True)
            self._assertResult(pattern, full_names, '/tmp/test_foo2.txt')

        finally:
            mg.cleanUp()
            if os.name != "nt":
                self.pool.DeleteElement(mg_name)
