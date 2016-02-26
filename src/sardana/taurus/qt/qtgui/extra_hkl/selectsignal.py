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
import PyQt4.Qt as Qt
from taurus.qt.qtgui.container import TaurusWidget
from taurus.qt.qtgui.base import TaurusBaseWidget
import time
import PyTango

import taurus.core


from PyQt4 import QtCore, QtGui

import taurus.core

from taurus.qt.qtgui.util.ui import UILoadable


class SignalComboBox(Qt.QComboBox, TaurusBaseWidget):
    """ComboBox representing list of possible signals"""

    def __init__(self, parent=None):
        name = self.__class__.__name__
        self.call__init__wo_kw(Qt.QComboBox, parent)
        self.call__init__(TaurusBaseWidget, name)
        self.setSizeAdjustPolicy(Qt.QComboBox.AdjustToContentsOnFirstShow)
        self.setToolTip("Choose a signal ...")
        QtCore.QMetaObject.connectSlotsByName(self)

    def loadSignals(self, signals):
        self.clear()
        self.addItems(signals)


@UILoadable(with_ui="_ui")
class SelectSignal(TaurusWidget):

    def __init__(self, parent=None, designMode=False):
        TaurusWidget.__init__(self, parent, designMode=designMode)

        self.loadUi(filename="selectsignal.ui")

        self.signalComboBox = SignalComboBox(self)
        self.signalComboBox.setGeometry(QtCore.QRect(70, 50, 161, 27))
        self.signalComboBox.setObjectName("SignalcomboBox")

        self.connect(self.signalComboBox, Qt.SIGNAL(
            "currentIndexChanged(QString)"), self.onSignalChanged)

        self.doorName = None
        self.door_device = None

    @classmethod
    def getQtDesignerPluginInfo(cls):
        ret = TaurusWidget.getQtDesignerPluginInfo()
        ret['module'] = 'selectsignal'
        ret['group'] = 'Taurus Containers'
        ret['container'] = ':/designer/frame.png'
        ret['container'] = False
        return ret

    def update_signals(self, doorname):
        if self.doorName != doorname:
            self.doorName = doorname
            self.door_device = taurus.Device(self.doorName)
            print "Create door_device with name " + str(self.doorName)

        if self.doorName != None:
            signals = []
            isig = 0
            macro_cmd = []
            macro_cmd.append("lsmeas")
            self.door_device.RunMacro(macro_cmd)
            while(self.door_device.State()) == PyTango.DevState.RUNNING:
                time.sleep(0.01)
            output_values = self.door_device.read_attribute("Output").value
            for line in output_values:
                if line.find('*') != -1:
                    for name in line.split(' '):
                        if name != '':
                            isig = isig + 1
                            if isig > 3:  # Don't add the asterik, the group name and the timer as timer
                                name = name.replace(',', '')
                                signals.append(name)

            self.signalComboBox.loadSignals(signals)

    def onSignalChanged(self, signalname):
        self._ui.SignallineEdit.setText(signalname)


def main():
    app = Qt.QApplication(sys.argv)
    w = SelectSignal()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
