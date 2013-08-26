# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/tmp/tmp6Nqu9Q.ui'
#
# Created: Wed Aug  7 10:19:38 2013
#      by: PyQt4 UI code generator 4.6.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_DisplayScanAngles(object):
    def setupUi(self, DisplayScanAngles):
        DisplayScanAngles.setObjectName("DisplayScanAngles")
        DisplayScanAngles.resize(856, 279)
        self.label = QtGui.QLabel(DisplayScanAngles)
        self.label.setGeometry(QtCore.QRect(40, 20, 161, 17))
        self.label.setObjectName("label")

        self.retranslateUi(DisplayScanAngles)
        QtCore.QMetaObject.connectSlotsByName(DisplayScanAngles)

    def retranslateUi(self, DisplayScanAngles):
        DisplayScanAngles.setWindowTitle(QtGui.QApplication.translate("DisplayScanAngles", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("DisplayScanAngles", "Angles during the scan", None, QtGui.QApplication.UnicodeUTF8))

from taurus.qt.qtgui.container import TaurusWidget

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    DisplayScanAngles = QtGui.TaurusWidget()
    ui = Ui_DisplayScanAngles()
    ui.setupUi(DisplayScanAngles)
    DisplayScanAngles.show()
    sys.exit(app.exec_())

