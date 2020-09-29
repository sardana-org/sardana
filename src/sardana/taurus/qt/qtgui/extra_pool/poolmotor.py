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

import operator
from enum import IntEnum

import PyTango

from taurus.external.qt import Qt, compat

import taurus
from taurus.core.util.colors import DEVICE_STATE_PALETTE
from taurus.core.taurusbasetypes import TaurusEventType
from taurus.core.tango.tangovalidator import TangoDeviceNameValidator
import taurus.qt.qtcore.mimetypes
from taurus.qt.qtgui.compact import TaurusReadWriteSwitcher
from taurus.qt.qtgui.dialog import ProtectTaurusMessageBox
from taurus.qt.qtgui.container import TaurusWidget
from taurus.qt.qtgui.container import TaurusFrame
from taurus.qt.qtgui.display import TaurusLabel
from taurus.qt.qtgui.input import TaurusValueLineEdit
from taurus.qt.qtgui.panel import DefaultLabelWidget
from taurus.qt.qtgui.panel import DefaultUnitsWidget
from taurus.qt.qtgui.panel import TaurusValue, TaurusAttrForm
from taurus.qt.qtcore.mimetypes import TAURUS_DEV_MIME_TYPE, TAURUS_ATTR_MIME_TYPE
from taurus.qt.qtgui.util.ui import UILoadable


class LimitsListener(Qt.QObject):
    """
    A class that listens to changes on motor limits.
    If that is the case it emits a signal so the application
    can do whatever with it.
    """

    updateLimits = Qt.pyqtSignal(compat.PY_OBJECT)

    def __init__(self):
        Qt.QObject.__init__(self)

    def eventReceived(self, evt_src, evt_type, evt_value):
        if evt_type not in [TaurusEventType.Change, TaurusEventType.Periodic]:
            return
        limits = evt_value.value
        self.updateLimits.emit(limits.tolist())


class Limit(IntEnum):
    Home = 0
    Positive = 1
    Negative = 2


class LimitInfo:

    def __init__(self, exist=False, active=False, status=""):
        # for software limit True when defined
        # for hardware limit True when physical motor, False when pseudo
        self.exist = exist
        self.active = active
        self.status = status


def eval_hw_limit(limit, value):
    """Evaluate hardware limit information

    :param limit: which limit (negative or positive)
    :type limit: `Limit`
    :param value: limit value, `None` means no hardware limit (pseudo motor)
    :type value: `bool` or `None`
    :return: limit information
    :rtype: `LimitInfo`
    """
    if limit is Limit.Positive:
        status = "Positive "
    elif limit is Limit.Negative:
        status = "Negative "
    else:
        raise ValueError("{} wrong limit".format(limit))
    exist = True
    active = False
    status += "hardware limit "
    if value is None:
        exist = False
        status += "does not exist."
    elif value:
        active = True
        status += "is active."
    else:
        status += "is not active."
    return LimitInfo(exist, active, status)


def eval_sw_limit(limit, position_attr):
    """Evaluate software limit information

    :param limit: which limit (negative or positive)
    :type limit: `Limit`
    :param position_attr: position attribute
    :type position_attr: `taurus.core.tango.TangoAttribute`
    :return: limit information
    :rtype: `LimitInfo`
    """
    if limit == Limit.Positive:
        getter_name = "getMaxRange"
        comparator = operator.ge
        not_defined = float("inf")
        status = "Positive "
    elif limit == Limit.Negative:
        getter_name = "getMinRange"
        comparator = operator.le
        not_defined = float("-inf")
        status = "Negative "
    else:
        raise ValueError("{} wrong limit".format(limit))
    active = False
    exist = False
    lim_value = getattr(position_attr, getter_name)().magnitude
    status += "software limit is "
    if lim_value == not_defined:
        status += "not defined."
    else:
        exist = True
        position = position_attr.read().rvalue.magnitude
        if comparator(position, lim_value):
            status += "active."
            active = True
        else:
            status += "defined."
    return LimitInfo(exist, active, status)


class PoolMotorClient():

    maxint_in_32_bits = 2147483647

    def __init__(self):
        self.motor_dev = None
        self.has_limits = False
        self.has_encoder = False

    def setMotor(self, pool_motor_dev_name):
        # AT SOME POINT THIS WILL BE USING THE 'POOL' TAURUS EXTENSION
        # TO OPERATE THE MOTOR INSTEAD OF A 'TANGO' TAURUSDEVICE
        try:
            self.motor_dev = taurus.Device(pool_motor_dev_name)
            # IT IS IMPORTANT TO KNOW IF IT IS AN ICEPAP MOTOR, SO EXTRA FEATURES CAN BE PROVIDED
            # PENDING.
            self.has_limits = hasattr(self.motor_dev, 'Limit_Switches')
            self.has_encoder = hasattr(self.motor_dev, 'Encoder')
        except Exception as e:
            taurus.warning('Exception Creating Motor Device %s', str(e))

    def moveMotor(self, pos):
        #self.motor_dev['position'] = pos
        # Make use of Taurus operations (being logged)
        self.motor_dev.getAttribute('Position').write(pos)

    def moveInc(self, inc):
        self.moveMotor(self.motor_dev['position'].value + inc)

    @Qt.pyqtSlot()
    def jogNeg(self):
        neg_limit = -((self.maxint_in_32_bits // 2) - 1)
        # THERE IS A BUG IN THE ICEPAP THAT DOES NOT ALLOW MOVE ABSOLUTE FURTHER THAN 32 BIT
        # SO IF THERE ARE STEPS PER UNIT, max_int HAS TO BE REDUCED
        if hasattr(self.motor_dev, 'step_per_unit'):
            neg_limit = neg_limit / self.motor_dev['step_per_unit'].value
        try:
            min_value = self.motor_dev.getAttribute(
                'Position').getConfig().getValueObj().min_value
            neg_limit = float(min_value)
        except Exception:
            pass
        self.moveMotor(neg_limit)

    @Qt.pyqtSlot()
    def jogPos(self):
        pos_limit = (self.maxint_in_32_bits // 2) - 1
        # THERE IS A BUG IN THE ICEPAP THAT DOES NOT ALLOW MOVE ABSOLUTE FURTHER THAN 32 BIT
        # SO IF THERE ARE STEPS PER UNIT, max_int HAS TO BE REDUCED
        if hasattr(self.motor_dev, 'step_per_unit'):
            pos_limit = pos_limit / self.motor_dev['step_per_unit'].value
        try:
            max_value = self.motor_dev.getAttribute(
                'Position').getConfig().getValueObj().max_value
            pos_limit = float(max_value)
        except Exception:
            pass
        self.moveMotor(pos_limit)

    @Qt.pyqtSlot()
    def goHome(self):
        pass

    @Qt.pyqtSlot()
    def abort(self):
        self.motor_dev.abort()


class LabelWidgetDragsDeviceAndAttribute(DefaultLabelWidget):
    """ Offer richer mime data with taurus-device, taurus-attribute, and plain-text. """

    def mouseMoveEvent(self, event):
        model = self.taurusValueBuddy().getModelName().encode('utf-8')
        mimeData = Qt.QMimeData()
        mimeData.setText(self.text())
        attr_name = model
        dev_name = model.rpartition(b'/')[0]
        mimeData.setData(TAURUS_DEV_MIME_TYPE, dev_name)
        mimeData.setData(TAURUS_ATTR_MIME_TYPE, attr_name)

        drag = Qt.QDrag(self)
        drag.setMimeData(mimeData)
        drag.setHotSpot(event.pos() - self.rect().topLeft())
        drag.exec_(Qt.Qt.CopyAction, Qt.Qt.CopyAction)


class PoolMotorConfigurationForm(TaurusAttrForm):

    def __init__(self, parent=None, designMode=False):
        TaurusAttrForm.__init__(self, parent, designMode)
        self._form.setWithButtons(False)

    def getMotorControllerType(self):
        modelObj = self.getModelObj()
        modelNormalName = modelObj.getNormalName()
        poolDsId = modelObj.getDeviceProxy().info().server_id
        db = taurus.Database()
        pool_devices = tuple(db.get_device_class_list(poolDsId).value_string)
        pool_dev_name = pool_devices[pool_devices.index('Pool') - 1]
        pool = taurus.Device(pool_dev_name)
        poolMotorInfos = pool["MotorList"].value
        for motorInfo in poolMotorInfos:
            # BE CAREFUL, THIS ONLY WORKS IF NOBODY CHANGES THE DEVICE NAME OF A MOTOR!!!
            # ALSO THERE COULD BE A CASE PROBLEM, BETTER DO COMPARISONS WITH .lower()
            # to better understand following actions
            # this is an example of one motor info record
            #'dummymotor10 (motor/dummymotorctrl/10) (dummymotorctrl/10) Motor',
            motorInfos = motorInfo.split()
            if modelNormalName.lower() == motorInfos[1][1:-1].lower():
                controllerName = motorInfos[2][1:-1].split("/")[0]

        poolControllerInfos = pool["ControllerList"].value
        for controllerInfo in poolControllerInfos:
            # to better understand following actions
            # this is an example of one controller info record
            #'dummymotorctrl (DummyMotorController.DummyMotorController/dummymotorctrl) - Motor Python ctrl (DummyMotorController.py)'
            controllerInfos = controllerInfo.split()
            if controllerName.lower() == controllerInfos[0].lower():
                controllerType = controllerInfos[1][1:-1].split("/")[0]
        return controllerType

    def getDisplayAttributes(self, controllerType):
        attributes = ['position',
                      'state',
                      'status',
                      'velocity',
                      'acceleration',
                      'base_rate',
                      'step_per_unit',
                      'dialposition',
                      'sign',
                      'offset',
                      'backlash']

        if controllerType == "IcePAPCtrl.IcepapController":
            attributes.insert(1, "encoder")
            attributes.extend(['frequency',
                               'poweron',
                               'closedloop',
                               'useencodersource',
                               'encodersource',
                               'encodersourceformula',
                               'statusstopcode',
                               'statusdisable',
                               'statusready',
                               'statuslim-',
                               'statuslim+',
                               'statushome'])

        elif controllerType == "PmacCtrl.PmacController":
            attributes.extend(["motoractivated",
                               "negativeendlimitset",
                               "positiveendlimitset",
                               "handwheelenabled",
                               "phasedmotor",
                               "openloopmode",
                               "runningdefine-timemove",
                               "integrationmode",
                               "dwellinprogress",
                               "datablockerror",
                               "desiredvelocityzero",
                               "abortdeceleration",
                               "blockrequest",
                               "homesearchinprogress",
                               "assignedtocoordinatesystem",
                               "coordinatesystem",
                               "amplifierenabled",
                               "stoppedonpositionlimit",
                               "homecomplete",
                               "phasingsearcherror",
                               "triggermove",
                               "integratedfatalfollowingerror",
                               "i2t_amplifierfaulterror",
                               "backlashdirectionflag",
                               "amplifierfaulterror",
                               "fatalfollowingerror",
                               "warningfollowingerror",
                               "inposition",
                               "motionprogramrunning"])

        elif controllerType == "TurboPmacCtrl.TurboPmacController":
            attributes.extend(["motoractivated",
                               "negativeendlimitset",
                               "positiveendlimitset",
                               "extendedservoalgorithmenabled"
                               "amplifierenabled",
                               "openloopmode",
                               "movetimeractive",
                               "integrationmode",
                               "dwellinprogress",
                               "datablockerror",
                               "desiredvelocityzero",
                               "abortdeceleration",
                               "blockrequest",
                               "homesearchinprogress",
                               "user-writtenphaseenable",
                               "user-writtenservoenable",
                               "alternatesource/destination",
                               "phasedmotor",
                               "followingoffsetmode",
                               "followingenabled",
                               "errortriger",
                               "softwarepositioncapture",
                               "integratorinvelocityloop",
                               "alternatecommand-outputmode",
                               "coordinatesystem",
                               "coordinatedefinition",
                               "assignedtocoordinatesystem",
                               "foregroundinposition",
                               "stoppedondesiredpositionlimit",
                               "stoppedonpositionlimit",
                               "homecomplete",
                               "phasing_search/read_active",
                               "triggermove",
                               "integratedfatalfollowingerror",
                               "i2t_amplifierfaulterror",
                               "backlashdirectionflag",
                               "amplifierfaulterror",
                               "fatalfollowingerror",
                               "warningfollowingerror",
                               "inposition"])
        return attributes

    def setModel(self, modelName):
        TaurusAttrForm.setModel(self, modelName)
        controllerType = self.getMotorControllerType()
        attributes = self.getDisplayAttributes(controllerType)
        #self.setViewFilters([lambda a: a.name.lower() in attributes])
        self.setSortKey(lambda att: attributes.index(
            att.name.lower()) if att.name.lower() in attributes else 1)


##########################################################################
# NEW APPROACH TO OPERATE POOL MOTORS FROM A TAURUS FORM INHERITTING DIRECTLY FROM TaurusVALUE #
# AND USING PARTICULAR CLASSES THAT KNOW THEY ARE PART OF A TAURUSVALUE AND CAN INTERACT       #
##########################################################################

class TaurusAttributeListener(Qt.QObject):
    """
    A class that recieves events on tango attribute changes.
    If that is the case it emits a signal with the event's value.
    """

    eventReceivedSignal = Qt.pyqtSignal(compat.PY_OBJECT)

    def __init__(self):
        Qt.QObject.__init__(self)

    def eventReceived(self, evt_src, evt_type, evt_value):
        if evt_type not in [TaurusEventType.Change, TaurusEventType.Periodic]:
            return
        try:
            value = evt_value.rvalue.magnitude
        except AttributeError:
            # spectrum/images or str attribute values are not Quantities
            value = evt_value.rvalue
        self.eventReceivedSignal.emit(value)


##################################################
#                  LABEL WIDGET                  #
##################################################
class PoolMotorTVLabelWidget(TaurusWidget):
    '''
    @TODO tooltip should be extended with status info
    @TODO context menu should be the lbl_alias extended
    @TODO default tooltip extended with the complete (multiline) status
    @TODO rightclick popup menu with actions: (1) switch user/expert view, (2) Config -all attributes-, (3) change motor
    For the (3), a drop event should accept if it is a device, and add it to the 'change-motor' list and select
    @TODO on the 'expert' row, it could be an ENABLE section with a button to set PowerOn to True/False
    '''

    layoutAlignment = Qt.Qt.AlignTop

    def __init__(self, parent=None, designMode=False):
        TaurusWidget.__init__(self, parent, designMode)
        self.setLayout(Qt.QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        self.lbl_alias = DefaultLabelWidget(parent, designMode)
        self.lbl_alias.setBgRole('none')
        self.layout().addWidget(self.lbl_alias)

        self.btn_poweron = Qt.QPushButton()
        self.btn_poweron.setText('Set ON')
        self.layout().addWidget(self.btn_poweron)

        # Align everything on top
        self.layout().addItem(Qt.QSpacerItem(
            1, 1, Qt.QSizePolicy.Minimum, Qt.QSizePolicy.Expanding))

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

    def setExpertView(self, expertView):
        btn_poweron_visible = expertView \
                              and self.taurusValueBuddy().hasPowerOn()
        self.btn_poweron.setVisible(btn_poweron_visible)

    @Qt.pyqtSlot()
    @ProtectTaurusMessageBox(
        msg='An error occurred trying to write PowerOn Attribute.')
    def setPowerOn(self):
        motor_dev = self.taurusValueBuddy().motor_dev
        if motor_dev is not None:
            poweron = (self.btn_poweron.text() == 'Set ON')
            motor_dev.getAttribute('PowerOn').write(poweron)

    def setModel(self, model):
        # Handle User/Expert view
        try:
            self.taurusValueBuddy().expertViewChanged.disconnect(
                self.setExpertView)
        except TypeError:
            pass
        try:
            self.btn_poweron.clicked.disconnect(self.setPowerOn)
        except TypeError:
            pass
        if model in (None, ''):
            self.lbl_alias.setModel(model)
            TaurusWidget.setModel(self, model)
            return
        self.lbl_alias.taurusValueBuddy = self.taurusValueBuddy
        self.lbl_alias.setModel(model)
        TaurusWidget.setModel(self, model + '/Status')
        self.taurusValueBuddy().expertViewChanged.connect(
            self.setExpertView)
        # Handle Power ON/OFF
        self.btn_poweron.clicked.connect(self.setPowerOn)
        self.setExpertView(self.taurusValueBuddy()._expertView)

    def calculateExtendedTooltip(self, cache=False):
        default_label_widget_tooltip = DefaultLabelWidget.getFormatedToolTip(
            self.lbl_alias, cache)
        status_info = ''
        motor_dev = self.taurusValueBuddy().motor_dev
        if motor_dev is not None:
            status = motor_dev.getAttribute('Status').read().rvalue
            # MAKE IT LOOK LIKE THE STANDARD TABLE FOR TAURUS TOOLTIPS
            status_lines = status.split('\n')
            status_info = '<TABLE width="500" border="0" cellpadding="1" cellspacing="0"><TR><TD WIDTH="80" ALIGN="RIGHT" VALIGN="MIDDLE"><B>Status:</B></TD><TD>' + \
                status_lines[0] + '</TD></TR>'
            for status_extra_line in status_lines[1:]:
                status_info += '<TR><TD></TD><TD>' + status_extra_line + '</TD></TR>'
            status_info += '</TABLE>'
        return default_label_widget_tooltip + status_info

    def contextMenuEvent(self, event):
        # Overwrite the default taurus label behaviour
        menu = Qt.QMenu(self)
        action_expert_view = Qt.QAction(self)
        action_expert_view.setText('Expert View')
        action_expert_view.setCheckable(True)
        action_expert_view.setChecked(self.taurusValueBuddy()._expertView)
        menu.addAction(action_expert_view)
        action_expert_view.toggled.connect(
            self.taurusValueBuddy().setExpertView)

        action_tango_attributes = Qt.QAction(self)
        action_tango_attributes.setIcon(
            Qt.QIcon("categories:preferences-system.svg"))
        action_tango_attributes.setText('Tango Attributes')
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
        dev_name = model.getFullName().encode('utf-8')
        attr_name = dev_name + b'/Position'
        mimeData.setData(TAURUS_DEV_MIME_TYPE, dev_name)
        mimeData.setData(TAURUS_ATTR_MIME_TYPE, attr_name)

        drag = Qt.QDrag(self)
        drag.setMimeData(mimeData)
        drag.setHotSpot(event.pos() - self.rect().topLeft())
        drag.exec_(Qt.Qt.CopyAction, Qt.Qt.CopyAction)

##################################################
#                   READ WIDGET                  #
##################################################


class PoolMotorTVReadWidget(TaurusWidget):
    '''
    @TODO on the 'expert' row, there should be an Indexer/Encoder radiobuttongroup to show units from raw dial/indx/enc
    @TODO TaurusLCD may be used but, now it does not display the sign, and color is WHITE...
    '''

    layoutAlignment = Qt.Qt.AlignTop

    def __init__(self, parent=None, designMode=False):
        TaurusWidget.__init__(self, parent, designMode)

        self.setLayout(Qt.QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        limits_layout = Qt.QHBoxLayout()
        limits_layout.setContentsMargins(0, 0, 0, 0)
        limits_layout.setSpacing(0)

        self.lim_neg = Qt.QLabel()
        self.prepare_limit(self.lim_neg)
        self._config_limit(Limit.Negative,
                           hw_lim=LimitInfo(),
                           sw_lim=LimitInfo())
        limits_layout.addWidget(self.lim_neg)

        self.lim_pos = Qt.QLabel()
        self.prepare_limit(self.lim_pos)
        self._config_limit(Limit.Positive,
                           hw_lim=LimitInfo(),
                           sw_lim=LimitInfo())
        limits_layout.addWidget(self.lim_pos)

        self.layout().addLayout(limits_layout, 0, 0)

        self.lbl_read = TaurusLabel()
        self.lbl_read.setFgRole('rvalue.magnitude')
        self.lbl_read.setBgRole('quality')
        self.lbl_read.setSizePolicy(Qt.QSizePolicy(
            Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Fixed))
        self.layout().addWidget(self.lbl_read, 0, 1)

        # WITH A COMPACT VIEW, BETTER TO BE ABLE TO STOP!
        self.btn_stop = Qt.QPushButton()
        self.btn_stop.setToolTip('Stops the motor')
        self.prepare_button(self.btn_stop)
        self.btn_stop.setIcon(Qt.QIcon("actions:media_playback_stop.svg"))
        self.layout().addWidget(self.btn_stop, 0, 2)

        self.btn_stop.clicked.connect(self.abort)

        # WITH COMPACT VIEW, WE NEED TO FORWARD DOUBLE CLICK EVENT
        self.lbl_read.installEventFilter(self)

        # @TODO right now, no options here...
        #self.cb_expertRead = Qt.QComboBox()
        # self.cb_expertRead.addItems(['Enc'])
        #self.layout().addWidget(self.cb_expertRead, 1, 0)

        self.lbl_enc = None
        self.lbl_enc_read = None

        # Align everything on top
        self.layout().addItem(Qt.QSpacerItem(
            1, 1, Qt.QSizePolicy.Minimum, Qt.QSizePolicy.Expanding), 2, 0, 1, 2)

        # IN ORDER TO BEHAVE AS EXPECTED REGARDING THE 'COMPACT VIEW' FEATURE
        # WE NEED TO SET THE 'EXPERTVIEW' WITHOUT ACCESSING THE taurusValueBuddy WHICH IS STILL NOT LINKED
        # SO WE ASSUME 'expertview is FALSE' AND WE HAVE TO AVOID self.setExpertView :-(
        # WOULD BE NICE THAT THE taurusValueBuddy COULD EMIT THE PROPER
        # SIGNAL...

    def eventFilter(self, obj, event):
        if event.type() == Qt.QEvent.MouseButtonDblClick:
            if isinstance(self.parent(), TaurusReadWriteSwitcher):
                self.parent().enterEdit()
                return True
        try:
            if obj is self.lbl_read:
                return self.lbl_read.eventFilter(obj, event)
        except AttributeError:
            # self.lbl_read may not exist now
            pass
        return True

    @Qt.pyqtSlot()
    @ProtectTaurusMessageBox(msg='An error occurred trying to abort the motion.')
    def abort(self):
        motor_dev = self.taurusValueBuddy().motor_dev
        if motor_dev is not None:
            motor_dev.abort()

    def setExpertView(self, expertView):
        if self.lbl_enc_read is None:
            return
        self.lbl_enc.setVisible(False)
        self.lbl_enc_read.setVisible(False)
        if expertView and self.taurusValueBuddy().motor_dev is not None:
            encoder = self.taurusValueBuddy().hasEncoder()
            self.lbl_enc.setVisible(encoder)
            self.lbl_enc_read.setVisible(encoder)

    def prepare_button(self, btn):
        btn_policy = Qt.QSizePolicy(Qt.QSizePolicy.Fixed, Qt.QSizePolicy.Fixed)
        btn_policy.setHorizontalStretch(0)
        btn_policy.setVerticalStretch(0)
        btn.setSizePolicy(btn_policy)
        btn.setMinimumSize(25, 25)
        btn.setMaximumSize(25, 25)
        btn.setText('')

    def prepare_limit(self, lbl):
        lbl_policy = Qt.QSizePolicy(Qt.QSizePolicy.Fixed, Qt.QSizePolicy.Fixed)
        lbl_policy.setHorizontalStretch(0)
        lbl_policy.setVerticalStretch(0)
        lbl.setSizePolicy(lbl_policy)
        lbl.setText('')

    def _config_limit(self, limit, hw_lim, sw_lim):
        """Configure sub-widgets according to limit information

        :param limit: which limit (negative or positive)
        :type limit: `Limit`
        :param hw_lim: hardware limit information
        :type hw_lim: `LimitInfo`
        :param hw_lim: software limit information
        :type hw_lim: `LimitInfo`
        """
        if limit == Limit.Negative:
            widget = self.lim_neg
            icon = Qt.QIcon("designer:minus.png")
        elif limit == Limit.Positive:
            widget = self.lim_pos
            icon = Qt.QIcon("designer:plus.png")
        else:
            raise ValueError("{} wrong limit".format(limit))
        widget.setStyleSheet('')
        if hw_lim.exist or sw_lim.exist:
            pixmap = Qt.QPixmap(icon.pixmap(Qt.QSize(32, 32),
                                            Qt.QIcon.Active))
            if hw_lim.active or sw_lim.active:
                colour = DEVICE_STATE_PALETTE.qtStyleSheet(
                    PyTango.DevState.ALARM)
                widget.setStyleSheet(colour)
        else:
            pixmap = Qt.QPixmap(icon.pixmap(Qt.QSize(32, 32),
                                            Qt.QIcon.Disabled))
        tool_tip = hw_lim.status + " " + sw_lim.status
        widget.setToolTip(tool_tip)
        widget.setPixmap(pixmap)

    def _create_encoder(self):
        if self.taurusValueBuddy().hasEncoder() and self.lbl_enc_read is None:
            self.lbl_enc = Qt.QLabel('Encoder')
            self.layout().addWidget(self.lbl_enc, 1, 0)

            self.lbl_enc_read = TaurusLabel()
            self.lbl_enc_read.setBgRole('none')
            self.lbl_enc_read.setSizePolicy(Qt.QSizePolicy(
                Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Fixed))
            self.layout().addWidget(self.lbl_enc_read, 1, 1)

            # Align everything on top
            self.layout().addItem(Qt.QSpacerItem(
                1, 1, Qt.QSizePolicy.Minimum,
                Qt.QSizePolicy.Expanding), 2, 0, 1, 2)

            self.lbl_enc.setVisible(False)
            self.lbl_enc_read.setVisible(False)

    def setModel(self, model):
        if hasattr(self, 'taurusValueBuddy'):
            try:
                self.taurusValueBuddy().expertViewChanged.disconnect(
                    self.setExpertView)
            except TypeError:
                pass
        if model in (None, ''):
            TaurusWidget.setModel(self, model)
            self.lbl_read.setModel(model)
            if self.lbl_enc_read is not None:
                self.lbl_enc_read.setModel(model)
            return
        TaurusWidget.setModel(self, model + '/Position')
        self.lbl_read.setModel(model + '/Position')
        if (self.taurusValueBuddy().hasEncoder()
                and self.lbl_enc_read is None):
            self._create_encoder()
            self.lbl_enc_read.setModel(model + '/Encoder')
        # Handle User/Expert view
        self.setExpertView(self.taurusValueBuddy()._expertView)
        self.taurusValueBuddy().expertViewChanged.connect(
            self.setExpertView)

##################################################
#                  WRITE WIDGET                  #
##################################################

class PoolMotorTVWriteWidget(TaurusWidget):

    layoutAlignment = Qt.Qt.AlignTop

    applied = Qt.pyqtSignal()

    def __init__(self, parent=None, designMode=False):
        TaurusWidget.__init__(self, parent, designMode)

        # ------------------------------------------------------------
        # Workaround for Taurus3 support
        if int(taurus.Release.version.split('.')[0]) < 4:
            from taurus.qt.qtgui.base.taurusbase import baseOldSignal
            self.applied = baseOldSignal('applied', self)
        # ------------------------------------------------------------

        self.setLayout(Qt.QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        self.le_write_absolute = TaurusValueLineEdit()
        self.layout().addWidget(self.le_write_absolute, 0, 0)

        self.qw_write_relative = Qt.QWidget()
        self.qw_write_relative.setLayout(Qt.QHBoxLayout())
        self.qw_write_relative.layout().setContentsMargins(0, 0, 0, 0)
        self.qw_write_relative.layout().setSpacing(0)

        self.cb_step = Qt.QComboBox()
        self.cb_step.setSizePolicy(Qt.QSizePolicy(
            Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Fixed))
        self.cb_step.setEditable(True)
        self.cb_step.lineEdit().setValidator(Qt.QDoubleValidator(self))
        self.cb_step.lineEdit().setAlignment(Qt.Qt.AlignRight)
        self.cb_step.addItem('1')
        self.qw_write_relative.layout().addWidget(self.cb_step)

        self.btn_step_down = Qt.QPushButton()
        self.btn_step_down.setToolTip('Decrements motor position')
        self.prepare_button(self.btn_step_down)
        self.btn_step_down.setIcon(
            Qt.QIcon("actions:media_playback_backward.svg"))
        self.qw_write_relative.layout().addWidget(self.btn_step_down)

        self.btn_step_up = Qt.QPushButton()
        self.btn_step_up.setToolTip('Increments motor position')
        self.prepare_button(self.btn_step_up)
        self.btn_step_up.setIcon(Qt.QIcon("actions:media_playback_start.svg"))
        self.qw_write_relative.layout().addWidget(self.btn_step_up)

        self.layout().addWidget(self.qw_write_relative, 0, 0)

        self.cbAbsoluteRelative = Qt.QComboBox()
        self.cbAbsoluteRelative.currentIndexChanged['QString'].connect(
            self.cbAbsoluteRelativeChanged)
        self.cbAbsoluteRelative.addItems(['Abs', 'Rel'])
        self.layout().addWidget(self.cbAbsoluteRelative, 0, 1)
        self.registerConfigProperty(
            self.cbAbsoluteRelative.currentIndex,
            self.cbAbsoluteRelative.setCurrentIndex, 'AbsRelIndex')
        # WITH THE COMPACCT VIEW FEATURE, BETTER TO HAVE IT IN THE READ WIDGET
        # WOULD BE BETTER AS AN 'EXTRA WIDGET' (SOME DAY...)
        #self.btn_stop = Qt.QPushButton()
        #self.btn_stop.setToolTip('Stops the motor')
        # self.prepare_button(self.btn_stop)
        # self.btn_stop.setIcon(getIcon(':/actions/media_playback_stop.svg'))
        #self.layout().addWidget(self.btn_stop, 0, 2)

        btns_layout = Qt.QHBoxLayout()
        btns_layout.setContentsMargins(0, 0, 0, 0)
        btns_layout.setSpacing(0)

        btns_layout.addItem(Qt.QSpacerItem(
            1, 1, Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Minimum))

        self.btn_to_neg = Qt.QPushButton()
        self.btn_to_neg.setToolTip(
            'Moves the motor towards the Negative Software Limit')
        self.prepare_button(self.btn_to_neg)
        self.btn_to_neg.setIcon(Qt.QIcon("actions:media_skip_backward.svg"))
        btns_layout.addWidget(self.btn_to_neg)

        self.btn_to_neg_press = Qt.QPushButton()
        self.btn_to_neg_press.setToolTip(
            'Moves the motor (while pressed) towards the Negative Software Limit')
        self.prepare_button(self.btn_to_neg_press)
        self.btn_to_neg_press.setIcon(
            Qt.QIcon("actions:media_seek_backward.svg"))
        btns_layout.addWidget(self.btn_to_neg_press)

        self.btn_to_pos_press = Qt.QPushButton()
        self.prepare_button(self.btn_to_pos_press)
        self.btn_to_pos_press.setToolTip(
            'Moves the motor (while pressed) towards the Positive Software Limit')
        self.btn_to_pos_press.setIcon(
            Qt.QIcon("actions:media_seek_forward.svg"))
        btns_layout.addWidget(self.btn_to_pos_press)

        self.btn_to_pos = Qt.QPushButton()
        self.btn_to_pos.setToolTip(
            'Moves the motor towards the Positive Software Limit')
        self.prepare_button(self.btn_to_pos)
        self.btn_to_pos.setIcon(Qt.QIcon("actions:media_skip_forward.svg"))
        btns_layout.addWidget(self.btn_to_pos)

        btns_layout.addItem(Qt.QSpacerItem(
            1, 1, Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Minimum))

        self.layout().addLayout(btns_layout, 1, 0, 1, 3)

        self.btn_step_down.clicked.connect(self.stepDown)
        self.btn_step_up.clicked.connect(self.stepUp)
        # self.btn_stop.clicked.connect(self.abort)
        self.btn_to_neg.clicked.connect(self.goNegative)
        self.btn_to_neg_press.pressed.connect(self.goNegative)
        self.btn_to_neg_press.released.connect(self.abort)
        self.btn_to_pos.clicked.connect(self.goPositive)
        self.btn_to_pos_press.pressed.connect(self.goPositive)
        self.btn_to_pos_press.released.connect(self.abort)

        # Align everything on top
        self.layout().addItem(Qt.QSpacerItem(
            1, 1, Qt.QSizePolicy.Minimum, Qt.QSizePolicy.Expanding), 2, 0, 1, 3)

        # IN ORDER TO BEHAVE AS EXPECTED REGARDING THE 'COMPACT VIEW' FEATURE
        # WE NEED TO SET THE 'EXPERTVIEW' WITHOUT ACCESSING THE taurusValueBuddy WHICH IS STILL NOT LINKED
        # SO WE ASSUME 'expertview is FALSE' AND WE HAVE TO AVOID self.setExpertView :-(
        # WOULD BE NICE THAT THE taurusValueBuddy COULD EMIT THE PROPER
        # SIGNAL...
        self.btn_to_neg.setVisible(False)
        self.btn_to_neg_press.setVisible(False)
        self.btn_to_pos.setVisible(False)
        self.btn_to_pos_press.setVisible(False)

        # IN EXPERT VIEW, WE HAVE TO FORWARD THE ''editingFinished()' SIGNAL
        # FROM TaurusValueLineEdit TO Switcher
        self.le_write_absolute.applied.connect(self.emitEditingFinished)
        self.btn_step_down.clicked.connect(self.emitEditingFinished)
        self.btn_step_up.clicked.connect(self.emitEditingFinished)
        self.btn_to_neg.clicked.connect(self.emitEditingFinished)
        self.btn_to_pos.clicked.connect(self.emitEditingFinished)

        # list of widgets used for edition
        editingWidgets = (self.le_write_absolute, self.cbAbsoluteRelative,
                          self.cb_step, self.btn_step_down,
                          self.btn_step_up, self.btn_to_neg,
                          self.btn_to_pos, self.btn_to_neg_press,
                          self.btn_to_pos_press)

        for w in editingWidgets:
            w.installEventFilter(self)

    def eventFilter(self, obj, event):
        '''reimplemented to intercept events from the subwidgets'''
        try:
            if obj in (self.btn_to_neg_press, self.btn_to_pos_press):
                if event.type() == Qt.QEvent.MouseButtonRelease:
                    self.emitEditingFinished()
        except AttributeError:
            # self.btn_to_neg_press, self.btn_to_pos_press may not exist now
            pass
        # emit editingFinished when focus out to a non-editing widget
        if event.type() == Qt.QEvent.FocusOut:
            focused = Qt.qApp.focusWidget()
            focusInChild = focused in self.findChildren(focused.__class__)
            if not focusInChild:
                self.emitEditingFinished()
        return False

    def cbAbsoluteRelativeChanged(self, abs_rel_option):
        abs_visible = abs_rel_option == 'Abs'
        rel_visible = abs_rel_option == 'Rel'
        if rel_visible:
            self.resetPendingOperations()
        self.le_write_absolute.setVisible(abs_visible)
        self.qw_write_relative.setVisible(rel_visible)

    @Qt.pyqtSlot()
    def stepDown(self):
        self.goRelative(-1)

    @Qt.pyqtSlot()
    def stepUp(self):
        self.goRelative(+1)

    @ProtectTaurusMessageBox(msg='An error occurred trying to move the motor.')
    def goRelative(self, direction):
        motor_dev = self.taurusValueBuddy().motor_dev
        if motor_dev is not None:
            increment = direction * float(self.cb_step.currentText())
            position = float(
                motor_dev.getAttribute('Position').read().rvalue.magnitude)
            target_position = position + increment
            motor_dev.getAttribute('Position').write(target_position)

    @Qt.pyqtSlot()
    @ProtectTaurusMessageBox(msg='An error occurred trying to move the motor.')
    def goNegative(self):
        motor_dev = self.taurusValueBuddy().motor_dev
        if motor_dev is not None:
            min_value = float(motor_dev.getAttribute('Position').min_value)
            motor_dev.getAttribute('Position').write(min_value)

    @Qt.pyqtSlot()
    @ProtectTaurusMessageBox(msg='An error occurred trying to move the motor.')
    def goPositive(self):
        motor_dev = self.taurusValueBuddy().motor_dev
        if motor_dev is not None:
            max_value = float(motor_dev.getAttribute('Position').max_value)
            motor_dev.getAttribute('Position').write(max_value)

    @Qt.pyqtSlot()
    @ProtectTaurusMessageBox(msg='An error occurred trying to abort the motion.')
    def abort(self):
        motor_dev = self.taurusValueBuddy().motor_dev
        if motor_dev is not None:
            motor_dev.abort()

    def prepare_button(self, btn):
        btn_policy = Qt.QSizePolicy(Qt.QSizePolicy.Fixed, Qt.QSizePolicy.Fixed)
        btn_policy.setHorizontalStretch(0)
        btn_policy.setVerticalStretch(0)
        btn.setSizePolicy(btn_policy)
        btn.setMinimumSize(25, 25)
        btn.setMaximumSize(25, 25)
        btn.setText('')

    def setExpertView(self, expertView):
        self.btn_to_neg.setVisible(expertView)
        self.btn_to_neg_press.setVisible(expertView)

        self.btn_to_pos.setVisible(expertView)
        self.btn_to_pos_press.setVisible(expertView)

        if expertView and self.taurusValueBuddy().motor_dev is not None:
            neg_sw_limit_enabled = self.taurusValueBuddy().motor_dev.getAttribute(
                'Position').min_value.lower() != 'not specified'
            self.btn_to_neg.setEnabled(neg_sw_limit_enabled)
            self.btn_to_neg_press.setEnabled(neg_sw_limit_enabled)

            pos_sw_limit_enabled = self.taurusValueBuddy().motor_dev.getAttribute(
                'Position').max_value.lower() != 'not specified'
            self.btn_to_pos.setEnabled(pos_sw_limit_enabled)
            self.btn_to_pos_press.setEnabled(pos_sw_limit_enabled)

    def setModel(self, model):
        if hasattr(self, 'taurusValueBuddy'):
            try:
                self.taurusValueBuddy().expertViewChanged.disconnect(
                    self.setExpertView)
            except TypeError:
                pass
        if model in (None, ''):
            TaurusWidget.setModel(self, model)
            self.le_write_absolute.setModel(model)
            return
        TaurusWidget.setModel(self, model + '/Position')
        self.le_write_absolute.setModel(model + '/Position#wvalue.magnitude')

        # Handle User/Expert View
        self.setExpertView(self.taurusValueBuddy()._expertView)
        self.taurusValueBuddy().expertViewChanged.connect(
            self.setExpertView)

    def keyPressEvent(self, key_event):
        if key_event.key() == Qt.Qt.Key_Escape:
            self.abort()
            key_event.accept()
        TaurusWidget.keyPressEvent(self, key_event)

    @Qt.pyqtSlot()
    def emitEditingFinished(self):
        self.applied.emit()

    def _config_limit(self, limit, hw_lim, sw_lim):
        """Configure sub-widgets according to limit information

        :param limit: which limit (negative or positive)
        :type limit: `Limit`
        :param hw_lim: hardware limit information
        :type hw_lim: `LimitInfo`
        :param hw_lim: software limit information
        :type hw_lim: `LimitInfo`
        """
        if limit == Limit.Negative:
            step_widget = self.btn_step_down
            to_widget = self.btn_to_neg
            to_press_widget = self.btn_to_neg_press
        elif limit == Limit.Positive:
            step_widget = self.btn_step_up
            to_widget = self.btn_to_pos
            to_press_widget = self.btn_to_pos_press
        else:
            raise ValueError("{} wrong limit".format(limit))
        active = hw_lim.active or sw_lim.active
        style_sheet = ""
        if active:
            style_sheet = 'QPushButton{{{}}}'.format(
                DEVICE_STATE_PALETTE.qtStyleSheet(PyTango.DevState.ALARM))
        step_widget.setEnabled(not active)
        allow_to = not active and sw_lim.exist
        to_widget.setEnabled(allow_to)
        to_press_widget.setEnabled(allow_to)
        step_widget.setStyleSheet(style_sheet)


##################################################
#                  UNITS WIDGET                  #
##################################################
class PoolMotorTVUnitsWidget(DefaultUnitsWidget):

    layoutAlignment = Qt.Qt.AlignTop

    def __init__(self, parent=None, designMode=False):
        DefaultUnitsWidget.__init__(self, parent, designMode)

    def setModel(self, model):
        if model in (None, ''):
            DefaultUnitsWidget.setModel(self, model)
            return
        DefaultUnitsWidget.setModel(self, model + '/Position')

##################################################
#                TV MOTOR WIDGET                 #
##################################################


class PoolMotorTV(TaurusValue):
    ''' A widget that displays and controls a pool Motor device.  It
    behaves as a TaurusValue.
    @TODO the view mode should be stored in the configuration
    @TODO the motor list should be stored in the configuration
    @TODO the selected radiobuttons (dial/indx/enc) and (abs/rel) should be stored in configuration
    @TODO it would be nice if the neg/pos limits could react also when software limits are 'active'
    @TODO expert view for read widget should include signals (indexer/encoder/inpos)...
    '''

    expertViewChanged = Qt.pyqtSignal(bool)

    def __init__(self, parent=None, designMode=False):
        TaurusValue.__init__(self, parent=parent, designMode=designMode)
        self.setLabelWidgetClass(PoolMotorTVLabelWidget)
        self.setReadWidgetClass(PoolMotorTVReadWidget)
        self.setWriteWidgetClass(PoolMotorTVWriteWidget)
        self.setUnitsWidgetClass(PoolMotorTVUnitsWidget)
        self.motor_dev = None
        self._expertView = False
        self.registerConfigProperty(
            self.getExpertView, self.setExpertView, 'ExpertView')
        self.limits_listener = None
        self.poweron_listener = None
        self.status_listener = None
        self.position_listener = None
        self.setExpertView(False)

    def setExpertView(self, expertView):
        self._expertView = expertView
        self.expertViewChanged.emit(expertView)

    def getExpertView(self):
        return self._expertView

    def minimumHeight(self):
        return None  # @todo: UGLY HACK to avoid subwidgets being forced to minimumheight=20

    def setModel(self, model):
        TaurusValue.setModel(self, model)

        # disconnect signals
        try:
            if self.limits_listener is not None:
                self.limits_listener.eventReceivedSignal.disconnect(
                    self.updateLimits)
        except TypeError:
            pass

        try:
            if self.poweron_listener is not None:
                self.poweron_listener.eventReceivedSignal.disconnect(
                    self.updatePowerOn)
        except TypeError:
            pass

        try:
            if self.status_listener is not None:
                self.status_listener.eventReceivedSignal.disconnect(
                    self.updateStatus)
        except TypeError:
            pass

        try:
            if self.position_listener is not None:
                self.position_listener.eventReceivedSignal.disconnect(
                    self.updatePosition)
        except TypeError:
            pass

        try:
            # remove listeners
            if self.motor_dev is not None:
                if self.hasHwLimits():
                    self.motor_dev.getAttribute(
                        'Limit_Switches').removeListener(self.limits_listener)
                if self.hasPowerOn():
                    self.motor_dev.getAttribute(
                        'PowerOn').removeListener(self.poweron_listener)
                self.motor_dev.getAttribute(
                    'Status').removeListener(self.status_listener)
                self.motor_dev.getAttribute(
                    'Position').removeListener(self.position_listener)

            if model == '' or model is None:
                self.motor_dev = None
                return
            self.motor_dev = taurus.Device(model)
            # CONFIGURE A LISTENER IN ORDER TO UPDATE LIMIT SWITCHES STATES
            self.limits_listener = TaurusAttributeListener()
            if self.hasHwLimits():
                self.limits_listener.eventReceivedSignal.connect(
                    self.updateLimits)
                self._limit_switches = self.motor_dev.getAttribute(
                    'Limit_Switches')
                self._limit_switches.addListener(self.limits_listener)

            # CONFIGURE AN EVENT RECEIVER IN ORDER TO PROVIDE POWERON <-
            # True/False EXPERT OPERATION
            self.poweron_listener = TaurusAttributeListener()
            if self.hasPowerOn():
                self.poweron_listener.eventReceivedSignal.connect(
                    self.updatePowerOn)
                self._poweron = self.motor_dev.getAttribute('PowerOn')
                self._poweron.addListener(self.poweron_listener)

            # CONFIGURE AN EVENT RECEIVER IN ORDER TO UPDATED STATUS TOOLTIP
            self.status_listener = TaurusAttributeListener()
            self.status_listener.eventReceivedSignal.connect(
                self.updateStatus)
            self._status = self.motor_dev.getAttribute('Status')
            self._status.addListener(self.status_listener)

            # CONFIGURE AN EVENT RECEIVER IN ORDER TO ACTIVATE LIMIT BUTTONS ON
            # SOFTWARE LIMITS
            self.position_listener = TaurusAttributeListener()
            self.position_listener.eventReceivedSignal.connect(
                self.updatePosition)
            self._position = self.motor_dev.getAttribute('Position')
            self._position.addListener(self.position_listener)
            self.motor_dev.getAttribute('Position').enablePolling(force=True)

            self.setExpertView(self._expertView)
        except Exception as e:
            self.warning("Exception caught while setting model: %s", repr(e))
            self.motor_dev = None
            return

    def hasPowerOn(self):
        try:
            return hasattr(self.motor_dev, 'PowerOn')
        except:
            return False

    def hasHwLimits(self):
        try:
            return hasattr(self.motor_dev, 'Limit_Switches')
        except:
            return False

    def updateLimits(self, limits, position=None):
        if isinstance(limits, dict):
            limits = limits["limits"]

        pos_hw_lim = eval_hw_limit(Limit.Positive, limits[Limit.Positive])
        neg_hw_lim = eval_hw_limit(Limit.Negative, limits[Limit.Negative])
        position_attr = self.motor_dev.getAttribute('Position')
        pos_sw_lim = eval_sw_limit(Limit.Positive, position_attr)
        neg_sw_lim = eval_sw_limit(Limit.Negative, position_attr)

        read_widget = self.readWidget(followCompact=True)
        read_widget._config_limit(Limit.Positive, pos_hw_lim, pos_sw_lim)
        read_widget._config_limit(Limit.Negative, neg_hw_lim, neg_sw_lim)

        write_widget = self.writeWidget(followCompact=True)
        write_widget._config_limit(Limit.Positive, pos_hw_lim, pos_sw_lim)
        write_widget._config_limit(Limit.Negative, neg_hw_lim, neg_sw_lim)

    def updatePowerOn(self, poweron='__no_argument__'):
        if poweron == '__no_argument__':
            msg = 'updatePowerOn called without args (bug in old PyQt). Ignored'
            self.debug(msg)
            return
        btn_text = 'Set ON'
        if poweron:
            btn_text = 'Set OFF'
        self.labelWidget().btn_poweron.setText(btn_text)

    def updateStatus(self, status):
        # SHOULD THERE BE A BETTER METHOD FOR THIS UPDATE?
        # IF THIS IS NOT DONE, THE TOOLTIP IS NOT CALCULATED EVERY TIME
        # TaurusLabel.updateStyle DIDN'T WORK, SO I HAD TO GO DEEPER TO THE CONTROLLER...
        # self.labelWidget().lbl_alias.updateStyle()
        self.labelWidget().lbl_alias.controllerUpdate()

    def updatePosition(self, position='__no_argument__'):
        if position == '__no_argument__':
            msg = 'updatePowerOn called without args (bug in old PyQt). Ignored'
            self.debug(msg)
            return
        # we do not need the position for nothing...
        # we just want to check if any software limit is 'active'
        # and updateLimits takes care of it
        if self.motor_dev is not None:
            limit_switches = [None, None, None]
            if self.hasHwLimits():
                limit_switches = self.motor_dev.getAttribute(
                    'Limit_switches').read().rvalue
                # print "update limits", limit_switches
            self.updateLimits(limit_switches, position=position)

    def hasEncoder(self):
        try:
            return hasattr(self.motor_dev, 'Encoder')
        except:
            return False

    def showTangoAttributes(self):
        model = self.getModel()
        taurus_attr_form = TaurusAttrForm()
        taurus_attr_form.setMinimumSize(Qt.QSize(555, 800))
        taurus_attr_form.setModel(model)
        taurus_attr_form.setWindowTitle(
            '%s Tango Attributes' % taurus.Factory().getDevice(model).getSimpleName())
        taurus_attr_form.show()

    # def showEvent(self, event):
    ###     TaurusValue.showEvent(self, event)
    # if self.motor_dev is not None:
    # self.motor_dev.getAttribute('Position').enablePolling(force=True)
    ###
    # def hideEvent(self, event):
    ###     TaurusValue.hideEvent(self, event)
    # if self.motor_dev is not None:
    # self.motor_dev.getAttribute('Position').disablePolling()

###################################################
# A SIMPLER WIDGET THAT MAY BE USED OUTSIDE FORMS #
###################################################


class PoolMotor(TaurusFrame):
    ''' A widget that displays and controls a pool Motor device.
    '''

    def __init__(self, parent=None, designMode=False):
        TaurusFrame.__init__(self, parent, designMode)

        self.setLayout(Qt.QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        self.setFrameShape(Qt.QFrame.Box)

        self.pool_motor_tv = PoolMotorTV(self)

    def setModel(self, model):
        self.pool_motor_tv.setModel(model)
        try:
            self.motor_dev = taurus.Device(model)
        except:
            return


def main():

    import sys
    import taurus.qt.qtgui.application
    import taurus.core.util.argparse
    from taurus.qt.qtgui.panel import TaurusForm
    parser = taurus.core.util.argparse.get_taurus_parser()
    parser.usage = "%prog [options] [<motor1> [<motor2>] ...]"

    app = taurus.qt.qtgui.application.TaurusApplication(cmd_line_parser=parser)
    args = app.get_command_line_args()

    #models = ['tango://controls02:10000/motor/gcipap10ctrl/8']
    models = ['motor/motctrl13/3']

    if len(args) > 0:
        models = args

    w = Qt.QWidget()
    w.setLayout(Qt.QVBoxLayout())

    tests = []
    # tests.append(1)
    tests.append(2)
    # tests.append(3)
    # tests.append(4)

    # 2) Test PoolMotorTV motor widget
    form_tv = TaurusForm()
    form_tv.setModifiableByUser(True)
    tv_widget_class = 'sardana.taurus.qt.qtgui.extra_pool.PoolMotorTV'
    tv_tgclass_map = {'SimuMotor': (tv_widget_class, (), {}),
                      'Motor': (tv_widget_class, (), {}),
                      'PseudoMotor': (tv_widget_class, (), {})}
    form_tv.setCustomWidgetMap(tv_tgclass_map)

    if 2 in tests:
        form_tv.setModel(models)
        w.layout().addWidget(form_tv)
        form_tv.setCompact(True)

    # 3) Test Stand-Alone PoolMotor widget
    # New approach would be to let PoolMotorTV live outside a TaurusForm.... but inside a GridLayout
    # Carlos already said this is not a good approach but...
    if 3 in tests:
        for motor in models:
            motor_widget = PoolMotor()
            motor_widget.setModel(motor)
            w.layout().addWidget(motor_widget)

    w.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
