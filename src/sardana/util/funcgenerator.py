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

import time
import threading
import math
import copy
import numpy
import traceback

from sardana import State
from sardana.sardanaevent import EventGenerator, EventType
from sardana.pool.pooldefs import SynchParam, SynchDomain
from taurus.core.util.log import Logger


def strictly_increasing(l):
    """Check whether list l has strictly increasing values"""
    return all(x < y for x, y in zip(l, l[1:]))


def strictly_decreasing(l):
    """Check whether list l has strictly deacreasing values"""
    return all(x > y for x, y in zip(l, l[1:]))


class FunctionGenerator(EventGenerator, Logger):
    """Generator of active and passive events describing a rectangular
    function.

    .. note::
        The FunctionGenerator class has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the module) may occur if
        deemed necessary by the core developers.
    """

    MAX_NAP_TIME = 0.1

    def __init__(self, name="FunctionGenerator"):
        EventGenerator.__init__(self)
        Logger.__init__(self, name)
        self._name = name
        self._initial_domain = None
        self._active_domain = None
        self._position_event = threading.Event()
        self._position = None
        self._initial_domain_in_use = None
        self._active_domain_in_use = None
        self._active_events = list()
        self._passive_events = list()
        self._started = False
        self._stopped = False
        self._running = False
        self._start_time = None
        self._direction = None
        self._condition = None
        self._id = None
        self._start_fired = False

    def get_name(self):
        return self._name

    name = property(get_name)

    def set_initial_domain(self, domain):
        self._initial_domain = domain

    def get_initial_domain(self):
        return self._initial_domain

    initial_domain = property(get_initial_domain, set_initial_domain)

    def set_active_domain(self, domain):
        self._active_domain = domain

    def get_active_domain(self):
        return self._active_domain

    active_domain = property(get_active_domain, set_active_domain)

    def set_initial_domain_in_use(self, domain):
        self._initial_domain_in_use = domain

    def get_initial_domain_in_use(self):
        return self._initial_domain_in_use

    initial_domain_in_use = property(get_initial_domain_in_use,
                                     set_initial_domain_in_use)

    def set_active_domain_in_use(self, domain):
        self._active_domain_in_use = domain

    def get_active_domain_in_use(self):
        return self._active_domain_in_use

    active_domain_in_use = property(get_active_domain_in_use,
                                    set_active_domain_in_use)

    def add_active_event(self, event):
        self._active_events.append(event)

    def set_active_events(self, events):
        self._active_events = events

    def get_active_events(self):
        return self._active_events

    active_events = property(get_active_events, set_active_events)

    def add_passive_event(self, event):
        self._passive_events.append(event)

    def set_passive_events(self, events):
        self._passive_events = events

    def get_passive_events(self):
        return self._passive_events

    passive_events = property(get_passive_events, set_passive_events)

    def set_direction(self, direction):
        self._direction = direction
        if direction == 1:
            self._condition = numpy.greater_equal
        elif direction == -1:
            self._condition = numpy.less_equal
        else:
            raise ValueError("direction can be -1 or 1 (negative or positive)")

    def get_direction(self):
        return self._direction

    direction = property(get_direction, set_direction)

    def event_received(self, *args, **kwargs):
        _, _, v = args
        if v.error:
            exc_info = v.exc_info
            self.error("Synchronization base attribute in error")
            msg = "Details: " + "".join(traceback.format_exception(*exc_info))
            self.debug(msg)
            return
        self._position = v.value
        self._position_event.set()

    def start(self):
        self._start_time = time.time()
        self._stopped = False
        self._started = True
        self._position = None
        self._start_fired = False
        self._position_event.clear()
        self._id = 0
        self.fire_event(EventType("state"), State.Moving)

    def stop(self):
        self._stopped = True

    abort = stop

    def is_started(self):
        return self._started

    def is_stopped(self):
        return self._stopped

    def is_running(self):
        return self._running

    def run(self):
        self._running = True
        try:
            while len(self.active_events) > 0 and not self.is_stopped():
                self.wait_active()
                self.fire_active()
                self.wait_passive()
                self.fire_passive()
                self._id += 1
        finally:
            self._started = False
            self._running = False
            self._stopped = False
            self.fire_event(EventType("state"), State.On)

    def sleep(self, period):
        if period <= 0:
            return
        necessary_naps = int(math.ceil(period / self.MAX_NAP_TIME))
        if necessary_naps == 0:  # avoid zero ZeroDivisionError
            nap = 0
        else:
            nap = period / necessary_naps
        for _ in range(necessary_naps):
            if self.is_stopped():
                break
            time.sleep(nap)

    def fire_start(self):
        self.fire_event(EventType("start"), self._id)
        self._start_fired = True
        if self._id > 0:
            msg = "start was fired with {0} delay".format(self._id)
            self.warning(msg)

    def wait_active(self):
        candidate = self.active_events[0]
        if self.initial_domain_in_use == SynchDomain.Time:
            now = time.time()
            candidate += self._start_time
            self.sleep(candidate - now)
        else:
            while True:
                if self.is_stopped():
                    break
                if self._position_event.isSet():
                    self._position_event.clear()
                    now = self._position
                    if self._condition(now, candidate):
                        break
                else:
                    self._position_event.wait(self.MAX_NAP_TIME)

    def fire_active(self):
        # check if some events needs to be skipped
        i = 0
        while i < len(self.active_events) - 1:
            candidate = self.active_events[i + 1]
            if self.initial_domain_in_use is SynchDomain.Time:
                candidate += self._start_time
                now = time.time()
            elif self.initial_domain_in_use is SynchDomain.Position:
                now = self._position
            if self._condition(now, candidate):
                i += 1
            else:
                break
        self._id += i
        if not self._start_fired:
            self.fire_start()
        self.fire_event(EventType("active"), self._id)
        self.active_events = self.active_events[i + 1:]
        self.passive_events = self.passive_events[i:]

    def wait_passive(self):
        if self.active_domain_in_use == SynchDomain.Time:
            now = time.time()
            candidate = self._start_time + self.passive_events[0]
            self.sleep(candidate - now)
        else:
            while True:
                if self._position_event.isSet():
                    self._position_event.clear()
                    if self._condition(self._position, self.passive_events[0]):
                        break
                else:
                    self._position_event.wait(self.MAX_NAP_TIME)
                    if self.is_stopped():
                        break

    def fire_passive(self):
        self.fire_event(EventType("passive"), self._id)
        self.set_passive_events(self.passive_events[1:])
        if len(self.passive_events) == 0:
            self.fire_end()

    def fire_end(self):
        self.fire_event(EventType("end"), self._id)

    def set_configuration(self, configuration):
        # make a copy since we may inject the initial time
        configuration = copy.deepcopy(configuration)
        active_events = []
        passive_events = []
        self._direction = None
        # create short variables for commodity
        Time = SynchDomain.Time
        Position = SynchDomain.Position
        Initial = SynchParam.Initial
        Delay = SynchParam.Delay
        Active = SynchParam.Active
        Total = SynchParam.Total
        Repeats = SynchParam.Repeats

        for i, group in enumerate(configuration):
            # inject delay as initial time - generation will be
            # relative to the start time
            initial_param = group.get(Initial)
            if initial_param is None:
                initial_param = dict()
            if Time not in initial_param:
                delay_param = group.get(Delay)
                if Time in delay_param:
                    initial_param[Time] = delay_param[Time]
                group[Initial] = initial_param
            # determine active domain in use
            msg = "no initial value in group %d" % i
            if self.initial_domain in initial_param:
                self.initial_domain_in_use = self.initial_domain
            elif Position in initial_param:
                self.initial_domain_in_use = Position
            elif Time in initial_param:
                self.initial_domain_in_use = Time
            else:
                raise ValueError(msg)
            # determine passive domain in use
            active_param = group.get(Active)
            msg = "no active value in group %d" % i
            if self.active_domain is None:
                if Time in active_param:
                    self.active_domain_in_use = Time
                elif Position in active_param:
                    self.active_domain_in_use = Position
                else:
                    raise ValueError(msg)
            elif self.active_domain in active_param:
                self.active_domain_in_use = self.active_domain
            else:
                raise ValueError(msg)
            # create short variables for commodity
            initial_domain_in_use = self.initial_domain_in_use
            active_domain_in_use = self.active_domain_in_use
            repeats = group.get(Repeats, 1)
            active = active_param[active_domain_in_use]
            initial_in_initial_domain = initial_param[initial_domain_in_use]
            initial_in_active_domain = initial_param[active_domain_in_use]
            active_event_in_initial_domain = initial_in_initial_domain
            active_event_in_active_domain = initial_in_active_domain
            if repeats > 1:
                total_param = group[Total]
                total_in_initial_domain = total_param[initial_domain_in_use]
                total_in_active_domain = total_param[active_domain_in_use]
                for _ in range(repeats):
                    passive_event = active_event_in_active_domain + active
                    active_events.append(active_event_in_initial_domain)
                    passive_events.append(passive_event)
                    active_event_in_initial_domain += total_in_initial_domain
                    active_event_in_active_domain += total_in_active_domain
            else:
                active_events.append(active_event_in_initial_domain)
                passive_event = active_event_in_active_domain + active
                passive_events.append(passive_event)

        # determine direction
        if self.direction is None:
            if strictly_increasing(active_events):
                self.direction = 1
            elif strictly_decreasing(active_events):
                self.direction = -1
            else:
                msg = "active values indicate contradictory directions"
                raise ValueError(msg)

        self.active_events = active_events
        self.passive_events = passive_events
