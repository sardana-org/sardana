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
# along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################

"""This module provides widget for configuring the data acquisition and display of an experiment"""

__all__ = ["ExpDescriptionEditor"]


import json
from taurus.external.qt import Qt, QtCore, QtGui, compat
import copy
import taurus
import taurus.core
from taurus.qt.qtgui.base import TaurusBaseWidget

from sardana.taurus.qt.qtcore.tango.sardana.model import SardanaBaseProxyModel, SardanaTypeTreeItem
from sardana.sardanadefs import ElementType, TYPE_ACQUIRABLE_ELEMENTS
from taurus.qt.qtgui.util.ui import UILoadable

# Using a plain model and filtering and checking
# 'Acquirable' in item.itemData().interfaces is more elegant,
# but things don't get properly sorted...

# from taurus.qt.qtcore.tango.sardana.model import SardanaElementPlainModel


def _to_fqdn(name, logger=None):
    """Helper to convert name into a FQDN URI reference. Works for devices
    and attributes.
    Prior to sardana 2.4.0 Pool element references were using not unique full
    names e.g. pc255:10000/motor/motctrl20/1. This helper converts them into
    FQDN URI references e.g. tango://pc255.cells.es:10000/motor/motctrl20/1.
    It is similarly solved for attribute names.
    """
    full_name = name
    # try to use Taurus 4 to retrieve FQDN URI name
    try:
        from taurus.core.tango.tangovalidator import TangoDeviceNameValidator
        try:
            full_name, _, _ = TangoDeviceNameValidator().getNames(name)
        # it is not a device try as an attribute
        except Exception:
            from taurus.core.tango.tangovalidator import \
                TangoAttributeNameValidator
            full_name, _, _ = TangoAttributeNameValidator().getNames(name)
    # if Taurus3 in use just continue
    except ImportError:
        pass
    if full_name != name and logger:
        msg = ("PQDN full name is deprecated in favor of FQDN full name. "
               "Re-apply pre-scan snapshot configuration in order to "
               "upgrade.")
        logger.warning(msg)
    return full_name


class SardanaAcquirableProxyModel(SardanaBaseProxyModel):
    #    ALLOWED_TYPES = 'Acquirable'
    #
    #    def filterAcceptsRow(self, sourceRow, sourceParent):
    #        sourceModel = self.sourceModel()
    #        idx = sourceModel.index(sourceRow, 0, sourceParent)
    #        item = idx.internalPointer()
    #        return 'Acquirable' in item.itemData().interfaces

    #    ALLOWED_TYPES = ['Motor', 'CTExpChannel', 'ZeroDExpChannel', 'OneDExpChannel',
    #                     'TwoDExpChannel', 'ComChannel', 'IORegister', 'PseudoMotor',
    #                     'PseudoCounter']

    ALLOWED_TYPES = [ElementType[t] for t in TYPE_ACQUIRABLE_ELEMENTS]

    def filterAcceptsRow(self, sourceRow, sourceParent):
        sourceModel = self.sourceModel()
        idx = sourceModel.index(sourceRow, 0, sourceParent)
        treeItem = idx.internalPointer()
        if isinstance(treeItem, SardanaTypeTreeItem):
            return treeItem.itemData() in self.ALLOWED_TYPES
        return True


def find_diff(first, second):
    """
    Return a dict of keys that differ with another config object.  If a value
    is not found in one fo the configs, it will be represented by KEYNOTFOUND.
    :param first: Fist configuration to diff.
    :param second: Second configuration to diff.
    :return: Dict of Key => (first.val, second.val)
    """

    KEYNOTFOUNDIN1 = 'KeyNotFoundInRemote'
    KEYNOTFOUNDIN2 = 'KeyNotFoundInLocal'

    # The GUI can not change these keys. They are changed by the server.
    SKIPKEYS = ['_controller_name', 'description', 'timer', 'monitor', 'ndim',
                'source']

    # These keys can have a list as value.
    SKIPLIST = ['scanfile', 'plot_axes', 'prescansnapshot', 'shape']

    DICT_TYPES = [taurus.core.util.containers.CaselessDict, dict]
    diff = {}
    sd1 = set(first)
    sd2 = set(second)

    # Keys missing in the second dict
    for key in sd1.difference(sd2):
        if key in SKIPKEYS:
            continue
        diff[key] = (first[key], KEYNOTFOUNDIN2)
    # Keys missing in the first dict
    for key in sd2.difference(sd1):
        if key in SKIPKEYS:
            continue
        diff[key] = (KEYNOTFOUNDIN1, second[key])

    # Check for differences
    for key in sd1.intersection(sd2):
        if key in SKIPKEYS:
            continue
        value1 = first[key]
        value2 = second[key]
        if type(value1) in DICT_TYPES:
            try:
                idiff = find_diff(value1, value2)
            except Exception:
                idiff = 'Error on processing'
            if len(idiff) > 0:
                diff[key] = idiff
        elif isinstance(value1, list) and key.lower() not in SKIPLIST:
            ldiff = []
            for v1, v2 in zip(value1, value2):
                try:
                    idiff = find_diff(v1, v2)
                except Exception:
                    idiff = 'Error on processing'
                ldiff.append(idiff)
            if len(ldiff) > 0:
                diff[key] = ldiff
        else:
            if value1 != value2:
                diff[key] = (first[key], second[key])
    return diff


@UILoadable(with_ui='ui')
class ExpDescriptionEditor(Qt.QWidget, TaurusBaseWidget):
    '''
    A widget for editing the configuration of a experiment (measurement groups,
    plot and storage parameters, etc).

    It receives a Sardana Door name as its model and gets/sets the configuration
    using the `ExperimentConfiguration` environmental variable for that Door.
    '''

    createExpConfChangedDialog = Qt.pyqtSignal()
    experimentConfigurationChanged = Qt.pyqtSignal(compat.PY_OBJECT)

    def __init__(self, parent=None, door=None, autoUpdate=False):
        Qt.QWidget.__init__(self, parent)
        TaurusBaseWidget.__init__(self, 'ExpDescriptionEditor')
        self.loadUi()
        self.ui.buttonBox.setStandardButtons(
            Qt.QDialogButtonBox.Reset | Qt.QDialogButtonBox.Apply)
        self.ui.buttonBox.button(Qt.QDialogButtonBox.Reset).setText('Reload')

        newperspectivesDict = copy.deepcopy(
            self.ui.sardanaElementTree.KnownPerspectives)
        #newperspectivesDict[self.ui.sardanaElementTree.DftPerspective]['model'] = [SardanaAcquirableProxyModel, SardanaElementPlainModel]
        newperspectivesDict[self.ui.sardanaElementTree.DftPerspective][
            'model'][0] = SardanaAcquirableProxyModel
        # assign a copy because if just a key of this class memberwas modified,
        # all instances of this class would be affected
        self.ui.sardanaElementTree.KnownPerspectives = newperspectivesDict
        self.ui.sardanaElementTree._setPerspective(
            self.ui.sardanaElementTree.DftPerspective)

        self._localConfig = None
        self._originalConfiguration = None
        self._dirty = False
        self._dirtyMntGrps = set()

        self._autoUpdate = False
        self._warningWidget = None
        self.setContextMenuPolicy(Qt.Qt.ActionsContextMenu)
        self._autoUpdateAction = Qt.QAction("Auto update", self)
        self._autoUpdateAction.setCheckable(True)
        self._autoUpdateAction.toggled.connect(self.setAutoUpdate)
        self.addAction(self._autoUpdateAction)
        self._autoUpdateAction.setChecked(autoUpdate)
        self.registerConfigProperty(
            self._autoUpdateAction.isChecked,
            self._autoUpdateAction.setChecked,
            "autoUpdate")

        # Pending event variables
        self._expConfChangedDialog = None

        self.createExpConfChangedDialog.connect(
            self._createExpConfChangedDialog)
        self.ui.activeMntGrpCB.activated['QString'].connect(
            self.changeActiveMntGrp)
        self.ui.createMntGrpBT.clicked.connect(
            self.createMntGrp)
        self.ui.deleteMntGrpBT.clicked.connect(
            self.deleteMntGrp)
        self.ui.compressionCB.currentIndexChanged['int'].connect(
            self.onCompressionCBChanged)
        self.ui.pathLE.textEdited.connect(
            self.onPathLEEdited)
        self.ui.filenameLE.textEdited.connect(
            self.onFilenameLEEdited)
        self.ui.channelEditor.getQModel().dataChanged.connect(
            self._updateButtonBox)
        self.ui.channelEditor.getQModel().modelReset.connect(
            self._updateButtonBox)
        preScanList = self.ui.preScanList
        preScanList.dataChangedSignal.connect(self.onPreScanSnapshotChanged)
        self.ui.choosePathBT.clicked.connect(
            self.onChooseScanDirButtonClicked)

        if door is not None:
            self.setModel(door)

        self.ui.buttonBox.clicked.connect(self.onDialogButtonClicked)

        # Taurus Configuration properties and delegates
        self.registerConfigDelegate(self.ui.channelEditor)

    def setAutoUpdate(self, auto_update):
        if auto_update and not self._autoUpdate:
            self._warningWidget = self._getWarningWidget()
            self.ui.verticalLayout_3.insertWidget(0, self._warningWidget)
        if not auto_update and self._autoUpdate:
            self.ui.verticalLayout_3.removeWidget(self._warningWidget)
            self._warningWidget.deleteLater()
            self._warningWidget = None
        self._autoUpdate = auto_update

    def _getWarningWidget(self):
        w = Qt.QWidget()
        layout = QtGui.QHBoxLayout()
        w.setLayout(layout)
        icon = QtGui.QIcon.fromTheme('dialog-warning')
        pixmap = QtGui.QPixmap(icon.pixmap(QtCore.QSize(32, 32)))
        label_icon = QtGui.QLabel()
        label_icon.setPixmap(pixmap)
        label = QtGui.QLabel('This experiment configuration dialog '
                             'updates automatically on external changes!')
        layout.addWidget(label_icon)
        layout.addWidget(label)
        layout.addStretch(1)
        return w

    def _getResumeText(self):
        msg_resume = '<p> Summary of differences: <ul>'
        mnt_grps = ''
        envs = ''
        for key in self._diff:
            if key == 'MntGrpConfigs':
                for names in self._diff['MntGrpConfigs']:
                    if mnt_grps != '':
                        mnt_grps += ', '
                    mnt_grps += '<b>{0}</b>'.format(names)
            else:
                if envs != '':
                    envs += ', '
                envs += '<b>{0}</b>'.format(key)
        values = ''
        if mnt_grps != '':
            values += '<li> Measurement Groups: {0}</li>'.format(mnt_grps)
        if envs != '':
            values += '<li> Enviroment variables: {0}</li>'.format(envs)

        msg_resume += values
        msg_resume += ' </ul> </p>'
        return msg_resume

    def _getDetialsText(self):
        msg_detials = 'Changes {key: [external, local], ...}\n'
        msg_detials += json.dumps(self._diff, sort_keys=True)
        return msg_detials

    def _createExpConfChangedDialog(self):
        msg_details = self._getDetialsText()
        msg_info = self._getResumeText()
        self._expConfChangedDialog = Qt.QMessageBox()
        self._expConfChangedDialog.setIcon(Qt.QMessageBox.Warning)
        self._expConfChangedDialog.setWindowTitle('External Changes')
        # text = '''
        # <p align='justify'>
        # The experiment configuration has been modified externally.<br/>
        # You can either:<br/> <l1><b>Load</b> the new configuration from the
        # door
        # (discarding local changes) or <b>Keep</b> your local configuration
        # (would eventually overwrite the external changes when applying).
        # </p>'''
        text = '''
        <p>The experiment configuration has been modified externally.<br>
        You can either:
        <ul>
        <li><strong>Load </strong>the new external configuration</li>
        <li><strong>Keep </strong>your local expconf configuration<br>
        (It can be eventually applied)</li>
        </ul></p>
        '''
        self._expConfChangedDialog.setText(text)
        self._expConfChangedDialog.setTextFormat(QtCore.Qt.RichText)
        self._expConfChangedDialog.setInformativeText(msg_info)
        self._expConfChangedDialog.setDetailedText(msg_details)
        self._expConfChangedDialog.setStandardButtons(Qt.QMessageBox.Ok |
                                                      Qt.QMessageBox.Cancel)
        btn_ok = self._expConfChangedDialog.button(Qt.QMessageBox.Ok)
        btn_ok.setText('Load')
        btn_cancel = self._expConfChangedDialog.button(Qt.QMessageBox.Cancel)
        btn_cancel.setText('Keep')
        result = self._expConfChangedDialog.exec_()
        self._expConfChangedDialog = None
        if result == Qt.QMessageBox.Ok:
            self._reloadConf(force=True)
        elif result == Qt.QMessageBox.Cancel:
            self.ui.buttonBox.setEnabled(True)

    @QtCore.pyqtSlot()
    def _experimentConfigurationChanged(self):
        self._diff = ''
        try:
            self._diff = self._getDiff()
        except Exception as e:
            raise RuntimeError('Error on processing! {0}'.format(e))

        if len(self._diff) > 0:
            if self._autoUpdate:
                self._reloadConf(force=True)
            else:
                if self._expConfChangedDialog is None:
                    if hasattr(self, 'createExpConfChangedDialog'):
                        self.createExpConfChangedDialog.emit()
                else:
                    msg_details = self._getDetialsText()
                    msg_info = self._getResumeText()
                    self._expConfChangedDialog.setInformativeText(msg_info)
                    self._expConfChangedDialog.setDetailedText(msg_details)

    def _getDiff(self):
        door = self.getModelObj()
        if door is None:
            return []

        new_conf = door.getExperimentConfiguration()
        old_conf = self._localConfig
        return find_diff(new_conf, old_conf)

    def getModelClass(self):
        '''reimplemented from :class:`TaurusBaseWidget`'''
        return taurus.core.taurusdevice.TaurusDevice

    def onChooseScanDirButtonClicked(self):
        ret = Qt.QFileDialog.getExistingDirectory(
            self, 'Choose directory for saving files', self.ui.pathLE.text())
        if ret:
            self.ui.pathLE.setText(ret)
            self.ui.pathLE.textEdited.emit(ret)

    def onDialogButtonClicked(self, button):
        role = self.ui.buttonBox.buttonRole(button)
        if role == Qt.QDialogButtonBox.ApplyRole:
            if not self.writeExperimentConfiguration(ask=False):
                self._reloadConf(force=True)
        elif role == Qt.QDialogButtonBox.ResetRole:
            self._reloadConf()

    def closeEvent(self, event):
        '''This event handler receives widget close events'''
        if self.isDataChanged():
            self.writeExperimentConfiguration(ask=True)
        Qt.QWidget.closeEvent(self, event)

    def setModel(self, model):
        '''reimplemented from :class:`TaurusBaseWidget`'''
        TaurusBaseWidget.setModel(self, model)
        self._reloadConf(force=True)
        # set the model of some child widgets
        door = self.getModelObj()
        if door is None:
            return
        # @todo: get the tghost from the door model instead
        tghost = taurus.Authority().getNormalName()
        msname = door.macro_server.getFullName()
        self.ui.taurusModelTree.setModel(tghost)
        self.ui.sardanaElementTree.setModel(msname)
        door.experimentConfigurationChanged.connect(
            self._experimentConfigurationChanged)

    def _reloadConf(self, force=False):
        if not force and self.isDataChanged():
            op = Qt.QMessageBox.question(self, "Reload info from door",
                                         "If you reload, all current experiment configuration changes will be lost. Reload?",
                                         Qt.QMessageBox.Yes | Qt.QMessageBox.Cancel)
            if op != Qt.QMessageBox.Yes:
                return
        door = self.getModelObj()
        if door is None:
            return
        conf = door.getExperimentConfiguration()
        self._originalConfiguration = copy.deepcopy(conf)
        self.setLocalConfig(conf)
        self._setDirty(False)
        self._dirtyMntGrps = set()
        # set a list of available channels
        avail_channels = {}
        for ch_info in \
                list(door.macro_server.getExpChannelElements().values()):
            avail_channels[ch_info.full_name] = ch_info.getData()
        self.ui.channelEditor.getQModel().setAvailableChannels(avail_channels)
        # set a list of available triggers
        avail_triggers = {'software': {"name": "software"}}
        tg_elements = door.macro_server.getElementsOfType('TriggerGate')
        for tg_info in list(tg_elements.values()):
            avail_triggers[tg_info.full_name] = tg_info.getData()
        self.ui.channelEditor.getQModel().setAvailableTriggers(avail_triggers)
        self.experimentConfigurationChanged.emit(copy.deepcopy(conf))

    def _setDirty(self, dirty):
        self._dirty = dirty
        self._updateButtonBox()

    def isDataChanged(self):
        """Tells if the local data has been modified since it was last refreshed

        :return: (bool) True if he local data has been modified since it was last refreshed
        """
        return bool(self._dirty or self.ui.channelEditor.getQModel().isDataChanged() or self._dirtyMntGrps)

    def _updateButtonBox(self, *args, **kwargs):
        self.ui.buttonBox.setEnabled(self.isDataChanged())

    def getLocalConfig(self):
        return self._localConfig

    def setLocalConfig(self, conf):
        '''gets a ExpDescription dictionary and sets up the widget'''

        self._localConfig = conf

        # set the Channel Editor
        activeMntGrpName = self._localConfig['ActiveMntGrp'] or ''
        if activeMntGrpName in self._localConfig['MntGrpConfigs']:
            mgconfig = self._localConfig['MntGrpConfigs'][activeMntGrpName]
            self.ui.channelEditor.getQModel().setDataSource(mgconfig)
        else:
            self.ui.channelEditor.getQModel().setDataSource({})

        # set the measurement group ComboBox
        self.ui.activeMntGrpCB.clear()
        mntGrpLabels = []
        for _, mntGrpConf in list(self._localConfig['MntGrpConfigs'].items()):
            # get labels to visualize names with lower and upper case
            mntGrpLabels.append(mntGrpConf['label'])
        self.ui.activeMntGrpCB.addItems(sorted(mntGrpLabels))
        idx = self.ui.activeMntGrpCB.findText(activeMntGrpName,
                                              # case insensitive find
                                              Qt.Qt.MatchFixedString)
        self.ui.activeMntGrpCB.setCurrentIndex(idx)

        # set the system snapshot list
        # I get it before clearing because clear() changes the _localConfig
        psl = self._localConfig.get('PreScanSnapshot')
        # TODO: For Taurus 4 compatibility
        psl_fullname = []
        for name, display in psl:
            name = _to_fqdn(name, self)
            psl_fullname.append((name, display))

        self.ui.preScanList.clear()
        self.ui.preScanList.addModels(psl_fullname)

        # other settings
        self.ui.filenameLE.setText(", ".join(self._localConfig['ScanFile']))
        self.ui.pathLE.setText(self._localConfig['ScanDir'] or '')
        self.ui.compressionCB.setCurrentIndex(
            self._localConfig['DataCompressionRank'] + 1)

    def writeExperimentConfiguration(self, ask=True):
        '''sends the current local configuration to the door

        :param ask: (bool) If True (default) prompts the user before saving.
        '''

        if ask:
            op = Qt.QMessageBox.question(self, "Save configuration?",
                                         'Do you want to save the current configuration?\n(if not, any changes will be lost)',
                                         Qt.QMessageBox.Yes | Qt.QMessageBox.No)
            if op != Qt.QMessageBox.Yes:
                return False

        conf = self.getLocalConfig()

        # make sure that no empty measurement groups are written
        for mgname, mgconfig in list(conf.get('MntGrpConfigs', {}).items()):
            if mgconfig is not None and not mgconfig.get('controllers'):
                mglabel = mgconfig['label']
                Qt.QMessageBox.information(self, "Empty Measurement group",
                                           "The measurement group '%s' is empty. Fill it (or delete it) before applying" % mglabel,
                                           Qt.QMessageBox.Ok)
                self.changeActiveMntGrp(mgname)
                return False

        # check if the currently displayed mntgrp is changed
        if self.ui.channelEditor.getQModel().isDataChanged():
            self._dirtyMntGrps.add(self._localConfig['ActiveMntGrp'])

        door = self.getModelObj()
        try:
            door.setExperimentConfiguration(conf, mnt_grps=self._dirtyMntGrps)
        except Exception as e:
            Qt.QMessageBox.critical(self, 'Wrong configuration',
                                    '{0}'.format(e))
            return False
        self._originalConfiguration = copy.deepcopy(conf)
        self._dirtyMntGrps = set()
        self.ui.channelEditor.getQModel().setDataChanged(False)
        self._setDirty(False)
        self.experimentConfigurationChanged.emit(copy.deepcopy(conf))
        return True

    @Qt.pyqtSlot('QString')
    def changeActiveMntGrp(self, activeMntGrpName):
        if self._localConfig is None:
            return
        if activeMntGrpName == self._localConfig['ActiveMntGrp']:
            return  # nothing changed
        if activeMntGrpName not in self._localConfig['MntGrpConfigs']:
            raise KeyError('Unknown measurement group "%s"' % activeMntGrpName)

        # add the previous measurement group to the list of "dirty" groups if
        # something was changed
        if self.ui.channelEditor.getQModel().isDataChanged():
            self._dirtyMntGrps.add(self._localConfig['ActiveMntGrp'])

        self._localConfig['ActiveMntGrp'] = activeMntGrpName

        i = self.ui.activeMntGrpCB.findText(activeMntGrpName,
                                            # case insensitive find
                                            Qt.Qt.MatchFixedString)
        self.ui.activeMntGrpCB.setCurrentIndex(i)
        mgconfig = self._localConfig['MntGrpConfigs'][activeMntGrpName]
        self.ui.channelEditor.getQModel().setDataSource(mgconfig)
        self._setDirty(True)

    def createMntGrp(self):
        '''creates a new Measurement Group'''

        if self._localConfig is None:
            return

        mntGrpName, ok = Qt.QInputDialog.getText(self, "New Measurement Group",
                                                 "Enter a name for the new measurement Group")
        if not ok:
            return
        mntGrpName = str(mntGrpName)

        # check that the given name is not an existing pool element
        ms = self.getModelObj().macro_server
        poolElementNames = [
            v.name for v in
            list(ms.getElementsWithInterface("PoolElement").values())]
        while mntGrpName in poolElementNames:
            msg = ("The name '%s' already is used for another pool element. "
                   "Please Choose a different one." % mntGrpName)
            Qt.QMessageBox.warning(self, "Cannot create Measurement group",
                                   msg, Qt.QMessageBox.Ok)
            msg = "Enter a name for the new measurement Group"
            mntGrpName, ok = Qt.QInputDialog.getText(self,
                                                     "New Measurement Group",
                                                     msg,
                                                     Qt.QLineEdit.Normal,
                                                     mntGrpName)
            if not ok:
                return
            mntGrpName = str(mntGrpName)

        # check that the measurement group is not already in the localConfig
        msg = ('A measurement group named "%s" already exists. A new one '
               'will not be created' % mntGrpName)
        if mntGrpName in self._localConfig['MntGrpConfigs']:
            Qt.QMessageBox.warning(self, "%s already exists" % mntGrpName,
                                   msg)
            return

        # add an empty configuration dictionary to the local config
        mgconfig = {'label': mntGrpName, 'controllers': {}}
        self._localConfig['MntGrpConfigs'][mntGrpName] = mgconfig
        # add the new measurement group to the list of "dirty" groups
        self._dirtyMntGrps.add(mntGrpName)
        # add the name to the combobox
        self.ui.activeMntGrpCB.addItem(mntGrpName)
        # make it the Active MntGrp
        self.changeActiveMntGrp(mntGrpName)

    def deleteMntGrp(self):
        '''creates a new Measurement Group'''
        activeMntGrpName = str(self.ui.activeMntGrpCB.currentText())
        op = Qt.QMessageBox.question(self, "Delete Measurement Group",
                                     "Remove the measurement group '%s'?" % activeMntGrpName,
                                     Qt.QMessageBox.Yes | Qt.QMessageBox.Cancel)
        if op != Qt.QMessageBox.Yes:
            return
        currentIndex = self.ui.activeMntGrpCB.currentIndex()
        if self._localConfig is None:
            return
        if activeMntGrpName not in self._localConfig['MntGrpConfigs']:
            raise KeyError('Unknown measurement group "%s"' % activeMntGrpName)

        # add the current measurement group to the list of "dirty" groups
        self._dirtyMntGrps.add(activeMntGrpName)

        self._localConfig['MntGrpConfigs'][activeMntGrpName] = None
        self.ui.activeMntGrpCB.setCurrentIndex(-1)
        self.ui.activeMntGrpCB.removeItem(currentIndex)
        self.ui.channelEditor.getQModel().setDataSource({})
        self._setDirty(True)

    @Qt.pyqtSlot('int')
    def onCompressionCBChanged(self, idx):
        if self._localConfig is None:
            return
        self._localConfig['DataCompressionRank'] = idx - 1
        self._setDirty(True)

    def onPathLEEdited(self, text):
        self._localConfig['ScanDir'] = str(text)
        self._setDirty(True)

    def onFilenameLEEdited(self, text):
        self._localConfig['ScanFile'] = [v.strip()
                                         for v in str(text).split(',')]
        self._setDirty(True)

    def onPreScanSnapshotChanged(self, items):
        door = self.getModelObj()
        ms = door.macro_server
        preScanList = []
        for e in items:
            nfo = ms.getElementInfo(e.src)
            if nfo is None:
                full_name = e.src
                display = e.display
            else:
                full_name = nfo.full_name
                display = nfo.name
            preScanList.append((full_name, display))
        self._localConfig['PreScanSnapshot'] = preScanList
        self._setDirty(True)


def demo(model=None, autoUpdate=False):
    """Experiment configuration"""
    #w = main_ChannelEditor()
    w = ExpDescriptionEditor(autoUpdate=autoUpdate)
    if model is None:
        from sardana.taurus.qt.qtgui.extra_macroexecutor import \
            TaurusMacroConfigurationDialog
        dialog = TaurusMacroConfigurationDialog(w)
        accept = dialog.exec_()
        if accept:
            model = str(dialog.doorComboBox.currentText())
    if model is not None:
        w.setModel(model)
    return w


def main():
    import sys
    import taurus.qt.qtgui.application
    Application = taurus.qt.qtgui.application.TaurusApplication

    app = Application.instance()
    owns_app = app is None
    if owns_app:
        import taurus.core.util.argparse
        parser = taurus.core.util.argparse.get_taurus_parser()
        parser.usage = "%prog [options] <door name>"
        parser.add_option('--auto-update', dest='auto_update',
                          action='store_true',
                          help='Set auto update of experiment configuration')

        app = Application(app_name="Exp. Description demo", app_version="1.0",
                          org_domain="Sardana", org_name="Tango community",
                          cmd_line_parser=parser)

    args = app.get_command_line_args()
    opt = app.get_command_line_options()

    if len(args) == 1:
        auto_update = opt.auto_update is not None
        w = demo(model=args[0], autoUpdate=auto_update)
    else:
        w = demo()
    w.show()

    if owns_app:
        sys.exit(app.exec_())
    else:
        return w


if __name__ == "__main__":
    main()
