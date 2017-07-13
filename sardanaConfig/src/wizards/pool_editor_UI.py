# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'poolEditor.ui'
#
# Created: Wed Nov 10 10:49:04 2010
#      by: PyQt4 UI code generator 4.4.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui


class Ui_PoolEditor(object):

    def setupUi(self, PoolEditor):
        PoolEditor.setObjectName("PoolEditor")
        PoolEditor.resize(400, 333)
        self.gridLayout = QtGui.QGridLayout(PoolEditor)
        self.gridLayout.setObjectName("gridLayout")
        self.gridLayout_2 = QtGui.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.instanceNameLineEdit = QtGui.QLineEdit(PoolEditor)
        self.instanceNameLineEdit.setObjectName("instanceNameLineEdit")
        self.gridLayout_2.addWidget(self.instanceNameLineEdit, 0, 1, 1, 1)
        self.instanceNameLabel = QtGui.QLabel(PoolEditor)
        self.instanceNameLabel.setObjectName("instanceNameLabel")
        self.gridLayout_2.addWidget(self.instanceNameLabel, 0, 0, 1, 1)
        self.poolDeviceNameLineEdit = QtGui.QLineEdit(PoolEditor)
        self.poolDeviceNameLineEdit.setObjectName("poolDeviceNameLineEdit")
        self.gridLayout_2.addWidget(self.poolDeviceNameLineEdit, 1, 1, 1, 1)
        self.aliasLineEdit = QtGui.QLineEdit(PoolEditor)
        self.aliasLineEdit.setObjectName("aliasLineEdit")
        self.gridLayout_2.addWidget(self.aliasLineEdit, 2, 1, 1, 1)
        self.poolVersionLineEdit = QtGui.QLineEdit(PoolEditor)
        self.poolVersionLineEdit.setObjectName("poolVersionLineEdit")
        self.gridLayout_2.addWidget(self.poolVersionLineEdit, 3, 1, 1, 1)
        self.poolDeviceNameLabel = QtGui.QLabel(PoolEditor)
        self.poolDeviceNameLabel.setObjectName("poolDeviceNameLabel")
        self.gridLayout_2.addWidget(self.poolDeviceNameLabel, 1, 0, 1, 1)
        self.aliasLabel = QtGui.QLabel(PoolEditor)
        self.aliasLabel.setObjectName("aliasLabel")
        self.gridLayout_2.addWidget(self.aliasLabel, 2, 0, 1, 1)
        self.poolVersionLabel = QtGui.QLabel(PoolEditor)
        self.poolVersionLabel.setObjectName("poolVersionLabel")
        self.gridLayout_2.addWidget(self.poolVersionLabel, 3, 0, 1, 1)
        self.poolDeviceNameCheckBox = QtGui.QCheckBox(PoolEditor)
        self.poolDeviceNameCheckBox.setObjectName("poolDeviceNameCheckBox")
        self.gridLayout_2.addWidget(self.poolDeviceNameCheckBox, 1, 2, 1, 1)
        self.aliasCheckBox = QtGui.QCheckBox(PoolEditor)
        self.aliasCheckBox.setObjectName("aliasCheckBox")
        self.gridLayout_2.addWidget(self.aliasCheckBox, 2, 2, 1, 1)
        self.poolVersionCheckBox = QtGui.QCheckBox(PoolEditor)
        self.poolVersionCheckBox.setObjectName("poolVersionCheckBox")
        self.gridLayout_2.addWidget(self.poolVersionCheckBox, 3, 2, 1, 1)
        self.gridLayout.addLayout(self.gridLayout_2, 0, 0, 1, 1)
        self.groupBox = QtGui.QGroupBox(PoolEditor)
        self.groupBox.setObjectName("groupBox")
        self.horizontalLayout = QtGui.QHBoxLayout(self.groupBox)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.poolPathList = QtGui.QListWidget(self.groupBox)
        self.poolPathList.setObjectName("poolPathList")
        self.horizontalLayout.addWidget(self.poolPathList)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.addButton = QtGui.QToolButton(self.groupBox)
        self.addButton.setObjectName("addButton")
        self.verticalLayout.addWidget(self.addButton)
        self.removeButton = QtGui.QToolButton(self.groupBox)
        self.removeButton.setObjectName("removeButton")
        self.verticalLayout.addWidget(self.removeButton)
        self.upButton = QtGui.QToolButton(self.groupBox)
        self.upButton.setArrowType(QtCore.Qt.NoArrow)
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
        self.createButton = QtGui.QPushButton(PoolEditor)
        self.createButton.setObjectName("createButton")
        self.horizontalLayout_2.addWidget(self.createButton)
        self.closeButton = QtGui.QPushButton(PoolEditor)
        self.closeButton.setObjectName("closeButton")
        self.horizontalLayout_2.addWidget(self.closeButton)
        self.gridLayout.addLayout(self.horizontalLayout_2, 2, 0, 1, 1)

        self.retranslateUi(PoolEditor)
        QtCore.QObject.connect(self.poolDeviceNameCheckBox, QtCore.SIGNAL(
            "toggled(bool)"), self.poolDeviceNameLineEdit.setDisabled)
        QtCore.QObject.connect(self.aliasCheckBox, QtCore.SIGNAL(
            "toggled(bool)"), self.aliasLineEdit.setDisabled)
        QtCore.QObject.connect(self.poolVersionCheckBox, QtCore.SIGNAL(
            "toggled(bool)"), self.poolVersionLineEdit.setDisabled)
        QtCore.QObject.connect(self.closeButton, QtCore.SIGNAL(
            "clicked()"), PoolEditor.close)
        QtCore.QMetaObject.connectSlotsByName(PoolEditor)

    def retranslateUi(self, PoolEditor):
        PoolEditor.setWindowTitle(QtGui.QApplication.translate(
            "PoolEditor", "Create Pool", None, QtGui.QApplication.UnicodeUTF8))
        self.instanceNameLabel.setText(QtGui.QApplication.translate(
            "PoolEditor", "Instance name", None, QtGui.QApplication.UnicodeUTF8))
        self.poolDeviceNameLabel.setText(QtGui.QApplication.translate(
            "PoolEditor", "Pool device name", None, QtGui.QApplication.UnicodeUTF8))
        self.aliasLabel.setText(QtGui.QApplication.translate(
            "PoolEditor", "Alias (optional)", None, QtGui.QApplication.UnicodeUTF8))
        self.poolVersionLabel.setText(QtGui.QApplication.translate(
            "PoolEditor", "Pool version", None, QtGui.QApplication.UnicodeUTF8))
        self.poolDeviceNameCheckBox.setText(QtGui.QApplication.translate(
            "PoolEditor", "Automatic", None, QtGui.QApplication.UnicodeUTF8))
        self.aliasCheckBox.setText(QtGui.QApplication.translate(
            "PoolEditor", "Automatic", None, QtGui.QApplication.UnicodeUTF8))
        self.poolVersionCheckBox.setText(QtGui.QApplication.translate(
            "PoolEditor", "Automatic", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate(
            "PoolEditor", "PoolPath", None, QtGui.QApplication.UnicodeUTF8))
        self.createButton.setText(QtGui.QApplication.translate(
            "PoolEditor", "Create", None, QtGui.QApplication.UnicodeUTF8))
        self.closeButton.setText(QtGui.QApplication.translate(
            "PoolEditor", "Close", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    PoolEditor = QtGui.QDialog()
    ui = Ui_PoolEditor()
    ui.setupUi(PoolEditor)
    PoolEditor.show()
    sys.exit(app.exec_())
