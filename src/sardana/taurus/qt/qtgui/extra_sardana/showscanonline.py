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

"""This module contains a taurus ShowScanOnline widget."""

__all__ = ["ShowScanOnline"]

from sardana.taurus.qt.qtgui.macrolistener import \
    DynamicPlotManager
from taurus.qt.qtgui.taurusgui import TaurusGui


class ShowScanOnline(DynamicPlotManager):

    def __init__(self, parent):
        DynamicPlotManager.__init__(self, parent)

    def onExpConfChanged(self, expconf):
        DynamicPlotManager.onExpConfChanged(self, expconf)
        activeMntGrp = expconf['ActiveMntGrp']
        msg = 'Plotting scans for "%s" Measurement Group' % activeMntGrp
        self.parent().newShortMessage.emit(msg)

    def createPanel(self, widget, name, **kwargs):
        ''' Reimplemented from :class:`DynamicPlotManager` to delegate panel
        management to the parent widget (a TaurusGui)'''
        mainwindow = self.parent()
        return mainwindow.createPanel(widget, name, **kwargs)

    def getPanelWidget(self, name):
        ''' Reimplemented from :class:`DynamicPlotManager` to delegate panel
        management to the parent widget (a TaurusGui)'''
        mainwindow = self.parent()
        return mainwindow.getPanel(name).widget()

    def removePanel(self, name):
        ''' Reimplemented from :class:`DynamicPlotManager` to delegate panel
        management to the parent widget (a TaurusGui)'''
        mainwindow = self.parent()
        mainwindow.removePanel(name)

    def removeTemporaryPanels(self, names=None):
        '''Remove temporary panels managed by this widget'''
        # for now, the only temporary panels are the plots
        DynamicPlotManager.removePanels(self, names=names)


class TaurusGuiLite(TaurusGui):

    ENABLE_APPLETS_TOOLBAR = False
    ENABLE_PANELS_MENU = False
    ENABLED_SHARE_DATA_CONNECTIONS = False
    ENABLE_QUICK_ACCESS_TOOLBAR = False
    ENABLE_TOOLS_MENU = False
    ENABLE_TAURUS_MENU = False
    ENABLE_FULLSCREEN_TOOLBAR = False
    ENABLE_PERSPECTIVE_TOOLBAR = False


def main():

    from taurus.qt.qtgui.application import TaurusApplication
    import sys

    from taurus.core.util.argparse import get_taurus_parser

    parser = get_taurus_parser()
    parser.set_usage("python showscanonline.py [door_name]")
    app = TaurusApplication(app_name='Showscan Online', org_domain="Sardana",
                            org_name="Tango communinity",
                            cmd_line_parser=parser)

    gui = TaurusGuiLite()
    args = app.get_command_line_args()

    if len(args) < 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    door_name = args[0]
    widget = ShowScanOnline(gui)
    widget.setModel(door_name)
    gui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
