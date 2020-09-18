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

from taurus.external.qt import Qt
from taurus import Database
from taurus.core.taurusbasetypes import TaurusElementType
from taurus.core.tango.tangodatabase import TangoAttrInfo
from taurus.qt.qtgui.tree import TaurusDbTreeWidget
from sardana.taurus.qt.qtgui.extra_macroexecutor.macroparameterseditor.macroparameterseditor import MacroParametersEditor
from sardana.taurus.qt.qtgui.extra_macroexecutor.macroparameterseditor.parameditors import LineEditParam, ParamBase, ComboBoxParam, CheckBoxParam, DirPathParam, MSAttrListComboBoxParam
from sardana.taurus.qt.qtgui.extra_macroexecutor.macroparameterseditor.model import ParamEditorModel
from sardana.taurus.qt.qtgui.extra_macroexecutor.common import MSAttrListComboBox


class SenvEditor(Qt.QWidget, MacroParametersEditor):

    def __init__(self, parent=None):
        Qt.QWidget.__init__(self, parent)
        MacroParametersEditor.__init__(self)
        self.valueWidget = None

    def initComponents(self):
        self.setLayout(Qt.QFormLayout())

        self.layout().addRow(Qt.QLabel("Setting environment variable:", self))

        self.nameComboBox = ComboBoxParam(self)
        self.nameComboBox.addItems(
            ["ActiveMntGrp", "ExtraColumns", "JsonRecorder", "ScanFile", "ScanDir"])
        self.nameComboBox.setEditable(True)
        self.nameComboBox.currentIndexChanged.connect(
            self.onNameComboBoxChanged)
        self.layout().addRow("name:", self.nameComboBox)

        nameIndex = self.model().index(0, 1, self.rootIndex())
        self.nameComboBox.setIndex(nameIndex)

    def setRootIndex(self, rootIndex):
        self._rootIndex = rootIndex
        self.initComponents()

    def rootIndex(self):
        return self._rootIndex

    def model(self):
        return self._model

    def setModel(self, model):
        self._model = model
        if isinstance(model, ParamEditorModel):
            self.setRootIndex(Qt.QModelIndex())

    def onNameComboBoxChanged(self, index):
        # note that the index parameter is ignored!
        text = str(self.nameComboBox.currentText())
        if self.valueWidget is not None:
            label = self.layout().labelForField(self.valueWidget)
            if label is not None:
                self.layout().removeWidget(label)
                label.setParent(None)
                label = None

            self.layout().removeWidget(self.valueWidget)
            self.valueWidget.resetValue()
            self.valueWidget.setParent(None)
            self.valueWidget = None

        self.valueWidget, label = getSenvValueEditor(text, self)
        if text == "ActiveMntGrp":
            self.valueWidget.setModel(self.model())
            self.valueWidget.setModel("/MeasurementGroupList")

        paramRepeatIndex = self.model().index(1, 0, self.rootIndex())
        repeatIndex = paramRepeatIndex.child(0, 0)
        valueIndex = repeatIndex.child(0, 1)
        self.valueWidget.setIndex(valueIndex)

        if label:
            self.layout().addRow(label, self.valueWidget)
        else:
            self.layout().addRow(self.valueWidget)


def getSenvValueEditor(envName, parent):
    """Factory method, requires: string, and QWidget as a parent for returned editor.
    Factory returns a tuple of widget and a label for it.

    :return: (Qt.QWidget, str) """
    label = "value:"
    if envName == "ActiveMntGrp":
        editor = MSAttrListComboBoxParam(parent)
    elif envName == "ExtraColumns":
        editor = ExtraColumnsEditor(parent)
        label = None
    elif envName == "JsonRecorder":
        editor = CheckBoxParam(parent)
    elif envName == "ScanDir":
        editor = DirPathParam(parent)
    elif envName == "ScanFile":
        editor = LineEditParam(parent)
    else:
        editor = LineEditParam(parent)
    return editor, label


class ExtraColumnsEditor(ParamBase, Qt.QWidget):

    def __init__(self, parent=None, paramModel=None):
        ParamBase.__init__(self, paramModel)
        Qt.QWidget.__init__(self, parent)
        self.setLayout(Qt.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        addNewColumnButton = Qt.QPushButton(
            Qt.QIcon.fromTheme("list-add"), "Add new column...", self)
        removeSelectedColumnsButton = Qt.QPushButton(
            Qt.QIcon.fromTheme("list-remove"), "Remove selected...", self)
        buttonsLayout = Qt.QHBoxLayout()
        buttonsLayout.addWidget(addNewColumnButton)
        buttonsLayout.addWidget(removeSelectedColumnsButton)
        self.layout().addLayout(buttonsLayout)

        self.extraColumnsTable = ExtraColumnsTable(self)
        self.extraColumnsModel = ExtraColumnsModel()
        self.extraColumnsTable.setModel(self.extraColumnsModel)
        self.extraColumnsTable.setItemDelegate(
            ExtraColumnsDelegate(self.extraColumnsTable))

        self.layout().addWidget(self.extraColumnsTable)

        addNewColumnButton.clicked.connect(self.onAddNewColumn)
        removeSelectedColumnsButton.clicked.connect(
            self.onRemoveSelectedColumns)
        self.extraColumnsModel.dataChanged.connect(self.onExtraColumnsChanged)
        self.extraColumnsModel.modelReset.connect(self.onExtraColumnsChanged)

    def getValue(self):
        return repr(self.extraColumnsTable.model().columns())

    def setValue(self, value):
        try:
            columns = eval(value)
        except:
            columns = []
        self.extraColumnsTable.setColumns(columns)

    def onAddNewColumn(self):
        self.extraColumnsTable.insertRows()
        self.onModelChanged()

    def onRemoveSelectedColumns(self):
        self.extraColumnsTable.removeRows()
        self.onModelChanged()

    def onExtraColumnsChanged(self):
        self.onModelChanged()


class ExtraColumnsTable(Qt.QTableView):

    def __init__(self, parent):
        Qt.QTableView.__init__(self, parent)
        self.setSelectionBehavior(Qt.QAbstractItemView.SelectRows)
        self.setSelectionMode(Qt.QAbstractItemView.ExtendedSelection)

    def setColumns(self, columns):
        if columns is None:
            columns = []
        self.model().setColumns(columns)
        self.resizeColumnsToContents()

    def insertRows(self):
        self.model().insertRows(self.model().rowCount())

    def removeRows(self):
        rows = [index.row() for index in self.selectedIndexes()]
        rows = list(set(rows))
        rows.sort(reverse=True)
        for row in rows:
            self.model().removeRows(row)


class ExtraColumnsDelegate(Qt.QItemDelegate):

    def __init__(self, parent=None):
        Qt.QItemDelegate.__init__(self, parent)
        db = Database()
        self.host = db.getNormalName()

    def createEditor(self, parent, option, index):
        if index.column() == 1:
            self.combo_attr_tree_widget = TaurusDbTreeWidget(
                perspective=TaurusElementType.Device)
            self.combo_attr_tree_widget.setModel(self.host)
            treeView = self.combo_attr_tree_widget.treeView()
            qmodel = self.combo_attr_tree_widget.getQModel()
            editor = Qt.QComboBox(parent)
            editor.setModel(qmodel)
            editor.setMaxVisibleItems(20)
            editor.setView(treeView)
        elif index.column() == 2:
            editor = MSAttrListComboBox(parent)
            editor.setModel(index.model())
            editor.setModel("/InstrumentList")
        else:
            editor = Qt.QItemDelegate.createEditor(self, parent, option, index)
        return editor

    def setEditorData(self, editor, index):
        if index.column() == 2:
            text = index.model().data(index, Qt.Qt.DisplayRole)
            editor.setCurrentText(text)
        else:
            Qt.QItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        column = index.column()
        if column == 1:
            selectedItems = self.combo_attr_tree_widget.selectedItems()
            if not len(selectedItems) == 1:
                return
            taurusTreeAttributeItem = selectedItems[0]
            itemData = taurusTreeAttributeItem.itemData()
            if isinstance(itemData, TangoAttrInfo):
                model.setData(index, itemData.fullName())
        elif column == 2:
            model.setData(index, editor.currentText())
        else:
            Qt.QItemDelegate.setModelData(self, editor, model, index)

    def sizeHint(self, option, index):
        if index.column() == 0:
            fm = option.fontMetrics
            text = index.model().data(index, Qt.Qt.DisplayRole)
            document = Qt.QTextDocument()
            document.setDefaultFont(option.font)
            document.setHtml(text)
            size = Qt.QSize(document.idealWidth() + 5, fm.height())
        elif index.column() == 1:
            editor = self.createEditor(self.parent(), option, index)
            if editor is None:
                size = Qt.QItemDelegate.sizeHint(self, option, index)
            else:
                size = editor.sizeHint()
                editor.hide()
                editor.setParent(None)
#                editor.destroy()
        else:
            size = Qt.QItemDelegate.sizeHint(self, option, index)
        return size


class ExtraColumnsModel(Qt.QAbstractTableModel):

    def __init__(self, columns=None):
        if columns is None:
            columns = []
        Qt.QAbstractItemModel.__init__(self)
        self.__columns = columns

    def setColumns(self, columns):
        self.beginResetModel()
        self.__columns = columns
        self.endResetModel()

    def columns(self):
        return self.__columns

    def rowCount(self, index=Qt.QModelIndex()):
        return len(self.__columns)

    def columnCount(self, index=Qt.QModelIndex()):
        return 3

    def data(self, index, role=Qt.Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return None
        row = index.row()
        column = index.column()
        # Display Role
        if role == Qt.Qt.DisplayRole:
            if column == 0:
                return Qt.QString(self.__columns[row]['label'])
            elif column == 1:
                return Qt.QString(self.__columns[row]['model'])
            elif column == 2:
                return Qt.QString(self.__columns[row]['instrument'])
        return None

    def headerData(self, section, orientation, role=Qt.Qt.DisplayRole):
        if role == Qt.Qt.TextAlignmentRole:
            if orientation == Qt.Qt.Horizontal:
                return int(Qt.Qt.AlignLeft | Qt.Qt.AlignVCenter)
            return int(Qt.Qt.AlignRight | Qt.Qt.AlignVCenter)
        if role != Qt.Qt.DisplayRole:
            return None
        # So this is DisplayRole...
        if orientation == Qt.Qt.Horizontal:
            if section == 0:
                return "Label"
            elif section == 1:
                return "Attribute"
            elif section == 2:
                return "Instrument"
            return None
        else:
            return str(section + 1)

    def flags(self, index):
        flags = Qt.Qt.ItemIsEnabled | Qt.Qt.ItemIsSelectable
        if index.isValid():
            column = index.column()
            if column in (0, 1, 2):
                flags |= Qt.Qt.ItemIsEditable
        return flags

    def setData(self, index, value=None, role=Qt.Qt.EditRole):
        if index.isValid() and (0 <= index.row() < self.rowCount()):
            row = index.row()
            column = index.column()
            if column == 0:
                self.__columns[row]['label'] = value
            elif column == 1:
                self.__columns[row]['model'] = value
            elif column == 2:
                self.__columns[row]['instrument'] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def insertRows(self, row, rows=1, parentindex=None):
        if parentindex is None:
            parentindex = Qt.QModelIndex()
        first = row
        last = row + rows - 1
        self.beginInsertRows(parentindex, first, last)
        for row in range(first, last + 1):
            self.insertRow(row)
        self.endInsertRows()
        return True

    def insertRow(self, row, parentIndex=None):
        self.__columns.insert(
            row, {'label': '', 'model': '', 'instrument': ''})

    def removeRows(self, row, rows=1, parentindex=None):
        if parentindex is None:
            parentindex = Qt.QModelIndex()
        first = row
        last = row + rows - 1
        self.beginRemoveRows(parentindex, first, last)
        for row in range(first, last + 1):
            self.removeRow(row)
        self.endRemoveRows()
        return True

    def removeRow(self, row, parentIndex=None):
        self.__columns.pop(row)

CUSTOM_EDITOR = SenvEditor

if __name__ == "__main__":
    import sys
    import taurus
    from taurus.core.util.argparse import get_taurus_parser
    from taurus.qt.qtgui.application import TaurusApplication
    from sardana.taurus.core.tango.sardana.macro import MacroNode

    parser = get_taurus_parser()
    app = TaurusApplication(sys.argv, cmd_line_parser=parser)
    args = app.get_command_line_args()
    editor = SenvEditor()
    macroServer = taurus.Device(args[0])
    macroInfoObj = macroServer.getMacroInfoObj("senv")
    macroNode = MacroNode()
    editor.setMacroNode(macroNode)
    editor.show()

    sys.exit(app.exec_())
