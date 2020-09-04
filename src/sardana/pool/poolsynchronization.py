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


"""This module is part of the Python Pool library. It defines the classes
for the synchronization"""

__all__ = ["PoolSynchronization", "SynchDescription", "TGChannel"]

import time
import threading
from functools import partial
from taurus.core.util.log import DebugIt
from sardana import State
from sardana.sardanathreadpool import get_thread_pool
from sardana.pool.pooldefs import SynchDomain, SynchParam
from sardana.pool.poolaction import ActionContext, PoolActionItem, PoolAction
from sardana.util.funcgenerator import FunctionGenerator

# The purpose of this class was inspired on the CTAcquisition concept


class TGChannel(PoolActionItem):
    """An item involved in the trigger/gate generation.
    Maps directly to a trigger object

    .. note::
        The TGChannel class has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the module) may occur if
        deemed necessary by the core developers.
    """

    def __init__(self, trigger_gate, info=None):
        PoolActionItem.__init__(self, trigger_gate)
        if info:
            self.__dict__.update(info)

    def __getattr__(self, name):
        return getattr(self.element, name)


class SynchDescription(list):
    """Synchronization description. It is composed from groups - repetitions
    of equidistant synchronization events. Each group is described by
    :class:`~sardana.pool.pooldefs.SynchParam` parameters which may have
    values in :class:`~sardana.pool.pooldefs.SynchDomain` domains.
    """

    @property
    def repetitions(self):
        repetitions = 0
        for group in self:
            repetitions += group[SynchParam.Repeats]
        return repetitions

    @property
    def active_time(self):
        return self._get_param(SynchParam.Active)

    @property
    def total_time(self):
        return self._get_param(SynchParam.Total)

    @property
    def passive_time(self):
        return self.total_time - self.active_time

    def _get_param(self, param, domain=SynchDomain.Time):
        """
        Extract parameter from synchronization description and its groups. If
        there is only one group in the synchronization description then
        returns float with the value. Otherwise a list of floats with
        different values.

        :param param: parameter type
        :type param: :class:`~sardana.pool.pooldefs.SynchParam`
        :param domain: domain
        :type param: :class:`~sardana.pool.pooldefs.SynchDomain`
        :return: parameter value(s)
        :rtype float or [float]
        """

        if len(self) == 1:
            return self[0][param][domain]

        values = []
        for group in self:
            value = group[param][domain]
            repeats = group[SynchParam.Repeats]
            values += [value] * repeats
        return values


class PoolSynchronization(PoolAction):
    """Synchronization action.

    It coordinates trigger/gate elements and software synchronizer.

    .. todo: Think of moving the ready/busy mechanism to PoolAction
    """

    def __init__(self, main_element, name="Synchronization"):
        PoolAction.__init__(self, main_element, name)
        # Even if rest of Sardana is using "." in logger names use "-" as
        # sepator. This is in order to avoid confusion about the logger
        # hierary - by default python logging use "." to indicate loggers'
        # hirarchy in case parent-children relation is established between the
        # loggers.
        # TODO: review if it is possible in Sardana to use a common separator.
        soft_synch_name = main_element.name + "-SoftSynch"
        self._synch_soft = FunctionGenerator(name=soft_synch_name)
        self._listener = None
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

    def add_listener(self, listener):
        self._listener = listener

    def start_action(self, ctrls, synch_description, moveable=None,
                     sw_synch_initial_domain=None, *args, **kwargs):
        """Start synchronization action.

        :param ctrls: list of enabled trigger/gate controllers
        :type ctrls: list
        :param synch_description: synchronization description
        :type synch_description:
         :class:`~sardana.pool.poolsynchronization.SynchDescription`
        :param moveable: (optional) moveable object used as the
         synchronization source in the Position domain
        :type moveable: :class:`~sardna.pool.poolmotor.PoolMotor` or
         :class:`~sardana.pool.poolpseudomotor.PoolPseudoMotor`
        :param sw_synch_initial_domain: (optional) - initial domain for
         software synchronizer, can be either
         :obj:`~sardana.pool.pooldefs.SynchDomain.Time` or
         :obj:`~sardana.pool.pooldefs.SynchDomain.Position`
        """
        with ActionContext(self):

            # loads synchronization description
            for ctrl in ctrls:
                pool_ctrl = ctrl.element
                pool_ctrl.ctrl.PreSynchAll()
                for channel in ctrl.get_channels(enabled=True):
                    axis = channel.axis
                    ret = pool_ctrl.ctrl.PreSynchOne(axis, synch_description)
                    if not ret:
                        msg = ("%s.PreSynchOne(%d) returns False" %
                               (ctrl.name, axis))
                        raise Exception(msg)
                    pool_ctrl.ctrl.SynchOne(axis, synch_description)
                pool_ctrl.ctrl.SynchAll()

            # attaching listener (usually acquisition action)
            # to the software trigger gate generator
            if self._listener is not None:
                if sw_synch_initial_domain is not None:
                    self._synch_soft.initial_domain = sw_synch_initial_domain
                self._synch_soft.set_configuration(synch_description)
                self._synch_soft.add_listener(self._listener)
                remove_acq_listener = partial(self._synch_soft.remove_listener,
                                              self._listener)
                self.add_finish_hook(remove_acq_listener, False)
                self._synch_soft.add_listener(
                    self.main_element.on_element_changed)
                remove_mg_listener = partial(self._synch_soft.remove_listener,
                                             self.main_element)
                self.add_finish_hook(remove_mg_listener, False)
            # subscribing to the position change events to generate events
            # in position domain
            if moveable is not None:
                position = moveable.get_position_attribute()
                position.add_listener(self._synch_soft)
                remove_pos_listener = partial(position.remove_listener,
                                              self._synch_soft)
                self.add_finish_hook(remove_pos_listener, False)

            # start software synchronizer
            if self._listener is not None:
                self._synch_soft.start()
                get_thread_pool().add(self._synch_soft.run)

            # PreStartAll on all controllers
            for ctrl in ctrls:
                pool_ctrl = ctrl.element
                pool_ctrl.ctrl.PreStartAll()

            # PreStartOne & StartOne on all elements
            for ctrl in ctrls:
                pool_ctrl = ctrl.element
                for channel in ctrl.get_channels(enabled=True):
                    axis = channel.axis
                    ret = pool_ctrl.ctrl.PreStartOne(axis)
                    if not ret:
                        raise Exception("%s.PreStartOne(%d) returns False"
                                        % (pool_ctrl.name, axis))
                    pool_ctrl.ctrl.StartOne(axis)

            # set the state of all elements to inform their listeners
            self._channels = []
            for ctrl in ctrls:
                for channel in ctrl.get_channels(enabled=True):
                    channel.set_state(State.Moving, propagate=2)
                    self._channels.append(channel)

            # StartAll on all controllers
            for ctrl in ctrls:
                pool_ctrl = ctrl.element
                pool_ctrl.ctrl.StartAll()

    def is_triggering(self, states):
        """Determines if we are synchronizing or not based on the states
        returned by the controller(s) and the software synchronizer.

        :param states: a map containing state information as returned by
                       read_state_info: ((state, status), exception_error)
        :type states: dict<PoolElement, tuple(tuple(int, str), str))
        :return: returns True if is triggering or False otherwise
        :rtype: bool
        """
        for elem in states:
            state_info_idx = 0
            state_idx = 0
            state_tggate = states[elem][state_info_idx][state_idx]
            if self._is_in_action(state_tggate):
                return True
        return False

    @DebugIt()
    def action_loop(self):
        """action_loop method
        """
        states = {}
        for channel in self._channels:
            element = channel.element
            states[element] = None

        # Triggering loop
        # TODO: make nap configurable (see motion or acquisition loops)
        nap = 0.01
        while True:
            self.read_state_info(ret=states)
            if not self.is_triggering(states):
                break
            time.sleep(nap)

        # Set element states after ending the triggering
        for element, state_info in list(states.items()):
            with element:
                element.clear_operation()
                state_info = element._from_ctrl_state_info(state_info)
                element.set_state_info(state_info, propagate=2)

        # wait for software synchronizer to finish
        if self._listener is not None:
            while True:
                if not self._synch_soft.is_started():
                    break
                time.sleep(0.01)
