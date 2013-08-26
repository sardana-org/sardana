# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/tmp/tmp7dATXr.ui'
#
# Created: Fri Aug  9 10:58:33 2013
#      by: PyQt4 UI code generator 4.6.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_ReflectionsEditor(object):
    def setupUi(self, ReflectionsEditor):
        ReflectionsEditor.setObjectName("ReflectionsEditor")
        ReflectionsEditor.resize(801, 437)
        self.rl_label1 = QtGui.QLabel(ReflectionsEditor)
        self.rl_label1.setGeometry(QtCore.QRect(20, 20, 36, 17))
        self.rl_label1.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.rl_label1.setObjectName("rl_label1")
        self.rl_label1_2 = QtGui.QLabel(ReflectionsEditor)
        self.rl_label1_2.setGeometry(QtCore.QRect(105, 20, 36, 17))
        self.rl_label1_2.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.rl_label1_2.setObjectName("rl_label1_2")
        self.rl_label1_3 = QtGui.QLabel(ReflectionsEditor)
        self.rl_label1_3.setGeometry(QtCore.QRect(190, 20, 36, 17))
        self.rl_label1_3.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.rl_label1_3.setObjectName("rl_label1_3")
        self.rl_label1_4 = QtGui.QLabel(ReflectionsEditor)
        self.rl_label1_4.setGeometry(QtCore.QRect(260, 20, 36, 17))
        self.rl_label1_4.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.rl_label1_4.setObjectName("rl_label1_4")
        self.ApplyButton = QtGui.QPushButton(ReflectionsEditor)
        self.ApplyButton.setGeometry(QtCore.QRect(380, 390, 106, 26))
        self.ApplyButton.setObjectName("ApplyButton")
        self.ClearButton = QtGui.QPushButton(ReflectionsEditor)
        self.ClearButton.setGeometry(QtCore.QRect(250, 390, 106, 26))
        self.ClearButton.setObjectName("ClearButton")

        self.retranslateUi(ReflectionsEditor)
        QtCore.QMetaObject.connectSlotsByName(ReflectionsEditor)

    def retranslateUi(self, ReflectionsEditor):
        ReflectionsEditor.setWindowTitle(QtGui.QApplication.translate("ReflectionsEditor", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.rl_label1.setText(QtGui.QApplication.translate("ReflectionsEditor", "Index", None, QtGui.QApplication.UnicodeUTF8))
        self.rl_label1_2.setText(QtGui.QApplication.translate("ReflectionsEditor", "H", None, QtGui.QApplication.UnicodeUTF8))
        self.rl_label1_3.setText(QtGui.QApplication.translate("ReflectionsEditor", "K", None, QtGui.QApplication.UnicodeUTF8))
        self.rl_label1_4.setText(QtGui.QApplication.translate("ReflectionsEditor", "L", None, QtGui.QApplication.UnicodeUTF8))
        self.ApplyButton.setText(QtGui.QApplication.translate("ReflectionsEditor", "Apply", None, QtGui.QApplication.UnicodeUTF8))
        self.ClearButton.setText(QtGui.QApplication.translate("ReflectionsEditor", "Clear", None, QtGui.QApplication.UnicodeUTF8))

from taurus.qt.qtgui.container import TaurusWidget

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ReflectionsEditor = QtGui.TaurusWidget()
    ui = Ui_ReflectionsEditor()
    ui.setupUi(ReflectionsEditor)
    ReflectionsEditor.show()
    sys.exit(app.exec_())

