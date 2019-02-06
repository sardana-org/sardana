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

    enableJorgBar = False
    enablePanelsMenu = False
    enableSharedDataConnections = False
    enableQuickAccessToolBar = False
    enableToolsMenu = False
    enableTaurusMenu = False
    enableFullScreenToolBar = False
    enablePerspectivesToolBar = False


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
