#!/usr/bin/env python

##############################################################################
##
## This file is part of Sardana
##
## http://www.sardana-controls.org/
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
##
## Sardana is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## Sardana is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################


__docformat__ = 'restructuredtext'

import sys
from taurus.external.qt import Qt
import taurus.core
from taurus.qt.qtgui.container import TaurusWidget

from taurus.qt.qtgui.util.ui import UILoadable


@UILoadable(with_ui="_ui")
class ComputeU(TaurusWidget):

    def __init__(self, parent=None, designMode=False):
        TaurusWidget.__init__(self, parent, designMode=designMode)

        self.loadUi(filename="computeu.ui")

        self.connect(self._ui.ComputeButton, Qt.SIGNAL(
            "clicked()"), self.compute_u)

    @classmethod
    def getQtDesignerPluginInfo(cls):
        ret = TaurusWidget.getQtDesignerPluginInfo()
        ret['module'] = 'computeu'
        ret['group'] = 'Taurus Containers'
        ret['container'] = ':/designer/frame.png'
        ret['container'] = False
        return ret

    def setModel(self, model):
        if model != None:
            self.device = taurus.Device(model)

    def compute_u(self):
        index = []
        index.append(int(self._ui.indexreflection1lineEdit.text()))
        index.append(int(self._ui.indexreflection2lineEdit.text()))

        self.device.write_attribute("computeub", index)


def main():
    app = Qt.QApplication(sys.argv)
    w = ComputeU()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
