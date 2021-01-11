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
This module contains a taurus ShowScanWidget, ShowScanWindow and ShowScanOnline
widgets.
"""

__all__ = [
    "ScanInfoForm", "ScanPointForm", "ScanPlotWidget",
    "ScanPlotWindow", "ScanWindow", "ShowScanOnline"
]

import click
import pkg_resources

from taurus.external.qt import Qt, uic
from taurus.qt.qtgui.base import TaurusBaseWidget
from taurus.qt.qtgui.taurusgui import TaurusGui
from sardana.taurus.qt.qtgui.macrolistener import (
    MultiPlotWidget, PlotManager, DynamicPlotManager, assertPlotAvailability
)


def set_text(label, field=None, data=None, default='---'):
    if field is None and data is None:
        value = default
    elif field is None:
        value = data
    elif data is None:
        value = field
    else:
        value = data.get(field, default)
    if isinstance(value, (tuple, list)):
        value = ', '.join(value)
    elif isinstance(value, float):
        value = '{:8.4f}'.format(value)
    else:
        value = str(value)
    if len(value) > 60:
        value = '...{}'.format(value[-57:])
    label.setText(value)


def resize_form(form, new_size):
    layout = form.layout()
    curr_size = layout.rowCount()
    nb = new_size - curr_size
    while nb > 0:
        layout.addRow(Qt.QLabel(), Qt.QLabel())
        nb -= 1
    while nb < 0:
        layout.removeRow(layout.rowCount() - 1)
        nb += 1


def fill_form(form, fields, offset=0):
    resize_form(form, len(fields) + offset)
    layout = form.layout()
    result = []
    for row, field in enumerate(fields):
        label, value = field
        w_item = layout.itemAt(row + offset, Qt.QFormLayout.LabelRole)
        w_label = w_item.widget()
        set_text(w_label, label)
        w_item = layout.itemAt(row + offset, Qt.QFormLayout.FieldRole)
        w_field = w_item.widget()
        set_text(w_field, value)
        result.append((w_label, w_field))
    return result


def load_scan_info_form(widget):
    ui_name = pkg_resources.resource_filename(__package__ + '.ui',
                                              'ScanInfoForm.ui')
    uic.loadUi(ui_name, baseinstance=widget)
    return widget


class ScanInfoForm(Qt.QWidget, TaurusBaseWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        load_scan_info_form(self)

    def setModel(self, doorname):
        super().setModel(doorname)
        if not doorname:
            return
        door = self.getModelObj()
        door.recordDataUpdated.connect(self.onRecordDataUpdated)

    def onRecordDataUpdated(self, record_data):
        data = record_data[1]
        handler = self.event_handler.get(data.get("type"))
        handler and handler(self, data['data'])

    def onStart(self, meta):
        set_text(self.title_value, 'title', meta)
        set_text(self.scan_nb_value, 'serialno', meta)
        set_text(self.start_value, 'starttime', meta)
        set_text(self.end_value, 'endtime', meta)
        set_text(self.status_value, 'Running')

        directory = meta.get('scandir', '')
        self.directory_groupbox.setEnabled(True if directory else False)
        self.directory_groupbox.setTitle('Directory: {}'.format(directory))
        files = meta.get('scanfile', ())
        if isinstance(files, str):
            files = files,
        elif files is None:
            files = ()
        files = [('File:', filename) for filename in files]
        fill_form(self.directory_groupbox, files)

    def onEnd(self, meta):
        set_text(self.end_value, 'endtime', meta)
        set_text(self.status_value, 'Finished')

    event_handler = {
        "data_desc": onStart,
        "record_end": onEnd
    }


def load_scan_point_form(widget):
    ui_name = pkg_resources.resource_filename(__package__ + '.ui',
                                              'ScanPointForm.ui')
    uic.loadUi(ui_name, baseinstance=widget)
    return widget


class ScanPointForm(Qt.QWidget, TaurusBaseWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        load_scan_point_form(self)
        self._in_scan = False

    def setModel(self, doorname):
        super().setModel(doorname)
        if not doorname:
            return
        door = self.getModelObj()
        door.recordDataUpdated.connect(self.onRecordDataUpdated)

    def onRecordDataUpdated(self, record_data):
        data = record_data[1]
        handler = self.event_handler.get(data.get("type"))
        handler and handler(self, data['data'])

    def onStart(self, meta):
        set_text(self.scan_nb_value, 'serialno', meta)
        cols = meta['column_desc']
        col_labels = [(c['label']+':', '') for c in cols]
        fields = fill_form(self, col_labels, 1)
        self.fields = {col['name']: field for col, field in zip(cols, fields)}
        self._in_scan = True

    def onPoint(self, point):
        if self._in_scan:
            for name, value in point.items():
                set_text(self.fields[name][1], value)

    def onEnd(self, meta):
        self._in_scan = False

    event_handler = {
        "data_desc": onStart,
        "record_data": onPoint,
        "record_end": onEnd
    }


class ScanPlotWidget(MultiPlotWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = PlotManager(self)
        self.setModel = self.manager.setModel
        self.setGroupMode = self.manager.setGroupMode


class ScanPlotWindow(Qt.QMainWindow):

    def __init__(self, parent=None):
        super().__init__()
        plot_widget = ScanPlotWidget(parent=self)
        self.setCentralWidget(plot_widget)
        self.plotWidget = self.centralWidget
        self.setModel = plot_widget.setModel
        self.setGroupMode = plot_widget.setGroupMode
        sbar = self.statusBar()
        sbar.showMessage("Ready!")
        plot_widget.manager.newShortMessage.connect(sbar.showMessage)


def load_scan_window(widget):
    ui_name = pkg_resources.resource_filename(__package__ + '.ui',
                                              'ScanWindow.ui')
    uic.loadUi(ui_name, baseinstance=widget)
    return widget


class ScanWindow(Qt.QMainWindow):

    def __init__(self, parent=None):
        super().__init__()
        load_scan_window(self)
        sbar = self.statusBar()
        sbar.showMessage("Ready!")
        self.plot_widget.manager.newShortMessage.connect(sbar.showMessage)

    def setModel(self, model):
        self.plot_widget.setModel(model)
        self.info_form.setModel(model)
        self.point_form.setModel(model)



class ShowScanOnline(DynamicPlotManager):

    def __init__(self, parent):
        DynamicPlotManager.__init__(self, parent=parent)
        Qt.qApp.SDM.connectWriter("shortMessage", self, 'newShortMessage')

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

    widget = ScanWindow()
    widget.plot_widget.setGroupMode(group)
    widget.setModel(door)
    widget.show()
    return app.exec_()


if __name__ == "__main__":
    main()
