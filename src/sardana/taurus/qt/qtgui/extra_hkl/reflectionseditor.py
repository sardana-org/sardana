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

__docformat__ = 'restructuredtext'

import sys
from taurus.external.qt import Qt
import taurus.core
from taurus.qt.qtgui.container import TaurusWidget
from taurus.qt.qtgui.input import TaurusValueLineEdit

from taurus.external.qt import QtCore, QtGui

from taurus.qt.qtgui.util.ui import UILoadable


@UILoadable(with_ui="_ui")
class ReflectionsEditor(TaurusWidget):

    def __init__(self, parent=None, designMode=False):
        TaurusWidget.__init__(self, parent, designMode=designMode)

        self.loadUi(filename="reflectionseditor.ui")

        self._ui.ApplyButton.clicked.connect(self.apply)
        self._ui.ClearButton.clicked.connect(self.clear)

    @classmethod
    def getQtDesignerPluginInfo(cls):
        ret = TaurusWidget.getQtDesignerPluginInfo()
        ret['module'] = 'reflectionseditor'
        ret['group'] = 'Taurus Containers'
        ret['container'] = ':/designer/frame.png'
        ret['container'] = False
        return ret

    def setModel(self, model):
        if model is not None:
            self.device = taurus.Device(model)

        xhkl = []
        xangles = []
        xlabels = []
        for i in range(0, 6):
            xhkl.append(70 + 80 * i)
            xangles.append(310 + 80 * i)
            xlabels.append(340 + 90 * i)
        ybasis = 20

        reflections = self.device.reflectionlist

        angle_names = []
        self.angle_labels = []
        self.hkl_values = []
        self.angle_values = []
        self.index_values = []

        # Find number of real motors
        self.nb_angles = len(self.device.motorlist)

        if reflections is not None:
            self.nb_reflections = len(reflections)
        else:
            self.nb_reflections = 0

        try:
            angle_names = self.device.motorroles
        except:  # Only for compatibility
            if self.nb_angles == 4:
                angle_names.append("omega")
                angle_names.append("chi")
                angle_names.append("phi")
                angle_names.append("tth")
            elif self.nb_angles == 6:
                angle_names.append("mu")
                angle_names.append("th")
                angle_names.append("chi")
                angle_names.append("phi")
                angle_names.append("gamma")
                angle_names.append("delta")

        for jref in range(0, 10):
            self.index_values.append(QtGui.QLineEdit(self))
            self.index_values[jref].setLayoutDirection(QtCore.Qt.RightToLeft)
            self.index_values[jref].setGeometry(
                QtCore.QRect(20, ybasis + 30 * (jref + 1), 51, 27))
            object_name = "indexvalue" + str(jref)
            self.index_values[jref].setObjectName(object_name)

        for i in range(0, 3):
            self.hkl_values.append([])
            for jref in range(0, 10):
                self.hkl_values[i].append(QtGui.QLineEdit(self))
                self.hkl_values[i][jref].setLayoutDirection(
                    QtCore.Qt.RightToLeft)
                self.hkl_values[i][jref].setGeometry(
                    QtCore.QRect(xhkl[i], ybasis + 30 * (jref + 1), 81, 27))
                object_name = "hklvalue" + str(i) + "_" + str(jref)
                self.hkl_values[i][jref].setObjectName(object_name)

        for i in range(0, self.nb_angles):
            self.angle_labels.append(QtGui.QLabel(self))
            self.angle_labels[i].setGeometry(
                QtCore.QRect(xangles[i], ybasis, 70, 20))
            self.angle_labels[i].setLayoutDirection(QtCore.Qt.RightToLeft)
            object_name = "anglelabel" + str(i)
            self.angle_labels[i].setObjectName(object_name)
            self.angle_labels[i].setText(QtGui.QApplication.translate(
                "Form", angle_names[i], None))
            self.angle_values.append([])
            for jref in range(0, 10):
                self.angle_values[i].append(QtGui.QLineEdit(self))
                self.angle_values[i][jref].setLayoutDirection(
                    QtCore.Qt.RightToLeft)
                self.angle_values[i][jref].setGeometry(QtCore.QRect(
                    xangles[i], ybasis + 30 * (jref + 1), 81, 27))
                object_name = "anglevalue" + str(i) + "_" + str(jref)
                self.angle_values[i][jref].setObjectName(object_name)

        for jref in range(0, self.nb_reflections):
            ref = reflections[jref]
            # Fill index
            self.index_values[jref].setText(str(jref))
            # Fill hkl values
            for i in range(0, 3):
                self.hkl_values[i][jref].setText(
                    ("%12.4f" % ref[i + 1]).strip())
            # Fill the angle values
            for i in range(0, self.nb_angles):
                self.angle_values[i][jref].setText(
                    ("%12.4f" % ref[i + 6]).strip())

    def apply(self):
        # Get the values for the new reflections
        hklnew = []
        anglesnew = []
        indexnew = []
        iref_hkl = []
        iref_angles = []
        for jref in range(0, 10):
            hklnew.append([])
            anglesnew.append([])
            try:
                indexnew.append(int(self.index_values[jref].text()))
            except:
                indexnew.append(-1)
            icount = 0
            for ihkl in range(0, 3):
                try:
                    hklnew[jref].append(
                        float(self.hkl_values[ihkl][jref].text()))
                    icount = icount + 1
                except:
                    hklnew[jref].append('')
            iref_hkl.append(icount)
            icount = 0
            for iangle in range(0, self.nb_angles):
                try:
                    anglesnew[jref].append(
                        float(self.angle_values[iangle][jref].text()))
                    icount = icount + 1
                except:
                    anglesnew[jref].append('')
            iref_angles.append(icount)

        # Remove all reflections
        if self.device.reflectionlist is not None:
            self.nb_reflections = len(self.device.reflectionlist)
        else:
            self.nb_reflections = 0
        for i in range(0, self.nb_reflections):
            # The index is reset after removing, so we remove always the first
            # one
            self.device.write_attribute("removereflection", 0)

        # Create reflections (always with current angles attached)
        for jref in range(0, 10):
            for iref in range(0, 10):
                if indexnew[jref] == iref:
                    self.index_values[jref].setText(str(jref))
                    if iref_hkl[iref] == 3:
                        self.device.write_attribute(
                            "addreflection", hklnew[iref])
                # Set the angles if given
                    if iref_angles[iref] == self.nb_angles:
                        cmd = []
                        cmd.append(iref)
                        for i in range(0, self.nb_angles):
                            cmd.append(anglesnew[iref][i])
                        self.device.write_attribute(
                            "adjustanglestoreflection", cmd)

        self.clear()

    def clear(self):
        reflections = self.device.reflectionlist

        # Clean the values
        for jref in range(0, 10):
            # Fill hkl values
            for i in range(0, 3):
                self.hkl_values[i][jref].setText('')
            # Fill the angle values
            for i in range(0, self.nb_angles):
                self.angle_values[i][jref].setText('')

        # Add the reflections
        if reflections is not None:
            self.nb_reflections = len(reflections)
            for jref in range(0, len(reflections)):
                # Fill the index
                self.index_values[jref].setText(str(jref))
                ref = reflections[jref]
                # Fill hkl values
                for i in range(0, 3):
                    self.hkl_values[i][jref].setText(
                        ("%12.4f" % ref[i + 1]).strip())
                # Fill the angle values
                for i in range(0, self.nb_angles):
                    self.angle_values[i][jref].setText(
                        ("%12.4f" % ref[i + 6]).strip())
        else:
            self.nb_reflections = 0


def main():
    app = Qt.QApplication(sys.argv)
    w = ReflectionsEditor()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
