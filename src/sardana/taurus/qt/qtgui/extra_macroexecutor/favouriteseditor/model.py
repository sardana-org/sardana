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

from taurus.external.qt import Qt
from lxml import etree

from sardana.taurus.core.tango.sardana import macro


class MacrosListModel(Qt.QAbstractListModel):

    def __init__(self, parent=None):
        Qt.QAbstractListModel.__init__(self, parent)
        self.list = []
        self._max_len = None

    def setMaxLen(self, max_len):
        self._max_len = max_len

    def rowCount(self, parent=Qt.QModelIndex()):
        return len(self.list)

    def data(self, index, role):
        if index.isValid() and role == Qt.Qt.DisplayRole:
            macroNode = self.list[index.row()]
            return self.list[index.row()].toSpockCommand()
        else:
            return None

    def index(self, row, column=0, parent=Qt.QModelIndex()):
        if self.rowCount():
            return self.createIndex(row, column, self.list[row])
        else:
            return Qt.QModelIndex()

    def insertRow(self, macroNode, row=0):
        self.beginInsertRows(Qt.QModelIndex(), row, row)
        if self._max_len is not None and len(self.list) == self._max_len:
            self.list.pop()
        self.list.insert(row, macroNode)
        self.endInsertRows()
        return self.index(row)

    def removeRow(self, row):
        self.beginRemoveRows(Qt.QModelIndex(), row, row)
        self.list.pop(row)
        self.endRemoveRows()
        if row == self.rowCount():
            row = row - 1
        return self.index(row)

    def isUpRowAllowed(self, index):
        return index.row() > 0

    def upRow(self, row):
        """This method move macro up and returns index with its new position"""
        macroNode = self.list[row]
        self.removeRow(row)
        return self.insertRow(macroNode, row - 1)

    def isDownRowAllowed(self, index):
        return index.row() < self.rowCount() - 1

    def downRow(self, row):
        """This method move macro down and returns index with its new position"""
        macroNode = self.list[row]
        self.removeRow(row)
        return self.insertRow(macroNode, row + 1)

    def toXmlString(self, pretty=False):
        listElement = etree.Element("list")
        for macroNode in self.list:
            listElement.append(macroNode.toXml(withId=False))
        xmlTree = etree.ElementTree(listElement)
        xmlString = etree.tostring(xmlTree, encoding='unicode',
                                   pretty_print=pretty)
        return xmlString

    def fromXmlString(self, xmlString):
        self.beginResetModel()
        listElement = etree.fromstring(xmlString)
        for childElement in listElement.iterchildren("macro"):
            if self._max_len is not None and len(self.list) >= self._max_len:
                break
            macroNode = macro.MacroNode()
            macroNode.fromXml(childElement)
            self.list.append(macroNode)
        self.endResetModel()
