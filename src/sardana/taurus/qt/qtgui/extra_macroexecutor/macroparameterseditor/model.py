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
model.py:
"""

import copy
from lxml import etree

from taurus.external.qt import Qt

from sardana.taurus.core.tango.sardana import macro
from sardana.taurus.qt.qtgui.extra_macroexecutor import globals
from sardana.macroserver.msparameter import Optional


class ParamEditorModel(Qt.QAbstractItemModel):

    def __init__(self, parent=None):
        Qt.QAbstractItemModel.__init__(self, parent)
        self.columns = 2
        self.setRoot()
        self.headers = ["Parameter", "Value"]

    def root(self):
        return self._root

    def setRoot(self, node=None):
        self.beginResetModel()
        if node is None:
            node = macro.MacroNode()
        self._root = node
        self.endResetModel()

    def flags(self, index):
        if index.column() == 0:
            return Qt.Qt.ItemIsEnabled | Qt.Qt.ItemIsSelectable

        node = self.nodeFromIndex(index)

        if (index.column() == 1 and
                isinstance(node, macro.SingleParamNode) and
                not node.type() in globals.EDITOR_NONEDITABLE_PARAMS):
            return Qt.Qt.ItemIsEnabled | Qt.Qt.ItemIsEditable
        return Qt.Qt.ItemIsEnabled

    def _insertRow(self, parentIndex, node=None, row=-1):
        parentNode = self.nodeFromIndex(parentIndex)

        if row == -1:
            row = len(parentNode)

        if node is None:
            node = parentNode.newRepeat()

        self.beginInsertRows(parentIndex, row, row)
        row = parentNode.insertChild(node, row)
        self.endInsertRows()

        return self.index(row, 0, parentIndex)

    def _removeRow(self, index):
        """This method is used remove macro (pased via index)"""
        node = self.nodeFromIndex(index)
        parentIndex = index.parent()
        parentNode = self.nodeFromIndex(parentIndex)
        row = parentNode.rowOfChild(node)
        self.beginRemoveRows(parentIndex, row, row)
        parentNode.removeChild(node)
        self.endRemoveRows()

    def _upRow(self, index):
        node = self.nodeFromIndex(index)
        parentIndex = index.parent()
        parentNode = self.nodeFromIndex(parentIndex)
        row = parentNode.rowOfChild(node)
        self._removeRow(index)
        newIndex = self._insertRow(parentIndex, node, row - 1)
        parentNode.arrangeIndexes()
        return newIndex

    def _downRow(self, index):
        node = self.nodeFromIndex(index)
        parentIndex = index.parent()
        parentNode = self.nodeFromIndex(parentIndex)
        row = parentNode.rowOfChild(node)
        self._removeRow(index)
        newIndex = self._insertRow(parentIndex, node, row + 1)
        parentNode.arrangeIndexes()
        return newIndex

    def duplicateNode(self, index):
        node_to_duplicate = self.nodeFromIndex(index)
        parentIndex = index.parent()
        parentNode = self.nodeFromIndex(parentIndex)
        node = copy.deepcopy(node_to_duplicate)
        self._insertRow(parentIndex, node, -1)
        if isinstance(parentNode, macro.RepeatParamNode):
            parentNode.arrangeIndexes()

    def addRepeat(self, index, callReset=True):
        paramRepeatNode = self.nodeFromIndex(index)
        paramRepeatNode.addRepeat()
        if callReset:
            self.beginResetModel()
            self.endResetModel()

    def delRepeat(self, index, callReset=True):
        branchIndex = self.parent(index)
        branch = self.nodeFromIndex(branchIndex)
        child = self.nodeFromIndex(index)
        branch.removeChild(child)
        if callReset:
            self.beginResetModel()
            self.endResetModel()

    def upRepeat(self, index, callReset=True):
        branchIndex = self.parent(index)
        branch = self.nodeFromIndex(branchIndex)
        child = self.nodeFromIndex(index)
        branch.upChild(child)
        if callReset:
            self.beginResetModel()
            self.endResetModel()

    def downRepeat(self, index, callReset=True):
        branchIndex = self.parent(index)
        branch = self.nodeFromIndex(branchIndex)
        child = self.nodeFromIndex(index)
        branch.downChild(child)
        if callReset:
            self.beginResetModel()
            self.endResetModel()

    def DuplicateRepeat(self, index, callReset=True):
        branchIndex = self.parent(index)
        branch = self.nodeFromIndex(branchIndex)
        child = self.nodeFromIndex(index)
        branch.downChild(child)
        if callReset:
            self.beginResetModel()
            self.endResetModel()

    def rowCount(self, index):
        node = self.nodeFromIndex(index)
        if node is None or isinstance(node, macro.SingleParamNode):
            return 0
        return len(node)

    def columnCount(self, parent):
        return self.columns

    def data(self, index, role):
        if not index.isValid() or not (0 <= index.row() < self.rowCount(index.parent())):
            return None

        if role == Qt.Qt.DisplayRole:
            node = self.nodeFromIndex(index)
            if index.column() == 0:
                return node.name()
            elif index.column() == 1:
                value = node.value()
                if value is None:
                    value = node.defValue()
                    if value == Optional:
                        # TODO: treat optional parameters
                        value = None
                return str(value)
        return None

    def setData(self, index, value, role=Qt.Qt.EditRole):
        node = self.nodeFromIndex(index)
#        if index.isValid() and 0 <= index.row() < len(node.parent()):
        if index.column() == 1:
            node.setValue(value)
            self.dataChanged.emit(index, index)
            return True
        return False

    def headerData(self, section, orientation, role):
        if orientation == Qt.Qt.Horizontal and role == Qt.Qt.DisplayRole:
            return self.headers[section]
        return None

    def index(self, row, column, parent):
        if not parent.isValid():
            parentNode = self.root()
        else:
            parentNode = parent.internalPointer()
        childNode = parentNode.child(row)
        if childNode is None:
            return Qt.QModelIndex()
        else:
            return self.createIndex(row, column, childNode)

    def parent(self, child):
        node = self.nodeFromIndex(child)
        if node is None:
            return Qt.QModelIndex()
        parent = node.parent()
        if parent is None or isinstance(parent, macro.SequenceNode):
            return Qt.QModelIndex()
        grandparent = parent.parent()
        if grandparent is None:
            return Qt.QModelIndex()
        row = grandparent.rowOfChild(parent)
        return self.createIndex(row, 0, parent)

    def nodeFromIndex(self, index):
        if index.isValid():
            return index.internalPointer()
        else:
            return self.root()

    def toSpockCommand(self):
        """
        Converts root obj (MacroNode) to string representing spock command and returns it.

        :return: (etree.Element)
        """

        return self.root().toSpockCommand()

    def toXmlString(self):
        """
        Converts root obj (MacroNode) to xml string and returns it.

        :return: (etree.Element)
        """

        xmlElement = self.root().toXml()
        return etree.tostring(xmlElement, encoding='unicode')
