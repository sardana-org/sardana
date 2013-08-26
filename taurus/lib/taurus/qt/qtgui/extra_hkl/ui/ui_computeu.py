# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/tmp/tmpelhJop.ui'
#
# Created: Wed Aug  7 12:35:40 2013
#      by: PyQt4 UI code generator 4.6.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_ComputeU(object):
    def setupUi(self, ComputeU):
        ComputeU.setObjectName("ComputeU")
        ComputeU.resize(400, 157)
        self.ComputeButton = QtGui.QPushButton(ComputeU)
        self.ComputeButton.setGeometry(QtCore.QRect(140, 120, 106, 26))
        self.ComputeButton.setObjectName("ComputeButton")
        self.label = QtGui.QLabel(ComputeU)
        self.label.setGeometry(QtCore.QRect(20, 20, 231, 17))
        self.label.setObjectName("label")
        self.indexreflection1lineEdit = QtGui.QLineEdit(ComputeU)
        self.indexreflection1lineEdit.setGeometry(QtCore.QRect(70, 60, 81, 27))
        self.indexreflection1lineEdit.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.indexreflection1lineEdit.setObjectName("indexreflection1lineEdit")
        self.indexreflection2lineEdit = QtGui.QLineEdit(ComputeU)
        self.indexreflection2lineEdit.setGeometry(QtCore.QRect(240, 60, 81, 27))
        self.indexreflection2lineEdit.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.indexreflection2lineEdit.setObjectName("indexreflection2lineEdit")

        self.retranslateUi(ComputeU)
        QtCore.QMetaObject.connectSlotsByName(ComputeU)

    def retranslateUi(self, ComputeU):
        ComputeU.setWindowTitle(QtGui.QApplication.translate("ComputeU", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.ComputeButton.setText(QtGui.QApplication.translate("ComputeU", "Compute", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("ComputeU", "Use reflections (select by index):", None, QtGui.QApplication.UnicodeUTF8))

from taurus.qt.qtgui.container import TaurusWidget

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ComputeU = QtGui.TaurusWidget()
    ui = Ui_ComputeU()
    ui.setupUi(ComputeU)
    ComputeU.show()
    sys.exit(app.exec_())

