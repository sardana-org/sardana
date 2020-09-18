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
dooroutput.py:
"""

import taurus.core
from taurus.external.qt import Qt



class DoorOutput(Qt.QPlainTextEdit):
    """Widget used for displaying changes of door's attributes: Output, Info, Warning and Error."""

    def __init__(self, parent=None):
        Qt.QPlainTextEdit.__init__(self, parent)
        self.setReadOnly(True)
        self.setFont(Qt.QFont("Courier", 9))
        self.stopAction = Qt.QAction("Stop scrolling", self)
        self.stopAction.setCheckable(True)
        self.stopAction.setChecked(False)
        self._isStopped = False
        self.showDebug = Qt.QAction("Show debug details", self)
        self.showDebug.setCheckable(True)
        self.showDebug.setChecked(False)
        self._isDebugging = False

    def onDoorOutputChanged(self, output):
        """call on output attribute changed"""
        txt = "<font color=\"Black\">"
        if output is None:
            return
        for i, line in enumerate(output):
            if i > 0:
                txt += "<br/>"
            txt += line.replace(' ', '&nbsp;')
        txt += "</font>"
        self.appendHtmlText(txt)

    def onDoorInfoChanged(self, info):
        """call on info attribute changed"""
        txt = "<font color=\"Blue\">"
        if info is None:
            return
        for i, line in enumerate(info):
            if i > 0:
                txt += "<br/>"
            txt += line.replace(' ', '&nbsp;')
        txt += "</font>"
        self.appendHtmlText(txt)

    def onDoorWarningChanged(self, warning):
        """call on warning attribute changed"""
        txt = "<font color=\"Orange\">"
        if warning is None:
            return
        for i, line in enumerate(warning):
            if i > 0:
                txt += "<br/>"
            txt += line.replace(' ', '&nbsp;')
        txt += "</font>"
        self.appendHtmlText(txt)

    def onDoorErrorChanged(self, error):
        """call on error attribute changed"""
        txt = "<font color=\"Red\">"
        if error is None:
            return
        for i, line in enumerate(error):
            if i > 0:
                txt += "<br/>"
            txt += line.replace(' ', '&nbsp;')
        txt += "</font>"
        self.appendHtmlText(txt)

    def onDoorDebugChanged(self, debug):
        """call on debug attribute changed"""
        txt = "<font color=\"Grey\">"
        if self._isDebugging:
            if debug is None:
                return
            for i, line in enumerate(debug):
                if i > 0:
                    txt += "<br/>"
                txt += line.replace(' ', '&nbsp;')
            txt += "</font>"
            self.appendHtmlText(txt)
            if not self._isStopped:
                self.moveCursor(Qt.QTextCursor.End)

    def appendHtmlText(self, text):
        self.appendHtml(text)
        if not self._isStopped:
            self.moveCursor(Qt.QTextCursor.End)

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        clearAction = Qt.QAction("Clear", menu)
        menu.addAction(clearAction)
        menu.addAction(self.stopAction)
        menu.addAction(self.showDebug)
        if not len(self.toPlainText()):
            clearAction.setEnabled(False)

        clearAction.triggered.connect(self.clear)
        self.stopAction.toggled.connect(self.stopScrolling)
        self.showDebug.toggled.connect(self.showDebugDetails)
        menu.exec_(event.globalPos())

    def stopScrolling(self, stop):
        self._isStopped = stop

    def showDebugDetails(self, debug):
        self._isDebugging = debug


class DoorDebug(Qt.QPlainTextEdit):
    """Deprecated. Do not use"""

    """Widget used for displaying changes of door's Debug attribute."""

    def __init__(self, parent=None):
        Qt.QPlainTextEdit.__init__(self, parent)
        self.setReadOnly(True)
        self.setFont(Qt.QFont("Courier", 9))
        self.stopAction = Qt.QAction("Stop scrolling", self)
        self.stopAction.setCheckable(True)
        self.stopAction.setChecked(False)
        self._isStopped = False

        from taurus.core.util.log import warning

        msg = ("DoorDebug is deprecated since version 3.0.3. "
               "Use DoorOutput 'Show debug details' feature instead.")
        warning(msg)

    def onDoorDebugChanged(self, debug):
        """call on debug attribute changed"""
        if debug is None:
            return
        for line in debug:
            self.appendPlainText(line)

        if not self._isStopped:
            self.moveCursor(Qt.QTextCursor.End)

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        clearAction = Qt.QAction("Clear", menu)
        menu.addAction(clearAction)
        menu.addAction(self.stopAction)
        if not len(self.toPlainText()):
            clearAction.setEnabled(False)

        clearAction.triggered.connect(self.clear)
        self.stopAction.toggled.connect(self.stopScrolling)
        menu.exec_(event.globalPos())

    def stopScrolling(self, stop):
        self._isStopped = stop


class DoorResult(Qt.QPlainTextEdit):
    """Widget used for displaying changes of door's Result attribute."""

    def __init__(self, parent=None):
        Qt.QPlainTextEdit.__init__(self, parent)
        self.setReadOnly(True)
        self.setFont(Qt.QFont("Courier", 9))

    def onDoorResultChanged(self, result):
        """call on result attribute changed"""
        if result is None:
            return
        for line in result:
            self.appendPlainText(line)
        self.moveCursor(Qt.QTextCursor.End)

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        clearAction = Qt.QAction("Clear", menu)
        menu.addAction(clearAction)
        if not len(self.toPlainText()):
            clearAction.setEnabled(False)

        clearAction.triggered.connect(self.clear)
        menu.exec_(event.globalPos())


if __name__ == "__main__":
    import sys
    import taurus
    from taurus.core.util.argparse import get_taurus_parser
    from taurus.qt.qtgui.application import TaurusApplication

    parser = get_taurus_parser()
    app = TaurusApplication(sys.argv, cmd_line_parser=parser)
    args = app.get_command_line_args()

    doorOutput = DoorOutput()
    if len(args) == 1:
        door = taurus.Device(args[0])
        door.outputUpdated.connect(doorOutput.onDoorOutputChanged)
        door.infoUpdated.connect(doorOutput.onDoorInfoChanged)
        door.warningUpdated.connect(doorOutput.onDoorWarningChanged)
        door.errorUpdated.connect(doorOutput.onDoorErrorChanged)
        door.debugUpdated.connect(doorOutput.onDoorDebugChanged)

    doorOutput.show()
    sys.exit(app.exec_())
