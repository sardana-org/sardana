#!/usr/bin/env python

##############################################################################
##
## This file is part of Sardana
##
## http://www.sardana-controls.org/
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


__docformat__ = 'restructuredtext'

import sys
import time
from taurus.external.qt import Qt
# TODO: avoid using of PyTango - use Taurus instead
import PyTango
import sardana

from taurus.qt.qtgui.container import TaurusWidget
from taurus.qt.qtgui.display import TaurusLabel
from taurus.qt.qtgui.base import TaurusBaseWidget

from taurus.external.qt import QtCore, QtGui

from taurus.qt.qtcore.communication import SharedDataManager
from taurus.qt.qtgui.input import TaurusValueLineEdit


import taurus.core.util.argparse
import taurus.qt.qtgui.application
from taurus.qt.qtgui.util.ui import UILoadable

from sardana.taurus.qt.qtgui.extra_macroexecutor import TaurusMacroConfigurationDialog


from selectsignal import SelectSignal


class EngineModesComboBox(Qt.QComboBox, TaurusBaseWidget):
    """ComboBox representing list of engine modes"""

    def __init__(self, parent=None):
        name = self.__class__.__name__
        self.call__init__wo_kw(Qt.QComboBox, parent)
        self.call__init__(TaurusBaseWidget, name)
        self.setSizeAdjustPolicy(Qt.QComboBox.AdjustToContentsOnFirstShow)
        self.setToolTip("Choose a engine mode ...")
        QtCore.QMetaObject.connectSlotsByName(self)

    def loadEngineModeNames(self, enginemodes):
        self.clear()
        self.addItems(enginemodes)


@UILoadable(with_ui="_ui")
class DiffractometerAlignment(TaurusWidget):

    def __init__(self, parent=None, designMode=False):
        TaurusWidget.__init__(self, parent, designMode=designMode)

        self.loadUi(filename="diffractometeralignment.ui")

        self.selectsignal = SelectSignal()

        self.connect(self._ui.AlignmentStopButton,
                     Qt.SIGNAL("clicked()"), self.stop_movements)
        self.connect(self._ui.AlignmentStoreReflectionButton,
                     Qt.SIGNAL("clicked()"), self.store_reflection)

        self.connect(self._ui.MacroServerConnectionButton, Qt.SIGNAL(
            "clicked()"), self.open_macroserver_connection_panel)

        self.connect(self._ui.SelectSignalButton, Qt.SIGNAL(
            "clicked()"), self.open_selectsignal_panel)

        # Create a global SharedDataManager
        Qt.qApp.SDM = SharedDataManager(self)

    @classmethod
    def getQtDesignerPluginInfo(cls):
        ret = TaurusWidget.getQtDesignerPluginInfo()
        ret['module'] = 'diffractometeralignment'
        ret['group'] = 'Taurus Containers'
        ret['container'] = ':/designer/frame.png'
        ret['container'] = False
        return ret

    def setModel(self, model):
        if model != None:
            self.device = taurus.Device(model)

        self.pseudo_motor_names = []
        for motor in self.device.hklpseudomotorlist:
            self.pseudo_motor_names.append(motor.split(' ')[0])

        self.h_device_name = self.pseudo_motor_names[0]
        self.h_device = taurus.Device(self.h_device_name)
        self.k_device_name = self.pseudo_motor_names[1]
        self.k_device = taurus.Device(self.k_device_name)
        self.l_device_name = self.pseudo_motor_names[2]
        self.l_device = taurus.Device(self.l_device_name)

        # Set model to hkl components

        hmodel = self.h_device_name + "/Position"
        self._ui.taurusValueLineH.setModel(hmodel)
        self._ui.taurusLabelValueH.setModel(hmodel)
        kmodel = self.k_device_name + "/Position"
        self._ui.taurusValueLineK.setModel(kmodel)
        self._ui.taurusLabelValueK.setModel(kmodel)
        lmodel = self.l_device_name + "/Position"
        self._ui.taurusValueLineL.setModel(lmodel)
        self._ui.taurusLabelValueL.setModel(lmodel)

        # Add dynamically the angle widgets

        motor_list = self.device.motorlist
        self.motor_names = []
        self.motor_devices = []

        for motor in self.device.motorlist:
            self.motor_names.append(motor.split(' ')[0])
            self.motor_devices.append(taurus.Device(
                self.motor_names[len(self.motor_names) - 1]))

        self.nb_motors = len(motor_list)

        angles_labels = []
        self.angles_names = []
        angles_taurus_label = []
        angles_taurus_input = []

        gap_x = 650 / self.nb_motors

        try:
            self.angles_names = self.device.motorroles
        except:  # Only for compatibility
            if self.nb_motors == 4:
                self.angles_names.append("omega")
                self.angles_names.append("chi")
                self.angles_names.append("phi")
                self.angles_names.append("theta")
            elif self.nb_motors == 6:
                self.angles_names.append("mu")
                self.angles_names.append("th")
                self.angles_names.append("chi")
                self.angles_names.append("phi")
                self.angles_names.append("gamma")
                self.angles_names.append("delta")

        for i in range(0, self.nb_motors):
            angles_labels.append(QtGui.QLabel(self))
            angles_labels[i].setGeometry(
                QtCore.QRect(150 + gap_x * i, 40, 71, 17))
            angles_labels[i].setLayoutDirection(QtCore.Qt.RightToLeft)
            alname = "angleslabel" + str(i)
            angles_labels[i].setObjectName(alname)
            angles_labels[i].setText(QtGui.QApplication.translate(
                "HKLScan", self.angles_names[i], None,
                QtGui.QApplication.UnicodeUTF8))

            angles_taurus_label.append(TaurusLabel(self))
            angles_taurus_label[i].setGeometry(
                QtCore.QRect(150 + gap_x * i, 70, 81, 19))
            atlname = "anglestauruslabel" + str(i)
            angles_taurus_label[i].setObjectName(atlname)
            angles_taurus_label[i].setModel(self.motor_names[i] + "/Position")

            angles_taurus_input.append(TaurusValueLineEdit(self))
            angles_taurus_input[i].setGeometry(
                QtCore.QRect(145 + gap_x * i, 100, 91, 27))
            atlname = "anglestaurusinput" + str(i)
            angles_taurus_input[i].setObjectName(atlname)
            angles_taurus_input[i].setModel(self.motor_names[i] + "/Position")

        # Set model to engine and modes

        enginemodel = model + '/engine'
        self._ui.taurusLabelEngine.setModel(enginemodel)
        enginemodemodel = model + '/enginemode'
        self._ui.taurusLabelEngineMode.setModel(enginemodemodel)

        self.enginemodescombobox = EngineModesComboBox(self)
        self.enginemodescombobox.setGeometry(QtCore.QRect(150, 315, 221, 27))
        self.enginemodescombobox.setObjectName("enginemodeslist")

        self.enginemodescombobox.loadEngineModeNames(self.device.hklmodelist)

        self.connect(self.enginemodescombobox, Qt.SIGNAL(
            "currentIndexChanged(QString)"), self.onModeChanged)

        # Add dynamically the scan buttons, range inputs and 'to max' buttons

        scan_buttons = []
        self.range_inputs = []
        self.tomax_buttons = []  # The text will be change when the max. is computed

        exec_functions = [self.exec_scan1, self.exec_scan2, self.exec_scan3,
                          self.exec_scan4, self.exec_scan5, self.exec_scan6]

        tomax_functions = [self.tomax_scan1, self.tomax_scan2, self.tomax_scan3,
                           self.tomax_scan4, self.tomax_scan5, self.tomax_scan6]

        gap_x = 650 / self.nb_motors

        for i in range(0, self.nb_motors):
            scan_buttons.append(QtGui.QPushButton(self))
            scan_buttons[i].setGeometry(
                QtCore.QRect(150 + gap_x * i, 405, 100, 26))
            wname = "scanbutton" + str(i)
            scan_buttons[i].setObjectName(wname)
            scan_buttons[i].setText(QtGui.QApplication.translate(
                "DiffractometerAlignment", self.angles_names[i], None,
                QtGui.QApplication.UnicodeUTF8))
            self.connect(scan_buttons[i], Qt.SIGNAL(
                "clicked()"), exec_functions[i])

            self.range_inputs.append(QtGui.QLineEdit(self))
            self.range_inputs[i].setGeometry(
                QtCore.QRect(150 + gap_x * i, 440, 100, 26))
            self.range_inputs[i].setLayoutDirection(QtCore.Qt.RightToLeft)
            wname = "rangeinput" + str(i)
            self.range_inputs[i].setObjectName(wname)

            self.tomax_buttons.append(QtGui.QPushButton(self))
            self.tomax_buttons[i].setGeometry(
                QtCore.QRect(150 + gap_x * i, 475, 100, 26))
            wname = "tomaxbutton" + str(i)
            self.tomax_buttons[i].setObjectName(wname)
            self.tomax_buttons[i].setText(QtGui.QApplication.translate(
                "DiffractometerAlignment", 'n.n.', None,
                QtGui.QApplication.UnicodeUTF8))
            self.connect(self.tomax_buttons[i], Qt.SIGNAL(
                "clicked()"), tomax_functions[i])

    def exec_scan1(self):
        self.exec_scan(0)

    def exec_scan2(self):
        self.exec_scan(1)

    def exec_scan3(self):
        self.exec_scan(2)

    def exec_scan4(self):
        self.exec_scan(3)

    def exec_scan5(self):
        self.exec_scan(4)

    def exec_scan6(self):
        self.exec_scan(5)

    def exec_scan(self, imot):
        macro_command = []

        macro_command.append("_diff_scan")
        macro_command.append(str(self.motor_names[imot]))
        current_pos = self.motor_devices[imot].Position
        range_scan = float(self.range_inputs[imot].text())
        macro_command.append(str(current_pos - range_scan))
        macro_command.append(str(current_pos + range_scan))
        macro_command.append(str(self._ui.NbPointslineEdit.text()))
        macro_command.append(
            str(self.selectsignal._ui.SampleTimelineEdit.text()))
        macro_command.append(str(self.selectsignal._ui.SignallineEdit.text()))

        self.door_device.RunMacro(macro_command)
        while(self.door_device.State()) == PyTango.DevState.RUNNING:
            time.sleep(0.01)
        # TODO: the string parsing should be eliminated and the sardana
        # generic "goto_peak" feature should be used instead - when available
        output_values = self.door_device.read_attribute("Output").value
        if output_values != None:
            for i in range(len(output_values)):
                if output_values[i] == "Position to move":
                    self.tomax_buttons[imot].setText(QtGui.QApplication.translate(
                        "DiffractometerAlignment", str(output_values[i + 1]),
                        None, QtGui.QApplication.UnicodeUTF8))

    def tomax_scan1(self):
        self.tomax_scan(0)

    def tomax_scan2(self):
        self.tomax_scan(1)

    def tomax_scan3(self):
        self.tomax_scan(2)

    def tomax_scan4(self):
        self.tomax_scan(3)

    def tomax_scan5(self):
        self.tomax_scan(4)

    def tomax_scan6(self):
        self.tomax_scan(5)

    def tomax_scan(self, imot):
        motor = str(self.motor_names[imot])
        position = str(self.tomax_buttons[imot].text())
        macro_command = ["mv", motor, position]
        self.door_device.RunMacro(macro_command)

    def onModeChanged(self, modename):
        if self.device.engine != "hkl":
            self.device.write_attribute("engine", "hkl")
        self.device.write_attribute("enginemode", str(modename))

    def open_macroserver_connection_panel(self):
        w = TaurusMacroConfigurationDialog(self)
        Qt.qApp.SDM.connectReader("macroserverName", w.selectMacroServer)
        Qt.qApp.SDM.connectReader("doorName", w.selectDoor)
        Qt.qApp.SDM.connectReader("doorName", self.onDoorChanged)
        Qt.qApp.SDM.connectWriter(
            "macroserverName", w, 'macroserverNameChanged')
        Qt.qApp.SDM.connectWriter("doorName", w, 'doorNameChanged')

        w.show()

    def onDoorChanged(self, doorName):
        if doorName != self.door_device_name:
            self.door_device_name = doorName
            self.door_device = taurus.Device(doorName)

    def stop_movements(self):
        self.door_device.StopMacro()

    def store_reflection(self):
        hklref = []
        hklref.append(self.h_device.Position)
        hklref.append(self.k_device.Position)
        hklref.append(self.l_device.Position)

        self.device.write_attribute("addreflection", hklref)

    def open_selectsignal_panel(self):

        self.selectsignal.update_signals(self.door_device_name)
        self.selectsignal.show()


def main():

    parser = taurus.core.util.argparse.get_taurus_parser()
    parser.usage = "%prog <model> [door_name]"
    desc = ("a taurus application for diffractometer alignment: h, k, l " +
            "movements and scans, go to maximum, ...")
    parser.set_description(desc)

    app = taurus.qt.qtgui.application.TaurusApplication(cmd_line_parser=parser,
            app_version=sardana.Release.version)
    app.setApplicationName("diffractometeralignment")
    args = app.get_command_line_args()
    if len(args) < 1:
        msg = "model not set (requires diffractometer controller)"
        parser.error(msg)

    w = DiffractometerAlignment()
    w.model = args[0]
    w.setModel(w.model)

    w.door_device = None
    w.door_device_name = None
    if len(args) > 1:
        w.onDoorChanged(args[1])
    else:
        msg = ("No door name supplied. Connection to MacroServer/Door will " +
               "not not automatically done.")
        app.warning(msg)

    w.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
