# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mg_gui.ui'
#
# Created: Fri Jul 29 15:42:51 2011
#      by: PyQt4 UI code generator 4.8.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s


class Ui_Form(object):

    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(501, 414)
        self.gridLayout_2 = QtGui.QGridLayout(Form)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.groupBox = QtGui.QGroupBox(Form)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.gridLayout = QtGui.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.taurusLabel = TaurusLabel(self.groupBox)
        self.taurusLabel.setObjectName(_fromUtf8("taurusLabel"))
        self.gridLayout.addWidget(self.taurusLabel, 0, 0, 1, 1)
        self.taurusLabel_2 = TaurusLabel(self.groupBox)
        self.taurusLabel_2.setObjectName(_fromUtf8("taurusLabel_2"))
        self.gridLayout.addWidget(self.taurusLabel_2, 0, 2, 1, 1)
        self.taurusLed_2 = TaurusLed(self.groupBox)
        self.taurusLed_2.setObjectName(_fromUtf8("taurusLed_2"))
        self.gridLayout.addWidget(self.taurusLed_2, 0, 3, 1, 1)
        self.taurusLabel_3 = TaurusLabel(self.groupBox)
        self.taurusLabel_3.setObjectName(_fromUtf8("taurusLabel_3"))
        self.gridLayout.addWidget(self.taurusLabel_3, 1, 0, 1, 1)
        self.taurusLabel_4 = TaurusLabel(self.groupBox)
        self.taurusLabel_4.setObjectName(_fromUtf8("taurusLabel_4"))
        self.gridLayout.addWidget(self.taurusLabel_4, 1, 2, 1, 1)
        self.taurusLed_3 = TaurusLed(self.groupBox)
        self.taurusLed_3.setObjectName(_fromUtf8("taurusLed_3"))
        self.gridLayout.addWidget(self.taurusLed_3, 1, 3, 1, 1)
        self.taurusLabel_5 = TaurusLabel(self.groupBox)
        self.taurusLabel_5.setObjectName(_fromUtf8("taurusLabel_5"))
        self.gridLayout.addWidget(self.taurusLabel_5, 2, 0, 1, 1)
        self.taurusLabel_6 = TaurusLabel(self.groupBox)
        self.taurusLabel_6.setObjectName(_fromUtf8("taurusLabel_6"))
        self.gridLayout.addWidget(self.taurusLabel_6, 2, 2, 1, 1)
        self.taurusLed_4 = TaurusLed(self.groupBox)
        self.taurusLed_4.setObjectName(_fromUtf8("taurusLed_4"))
        self.gridLayout.addWidget(self.taurusLed_4, 2, 3, 1, 1)
        self.taurusLabel_7 = TaurusLabel(self.groupBox)
        self.taurusLabel_7.setObjectName(_fromUtf8("taurusLabel_7"))
        self.gridLayout.addWidget(self.taurusLabel_7, 3, 0, 1, 1)
        self.taurusLabel_8 = TaurusLabel(self.groupBox)
        self.taurusLabel_8.setObjectName(_fromUtf8("taurusLabel_8"))
        self.gridLayout.addWidget(self.taurusLabel_8, 3, 2, 1, 1)
        self.taurusLed_5 = TaurusLed(self.groupBox)
        self.taurusLed_5.setObjectName(_fromUtf8("taurusLed_5"))
        self.gridLayout.addWidget(self.taurusLed_5, 3, 3, 1, 1)
        self.taurusLabel_9 = TaurusLabel(self.groupBox)
        self.taurusLabel_9.setObjectName(_fromUtf8("taurusLabel_9"))
        self.gridLayout.addWidget(self.taurusLabel_9, 4, 0, 1, 1)
        self.taurusLabel_10 = TaurusLabel(self.groupBox)
        self.taurusLabel_10.setObjectName(_fromUtf8("taurusLabel_10"))
        self.gridLayout.addWidget(self.taurusLabel_10, 4, 2, 1, 1)
        self.taurusLed_6 = TaurusLed(self.groupBox)
        self.taurusLed_6.setObjectName(_fromUtf8("taurusLed_6"))
        self.gridLayout.addWidget(self.taurusLed_6, 4, 3, 1, 1)
        self.taurusLabel_11 = TaurusLabel(self.groupBox)
        self.taurusLabel_11.setObjectName(_fromUtf8("taurusLabel_11"))
        self.gridLayout.addWidget(self.taurusLabel_11, 5, 0, 1, 1)
        self.taurusLabel_12 = TaurusLabel(self.groupBox)
        self.taurusLabel_12.setObjectName(_fromUtf8("taurusLabel_12"))
        self.gridLayout.addWidget(self.taurusLabel_12, 5, 2, 1, 1)
        self.taurusLed_7 = TaurusLed(self.groupBox)
        self.taurusLed_7.setObjectName(_fromUtf8("taurusLed_7"))
        self.gridLayout.addWidget(self.taurusLed_7, 5, 3, 1, 1)
        self.gridLayout_2.addWidget(self.groupBox, 0, 2, 1, 1)
        self.groupBox_2 = QtGui.QGroupBox(Form)
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.gridLayout_3 = QtGui.QGridLayout(self.groupBox_2)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.taurusLabel_13 = TaurusLabel(self.groupBox_2)
        self.taurusLabel_13.setObjectName(_fromUtf8("taurusLabel_13"))
        self.gridLayout_3.addWidget(self.taurusLabel_13, 0, 0, 1, 1)
        self.taurusLabel_14 = TaurusLabel(self.groupBox_2)
        self.taurusLabel_14.setObjectName(_fromUtf8("taurusLabel_14"))
        self.gridLayout_3.addWidget(self.taurusLabel_14, 0, 2, 1, 1)
        self.taurusLed_8 = TaurusLed(self.groupBox_2)
        self.taurusLed_8.setObjectName(_fromUtf8("taurusLed_8"))
        self.gridLayout_3.addWidget(self.taurusLed_8, 0, 3, 1, 1)
        self.taurusLabel_15 = TaurusLabel(self.groupBox_2)
        self.taurusLabel_15.setObjectName(_fromUtf8("taurusLabel_15"))
        self.gridLayout_3.addWidget(self.taurusLabel_15, 1, 0, 1, 1)
        self.taurusLabel_16 = TaurusLabel(self.groupBox_2)
        self.taurusLabel_16.setObjectName(_fromUtf8("taurusLabel_16"))
        self.gridLayout_3.addWidget(self.taurusLabel_16, 1, 2, 1, 1)
        self.taurusLed_9 = TaurusLed(self.groupBox_2)
        self.taurusLed_9.setObjectName(_fromUtf8("taurusLed_9"))
        self.gridLayout_3.addWidget(self.taurusLed_9, 1, 3, 1, 1)
        self.taurusLabel_17 = TaurusLabel(self.groupBox_2)
        self.taurusLabel_17.setObjectName(_fromUtf8("taurusLabel_17"))
        self.gridLayout_3.addWidget(self.taurusLabel_17, 2, 0, 1, 1)
        self.taurusLabel_18 = TaurusLabel(self.groupBox_2)
        self.taurusLabel_18.setObjectName(_fromUtf8("taurusLabel_18"))
        self.gridLayout_3.addWidget(self.taurusLabel_18, 2, 2, 1, 1)
        self.taurusLed_10 = TaurusLed(self.groupBox_2)
        self.taurusLed_10.setObjectName(_fromUtf8("taurusLed_10"))
        self.gridLayout_3.addWidget(self.taurusLed_10, 2, 3, 1, 1)
        self.taurusLabel_19 = TaurusLabel(self.groupBox_2)
        self.taurusLabel_19.setObjectName(_fromUtf8("taurusLabel_19"))
        self.gridLayout_3.addWidget(self.taurusLabel_19, 3, 0, 1, 1)
        self.taurusLabel_20 = TaurusLabel(self.groupBox_2)
        self.taurusLabel_20.setObjectName(_fromUtf8("taurusLabel_20"))
        self.gridLayout_3.addWidget(self.taurusLabel_20, 3, 2, 1, 1)
        self.taurusLed_11 = TaurusLed(self.groupBox_2)
        self.taurusLed_11.setObjectName(_fromUtf8("taurusLed_11"))
        self.gridLayout_3.addWidget(self.taurusLed_11, 3, 3, 1, 1)
        self.taurusLabel_21 = TaurusLabel(self.groupBox_2)
        self.taurusLabel_21.setObjectName(_fromUtf8("taurusLabel_21"))
        self.gridLayout_3.addWidget(self.taurusLabel_21, 4, 0, 1, 1)
        self.taurusLabel_22 = TaurusLabel(self.groupBox_2)
        self.taurusLabel_22.setObjectName(_fromUtf8("taurusLabel_22"))
        self.gridLayout_3.addWidget(self.taurusLabel_22, 4, 2, 1, 1)
        self.taurusLed_12 = TaurusLed(self.groupBox_2)
        self.taurusLed_12.setObjectName(_fromUtf8("taurusLed_12"))
        self.gridLayout_3.addWidget(self.taurusLed_12, 4, 3, 1, 1)
        self.taurusLabel_23 = TaurusLabel(self.groupBox_2)
        self.taurusLabel_23.setObjectName(_fromUtf8("taurusLabel_23"))
        self.gridLayout_3.addWidget(self.taurusLabel_23, 5, 0, 1, 1)
        self.taurusLabel_24 = TaurusLabel(self.groupBox_2)
        self.taurusLabel_24.setObjectName(_fromUtf8("taurusLabel_24"))
        self.gridLayout_3.addWidget(self.taurusLabel_24, 5, 2, 1, 1)
        self.taurusLed_13 = TaurusLed(self.groupBox_2)
        self.taurusLed_13.setObjectName(_fromUtf8("taurusLed_13"))
        self.gridLayout_3.addWidget(self.taurusLed_13, 5, 3, 1, 1)
        self.gridLayout_2.addWidget(self.groupBox_2, 0, 3, 1, 1)
        self.groupBox_4 = QtGui.QGroupBox(Form)
        self.groupBox_4.setObjectName(_fromUtf8("groupBox_4"))
        self.gridLayout_5 = QtGui.QGridLayout(self.groupBox_4)
        self.gridLayout_5.setObjectName(_fromUtf8("gridLayout_5"))
        self.taurusLabel_26 = TaurusLabel(self.groupBox_4)
        self.taurusLabel_26.setObjectName(_fromUtf8("taurusLabel_26"))
        self.gridLayout_5.addWidget(self.taurusLabel_26, 0, 0, 1, 3)
        self.taurusLed_14 = TaurusLed(self.groupBox_4)
        self.taurusLed_14.setObjectName(_fromUtf8("taurusLed_14"))
        self.gridLayout_5.addWidget(self.taurusLed_14, 1, 0, 1, 1)
        self.taurusLabel_29 = TaurusLabel(self.groupBox_4)
        self.taurusLabel_29.setObjectName(_fromUtf8("taurusLabel_29"))
        self.gridLayout_5.addWidget(self.taurusLabel_29, 2, 0, 1, 1)
        self.taurusLabel_30 = TaurusLabel(self.groupBox_4)
        self.taurusLabel_30.setObjectName(_fromUtf8("taurusLabel_30"))
        self.gridLayout_5.addWidget(self.taurusLabel_30, 2, 1, 1, 1)
        self.taurusValueLineEdit_2 = TaurusValueLineEdit(self.groupBox_4)
        self.taurusValueLineEdit_2.setObjectName(
            _fromUtf8("taurusValueLineEdit_2"))
        self.gridLayout_5.addWidget(self.taurusValueLineEdit_2, 2, 2, 1, 1)
        self.taurusLabel_33 = TaurusLabel(self.groupBox_4)
        self.taurusLabel_33.setObjectName(_fromUtf8("taurusLabel_33"))
        self.gridLayout_5.addWidget(self.taurusLabel_33, 3, 0, 1, 1)
        self.taurusLabel_34 = TaurusLabel(self.groupBox_4)
        self.taurusLabel_34.setObjectName(_fromUtf8("taurusLabel_34"))
        self.gridLayout_5.addWidget(self.taurusLabel_34, 3, 1, 1, 1)
        self.taurusValueLineEdit_4 = TaurusValueLineEdit(self.groupBox_4)
        self.taurusValueLineEdit_4.setObjectName(
            _fromUtf8("taurusValueLineEdit_4"))
        self.gridLayout_5.addWidget(self.taurusValueLineEdit_4, 3, 2, 1, 1)
        self.taurusLabel_37 = TaurusLabel(self.groupBox_4)
        self.taurusLabel_37.setObjectName(_fromUtf8("taurusLabel_37"))
        self.gridLayout_5.addWidget(self.taurusLabel_37, 4, 0, 1, 1)
        self.taurusLabel_38 = TaurusLabel(self.groupBox_4)
        self.taurusLabel_38.setObjectName(_fromUtf8("taurusLabel_38"))
        self.gridLayout_5.addWidget(self.taurusLabel_38, 4, 1, 1, 1)
        self.taurusValueLineEdit_6 = TaurusValueLineEdit(self.groupBox_4)
        self.taurusValueLineEdit_6.setObjectName(
            _fromUtf8("taurusValueLineEdit_6"))
        self.gridLayout_5.addWidget(self.taurusValueLineEdit_6, 4, 2, 1, 1)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.taurusCommandButton_2 = TaurusCommandButton(self.groupBox_4)
        self.taurusCommandButton_2.setObjectName(
            _fromUtf8("taurusCommandButton_2"))
        self.horizontalLayout_2.addWidget(self.taurusCommandButton_2)
        self.cfgMg2 = QtGui.QToolButton(self.groupBox_4)
        self.cfgMg2.setObjectName(_fromUtf8("cfgMg2"))
        self.horizontalLayout_2.addWidget(self.cfgMg2)
        self.horizontalLayout_2.setStretch(0, 1)
        self.gridLayout_5.addLayout(self.horizontalLayout_2, 1, 1, 1, 2)
        self.gridLayout_2.addWidget(self.groupBox_4, 1, 3, 1, 1)
        self.groupBox_3 = QtGui.QGroupBox(Form)
        self.groupBox_3.setObjectName(_fromUtf8("groupBox_3"))
        self.gridLayout_4 = QtGui.QGridLayout(self.groupBox_3)
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.taurusLabel_25 = TaurusLabel(self.groupBox_3)
        self.taurusLabel_25.setObjectName(_fromUtf8("taurusLabel_25"))
        self.gridLayout_4.addWidget(self.taurusLabel_25, 0, 0, 1, 3)
        self.taurusLabel_27 = TaurusLabel(self.groupBox_3)
        self.taurusLabel_27.setObjectName(_fromUtf8("taurusLabel_27"))
        self.gridLayout_4.addWidget(self.taurusLabel_27, 2, 1, 1, 1)
        self.taurusLabel_28 = TaurusLabel(self.groupBox_3)
        self.taurusLabel_28.setObjectName(_fromUtf8("taurusLabel_28"))
        self.gridLayout_4.addWidget(self.taurusLabel_28, 2, 0, 1, 1)
        self.taurusValueLineEdit = TaurusValueLineEdit(self.groupBox_3)
        self.taurusValueLineEdit.setObjectName(
            _fromUtf8("taurusValueLineEdit"))
        self.gridLayout_4.addWidget(self.taurusValueLineEdit, 2, 2, 1, 1)
        self.taurusLed = TaurusLed(self.groupBox_3)
        self.taurusLed.setObjectName(_fromUtf8("taurusLed"))
        self.gridLayout_4.addWidget(self.taurusLed, 1, 0, 1, 1)
        self.taurusLabel_31 = TaurusLabel(self.groupBox_3)
        self.taurusLabel_31.setObjectName(_fromUtf8("taurusLabel_31"))
        self.gridLayout_4.addWidget(self.taurusLabel_31, 3, 0, 1, 1)
        self.taurusLabel_32 = TaurusLabel(self.groupBox_3)
        self.taurusLabel_32.setObjectName(_fromUtf8("taurusLabel_32"))
        self.gridLayout_4.addWidget(self.taurusLabel_32, 3, 1, 1, 1)
        self.taurusValueLineEdit_3 = TaurusValueLineEdit(self.groupBox_3)
        self.taurusValueLineEdit_3.setObjectName(
            _fromUtf8("taurusValueLineEdit_3"))
        self.gridLayout_4.addWidget(self.taurusValueLineEdit_3, 3, 2, 1, 1)
        self.taurusLabel_35 = TaurusLabel(self.groupBox_3)
        self.taurusLabel_35.setObjectName(_fromUtf8("taurusLabel_35"))
        self.gridLayout_4.addWidget(self.taurusLabel_35, 4, 0, 1, 1)
        self.taurusLabel_36 = TaurusLabel(self.groupBox_3)
        self.taurusLabel_36.setObjectName(_fromUtf8("taurusLabel_36"))
        self.gridLayout_4.addWidget(self.taurusLabel_36, 4, 1, 1, 1)
        self.taurusValueLineEdit_5 = TaurusValueLineEdit(self.groupBox_3)
        self.taurusValueLineEdit_5.setObjectName(
            _fromUtf8("taurusValueLineEdit_5"))
        self.gridLayout_4.addWidget(self.taurusValueLineEdit_5, 4, 2, 1, 1)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.taurusCommandButton = TaurusCommandButton(self.groupBox_3)
        self.taurusCommandButton.setObjectName(
            _fromUtf8("taurusCommandButton"))
        self.horizontalLayout_3.addWidget(self.taurusCommandButton)
        self.cfgMg1 = QtGui.QToolButton(self.groupBox_3)
        self.cfgMg1.setObjectName(_fromUtf8("cfgMg1"))
        self.horizontalLayout_3.addWidget(self.cfgMg1)
        self.gridLayout_4.addLayout(self.horizontalLayout_3, 1, 1, 1, 2)
        self.gridLayout_2.addWidget(self.groupBox_3, 1, 2, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate(
            "Form", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate(
            "Form", "CTs of CTRL1", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl1/1/value?configuration=dev_alias", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel.setBgRole(QtGui.QApplication.translate(
            "Form", "none", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_2.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl1/1/value", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLed_2.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl1/1/state", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_3.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl1/2/value?configuration=dev_alias", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_3.setBgRole(QtGui.QApplication.translate(
            "Form", "none", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_4.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl1/2/value", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLed_3.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl1/2/state", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_5.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl1/3/value?configuration=dev_alias", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_5.setBgRole(QtGui.QApplication.translate(
            "Form", "none", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_6.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl1/3/value", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLed_4.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl1/3/state", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_7.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl1/4/value?configuration=dev_alias", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_7.setBgRole(QtGui.QApplication.translate(
            "Form", "none", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_8.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl1/4/value", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLed_5.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl1/4/state", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_9.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl1/5/value?configuration=dev_alias", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_9.setBgRole(QtGui.QApplication.translate(
            "Form", "none", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_10.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl1/5/value", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLed_6.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl1/5/state", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_11.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl1/6/value?configuration=dev_alias", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_11.setBgRole(QtGui.QApplication.translate(
            "Form", "none", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_12.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl1/6/value", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLed_7.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl1/6/state", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate(
            "Form", "CTs of CTRL2", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_13.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl2/1/value?configuration=dev_alias", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_13.setBgRole(QtGui.QApplication.translate(
            "Form", "none", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_14.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl2/1/value", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLed_8.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl2/1/state", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_15.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl2/2/value?configuration=dev_alias", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_15.setBgRole(QtGui.QApplication.translate(
            "Form", "none", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_16.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl2/2/value", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLed_9.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl2/2/state", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_17.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl2/3/value?configuration=dev_alias", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_17.setBgRole(QtGui.QApplication.translate(
            "Form", "none", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_18.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl2/3/value", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLed_10.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl2/3/state", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_19.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl2/4/value?configuration=dev_alias", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_19.setBgRole(QtGui.QApplication.translate(
            "Form", "none", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_20.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl2/4/value", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLed_11.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl2/4/state", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_21.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl2/5/value?configuration=dev_alias", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_21.setBgRole(QtGui.QApplication.translate(
            "Form", "none", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_22.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl2/5/value", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLed_12.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl2/5/state", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_23.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl2/6/value?configuration=dev_alias", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_23.setBgRole(QtGui.QApplication.translate(
            "Form", "none", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_24.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl2/6/value", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLed_13.setModel(QtGui.QApplication.translate(
            "Form", "expchan/dummyctctrl2/6/state", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_4.setTitle(QtGui.QApplication.translate(
            "Form", "MG2", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_26.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg2/elementlist", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_26.setBgRole(QtGui.QApplication.translate(
            "Form", "none", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLed_14.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg2/state", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_29.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg2/integrationtime?configuration=label", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_29.setBgRole(QtGui.QApplication.translate(
            "Form", "none", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_30.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg2/integrationtime", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusValueLineEdit_2.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg2/integrationtime", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_33.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg2/monitorcount?configuration=label", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_33.setBgRole(QtGui.QApplication.translate(
            "Form", "none", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_34.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg2/monitorcount", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusValueLineEdit_4.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg2/monitorcount", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_37.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg2/acquisitionmode?configuration=label", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_37.setBgRole(QtGui.QApplication.translate(
            "Form", "none", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_38.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg2/acquisitionmode", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusValueLineEdit_6.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg2/acquisitionmode", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusCommandButton_2.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg2", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusCommandButton_2.setCommand(QtGui.QApplication.translate(
            "Form", "start", None, QtGui.QApplication.UnicodeUTF8))
        self.cfgMg2.setText(QtGui.QApplication.translate(
            "Form", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_3.setTitle(QtGui.QApplication.translate(
            "Form", "MG1", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_25.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg1/elementlist", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_25.setBgRole(QtGui.QApplication.translate(
            "Form", "none", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_27.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg1/integrationtime", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_28.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg1/integrationtime?configuration=label", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_28.setBgRole(QtGui.QApplication.translate(
            "Form", "none", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusValueLineEdit.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg1/integrationtime", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLed.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg1/state", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_31.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg1/monitorcount?configuration=label", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_31.setBgRole(QtGui.QApplication.translate(
            "Form", "none", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_32.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg1/monitorcount", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusValueLineEdit_3.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg1/monitorcount", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_35.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg1/acquisitionmode?configuration=label", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_35.setBgRole(QtGui.QApplication.translate(
            "Form", "none", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusLabel_36.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg1/acquisitionmode", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusValueLineEdit_5.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg1/acquisitionmode", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusCommandButton.setModel(QtGui.QApplication.translate(
            "Form", "mntgrp/v3/mg1", None, QtGui.QApplication.UnicodeUTF8))
        self.taurusCommandButton.setCommand(QtGui.QApplication.translate(
            "Form", "start", None, QtGui.QApplication.UnicodeUTF8))
        self.cfgMg1.setText(QtGui.QApplication.translate(
            "Form", "...", None, QtGui.QApplication.UnicodeUTF8))

from taurus.qt.qtgui.display import TaurusLabel, TaurusLed
from taurus.qt.qtgui.input import TaurusValueLineEdit
from taurus.qt.qtgui.button import TaurusCommandButton

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Form = QtGui.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())
