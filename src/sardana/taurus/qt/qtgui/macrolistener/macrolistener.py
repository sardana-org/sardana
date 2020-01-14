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
This module provides objects to manage macro-related tasks. Its primary use is
to be used within a TaurusGui for managing panels for:
- setting preferences in the sardana control system for data I/O
- displaying results of macro executions, including creating/removing panels
  for plotting results of scans
- editing macros

.. note:: This module was originally implemented in taurus as
          `taurus.qt.qtgui.taurusgui.macrolistener`
"""



from builtins import object

import datetime
import collections

import numpy

try:
    import pyqtgraph
except ImportError:
    pyqtgraph = None

from taurus.external.qt import Qt
from taurus.qt.qtgui.base import TaurusBaseComponent
from taurus.core.util.containers import ArrayBuffer, LoopList

from sardana.taurus.core.tango.sardana import PlotType


__all__ = ['MacroBroker', 'DynamicPlotManager', 'assertPlotAvailability']

__docformat__ = 'restructuredtext'

COLORS = [Qt.QColor(Qt.Qt.red),
          Qt.QColor(Qt.Qt.blue),
          Qt.QColor(Qt.Qt.green),
          Qt.QColor(Qt.Qt.magenta),
          Qt.QColor(Qt.Qt.cyan),
          Qt.QColor(Qt.Qt.yellow),
          Qt.QColor(Qt.Qt.white)]

SYMBOLS = ['o', 't', 't1', 't2', 't3', 's', 'p']

CURVE_STYLES = [(color, symbol) for symbol in SYMBOLS for color in COLORS]

NO_PLOT_MESSAGE = 'Plots cannot be displayed (pyqtgraph not installed)'


def assertPlotAvailability(exit_on_error=True):
    if pyqtgraph is None:
        Qt.QMessageBox.critical(None, 'Plot error', NO_PLOT_MESSAGE)
        if exit_on_error:
            exit(1)


class ScanPlot(Qt.QWidget):

    def __init__(self, x_axis, parent=None):
        super().__init__(parent)
        layout = Qt.QVBoxLayout(self)
#        layout.setContentsMargins(0, 0, 0, 0)
        self.plot_widget = self._buildPlotWidget(x_axis)
        layout.addWidget(self.plot_widget)
        self.x_axis = dict(x_axis, data=[])
        self.channels = []

    def _buildPlotWidget(self, x_axis):
        available = pyqtgraph is not None
        if available:
            widget = pyqtgraph.PlotWidget(labels=dict(bottom=x_axis['label']))
            widget.showGrid(x=True, y=True)
            widget.scan_legend = widget.addLegend()
        else:
            widget = Qt.QLabel(NO_PLOT_MESSAGE)
        widget.plot_available = available
        return widget

    def prepare(self, channels, nb_points=None):
        widget = self.plot_widget
        if not widget.plot_available:
            return
        widget.clear()
        # legend is not properly updated when we clear the plot
        widget.scan_legend.scene().removeItem(widget.scan_legend)
        widget.scan_legend = widget.addLegend()

        nb_points = 2**16 if nb_points is None else nb_points
        self.x_axis['data'] = ArrayBuffer(numpy.full(nb_points, numpy.nan))
        self.channels = []
        styles = LoopList(CURVE_STYLES)
        for channel in channels:
            # don't use symbol: slows down plotting
            pen, _ = styles.next()
            item = widget.plot(name=channel['label'], pen=pen)
            channel = dict(channel, plot_item=item,
                           data=ArrayBuffer(numpy.full(nb_points, numpy.nan)))
            self.channels.append(channel)

    def onNewPoint(self, data):
        if not self.plot_widget.plot_available:
            return
        x_data = self.x_axis['data']
        x_data.append(data[self.x_axis['name']])
        for channel in self.channels:
            name = channel['name']
            y_data = channel['data']
            plot_item = channel['plot_item']
            y_data.append(data[name])
            plot_item.setData(x_data.contents(), y_data.contents())


class DynamicPlotManager(Qt.QObject, TaurusBaseComponent):
    '''This is a manager of plots related to the execution of macros.
    It dynamically creates/removes plots according to the configuration made by
    an ExperimentConfiguration widget.

    Currently it supports only 1D scan trends (2D scans are only half-baked)

    To use it simply instantiate it and pass it a door name as a model. You may
    want to call :meth:`onExpConfChanged` to update the configuration being
    used.
    '''

    plots_available = pyqtgraph is not None

    newShortMessage = Qt.pyqtSignal('QString')

    def __init__(self, parent=None):
        Qt.QObject.__init__(self, parent)
        TaurusBaseComponent.__init__(self, self.__class__.__name__)

        self.__panels = {}

        self._trends1d = {}
        self._trends2d = {}
        Qt.qApp.SDM.connectWriter("shortMessage", self, 'newShortMessage')

    def setModel(self, doorname):
        '''reimplemented from :meth:`TaurusBaseComponent`

        :param doorname: (str) device name corresponding to a Door device.
        '''
        TaurusBaseComponent.setModel(self, doorname)
        # self._onDoorChanged(doorname)
        if not doorname:
            return
        self.door = self.getModelObj()
        if not isinstance(self.door, Qt.QObject):
            msg = "Unexpected type (%s) for %s" % (repr(type(self.door)),
                                                   doorname)
            Qt.QMessageBox.critical(
                self.parent(), 'Door connection error', msg)
            return

        self._checkJsonRecorder()

        self.door.recordDataUpdated.connect(self.onRecordDataUpdated)
        self.old_arg = None
        self.message_template = 'Ready!'

    def _checkJsonRecorder(self):
        '''Checks if JsonRecorder env var is set and offers to set it'''
        door = self.getModelObj()
        if 'JsonRecorder' not in door.getEnvironment():
            msg = ('JsonRecorder environment variable is not set, but it '
                   + 'is needed for displaying trend plots.\n'
                   + 'Enable it globally for %s?') % door.getFullName()
            result = Qt.QMessageBox.question(
                self.parent(), 'JsonRecorder not set', msg,
                Qt.QMessageBox.Yes | Qt.QMessageBox.No)
            if result == Qt.QMessageBox.Yes:
                door.putEnvironment('JsonRecorder', True)
                self.info('JsonRecorder Enabled for %s' % door.getFullName())

    def onRecordDataUpdated(self, arg):
        """
        Receive RecordDataUpdated tuple, the method detects when the event
        type is 'data_desc' (come with new data description), it will call
        to 'onExpConfChanged' to refresh the plots configuration,
        adding/removing plots based in the new Experimental configuration.

        Note: After the plots reorder, the data description event is resend
        to reconfig the plot with the new data description.

        :param arg: RecordData Tuple
        :return:
        """

        # Filter events sent by itself
        if arg == self.old_arg:
            return

        self.old_arg = arg

        data = arg[1]
        if 'type' in data:
            event_type = data['type']
            if event_type == 'data_desc':
                self.prepare(data)
            elif event_type == 'record_data':
                self.newPoint(data)
            elif event_type == 'record_end':
                self.end(data)

    def prepare(self, data_desc):
        """
        Prepare UI for a new scan. Rebuilds plots as necessary to adapt to the
        new scan channels and moveables
        """
        data = data_desc['data']
        # dict< axis: list<channels> >
        trends1d = collections.defaultdict(list)
        column_map = {col['name']: col for col in data['column_desc']}

        # build a map of axis and corresponding channels
        for column in data['column_desc']:
            ptype = column.get('plot_type', PlotType.No)
            if ptype == PlotType.No:
                continue
            ch_name = column['name']
            axes = []
            for axis in column.get('plot_axes', ()):
                if axis == '<idx>':
                    axis = 'point_nb'
                axes.append(axis)
            if ptype == PlotType.Spectrum:
                ndim = column.get('ndim', 0) or 0
                if ndim == 0:  # this is a trend
                    for axis in axes:
                        trends1d[axis].append(column)
                else:
                    self.warning('Cannot create spectrum plot for %d dims '
                                 'channel %r', ndim, ch_name)
            elif ptype == PlotType.Image:
                self.warning('Unsupported image plot for %s', ch_name)

        # build list of widgets: one plot for each axis. Widgets are recycled
        # from the previous scans if possible to avoid rearranging the GUI
        for axis in trends1d:
            if axis not in self._trends1d:
                x_axis = column_map[axis]
                w = ScanPlot(x_axis)
                title = 'Trend1D - ' + x_axis['label']
                self.createPanel(w, title, registerconfig=False,
                                 permanent=False)
                self._trends1d[axis] = title

        # remove widgets from previous scans which are not used in current scan
        for axis in tuple(self._trends1d):
            if axis not in trends1d:
                self.removePanel(self._trends1d[axis])
                del self._trends1d[axis]

        # prepare each plot widget with list of channels
        nb_points = data.get('total_scan_intervals', 2**16) + 1
        for axis, panel_name in self._trends1d.items():
            widget = self.getPanelWidget(panel_name)
            widget.prepare(trends1d[axis], nb_points)

        # build status message
        serialno = 'Scan #{}'.format(data.get('serialno', '?'))
        title = data.get('title', 'unnamed operation')
        if data.get('scandir') and data.get('scanfile'):
            scan_file = data['scanfile']
            if isinstance(scan_file, (list, tuple)):
                scan_file = '&'.join(data['scanfile'])
            saving = data['scandir'] + '/' + scan_file
        else:
            saving = 'no saving!'
        started = 'Started ' + data.get('starttime', '?')
        progress = '{progress}'
        self.message_template = ' | '.join((serialno, title, started,
                                            progress, saving))
        self.newShortMessage.emit(
            self.message_template.format(progress='Preparing...'))

    def newPoint(self, point):
        data = point['data']
        for _, panel_name in self._trends1d.items():
            widget = self.getPanelWidget(panel_name)
            widget.onNewPoint(data)
        point_nb = 'Point #{}'.format(data['point_nb'])
        msg = self.message_template.format(progress=point_nb)
        self.newShortMessage.emit(msg)

    def end(self, end_data):
        data = end_data['data']
        progress = 'Ended {}'.format(data['endtime'])
        msg = self.message_template.format(progress=progress)
        self.newShortMessage.emit(msg)

    def createPanel(self, widget, name, **kwargs):
        '''Creates a "panel" from a widget. In this basic implementation this
        means that the widgets is shown as a non-modal top window

        :param widget: (QWidget) widget to be used for the panel
        :param name: (str) name of the panel. Must be unique.

        Note: for backawards compatibility, this implementation accepts
        arbitrary keyword arguments which are just ignored
        '''
        widget.setWindowTitle(name)
        widget.show()
        self.__panels[name] = widget

    def getPanelWidget(self, name):
        '''Returns the widget associated to a panel name

        :param name: (str) name of the panel. KeyError is raised if not found

        :return: (QWidget)
        '''
        return self.__panels[name]

    def removePanel(self, name):
        '''stop managing the given panel

        :param name: (str) name of the panel'''
        widget = self.__panels.pop(name)
        if hasattr(widget, 'setModel'):
            widget.setModel(None)
        widget.setParent(None)
        widget.close()

    def removePanels(self, names=None):
        '''removes panels.

        :param names: (seq<str>) names of the panels to be removed. If None is
                      given (default), all the panels are removed.
        '''
        if names is None:
            names = (list(self._trends1d.values())
                     + list(self._trends2d.values()))
            # TODO: do the same for other temporary panels
        for pname in names:
            self.removePanel(pname)


class MacroBroker(DynamicPlotManager):
    '''A manager of all macro-related panels of a TaurusGui.

    It creates, destroys and manages connections for the following objects:

        - Macro Configuration dialog
        - Experiment Configuration panel
        - Macro Executor panel
        - Sequencer panel
        - Macro description viewer
        - Door output, result and debug panels
        - Macro editor
        - Macro "panic" button (to abort macros)
        - Dynamic plots (see :class:`DynamicPlotManager`)
    '''

    def __init__(self, parent):
        '''Passing the parent object (the main window) is mandatory'''
        DynamicPlotManager.__init__(self, parent)

        self._createPermanentPanels()

        # connect the broker to shared data
        Qt.qApp.SDM.connectReader("doorName", self.setModel)

    def setModel(self, doorname):
        ''' Reimplemented from :class:`DynamicPlotManager`.'''
        # disconnect the previous door
        door = self.getModelObj()
        if door is not None:  # disconnect it from *all* shared data providing
            SDM = Qt.qApp.SDM
            try:
                SDM.disconnectWriter("macroStatus", door,
                                     "macroStatusUpdated")
            except Exception:
                self.info("Could not disconnect macroStatusUpdated")
            try:
                SDM.disconnectWriter("doorOutputChanged", door,
                                     "outputUpdated")
            except Exception:
                self.info("Could not disconnect outputUpdated")
            try:
                SDM.disconnectWriter("doorInfoChanged", door, "infoUpdated")
            except Exception:
                self.info("Could not disconnect infoUpdated")
            try:
                SDM.disconnectWriter("doorWarningChanged", door,
                                     "warningUpdated")
            except Exception:
                self.info("Could not disconnect warningUpdated")
            try:
                SDM.disconnectWriter("doorErrorChanged", door, "errorUpdated")
            except Exception:
                self.info("Could not disconnect errorUpdated")
            try:
                SDM.disconnectWriter("doorDebugChanged", door, "debugUpdated")
            except Exception:
                self.info("Could not disconnect debugUpdated")
            try:
                SDM.disconnectWriter("doorResultChanged", door,
                                     "resultUpdated")
            except Exception:
                self.info("Could not disconnect resultUpdated")
            try:
                SDM.disconnectWriter("expConfChanged", door,
                                     "experimentConfigurationChanged")
            except Exception:
                self.info(
                    "Could not disconnect experimentConfigurationChanged")
        # set the model
        DynamicPlotManager.setModel(self, doorname)

        # connect the new door
        door = self.getModelObj()
        if door is not None:
            SDM = Qt.qApp.SDM
            SDM.connectWriter("macroStatus", door, "macroStatusUpdated")
            SDM.connectWriter("doorOutputChanged", door, "outputUpdated")
            SDM.connectWriter("doorInfoChanged", door, "infoUpdated")
            SDM.connectWriter("doorWarningChanged", door, "warningUpdated")
            SDM.connectWriter("doorErrorChanged", door, "errorUpdated")
            SDM.connectWriter("doorDebugChanged", door, "debugUpdated")
            SDM.connectWriter("doorResultChanged", door, "resultUpdated")
            SDM.connectWriter("expConfChanged", door,
                              "experimentConfigurationChanged")

    def _createPermanentPanels(self):
        '''creates panels on the main window'''
        from sardana.taurus.qt.qtgui.extra_macroexecutor import \
            TaurusMacroExecutorWidget, TaurusSequencerWidget, \
            TaurusMacroConfigurationDialog, TaurusMacroDescriptionViewer, \
            DoorOutput, DoorDebug, DoorResult

        from sardana.taurus.qt.qtgui.extra_sardana import \
            ExpDescriptionEditor

        mainwindow = self.parent()

        # Create macroconfiguration dialog & action
        self.__macroConfigurationDialog = \
            TaurusMacroConfigurationDialog(mainwindow)
        self.macroConfigurationAction = mainwindow.taurusMenu.addAction(
            Qt.QIcon.fromTheme("preferences-system-session"),
            "Macro execution configuration...",
            self.__macroConfigurationDialog.show)

        SDM = Qt.qApp.SDM
        SDM.connectReader("macroserverName",
                          self.__macroConfigurationDialog.selectMacroServer)
        SDM.connectReader("doorName",
                          self.__macroConfigurationDialog.selectDoor)
        SDM.connectWriter("macroserverName", self.__macroConfigurationDialog,
                          'macroserverNameChanged')
        SDM.connectWriter("doorName", self.__macroConfigurationDialog,
                          'doorNameChanged')

        # Create ExpDescriptionEditor dialog
        self.__expDescriptionEditor = ExpDescriptionEditor()
        SDM.connectReader("doorName", self.__expDescriptionEditor.setModel)
        mainwindow.createPanel(self.__expDescriptionEditor,
                               'Experiment Config',
                               registerconfig=True,
                               icon=Qt.QIcon.fromTheme('preferences-system'),
                               permanent=True)
        ###############################
        # TODO: These lines can be removed once the door does emit
        # "experimentConfigurationChanged" signals
        SDM.connectWriter("expConfChanged", self.__expDescriptionEditor,
                          "experimentConfigurationChanged")
        ################################

        # put a Macro Executor
        self.__macroExecutor = TaurusMacroExecutorWidget()
        SDM.connectReader("macroserverName", self.__macroExecutor.setModel)
        SDM.connectReader("doorName", self.__macroExecutor.onDoorChanged)
        SDM.connectReader("macroStatus",
                          self.__macroExecutor.onMacroStatusUpdated)
        SDM.connectWriter("macroName", self.__macroExecutor,
                          "macroNameChanged")
        SDM.connectWriter("executionStarted", self.__macroExecutor,
                          "macroStarted")
        SDM.connectWriter("plotablesFilter", self.__macroExecutor,
                          "plotablesFilterChanged")
        SDM.connectWriter("shortMessage", self.__macroExecutor,
                          "shortMessageEmitted")
        mainwindow.createPanel(self.__macroExecutor, 'Macros',
                               registerconfig=True, permanent=True)

        # put a Sequencer
        self.__sequencer = TaurusSequencerWidget()
        SDM.connectReader("macroserverName", self.__sequencer.setModel)
        SDM.connectReader("doorName", self.__sequencer.onDoorChanged)
        SDM.connectReader("macroStatus",
                          self.__sequencer.onMacroStatusUpdated)
        SDM.connectWriter("macroName", self.__sequencer.tree,
                          "macroNameChanged")
        SDM.connectWriter("macroName", self.__sequencer,
                          "macroNameChanged")
        SDM.connectWriter("executionStarted", self.__sequencer,
                          "macroStarted")
        SDM.connectWriter("plotablesFilter", self.__sequencer,
                          "plotablesFilterChanged")
        SDM.connectWriter("shortMessage", self.__sequencer,
                          "shortMessageEmitted")
        mainwindow.createPanel(self.__sequencer, 'Sequences',
                               registerconfig=True, permanent=True)

        # puts a macrodescriptionviewer
        self.__macroDescriptionViewer = TaurusMacroDescriptionViewer()
        SDM.connectReader("macroserverName",
                          self.__macroDescriptionViewer.setModel)
        SDM.connectReader("macroName",
                          self.__macroDescriptionViewer.onMacroNameChanged)
        mainwindow.createPanel(self.__macroDescriptionViewer,
                               'MacroDescription', registerconfig=True,
                               permanent=True)

        # puts a doorOutput
        self.__doorOutput = DoorOutput()
        SDM.connectReader("doorOutputChanged",
                          self.__doorOutput.onDoorOutputChanged)
        SDM.connectReader("doorInfoChanged",
                          self.__doorOutput.onDoorInfoChanged)
        SDM.connectReader("doorWarningChanged",
                          self.__doorOutput.onDoorWarningChanged)
        SDM.connectReader("doorErrorChanged",
                          self.__doorOutput.onDoorErrorChanged)
        SDM.connectReader("doorDebugChanged",
                          self.__doorOutput.onDoorDebugChanged)
        mainwindow.createPanel(self.__doorOutput, 'DoorOutput',
                               registerconfig=False, permanent=True)

        # puts doorResult
        self.__doorResult = DoorResult(mainwindow)
        SDM.connectReader("doorResultChanged",
                          self.__doorResult.onDoorResultChanged)
        mainwindow.createPanel(self.__doorResult, 'DoorResult',
                               registerconfig=False, permanent=True)

        # puts sardanaEditor
        # self.__sardanaEditor = SardanaEditor()
        # SDM.connectReader("macroserverName", self.__sardanaEditor.setModel)
        # mainwindow.createPanel(self.__sardanaEditor, 'SardanaEditor',
        #                        registerconfig=False, permanent=True)

        # add panic button for aborting the door
        text = "Panic Button: stops the pool (double-click for abort)"
        self.doorAbortAction = mainwindow.jorgsBar.addAction(
            Qt.QIcon("actions:process-stop.svg"),
            text, self.__onDoorAbort)

        # store beginning of times as a datetime
        self.__lastAbortTime = datetime.datetime(1, 1, 1)

        # store doubleclick interval as a timedelta
        td = datetime.timedelta(0, 0, 1000 * Qt.qApp.doubleClickInterval())
        self.__doubleclickInterval = td

    def __onDoorAbort(self):
        '''slot to be called when the abort action is triggered.
        It sends stop command to the pools (or abort if the action
        has been triggered twice in less than self.__doubleclickInterval

        .. note:: An abort command is always preceded by an stop command
        '''
        # decide whether to send stop or abort
        now = datetime.datetime.now()
        if now - self.__lastAbortTime < self.__doubleclickInterval:
            cmd = 'abort'
        else:
            cmd = 'stop'

        door = self.getModelObj()

        # abort the door
        door.command_inout('abort')
        # send stop/abort to all pools
        pools = door.macro_server.getElementsOfType('Pool')
        for pool in list(pools.values()):
            self.info('Sending %s command to %s' % (cmd, pool.getFullName()))
            try:
                pool.getObj().command_inout(cmd)
            except Exception:
                self.info('%s command failed on %s', cmd, pool.getFullName(),
                          exc_info=1)
        self.newShortMessage.emit("%s command sent to all pools" % cmd)
        self.__lastAbortTime = now

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


if __name__ == "__main__":
    import sys
    from taurus.qt.qtgui.application import TaurusApplication

    app = TaurusApplication()

    b = DynamicPlotManager(None)

    b.setModel('door/cp1/1')

    print('...')
    sys.exit(app.exec_())
