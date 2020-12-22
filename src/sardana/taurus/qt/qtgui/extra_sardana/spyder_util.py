#!/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
##
# This file is part of Sardana
##
# http://www.sardana-controls.org/
##
# Copyright 2020 DESY
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
Functions vendored from Spyder.

.. note::
   
In comparison to original Spyder code, this code was modified -
it drops compatiblity layer for Python 2/3 and PyQt 4/5.
Right now it will only work for Python3 and PyQt5.
"""

import sys

from taurus.external.qt import Qt


class SpyderAction(Qt.QAction):
    """Spyder QAction class wrapper to handle cross platform patches."""

    def __init__(self, *args, **kwargs):
        """Spyder QAction class wrapper to handle cross platform patches."""
        super(SpyderAction, self).__init__(*args, **kwargs)
        if sys.platform == "darwin":
            self.setIconVisibleInMenu(False)

    def __str__(self):
        return "SpyderAction('{0}')".format(self.text())

    def __repr__(self):
        return "SpyderAction('{0}')".format(self.text())


def create_action(parent, text, shortcut=None, icon=None, tip=None,
                  toggled=None, triggered=None, data=None, menurole=None,
                  context=Qt.WindowShortcut):
    """Create a QAction"""
    action = SpyderAction(text, parent)
    if triggered is not None:
        action.triggered.connect(triggered)
    if toggled is not None:
        action.toggled.connect(toggled)
        action.setCheckable(True)
    if icon is not None:
        action.setIcon(icon)
    if tip is not None:
        action.setToolTip(tip)
        action.setStatusTip(tip)
    if data is not None:
        action.setData(data)
    if menurole is not None:
        action.setMenuRole(menurole)

    # Workround for Mac because setting context=Qt.WidgetShortcut
    # there doesn't have any effect
    if sys.platform == 'darwin':
        action._shown_shortcut = None
        if context == Qt.WidgetShortcut:
            if shortcut is not None:
                action._shown_shortcut = shortcut
            else:
                # This is going to be filled by
                # main.register_shortcut
                action._shown_shortcut = 'missing'
        else:
            if shortcut is not None:
                action.setShortcut(shortcut)
            action.setShortcutContext(context)
    else:
        if shortcut is not None:
            action.setShortcut(shortcut)
        action.setShortcutContext(context)

    return action
