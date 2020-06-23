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

import sys

import sardana
from taurus.external.qt import Qt
from taurus.qt.qtgui.container import TaurusWidget
from taurus.qt.qtgui.display import TaurusLabel
from taurus.qt.qtgui.base import TaurusBaseWidget

from taurus.external.qt import QtCore, QtGui

import taurus.core
from taurus.qt.qtcore.communication import SharedDataManager
from taurus.qt.qtgui.input import TaurusValueLineEdit

from .displayscanangles import DisplayScanAngles

import taurus.core.util.argparse
import taurus.qt.qtgui.application
from taurus.qt.qtgui.util.ui import UILoadable

from PyTango import *
from sardana.taurus.qt.qtgui.extra_macroexecutor import TaurusMacroExecutorWidget, TaurusSequencerWidget, \
    TaurusMacroConfigurationDialog, \
    TaurusMacroDescriptionViewer, DoorOutput, DoorDebug, DoorResult

__docformat__ = 'restructuredtext'


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
class HKLScan(TaurusWidget):

    def __init__(self, parent=None, designMode=False):
        TaurusWidget.__init__(self, parent, designMode=designMode)

        self.loadUi(filename="hklscan.ui")

        self._ui.hklStartScanButton.clicked.connect(self.start_hklscan)
        self._ui.hklStopScanButton.clicked.connect(self.stop_hklscan)
        self._ui.hklDisplayAnglesButton.clicked.connect(self.display_angles)
        self._ui.MacroServerConnectionButton.clicked.connect(
            self.open_macroserver_connection_panel)

        # Create a global SharedDataManager
        Qt.qApp.SDM = SharedDataManager(self)

    @classmethod
    def getQtDesignerPluginInfo(cls):
        ret = TaurusWidget.getQtDesignerPluginInfo()
        ret['module'] = 'hklscan'
        ret['group'] = 'Taurus Containers'
        ret['container'] = ':/designer/frame.png'
        ret['container'] = True
        return ret

    def setModel(self, model):
        if model is not None:
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

        # Add dynamically the angle widgets

        motor_list = self.device.motorlist
        motor_names = []
        for motor in self.device.motorlist:
            motor_names.append(motor.split(' ')[0])

        self.nb_motors = len(motor_list)

        angles_labels = []
        angles_names = []
        angles_taurus_label = []

        gap_x = 800 // self.nb_motors

        try:
            angles_names = self.device.motorroles
        except:  # Only for compatibility
            if self.nb_motors == 4:
                angles_names.append("omega")
                angles_names.append("chi")
                angles_names.append("phi")
                angles_names.append("theta")
            elif self.nb_motors == 6:
                angles_names.append("mu")
                angles_names.append("th")
                angles_names.append("chi")
                angles_names.append("phi")
                angles_names.append("gamma")
                angles_names.append("delta")

        for i in range(0, self.nb_motors):
            angles_labels.append(QtGui.QLabel(self))
            angles_labels[i].setGeometry(
                QtCore.QRect(50 + gap_x * i, 290, 51, 17))
            alname = "angleslabel" + str(i)
            angles_labels[i].setObjectName(alname)
            angles_labels[i].setText(QtGui.QApplication.translate(
                "HKLScan", angles_names[i], None))
            angles_taurus_label.append(TaurusLabel(self))
            angles_taurus_label[i].setGeometry(
                QtCore.QRect(50 + gap_x * i, 320, 81, 19))
            atlname = "anglestauruslabel" + str(i)
            angles_taurus_label[i].setObjectName(atlname)
            angles_taurus_label[i].setModel(motor_names[i] + "/Position")

        # Set model to hkl display

        hmodel = self.h_device_name + "/Position"
        self._ui.taurusValueLineH.setModel(hmodel)
        self._ui.taurusLabelValueH.setModel(hmodel)
        kmodel = self.k_device_name + "/Position"
        self._ui.taurusValueLineK.setModel(kmodel)
        self._ui.taurusLabelValueK.setModel(kmodel)
        lmodel = self.l_device_name + "/Position"
        self._ui.taurusValueLineL.setModel(lmodel)
        self._ui.taurusLabelValueL.setModel(lmodel)

        # Set model to engine and modes

        enginemodel = model + '/engine'
        self._ui.taurusLabelEngine.setModel(enginemodel)
        enginemodemodel = model + '/enginemode'
        self._ui.taurusLabelEngineMode.setModel(enginemodemodel)

        self.enginemodescombobox = EngineModesComboBox(self)
        self.enginemodescombobox.setGeometry(QtCore.QRect(150, 445, 221, 27))
        self.enginemodescombobox.setObjectName("enginemodeslist")

        self.enginemodescombobox.loadEngineModeNames(self.device.hklmodelist)

        self.enginemodescombobox.currentIndexChanged['QString'].connect(
            self.onModeChanged)

    @Qt.pyqtSlot('QString')
    def onModeChanged(self, modename):
        if self.device.engine != "hkl":
            self.device.write_attribute("engine", "hkl")
        self.device.write_attribute("enginemode", str(modename))

    def start_hklscan(self):
        start_hkl = []
        stop_hkl = []
        start_hkl.append(float(self._ui.lineEditStartH.text()))
        start_hkl.append(float(self._ui.lineEditStartK.text()))
        start_hkl.append(float(self._ui.lineEditStartL.text()))
        stop_hkl.append(float(self._ui.lineEditStopH.text()))
        stop_hkl.append(float(self._ui.lineEditStopK.text()))
        stop_hkl.append(float(self._ui.lineEditStopL.text()))
        nb_points = int(self._ui.LineEditNbpoints.text())
        sample_time = float(self._ui.LineEditSampleTime.text())
        dim = 0
        macro_name = ["ascan", "a2scan", "a3scan"]
        macro_command = []
        index_to_scan = []
        if self.door_device is not None:
            for i in range(0, 3):
                if start_hkl[i] != stop_hkl[i]:
                    dim = dim + 1
                    index_to_scan.append(i)
            if dim > 0:
                macro_command.append(macro_name[dim - 1])
                for i in range(len(index_to_scan)):
                    macro_command.append(
                        str(self.pseudo_motor_names[index_to_scan[i]]))
                    macro_command.append(str(start_hkl[index_to_scan[i]]))
                    macro_command.append(str(stop_hkl[index_to_scan[i]]))
                macro_command.append(str(nb_points))
                macro_command.append(str(sample_time))
                self.door_device.RunMacro(macro_command)

    def stop_hklscan(self):
        self.door_device.StopMacro()

    def display_angles(self):

        xangle = []
        for i in range(0, 6):
            xangle.append(40 + i * 100)

        yhkl = 50

        tr = self.device.selectedtrajectory

        w = DisplayScanAngles()

        angles_labels = []
        angles_names = []

        if self.nb_motors == 4:
            angles_names.append("omega")
            angles_names.append("chi")
            angles_names.append("phi")
            angles_names.append("theta")
        elif self.nb_motors == 6:
            angles_names.append("mu")
            angles_names.append("th")
            angles_names.append("chi")
            angles_names.append("phi")
            angles_names.append("gamma")
            angles_names.append("delta")

        dsa_label = []
        for i in range(0, self.nb_motors):
            dsa_label.append(QtGui.QLabel(w))
            dsa_label[i].setGeometry(QtCore.QRect(xangle[i], yhkl, 51, 20))
            label_name = "dsa_label_" + str(i)
            dsa_label[i].setObjectName(label_name)
            dsa_label[i].setText(QtGui.QApplication.translate(
                "Form", angles_names[i], None))

        start_hkl = []
        stop_hkl = []
        missed_values = 0
        # TODO: This code will raise exception if one of the line edits is empty.
        # But not all dimensions (H & K & L) are obligatory. One could try
        # to display angles of just 1 or 2 dimensional scan.
        try:
            start_hkl.append(float(self._ui.lineEditStartH.text()))
            start_hkl.append(float(self._ui.lineEditStartK.text()))
            start_hkl.append(float(self._ui.lineEditStartL.text()))
            stop_hkl.append(float(self._ui.lineEditStopH.text()))
            stop_hkl.append(float(self._ui.lineEditStopK.text()))
            stop_hkl.append(float(self._ui.lineEditStopL.text()))
            nb_points = int(self._ui.LineEditNbpoints.text())
        except:
            nb_points = -1
            missed_values = 1

        increment_hkl = []

        if nb_points > 0:
            for i in range(0, 3):
                increment_hkl.append((stop_hkl[i] - start_hkl[i]) / nb_points)

        taurusValueAngle = []

        for i in range(0, nb_points + 1):
            hkl_temp = []
            for j in range(0, 3):
                hkl_temp.append(start_hkl[j] + i * increment_hkl[j])

            no_trajectories = 0
            try:
                self.device.write_attribute("computetrajectoriessim", hkl_temp)
            except:
                no_trajectories = 1

            if not no_trajectories:

                angles_list = self.device.trajectorylist[tr]

                taurusValueAngle.append([])

                for iangle in range(0, self.nb_motors):
                    taurusValueAngle[i].append(TaurusValueLineEdit(w))
                    taurusValueAngle[i][iangle].setGeometry(
                        QtCore.QRect(xangle[iangle], yhkl + 30 * (i + 1), 80, 27))
                    taurusValueAngle[i][iangle].setReadOnly(True)
                    tva_name = "taurusValueAngle" + str(i) + "_" + str(iangle)
                    taurusValueAngle[i][iangle].setObjectName(tva_name)
                    taurusValueAngle[i][iangle].setValue(
                        "%10.4f" % angles_list[iangle])
            else:
                taurusValueAngle.append(TaurusValueLineEdit(w))
                taurusValueAngle[i].setGeometry(QtCore.QRect(
                    xangle[0], yhkl + 30 * (i + 1), self.nb_motors * 120, 27))
                taurusValueAngle[i].setReadOnly(True)
                tva_name = "taurusValueAngle" + str(i)
                taurusValueAngle[i].setObjectName(tva_name)
                taurusValueAngle[i].setValue(
                    "...                             No angle solution for hkl values                             ...")
        # TODO: not all dimensions (H & K & L) are obligatory. One could try
        # to display angles of just 1 or 2 dimensional scan.
        if nb_points == -1:
            nb_points = 0
            taurusValueAngle.append(TaurusValueLineEdit(w))
            taurusValueAngle[0].setGeometry(QtCore.QRect(
                xangle[0], yhkl + 30, self.nb_motors * 120, 27))
            taurusValueAngle[0].setReadOnly(True)
            tva_name = "taurusValueAngle"
            taurusValueAngle[0].setObjectName(tva_name)
            taurusValueAngle[0].setValue(
                "...          No scan parameters filled. Fill them in the main window         ...")

        w.resize(self.nb_motors * 140, 120 + nb_points * 40)

        w.show()
        w.show()

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


def main():

    parser = taurus.core.util.argparse.get_taurus_parser()
    parser.usage = "%prog  <model> [door_name]"
    parser.set_description("a taurus application for performing hkl scans")

    app = taurus.qt.qtgui.application.TaurusApplication(
        cmd_line_parser=parser, app_version=sardana.Release.version)
    app.setApplicationName("hklscan")
    args = app.get_command_line_args()
    if len(args) < 1:
        msg = "model not set (requires diffractometer controller)"
        parser.error(msg)

    w = HKLScan()
    w.model = args[0]
    w.setModel(w.model)

    w.door_device = None
    w.door_device_name = None
    if len(args) > 1:
        w.onDoorChanged(args[1])
    else:
        print("WARNING: Not door name supplied. Connection to "
              "MacroServer/Door not automatically done")
    w.show()

    sys.exit(app.exec_())

 #   if len(sys.argv)>1: model=sys.argv[1]
 #   else: model = None
 #   app = Qt.QApplication(sys.argv)
 #   w = HKLScan()
 #   w.setModel(model)
 #   w.show()
 #   sys.exit(app.exec_())

if __name__ == "__main__":
    main()
