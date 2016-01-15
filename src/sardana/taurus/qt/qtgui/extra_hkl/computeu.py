#!/usr/bin/env python

# Code implementation generated from reading ui file 'computeu.ui'
#
# Created: Wed Aug  7 12:21:07 2013 
#      by: Taurus UI code generator 3.0.1
#
# WARNING! All changes made in this file will be lost!

__docformat__ = 'restructuredtext'

import sys
import PyQt4.Qt as Qt
from ui_computeu import Ui_ComputeU
import taurus.core
from taurus.qt.qtgui.container import TaurusWidget


class ComputeU(TaurusWidget):

    def __init__(self, parent=None, designMode=False):
        TaurusWidget.__init__(self, parent, designMode=designMode)
        
        self._ui = Ui_ComputeU()
        self._ui.setupUi(self)
        self.connect(self._ui.ComputeButton, Qt.SIGNAL("clicked()"), self.compute_u)
        
    @classmethod
    def getQtDesignerPluginInfo(cls):
        ret = TaurusWidget.getQtDesignerPluginInfo()
        ret['module'] = 'computeu'
        ret['group'] = 'Taurus Containers'
        ret['container'] = ':/designer/frame.png'
        ret['container'] = False
        return ret

    def setModel(self,model):
        if model !=  None:
            self.device = taurus.Device(model)

    def compute_u(self):
        index = []
        index.append(int(self._ui.indexreflection1lineEdit.text()))
        index.append(int(self._ui.indexreflection2lineEdit.text()))
        
        self.device.write_attribute("computeu", index)

def main():
    app = Qt.QApplication(sys.argv)
    w = ComputeU()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
