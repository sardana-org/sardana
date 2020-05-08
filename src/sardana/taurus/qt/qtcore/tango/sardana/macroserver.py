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

"""MacroServer extension for taurus Qt"""

__all__ = ["QDoor", "QMacroServer",
           "MacroServerMessageErrorHandler", "registerExtensions"]

import copy
from taurus.core.taurusbasetypes import TaurusEventType
from taurus.external.qt import Qt, compat

from sardana.taurus.core.tango.sardana.macroserver import BaseMacroServer, \
    BaseDoor

CHANGE_EVTS = TaurusEventType.Change, TaurusEventType.Periodic


class QDoor(BaseDoor, Qt.QObject):

    __pyqtSignals__ = ["resultUpdated",
                       "recordDataUpdated", "macroStatusUpdated"]
    __pyqtSignals__ += ["%sUpdated" % l.lower() for l in BaseDoor.log_streams]

    EXP_DESC_ENV_VARS = ['ActiveMntGrp', 'ScanDir', 'ScanFile',
                         'DataCompressionRank', 'PreScanSnapshot']

    # sometimes we emit None hence the type is object
    # (but most of the data are passed with type list)
    resultUpdated = Qt.pyqtSignal(compat.PY_OBJECT)
    recordDataUpdated = Qt.pyqtSignal(compat.PY_OBJECT)
    macroStatusUpdated = Qt.pyqtSignal(compat.PY_OBJECT)
    errorUpdated = Qt.pyqtSignal(compat.PY_OBJECT)
    warningUpdated = Qt.pyqtSignal(compat.PY_OBJECT)
    infoUpdated = Qt.pyqtSignal(compat.PY_OBJECT)
    outputUpdated = Qt.pyqtSignal(compat.PY_OBJECT)
    debugUpdated = Qt.pyqtSignal(compat.PY_OBJECT)
    experimentConfigurationChanged = Qt.pyqtSignal(compat.PY_OBJECT)
    elementsChanged = Qt.pyqtSignal()
    environmentChanged = Qt.pyqtSignal()

    def __init__(self, name, qt_parent=None, **kw):
        self.call__init__wo_kw(Qt.QObject, qt_parent)
        self.call__init__(BaseDoor, name, **kw)
        self._mntgrps_connected = []
        self._use_experiment_configuration = False
        self._connections_prepared = False

    def resultReceived(self, log_name, result):
        res = BaseDoor.resultReceived(self, log_name, result)
        self.resultUpdated.emit(res)
        return res

    def recordDataReceived(self, s, t, v):
        if t not in CHANGE_EVTS:
            return
        res = BaseDoor.recordDataReceived(self, s, t, v)
        self.recordDataUpdated.emit(res)
        return res

    def macroStatusReceived(self, s, t, v):
        res = BaseDoor.macroStatusReceived(self, s, t, v)
        if t == TaurusEventType.Error:
            macro = None
        else:
            macro = self.getRunningMacro()
        if macro is None:
            return

        self.macroStatusUpdated.emit((macro, res))
        return res

    def logReceived(self, log_name, output):
        res = BaseDoor.logReceived(self, log_name, output)
        log_name = log_name.lower()
        logUpdated = getattr(self, "%sUpdated" % log_name)
        logUpdated.emit(output)
        return res

    def _prepare_connections(self):
        if not self._use_experiment_configuration and \
                not self._connections_prepared:
            self.macro_server.environmentChanged.connect(
                self._onEnvironmentChanged)
            self.macro_server.elementsChanged.connect(self._elementsChanged)
            self._elementsChanged()
            self._connections_prepared = True

    def _elementsChanged(self):
        mntgrps = self.macro_server.getElementsOfType("MeasurementGroup")
        # one or more measurement group was deleted
        mntgrp_changed = len(self._mntgrps_connected) > len(mntgrps)
        new_mntgrps_connected = []
        for name, mg in list(mntgrps.items()):
            if name not in self._mntgrps_connected:
                mntgrp_changed = True  # this measurement group is new
                obj = mg.getObj()
                obj.configurationChanged.connect(
                    self._onExperimentConfigurationChanged)
            new_mntgrps_connected.append(name)
        self._mntgrps_connected = new_mntgrps_connected

        if mntgrp_changed:
            self._onExperimentConfigurationChanged()

    def _onEnvironmentChanged(self, env_changes):
        """
        Filter environment changes that affect to the experiment
        configuration.

        :param env_changes: tuple with three elements in the following order:

        * added (environment variables added)
        * removed (environment variables removed)
        * changed (environment variables changed)

        :type env_changes: :obj:`tuple`
        """
        env_exp_changed = False
        # Filter only the Environment added/removed/changes related with
        # the experiment, not for all.
        for envs in env_changes:
            val = envs.intersection(self.EXP_DESC_ENV_VARS)
            if len(val) > 0:
                env_exp_changed = True
                break
        if not env_exp_changed:
            return
        self._onExperimentConfigurationChanged()

    def _onExperimentConfigurationChanged(self, *args):
        conf = copy.deepcopy(BaseDoor.getExperimentConfiguration(self))
        self.experimentConfigurationChanged.emit(conf)

    def getExperimentConfigurationObj(self):
        self._prepare_connections()
        return BaseDoor.getExperimentConfigurationObj(self)

    def getExperimentConfiguration(self):
        self._prepare_connections()
        return BaseDoor.getExperimentConfiguration(self)


class QMacroServer(BaseMacroServer, Qt.QObject):

    # TODO: Choose and homogenize signals named ...Updated and ...Changed.
    #  e.g: there should exist only one signal for elementsUpdated
    #  and elementsChanged.
    typesUpdated = Qt.pyqtSignal()
    elementsUpdated = Qt.pyqtSignal()
    elementsChanged = Qt.pyqtSignal()
    macrosUpdated = Qt.pyqtSignal()
    environmentChanged = Qt.pyqtSignal(compat.PY_OBJECT)

    def __init__(self, name, qt_parent=None, **kw):
        self.call__init__wo_kw(Qt.QObject, qt_parent)
        self.call__init__(BaseMacroServer, name, **kw)

    # TODO: The following three methods are not used, and are not
    #  implemented in the base class 'BaseMacroServer': Implement them.
    #  (Now commented because they give conflicts with new style PyQt signals).
    # def typesChanged(self, s, t, v):
    #     res = BaseMacroServer.typesChanged(self, s, t, v)
    #     self.typesUpdated.emit()
    #     return res
    #
    # def elementsChanged(self, s, t, v):
    #     res = BaseMacroServer.elementsChanged(self, s, t, v)
    #     self.elementsUpdated.emit()
    #     return res
    #
    # def macrosChanged(self, s, t, v):
    #     res = BaseMacroServer.macrosChanged(self, s, t, v)
    #     self.macrosUpdated.emit()
    #     return res

    def on_elements_changed(self, s, t, v):
        ret = added, removed, changed = \
            BaseMacroServer.on_elements_changed(self, s, t, v)

        macros, elements = 0, 0
        for element in set.union(added, removed, changed):
            if "MacroCode" in element.interfaces:
                macros += 1
            elements += 1
            if elements and macros:
                break
        if elements:
            self.elementsChanged.emit()
        if macros:
            self.macrosUpdated.emit()
        return ret

    def on_environment_changed(self, s, t, v):
        ret = added, removed, changed = \
            BaseMacroServer.on_environment_changed(self, s, t, v)
        if added or removed or changed:
            self.environmentChanged.emit(ret)
        return ret


# ugly access to qtgui level: in future find a better way to register error
# handlers, maybe in TangoFactory & TaurusManager

from taurus.qt.qtgui.panel import TaurusMessageErrorHandler


class MacroServerMessageErrorHandler(TaurusMessageErrorHandler):

    def setError(self, err_type=None, err_value=None, err_traceback=None):
        """Translates the given error object into an HTML string and places it
        in the message panel

        :param error: an error object (typically an exception object)
        :type error: object"""

        msgbox = self._msgbox
        msgbox.setText(err_value)
        msg = "<html><body><pre>%s</pre></body></html>" % err_value
        msgbox.setDetailedHtml(msg)

        html_orig = """<html><head><style type="text/css">{style}
            </style></head><body>"""
        exc_info = "".join(err_traceback)
        style = ""
        try:
            import pygments.formatters
            import pygments.lexers
        except Exception:
            pygments = None
        if pygments is not None:
            formatter = pygments.formatters.HtmlFormatter()
            style = formatter.get_style_defs()
        html = html_orig.format(style=style)
        if pygments is None:
            html += "<pre>%s</pre>" % exc_info
        else:
            formatter = pygments.formatters.HtmlFormatter()
            html += pygments.highlight(exc_info,
                                       pygments.lexers.PythonTracebackLexer(

                                       ), formatter)
        html += "</body></html>"
        msgbox.setOriginHtml(html)


def registerExtensions():
    """Registers the macroserver extensions in the
    :class:taurus.core.tango.TangoFactory`"""
    import taurus
    factory = taurus.Factory()
    factory.registerDeviceClass('MacroServer', QMacroServer)
    factory.registerDeviceClass('Door', QDoor)

    # ugly access to qtgui level: in future find a better way to register error
    # handlers, maybe in TangoFactory & TaurusManager
    import sardana.taurus.core.tango.sardana.macro
    import taurus.qt.qtgui.panel
    MacroRunExcep = sardana.taurus.core.tango.sardana.macro.MacroRunException
    TaurusMessagePanel = taurus.qt.qtgui.panel.TaurusMessagePanel

    TaurusMessagePanel.registerErrorHandler(MacroRunExcep,
                                            MacroServerMessageErrorHandler)
