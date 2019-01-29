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

"""
motor.py:
"""


from taurus.external.qt import Qt
from taurus.qt.qtgui.base import TaurusBaseWidget
from taurus.qt.qtgui.util.ui import UILoadable


def showDialogConfigureMotor(parent):
    Dialog = Qt.QDialog(parent)
    Dialog.resize((Qt.QSize(Qt.QRect(0, 0, 310, 309).size()
                            ).expandedTo(Dialog.minimumSizeHint())))
    motorV2 = TaurusMotorV2(Dialog)
    motorV2.setModel(parent.model)
    motorV2.setGeometry(Qt.QRect(10, 10, 291, 291))
    Dialog.show()


@UILoadable(with_ui='ui')
class TaurusMotorH(Qt.QWidget, TaurusBaseWidget):

    __pyqtSignals__ = ("modelChanged(const QString &)",)

    def __init__(self, parent=None, designMode=False):
        self.call__init__wo_kw(Qt.QWidget, parent)
        self.call__init__(TaurusBaseWidget, str(
            self.objectName()), designMode=designMode)
        self.loadUi()
        self.ui.config.clicked.connect(self.configureMotor)

    def sizeHint(self):
        return Qt.QSize(330, 50)

    def configureMotor(self):
        showDialogConfigureMotor(self.ui.TaurusGroupBox)

    @classmethod
    def getQtDesignerPluginInfo(cls):
        return None
#        ret = TaurusBaseWidget.getQtDesignerPluginInfo()
#        ret['module'] = 'taurus.qt.qtgui.extra_pool'
#        ret['group'] = 'Taurus Sardana'
#        ret['icon'] = ':/designer/extra_pool.png'
#        return ret

    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # QT properties
    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    @Qt.pyqtSlot()
    def getModel(self):
        return self.ui.TaurusGroupBox.getModel()

    @Qt.pyqtSlot("QString")
    def setModel(self, model):
        self.ui.TaurusGroupBox.setModel(model)

    @Qt.pyqtSlot()
    def resetModel(self):
        self.ui.TaurusGroupBox.resetModel()

    @Qt.pyqtSlot()
    def getShowText(self):
        return self.ui.TaurusGroupBox.getShowText()

    @Qt.pyqtSlot(bool)
    def setShowText(self, showText):
        self.ui.TaurusGroupBox.setShowText(showText)

    @Qt.pyqtSlot()
    def resetShowText(self):
        self.ui.TaurusGroupBox.resetShowText()

    model = Qt.pyqtProperty("QString", getModel, setModel, resetModel)
    showText = Qt.pyqtProperty("bool", getShowText, setShowText, resetShowText)


@UILoadable(with_ui='ui')
class TaurusMotorH2(Qt.QWidget, TaurusBaseWidget):

    __pyqtSignals__ = ("modelChanged(const QString &)",)

    def __init__(self, parent=None, designMode=False):
        self.call__init__wo_kw(Qt.QWidget, parent)
        self.call__init__(TaurusBaseWidget, str(
            self.objectName()), designMode=designMode)
        self.loadUi()
        self.ui.config.clicked.connect(self.configureMotor)

    def sizeHint(self):
        return Qt.QSize(215, 85)

    def configureMotor(self):
        showDialogConfigureMotor(self.ui.TaurusGroupBox)

    @classmethod
    def getQtDesignerPluginInfo(cls):
        return None
#        ret = TaurusBaseWidget.getQtDesignerPluginInfo()
#        ret['module'] = 'taurus.qt.qtgui.extra_pool'
#        ret['group'] = 'Taurus Sardana'
#        ret['icon'] = ':/designer/extra_pool.png'
#        return ret

    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # QT properties
    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    @Qt.pyqtSlot()
    def getModel(self):
        return self.ui.TaurusGroupBox.getModel()

    @Qt.pyqtSlot("QString")
    def setModel(self, model):
        self.ui.TaurusGroupBox.setModel(model)

    @Qt.pyqtSlot()
    def resetModel(self):
        self.ui.TaurusGroupBox.resetModel()

    @Qt.pyqtSlot()
    def getShowText(self):
        return self.ui.TaurusGroupBox.getShowText()

    @Qt.pyqtSlot(bool)
    def setShowText(self, showText):
        self.ui.TaurusGroupBox.setShowText(showText)

    @Qt.pyqtSlot()
    def resetShowText(self):
        self.ui.TaurusGroupBox.resetShowText()

    model = Qt.pyqtProperty("QString", getModel, setModel, resetModel)
    showText = Qt.pyqtProperty("bool", getShowText, setShowText, resetShowText)


@UILoadable(with_ui='ui')
class TaurusMotorV(Qt.QWidget, TaurusBaseWidget):

    __pyqtSignals__ = ("modelChanged(const QString &)",)

    def __init__(self, parent=None, designMode=False):
        self.call__init__wo_kw(Qt.QWidget, parent)
        self.call__init__(TaurusBaseWidget, str(
            self.objectName()), designMode=designMode)
        self.loadUi()
        self.ui.config.clicked.connect(self.configureMotor)

    def sizeHint(self):
        return Qt.QSize(120, 145)

    def configureMotor(self):
        showDialogConfigureMotor(self.ui.TaurusGroupBox)

    @classmethod
    def getQtDesignerPluginInfo(cls):
        return None
#        ret = TaurusBaseWidget.getQtDesignerPluginInfo()
#        ret['module'] = 'taurus.qt.qtgui.extra_pool'
#        ret['group'] = 'Taurus Sardana'
#        ret['icon'] = ':/designer/extra_pool.png'
#        return ret

    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # QT properties
    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    @Qt.pyqtSlot()
    def getModel(self):
        return self.ui.TaurusGroupBox.getModel()

    @Qt.pyqtSlot("QString")
    def setModel(self, model):
        self.ui.TaurusGroupBox.setModel(model)

    @Qt.pyqtSlot()
    def resetModel(self):
        self.ui.TaurusGroupBox.resetModel()

    @Qt.pyqtSlot()
    def getShowText(self):
        return self.ui.TaurusGroupBox.getShowText()

    @Qt.pyqtSlot(bool)
    def setShowText(self, showText):
        self.ui.TaurusGroupBox.setShowText(showText)

    @Qt.pyqtSlot()
    def resetShowText(self):
        self.ui.TaurusGroupBox.resetShowText()

    model = Qt.pyqtProperty("QString", getModel, setModel, resetModel)
    showText = Qt.pyqtProperty("bool", getShowText, setShowText, resetShowText)


@UILoadable(with_ui='ui')
class TaurusMotorV2(Qt.QWidget, TaurusBaseWidget):

    __pyqtSignals__ = ("modelChanged(const QString &)",)

    def __init__(self, parent=None, designMode=False):
        self.call__init__wo_kw(Qt.QWidget, parent)
        self.call__init__(TaurusBaseWidget, str(
            self.objectName()), designMode=designMode)
        self.loadUi()

    def sizeHint(self):
        return Qt.QSize(300, 275)

    @classmethod
    def getQtDesignerPluginInfo(cls):
        return None
#        ret = TaurusBaseWidget.getQtDesignerPluginInfo()
#        ret['module'] = 'taurus.qt.qtgui.extra_pool'
#        ret['group'] = 'Taurus Sardana'
#        ret['icon'] = ':/designer/extra_pool.png'
#        return ret

    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # QT properties
    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    @Qt.pyqtSlot()
    def getModel(self):
        return self.ui.TaurusGroupBox.getModel()

    @Qt.pyqtSlot("QString")
    def setModel(self, model):
        self.ui.TaurusGroupBox.setModel(model)

    @Qt.pyqtSlot()
    def resetModel(self):
        self.ui.TaurusGroupBox.resetModel()

    @Qt.pyqtSlot()
    def getShowText(self):
        return self.ui.TaurusGroupBox.getShowText()

    @Qt.pyqtSlot(bool)
    def setShowText(self, showText):
        self.ui.TaurusGroupBox.setShowText(showText)

    @Qt.pyqtSlot()
    def resetShowText(self):
        self.ui.TaurusGroupBox.resetShowText()

    model = Qt.pyqtProperty("QString", getModel, setModel, resetModel)
    showText = Qt.pyqtProperty("bool", getShowText, setShowText, resetShowText)


if __name__ == "__main__":

    import sys
    app = Qt.QApplication(sys.argv)

    form = TaurusMotorH()
    form.setModel(sys.argv[1])

    form.show()
    sys.exit(app.exec_())
