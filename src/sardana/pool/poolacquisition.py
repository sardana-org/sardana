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

"""This module is part of the Python Pool library. It defines the class for an
acquisition"""

__all__ = ["get_acq_ctrls", "AcquisitionState", "AcquisitionMap",
           "PoolCTAcquisition", "Pool0DAcquisition", "PoolIORAcquisition",
           "PoolAcquisitionHardware", "PoolAcquisitionSoftware",
           "PoolAcquisitionSoftwareStart"]

__docformat__ = 'restructuredtext'

import time
import weakref
import datetime
import traceback
import functools
import threading

from taurus.core.util.log import DebugIt
from taurus.core.util.enumeration import Enumeration

from sardana import AttrQuality, SardanaValue, State, ElementType, \
    TYPE_TIMERABLE_ELEMENTS

from sardana.sardanathreadpool import get_thread_pool
from sardana.pool import AcqSynch, AcqMode
from sardana.pool.poolaction import ActionContext, PoolAction, \
    OperationContext
from sardana.pool.poolsynchronization import PoolSynchronization

#: enumeration representing possible motion states
AcquisitionState = Enumeration("AcquisitionState", (
    "Stopped",
    #    "StoppedOnError",
    #    "StoppedOnAbort",
    "Acquiring",
    "Invalid"))

AS = AcquisitionState
AcquiringStates = AS.Acquiring,
StoppedStates = AS.Stopped,  # MS.StoppedOnError, MS.StoppedOnAbort

AcquisitionMap = {
    # AS.Stopped           : State.On,
    AS.Acquiring: State.Moving,
    AS.Invalid: State.Invalid,
}


def is_value_error(value):
    if isinstance(value, SardanaValue) and value.error:
        return True
    return False


def get_acq_ctrls(ctrls):
    """Converts configuration controllers into acquisition controllers.

    Takes care about converting their internals as well.

    :param ctrls: sequence of configuration controllers objects
    :type ctrls: sardana.pool.poolmeasurementgroup.ControllerConfiguration
    :return: sequence of acquisition controllers
    :rtype: :class:`~sardana.pool.poolacquisition.AcqController`

    .. note::
        The get_acq_ctrls function has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the class) may occur if
        deemed necessary by the core developers.
    """
    action_ctrls = []
    for ctrl in ctrls:
        action_ctrl = AcqController(ctrl)
        action_ctrls.append(action_ctrl)
    return action_ctrls


def get_timerable_ctrls(ctrls, acq_mode):
    """Converts timerable configuration controllers into acquisition
    controllers.

    Take care about converting their internals as well.
    Take care about assigning master according to acq_mode.

    :param ctrls: sequence of configuration controllers objects
    :type ctrls: sardana.pool.poolmeasurementgroup.ControllerConfiguration
    :param acq_mode: acquisition mode (timer/monitor)
    :type acq_mode: :class:`sardana.pool.AcqMode`
    :return: sequence of acquisition controllers
    :rtype: :class:`~sardana.pool.poolacquisition.AcqController`

    .. note::
        The get_timerable_ctrls function has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the class) may occur if
        deemed necessary by the core developers.
    """
    action_ctrls = []
    for ctrl in ctrls:
        attrs = {}
        if acq_mode is not None:
            master = None
            if acq_mode is AcqMode.Timer:
                master = ctrl.timer
            elif acq_mode is AcqMode.Monitor:
                master = ctrl.monitor
            attrs = {'master': master}
        action_ctrl = AcqController(ctrl, attrs)
        action_ctrls.append(action_ctrl)
    return action_ctrls


def get_timerable_items(ctrls, master, acq_mode=AcqMode.Timer):
    """Converts timerable configuration items into acquisition items.

    The timerable items are controllers and master. Convert these into
    the corresponding acquisition items.

    Take care about converting their internals as well.
    Take care about assigning master according to acq_mode.

    :param ctrls: sequence of configuration controllers objects
    :type ctrls: :obj:list<:class:`~sardana.pool.poolmeasurementgroup.ControllerConfiguration`>  # noqa
    :param master: master configuration object
    :type master: :class:`~sardana.pool.poolmeasurementgroup.ChannelConfiguration`  # noqa
    :param acq_mode: acquisition mode (timer/monitor)
    :type acq_mode: :class:`sardana.pool.AcqMode`
    :return: sequence of acquisition controllers
    :rtype: :class:`~sardana.pool.poolacquisition.AcqController`

    .. note::
        The get_timerable_ctrls function has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the class) may occur if
        deemed necessary by the core developers.
    """
    ctrls = get_timerable_ctrls(ctrls, acq_mode)
    # Search master AcqConfigurationItem obj
    for ctrl in ctrls:
        for channel in ctrl.get_channels():
            if channel.configuration == master:
                master = channel
                break
    return ctrls, master


class ActionArgs(object):

    def __init__(self, args, kwargs=None):
        self.args = args
        if kwargs is None:
            kwargs = {}
        self.kwargs = kwargs


class AcqConfigurationItem(object):
    """Wrapper for configuration item that will be used in an action.

    .. note::
        The AcqConfigurationItem function has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the class) may occur if
        deemed necessary by the core developers.
    """

    def __init__(self, configuration, attrs=None):
        """Constructs action item from a configuration item.

        Eventually it can be enriched with attrs.

        :param configuration: item configuration object
        :type configuration:
            :class:`sardana.pool.poolmeasurementgroup.ConfigurationItem`
        :param attrs: extra attributes to be inserted
        :type attrs: dict
        """
        self._configuration = weakref.ref(configuration)
        self.enabled = True

        if attrs is not None:
            self.__dict__.update(attrs)

    def __getattr__(self, item):
        return getattr(self.configuration, item)

    def get_configuration(self):
        """Returns the element associated with this item"""
        return self._configuration()

    def set_configuration(self, configuration):
        """Sets the element for this item"""
        self._configuration = weakref.ref(configuration)

    configuration = property(get_configuration)


class AcqController(AcqConfigurationItem):
    """Wrapper for controller configuration that will be used in an action.

    .. note::
        The AcqController function has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the class) may occur if
        deemed necessary by the core developers.
    """

    def __init__(self, configuration, attrs=None):
        """Constructs action controller from a configuration controller.

        Eventually it can be enriched with attrs.

        :param configuration: controller configuration object
        :type configuration:
            :class:`sardana.pool.poolmeasurementgroup.ControllerConfiguration`
        :param attrs: extra attributes to be inserted
        :type attrs: dict
        """
        master = None
        if attrs is not None:
            master = attrs.get('master')
        self._channels = []
        self._channels_enabled = []
        self._channels_disabled = []
        ch_attrs = {'controller': self}
        for conf_channel in configuration.get_channels():
            action_channel = AcqConfigurationItem(conf_channel, ch_attrs)
            self._channels.append(action_channel)
            if conf_channel in configuration.get_channels(enabled=True):
                self._channels_enabled.append(action_channel)
            if conf_channel in configuration.get_channels(enabled=False):
                self._channels_disabled.append(action_channel)
            if master is None:
                continue
            if master == conf_channel:
                attrs['master'] = action_channel
                master = None
        AcqConfigurationItem.__init__(self, configuration, attrs)

    def get_channels(self, enabled=None):
        if enabled is None:
            return list(self._channels)
        elif enabled:
            return list(self._channels_enabled)
        else:
            return list(self._channels_disabled)


class AcquisitionBaseContext(OperationContext):

    def exit(self):
        pool_action = self._pool_action
        pool_action._reset_ctrl_dicts()
        return OperationContext.exit(self)


class PoolAcquisition(PoolAction):
    """Acquisition action which is internally composed for sub-actions.

    Handle acquisition of experimental channels of the following types:
    * timerable (C/T, 1D and 2D) synchronized by software or hardware
    trigger/gate/start
    * 0D

    Synchronized by T/G elements or sofware synchronizer.
    """

    def __init__(self, main_element, name="Acquisition"):
        PoolAction.__init__(self, main_element, name)
        zerodname = name + ".0DAcquisition"
        hwname = name + ".HardwareAcquisition"
        swname = name + ".SoftwareAcquisition"
        sw_start_name = name + ".SoftwareStartAcquisition"
        synchname = name + ".Synchronization"

        self._sw_acq_args = None
        self._sw_start_acq_args = None
        self._0d_acq_args = None
        self._hw_acq_args = None
        self._synch_args = None
        self._sw_acq = PoolAcquisitionSoftware(main_element, name=swname)
        self._sw_start_acq = PoolAcquisitionSoftwareStart(
            main_element, name=sw_start_name)
        self._0d_acq = Pool0DAcquisition(main_element, name=zerodname)
        self._hw_acq = PoolAcquisitionHardware(main_element, name=hwname)
        self._synch = PoolSynchronization(main_element, name=synchname)
        self._handled_first_active = False

    def event_received(self, *args, **kwargs):
        """Callback executed on event of software synchronizer.

        Reacts on start, active, passive or end type of events
        """
        timestamp = time.time()
        _, type_, index = args
        name = type_.name
        if name == "state":
            return
        t_fmt = '%Y-%m-%d %H:%M:%S.%f'
        t_str = datetime.datetime.fromtimestamp(timestamp).strftime(t_fmt)
        msg = '%s event with id: %d received at: %s' % (name, index, t_str)
        self.debug(msg)
        if name == "start":
            if self._sw_start_acq_args is not None:
                self._sw_start_acq._wait()
                self._sw_start_acq._set_busy()
                self.debug('Executing software start acquisition.')
                self._sw_start_acq._started = True
                get_thread_pool().add(self._sw_start_acq.run,
                                      self._sw_start_acq._set_ready,
                                      *self._sw_start_acq_args.args,
                                      **self._sw_start_acq_args.kwargs)
        elif name == "active":
            # this code is not thread safe, but for the moment we assume that
            # only one EventGenerator will work at the same time
            if self._handled_first_active:
                timeout = 0
            else:
                timeout = None
                self._handled_first_active = True
            if self._sw_acq_args is not None:
                if not self._sw_acq._wait(timeout):
                    msg = ('Skipping trigger: software acquisition is still'
                           ' in progress.')
                    self.debug(msg)
                    return
                else:
                    self._sw_acq._set_busy()
                    self.debug('Executing software acquisition.')
                    self._sw_acq_args.kwargs.update({'index': index})
                    self._sw_acq._started = True
                    get_thread_pool().add(self._sw_acq.run,
                                          self._sw_acq._set_ready,
                                          *self._sw_acq_args.args,
                                          **self._sw_acq_args.kwargs)
            if self._0d_acq_args is not None:
                if not self._0d_acq._wait(timeout):
                    msg = ('Skipping trigger: ZeroD acquisition is still in'
                           ' progress.')
                    self.debug(msg)
                    return
                else:
                    self._0d_acq._set_busy()
                    self.debug('Executing ZeroD acquisition.')
                    self._0d_acq_args.kwargs.update({'index': index})
                    self._0d_acq._started = True
                    self._0d_acq._stopped = False
                    self._0d_acq._aborted = False
                    get_thread_pool().add(self._0d_acq.run,
                                          self._0d_acq._set_ready,
                                          *self._0d_acq_args.args,
                                          **self._0d_acq_args.kwargs)
        elif name == "passive":
            # TODO: _0d_acq_args comparison may not be necessary
            if (self._0d_acq_args is not None
                    and not self._0d_acq._is_ready()):
                self.debug('Stopping ZeroD acquisition.')
                self._0d_acq.stop_action()

    def prepare(self, config, acq_mode, value, synch_description=None,
                moveable=None, sw_synch_initial_domain=None,
                nb_starts=1, **kwargs):
        """Prepare measurement process.

        Organize sub-action arguments and loads configuration parameters to
        the hardware controllers.
        """
        self._sw_acq_args = None
        self._sw_start_acq_args = None
        self._0d_acq_args = None
        self._hw_acq_args = None
        self._synch_args = None
        self._handled_first_active = False
        ctrls_hw = []
        ctrls_sw = []
        ctrls_sw_start = []

        repetitions = synch_description.repetitions
        latency = synch_description.passive_time
        # Prepare controllers synchronized by hardware
        acq_sync_hw = [AcqSynch.HardwareTrigger, AcqSynch.HardwareStart,
                       AcqSynch.HardwareGate]
        ctrls = config.get_timerable_ctrls(acq_synch=acq_sync_hw, enabled=True)
        if len(ctrls) > 0:
            ctrls_hw = get_timerable_ctrls(ctrls, acq_mode)
            hw_args = (ctrls_hw, value, repetitions, latency)
            hw_kwargs = {}
            hw_kwargs.update(kwargs)
            self._hw_acq_args = ActionArgs(hw_args, hw_kwargs)

        # Prepare controllers synchronized by software Trigger and Gate
        acq_sync_sw = [AcqSynch.SoftwareGate, AcqSynch.SoftwareTrigger]
        ctrls = config.get_timerable_ctrls(acq_synch=acq_sync_sw, enabled=True)
        if len(ctrls) > 0:
            if acq_mode is AcqMode.Timer:
                master = config.get_master_timer_software()
            elif acq_mode is AcqMode.Monitor:
                master = config.get_master_monitor_software()

            ctrls_sw, master_sw = get_timerable_items(ctrls, master, acq_mode)

            sw_args = (ctrls_sw, value, master_sw)
            sw_kwargs = {'synch': True}
            sw_kwargs.update(kwargs)
            self._sw_acq_args = ActionArgs(sw_args, sw_kwargs)

        # Prepare controllers synchronized by software Start
        ctrls = config.get_timerable_ctrls(acq_synch=AcqSynch.SoftwareStart,
                                           enabled=True)
        if len(ctrls) > 0:
            if acq_mode is AcqMode.Timer:
                master = config.get_master_timer_software_start()
            elif acq_mode is AcqMode.Monitor:
                master = config.get_master_monitor_software_start()

            ctrls_sw_start, master_sw_start = get_timerable_items(ctrls,
                                                                  master,
                                                                  acq_mode)
            sw_start_args = (ctrls_sw_start, value, master_sw_start,
                             repetitions, latency)
            sw_start_kwargs = {'synch': True}
            sw_start_kwargs.update(kwargs)
            self._sw_start_acq_args = ActionArgs(sw_start_args,
                                                 sw_start_kwargs)

        # Prepare 0D controllers
        ctrls = config.get_zerod_ctrls(enabled=True)
        if len(ctrls) > 0:
            ctrls_acq_0d = get_acq_ctrls(ctrls)
            zerod_args = (ctrls_acq_0d,)
            zerod_kwargs = {'synch': True}
            zerod_kwargs.update(kwargs)
            self._0d_acq_args = ActionArgs(zerod_args, zerod_kwargs)

        # Prepare synchronizer controllers
        ctrls = config.get_synch_ctrls(enabled=True)
        ctrls_synch = get_acq_ctrls(ctrls)
        synch_args = (ctrls_synch, synch_description)
        synch_kwargs = {'moveable': moveable,
                        'sw_synch_initial_domain': sw_synch_initial_domain}
        synch_kwargs.update(kwargs)
        self._synch_args = ActionArgs(synch_args, synch_kwargs)

        # Load the configuration to the timerable controllers
        # TODO: apply the configuration only if necessary
        # Checking only the "changed" flag is not enough, one needs to check
        # if the controllers were not used with different measurement groups
        # configurations meanwhile (see: sardana-org/sardana#1171) in this
        # case the configuration must be applied even if it was not changed
        # if config.changed:
        ctrls = ctrls_hw + ctrls_sw_start + ctrls_sw

        for ctrl in ctrls:
            pool_ctrl = ctrl.element
            if not pool_ctrl.is_online():
                raise RuntimeError('The controller {0} is '
                                   'offline'.format(pool_ctrl.name))
            pool_ctrl.set_ctrl_par('acquisition_mode', acq_mode)
            pool_ctrl.operator = self.main_element
            pool_ctrl.set_ctrl_par('timer', ctrl.timer.axis)
            pool_ctrl.set_ctrl_par('monitor', ctrl.monitor.axis)
            synch = config.get_acq_synch_by_controller(pool_ctrl)
            pool_ctrl.set_ctrl_par('synchronization', synch)

            if ctrl.is_referable():
                for channel in ctrl.get_channels():
                    value_ref_enabled = channel.value_ref_enabled
                    pool_ctrl.set_axis_par(channel.axis,
                                           "value_ref_enabled",
                                           value_ref_enabled)
                    if value_ref_enabled:
                        pool_ctrl.set_axis_par(channel.axis,
                                               "value_ref_pattern",
                                               channel.value_ref_pattern)

        config.changed = False

        # Call synchronizer controllers prepare method
        self._prepare_synch_ctrls(ctrls_synch, nb_starts)

        # Call hardware and software start controllers prepare method
        ctrls = ctrls_hw + ctrls_sw_start
        self._prepare_ctrls(ctrls, value, repetitions, latency,
                            nb_starts)

        # Call software controllers prepare method
        nb_starts = nb_starts * repetitions
        repetitions = 1
        self._prepare_ctrls(ctrls_sw, value, repetitions, latency,
                            nb_starts)


    @staticmethod
    def _prepare_ctrls(ctrls, value, repetitions, latency, nb_starts):
        for ctrl in ctrls:
            axis = ctrl.master.axis
            pool_ctrl = ctrl.element
            pool_ctrl.ctrl.PrepareOne(axis, value, repetitions, latency,
                                      nb_starts)

    @staticmethod
    def _prepare_synch_ctrls(ctrls, nb_starts):
        for ctrl in ctrls:
            for chn in ctrl.get_channels():
                axis = chn.axis
                pool_ctrl = ctrl.element
                pool_ctrl.ctrl.PrepareOne(axis, nb_starts)

    def is_running(self):
        """Checks if acquisition is running.

        Acquisition is runnin if any of its sub-actions is running.
        """
        return self._sw_start_acq.is_running()\
            or self._0d_acq.is_running()\
            or self._sw_acq.is_running()\
            or self._hw_acq.is_running()\
            or self._synch.is_running()

    def run(self, *args, **kwargs):
        """Runs acquisition according to previous preparation."""
        for elem in self.get_elements():
            elem.put_state(None)
            # TODO: temporarily clear value buffers at the beginning of the
            # acquisition instead of doing it in the finish hook of each
            # acquisition sub-actions. See extensive explanation in the
            # constructor of PoolAcquisitionBase.
            try:
                elem.clear_value_buffer()
            except AttributeError:
                continue
            try:
                elem.clear_value_ref_buffer()
            except AttributeError:
                continue
            # clean also the pseudo counters, even the ones that do not
            # participate directly in the acquisition
            for pseudo_elem in elem.get_pseudo_elements():
                pseudo_elem.clear_value_buffer()

        if self._hw_acq_args is not None:
            self._hw_acq._wait()
            self._hw_acq._set_busy()
            self._hw_acq.run(*self._hw_acq_args.args,
                             **self._hw_acq_args.kwargs,
                             cb=self._hw_acq._set_ready)

        if self._sw_acq_args is not None\
                or self._sw_start_acq_args is not None\
                or self._0d_acq_args is not None:
            self._synch.add_listener(self)

        if self._synch_args is not None:
            self._synch._wait()
            self._synch._set_busy()
            self._synch.run(*self._synch_args.args,
                            **self._synch_args.kwargs,
                            cb=self._synch._set_ready)

    def _get_action_for_element(self, element):
        elem_type = element.get_type()
        if elem_type in TYPE_TIMERABLE_ELEMENTS:
            config = self.main_element.configuration
            try:
                acq_synch = config.get_acq_synch_by_channel(element)
            # when configuration was not yet set and one sets the
            # measurement group's integration time (this may happen on Tango
            # device initialization when memorized attributes are set we
            # fallback to software acquisition
            except KeyError:
                acq_synch = AcqSynch.SoftwareTrigger
            if acq_synch in (AcqSynch.SoftwareTrigger,
                             AcqSynch.SoftwareGate):
                return self._sw_acq
            elif acq_synch == AcqSynch.SoftwareStart:
                return self._sw_start_acq
            elif acq_synch in (AcqSynch.HardwareTrigger,
                               AcqSynch.HardwareGate,
                               AcqSynch.HardwareStart):
                return self._hw_acq
        elif elem_type == ElementType.ZeroDExpChannel:
            return self._0d_acq
        elif elem_type == ElementType.TriggerGate:
            return self._synch
        else:
            raise RuntimeError("Could not determine action for element %s" %
                               element)

    def clear_elements(self):
        """Clears all elements from this action"""

    def add_element(self, element):
        """Adds a new element to this action.

        :param element: the new element to be added
        :type element: sardana.pool.poolelement.PoolElement"""
        action = self._get_action_for_element(element)
        action.add_element(element)

    def remove_element(self, element):
        """Removes an element from this action. If the element is not part of
        this action, a ValueError is raised.

        :param element: the new element to be removed
        :type element: sardana.pool.poolelement.PoolElement

        :raises: ValueError"""
        for action in self._get_acq_for_element(element):
            action.remove_element(element)

    def get_elements(self, copy_of=False):
        """Returns a sequence of all elements involved in this action.

        :param copy_of: If False (default) the internal container of
                        elements is returned. If True, a copy of the
                        internal container is returned instead
        :type copy_of: bool
        :return: a sequence of all elements involved in this action.
        :rtype: seq<sardana.pool.poolelement.PoolElement>"""
        return (self._hw_acq.get_elements() + self._sw_acq.get_elements()
                + self._sw_start_acq.get_elements()
                + self._0d_acq.get_elements() + self._synch.get_elements())

    def get_pool_controller_list(self):
        """Returns a list of all controller elements involved in this action.

        :return: a list of all controller elements involved in this action.
        :rtype: list<sardana.pool.poolelement.PoolController>"""
        return self._pool_ctrl_list

    def get_pool_controllers(self):
        """Returns a dict of all controller elements involved in this action.

        :return: a dict of all controller elements involved in this action.
        :rtype: dict<sardana.pool.poolelement.PoolController,
                seq<sardana.pool.poolelement.PoolElement>>"""
        ret = {}
        ret.update(self._hw_acq.get_pool_controllers())
        ret.update(self._sw_acq.get_pool_controllers())
        ret.update(self._sw_start_acq.get_pool_controllers())
        ret.update(self._0d_acq.get_pool_controllers())
        return ret

    def read_value(self, ret=None, serial=False):
        """Reads value information of all elements involved in this action

        :param ret: output map parameter that should be filled with value
                    information. If None is given (default), a new map is
                    created an returned
        :type ret: dict
        :param serial: If False (default) perform controller HW value requests
                       in parallel. If True, access is serialized.
        :type serial: bool
        :return: a map containing value information per element
        :rtype: dict<:class:~`sardana.pool.poolelement.PoolElement`,
                     :class:~`sardana.sardanavalue.SardanaValue`>"""
        # TODO: this is broken now - fix it
        ret = self._ct_acq.read_value(ret=ret, serial=serial)
        ret.update(self._0d_acq.read_value(ret=ret, serial=serial))
        return ret


class PoolAcquisitionBase(PoolAction):
    """Base class for sub-acquisition.

    .. note::
        The PoolAcquisitionBase class has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the module) may occur if
        deemed necessary by the core developers.

    .. todo: Think of moving the ready/busy mechanism to PoolAction
    """

    def __init__(self, main_element, name):
        PoolAction.__init__(self, main_element, name)
        self._channels = []
        self._index = None
        self._ready = threading.Event()
        self._ready.set()

    def _is_ready(self):
        return self._ready.is_set()

    def _wait(self, timeout=None):
        return self._ready.wait(timeout)

    def _set_ready(self, _=None):
        self._ready.set()

    def _is_busy(self):
        return not self._ready.is_set()

    def _set_busy(self):
        self._ready.clear()


class PoolAcquisitionTimerable(PoolAcquisitionBase):
    """Base class for acquisitions of timerable channels.

     Implements a generic start_action method. action_loop method must be
     implemented by the sub-class.

    .. note::
        The PoolAcquisitionTimerable class has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the module) may occur if
        deemed necessary by the core developers.
    """

    OperationContextClass = AcquisitionBaseContext

    def __init__(self, main_element, name):
        PoolAcquisitionBase.__init__(self, main_element, name)
        self._nb_states_per_value = None
        self._acq_sleep_time = None
        self._pool_ctrl_dict_loop = None
        self._pool_ctrl_dict_ref = None
        self._pool_ctrl_dict_value = None

        # TODO: for the moment we can not clear value buffers at the end of
        # the acquisition. This is because of the pseudo counters that are
        # based on channels synchronized by hardware and software.
        # These two acquisition actions finish at different moment so the
        # pseudo counter will loose the value buffer of some of its physicals
        # if we clear the buffer at the end.
        # Whenever there will be solution for that, after refactoring of the
        # acquisition actions, uncomment this line
        # self.add_finish_hook(self.clear_value_buffers, True)

    def get_read_value_ref_ctrls(self):
        return self._pool_ctrl_dict_ref

    def read_value_ref(self, ret=None, serial=False):
        """Reads value ref information of all elements involved in this action

        :param ret: output map parameter that should be filled with value
                    information. If None is given (default), a new map is
                    created an returned
        :type ret: dict
        :param serial: If False (default) perform controller HW value requests
                       in parallel. If True, access is serialized.
        :type serial: bool
        :return: a map containing value information per element
        :rtype: dict<:class:~`sardana.pool.poolelement.PoolElement`,
                     (value object, Exception or None)>"""
        with ActionContext(self):
            return self.raw_read_value_ref(ret=ret, serial=serial)

    def raw_read_value_ref(self, ret=None, serial=False):
        """**Unsafe**. Reads value ref information of all referable elements
        involved in this acquisition

        :param ret: output map parameter that should be filled with value
                    information. If None is given (default), a new map is
                    created an returned
        :type ret: dict
        :param serial: If False (default) perform controller HW value requests
                       in parallel. If True, access is serialized.
        :type serial: bool
        :return: a map containing value information per element
        :rtype: dict<:class:~`sardana.pool.poolelement.PoolElement,
                :class:`sardana.sardanavalue.SardanaValue`>
        """
        if ret is None:
            ret = {}

        read = self._raw_read_value_ref_concurrent
        if serial:
            read = self._raw_read_value_ref_serial

        value_info = self._value_info

        with value_info:
            value_info.init(len(self.get_read_value_ref_ctrls()))
            read(ret)
            value_info.wait()
        return ret

    def _raw_read_value_ref_serial(self, ret):
        """Internal method. Read value ref in a serial mode"""
        for pool_ctrl in self.get_read_value_ref_ctrls():
            self._raw_read_ctrl_value_ref(ret, pool_ctrl)
        return ret

    def _raw_read_value_ref_concurrent(self, ret):
        """Internal method. Read value ref in a concurrent mode"""
        th_pool = get_thread_pool()
        for pool_ctrl in self.get_read_value_ref_ctrls():
            th_pool.add(self._raw_read_ctrl_value_ref, None, ret, pool_ctrl)
        return ret

    def _raw_read_ctrl_value_ref(self, ret, pool_ctrl):
        """Internal method. Read controller value ref information and store
        it in ret parameter"""
        try:
            axes = [elem.axis for elem in self._pool_ctrl_dict_ref[pool_ctrl]]
            value_infos = pool_ctrl.raw_read_axis_value_refs(axes)
            ret.update(value_infos)
        finally:
            self._value_info.finish_one()

    def _process_value_buffer(self, acquirable, value, final=False):
        final_str = "final " if final else ""
        if is_value_error(value):
            self.error("Loop %sread value error for %s" % (final_str,
                                                           acquirable.name))
            msg = "Details: " + "".join(
                traceback.format_exception(*value.exc_info))
            self.debug(msg)
            acquirable.put_value(value, propagate=2)
        else:
            acquirable.extend_value_buffer(value, propagate=2)

    def _process_value_ref_buffer(self, acquirable, value_ref, final=False):
        final_str = "final " if final else ""
        if is_value_error(value_ref):
            self.error("Loop read ref %svalue error for %s" %
                       (final_str, acquirable.name))
            msg = "Details: " + "".join(
                traceback.format_exception(*value_ref.exc_info))
            self.debug(msg)
            acquirable.put_value_ref(value_ref, propagate=2)
        else:
            acquirable.extend_value_ref_buffer(value_ref, propagate=2)

    def in_acquisition(self, states):
        """Determines if we are in acquisition or if the acquisition has ended
        based on the current unit trigger modes and states returned by the
        controller(s)

        :param states: a map containing state information as returned by
                       read_state_info
        :type states: dict<PoolElement, State>
        :return: returns True if in acquisition or False otherwise
        :rtype: bool"""
        for elem in states:
            s = states[elem][0][0]
            if self._is_in_action(s):
                return True

    @DebugIt()
    def start_action(self, ctrls, value, master, repetitions, latency,
                     index, acq_sleep_time, nb_states_per_value,
                     **kwargs):
        """
        Prepares everything for acquisition and starts it
        :param ctrls: List of enabled pool acquisition controllers
        :type ctrls: list
        :param value: integration time/monitor counts
        :type value: float/int or seq<float/int>
        :param repetitions: repetitions
        :type repetitions: int
        :param latency:
        :type latency: float
        :param master: master channel is the last one to start
        :type master: Channel
        :param index:
        :type index: int
        :param acq_sleep_time: sleep time between state queries
        :type acq_sleep_time: float
        :param nb_states_per_value: how many state queries between readouts
        :type nb_states_per_value: int
        :param args:
        :param kwargs:
        :return:
        """

        pool = self.pool
        self._aborted = False
        self._stopped = False

        self._index = index

        self._acq_sleep_time = acq_sleep_time
        if self._acq_sleep_time is None:
            self._acq_sleep_time = pool.acq_loop_sleep_time

        self._nb_states_per_value = nb_states_per_value
        if self._nb_states_per_value is None:
            self._nb_states_per_value = pool.acq_loop_states_per_value

        # make sure the controller which has the master channel is the last to
        # be called
        if master is not None:
            ctrls.remove(master.controller)
            ctrls.append(master.controller)

        # controllers that will be read during the action
        self._set_pool_ctrl_dict_loop(ctrls)
        # split controllers to read value and value reference
        self._split_ctrl(ctrls)
        # channels that are acquired (only enabled)
        self._channels = []

        def load(channel, value, repetitions, latency=0):
            axis = channel.axis
            pool_ctrl = channel.controller
            ctrl = pool_ctrl.ctrl
            ctrl.PreLoadAll()
            res = ctrl.PreLoadOne(axis, value, repetitions, latency)
            if not res:
                msg = ("%s.PreLoadOne(%d) returned False" %
                       (pool_ctrl.name, axis))
                raise Exception(msg)
            ctrl.LoadOne(axis, value, repetitions, latency)
            ctrl.LoadAll()

        with ActionContext(self):
            # PreLoadAll, PreLoadOne, LoadOne and LoadAll
            for ctrl in ctrls:
                # TODO find solution for master now sardana only use timer
                load(ctrl.timer, value, repetitions, latency)

            # TODO: remove when the action allows to use tango attributes
            try:
                ctrls.pop('__tango__')
            except Exception:
                pass

            # PreStartAll on all enabled controllers
            for ctrl in ctrls:
                pool_ctrl = ctrl.element
                pool_ctrl.ctrl.PreStartAll()

            # PreStartOne & StartOne on all enabled elements
            for ctrl in ctrls:
                channels = ctrl.get_channels(enabled=True)

                # make sure that the master timer/monitor is started as
                # the last one
                channels.remove(ctrl.master)
                channels.append(ctrl.master)
                for channel in channels:
                    axis = channel.axis
                    pool_ctrl = ctrl.element
                    ret = pool_ctrl.ctrl.PreStartOne(axis, value)
                    if not ret:
                        msg = ("%s.PreStartOne(%d) returns False" %
                               (ctrl.name, axis))
                        raise Exception(msg)
                    try:
                        pool_ctrl = ctrl.element
                        pool_ctrl.ctrl.StartOne(axis, value)
                    except Exception as e:
                        self.debug(e, exc_info=True)
                        channel.set_state(State.Fault, propagate=2)
                        msg = ("%s.StartOne(%d) failed" %
                               (ctrl.name, axis))
                        raise Exception(msg)

                    self._channels.append(channel)

            # set the state of all elements to  and inform their listeners
            for channel in self._channels:
                channel.set_state(State.Moving, propagate=2)

            # StartAll on all enabled controllers
            for ctrl in ctrls:
                try:
                    pool_ctrl = ctrl.element
                    pool_ctrl.ctrl.StartAll()
                except Exception as e:
                    channels = ctrl.get_channels(enabled=True)
                    self.debug(e, exc_info=True)
                    for channel in channels:
                        channel.set_state(State.Fault, propagate=2)
                    msg = ("%s.StartAll() failed" % ctrl.name)
                    raise Exception(msg)

    def _set_pool_ctrl_dict_loop(self, ctrls):
        ctrl_channels = {}
        for ctrl in ctrls:
            pool_channels = []
            pool_ctrl = ctrl.element
            # only CT will be read in the loop, 1D and 2D not
            if ElementType.CTExpChannel not in ctrl.get_ctrl_types():
                continue
            for channel in ctrl.get_channels(enabled=True):
                pool_channels.append(channel.element)
            ctrl_channels[pool_ctrl] = pool_channels
        self._pool_ctrl_dict_loop = ctrl_channels

    def _split_ctrl(self, ctrls):
        ctrl_channels_value = {}
        ctrl_channels_ref = {}
        for ctrl in ctrls:
            if not ctrl.is_referable():
                pool_channels_value = []
                pool_ctrl = ctrl.element
                for channel in ctrl.get_channels(enabled=True):
                    pool_channels_value.append(channel.element)
                ctrl_channels_value[pool_ctrl] = pool_channels_value
            else:
                pool_channels_value = []
                pool_channels_ref = []
                pool_ctrl = ctrl.element
                for channel in ctrl.get_channels(enabled=True):
                    if channel.value_ref_enabled:
                        pool_channels_ref.append(channel.element)
                        if channel.has_pseudo_elements():
                            pool_channels_value.append(channel.element)
                    else:
                        pool_channels_value.append(channel.element)
                if len(pool_channels_value) > 0:
                    ctrl_channels_value[pool_ctrl] = pool_channels_value
                if len(pool_channels_ref) > 0:
                    ctrl_channels_ref[pool_ctrl] = pool_channels_ref

        self._pool_ctrl_dict_value = ctrl_channels_value
        self._pool_ctrl_dict_ref = ctrl_channels_ref

    def _reset_ctrl_dicts(self):
        self._pool_ctrl_dict_loop = None
        self._pool_ctrl_dict_value = None
        self._pool_ctrl_dict_ref = None

    def clear_value_buffers(self):
        for channel in self._channels:
            channel.clear_value_buffer()


class PoolAcquisitionHardware(PoolAcquisitionTimerable):
    """Acquisition action for controllers synchronized by hardware

    .. note::
        The PoolAcquisitionHardware class has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the module) may occur if
        deemed necessary by the core developers.

    .. todo:: Try to move the action loop logic to base class it is
    basically the same as in PoolAcquisitionSoftwareStart.
    """

    def __init__(self, main_element, name="AcquisitionHardware"):
        PoolAcquisitionTimerable.__init__(self, main_element, name)

    def start_action(self, ctrls, value, repetitions, latency,
                     acq_sleep_time=None, nb_states_per_value=None,
                     **kwargs):
        PoolAcquisitionTimerable.start_action(self, ctrls, value, None,
                                         repetitions, latency, None,
                                         acq_sleep_time, nb_states_per_value,
                                         **kwargs)

    def get_read_value_ctrls(self):
        return self._pool_ctrl_dict_value

    @DebugIt()
    def action_loop(self):
        i = 0

        states, values, value_refs = {}, {}, {}
        for channel in self._channels:
            element = channel.element
            states[element] = None

        nap = self._acq_sleep_time
        nb_states_per_value = self._nb_states_per_value

        while True:
            self.read_state_info(ret=states)
            if not self.in_acquisition(states):
                break

            # read value every n times
            if not i % nb_states_per_value:
                self.read_value(ret=values)
                for acquirable, value in list(values.items()):
                    self._process_value_buffer(acquirable, value)
                self.read_value_ref(ret=value_refs)
                for acquirable, value_ref in list(value_refs.items()):
                    self._process_value_ref_buffer(acquirable, value_ref)

            time.sleep(nap)
            i += 1

        with ActionContext(self):
            self.raw_read_value(ret=values)
            self.raw_read_value_ref(ret=value_refs)

        for acquirable, state_info in list(states.items()):
            if acquirable in values:
                value = values[acquirable]
                self._process_value_buffer(acquirable, value, final=True)
            if acquirable in value_refs:
                value_ref = value_refs[acquirable]
                self._process_value_ref_buffer(acquirable, value_ref,
                                               final=True)
            state_info = acquirable._from_ctrl_state_info(state_info)
            set_state_info = functools.partial(acquirable.set_state_info,
                                               state_info,
                                               propagate=2,
                                               safe=True)
            self.add_finish_hook(set_state_info, False)


class PoolAcquisitionSoftware(PoolAcquisitionTimerable):
    """Acquisition action for controllers synchronized by software

    .. note::
        The PoolAcquisitionSoftware class has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the module) may occur if
        deemed necessary by the core developers.
    """

    def __init__(self, main_element, name="AcquisitionSoftware", slaves=None):
        PoolAcquisitionTimerable.__init__(self, main_element, name)

        if slaves is None:
            slaves = ()
        self._slaves = slaves

    def get_read_value_ctrls(self):
        # technical debt in order to work both in case of meas group and
        # single channel
        if self._pool_ctrl_dict_value is not None:
            return self._pool_ctrl_dict_value
        else:
            return self._pool_ctrl_dict

    def get_read_value_ref_ctrls(self):
        # technical debt in order to work both in case of meas group and
        # single channel
        if self._pool_ctrl_dict_ref is not None:
            return self._pool_ctrl_dict_ref
        else:
            return self._pool_ctrl_dict

    def get_read_value_loop_ctrls(self):
        return self._pool_ctrl_dict_loop

    def start_action(self, ctrls, value, master, index, acq_sleep_time=None,
                     nb_states_per_value=None, **kwargs):
        PoolAcquisitionTimerable.start_action(self, ctrls, value, master, 1, 0,
                                         index, acq_sleep_time,
                                         nb_states_per_value, **kwargs)

    @DebugIt()
    def action_loop(self):
        states, values, value_refs = {}, {}, {}
        for channel in self._channels:
            element = channel.element
            states[element] = None

        nap = self._acq_sleep_time
        nb_states_per_value = self._nb_states_per_value

        i = 0
        while True:
            self.read_state_info(ret=states)
            if not self.in_acquisition(states):
                break

            # read value every n times
            if not i % nb_states_per_value:
                self.read_value_loop(ret=values)
                for acquirable, value in list(values.items()):
                    acquirable.put_value(value, quality=AttrQuality.Changing)

            time.sleep(nap)
            i += 1

        for slave in self._slaves:
            try:
                slave.stop_action()
            except Exception:
                self.warning("Unable to stop slave acquisition %s",
                             slave.getLogName())
                self.debug("Details", exc_info=1)

        with ActionContext(self):
            self.raw_read_value(ret=values)
            self.raw_read_value_ref(ret=value_refs)

        for acquirable, state_info in list(states.items()):
            if acquirable in values:
                value = values[acquirable]
                if is_value_error(value):
                    self.error("Loop final read value error for: %s" %
                               acquirable.name)
                    msg = "Details: " + "".join(
                        traceback.format_exception(*value.exc_info))
                    self.debug(msg)
                acquirable.get_value_attribute().set_quality(
                    AttrQuality.Valid)
                acquirable.append_value_buffer(value, self._index,
                                               propagate=2)
            if acquirable in value_refs:
                value_ref = value_refs[acquirable]
                if is_value_error(value_ref):
                    self.error("Loop final read value ref error for: %s" %
                               acquirable.name)
                    msg = "Details: " + "".join(
                        traceback.format_exception(*value_ref.exc_info))
                    self.debug(msg)
                acquirable.append_value_ref_buffer(value_ref, self._index)
            state_info = acquirable._from_ctrl_state_info(state_info)
            set_state_info = functools.partial(acquirable.set_state_info,
                                               state_info,
                                               propagate=2,
                                               safe=True)
            self.add_finish_hook(set_state_info, False)


class PoolAcquisitionSoftwareStart(PoolAcquisitionTimerable):
    """Acquisition action for controllers synchronized by software start

    .. note::
        The PoolAcquisitionSoftwareStart class has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the module) may occur if
        deemed necessary by the core developers.

    .. todo:: Try to move the action loop logic to base class it is
    basically the same as in PoolAcquisitionHardware.
    """

    def __init__(self, main_element, name="AcquisitionSoftwareStart"):
        PoolAcquisitionTimerable.__init__(self, main_element, name)

    def get_read_value_ctrls(self):
        # technical debt in order to work both in case of meas group and
        # single channel
        return self._pool_ctrl_dict_value

    def start_action(self, ctrls, value, master, repetitions, latency,
                     acq_sleep_time=None, nb_states_per_value=None,
                     **kwargs):
        PoolAcquisitionTimerable.start_action(self, ctrls, value, master,
                                         repetitions, latency, None,
                                         acq_sleep_time, nb_states_per_value,
                                         **kwargs)

    @DebugIt()
    def action_loop(self):
        i = 0

        states, values, value_refs = {}, {}, {}
        for channel in self._channels:
            element = channel.element
            states[element] = None

        nap = self._acq_sleep_time
        nb_states_per_value = self._nb_states_per_value

        while True:
            self.read_state_info(ret=states)
            if not self.in_acquisition(states):
                break

            # read value every n times
            if not i % nb_states_per_value:
                self.read_value(ret=values)
                for acquirable, value in list(values.items()):
                    if is_value_error(value):
                        self.error("Loop read value error for %s" %
                                   acquirable.name)
                        msg = "Details: " + "".join(
                            traceback.format_exception(*value.exc_info))
                        self.debug(msg)
                        acquirable.put_value(value)
                    else:
                        acquirable.extend_value_buffer(value)
                self.read_value_ref(ret=value_refs)
                for acquirable, value_ref in list(value_refs.items()):
                    if is_value_error(value_ref):
                        self.error("Loop read value ref error for %s" %
                                   acquirable.name)
                        msg = "Details: " + "".join(
                            traceback.format_exception(*value.exc_info))
                        self.debug(msg)
                        acquirable.put_value_ref(value)
                    else:
                        acquirable.extend_value_ref_buffer(value_ref)
            time.sleep(nap)
            i += 1

        with ActionContext(self):
            self.raw_read_value(ret=values)
            self.raw_read_value_ref(ret=value_refs)

        for acquirable, state_info in list(states.items()):
            if acquirable in values:
                value = values[acquirable]
                if is_value_error(value):
                    self.error("Loop final read value error for: %s" %
                               acquirable.name)
                    msg = "Details: " + "".join(
                        traceback.format_exception(*value.exc_info))
                    self.debug(msg)
                    acquirable.put_value(value)
                else:
                    acquirable.extend_value_buffer(value, propagate=2)
            if acquirable in value_refs:
                value_ref = value_refs[acquirable]
                if is_value_error(value_ref):
                    self.error("Loop final read value ref error for: %s" %
                               acquirable.name)
                    msg = "Details: " + "".join(
                        traceback.format_exception(*value_ref.exc_info))
                    self.debug(msg)
                    acquirable.put_value_ref(value_ref)
                else:
                    acquirable.extend_value_ref_buffer(value_ref, propagate=2)
            state_info = acquirable._from_ctrl_state_info(state_info)
            set_state_info = functools.partial(acquirable.set_state_info,
                                               state_info,
                                               propagate=2,
                                               safe=True)
            self.add_finish_hook(set_state_info, False)


class PoolCTAcquisition(PoolAcquisitionTimerable):
    """..todo:: remove it, still used by pseudo counter"""

    def __init__(self, main_element, name="CTAcquisition", slaves=None):
        self._channels = None

        if slaves is None:
            slaves = ()
        self._slaves = slaves

        PoolAcquisitionTimerable.__init__(self, main_element, name)

    def get_read_value_loop_ctrls(self):
        return self._pool_ctrl_dict_loop

    def in_acquisition(self, states):
        """Determines if we are in acquisition or if the acquisition has ended
        based on the current unit trigger modes and states returned by the
        controller(s)

        :param states: a map containing state information as returned by
                       read_state_info
        :type states: dict<PoolElement, State>
        :return: returns True if in acquisition or False otherwise
        :rtype: bool"""
        for elem in states:
            s = states[elem][0][0]
            if self._is_in_action(s):
                return True

    @DebugIt()
    def action_loop(self):
        i = 0

        states, values = {}, {}
        for element in self._channels:
            states[element] = None
            # values[element] = None

        nap = self._acq_sleep_time
        nb_states_per_value = self._nb_states_per_value

        # read values to send a first event when starting to acquire
        with ActionContext(self):
            self.raw_read_value_loop(ret=values)
            for acquirable, value in list(values.items()):
                acquirable.put_value(value, propagate=2)

        while True:
            self.read_state_info(ret=states)
            if not self.in_acquisition(states):
                break

            # read value every n times
            if not i % nb_states_per_value:
                self.read_value_loop(ret=values)
                for acquirable, value in list(values.items()):
                    acquirable.put_value(value)

            time.sleep(nap)
            i += 1

        for slave in self._slaves:
            try:
                slave.stop_action()
            except Exception:
                self.warning("Unable to stop slave acquisition %s",
                             slave.getLogName())
                self.debug("Details", exc_info=1)

        with ActionContext(self):
            self.raw_read_state_info(ret=states)
            self.raw_read_value_loop(ret=values)

        for acquirable, state_info in list(states.items()):
            # first update the element state so that value calculation
            # that is done after takes the updated state into account
            acquirable.set_state_info(state_info, propagate=0)
            if acquirable in values:
                value = values[acquirable]
                acquirable.put_value(value, propagate=2)
            state_info = acquirable._from_ctrl_state_info(state_info)
            set_state_info = functools.partial(acquirable.set_state_info,
                                               state_info,
                                               propagate=2,
                                               safe=True)
            self.add_finish_hook(set_state_info, False)


class Pool0DAcquisition(PoolAcquisitionBase):

    def __init__(self, main_element, name="0DAcquisition"):
        PoolAcquisitionBase.__init__(self, main_element, name)

    def start_action(self, conf_ctrls, index, acq_sleep_time=None,
                     nb_states_per_value=None, **kwargs):
        """Prepares everything for acquisition and starts it.

           :param: config"""

        pool = self.pool
        # TODO: rollback this change when a proper synchronization between
        # acquisition actions will be develop.
        # Now the meta acquisition action is resettung them to 0.
        # self._aborted = False
        # self._stopped = False

        self._index = index
        self._acq_sleep_time = acq_sleep_time
        if self._acq_sleep_time is None:
            self._acq_sleep_time = pool.acq_loop_sleep_time

        self._nb_states_per_value = nb_states_per_value
        if self._nb_states_per_value is None:
            self._nb_states_per_value = pool.acq_loop_states_per_value

        # channels that are acquired (only enabled)
        self._channels = []

        with ActionContext(self):
            # set the state of all elements to  and inform their listeners

            for conf_ctrl in conf_ctrls:
                for conf_channel in conf_ctrl.get_channels(enabled=True):
                    conf_channel.clear_buffer()
                    conf_channel.set_state(State.Moving, propagate=2)
                    self._channels.append(conf_channel)

    def in_acquisition(self, states):
        """Determines if we are in acquisition or if the acquisition has ended
        based on the current unit trigger modes and states returned by the
        controller(s)

        :param states: a map containing state information as returned by
                       read_state_info
        :type states: dict<PoolElement, State>
        :return: returns True if in acquisition or False otherwise
        :rtype: bool"""
        for state in states:
            s = states[state][0]
            if self._is_in_action(s):
                return True

    def action_loop(self):
        states, values = {}, {}
        for conf_channel in self._channels:
            element = conf_channel.element
            states[element] = None
            values[element] = None

        nap = self._acq_sleep_time
        while True:
            self.read_value(ret=values)
            for acquirable, value in list(values.items()):
                acquirable.put_current_value(value, propagate=0)
            if self._stopped or self._aborted:
                break
            time.sleep(nap)

        for element in self._channels:
            value = element.accumulated_value.value_obj
            element.append_value_buffer(value, self._index, propagate=2)

        with ActionContext(self):
            self.raw_read_state_info(ret=states)

        for acquirable, state_info in list(states.items()):
            state_info = acquirable._from_ctrl_state_info(state_info)
            set_state_info = functools.partial(acquirable.set_state_info,
                                               state_info,
                                               propagate=2,
                                               safe=True)
            self.add_finish_hook(set_state_info, False)

    def stop_action(self, *args, **kwargs):
        """Stop procedure for this action."""
        self._stopped = True

    def abort_action(self, *args, **kwargs):
        """Aborts procedure for this action"""
        self._aborted = True


class PoolIORAcquisition(PoolAction):

    def __init__(self, pool, name="IORAcquisition"):
        self._channels = None
        PoolAction.__init__(self, pool, name)

    def start_action(self, *args, **kwargs):
        pass

    def in_acquisition(self, states):
        return True
        pass

    @DebugIt()
    def action_loop(self):
        i = 0

        states, values = {}, {}
        for element in self._channels:
            states[element] = None
            values[element] = None

        # read values to send a first event when starting to acquire
        self.read_value(ret=values)
        for acquirable, value in list(values.items()):
            acquirable.put_value(value, propagate=2)

        while True:
            self.read_state_info(ret=states)

            if not self.in_acquisition(states):
                break

            # read value every n times
            if not i % 5:
                self.read_value(ret=values)
                for acquirable, value in list(values.items()):
                    acquirable.put_value(value)

            i += 1
            time.sleep(0.01)

        self.read_state_info(ret=states)

        # first update the element state so that value calculation
        # that is done after takes the updated state into account
        for acquirable, state_info in list(states.items()):
            acquirable.set_state_info(state_info, propagate=0)

        # Do NOT send events before we exit the OperationContext, otherwise
        # we may be asked to start another action before we leave the context
        # of the current action. Instead, send the events in the finish hook
        # which is executed outside the OperationContext

        def finish_hook(*args, **kwargs):
            # read values and propagate the change to all listeners
            self.read_value(ret=values)
            for acquirable, value in list(values.items()):
                acquirable.put_value(value, propagate=2)

            # finally set the state and propagate to all listeners
            for acquirable, state_info in list(states.items()):
                acquirable.set_state_info(state_info, propagate=2)

        self.set_finish_hook(finish_hook)
