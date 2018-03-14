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


def split_MGConfigurations(mg_cfg_in):
    """Split MeasurementGroup configuration with channels
    triggered by SW Trigger and channels triggered by HW trigger

    TODO: (technical debt) All the MeasurementGroup configuration
    logic should be encapsulate in a dedicated class instead of
    using a basic data structures like dict or lists...
    """
    ctrls_in = mg_cfg_in['controllers']
    mg_sw_cfg_out = {}
    mg_0d_cfg_out = {}
    mg_hw_cfg_out = {}
    mg_sw_cfg_out['controllers'] = ctrls_sw_out = {}
    mg_0d_cfg_out['controllers'] = ctrls_0d_out = {}
    mg_hw_cfg_out['controllers'] = ctrls_hw_out = {}
    for ctrl, ctrl_info in ctrls_in.items():
        external = isinstance(ctrl, str) and ctrl.startswith('__')
        # skipping external controllers e.g. Tango attributes
        if external:
            continue
        # splitting ZeroD based on the type
        if ctrl.get_ctrl_types()[0] == ElementType.ZeroDExpChannel:
            ctrls_0d_out[ctrl] = ctrl_info
        # ignoring PseudoCounter
        elif ctrl.get_ctrl_types()[0] == ElementType.PseudoCounter:
            pass
        # splitting rest of the channels based on the assigned trigger
        else:
            synchronizer = ctrl_info.get('synchronizer')
            if synchronizer is None or synchronizer == 'software':
                ctrls_sw_out[ctrl] = ctrl_info
            else:
                ctrls_hw_out[ctrl] = ctrl_info

    def find_master(ctrls, role):
        master_idx = float("+inf")
        master = None
        for ctrl_info in ctrls.values():
            element = ctrl_info[role]
            element_idx = ctrl_info["channels"][element]["index"]
            element_enabled = ctrl_info["channels"][element]["enabled"]
            # Find master only if is enabled
            if element_idx < master_idx and element_enabled:
                master = element
                master_idx = element_idx
        return master

    if len(ctrls_sw_out):
        mg_sw_cfg_out["timer"] = find_master(ctrls_sw_out, "timer")
        mg_sw_cfg_out["monitor"] = find_master(ctrls_sw_out, "monitor")
    if len(ctrls_hw_out):
        mg_hw_cfg_out["timer"] = find_master(ctrls_hw_out, "timer")
        mg_hw_cfg_out["monitor"] = find_master(ctrls_hw_out, "monitor")
    return (mg_hw_cfg_out, mg_sw_cfg_out, mg_0d_cfg_out)


def getTGConfiguration(MGcfg):
    '''Build TG configuration from complete MG configuration.

    TODO: (technical debt) All the MeasurementGroup configuration
    logic should be encapsulate in a dedicated class instead of
    using a basic data structures like dict or lists...

    :param MGcfg: configuration dictionary of the whole Measurement Group.
    :type MGcfg: dict<>
    :return: a configuration dictionary of TG elements organized by controller
    :rtype: dict<>
    '''

    # Create list with not repeated elements
    _tg_element_list = []

    for ctrl in MGcfg["controllers"]:
        tg_element = MGcfg["controllers"][ctrl].get('synchronizer', None)
        if (tg_element is not None and
                tg_element != "software" and
                tg_element not in _tg_element_list):
            _tg_element_list.append(tg_element)

    # Intermediate dictionary to organize each ctrl with its elements.
    ctrl_tgelem_dict = {}
    for tgelem in _tg_element_list:
        tg_ctrl = tgelem.get_controller()
        if tg_ctrl not in ctrl_tgelem_dict.keys():
            ctrl_tgelem_dict[tg_ctrl] = [tgelem]
        else:
            ctrl_tgelem_dict[tg_ctrl].append(tgelem)

    # Build TG configuration dictionary.
    TGcfg = {}
    TGcfg['controllers'] = {}

    for ctrl in ctrl_tgelem_dict:
        TGcfg['controllers'][ctrl] = ctrls = {}
        ctrls['channels'] = {}
        for tg_elem in ctrl_tgelem_dict[ctrl]:
            ch = ctrls['channels'][tg_elem] = {}
            ch['full_name'] = tg_elem.full_name
    # TODO: temporary returning tg_elements
    return TGcfg, _tg_element_list


def extract_integ_time(synchronization):
    """Extract integration time(s) from synchronization dict. If there is only
    one group in the synchronization than returns float with the integration
    time. Otherwise a list of floats with different integration times.

    TODO: (technical debt) All the MeasurementGroup synchronization
    logic should be encapsulate in a dedicated class instead of
    using a basic data structures like dict or lists...

    :param synchronization: group(s) where each group is described by
        SynchParam(s)
    :type synchronization: list(dict)
    :return list(float) or float
    """
    if len(synchronization) == 1:
        integ_time = synchronization[0][SynchParam.Active][SynchDomain.Time]
    else:
        integ_time = []
        for group in synchronization:
            active_time = group[SynchParam.Active][SynchDomain.Time]
            repeats = group[SynchParam.Repeats]
            integ_time += [active_time] * repeats
    return integ_time


def extract_repetitions(synchronization):
    """Extract repetitions from synchronization dict.

    TODO: (technical debt) All the MeasurementGroup synchronization
    logic should be encapsulate in a dedicated class instead of
    using a basic data structures like dict or lists...

    :param synchronization: group(s) where each group is described by
        SynchParam(s)
    :type synchronization: list(dict)
    :return: number of repetitions
    :rtype: int
    """
    repetitions = 0
    for group in synchronization:
        repetitions += group[SynchParam.Repeats]
    return repetitions


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
        config = kwargs['config']
        synchronization = kwargs["synchronization"]
        integ_time = extract_integ_time(synchronization)
        repetitions = extract_repetitions(synchronization)
        # TODO: this code splits the global mg configuration into
        # experimental channels triggered by hw and experimental channels
        # triggered by sw. Refactor it!!!!
        (hw_acq_cfg, sw_acq_cfg, zerod_acq_cfg) = split_MGConfigurations(
            config)
        synch_cfg, _ = getTGConfiguration(config)
        # starting continuous acquisition only if there are any controllers
        if len(hw_acq_cfg['controllers']):
            cont_acq_kwargs = dict(kwargs)
            cont_acq_kwargs['config'] = hw_acq_cfg
            cont_acq_kwargs['integ_time'] = integ_time
            cont_acq_kwargs['repetitions'] = repetitions
            self._hw_acq.run(*args, **cont_acq_kwargs)
        if len(sw_acq_cfg['controllers']) or len(zerod_acq_cfg['controllers']):
            self._synch.add_listener(self)
            if len(sw_acq_cfg['controllers']):
                sw_acq_kwargs = dict(kwargs)
                sw_acq_kwargs['config'] = sw_acq_cfg
                sw_acq_kwargs['integ_time'] = integ_time
                sw_acq_kwargs['repetitions'] = 1
                self.set_sw_config(sw_acq_kwargs)
            if len(zerod_acq_cfg['controllers']):
                zerod_acq_kwargs = dict(kwargs)
                zerod_acq_kwargs['config'] = zerod_acq_cfg
                self.set_0d_config(zerod_acq_kwargs)
        synch_kwargs = dict(kwargs)
        synch_kwargs['config'] = synch_cfg
        self._synch.run(*args, **synch_kwargs)

    def _get_action_for_element(self, element):
        elem_type = element.get_type()
        if elem_type in TYPE_TIMERABLE_ELEMENTS:
            main_element = self.main_element
            channel_to_acq_synch = main_element._channel_to_acq_synch
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
        self._channels = None
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
        """
        pool = self.pool

        self._aborted = False
        self._stopped = False

        self._acq_sleep_time = kwargs.pop("acq_sleep_time",
                                          pool.acq_loop_sleep_time)
        self._nb_states_per_value = kwargs.pop("nb_states_per_value",
                                               pool.acq_loop_states_per_value)

        self._integ_time = integ_time = kwargs.get("integ_time")
        self._mon_count = mon_count = kwargs.get("monitor_count")
        self._repetitions = repetitions = kwargs.get("repetitions")
        if integ_time is None and mon_count is None:
            raise Exception("must give integration time or monitor counts")
        if integ_time is not None and mon_count is not None:
            msg = ("must give either integration time or monitor counts "
                   "(not both)")
            raise Exception(msg)

        _ = kwargs.get("items", self.get_elements())
        cfg = kwargs['config']
        # determine which is the controller which holds the master channel

        if integ_time is not None:
            master_key = 'timer'
            master_value = integ_time
        if mon_count is not None:
            master_key = 'monitor'
            master_value = -mon_count
        master = cfg[master_key]
        if master is None:
            self.main_element.set_state(State.Fault, propagate=2)
            msg = "master {0} is unknown (probably disabled)".format(
                master_key)
            raise RuntimeError(msg)
        master_ctrl = master.controller

        pool_ctrls_dict = dict(cfg['controllers'])
        pool_ctrls_dict.pop('__tango__', None)

        # controllers to be started (only enabled) in the right order
        pool_ctrls = []
        # controllers that will be read at the end of the action
        self._pool_ctrl_dict_loop = _pool_ctrl_dict_loop = {}
        # channels that are acquired (only enabled)
        self._channels = channels = {}

        # select only suitable e.g. enabled, timerable controllers & channels
        for ctrl, pool_ctrl_data in pool_ctrls_dict.items():
            # skip not timerable controllers e.g. 0D
            if not ctrl.is_timerable():
                continue
            ctrl_enabled = False
            elements = pool_ctrl_data['channels']
            for element, element_info in elements.items():
                # skip disabled elements
                if not element_info['enabled']:
                    continue
                # Add only the enabled channels
                channel = Channel(element, info=element_info)
                channels[element] = channel
                ctrl_enabled = True
            # check if the ctrl has enabled channels
            if ctrl_enabled:
                # enabled controller can no be offline
                if not ctrl.is_online():
                    self.main_element.set_state(State.Fault, propagate=2)
                    msg = "controller {0} is offline".format(ctrl.name)
                    raise RuntimeError(msg)
                pool_ctrls.append(ctrl)
                # only CT will be read in the loop, 1D and 2D not
                if ElementType.CTExpChannel in ctrl.get_ctrl_types():
                    _pool_ctrl_dict_loop[ctrl] = pool_ctrl_data

        # timer/monitor channels can not be disabled
        for pool_ctrl in pool_ctrls:
            ctrl = pool_ctrl.ctrl
            pool_ctrl_data = pool_ctrls_dict[pool_ctrl]
            timer_monitor = pool_ctrl_data[master_key]
            if timer_monitor not in channels:
                self.main_element.set_state(State.Fault, propagate=2)
                msg = "timer/monitor ({0}) of {1} controller is "\
                      "disabled)".format(timer_monitor.name, pool_ctrl.name)
                raise RuntimeError(msg)

        # make sure the controller which has the master channel is the last to
        # be called
        pool_ctrls.remove(master_ctrl)
        pool_ctrls.append(master_ctrl)

        with ActionContext(self):
            # PreLoadAll, PreLoadOne, LoadOne and LoadAll
            for pool_ctrl in pool_ctrls:
                try:
                    ctrl = pool_ctrl.ctrl
                    pool_ctrl_data = pool_ctrls_dict[pool_ctrl]
                    ctrl.PreLoadAll()
                    master = pool_ctrl_data[master_key]
                    axis = master.axis
                    try:
                        res = ctrl.PreLoadOne(axis, master_value, repetitions)
                    except TypeError:
                        msg = ("PreLoadOne(axis, value) is deprecated since "
                               "version 2.3.0. Use PreLoadOne(axis, value, "
                               "repetitions) instead.")
                        self.warning(msg)
                        res = ctrl.PreLoadOne(axis, master_value)
                    if not res:
                        msg = ("%s.PreLoadOne(%d) returned False" %
                               (pool_ctrl.name, axis))
                        raise Exception(msg)
                    try:
                        ctrl.LoadOne(axis, master_value, repetitions)
                    except TypeError:
                        msg = ("LoadOne(axis, value) is deprecated since "
                               "version 2.3.0. Use LoadOne(axis, value, "
                               "repetitions) instead.")
                        self.warning(msg)
                        ctrl.LoadOne(axis, master_value)
                    ctrl.LoadAll()
                except Exception, e:
                    self.debug(e, exc_info=True)
                    master.set_state(State.Fault, propagate=2)
                    msg = ("Load sequence of %s failed" % pool_ctrl.name)
                    raise Exception(msg)

            # PreStartAll on all enabled controllers
            for pool_ctrl in pool_ctrls:
                pool_ctrl.ctrl.PreStartAll()

            # PreStartOne & StartOne on all enabled elements
            for pool_ctrl in pool_ctrls:
                ctrl = pool_ctrl.ctrl
                pool_ctrl_data = pool_ctrls_dict[pool_ctrl]
                elements = pool_ctrl_data['channels'].keys()
                timer_monitor = pool_ctrl_data[master_key]
                # make sure that the timer/monitor is started as the last one
                elements.remove(timer_monitor)
                elements.append(timer_monitor)
                for element in elements:
                    try:
                        channel = channels[element]
                    except KeyError:
                        continue
                    axis = element.axis
                    ret = ctrl.PreStartOne(axis, master_value)
                    if not ret:
                        msg = ("%s.PreStartOne(%d) returns False" %
                               (pool_ctrl.name, axis))
                        raise Exception(msg)
                    try:
                        ctrl.StartOne(axis, master_value)
                    except Exception, e:
                        self.debug(e, exc_info=True)
                        element.set_state(State.Fault, propagate=2)
                        msg = ("%s.StartOne(%d) failed" %
                               (pool_ctrl.name, axis))
                        raise Exception(msg)

            # set the state of all elements to  and inform their listeners
            for channel in channels:
                channel.set_state(State.Moving, propagate=2)

            # StartAll on all enabled controllers
            for pool_ctrl in pool_ctrls:
                try:
                    pool_ctrl.ctrl.StartAll()
                except Exception, e:
                    self.debug(e, exc_info=True)
                    elements = pool_ctrl_data['channels'].keys()
                    for element in elements:
                        element.set_state(State.Fault, propagate=2)
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
        cfg = kwargs['config']

        pool_ctrls_dict = dict(cfg['controllers'])
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
