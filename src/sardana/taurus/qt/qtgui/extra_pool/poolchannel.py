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
channelWidgets.py:
"""

__all__ = ["PoolChannel", "PoolChannelTV", "_PoolChannelTV"]

import weakref

import tango
import taurus
from taurus.core import DataType, DataFormat
from taurus.external.qt import Qt
from taurus.qt.qtcore.mimetypes import (TAURUS_DEV_MIME_TYPE,
                                        TAURUS_ATTR_MIME_TYPE)
from taurus.qt.qtgui.panel import (TaurusValue, TaurusDevButton,
                                   DefaultLabelWidget, DefaultUnitsWidget,
                                   TaurusAttrForm, TaurusForm,
                                   DefaultReadWidgetLabel, TaurusPlotButton,
                                   TaurusImageButton, TaurusValuesTableButton,
                                   )
from taurus.qt.qtgui.input import TaurusValueLineEdit
from taurus.qt.qtgui.dialog import ProtectTaurusMessageBox
from taurus.qt.qtgui.compact import TaurusReadWriteSwitcher
from taurus.qt.qtgui.container import TaurusWidget
from taurus.qt.qtgui.resource import getIcon
from sardana.taurus.qt.qtgui.extra_pool.poolmotor import \
    LabelWidgetDragsDeviceAndAttribute, TaurusAttributeListener


class PoolChannelTVLabelWidget(TaurusWidget):
    """
    @TODO tooltip should be extended with status info
    @TODO context menu should be the lbl_alias extended
    @TODO default tooltip extended with the complete (multiline) status
    @TODO rightclick popup menu with actions: (1) switch user/expert view,
          (2) Config -all attributes-, (3) change channel
          For the (3), a drop event should accept if it is a device,
          and add it to the "change-channel" list and select
    """

    def __init__(self, parent=None, designMode=False):
        TaurusWidget.__init__(self, parent, designMode)
        self.setLayout(Qt.QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        self.lbl_alias = DefaultLabelWidget(parent, designMode)
        self.lbl_alias.setBgRole("none")
        self.layout().addWidget(self.lbl_alias)

        # I don't like this approach, there should be something like
        # self.lbl_alias.addAction(...)
        self.lbl_alias.contextMenuEvent = \
            lambda event: self.contextMenuEvent(event)

        # I' don't like this approach, there should be something like
        # self.lbl_alias.addToolTipCallback(self.calculate_extra_tooltip)
        self.lbl_alias.getFormatedToolTip = self.calculateExtendedTooltip

        # I' don't like this approach, there should be something like
        # self.lbl_alias.disableDrag() or self.lbl_alias.setDragEnabled(False)
        # or better, define if Attribute or Device or Both have to be included
        # in the mimeData
        self.lbl_alias.mouseMoveEvent = self.mouseMoveEvent

    def setModel(self, model):
        if model in (None, ""):
            self.lbl_alias.setModel(model)
            TaurusWidget.setModel(self, model)
            return
        self.lbl_alias.taurusValueBuddy = self.taurusValueBuddy
        self.lbl_alias.setModel(model)
        TaurusWidget.setModel(self, model + "/Status")

    def calculateExtendedTooltip(self, cache=False):
        default_label_widget_tooltip = DefaultLabelWidget.getFormatedToolTip(
            self.lbl_alias, cache)
        status_info = ""
        channel_dev = self.taurusValueBuddy().channel_dev
        if channel_dev is not None:
            status = channel_dev.getAttribute("Status").read().value
            # MAKE IT LOOK LIKE THE STANDARD TABLE FOR TAURUS TOOLTIPS
            status_lines = status.split("\n")
            status_info = ("<TABLE width='500' border='0' cellpadding='1' "
                           "cellspacing='0'><TR><TD WIDTH='80' ALIGN='RIGHT'"
                           "VALIGN='MIDDLE'><B>Status:</B></TD><TD>"
                           + status_lines[0]
                           + "</TD></TR>")
            for status_extra_line in status_lines[1:]:
                status_info += ("<TR><TD></TD><TD>"
                                + status_extra_line
                                + "</TD></TR>")
            status_info += "</TABLE>"
        return default_label_widget_tooltip + status_info

    def contextMenuEvent(self, event):
        # Overwrite the default taurus label behaviour
        menu = Qt.QMenu(self)
        action_tango_attributes = Qt.QAction(self)
        action_tango_attributes.setIcon(
            getIcon(":/categories/preferences-system.svg"))
        action_tango_attributes.setText("Tango Attributes")
        menu.addAction(action_tango_attributes)
        action_tango_attributes.triggered.connect(
            self.taurusValueBuddy().showTangoAttributes)

        cm_action = menu.addAction("Compact")
        cm_action.setCheckable(True)
        cm_action.setChecked(self.taurusValueBuddy().isCompact())
        cm_action.toggled.connect(self.taurusValueBuddy().setCompact)

        menu.exec_(event.globalPos())
        event.accept()

    def mouseMoveEvent(self, event):
        model = self.taurusValueBuddy().getModelObj()
        mimeData = Qt.QMimeData()
        mimeData.setText(self.lbl_alias.text())
        dev_name = model.getFullName().encode("utf-8")
        attr_name = dev_name + b"/Value"
        mimeData.setData(TAURUS_DEV_MIME_TYPE, dev_name)
        mimeData.setData(TAURUS_ATTR_MIME_TYPE, attr_name)

        drag = Qt.QDrag(self)
        drag.setMimeData(mimeData)
        drag.setHotSpot(event.pos() - self.rect().topLeft())
        drag.exec_(Qt.Qt.CopyAction, Qt.Qt.CopyAction)


class _IntegTimeTaurusValueLineEdit(TaurusValueLineEdit):

    def sizeHint(self):
        size = Qt.QSize()
        size.setWidth(55)
        return size


class PoolChannelTVExtraWidget(TaurusWidget):
    """
    """

    def __init__(self, parent=None, designMode=False):
        TaurusWidget.__init__(self, parent, designMode)
        self.setLayout(Qt.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        self.le_integ_time = _IntegTimeTaurusValueLineEdit()
        le_policy = Qt.QSizePolicy(Qt.QSizePolicy.Preferred,
                                   Qt.QSizePolicy.Preferred)
        self.le_integ_time.setSizePolicy(le_policy)
        self.layout().addWidget(self.le_integ_time)

        # TODO: state listener should be part of *ExpChannel device Taurus
        #       Qt extension, it is necessary to change button's action,
        #       icon, etc.
        self.state_listener = TaurusAttributeListener()
        self.state_listener.eventReceivedSignal.connect(self.updateState)
        self.btn_start_stop_clicked_slot = None
        self.btn_start_stop = Qt.QPushButton()
        btn_policy = Qt.QSizePolicy(Qt.QSizePolicy.Fixed,
                                    Qt.QSizePolicy.Preferred)
        btn_policy.setHorizontalStretch(0)
        self.btn_start_stop.setSizePolicy(btn_policy)
        self.layout().addWidget(self.btn_start_stop)

    def updateState(self, state):
        btn_start_stop = self.btn_start_stop
        if self.btn_start_stop_clicked_slot is not None:
            btn_start_stop.clicked.disconnect(
                self.btn_start_stop_clicked_slot)
        if state == tango.DevState.MOVING:
            btn_start_stop.setToolTip("Stop the channel")
            btn_start_stop.setIcon(
                getIcon(":/actions/media_playback_stop.svg"))
            self.btn_start_stop_clicked_slot = self.abort
        else:
            btn_start_stop.setToolTip("Start the channel")
            btn_start_stop.setIcon(
                getIcon(":/actions/media_playback_start.svg"))
            self.btn_start_stop_clicked_slot = self.start
        btn_start_stop.clicked.connect(self.btn_start_stop_clicked_slot)

    def setModel(self, model):
        # first disconnect old model state listener
        model_obj = self.getModelObj()
        if model_obj is not None:
            model_obj.getAttribute("State").removeListener(
                self.state_listener)
        TaurusWidget.setModel(self, model)
        if model in (None, ""):
            self.le_integ_time.setModel(model)
            return
        self.le_integ_time.setModel(model + "/IntegrationTime")
        # connect new model state listener
        self.getModelObj().getAttribute("State").addListener(
            self.state_listener)

    @Qt.pyqtSlot()
    @ProtectTaurusMessageBox(
        msg="An error occurred trying to start the acquisition.")
    def start(self):
        channel_dev = self.taurusValueBuddy().channel_dev
        if channel_dev is not None:
            channel_dev.Start()

    @Qt.pyqtSlot()
    @ProtectTaurusMessageBox(
        msg="An error occurred trying to abort the acquisition.")
    def abort(self):
        channel_dev = self.taurusValueBuddy().channel_dev
        if channel_dev is not None:
            channel_dev.abort()


class PoolChannelTVUnitsWidget(DefaultUnitsWidget):

    def __init__(self, parent=None, designMode=False):
        DefaultUnitsWidget.__init__(self, parent, designMode)

    def setModel(self, model):
        if model in (None, ""):
            DefaultUnitsWidget.setModel(self, model)
            return
        DefaultUnitsWidget.setModel(self, model + "/Value")


class PoolChannelTV(TaurusValue):
    """A widget that displays and controls a pool channel device.
    It differs from :class:`PoolChannel` in that it behaves as a TaurusValue
    (i.e., it allows its subwidgets to be aligned in columns in a TaurusForm)`

    .. todo:: Ideally overriding of `getDefaultReadWidgetClass` and
      `updateReadWidget` should not be necessary. Creation of a dedicated wiget
      for displaying value should be delegated to a custom read widget.
    .. todo:: draw state-based coloured frame around spectrum and image
       buttons, when state is MOVING - blue, when ON - green, etc.
    """

    def __init__(self, parent=None, designMode=False):
        TaurusValue.__init__(self, parent=parent, designMode=designMode)
        self.setLabelWidgetClass(PoolChannelTVLabelWidget)
        self.setWriteWidgetClass(None)
        self.setUnitsWidgetClass(PoolChannelTVUnitsWidget)
        self.setExtraWidgetClass(PoolChannelTVExtraWidget)
        self.channel_dev = None

    def getDefaultReadWidgetClass(self, returnAll=False):
        """
        Returns the default class (or classes) to use as read widget for the
        current model.

        Override TaurusValue.getDefaultReadWidgetClass. Simply do the same
        but based on the Value attribute while our model obj is a device.

        :param returnAll: (bool) if True, the return value is a list of valid
                          classes instead of just one class

        :return: (class or list<class>) the default class  to use for the read
                 widget (or, if returnAll==True, a list of classes that can
                 show the attribute ). If a list is returned, it will be
                 loosely ordered by preference, being the first element
                 always the default one.
        """
        modelobj = self.getModelObj()
        if modelobj is None:
            if returnAll:
                return [DefaultReadWidgetLabel]
            else:
                return DefaultReadWidgetLabel

        valueobj = modelobj.getAttribute("Value")
        if valueobj.data_format == DataFormat._0D:
            result = [DefaultReadWidgetLabel]
        elif valueobj.data_format == DataFormat._1D:
            if valueobj.type in (DataType.Float, DataType.Integer):
                result = [TaurusPlotButton,
                          TaurusValuesTableButton, DefaultReadWidgetLabel]
            else:
                result = [TaurusValuesTableButton, DefaultReadWidgetLabel]
        elif valueobj.data_format == DataFormat._2D:
            if valueobj.type in (DataType.Float, DataType.Integer):
                try:
                    # unused import but useful to determine if
                    # TaurusImageButton should be added
                    from taurus.qt.qtgui.extra_guiqwt import TaurusImageDialog  # noqa
                    result = [TaurusImageButton,
                              TaurusValuesTableButton, DefaultReadWidgetLabel]
                except ImportError:
                    result = [TaurusValuesTableButton,
                              DefaultReadWidgetLabel]
            else:
                result = [TaurusValuesTableButton, DefaultReadWidgetLabel]
        else:
            self.warning('Unsupported attribute type %s' % valueobj.type)
            result = None

        if returnAll:
            return result
        else:
            return result[0]

    def updateReadWidget(self):
        """Update read widget by recreating it from scratch.

        Override TaurusValue.updateReadWidget. Simply do the same, just
        don't call setModel on the read widget at the end. Model of the read
        widget is set by our setModel when the read widget is already
        recreated.
        """
        # get the class for the widget and replace it if necessary
        try:
            klass = self.readWidgetClassFactory(self.readWidgetClassID)
            self._readWidget = self._newSubwidget(self._readWidget, klass)
        except Exception as e:
            self._destroyWidget(self._readWidget)
            self._readWidget = Qt.QLabel('[Error]')
            msg = 'Error creating read widget:\n' + str(e)
            self._readWidget.setToolTip(msg)
            self.debug(msg)

        # take care of the layout
        self.addReadWidgetToLayout()

        if self._readWidget is not None:
            # give the new widget a reference to its buddy TaurusValue object
            self._readWidget.taurusValueBuddy = weakref.ref(self)
            if isinstance(self._readWidget, TaurusReadWriteSwitcher):
                self._readWidget.readWidget.taurusValueBuddy = weakref.ref(
                    self)
                self._readWidget.writeWidget.taurusValueBuddy = weakref.ref(
                    self)

            # tweak the new widget
            if self.minimumHeight() is not None:
                self._readWidget.setMinimumHeight(self.minimumHeight())

    def setModel(self, model):
        TaurusValue.setModel(self, model)
        if model == "" or model is None:
            return
        self.readWidget().setModel(model + "/Value")
        self.channel_dev = taurus.Device(model)

    def showTangoAttributes(self):
        model = self.getModel()
        taurus_attr_form = TaurusAttrForm()
        taurus_attr_form.setMinimumSize(Qt.QSize(555, 800))
        taurus_attr_form.setModel(model)
        taurus_attr_form.setWindowTitle(
            '%s Tango Attributes' % self.getModelObj().getSimpleName())
        taurus_attr_form.show()


class _ParentDevButton(TaurusDevButton):
    '''A TaurusDevButton that receives an attribute name but sets
    the corresponding device as model. **For internal use only** '''

    def __init__(self, **kwargs):
        TaurusDevButton.__init__(self, **kwargs)
        self.setText('')
        self.setSizePolicy(Qt.QSizePolicy.Preferred, Qt.QSizePolicy.Maximum)

    def setModel(self, model):
        try:
            attr = taurus.Attribute(model)
        except:
            return
        dev = attr.getParentObj()
        devname = dev.getFullName()
        TaurusDevButton.setModel(self, devname)


class _PoolChannelTV(TaurusValue):
    ''' A widget that displays and controls a pool channel device.
    It differs from :class:`PoolChannel` in that it behaves as a TaurusValue
    (i.e., it allows its subwidgets to be aligned in columns in a TaurusForm)`
    '''

    def __init__(self, parent=None, designMode=False):
        TaurusValue.__init__(self, parent=parent, designMode=designMode)
        self.setLabelWidgetClass(LabelWidgetDragsDeviceAndAttribute)
        self.setLabelConfig('{dev.name}')

    def getDefaultExtraWidgetClass(self):
        return _ParentDevButton

    def setModel(self, model):
        if model is not None:
            # @todo: change this (it assumes tango naming!)
            model = "%s/value" % model
        TaurusValue.setModel(self, model)

    def showEvent(self, event):
        TaurusValue.showEvent(self, event)
        try:
            self.getModelObj().getParentObj().getAttribute('Value').enablePolling(force=True)
        except:
            pass

    def hideEvent(self, event):
        TaurusValue.hideEvent(self, event)
        try:
            self.getModelObj().getParentObj().getAttribute('Value').disablePolling()
        except:
            pass



class PoolChannel(TaurusWidget):
    ''' A widget that displays and controls a pool channel device

    .. seealso:: :class:`PoolChannelTV`
    '''

    def __init__(self, parent=None, designMode=False):
        TaurusWidget.__init__(self, parent)

        self.setLayout(Qt.QHBoxLayout())

        # put a widget with a TaurusValue
        w = Qt.QWidget()
        w.setLayout(Qt.QGridLayout())
        self._TaurusValue = TaurusValue(parent=w, designMode=designMode)
        self._TaurusValue.setLabelWidgetClass(
            LabelWidgetDragsDeviceAndAttribute)
        self._TaurusValue.setLabelConfig('{dev.name}')
        self.layout().addWidget(w)

        #...and a dev button next to the widget
        self._devButton = TaurusDevButton(parent=self, designMode=designMode)
        self._devButton.setText('')
        self.layout().addWidget(self._devButton)

        self.modelChanged.connect(self._updateTaurusValue)

    def _updateTaurusValue(self):
        m = self.getModelName()
        self._TaurusValue.setModel("%s/value" % m)
        self._devButton.setModel(m)


if __name__ == "__main__":
    import sys
    argv = sys.argv
    if len(argv) > 0:
        models = argv[1:]
    app = Qt.QApplication(sys.argv)

    form_tv = TaurusForm()
    form_tv.setModifiableByUser(True)
    tv_widget_class = "sardana.taurus.qt.qtgui.extra_pool.PoolChannelTV"
    tv_class_map = {"CTExpChannel": (tv_widget_class, (), {}),
                    "OneDExpChannel": (tv_widget_class, (), {}),
                    "TwoDExpChannel": (tv_widget_class, (), {})}
    form_tv.setCustomWidgetMap(tv_class_map)
    form_tv.setModel(models)

    w = Qt.QWidget()
    w.setLayout(Qt.QVBoxLayout())
    w.layout().addWidget(form_tv)

    w.show()
    sys.exit(app.exec_())
