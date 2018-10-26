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

"""This module is part of the Python Pool libray. It defines the class for an
acquisition"""

__all__ = ["AcquisitionState", "AcquisitionMap", "PoolCTAcquisition",
           "Pool0DAcquisition", "Channel", "PoolIORAcquisition"]

__docformat__ = 'restructuredtext'

import time
import datetime

from taurus.core.util.log import DebugIt
from taurus.core.util.enumeration import Enumeration

from sardana import SardanaValue, State, ElementType, TYPE_TIMERABLE_ELEMENTS
from sardana.sardanathreadpool import get_thread_pool
from sardana.pool import SynchParam, SynchDomain, AcqSynch, AcqMode
from sardana.pool.poolaction import ActionContext, PoolActionItem, PoolAction
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

MeasurementActions = Enumeration("MeasurementActions", (
    "AcquisitionHardware",
    "AcquisitionSoftware",
    "AcquisitionSoftwareStart",
    "Acquisition0D",
    "Synchronization")
)


def is_value_error(value):
    if isinstance(value, SardanaValue) and value.error:
        return True
    return False


class PoolAcquisition(PoolAction):

    def __init__(self, main_element, name="Acquisition"):
        PoolAction.__init__(self, main_element, name)
        zerodname = name + ".0DAcquisition"
        hwname = name + ".HardwareAcquisition"
        swname = name + ".SoftwareAcquisition"
        synchname = name + ".Synchronization"

        self._sw_acq_config = None
        self._0d_config = None
        self._0d_acq = Pool0DAcquisition(main_element, name=zerodname)
        self._sw_acq = PoolAcquisitionSoftware(main_element, name=swname)
        self._hw_acq = PoolAcquisitionHardware(main_element, name=hwname)
        self._synch = PoolSynchronization(main_element, name=synchname)

    def set_sw_config(self, config):
        self._sw_acq_config = config

    def set_0d_config(self, config):
        self._0d_config = config

    def event_received(self, *args, **kwargs):
        timestamp = time.time()
        _, type_, value = args
        name = type_.name
        if name == "state":
            return
        t_fmt = '%Y-%m-%d %H:%M:%S.%f'
        t_str = datetime.datetime.fromtimestamp(timestamp).strftime(t_fmt)
        msg = '%s event with id: %d received at: %s' % (name, value, t_str)
        self.debug(msg)
        if name == "active":
            # this code is not thread safe, but for the moment we assume that
            # only one EventGenerator will work at the same time
            if self._sw_acq_config:
                if self._sw_acq._is_started() or self._sw_acq.is_running():
                    msg = ('Skipping trigger: software acquisition is still'
                           ' in progress.')
                    self.debug(msg)
                    return
                else:
                    self.debug('Executing software acquisition.')
                    args = ()
                    kwargs = self._sw_acq_config
                    # TODO: key synch is not used on the code, remove it
                    kwargs['synch'] = True
                    kwargs['index'] = value
                    self._sw_acq._started = True
                    get_thread_pool().add(self._sw_acq.run, *args, **kwargs)
            if self._0d_config:
                if self._0d_acq._is_started() or self._0d_acq.is_running():
                    msg = ('Skipping trigger: ZeroD acquisition is still in'
                           ' progress.')
                    self.debug(msg)
                    return
                else:
                    self.debug('Executing ZeroD acquisition.')
                    args = ()
                    kwargs = self._0d_config
                    # TODO: key synch is not used on the code, remove it
                    kwargs['synch'] = True
                    kwargs['index'] = value
                    self._0d_acq._started = True
                    self._0d_acq._stopped = False
                    self._0d_acq._aborted = False
                    get_thread_pool().add(self._0d_acq.run, *args, **kwargs)
        elif name == "passive":
            if self._0d_config and (self._0d_acq._is_started() or
                                    self._0d_acq.is_running()):
                self.debug('Stopping ZeroD acquisition.')
                self._0d_acq.stop_action()

    def prepare(self, ctrl_lodeable, value, repetitions, latency,
                nr_of_starts):
        """Prepare measurement."""

        for conf_ctrl, lodeable in ctrl_lodeable.items():
            axis = lodeable.axis
            conf_ctrl.ctrl.PrepareOne(axis, value, repetitions, latency,
                                      nr_of_starts)

    def is_running(self):
        return self._0d_acq.is_running() or\
            self._sw_acq.is_running() or\
            self._hw_acq.is_running() or\
            self._synch.is_running()

    def run(self, head, config, multiple, acq_mode, value, synchronization,
            moveable, sw_synch_initial_domain=None, *args, **kwargs):

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
            # clean also the pseudo counters, even the ones that do not
            # participate directly in the acquisition
            for pseudo_elem in elem.get_pseudo_elements():
                pseudo_elem.clear_value_buffer()

        if acq_mode is AcqMode.Timer:
            value = synchronization.active_time
        repetitions = synchronization.repetitions
        latency_time = 0

        # starting continuous acquisition only if there are any controllers
        acq_sync_hw = [AcqSynch.HardwareTrigger, AcqSynch.HardwareStart,
                       AcqSynch.HardwareGate]
        ctrls_acq_hw = config.get_timerable_ctrls(acq_synch=acq_sync_hw,
                                                  enabled=True)


        if len(ctrls_acq_hw):
            self._hw_acq.run(conf_ctrls=ctrls_acq_hw,
                             value=value,
                             repetitions=repetitions,
                             latency_time=latency_time)

        # starting software acquisition only if there are any controller
        acq_sync_sw = [AcqSynch.SoftwareGate, AcqSynch.SoftwareTrigger]
        ctrls_acq_sw = config.get_timerable_ctrls(acq_synch=acq_sync_sw,
                                                  enabled=True)
        ctrls_acq_0d = config.get_zerod_ctrls(enabled=True)

        if len(ctrls_acq_sw) or len(ctrls_acq_0d):
            self._synch.add_listener(self)
            if len(ctrls_acq_sw):
                master = None
                if acq_mode is AcqMode.Timer:
                    master = config.get_master_timer_software()
                elif acq_mode is AcqMode.Monitor:
                    master = config.get_master_monitor_software()

                sw_acq_kwargs = dict(conf_ctrls=ctrls_acq_sw,
                                     value=value,
                                     repetitions=1,
                                     latency_time=latency_time,
                                     master=master)
                self.set_sw_config(sw_acq_kwargs)
            if len(ctrls_acq_0d):
                zerod_acq_kwargs = dict(conf_ctrls=ctrls_acq_0d)
                self.set_0d_config(zerod_acq_kwargs)

        #start the synchonization action
        ctrls_synch = config.get_synch_ctrls(enabled=True)
        self._synch.run(conf_ctrls=ctrls_synch,
                        synchronization=synchronization,
                        moveable=moveable,
                        sw_synch_initial_domain=sw_synch_initial_domain)

    def _get_action_for_element(self, element):
        elem_type = element.get_type()
        if elem_type in TYPE_TIMERABLE_ELEMENTS:
            config = self.main_element.configuration
            acq_synch = config.get_acq_synch_by_channel(element)
            if acq_synch in (AcqSynch.SoftwareTrigger,
                             AcqSynch.SoftwareGate):
                return self._sw_acq
            elif acq_synch in (AcqSynch.HardwareTrigger,
                               AcqSynch.HardwareGate):
                return self._hw_acq
            else:
                # by default software synchronization is in use
                return self._sw_acq
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
        return (self._hw_acq.get_elements() + self._sw_acq.get_elements() +
                self._0d_acq.get_elements() + self._synch.get_elements())

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


class Channel(PoolActionItem):

    def __init__(self, acquirable, info=None):
        PoolActionItem.__init__(self, acquirable)
        if info:
            self.__dict__.update(info)

    def __getattr__(self, name):
        return getattr(self.element, name)


class PoolAcquisitionBase(PoolAction):
    """Base class for acquisitions with a generic start_action method.

    .. note::
        The PoolAcquisitionBase class has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the module) may occur if
        deemed necessary by the core developers.
    """

    def __init__(self, main_element, name):
        PoolAction.__init__(self, main_element, name)
        self._channels = []
        self._index = None
        self._nb_states_per_value = None
        self._acq_sleep_time = None
        self._pool_ctrl_dict_loop = None

        # TODO: for the moment we can not clear value buffers at the end of
        # the acquisition. This is because of the pseudo counters that are
        # based on channels synchronized by hardware and software.
        # These two acquisition actions finish at different moment so the
        # pseudo counter will loose the value buffer of some of its physicals
        # if we clear the buffer at the end.
        # Whenever there will be solution for that, after refactoring of the
        # acquisition actions, uncomment this line
        # self.add_finish_hook(self.clear_value_buffers, True)

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
    def start_action(self, conf_ctrls, value, repetitions=1, latency=0,
                     master=None, index=None, acq_sleep_time=None,
                     nb_states_per_value=None, *args,
                     **kwargs):
        """
        Prepares everything for acquisition and starts it
        :param conf_ctrls: List of enabled controllers
        :type conf_ctrls: list
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
            conf_ctrls.remove(master.controller)
            conf_ctrls.append(master.controller)

        # controllers that will be read at during the action
        self._set_pool_ctrl_dict_loop(conf_ctrls)

        # channels that are acquired (only enabled)
        self._channels = []

        def load(conf_channel, value, repetitions, latency=0):
            axis = conf_channel.axis
            pool_ctrl = conf_channel.controller
            ctrl = pool_ctrl.ctrl
            ctrl.PreLoadAll()
            try:
                res = ctrl.PreLoadOne(axis, value, repetitions,
                                      latency)
            except TypeError:
                try:
                    res = ctrl.PreLoadOne(axis, value, repetitions)
                    msg = ("PreLoadOne(axis, value, repetitions) is "
                           "deprecated since version Jan19. Use PreLoadOne("
                           "axis, value, repetitions, latency_time) instead.")
                    self.warning(msg)
                except TypeError:
                    res = ctrl.PreLoadOne(axis, value)
                    msg = ("PreLoadOne(axis, value) is deprecated since "
                           "version 2.3.0. Use PreLoadOne(axis, value, "
                           "repetitions, latency_time) instead.")
                    self.warning(msg)
            if not res:
                msg = ("%s.PreLoadOne(%d) returned False" %
                       (pool_ctrl.name, axis))
                raise Exception(msg)
            try:
                ctrl.LoadOne(axis, value, repetitions, latency)
            except TypeError:
                try:
                    ctrl.LoadOne(axis, value, repetitions)
                    msg = ("LoadOne(axis, value, repetitions) is deprecated "
                           "since version Jan18. Use LoadOne(axis, value, "
                           "repetitions, latency_time) instead.")
                    self.warning(msg)
                except TypeError:
                    ctrl.LoadOne(axis, value)
                    msg = ("LoadOne(axis, value) is deprecated since "
                           "version 2.3.0. Use LoadOne(axis, value, "
                           "repetitions) instead.")
                    self.warning(msg)
            ctrl.LoadAll()

        with ActionContext(self):
            # PreLoadAll, PreLoadOne, LoadOne and LoadAll
            for conf_ctrl in conf_ctrls:
                # TODO find solution for master now sardana only use timer
                load(conf_ctrl.timer, value, repetitions, latency)

            # TODO: remove when the action allows to use tango attributes
            try:
                conf_ctrls.pop('__tango__')
            except Exception:
                pass

            # PreStartAll on all enabled controllers
            for conf_ctrl in conf_ctrls:
                conf_ctrl.ctrl.PreStartAll()

            # PreStartOne & StartOne on all enabled elements
            for conf_ctrl in conf_ctrls:
                conf_channels = conf_ctrl.get_channels(enabled=True)

                # make sure that the master timer/monitor is started as the
                # last one
                conf_channels.remove(conf_ctrl.timer)
                conf_channels.append(conf_ctrl.timer)
                for conf_channel in conf_channels:
                    axis = conf_channel.axis
                    ret = conf_ctrl.ctrl.PreStartOne(axis, value)
                    if not ret:
                        msg = ("%s.PreStartOne(%d) returns False" %
                               (conf_ctrl.name, axis))
                        raise Exception(msg)
                    try:
                        conf_ctrl.ctrl.StartOne(axis, value)
                    except Exception as e:
                        self.debug(e, exc_info=True)
                        conf_channel.set_state(State.Fault, propagate=2)
                        msg = ("%s.StartOne(%d) failed" %
                               (conf_ctrl.name, axis))
                        raise Exception(msg)

                    self._channels.append(conf_channel)

            # set the state of all elements to  and inform their listeners
            for conf_channel in self._channels:
                conf_channel.set_state(State.Moving, propagate=2)

            # StartAll on all enabled controllers
            for conf_ctrl in conf_ctrls:
                try:
                    conf_ctrl.ctrl.StartAll()
                except Exception as e:
                    conf_channels = conf_ctrl.get_channels(enabled=True)
                    self.debug(e, exc_info=True)
                    for conf_channel in conf_channels:
                        conf_channel.set_state(State.Fault, propagate=2)
                    msg = ("%s.StartAll() failed" % conf_ctrl.name)
                    raise Exception(msg)

    def _set_pool_ctrl_dict_loop(self, conf_ctrls):
        ctrl_channels = {}
        for conf_ctrl in conf_ctrls:
            pool_channels = []
            pool_ctrl = conf_ctrl.element
            # TODO: filter 1D and 2D for software synchronize acquisition
            for conf_channel in conf_ctrl.get_channels(enabled=True):
                pool_channels.append(conf_channel.element)
            ctrl_channels[pool_ctrl] = pool_channels
        self._pool_ctrl_dict_loop = ctrl_channels

    def clear_value_buffers(self):
        for channel in self._channels:
            channel.clear_value_buffer()


class PoolAcquisitionHardware(PoolAcquisitionBase):
    """Acquisition action for controllers synchronized by hardware

    .. note::
        The PoolAcquisitionHardware class has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the module) may occur if
        deemed necessary by the core developers.
    """

    def __init__(self, main_element, name="AcquisitionHardware"):
        PoolAcquisitionBase.__init__(self, main_element, name)

    @DebugIt()
    def action_loop(self):
        i = 0

        states, values = {}, {}
        for channel in self._channels:
            element = channel.element
            states[element] = None
            values[element] = None

        nap = self._acq_sleep_time
        nb_states_per_value = self._nb_states_per_value

        while True:
            self.read_state_info(ret=states)
            if not self.in_acquisition(states):
                break

            # read value every n times
            if not i % nb_states_per_value:
                self.read_value_loop(ret=values)
                for acquirable, value in values.items():
                    if is_value_error(value):
                        self.error("Loop read value error for %s" %
                                   acquirable.name)
                        acquirable.put_value(value)
                    else:
                        acquirable.extend_value_buffer(value)

            time.sleep(nap)
            i += 1

        with ActionContext(self):
            self.raw_read_state_info(ret=states)
            self.raw_read_value_loop(ret=values)

        for acquirable, state_info in states.items():
            # first update the element state so that value calculation
            # that is done after takes the updated state into account
            acquirable.set_state_info(state_info, propagate=0)
            if acquirable in values:
                value = values[acquirable]
                if is_value_error(value):
                    self.error("Loop final read value error for: %s" %
                               acquirable.name)
                    acquirable.put_value(value)
                else:
                    acquirable.extend_value_buffer(value, propagate=2)
            with acquirable:
                acquirable.clear_operation()
                state_info = acquirable._from_ctrl_state_info(state_info)
                acquirable.set_state_info(state_info, propagate=2)


class PoolAcquisitionSoftware(PoolAcquisitionBase):
    """Acquisition action for controllers synchronized by software

    .. note::
        The PoolAcquisitionSoftware class has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the module) may occur if
        deemed necessary by the core developers.
    """

    def __init__(self, main_element, name="AcquisitionSoftware", slaves=None):
        PoolAcquisitionBase.__init__(self, main_element, name)

        if slaves is None:
            slaves = ()
        self._slaves = slaves

    @DebugIt()
    def action_loop(self):
        states, values = {}, {}
        for channel in self._channels:
            element = channel.element
            states[element] = None
            values[element] = None

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
                for acquirable, value in values.items():
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

        for acquirable, state_info in states.items():
            # first update the element state so that value calculation
            # that is done after takes the updated state into account
            acquirable.set_state_info(state_info, propagate=0)
            if acquirable in values:
                value = values[acquirable]
                if is_value_error(value):
                    self.error("Loop final read value error for: %s" %
                               acquirable.name)
                acquirable.append_value_buffer(value, self._index)
            with acquirable:
                acquirable.clear_operation()
                state_info = acquirable._from_ctrl_state_info(state_info)
                acquirable.set_state_info(state_info, propagate=2)


class PoolAcquisitionSoftwareStart(PoolAcquisitionBase):
    """Acquisition action for controllers synchronized by software start

    .. note::
        The PoolAcquisitionSoftwareStart class has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the module) may occur if
        deemed necessary by the core developers.
    """

    def __init__(self, main_element, name="AcquisitionSoftwareStart"):
        PoolAcquisitionBase.__init__(self, main_element, name)

    @DebugIt()
    def action_loop(self):
        i = 0

        states, values = {}, {}
        for channel in self._channels:
            element = channel.element
            states[element] = None
            values[element] = None

        nap = self._acq_sleep_time
        nb_states_per_value = self._nb_states_per_value

        while True:
            self.read_state_info(ret=states)
            if not self.in_acquisition(states):
                break

            # read value every n times
            if not i % nb_states_per_value:
                self.read_value_loop(ret=values)
                for acquirable, value in values.items():
                    if is_value_error(value):
                        self.error("Loop read value error for %s" %
                                   acquirable.name)
                        acquirable.put_value(value)
                    else:
                        acquirable.extend_value_buffer(value)

            time.sleep(nap)
            i += 1

        with ActionContext(self):
            self.raw_read_state_info(ret=states)
            self.raw_read_value_loop(ret=values)

        for acquirable, state_info in states.items():
            # first update the element state so that value calculation
            # that is done after takes the updated state into account
            acquirable.set_state_info(state_info, propagate=0)
            if acquirable in values:
                value = values[acquirable]
                if is_value_error(value):
                    self.error("Loop final read value error for: %s" %
                               acquirable.name)
                    acquirable.put_value(value)
                else:
                    acquirable.extend_value_buffer(value, propagate=2)
            with acquirable:
                acquirable.clear_operation()
                state_info = acquirable._from_ctrl_state_info(state_info)
                acquirable.set_state_info(state_info, propagate=2)


class PoolCTAcquisition(PoolAcquisitionBase):

    def __init__(self, main_element, name="CTAcquisition", slaves=None):
        self._channels = None

        if slaves is None:
            slaves = ()
        self._slaves = slaves

        PoolAcquisitionBase.__init__(self, main_element, name)

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
            for acquirable, value in values.items():
                acquirable.put_value(value, propagate=2)

        while True:
            self.read_state_info(ret=states)
            if not self.in_acquisition(states):
                break

            # read value every n times
            if not i % nb_states_per_value:
                self.read_value_loop(ret=values)
                for acquirable, value in values.items():
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

        for acquirable, state_info in states.items():
            # first update the element state so that value calculation
            # that is done after takes the updated state into account
            acquirable.set_state_info(state_info, propagate=0)
            if acquirable in values:
                value = values[acquirable]
                acquirable.put_value(value, propagate=2)
            with acquirable:
                acquirable.clear_operation()
                state_info = acquirable._from_ctrl_state_info(state_info)
                acquirable.set_state_info(state_info, propagate=2)


class Pool0DAcquisition(PoolAction):

    def __init__(self, main_element, name="0DAcquisition"):
        self._channels = None
        self._index = None
        PoolAction.__init__(self, main_element, name)

    def start_action(self, conf_ctrls, index=None, acq_sleep_time=None,
                     nb_states_per_value=None, *args, **kwargs):
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
            for acquirable, value in values.items():
                acquirable.put_current_value(value, propagate=0)
            if self._stopped or self._aborted:
                break
            time.sleep(nap)

        for element in self._channels:
            value = element.accumulated_value.value_obj
            element.append_value_buffer(value, self._index, propagate=2)

        with ActionContext(self):
            self.raw_read_state_info(ret=states)

        for acquirable, state_info in states.items():
            # first update the element state so that value calculation
            # that is done after takes the updated state into account
            state_info = acquirable._from_ctrl_state_info(state_info)
            acquirable.set_state_info(state_info, propagate=0)
            with acquirable:
                acquirable.clear_operation()
                acquirable.set_state_info(state_info, propagate=2)

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
        for acquirable, value in values.items():
            acquirable.put_value(value, propagate=2)

        while True:
            self.read_state_info(ret=states)

            if not self.in_acquisition(states):
                break

            # read value every n times
            if not i % 5:
                self.read_value(ret=values)
                for acquirable, value in values.items():
                    acquirable.put_value(value)

            i += 1
            time.sleep(0.01)

        self.read_state_info(ret=states)

        # first update the element state so that value calculation
        # that is done after takes the updated state into account
        for acquirable, state_info in states.items():
            acquirable.set_state_info(state_info, propagate=0)

        # Do NOT send events before we exit the OperationContext, otherwise
        # we may be asked to start another action before we leave the context
        # of the current action. Instead, send the events in the finish hook
        # which is executed outside the OperationContext

        def finish_hook(*args, **kwargs):
            # read values and propagate the change to all listeners
            self.read_value(ret=values)
            for acquirable, value in values.items():
                acquirable.put_value(value, propagate=2)

            # finally set the state and propagate to all listeners
            for acquirable, state_info in states.items():
                acquirable.set_state_info(state_info, propagate=2)

        self.set_finish_hook(finish_hook)
