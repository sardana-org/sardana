from sardana.taurus.core.tango.sardana import *
import uuid
import numpy
from taurus import Device
from taurus.external.unittest import TestCase
from taurus.core.tango.tangovalidator import TangoDeviceNameValidator
from taurus.test.base import insertTest
from sardana.sardanautils import is_number, is_non_str_seq, is_pure_str
from sardana.taurus.core.tango.sardana.pool import registerExtensions
from sardana.tango.pool.test.base_sartest import SarTestTestCase

def is_numerical(obj):
    if is_number(obj):
        return True
    if is_non_str_seq(obj) or isinstance(obj, numpy.ndarray):
        if is_number(obj[0]):
            return True
        elif is_non_str_seq(obj[0]) or isinstance(obj, numpy.ndarray):
            if is_number(obj[0][0]):
                return True
    return False


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

    def test_enabled(self):
        elements = ["_test_ct_1_1", "_test_ct_1_2"]
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

            # mg = Device(mg_name)
            # enabled = mg.getOutput(*elements)
            # self._assertResult(enabled, elements, True)
            # for key in elements:
            #     self.assertTrue(mg._getOutputChannels()[key])
            # mg._setOutputChannels(False, elements)
            # for key in elements:
            #     self.assertFalse(mg._getOutputChannels()[key])
            # mg._setOutputChannels(True, elements)
            # for key in elements:
            #     self.assertTrue(mg._getOutputChannels()[key])
        finally:
            mg.cleanUp()
            self.pool.DeleteElement(mg_name)

    def testPlotTypeChannels(self, elements=["_test_ct_1_1", "_test_ct_1_2", "_test_ct_1_3"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)

        try:
            mg = Device(mg_name)
            print(mg._getPlotTypeChannels())
            mg._setPlotTypeChannels("Image", [elements[0]])
            mg._setPlotTypeChannels("Spectrum", [elements[1]])
            mg._setPlotTypeChannels("No", [elements[2]])
            print(mg._getPlotTypeChannels())
            try:
                mg._setPlotTypeChannels("asdf", [elements[2]])
                error = 1
            except:
                error = 0
            if error == 1:
                raise ValueError("Plot type string values are not restricted")
            print(mg._getPlotTypeChannels())

        finally:
            mg.cleanUp()
            self.pool.DeleteElement(mg_name)

    def testPlotAxesChannels(self, elements=["_test_ct_1_1", "_test_ct_1_2", "_test_ct_1_3"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)

        try:
            mg = Device(mg_name)
            mg._setPlotTypeChannels("Image", [elements[0]])
            mg._setPlotTypeChannels("Spectrum", [elements[1]])
            mg._setPlotTypeChannels("No", [elements[2]])
            print(mg._getPlotAxesChannels())
            mg._setPlotAxesChannels(["<idx>", "<idx>"], [elements[0]])
            mg._setPlotAxesChannels(["<mov>"], [elements[1]])
            print(mg._getPlotAxesChannels())
            mg._setPlotAxesChannels(["<mov>", "<idx>"], [elements[0]])
            mg._setPlotAxesChannels(["<idx>"], [elements[1]])
            print(mg._getPlotAxesChannels())
            mg._setPlotAxesChannels(["<mov>", "<mov>"], [elements[0]])
            print(mg._getPlotAxesChannels())

            try:
                mg._setPlotAxesChannels(["<mov>"], [elements[2]])
                error = 1
            except:
                error = 0
            if error == 1:
                raise ValueError("Channel without PlotType shouldn't accept a value")
            try:
                mg._setPlotAxesChannels(["<mov>", "<idx>"], [elements[1]])
                error = 1
            except:
                error = 0
            if error == 1:
                raise ValueError("PlotType spectrum should only accept one axis")
            try:
                mg._setPlotAxesChannels(["<mov>"], [elements[0]])
                error = 1
            except:
                error = 0
            if error == 1:
                raise ValueError("PlotType image should only accept two axis")

            print(mg._getPlotAxesChannels())
        finally:
            mg.cleanUp()
            self.pool.DeleteElement(mg_name)

    def testCtrlsTimer(self, elements=["_test_ct_1_1", "_test_ct_1_2", "_test_ct_1_3"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)
        try:
            mg = Device(mg_name)
            previous = mg._getCtrlsTimer()
            print(previous)
            mg._setCtrlsTimer(['_test_ct_1_3'])
            if mg._getCtrlsTimer() == previous:
                raise RuntimeError("setter function failed aplying changes")
            print(mg._getCtrlsTimer())

        finally:
            mg.cleanUp()
            self.pool.DeleteElement(mg_name)

    def testCtrlsMonitor(self, elements=["_test_ct_1_1", "_test_ct_1_2", "_test_ct_1_3"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)
        # TODO set method is missing a parameter (doesn't work as the description says)
        try:
            mg = Device(mg_name)
            previous = mg._getCtrlsMonitor()
            print(previous)
            mg._setCtrlsTimer(["_test_ct_1_2"])
            if mg._getCtrlsMonitor() == previous:
                raise RuntimeError("setter function failed aplying changes")
            print(mg._getCtrlsMonitor())

        finally:
            mg.cleanUp()
            self.pool.DeleteElement(mg_name)

    def testCtrlsSynchronization(self, elements=["_test_ct_1_1", "_test_ct_1_2", "_test_ct_1_3"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)
        try:
            mg = Device(mg_name)
            previous = mg._getCtrlsSynchronization()
            print(previous)
            mg._setCtrlsSynchronization('Gate')
            if mg._getCtrlsSynchronization() == previous:
                raise RuntimeError("setter function failed aplying changes")

            previous = mg._getCtrlsSynchronization()
            print(previous)
            mg._setCtrlsSynchronization('Trigger')
            if mg._getCtrlsSynchronization() == previous:
                raise RuntimeError("setter function failed aplying changes")

            previous = mg._getCtrlsSynchronization()
            print(previous)
            mg._setCtrlsSynchronization('Start')
            if mg._getCtrlsSynchronization() == previous:
                raise RuntimeError("setter function failed aplying changes")
            print(mg._getCtrlsSynchronization())

            try:
                mg._setCtrlsSynchronization('Software')
                error = 1
            except:
                error = 0
            if error == 1:
                raise ValueError("CtrlsSynchronization should only admit Gate/Trigger/Start")
            print(mg._getCtrlsSynchronization())

        finally:
            mg.cleanUp()
            self.pool.DeleteElement(mg_name)

    def testCtrlsSynchronizer(self, elements=["_test_ct_1_1", "_test_ct_1_2", "_test_ct_1_3"]):
        mg_name = str(uuid.uuid1())
        argin = [mg_name] + elements
        self.pool.CreateMeasurementGroup(argin)
        # TODO ERROR function doesn't accept triggergate
        try:
            mg = Device(mg_name)
            print(mg._getCtrlsSynchronizer())
            mg.setSynchronizer('software')
            print(mg._getCtrlsSynchronizer())
            mg.setSynchronizer('triggergate')
            print(mg._getCtrlsSynchronizer())

        finally:
            mg.cleanUp()
            self.pool.DeleteElement(mg_name)

if __name__ == '__main__':

    test = TestMeasurementGroupConfiguration()
    test.setUp()
    test.test_output()
    test.tearDown()
    # dev = taurus.Device("mntgrp/pool_test01_1/mntgrp03")
    # print(dev)
    # print(dev.getSynchronizer(ret_by_ctrl=True))
