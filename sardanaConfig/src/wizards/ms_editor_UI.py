# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'MSEditor.ui'
#
# Created: Fri Nov 19 12:49:34 2010
#      by: PyQt4 UI code generator 4.4.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui


class Ui_MSEditor(object):

    def setupUi(self, MSEditor):
        MSEditor.setObjectName("MSEditor")
        MSEditor.resize(400, 429)
        self.gridLayout = QtGui.QGridLayout(MSEditor)
        self.gridLayout.setObjectName("gridLayout")
        self.gridLayout_2 = QtGui.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.instanceNameLineEdit = QtGui.QLineEdit(MSEditor)
        self.instanceNameLineEdit.setObjectName("instanceNameLineEdit")
        self.gridLayout_2.addWidget(self.instanceNameLineEdit, 0, 1, 1, 1)
        self.instanceNameLabel = QtGui.QLabel(MSEditor)
        self.instanceNameLabel.setObjectName("instanceNameLabel")
        self.gridLayout_2.addWidget(self.instanceNameLabel, 0, 0, 1, 1)
        self.msDeviceNameLineEdit = QtGui.QLineEdit(MSEditor)
        self.msDeviceNameLineEdit.setObjectName("msDeviceNameLineEdit")
        self.gridLayout_2.addWidget(self.msDeviceNameLineEdit, 2, 1, 1, 1)
        self.msAliasLineEdit = QtGui.QLineEdit(MSEditor)
        self.msAliasLineEdit.setObjectName("msAliasLineEdit")
        self.gridLayout_2.addWidget(self.msAliasLineEdit, 3, 1, 1, 1)
        self.msVersionLineEdit = QtGui.QLineEdit(MSEditor)
        self.msVersionLineEdit.setObjectName("msVersionLineEdit")
        self.gridLayout_2.addWidget(self.msVersionLineEdit, 4, 1, 1, 1)
        self.msDeviceNameLabel = QtGui.QLabel(MSEditor)
        self.msDeviceNameLabel.setObjectName("msDeviceNameLabel")
        self.gridLayout_2.addWidget(self.msDeviceNameLabel, 2, 0, 1, 1)
        self.msAliasLabel = QtGui.QLabel(MSEditor)
        self.msAliasLabel.setObjectName("msAliasLabel")
        self.gridLayout_2.addWidget(self.msAliasLabel, 3, 0, 1, 1)
        self.msVersionLabel = QtGui.QLabel(MSEditor)
        self.msVersionLabel.setObjectName("msVersionLabel")
        self.gridLayout_2.addWidget(self.msVersionLabel, 4, 0, 1, 1)
        self.msDeviceNameCheckBox = QtGui.QCheckBox(MSEditor)
        self.msDeviceNameCheckBox.setObjectName("msDeviceNameCheckBox")
        self.gridLayout_2.addWidget(self.msDeviceNameCheckBox, 2, 2, 1, 1)
        self.msAliasCheckBox = QtGui.QCheckBox(MSEditor)
        self.msAliasCheckBox.setObjectName("msAliasCheckBox")
        self.gridLayout_2.addWidget(self.msAliasCheckBox, 3, 2, 1, 1)
        self.msVersionCheckBox = QtGui.QCheckBox(MSEditor)
        self.msVersionCheckBox.setObjectName("msVersionCheckBox")
        self.gridLayout_2.addWidget(self.msVersionCheckBox, 4, 2, 1, 1)
        self.poolNameComboBox = QtGui.QComboBox(MSEditor)
        self.poolNameComboBox.setObjectName("poolNameComboBox")
        self.gridLayout_2.addWidget(self.poolNameComboBox, 1, 1, 1, 1)
        self.poolNameLabel = QtGui.QLabel(MSEditor)
        self.poolNameLabel.setObjectName("poolNameLabel")
        self.gridLayout_2.addWidget(self.poolNameLabel, 1, 0, 1, 1)
        self.doorNameLabel = QtGui.QLabel(MSEditor)
        self.doorNameLabel.setObjectName("doorNameLabel")
        self.gridLayout_2.addWidget(self.doorNameLabel, 5, 0, 1, 1)
        self.doorAliasLabel = QtGui.QLabel(MSEditor)
        self.doorAliasLabel.setObjectName("doorAliasLabel")
        self.gridLayout_2.addWidget(self.doorAliasLabel, 6, 0, 1, 1)
        self.doorNameCheckBox = QtGui.QCheckBox(MSEditor)
        self.doorNameCheckBox.setObjectName("doorNameCheckBox")
        self.gridLayout_2.addWidget(self.doorNameCheckBox, 5, 2, 1, 1)
        self.doorAliasCheckBox = QtGui.QCheckBox(MSEditor)
        self.doorAliasCheckBox.setObjectName("doorAliasCheckBox")
        self.gridLayout_2.addWidget(self.doorAliasCheckBox, 6, 2, 1, 1)
        self.doorNameLineEdit = QtGui.QLineEdit(MSEditor)
        self.doorNameLineEdit.setObjectName("doorNameLineEdit")
        self.gridLayout_2.addWidget(self.doorNameLineEdit, 5, 1, 1, 1)
        self.doorAliasLineEdit = QtGui.QLineEdit(MSEditor)
        self.doorAliasLineEdit.setObjectName("doorAliasLineEdit")
        self.gridLayout_2.addWidget(self.doorAliasLineEdit, 6, 1, 1, 1)
        self.gridLayout.addLayout(self.gridLayout_2, 0, 0, 1, 1)
        self.groupBox = QtGui.QGroupBox(MSEditor)
        self.groupBox.setObjectName("groupBox")
        self.horizontalLayout = QtGui.QHBoxLayout(self.groupBox)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.msPathList = QtGui.QListWidget(self.groupBox)
        self.msPathList.setMouseTracking(True)
        self.msPathList.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.msPathList.setSelectionBehavior(
            QtGui.QAbstractItemView.SelectItems)
        self.msPathList.setObjectName("msPathList")
        self.horizontalLayout.addWidget(self.msPathList)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.addButton = QtGui.QToolButton(self.groupBox)
        self.addButton.setObjectName("addButton")
        self.verticalLayout.addWidget(self.addButton)
        self.removeButton = QtGui.QToolButton(self.groupBox)
        self.removeButton.setObjectName("removeButton")
        self.verticalLayout.addWidget(self.removeButton)
        self.upButton = QtGui.QToolButton(self.groupBox)
        self.upButton.setObjectName("upButton")
        self.verticalLayout.addWidget(self.upButton)
        self.downButton = QtGui.QToolButton(self.groupBox)
        self.downButton.setObjectName("downButton")
        self.verticalLayout.addWidget(self.downButton)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.gridLayout.addWidget(self.groupBox, 1, 0, 1, 1)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtGui.QSpacerItem(
            40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.createButton = QtGui.QPushButton(MSEditor)
        self.createButton.setObjectName("createButton")
        self.horizontalLayout_2.addWidget(self.createButton)
        self.closeButton = QtGui.QPushButton(MSEditor)
        self.closeButton.setObjectName("closeButton")
        self.horizontalLayout_2.addWidget(self.closeButton)
        self.gridLayout.addLayout(self.horizontalLayout_2, 2, 0, 1, 1)

        self.retranslateUi(MSEditor)
        QtCore.QObject.connect(self.msDeviceNameCheckBox, QtCore.SIGNAL(
            "toggled(bool)"), self.msDeviceNameLineEdit.setDisabled)
        QtCore.QObject.connect(self.msAliasCheckBox, QtCore.SIGNAL(
            "toggled(bool)"), self.msAliasLineEdit.setDisabled)
        QtCore.QObject.connect(self.msVersionCheckBox, QtCore.SIGNAL(
            "toggled(bool)"), self.msVersionLineEdit.setDisabled)
        QtCore.QObject.connect(
            self.closeButton, QtCore.SIGNAL("clicked()"), MSEditor.close)
        QtCore.QObject.connect(self.doorNameCheckBox, QtCore.SIGNAL(
            "toggled(bool)"), self.doorNameLineEdit.setDisabled)
        QtCore.QObject.connect(self.doorAliasCheckBox, QtCore.SIGNAL(
            "toggled(bool)"), self.doorAliasLineEdit.setDisabled)
        QtCore.QMetaObject.connectSlotsByName(MSEditor)

    def retranslateUi(self, MSEditor):
        MSEditor.setWindowTitle(QtGui.QApplication.translate(
            "MSEditor", "Create Pool", None, QtGui.QApplication.UnicodeUTF8))
        self.instanceNameLabel.setText(QtGui.QApplication.translate(
            "MSEditor", "Instance name", None, QtGui.QApplication.UnicodeUTF8))
        self.msDeviceNameLabel.setText(QtGui.QApplication.translate(
            "MSEditor", "MS device name", None, QtGui.QApplication.UnicodeUTF8))
        self.msAliasLabel.setText(QtGui.QApplication.translate(
            "MSEditor", "MS alias (optional)", None, QtGui.QApplication.UnicodeUTF8))
        self.msVersionLabel.setText(QtGui.QApplication.translate(
            "MSEditor", "MS version", None, QtGui.QApplication.UnicodeUTF8))
        self.msDeviceNameCheckBox.setText(QtGui.QApplication.translate(
            "MSEditor", "Automatic", None, QtGui.QApplication.UnicodeUTF8))
        self.msAliasCheckBox.setText(QtGui.QApplication.translate(
            "MSEditor", "Automatic", None, QtGui.QApplication.UnicodeUTF8))
        self.msVersionCheckBox.setText(QtGui.QApplication.translate(
            "MSEditor", "Automatic", None, QtGui.QApplication.UnicodeUTF8))
        self.poolNameLabel.setText(QtGui.QApplication.translate(
            "MSEditor", "Pool name", None, QtGui.QApplication.UnicodeUTF8))
        self.doorNameLabel.setText(QtGui.QApplication.translate(
            "MSEditor", "Door name", None, QtGui.QApplication.UnicodeUTF8))
        self.doorAliasLabel.setText(QtGui.QApplication.translate(
            "MSEditor", "Door alias (optional)", None, QtGui.QApplication.UnicodeUTF8))
        self.doorNameCheckBox.setText(QtGui.QApplication.translate(
            "MSEditor", "Automatic", None, QtGui.QApplication.UnicodeUTF8))
        self.doorAliasCheckBox.setText(QtGui.QApplication.translate(
            "MSEditor", "Automatic", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate(
            "MSEditor", "MacroPath", None, QtGui.QApplication.UnicodeUTF8))
        self.createButton.setText(QtGui.QApplication.translate(
            "MSEditor", "Create", None, QtGui.QApplication.UnicodeUTF8))
        self.closeButton.setText(QtGui.QApplication.translate(
            "MSEditor", "Close", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MSEditor = QtGui.QDialog()
    ui = Ui_MSEditor()
    ui.setupUi(MSEditor)
    MSEditor.show()
    sys.exit(app.exec_())
