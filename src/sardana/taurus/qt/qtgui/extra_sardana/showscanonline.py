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

import click

from taurus.qt.qtgui.taurusgui import TaurusGui
from sardana.taurus.qt.qtgui.macrolistener import (DynamicPlotManager,
                                                   assertPlotAvailability)


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
    HEARTBEAT = None
    FILE_MENU_ENABLED = False
    VIEW_MENU_ENABLED = False
    TAURUS_MENU_ENABLED = False
    TOOLS_MENU_ENABLED = False
    PANELS_MENU_ENABLED = False
    HELP_MENU_ENABLED = False
    FULLSCREEN_TOOLBAR_ENABLED = False
    APPLETS_TOOLBAR_ENABLED = False
    QUICK_ACCESS_TOOLBAR_ENABLED = False
    USER_PERSPECTIVES_ENABLED = False
    LOGGER_WIDGET_ENABLED = False
    SPLASH_LOGO_NAME = None


@click.command()
@click.option('--group', default='x-axis',
              type=click.Choice(['single', 'x-axis']),
              help='group curves')
@click.option('--taurus-log-level',
              type=click.Choice(['critical', 'error', 'warning', 'info',
                                 'debug', 'trace']),
              default='error', show_default=True,
              help='Show only logs with priority LEVEL or above')
@click.argument('door')
def main(group, taurus_log_level, door):
    import taurus
    taurus.setLogLevel(getattr(taurus, taurus_log_level.capitalize()))

    from taurus.qt.qtgui.application import TaurusApplication

    app = TaurusApplication(app_name='Showscan Online', org_domain="Sardana",
                            org_name="Tango communinity", cmd_line_parser=None)

    assertPlotAvailability()

    gui = TaurusGuiLite()

    widget = ShowScanOnline(gui)
    widget.setModel(door)
    widget.setGroupMode(group)
    gui.show()
    return app.exec_()


if __name__ == "__main__":
    main()
