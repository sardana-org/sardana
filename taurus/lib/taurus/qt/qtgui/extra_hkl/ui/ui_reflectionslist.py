# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/tmp/tmpGF5Pmi.ui'
#
# Created: Tue Aug 13 13:03:38 2013
#      by: PyQt4 UI code generator 4.6.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_ReflectionsList(object):
    def setupUi(self, ReflectionsList):
        ReflectionsList.setObjectName("ReflectionsList")
        ReflectionsList.resize(912, 167)
        self.ReflectionsListLabel = QtGui.QLabel(ReflectionsList)
        self.ReflectionsListLabel.setGeometry(QtCore.QRect(40, 20, 98, 17))
        self.ReflectionsListLabel.setObjectName("ReflectionsListLabel")
        self.rl_label1 = QtGui.QLabel(ReflectionsList)
        self.rl_label1.setGeometry(QtCore.QRect(20, 70, 36, 17))
        self.rl_label1.setObjectName("rl_label1")
        self.rl_label1_2 = QtGui.QLabel(ReflectionsList)
        self.rl_label1_2.setGeometry(QtCore.QRect(120, 70, 16, 17))
        self.rl_label1_2.setObjectName("rl_label1_2")
        self.rl_label1_3 = QtGui.QLabel(ReflectionsList)
        self.rl_label1_3.setGeometry(QtCore.QRect(195, 70, 16, 17))
        self.rl_label1_3.setObjectName("rl_label1_3")
        self.rl_label1_4 = QtGui.QLabel(ReflectionsList)
        self.rl_label1_4.setGeometry(QtCore.QRect(275, 70, 16, 17))
        self.rl_label1_4.setObjectName("rl_label1_4")
        self.rl_label1_5 = QtGui.QLabel(ReflectionsList)
        self.rl_label1_5.setGeometry(QtCore.QRect(330, 70, 41, 20))
        self.rl_label1_5.setObjectName("rl_label1_5")
        self.rl_label1_6 = QtGui.QLabel(ReflectionsList)
        self.rl_label1_6.setGeometry(QtCore.QRect(390, 70, 41, 20))
        self.rl_label1_6.setObjectName("rl_label1_6")

        self.retranslateUi(ReflectionsList)
        QtCore.QMetaObject.connectSlotsByName(ReflectionsList)

    def retranslateUi(self, ReflectionsList):
        ReflectionsList.setWindowTitle(QtGui.QApplication.translate("ReflectionsList", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.ReflectionsListLabel.setText(QtGui.QApplication.translate("ReflectionsList", "Reflections List", None, QtGui.QApplication.UnicodeUTF8))
        self.rl_label1.setText(QtGui.QApplication.translate("ReflectionsList", "Index", None, QtGui.QApplication.UnicodeUTF8))
        self.rl_label1_2.setText(QtGui.QApplication.translate("ReflectionsList", "H", None, QtGui.QApplication.UnicodeUTF8))
        self.rl_label1_3.setText(QtGui.QApplication.translate("ReflectionsList", "K", None, QtGui.QApplication.UnicodeUTF8))
        self.rl_label1_4.setText(QtGui.QApplication.translate("ReflectionsList", "L", None, QtGui.QApplication.UnicodeUTF8))
        self.rl_label1_5.setText(QtGui.QApplication.translate("ReflectionsList", "Relev.", None, QtGui.QApplication.UnicodeUTF8))
        self.rl_label1_6.setText(QtGui.QApplication.translate("ReflectionsList", "Aff.", None, QtGui.QApplication.UnicodeUTF8))

from taurus.qt.qtgui.container import TaurusWidget

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ReflectionsList = QtGui.TaurusWidget()
    ui = Ui_ReflectionsList()
    ui.setupUi(ReflectionsList)
    ReflectionsList.show()
    sys.exit(app.exec_())

