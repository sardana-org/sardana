from sardana.taurus.core.tango.sardana import *
import uuid
from taurus import Device
from taurus.external.unittest import TestCase
from taurus.core.tango.tangovalidator import TangoDeviceNameValidator
from sardana.taurus.core.tango.sardana.pool import registerExtensions
from sardana.tango.pool.test.base_sartest import SarTestTestCase


class TestMeasurementGroupConfiguration(SarTestTestCase, TestCase):

    def setUp(self):
        SarTestTestCase.setUp(self)
        registerExtensions()

    def tearDown(self):
        SarTestTestCase.tearDown(self)

    def _assertResult(self, result, channels, expected_value):
        expected_channels = list(channels)
        print(result)
        for channel, value in result.items():
            msg = "unexpected key: {}".format(channel)
            self.assertIn(channel, expected_channels, msg)
            expected_channels.remove(channel)
            self.assertEqual(value, expected_value)
        msg = "{} are missing".format(expected_channels)
        self.assertEqual(len(expected_channels), 0, msg)

    def _assertMultipleResults(self, result, channels, expected_values):
        expected_channels = list(channels)
        print(result)
        for (channel, value), expected_value in zip(result.items(), expected_values):
            msg = "unexpected key: {}".format(channel)
            self.assertIn(channel, expected_channels, msg)
            expected_channels.remove(channel)
            self.assertEqual(value, expected_value)
        msg = "{} are missing".format(expected_channels)
        self.assertEqual(len(expected_channels), 0, msg)

    def test_enabled(self, elements = ["_test_ct_1_1", "_test_ct_1_2"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)
        try:
            mg = Device(mg_name)
            enabled = mg.getEnabled(*elements)
            self._assertResult(enabled, elements, True)
            mg.setEnabled(False, *elements)
            enabled = mg.getEnabled(*elements)
            self._assertResult(enabled, elements, False)
            enabled = mg.getEnabled("_test_ct_ctrl_1")
            self._assertResult(enabled, elements, False)
            mg.setEnabled(True, *elements)
            enabled = mg.getEnabled(*elements)
            self._assertResult(enabled, elements, True)
            # enabled = mg.getEnabled(*elements, ret_full_name=True)
            v = TangoDeviceNameValidator()
            full_names = [v.getNames(element)[0] for element in elements]
            enabled = mg.getEnabled(*full_names)
            self._assertResult(enabled, elements, True)
            # TODO Fix ret_full_name error and make a test
        finally:
            mg.cleanUp()
            self.pool.DeleteElement(mg_name)

    def test_output(self, elements=["_test_ct_1_1", "_test_ct_1_2"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)

        try:
            mg = Device(mg_name)
            is_output = mg.getOutput(*elements)
            self._assertResult(is_output, elements, True)
            mg.setOutput(False, *elements)
            is_output = mg.getOutput(*elements)
            self._assertResult(is_output, elements, False)
            is_output = mg.getOutput("_test_ct_ctrl_1")
            self._assertResult(is_output, elements, False)
            mg.setOutput(True, *elements)
            is_output = mg.getOutput(*elements)
            self._assertResult(is_output, elements, True)
            # is_output = mg.getOutput(*elements, ret_full_name=True)
            v = TangoDeviceNameValidator()
            full_names = []
            for element in elements:
                full_names.append(v.getNames(element)[0])
            print(full_names)
            is_output = mg.getOutput(*full_names)
            self._assertResult(is_output, elements, True)
            # TODO Fix ret_full_name error and make a test
        finally:
            mg.cleanUp()
            self.pool.DeleteElement(mg_name)

    def test_PlotType(self, elements=["_test_ct_1_1", "_test_ct_1_2", "_test_ct_1_3"]):
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
            plottype = mg.getPlotType()
            expected_values = [2, 1, 0]
            self._assertMultipleResults(plottype, elements, expected_values)
            with self.assertRaises(ValueError):
                mg.setPlotType("asdf", elements[2])
            print(mg.getPlotType())

        finally:
            mg.cleanUp()
            self.pool.DeleteElement(mg_name)

    def test_PlotAxes(self, elements=["_test_ct_1_1", "_test_ct_1_2", "_test_ct_1_3"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)

        try:
            mg = Device(mg_name)
            mg.setPlotType("Image", elements[0])
            mg.setPlotType("Spectrum", elements[1])
            mg.setPlotType("No", elements[2])
            result = mg.getPlotAxes()
            self._assertResult(result, elements, [])
            mg.setPlotAxes(["<idx>", "<idx>"], elements[0])
            mg.setPlotAxes(["<mov>"], elements[1])
            result = mg.getPlotAxes()
            expected_result = [['<idx>', '<idx>'], ['<mov>'], []]
            self._assertMultipleResults(result, elements, expected_result)
            mg.setPlotAxes(["<mov>", "<idx>"], elements[0])
            mg.setPlotAxes(["<idx>"], elements[1])
            result = mg.getPlotAxes()
            expected_result = [['<mov>', '<idx>'], ['<idx>'], []]
            self._assertMultipleResults(result, elements, expected_result)
            mg.setPlotAxes(["<mov>", "<mov>"], elements[0])
            result = mg.getPlotAxes()
            expected_result = [['<mov>', '<mov>'], ['<idx>'], []]
            self._assertMultipleResults(result, elements, expected_result)

            with self.assertRaises(RuntimeError):
                mg.setPlotAxes(["<mov>"], elements[2])
            with self.assertRaises(ValueError):
                mg.setPlotAxes(["<mov>", "<idx>"], elements[1])
            with self.assertRaises(ValueError):
                mg.setPlotAxes(["<mov>"], elements[0])
            print(mg.getPlotAxes())
        finally:
            mg.cleanUp()
            self.pool.DeleteElement(mg_name)

    def test_Timer(self, elements=["_test_ct_1_1", "_test_ct_1_2", "_test_ct_1_3"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)
        try:
            mg = Device(mg_name)
            previous = mg.getTimer()
            print(previous)
            mg.setTimer('_test_ct_1_3')
            self.assertNotEqual(mg.getTimer(), previous)
            self._assertResult(mg.getTimer(), elements, '_test_ct_1_3')
            self._assertResult(mg.getTimer(ret_by_ctrl=True), ['_test_ct_ctrl_1'], '_test_ct_1_3')

        finally:
            mg.cleanUp()
            self.pool.DeleteElement(mg_name)

    def test_Monitor(self, elements=["_test_ct_1_1", "_test_ct_1_2", "_test_ct_1_3"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)
        try:
            mg = Device(mg_name)
            previous = mg.getMonitor()
            print(previous)
            mg.setMonitor("_test_ct_1_2")
            self.assertNotEqual(mg.getMonitor(), previous)
            self._assertResult(mg.getMonitor(), elements, '_test_ct_1_2')
            self._assertResult(mg.getMonitor(ret_by_ctrl=True), ['_test_ct_ctrl_1'], '_test_ct_1_2')

        finally:
            mg.cleanUp()
            self.pool.DeleteElement(mg_name)

    def test_Synchronizer(self, elements=["_test_ct_1_1", "_test_ct_1_2", "_test_ct_1_3"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)
        try:
            mg = Device(mg_name)
            result = mg.getSynchronizer()
            self._assertResult(result, elements, 'software')
            mg.setSynchronizer('_test_tg_1_2')
            result = mg.getSynchronizer()
            self._assertResult(result, elements, '_test_tg_1_2')
            mg.setSynchronizer('software')
            result = mg.getSynchronizer()
            self._assertResult(result, elements, 'software')
            result = mg.getSynchronizer(ret_by_ctrl=True)
            self._assertResult(result, ['_test_ct_ctrl_1'], 'software')
            with self.assertRaises(Exception):
                mg.setSynchronizer('asdf')
            self._assertResult(result, ['_test_ct_ctrl_1'], 'software')

        finally:
            mg.cleanUp()
            self.pool.DeleteElement(mg_name)

    def test_ValueRefEnabled(self, elements=["_test_2d_1_1", "_test_2d_1_2", "_test_ct_1_1", "_test_ct_1_2"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)
        try:
            mg = Device(mg_name)
            enabled = mg.getValueRefEnabled(*elements)
            self._assertResult(enabled, elements, False)
            mg.setValueRefEnabled(False, *elements)
            enabled = mg.getValueRefEnabled(*elements)
            self._assertResult(enabled, elements, False)
            enabled = mg.getValueRefEnabled("_test_2d_ctrl_1")
            self._assertResult(enabled, elements[:2], False)
            enabled = mg.getValueRefEnabled("_test_ct_ctrl_1")
            self._assertResult(enabled, elements[-2:], False)
            mg.setValueRefEnabled(True, *elements)
            enabled = mg.getValueRefEnabled(*elements)
            self._assertResult(enabled, elements, True)

        finally:
            mg.cleanUp()
            self.pool.DeleteElement(mg_name)

    def test_ValueRefPattern(self, elements=["_test_2d_1_1", "_test_2d_1_2", "_test_ct_1_3"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)
        try:
            mg = Device(mg_name)
            pattern = mg.getValueRefEnabled(*elements)
            self._assertResult(pattern, elements, False)
            mg.setValueRefEnabled('/tmp/test_foo.txt', *elements)
            pattern = mg.getValueRefEnabled(*elements)
            self._assertResult(pattern, elements, '/tmp/test_foo.txt')
            pattern = mg.getValueRefEnabled("_test_2d_ctrl_1")
            self._assertResult(pattern, elements, '/tmp/test_foo.txt')

        finally:
            mg.cleanUp()
            self.pool.DeleteElement(mg_name)

