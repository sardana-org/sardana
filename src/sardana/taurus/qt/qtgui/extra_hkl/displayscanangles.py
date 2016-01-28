#!/usr/bin/env python

# Code implementation generated from reading ui file 'displayscanangles.ui'
#
# Created: Mon Aug  5 14:13:28 2013 
#      by: Taurus UI code generator 3.0.1
#
# WARNING! All changes made in this file will be lost!

__docformat__ = 'restructuredtext'

import sys
import PyQt4.Qt as Qt
from taurus.qt.qtgui.container import TaurusWidget

from taurus.qt.qtgui.util.ui import UILoadable
   
@UILoadable(with_ui="_ui")
class DisplayScanAngles(TaurusWidget):

    def __init__(self, parent=None, designMode=False):
        TaurusWidget.__init__(self, parent, designMode=designMode)
        
        self.loadUi(filename="displayscanangles.ui")
        #self._ui.setupUi(self)
        
    
    @classmethod
    def getQtDesignerPluginInfo(cls):
        ret = TaurusWidget.getQtDesignerPluginInfo()
        ret['module'] = 'displayscanangles'
        ret['group'] = 'Taurus Containers'
        ret['container'] = 'y'
        ret['container'] = False
        return ret


def main():
    app = Qt.QApplication(sys.argv)
    w = DisplayScanAngles()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
