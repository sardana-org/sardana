#!/usr/bin/env python

##############################################################################
##
# This file is part of Sardana
##
# http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
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

"""This module provides a base widget that can be used to display a taurus
model in a table widget"""

__all__ = ["MntGrpChannelEditor"]

__docformat__ = 'restructuredtext'

from taurus.core.taurusdevice import TaurusDevice
from taurus.external.qt import Qt
from taurus.qt.qtcore.model import TaurusBaseTreeItem, TaurusBaseModel
from taurus.qt.qtgui.model import EditorToolBar
from taurus.qt.qtgui.table import TaurusBaseTableWidget
from taurus.qt.qtgui.panel import TaurusModelChooser
from taurus.core.taurusbasetypes import TaurusElementType

from sardana.taurus.core.tango.sardana import ChannelView, PlotType, \
    Normalization
from sardana.pool.pooldefs import AcqSynchType
from sardana.taurus.core.tango.sardana.pool import getChannelConfigs

#=========================================================================
# some dummydict for developing the "Experimental Configuration widget"
# This block is to be removed and the dictionaries will be defined and
# initialized in Sardana's Door code


# dict <str, obj> with (at least) keys:
#    - 'timer' : the timer channel name / timer channel id
#    - 'monitor' : the monitor channel name / monitor channel id
#    - 'controllers' : dict<Controller, dict> where:
#        - key: ctrl
#        - value: dict<str, dict> with (at least) keys:
#            - 'units': dict<str, dict> with (at least) keys:
#                - 'id' : the unit ID inside the controller
#                - 'timer' : the timer channel name / timer channel id
#                - 'monitor' : the monitor channel name / monitor channel id
#                - 'synchronization' : a value from AcqSynchType enum
#                - 'channels' where value is a dict<str, obj> with (at least) keys:
#                    - 'index' : int indicating the position of the channel in the measurement group
#                    - 'id' : the channel name ( channel id )
#                    optional keys:
#                    - 'enabled' : True/False (default is True)
#                    any hints:
#                    - 'output' : True/False (default is True)
#                    - 'plot_type' : a value from PlotType enum
#                    - 'plot_axes' : list<str> 'where str is channel name/'step#/'index#' (default is [])
#                    - 'label' : prefered label (default is channel name)
#                    - 'scale' : <float, float> with min/max (defaults to channel
#                                range if it is defined
#                    - 'plot_color' : int representing RGB
#    optional keys:
#    - 'label' : measurement group label (defaults to measurement group name)
#    - 'description' : measurement group description


#=========================================================================
# just an arbitrary value to use as default string length...
DEFAULT_STRING_LENGTH = 80


def createChannelDict(channel, index=None, **kwargs):
    from taurus.core.tango import FROM_TANGO_TO_STR_TYPE
    import PyTango
    import numpy

    if isinstance(channel, str):
        #@fixme: to make things uglier, I lazily assume Tango attribute namin
        dev_name, attr_name = channel.rsplit('/', 1)
        name = attr_name
        try:
            dev = PyTango.DeviceProxy(dev_name)
            db = dev.get_device_db()
            try:
                alias = db.get_alias(dev.name())
            except:
                # no alias...
                alias = dev.name()
            label = alias + "/" + attr_name
        except:
            label = channel
        full_name = channel
        source = channel
    else:
        name = channel['name']
        label = name
        full_name = channel['full_name']
        source = channel['source']

    ret = {
        'name': name,
        'label': label,
        'full_name': full_name,
        # bool. Whether this channel is enabled (if not enabled, it won't be
        # used for output or plot)
        'enabled': True,
        'output': True,  # bool. Whether to show output in the stdout
        'data_type': 'float64',
        'data_units': 'No unit',
        #           'timer': '', #should contain a channel name
        #           'monitor': '', #should contain a channel name
        #           'trigger': '', #should contain a channel name
        # 'value_ref_enabled': False,  # bool
        # 'value_ref_pattern': '',  # str
        'conditioning': '',  # this is a python expresion to be evaluated for conditioning the data. The data for this channel can be referred as 'x' and data from other channels can be referred by channel name
        'normalization': Normalization.No,  # one of the Normalization enumeration members
        # string indicating the location of the data of this channel within
        # the nexus tree
        'nexus_path': '',
    }

    # If the channel is a Tango one, try to guess data_type, shape and
    # data_units
    attrproxy = attrconf = value = None
    dtype = None
    try:
        attrproxy = PyTango.AttributeProxy(source)
        attrconf = attrproxy.get_config()
        # avoid trying to read for scalars. We know that their shape must be ()
        if attrconf.data_format != PyTango.AttrDataFormat.SCALAR:
            value = attrproxy.read().value
    except Exception as e:
        print(str(e))

    if value is not None:
        dtype = getattr(value, 'dtype', numpy.dtype(type(value))).name
        ret['data_units'] = attrconf.unit
    elif attrconf is not None:
        dtype = FROM_TANGO_TO_STR_TYPE[attrconf.data_type]
        ret['data_units'] = attrconf.unit

    if dtype is not None:
        #        if dtype.startswith('str'):
        #            dtype='char'
        #            shape = list(shape)+[DEFAULT_STRING_LENGTH]
        #        elif dtype == 'bool':
        #            dtype='int8'
        ret['data_type'] = dtype

    # now overwrite using the arguments
    ret.update(kwargs)

    # Calculate the index
    if index is not None:
        # an integer used for ordering the channel in this measurement group
        ret['index'] = index

    # Choose a default plot_type for the channel
    if 'plot_type' not in ret:
        ret['plot_type'] = PlotType.No

    # And a default value for plot_axes
    if 'plot_axes' not in ret:
        default_axes = {PlotType.No: [], PlotType.Spectrum: [
            '<mov>'], PlotType.Image: ['<idx>', '<idx>']}
        # a string defining a colon-separated list of axis names. An axis can
        # be a channel name or "<idx>". This shares the syntax of the NeXus
        # @axes attribute
        ret['plot_axes'] = default_axes[ret['plot_type']]

    return ret


def getElementTypeIcon(t):
    if t == ChannelView.Channel:
        return Qt.QIcon("actions:system-shutdown.svg")
    elif t == ChannelView.Enabled:
        return Qt.QIcon("status:true.svg")
    elif t == ChannelView.Output:
        return Qt.QIcon.fromTheme("utilities-terminal")
    elif t == ChannelView.PlotType:
        return Qt.QIcon("apps:utilities-system-monitor.svg")
    elif t == ChannelView.PlotAxes:
        return Qt.QIcon("apps:utilities-system-monitor.svg")
    elif t == ChannelView.Timer:
        return Qt.QIcon("status:flag-green-clock.svg")
    elif t == ChannelView.Monitor:
        return Qt.QIcon("status:flag-green.svg")
    elif t == ChannelView.Synchronization:
        return Qt.QIcon("actions:system-shutdown.svg")
    elif t == ChannelView.NXPath:
        return Qt.QIcon.fromTheme("document-save-as")
    elif t == ChannelView.Synchronizer:
        return Qt.QIcon("actions:system-shutdown.svg")

    return Qt.QIcon(":tango.png")


def getElementTypeSize(t):
    if t == ChannelView.Channel:
        return Qt.QSize(200, 24)
    elif t == ChannelView.Enabled:
        return Qt.QSize(50, 24)
    elif t == ChannelView.Output:
        return Qt.QSize(50, 24)
    elif t == ChannelView.PlotType:
        return Qt.QSize(50, 24)
    elif t == ChannelView.ValueRefEnabled:
        return Qt.QSize(50, 24)
    elif t == ChannelView.Synchronizer:
        return Qt.QSize(200, 24)
    return Qt.QSize(50, 24)


def getElementTypeToolTip(t):
    """Wrapper to prevent loading qtgui when this module is imported"""
    if t == ChannelView.Channel:
        return "Channel"
    elif t == ChannelView.Enabled:
        return "Channel active or not"
    elif t == ChannelView.Output:
        return "Channel output active or not"
    elif t == ChannelView.DataType:
        return "Type of data for storing (valid types are: char, float32, float64, [u]int{8|16|32|64})",
    elif t == ChannelView.PlotType:
        return "Plot type for this channel "
    elif t == ChannelView.PlotAxes:
        return "Independent variables to be used in the plot of this channel"
    elif t == ChannelView.Timer:
        return "The channel to be used as the timer"
    elif t == ChannelView.Monitor:
        return "The channel to be used as a monitor for stopping the acquisition"
    elif t == ChannelView.Synchronization:
        return "The channel to be used for triggering the acquisition"
    elif t == ChannelView.ValueRefEnabled:
        return "Channel value referencing active or not"
    elif t == ChannelView.ValueRefPattern:
        return "Channel value referencing pattern"
    elif t == ChannelView.Conditioning:
        return "An expression to evaluate on the data when displaying it"
    elif t == ChannelView.Normalization:
        return "Normalization mode for the data"
    elif t == ChannelView.NXPath:
        return "Location of the data of this channel within the NeXus tree"
    elif t == ChannelView.Synchronizer:
        return "Synchronization element"
    return "Unknown"


class BaseMntGrpChannelItem(TaurusBaseTreeItem):
    """ """

    dataChanged = Qt.pyqtSignal('QModelIndex', 'QModelIndex')

    def data(self, index):
        """Returns the data of this node for the given index

        :return: (object) the data for the given index
        """
        return self._itemData

    def role(self):
        """Returns the prefered role for the item.
        This implementation returns ChannelView.Unknown

        This method should be able to return any kind of python object as long
        as the model that is used is compatible.

        :return: (MacroView) the role in form of element type"""
        return ChannelView.Unknown


class MntGrpChannelItem(BaseMntGrpChannelItem):

    itemdata_keys_map = {ChannelView.Channel: 'label',
                         ChannelView.Enabled: 'enabled',
                         ChannelView.Output: 'output',
                         ChannelView.DataType: 'data_type',
                         ChannelView.PlotType: 'plot_type',
                         ChannelView.PlotAxes: 'plot_axes',
                         #                         ChannelView.Timer:'timer',
                         #                         ChannelView.Monitor:'monitor',
                         #                         ChannelView.Synchronization:'trigger',
                         ChannelView.ValueRefEnabled: 'value_ref_enabled',
                         ChannelView.ValueRefPattern: 'value_ref_pattern',
                         ChannelView.Conditioning: 'conditioning',
                         ChannelView.Normalization: 'normalization',
                         ChannelView.NXPath: 'nexus_path',
                         }

    def data(self, index):
        """Returns the data of this node for the given index

        :return: (object) the data for the given index
        """
        taurus_role = index.model().role(index.column())
        ch_name, ch_data = self.itemData()
        key = self.itemdata_keys_map[taurus_role]
        ret = ch_data[key]
        if taurus_role == ChannelView.PlotType:
            ret = PlotType[ret]
        elif taurus_role == ChannelView.Normalization:
            ret = Normalization[ret]
        elif taurus_role == ChannelView.PlotAxes:
            ret = "|".join(ret)
        return ret

    def setData(self, index, qvalue):
        ch_name, ch_data = self.itemData()
        taurus_role = index.model().role(index.column())
        key = self.itemdata_keys_map[taurus_role]
        if taurus_role in (ChannelView.Channel, ChannelView.Conditioning,
                           ChannelView.NXPath, ChannelView.Enabled,
                           ChannelView.Output, ChannelView.ValueRefEnabled,
                           ChannelView.ValueRefPattern):
            data = qvalue
        elif taurus_role == ChannelView.DataType:
            if len(qvalue.strip()) == 0:
                # empty strings are considered as unspecified data type
                try:
                    ch_data.pop(key)
                except KeyError:
                    pass  # data_type key may not be there if not specified
                return
            else:
                data = qvalue
        elif taurus_role == ChannelView.PlotType:
            data = PlotType[qvalue]
        elif taurus_role == ChannelView.Normalization:
            data = Normalization[qvalue]
        elif taurus_role == ChannelView.PlotAxes:
            data = [a for a in qvalue.split('|')]
        else:
            raise NotImplementedError('Unknown role')
        ch_data[key] = data

    def role(self):
        return ChannelView.Channel

    def toolTip(self, index):
        return "Channel " + self._itemData[0]

    def icon(self, index):
        taurus_role = index.model().role(index.column())
        if taurus_role == ChannelView.Channel:
            return Qt.QIcon("actions:system-shutdown.svg")


class MntGrpUnitItem(TaurusBaseTreeItem):
    pass


class BaseMntGrpChannelModel(TaurusBaseModel):
    ColumnNames = ("Channel", "enabled", "output", "Data Type",
                   "Plot Type", "Plot Axes", "Timer", "Monitor",
                   "Synchronizer", "Synchronization", "Ref Enabled",
                   "Ref Pattern", "Conditioning",
                   "Normalization", "NeXus Path")
    ColumnRoles = ((ChannelView.Channel, ChannelView.Channel),
                   ChannelView.Enabled, ChannelView.Output,
                   ChannelView.DataType, ChannelView.PlotType,
                   ChannelView.PlotAxes, ChannelView.Timer,
                   ChannelView.Monitor, ChannelView.Synchronizer,
                   ChannelView.Synchronization, ChannelView.ValueRefEnabled,
                   ChannelView.ValueRefPattern, ChannelView.Conditioning,
                   ChannelView.Normalization, ChannelView.NXPath)
    DftFont = Qt.QFont()

    _availableChannels = {}
    _availableTriggers = {}
    data_keys_map = {ChannelView.Timer: 'timer',
                     ChannelView.Monitor: 'monitor',
                     ChannelView.Synchronization: 'synchronization',
                     ChannelView.Synchronizer: 'synchronizer'
                     }

    def __init__(self, parent=None, data=None):
        TaurusBaseModel.__init__(self, parent=parent, data=data)
        self._mgconfig = None
        self._dirty = False

    def setAvailableChannels(self, cdict):
        self._availableChannels = cdict

    def getAvailableChannels(self):
        return self._availableChannels

    def setAvailableTriggers(self, tdict):
        self._availableTriggers = tdict

    def getAvailableTriggers(self):
        return self._availableTriggers

    def createNewRootItem(self):
        return BaseMntGrpChannelItem(self, self.ColumnNames)

    def roleIcon(self, taurus_role):
        return getElementTypeIcon(taurus_role)

    def roleSize(self, taurus_role):
        return getElementTypeSize(taurus_role)

    def roleToolTip(self, taurus_role):
        return getElementTypeToolTip(taurus_role)

    def getPyData(self, ctrlname=None, chname=None, key=None):
        '''
        If controller name and channel name are given, it returns the dictionary with the channel info.
        If only controller name is given, it returns the dictionary with the controller info.

        Note that it will raise a KeyError exception if any of the keys are not
        found or if chname is given without providing the unit id
        '''
        if ctrlname is None:
            raise ValueError('controller name must be passed')
        if chname is None:
            return self._mgconfig['controllers'][ctrlname]
        else:
            return self._mgconfig['controllers'][ctrlname]['channels'][chname]

    def setupModelData(self, mgconfig):
        if mgconfig is None:
            return
        root = self._rootItem  # @The root could eventually be changed for each unit or controller
        channelNodes = [MntGrpChannelItem(
            self, chcfg, root) for chcfg in getChannelConfigs(mgconfig)]
        for ch in channelNodes:
            root.appendChild(ch)
        self.updateMntGrpChannelIndex(root=root)
        # store the whole config object for accessing the info that is not at
        # the channel level
        self._mgconfig = mgconfig

    def setDataSource(self, data_src):
        self._dirty = False
        TaurusBaseModel.setDataSource(self, data_src)

    def updateMntGrpChannelIndex(self, root=None):
        '''
        assigns the MeasurementGroup index (the internal order in the MG)
        according to the order in the QModel
        '''
        if root is None:
            root = self._rootItem
        for row in range(root.childCount()):
            chname, chdata = root.child(row).itemData()
            chdata['index'] = row

    def flags(self, index):
        flags = TaurusBaseModel.flags(self, index)
        taurus_role = self.role(index.column())
        if taurus_role == ChannelView.Channel:  # channel column is not editable
            return flags
        elif taurus_role in (ChannelView.Timer,
                             ChannelView.Monitor,
                             ChannelView.Synchronizer,
                             ChannelView.Synchronization):
            ch_name, ch_data = index.internalPointer().itemData()
            if not ch_data['_controller_name'].startswith("__"):
                ch_info = self.getAvailableChannels()[ch_name]
                # only timerable channels accept these configurations
                if ch_info['type'] in ('CTExpChannel',
                                       'OneDExpChannel',
                                       'TwoDExpChannel'):
                    flags |= Qt.Qt.ItemIsEditable
        else:
            flags |= Qt.Qt.ItemIsEditable
        return flags

    def data(self, index, role=Qt.Qt.DisplayRole):
        """Reimplemented from :meth:`TaurusBaseModel.data`

        :return: (object) the data for the given index
        """
        # Try with the normal TaurusBaseModel item-oriented approach
        try:
            return TaurusBaseModel.data(self, index, role=role)
        except:
            pass
        # For those things which are inter-item, we handle them here
        taurus_role = self.role(index.column())
        if taurus_role == ChannelView.Synchronization:
            ch_name, ch_data = index.internalPointer().itemData()
            ctrlname = ch_data['_controller_name']
            if ctrlname.startswith("__"):
                return None
            ch_info = self.getAvailableChannels()[ch_name]
            if ch_info['type'] not in ('CTExpChannel',
                                       'OneDExpChannel',
                                       'TwoDExpChannel'):
                return None
            unitdict = self.getPyData(ctrlname=ctrlname)
            key = self.data_keys_map[taurus_role]
            synchronization = unitdict[key]
            return AcqSynchType[synchronization]
        elif taurus_role in (ChannelView.Timer, ChannelView.Monitor):
            ch_name, ch_data = index.internalPointer().itemData()
            ctrlname = ch_data['_controller_name']
            if ctrlname.startswith("__"):
                return None
            ch_info = self.getAvailableChannels()[ch_name]
            if ch_info['type'] in ('CTExpChannel', 'OneDExpChannel', 'TwoDExpChannel'):
                unitdict = self.getPyData(ctrlname=ctrlname)
                key = self.data_keys_map[taurus_role]
                master_full_name = unitdict.get(key, None)
            else:
                key = taurus_role == ChannelView.Timer and 'timer' or 'monitor'
                master_full_name = self._mgconfig.get(key, None)
            if master_full_name is None:
                return None
            else:
                master_info = self.getAvailableChannels()[master_full_name]
                return master_info['name']
        elif taurus_role == ChannelView.Synchronizer:
            ch_name, ch_data = index.internalPointer().itemData()
            ctrlname = ch_data['_controller_name']
            key = self.data_keys_map[taurus_role]
            ctrl_data = self.getPyData(ctrlname=ctrlname)
            trigger_fullname = ctrl_data.get(key, None)
            all_triggers = self.getAvailableTriggers()
            if trigger_fullname is None:
                return None
            else:
                trigger_name = all_triggers[trigger_fullname]
                return trigger_name['name']

        return None

    def setData(self, index, qvalue, role=Qt.Qt.EditRole):
        # For those things which are at the unit level, we handle them here
        taurus_role = self.role(index.column())
        if taurus_role in (ChannelView.Timer, ChannelView.Monitor, ChannelView.Synchronization):
            ch_name, ch_data = index.internalPointer().itemData()
            ch_info = self.getAvailableChannels()[ch_name]
            ctrl_data = self.getPyData(ctrlname=ch_data['_controller_name'])
            key = self.data_keys_map[taurus_role]
            data = qvalue
            self._dirty = True
            self.beginResetModel()
            is_settable = ch_info['type'] in (
                'CTExpChannel', 'OneDExpChannel', 'TwoDExpChannel')
            if taurus_role == ChannelView.Synchronization:
                data = AcqSynchType[data]
                if is_settable:
                    ctrl_data[key] = data
            else:
                if is_settable:
                    if ctrl_data[key] == self._mgconfig[key]:
                        self._mgconfig[key] = data
                    ctrl_data[key] = data
                else:
                    self._mgconfig[key] = data
            self.endResetModel()
            return True
        elif taurus_role == ChannelView.Synchronizer:
            ch_name, ch_data = index.internalPointer().itemData()
            ctrlname = ch_data['_controller_name']
            key = self.data_keys_map[taurus_role]
            self._dirty = True
            self.beginResetModel()
            ctrl_data = self.getPyData(ctrlname=ctrlname)
            ctrl_data[key] = qvalue
            self.endResetModel()
            return True
        # for the rest, we use the regular TaurusBaseModel item-oriented approach
        # ret = self._setData(index, qvalue, role) #@todo we do not use
        # _setData because it is not Qt4.4-compatible
        item = index.internalPointer()
        item.setData(index, qvalue)
        self._dirty = True
        self.dataChanged.emit(index, index)
        return True

    # @todo: Very inefficient implementation. We should use {begin|end}InsertRows
    def addChannel(self, chname=None, chinfo=None, ctrlname=None, external=False):

        if chname is None:
            chname = chinfo['full_name']
        chname = str(chname)
        if ctrlname is None:
            desc = self.getAvailableChannels()[chname]
            ctrlname = desc['controller']

        # update the internal data
        self.beginResetModel()  # we are altering the internal data here, so we need to protect it
        ctrlsdict = self.dataSource()['controllers']
        if ctrlname not in ctrlsdict:
            ctrlsdict[ctrlname] = ctrl = {'channels': {}}
            if not external and chinfo['type'] in ('CTExpChannel', 'OneDExpChannel', 'TwoDExpChannel'):
                ctrl['timer'] = chname
                ctrl['monitor'] = chname
                ctrl['synchronizer'] = "software"
                ctrl['synchronization'] = AcqSynchType.Trigger
        else:
            ctrl = ctrlsdict[ctrlname]
        channelsdict = ctrl['channels']
        if chname in channelsdict:
            self.error(
                'Channel "%s" is already in the measurement group. It will not be added again' % chname)
            return

        self._dirty = True
        if external:
            channelsdict[chname] = createChannelDict(chname)
        else:
            channelsdict[chname] = createChannelDict(chinfo)
        self.endResetModel()  # we are altering the internal data here, so we need to protect it
        self.refresh()  # note that another reset will be done here...

        #import pprint
        # pprint.pprint(self.dataSource())

    # @todo: Very inefficient implementation. We should use {begin|end}InsertRows
    def removeChannels(self, chnames):
        # update the internal data
        self._dirty = True
        self.beginResetModel()  # we are altering the internal data here, so we need to protect it
        for chname in chnames:
            avail_channels = self.getAvailableChannels()
            if chname in avail_channels:
                desc = self.getAvailableChannels()[chname]
                ctrlname = desc['controller']
            else:
                #@todo: This assumes that if it is not in the list of avail_channels, it must be an external tango channel
                ctrlname = '__tango__'
            try:
                self.dataSource()['controllers'][ctrlname][
                    'channels'].pop(chname)
                try:
                    if not self.dataSource()['controllers'][ctrlname]['channels']:
                        self.dataSource()['controllers'].pop(ctrlname)
                except:
                    self.error('error cleaning the data source dictionary')
            except:
                self.error('cannot find "%s" for removing' % chname)

        self.endResetModel()  # we are altering the internal data here, so we need to protect it
        self.refresh()  # note that another reset will be done here...

    # @todo: Very inefficient implementation. We should use {begin|end}MoveRows
    def swapChannels(self, root, row1, row2):
        self._dirty = True
        n1, d1 = root.child(row1).itemData()
        n2, d2 = root.child(row2).itemData()
        d1['index'], d2['index'] = d2['index'], d1['index']
        self.debug("swapping %s with %s" % (n1, n2))
        self.refresh()

    def isDataChanged(self):
        return self._dirty

    def setDataChanged(self, datachanged):
        self._dirty = datachanged


class MntGrpChannelModel(BaseMntGrpChannelModel):
    '''A BaseMntGrpChannelModel that communicates with a MntGrp device for setting and reading the configuration
    '''

    def setDataSource(self, mg):
        if self._data_src is not None:
            self._data_src.configurationChanged.disconnect(
                self.configurationChanged)
        if mg is not None:
            mg.configurationChanged.connect(self.configurationChanged)
        BaseMntGrpChannelModel.setDataSource(self, mg)

    def configurationChanged(self):
        self.refresh()

    def setupModelData(self, mg):
        if mg is None:
            return
        BaseMntGrpChannelModel.setupModelData(self, self.getSourceData())

    def writeSourceData(self):
        mg = self.dataSource()
        if mg is not None and self._mgconfig is not None:
            mg.setConfiguration(self._mgconfig)

    def getSourceData(self):
        """Gets data from the dataSource"""
        mg = self.dataSource()
        if mg is not None:
            return mg.getConfiguration()

    def getLocalData(self):
        """Gets the local data (may be different from the one in the data source
        since it may have been modified by the user)"""
        return self._mgconfig


class AxesSelector(Qt.QWidget):

    def __init__(self, parent, n=0, choices=None):
        '''Shows n comboboxes populated with choices. If n is 0, it just shows a LineEdit instead'''
        Qt.QWidget.__init__(self, parent)
        self._n = n
        self._CBs = []
        self._LE = None
        l = Qt.QHBoxLayout(self)
        if self._n == 0:
            self._LE = Qt.QLineEdit()
            l.addWidget(self._LE)
        else:
            for i in range(n):
                cb = Qt.QComboBox()
                l.addWidget(cb)
                self._CBs.append(cb)
        if choices is not None:
            self.setChoices(choices)

    def setChoices(self, choices):
        for cb in self._CBs:
            cb.addItems(choices)

    def text(self):
        return "|".join(self.getCurrentChoices())

    def getCurrentChoices(self):
        if self._LE is None:
            return [str(cb.currentText()) for cb in self._CBs]
        else:
            return [str(self._LE.text())]

    def setCurrentChoices(self, choice):
        if self._LE is None:
            texts = str(choice).split('|')
            for t, cb in zip(texts[:len(self._CBs)], self._CBs):
                cb.setCurrentIndex(max(0, cb.findText(t)))
        else:
            self._LE.setText(str(choice))


class ChannelDelegate(Qt.QStyledItemDelegate):

    def createEditor(self, parent, option, index):
        model = index.model()
        taurus_role = model.role(index.column())
        if taurus_role in (ChannelView.Channel, ChannelView.PlotType, ChannelView.Normalization,
                           ChannelView.Timer, ChannelView.Monitor, ChannelView.Synchronization,
                           ChannelView.Synchronizer):
            ret = Qt.QComboBox(parent)
        elif taurus_role == ChannelView.PlotAxes:
            item = index.internalPointer()
            ptype = item.itemData()[1]['plot_type']
            if ptype == PlotType.Spectrum:
                n = 1
            elif ptype == PlotType.Image:
                n = 2
            else:
                return None
            ret = AxesSelector(parent, n=n)
        else:
            ret = Qt.QStyledItemDelegate.createEditor(
                self, parent, option, index)
        ret.setAutoFillBackground(True)
        return ret

    def setEditorData(self, editor, index):
        model = index.model()
        dataSource = model.dataSource()
        taurus_role = model.role(index.column())
        if taurus_role == ChannelView.PlotType:
            editor.addItems(list(PlotType.keys()))
            current = model.data(index)
            editor.setCurrentIndex(editor.findText(current))
        elif taurus_role == ChannelView.Normalization:
            editor.addItems(list(Normalization.keys()))
            current = model.data(index)
            editor.setCurrentIndex(editor.findText(current))
        elif taurus_role in (ChannelView.Timer, ChannelView.Monitor):
            key = taurus_role == ChannelView.Timer and 'timer' or 'monitor'
            ch_name, ch_data = index.internalPointer().itemData()
            ctrl_filterlist = [ch_data['_controller_name']]
            ctrl_dict = getChannelConfigs(dataSource, ctrls=ctrl_filterlist)
            all_channels = model.getAvailableChannels()
            # if it is a timer capable type of element
            if all_channels[ch_name]['type'] in ('CTExpChannel', 'OneDExpChannel', 'TwoDExpChannel'):
                for full_name, channel_data in ctrl_dict:
                    editor.addItem(
                        channel_data['name'], full_name)
                current = model.data(index)
                editor.setCurrentIndex(editor.findText(current))
            else:
                for ctrl_data in list(dataSource['controllers'].values()):
                    if key in ctrl_data:
                        channel = all_channels[ctrl_data[key]]
                        editor.addItem(channel['name'], channel['full_name'])
                current = dataSource.get(key)  # current global timer/monitor
                editor.setCurrentIndex(editor.findData(current))
        elif taurus_role == ChannelView.Synchronization:
            editor.addItems(list(AcqSynchType.keys()))
            current = model.data(index)
            editor.setCurrentIndex(editor.findText(current))
        elif taurus_role == ChannelView.PlotAxes:
            selectables = ['<idx>', '<mov>'] + \
                [n for n, d in getChannelConfigs(dataSource)]
            editor.setChoices(selectables)
            current = model.data(index)
            editor.setCurrentChoices(current)
        elif taurus_role == ChannelView.Synchronizer:
            # add the triggergates to the editor
            all_triggers = model.getAvailableTriggers()
            for full_name, tg_data in list(all_triggers.items()):
                editor.addItem(tg_data['name'], full_name)
                current = model.data(index)
                editor.setCurrentIndex(editor.findText(current))
        else:
            Qt.QStyledItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        taurus_role = model.role(index.column())
        dataSource = model.dataSource()
        if taurus_role in (ChannelView.Channel, ChannelView.PlotType, ChannelView.Normalization):
            data = editor.currentText()
            model.setData(index, data)
        elif taurus_role == ChannelView.Synchronization:
            old_value = model.data(index)
            new_value = str(editor.currentText())
            if new_value == old_value:
                return
            ch_name, ch_data = index.internalPointer().itemData()
            channels = getChannelConfigs(
                dataSource, ctrls=[ch_data['_controller_name']])
            affected = [d['name'] for n, d in channels]
            if len(affected) > 1:
                op = Qt.QMessageBox.question(editor, "Caution: multiple channels affected",
                                             "This change will also affect the following channels:\n- %s \nContinue?" % "\n- ".join(
                                                 affected),
                                             Qt.QMessageBox.Yes | Qt.QMessageBox.Cancel)
                if op != Qt.QMessageBox.Yes:
                    return
            data = new_value
            model.setData(index, data)
        elif taurus_role in (ChannelView.Timer, ChannelView.Monitor):
            key = taurus_role == ChannelView.Timer and 'timer' or 'monitor'
            old_value = model.data(index)
            new_value = str(editor.currentText())
            if new_value == old_value:
                return
            ch_name, ch_data = index.internalPointer().itemData()
            all_channels = model.getAvailableChannels()
            # if it is a timer capable type of element
            ch_info = all_channels[ch_name]
            selected_master = editor.itemData(editor.currentIndex())
            if ch_info['type'] in ('CTExpChannel', 'OneDExpChannel', 'TwoDExpChannel'):
                affected = []
                ctrl_data = model.getPyData(
                    ctrlname=ch_data['_controller_name'])
                channels = getChannelConfigs(
                    dataSource, ctrls=[ch_data['_controller_name']])
                for n, d in channels:
                    affected.append(d['name'])
                # if old timer/monitor was also the global, then non
                # timerable/monitorable channels must be changed
                if ctrl_data[key] == dataSource.get(key):
                    for n, d in getChannelConfigs(dataSource):
                        if d['_controller_name'].startswith("__"):
                            continue
                        ch_info = all_channels[n]
                        if ch_info['type'] in ('CTExpChannel', 'OneDExpChannel', 'TwoDExpChannel'):
                            continue
                        affected.append(d['name'])

                if len(affected) > 1:
                    op = Qt.QMessageBox.question(editor, "Caution: multiple channels affected",
                                                 "This change will also affect the following channels:\n- %s \nContinue?" % "\n- ".join(
                                                     affected),
                                                 Qt.QMessageBox.Yes | Qt.QMessageBox.Cancel)
                    if op != Qt.QMessageBox.Yes:
                        return
            else:
                affected = []
                channels = getChannelConfigs(dataSource)
                for n, d in channels:
                    if d['_controller_name'].startswith("__"):
                        continue
                    ch_info = all_channels[n]
                    if ch_info['type'] in ('CTExpChannel', 'OneDExpChannel', 'TwoDExpChannel'):
                        continue
                    affected.append(d['name'])
                if len(affected) > 1:
                    op = Qt.QMessageBox.question(editor, "Caution: multiple channels affected",
                                                 "This change will also affect the following channels:\n- %s \nContinue?" % "\n- ".join(
                                                     affected),
                                                 Qt.QMessageBox.Yes | Qt.QMessageBox.Cancel)
                    if op != Qt.QMessageBox.Yes:
                        return
            model.setData(index, selected_master)
        elif taurus_role == ChannelView.PlotAxes:
            data = editor.text()
            model.setData(index, data)
        elif taurus_role == ChannelView.Synchronizer:
            old_value = model.data(index)
            new_value = str(editor.currentText())
            if new_value == old_value:
                return

            ch_name, ch_data = index.internalPointer().itemData()
            ctrl_name = ch_data['_controller_name']
            ctrl_data = dataSource['controllers'][ctrl_name]
            # get the affected channels
            affected = []
            channels = ctrl_data.get('channels')
            for _, ch_data in list(channels.items()):
                affected.append(ch_data['name'])

            if len(affected) > 1:
                op = Qt.QMessageBox.question(editor, "Caution: multiple channels affected",
                                             "This change will also affect the following channels:\n- %s \nContinue?" % "\n- ".join(
                                                 affected),
                                             Qt.QMessageBox.Yes | Qt.QMessageBox.Cancel)
                if op != Qt.QMessageBox.Yes:
                    return

            selected_master = editor.itemData(editor.currentIndex())
            model.setData(index, selected_master)
        else:
            Qt.QStyledItemDelegate.setModelData(self, editor, model, index)


class MntGrpChannelEditor(TaurusBaseTableWidget):
    """
    """

    KnownPerspectives = {
        "Channel": {
            "label": "Channels",
            "icon": "actions:system-shutdown.svg",
            "tooltip": "View by channel",
            "model": [BaseMntGrpChannelModel, ],
        },
    }

    DftPerspective = "Channel"
    _simpleViewColumns = (ChannelView.Channel, ChannelView.Output,
                          ChannelView.PlotType, ChannelView.PlotAxes)
    _simpleView = False

    def __init__(self, parent=None, designMode=False, with_filter_widget=True, perspective=None):
        TaurusBaseTableWidget.__init__(self, parent=parent, designMode=designMode,
                                       with_filter_widget=with_filter_widget,
                                       perspective=perspective, proxy=None)
        self.setContextMenuPolicy(Qt.Qt.ActionsContextMenu)
        self._simpleViewAction = Qt.QAction("Simple View", self)
        self._simpleViewAction.setCheckable(True)
        self._simpleViewAction.toggled.connect(self.setSimpleView)
        self.addAction(self._simpleViewAction)
        self.registerConfigProperty(
            self.isSimpleView, self.setSimpleView, "simpleView")

    def isSimpleView(self):
        return self._simpleView

    def setSimpleView(self, simpleview):
        if simpleview == self.isSimpleView():
            return
        columnRoles = list(self.getQModel().ColumnRoles)
        # account for the fact that the first element is a tuple instead of a
        # role
        columnRoles[0] = columnRoles[0][-1]
        columnIndexes = [columnRoles.index(r) for r in self._simpleViewColumns]
        for i in range(self.getQModel().columnCount()):
            hide = simpleview and (i not in columnIndexes)
            self.tableView().setColumnHidden(i, hide)
        self._simpleView = simpleview
        self._simpleViewAction.setChecked(simpleview)

    def resetSimpleView(self):
        self.setSimpleView(False)

    def createViewWidget(self):
        tableView = TaurusBaseTableWidget.createViewWidget(self)
        self._delegate = ChannelDelegate(self)
        # self._delegate.setItemEditorFactory(Qt.QItemEditorFactory()) #This
        # causes a segfault when calling ChannelDelegate.createEditor
        tableView.setItemDelegate(self._delegate)
        tableView.setSortingEnabled(False)
        self._editorBar.addTriggered.connect(self.addChannel)
        self._editorBar.removeTriggered.connect(self.removeChannels)
        self._editorBar.moveUpTriggered.connect(self.moveUpChannel)
        self._editorBar.moveDownTriggered.connect(self.moveDownChannel)
        self._editorBar.moveTopTriggered.connect(self.moveTopChannel)
        self._editorBar.moveBottomTriggered.connect(self.moveBottomChannel)
        return tableView

    def createToolArea(self):
        ta = TaurusBaseTableWidget.createToolArea(self)
        e_bar = self._editorBar = EditorToolBar(self, self)
        ta.append(e_bar)
        return ta

    def getModelClass(self):
        return TaurusDevice

    def addChannel(self, channel=None):
        qmodel = self.getQModel()
        dataSource = qmodel.dataSource()
        if channel is None:
            shown = [n for n, d in getChannelConfigs(dataSource)]
            avail_channels = qmodel.getAvailableChannels()
            clist = [ch_info['name'] for ch_name, ch_info
                     in list(avail_channels.items())
                     if ch_name not in shown]
            clist = sorted(clist) + ['(Other...)']
            chname, ok = Qt.QInputDialog.getItem(
                self, "New Channel", "Choose channel:", clist, 0, False)
            if not ok:
                return
        chname = str(chname)
        if chname == '(Other...)':
            models, ok = TaurusModelChooser.modelChooserDlg(parent=self, singleModel=False, windowTitle='Choose source of data',
                                                            selectables=[TaurusElementType.Attribute])
            if not ok:
                return
            for m in models:
                qmodel.addChannel(
                    chname=m, ctrlname='__tango__', external=True)
        else:
            for ch_info in list(avail_channels.values()):
                if ch_info['name'] == chname:
                    qmodel.addChannel(chinfo=ch_info)

    def removeChannels(self, channels=None):
        if channels is None:
            channels = self.selectedItems()
        chnames = [ch.itemData()[0] for ch in channels]
        self.getQModel().removeChannels(chnames)

    def _getSelectedChannel(self):
        channels = self.selectedItems()
        if len(channels) != 1:
            return None
        return channels[0]

    def moveBottomChannel(self):
        channel = self._getSelectedChannel()
        if channel is None:
            return
        row = channel.row()
        parent = channel.parent()
        if row >= parent.childCount() - 1:
            return
        else:
            # TODO: optimize it if necessary. Instead of moving one by one,
            # try to remove the item from the list and insert it at the bottom.
            self.moveDownChannel()
            return self.moveBottomChannel()

    def moveTopChannel(self):
        channel = self._getSelectedChannel()
        if channel is None:
            return
        row = channel.row()
        if row < 1:
            return
        else:
            # TODO: optimize it if necessary. Instead of moving one by one,
            # try to remove the item from the list and insert it at the top.
            self.moveUpChannel()
            return self.moveTopChannel()

    def moveUpChannel(self, channel=None):
        if channel is None:
            channel = self._getSelectedChannel()
            if channel is None:
                return
        parent = channel.parent()
        row = channel.row()
        if row < 1:
            return
        model = self.getQModel()
        model.swapChannels(parent, row, row - 1)
        idx = model.index(row - 1, 0)
        self.viewWidget().setCurrentIndex(idx)

    def moveDownChannel(self, channel=None):
        if channel is None:
            channel = self._getSelectedChannel()
            if channel is None:
                return
        parent = channel.parent()
        row = channel.row()
        if row >= parent.childCount() - 1:
            return
        model = self.getQModel()
        self.getQModel().swapChannels(parent, row, row + 1)
        idx = model.index(row + 1, 0)
        self.viewWidget().setCurrentIndex(idx)

    def getLocalConfig(self):
        return self.getQModel().getLocalData()

    @classmethod
    def getQtDesignerPluginInfo(cls):
        ret = TaurusBaseTableWidget.getQtDesignerPluginInfo()
        ret['module'] = 'taurus.qt.qtgui.extra_sardana'
        ret['group'] = 'Taurus Sardana'
        ret['icon'] = ":/designer/table.png"
        return ret

    simpleView = Qt.pyqtProperty(
        "bool", isSimpleView, setSimpleView, resetSimpleView)
