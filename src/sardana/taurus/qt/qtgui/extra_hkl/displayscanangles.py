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

__docformat__ = 'restructuredtext'

import sys
from taurus.external.qt import Qt
from taurus.qt.qtgui.container import TaurusWidget

from taurus.qt.qtgui.util.ui import UILoadable


@UILoadable(with_ui="_ui")
class DisplayScanAngles(TaurusWidget):

    def __init__(self, parent=None, designMode=False):
        TaurusWidget.__init__(self, parent, designMode=designMode)

        self.loadUi(filename="displayscanangles.ui")
        # self._ui.setupUi(self)

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
