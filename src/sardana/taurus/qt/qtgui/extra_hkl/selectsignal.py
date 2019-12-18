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
from taurus.qt.qtgui.container import TaurusWidget
from taurus.qt.qtgui.base import TaurusBaseWidget
import time
import PyTango

import taurus.core

from taurus.external.qt import QtCore, QtGui

from taurus.qt.qtgui.util.ui import UILoadable

from sardana.taurus.core.tango.sardana.macroserver import registerExtensions


class SignalComboBox(Qt.QComboBox, TaurusBaseWidget):
    """ComboBox representing list of possible signals"""

    def __init__(self, parent=None):
        name = self.__class__.__name__
        self.call__init__wo_kw(Qt.QComboBox, parent)
        self.call__init__(TaurusBaseWidget, name='')
        self.setSizeAdjustPolicy(Qt.QComboBox.AdjustToContentsOnFirstShow)
        self.setToolTip("Choose a signal ...")
        QtCore.QMetaObject.connectSlotsByName(self)

    def loadSignals(self, signals):
        self.clear()
        self.addItems(signals)


@UILoadable(with_ui="_ui")
class SelectSignal(TaurusWidget):

    def __init__(self, parent=None, designMode=False):
        TaurusWidget.__init__(self, parent=None, designMode=designMode)

        self.loadUi(filename="selectsignal.ui")

        self.signalComboBox = SignalComboBox(self)
        self.signalComboBox.setGeometry(QtCore.QRect(70, 50, 161, 27))
        self.signalComboBox.setObjectName("SignalcomboBox")

        self.signalComboBox.currentIndexChanged['QString'].connect(
            self.onSignalChanged)

        self.doorName = None
        self.door_device = None

        registerExtensions()

    @classmethod
    def getQtDesignerPluginInfo(cls):
        ret = TaurusWidget.getQtDesignerPluginInfo()
        ret['module'] = 'selectsignal'
        ret['group'] = 'Taurus Containers'
        ret['container'] = ':/designer/frame.png'
        ret['container'] = False
        return ret

    def update_signals(self, doorname=''):
        if self.doorName != doorname:
            self.doorName = doorname
            self.door_device = taurus.Device(self.doorName)
            print("Create door_device with name " + str(self.doorName))

        if self.doorName is not None:
            signals = []
            conf = self.door_device.getExperimentConfiguration()
            mg_name = conf['ActiveMntGrp']
            mg = taurus.Device(mg_name)
            signals = mg.ElementList
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
