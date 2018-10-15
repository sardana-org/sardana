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
from sardana.pool import SynchParam, SynchDomain, AcqSynch
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
                    kwargs['synch'] = True
                    kwargs['idx'] = value
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
                    kwargs['synch'] = True
                    kwargs['idx'] = value
                    self._0d_acq._started = True
                    self._0d_acq._stopped = False
                    self._0d_acq._aborted = False
                    get_thread_pool().add(self._0d_acq.run, *args, **kwargs)
        elif name == "passive":
            if self._0d_config and (self._0d_acq._is_started() or
                                    self._0d_acq.is_running()):
                self.debug('Stopping ZeroD acquisition.')
                self._0d_acq.stop_action()

    def prepare(self, config, nr_of_starts):
        """Prepare measurement."""
        timers = config.sw_sync_timers_enabled + \
            config.sw_start_timers_enabled + \
            config.hw_sync_timers_enabled

        for timer in timers:
            axis = timer.axis
            timer_ctrl = timer.controller
            ctrl = timer_ctrl.ctrl
            ctrl.PrepareOne(axis, nr_of_starts)

    def is_running(self):
        return self._0d_acq.is_running() or\
            self._sw_acq.is_running() or\
            self._hw_acq.is_running() or\
            self._synch.is_running()

    def run(self, *args, **kwargs):
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

        config = self.main_element.configuration
        synchronization = kwargs["synchronization"]
        integ_time = synchronization.integration_time
        repetitions = synchronization.repetitions
        latency_time = 0
        ctrls_channels_acq_hw = config.get_ctrls_channels()
        # starting continuous acquisition only if there are any controllers
        if len(config.ctrl_hw_sync):
            cont_acq_kwargs = dict(kwargs)
            cont_acq_kwargs['integ_time'] = integ_time
            cont_acq_kwargs['repetitions'] = repetitions
            self._hw_acq.run(*args, **cont_acq_kwargs)
        if len(config.ctrl_sw_sync) or len(config.ctrl_0d_sync):
            self._synch.add_listener(self)
            if len(config.ctrl_sw_sync):
                sw_acq_kwargs = dict(kwargs)
                sw_acq_kwargs['integ_time'] = integ_time
                sw_acq_kwargs['repetitions'] = 1
                self.set_sw_config(sw_acq_kwargs)
            if len(config.ctrl_0d_sync):
                zerod_acq_kwargs = dict(kwargs)
                self.set_0d_config(zerod_acq_kwargs)
        synch_kwargs = dict(kwargs)
        self._synch.run(*args, **synch_kwargs)

    def _get_action_for_element(self, element):
        elem_type = element.get_type()
        if elem_type in TYPE_TIMERABLE_ELEMENTS:
            main_element = self.main_element
            channel_to_acq_synch = \
                main_element.configuration.channel_to_acq_synch
            acq_synch = channel_to_acq_synch.get(element)
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
    def start_action(self, ctrls_channels, ctrls_loadables, value,
                     repetitions=1, latency=0, master=None,
                     index=None, acq_sleep_time=None,
                     nb_states_per_value=None, *args,
                     **kwargs):
        """Prepares everything for acquisition and starts it.
        :param acq_sleep_time: sleep time between state queries
        :param nb_states_per_value: how many state queries between readouts
        :param integ_time: integration time(s)
        :type integ_time: float or seq<float>
        :param repetitions: repetitions
        :type repetitions: int
        :param config: configuration dictionary (with information about
            involved controllers and channels)
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


        # controllers to be started (only enabled) in the right order
        pool_ctrls = ctrls_channels.keys()

        # make sure the controller which has the master channel is the last to
        # be called
        if master is not None:
            master_ctrl = master.controller
            pool_ctrls.remove(master_ctrl)
            pool_ctrls.append(master_ctrl)

        # controllers that will be read at the end of the action
        self._pool_ctrl_dict_loop = ctrls_channels
        # channels that are acquired (only enabled)
        self._channels = []

        def load(channel, value, repetitions, latency=0):
            axis = channel.axis
            pool_ctrl = channel.controller
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
            loadables = ctrls_loadables.values()
            for channel in loadables:
                load(channel, value, repetitions, latency)

            # TODO: remove when the action allows to use tango attributes
            try:
                pool_ctrls.pop('__tango__')
            except Exception:
                pass

            # PreStartAll on all enabled controllers
            for pool_ctrl in pool_ctrls:
                pool_ctrl.ctrl.PreStartAll()

            channels_started = []
            # PreStartOne & StartOne on all enabled elements
            for pool_ctrl in pool_ctrls:
                channels = ctrls_channels[pool_ctrl]
                ctrl = pool_ctrl.ctrl

                # make sure that the timer/monitor is started as the last one
                loadable = ctrls_loadables[pool_ctrl]
                channels.remove(loadable)
                channels.append(loadable)
                for channel in channels:
                    axis = channel.axis
                    ret = ctrl.PreStartOne(axis, value)
                    if not ret:
                        msg = ("%s.PreStartOne(%d) returns False" %
                               (pool_ctrl.name, axis))
                        raise Exception(msg)
                    try:
                        ctrl.StartOne(axis, value)
                    except Exception, e:
                        self.debug(e, exc_info=True)
                        channel.set_state(State.Fault, propagate=2)
                        msg = ("%s.StartOne(%d) failed" %
                               (pool_ctrl.name, axis))
                        raise Exception(msg)

                    self._channels.append(channel)

            # set the state of all elements to  and inform their listeners
            for channel in self._channels:
                channel.set_state(State.Moving, propagate=2)

            # StartAll on all enabled controllers
            for pool_ctrl in pool_ctrls:
                channels = ctrls_channels[pool_ctrl]
                try:
                    pool_ctrl.ctrl.StartAll()
                except Exception, e:
                    self.debug(e, exc_info=True)
                    for channel in channels:
                        channel.set_state(State.Fault, propagate=2)
                    msg = ("%s.StartAll() failed" % pool_ctrl.name)
                    raise Exception(msg)

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
        for element in self._channels:
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
    def start_action(self, *args, **kwargs):
        """Prepares everything for acquisition and starts it.
        :param acq_sleep_time: sleep time between state queries
        :param nb_states_per_value: how many state queries between readouts
        :param integ_time: integration time(s)
        :type integ_time: float or seq<float>
        :param repetitions: repetitions
        :type repetitions: int
        :param config: configuration dictionary (with information about
            involved controllers and channels)
        :param index: trigger index that will be assigned to the acquired value
        :type index: int
        """

        PoolAcquisitionBase.start_action(self, *args, **kwargs)
        self.index = kwargs.get("idx")

    @DebugIt()
    def action_loop(self):
        states, values = {}, {}
        for element in self._channels:
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
                acquirable.append_value_buffer(value, self.index)
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
        PoolAction.__init__(self, main_element, name)

    def start_action(self, *args, **kwargs):
        """Prepares everything for acquisition and starts it.

           :param: config"""

        pool = self.pool

        self._index = kwargs.get("idx")

        # prepare data structures
        # TODO: rollback this change when a proper synchronization between
        # acquisition actions will be develop.
        # Now the meta acquisition action is resettung them to 0.
#         self._aborted = False
#         self._stopped = False

        self._acq_sleep_time = kwargs.pop("acq_sleep_time",
                                          pool.acq_loop_sleep_time)
        self._nb_states_per_value = \
            kwargs.pop("nb_states_per_value",
                       pool.acq_loop_states_per_value)

        items = kwargs.get("items")
        if items is None:
            items = self.get_elements()
        cfg = self.main_element.configuration

        pool_ctrls_dict = dict(cfg.ctrl_0d_sync)
        pool_ctrls_dict.pop('__tango__', None)
        pool_ctrls = []
        for ctrl in pool_ctrls_dict:
            if ElementType.ZeroDExpChannel in ctrl.get_ctrl_types():
                pool_ctrls.append(ctrl)

        # Determine which channels are active
        self._channels = channels = {}
        for pool_ctrl in pool_ctrls:
            ctrl = pool_ctrl.ctrl
            pool_ctrl_data = pool_ctrls_dict[pool_ctrl]
            elements = pool_ctrl_data['channels']

            for element, element_info in elements.items():
                channel = Channel(element, info=element_info)
                channels[element] = channel

        with ActionContext(self):
            # set the state of all elements to  and inform their listeners
            for channel in channels:
                channel.clear_buffer()
                channel.set_state(State.Moving, propagate=2)

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
        for element in self._channels:
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
