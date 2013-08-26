# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/tmp/tmp3gTlTC.ui'
#
# Created: Fri Aug 16 12:19:03 2013
#      by: PyQt4 UI code generator 4.6.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_SelectSignal(object):
    def setupUi(self, SelectSignal):
        SelectSignal.setObjectName("SelectSignal")
        SelectSignal.resize(276, 201)
        self.label_signal = QtGui.QLabel(SelectSignal)
        self.label_signal.setGeometry(QtCore.QRect(50, 115, 51, 16))
        self.label_signal.setObjectName("label_signal")
        self.label_sampletime = QtGui.QLabel(SelectSignal)
        self.label_sampletime.setGeometry(QtCore.QRect(40, 160, 101, 16))
        self.label_sampletime.setObjectName("label_sampletime")
        self.SampleTimelineEdit = QtGui.QLineEdit(SelectSignal)
        self.SampleTimelineEdit.setGeometry(QtCore.QRect(150, 155, 81, 27))
        self.SampleTimelineEdit.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.SampleTimelineEdit.setObjectName("SampleTimelineEdit")
        self.line = QtGui.QFrame(SelectSignal)
        self.line.setGeometry(QtCore.QRect(10, 90, 251, 16))
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName("line")
        self.label_select = QtGui.QLabel(SelectSignal)
        self.label_select.setGeometry(QtCore.QRect(20, 20, 51, 16))
        self.label_select.setObjectName("label_select")
        self.SignallineEdit = QtGui.QLineEdit(SelectSignal)
        self.SignallineEdit.setGeometry(QtCore.QRect(120, 110, 111, 27))
        self.SignallineEdit.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.SignallineEdit.setObjectName("SignallineEdit")

        self.retranslateUi(SelectSignal)
        QtCore.QMetaObject.connectSlotsByName(SelectSignal)

    def retranslateUi(self, SelectSignal):
        SelectSignal.setWindowTitle(QtGui.QApplication.translate("SelectSignal", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label_signal.setText(QtGui.QApplication.translate("SelectSignal", "Signal:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_sampletime.setText(QtGui.QApplication.translate("SelectSignal", "Sample Time:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_select.setText(QtGui.QApplication.translate("SelectSignal", "Select:", None, QtGui.QApplication.UnicodeUTF8))

from taurus.qt.qtgui.container import TaurusWidget

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    SelectSignal = QtGui.TaurusWidget()
    ui = Ui_SelectSignal()
    ui.setupUi(SelectSignal)
    SelectSignal.show()
    sys.exit(app.exec_())

