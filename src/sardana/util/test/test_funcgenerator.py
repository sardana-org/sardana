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

import os
import time
import timeit
import numpy
from threading import Event, Timer

from unittest import TestCase
from taurus.core.util import ThreadPool

from sardana.pool.pooldefs import SynchDomain, SynchParam
from sardana.sardanaevent import EventGenerator, EventType, EventReceiver
from sardana.util.funcgenerator import FunctionGenerator


configuration_negative = [{SynchParam.Initial: {SynchDomain.Position: 0.},
                           SynchParam.Delay: {SynchDomain.Time: 0.1},
                           SynchParam.Active: {SynchDomain.Position: -.5,
                                               SynchDomain.Time: .05, },
                           SynchParam.Total: {SynchDomain.Position: -1,
                                              SynchDomain.Time: 0.1},
                           SynchParam.Repeats: 10}]

configuration_positive = [{SynchParam.Initial: {SynchDomain.Position: 0.},
                           SynchParam.Delay: {SynchDomain.Time: 0.3},
                           SynchParam.Active: {SynchDomain.Position: .5,
                                               SynchDomain.Time: .05, },
                           SynchParam.Total: {SynchDomain.Position: 1,
                                              SynchDomain.Time: 0.1},
                           SynchParam.Repeats: 10}]


class Position(EventGenerator):

    def __init__(self):
        EventGenerator.__init__(self)
        self.value = None
        self.error = False

    def run(self, start=0, end=2, step=0.01, sleep=0.01):
        for position in numpy.arange(start, end, step):
            self.value = position
            self.fire_event(EventType("Position"), self)
            time.sleep(sleep)


class Listener(EventReceiver):

    def __init__(self):
        EventReceiver.__init__(self)
        self.init()

    def init(self):
        self.start = False
        self.active_event_ids = list()
        self.passive_event_ids = list()
        self.end = False

    def event_received(self, *args, **kwargs):
        _, type_, value = args
        name = type_.name
        if name == "active":
            self.active_event_ids.append(value)
        elif name == "passive":
            self.passive_event_ids.append(value)
        elif name == "start":
            self.start = True
        elif name == "end":
            self.end = True
        else:
            ValueError("wrong event type")


class FuncGeneratorTestCase(TestCase):

    def setUp(self):
        self.thread_pool = ThreadPool("TestThreadPool", Psize=2)
        self.func_generator = FunctionGenerator()
        self.event = Event()
        self.listener = Listener()
        self.func_generator.add_listener(self.listener)

    def _done(self, _):
        self.event.set()
        self.event.clear()

    def test_sleep(self):
        if os.name == "nt":
            # (period, delta)
            tests = [(0.01, 0.02), (0.13, 0.05), (1.2, 0.2)]
        else:
            tests = [(0.01, 0.02), (0.13, 0.02), (1.2, 0.02)]
        for period, delta in tests:
            stmt = "fg.sleep(%f)" % period
            setup = "from sardana.util.funcgenerator import FunctionGenerator;\
                     fg = FunctionGenerator()"
            period_measured = timeit.timeit(stmt, setup, number=1)
            msg = "sleep period: %f, expected: %f +/- %f" % (period_measured,
                                                             period,
                                                             delta)
            self.assertAlmostEqual(period_measured,
                                   period,
                                   delta=delta,
                                   msg=msg)

    def test_run_time(self):
        self.func_generator.initial_domain = SynchDomain.Time
        self.func_generator.set_configuration(configuration_positive)
        self.func_generator.start()
        self.thread_pool.add(self.func_generator.run, self._done)
        self.event.wait(100)
        active_event_ids = self.listener.active_event_ids
        active_event_ids_ok = list(range(0, 10))
        msg = "Received active event ids: %s, expected: %s" % (
            active_event_ids, active_event_ids_ok)
        self.assertListEqual(active_event_ids, active_event_ids_ok, msg)
        self.assertTrue(self.listener.start, "Start event is missing")
        self.assertTrue(self.listener.end, "End event is missing")

    def test_stop_time(self):
        self.func_generator.initial_domain = SynchDomain.Time
        self.func_generator.set_configuration(configuration_positive)
        self.func_generator.start()
        self.thread_pool.add(self.func_generator.run, self._done)
        while not self.func_generator.is_running():
            time.sleep(0.01)
        # starting timer that will stop generation
        Timer(0.2, self.func_generator.stop).start()
        self.event.wait(100)
        self.assertFalse(self.func_generator.is_running(), "Stopping failed")
        self.listener.init()
        self.test_run_time()

    def test_run_position_negative(self):
        position = Position()
        position.add_listener(self.func_generator)
        self.func_generator.initial_domain = SynchDomain.Position
        self.func_generator.active_domain = SynchDomain.Position
        self.func_generator.direction = -1
        self.func_generator.set_configuration(configuration_negative)
        self.func_generator.start()
        self.thread_pool.add(self.func_generator.run, self._done)
        while not self.func_generator.is_running():
            time.sleep(0.1)
        self.thread_pool.add(position.run, None, 0, -10, -.05)
        self.event.wait(4)
        position.remove_listener(self.func_generator)
        active_event_ids = self.listener.active_event_ids
        active_event_ids_ok = list(range(0, 10))
        msg = "Received active event ids: %s, expected: %s" % (active_event_ids,
                                                               active_event_ids_ok)
        self.assertListEqual(active_event_ids, active_event_ids_ok, msg)

    def test_run_position_positive(self):
        position = Position()
        position.add_listener(self.func_generator)
        self.func_generator.initial_domain = SynchDomain.Position
        self.func_generator.active_domain = SynchDomain.Position
        self.func_generator.direction = 1
        self.func_generator.set_configuration(configuration_positive)
        self.func_generator.start()
        self.thread_pool.add(self.func_generator.run, self._done)
        while not self.func_generator.is_running():
            time.sleep(0.1)
        self.thread_pool.add(position.run, None, 0, 10, .05)
        self.event.wait(4)
        position.remove_listener(self.func_generator)
        active_event_ids = self.listener.active_event_ids
        active_event_ids_ok = list(range(0, 10))
        msg = "Received active event ids: %s, expected: %s" % (active_event_ids,
                                                               active_event_ids_ok)
        self.assertListEqual(active_event_ids, active_event_ids_ok, msg)

    def test_configuration_position(self):
        self.func_generator.initial_domain = SynchDomain.Position
        self.func_generator.active_domain = SynchDomain.Position
        self.func_generator.set_configuration(configuration_negative)
        active_events = self.func_generator.active_events
        active_events_ok = numpy.arange(0, -9, -1).tolist()
        msg = "Active events are wrong: %s" % active_events
        for a, b in zip(active_events, active_events_ok):
            self.assertAlmostEqual(a, b, 10, msg)
        passive_events = self.func_generator.passive_events
        passive_events_ok = numpy.arange(-.5, -9.5, -1).tolist()
        msg = "Passive events are wrong: %s" % passive_events
        for a, b in zip(passive_events, passive_events_ok):
            self.assertAlmostEqual(a, b, 10, msg)

    def test_configuration_time(self):
        self.func_generator.initial_domain = SynchDomain.Time
        self.func_generator.active_domain = SynchDomain.Time
        self.func_generator.set_configuration(configuration_positive)
        active_events = self.func_generator.active_events
        active_events_ok = numpy.arange(.3, 1.2, 0.1).tolist()
        msg = ("Active events mismatch, received: %s, expected: %s" %
               (active_events, active_events_ok))
        for a, b in zip(active_events, active_events_ok):
            self.assertAlmostEqual(a, b, 10, msg)
        passive_events = self.func_generator.passive_events
        passive_events_ok = numpy.arange(.35, 1.25, 0.1).tolist()
        msg = ("Passive events mismatch, received: %s, expected: %s" %
               (passive_events, passive_events_ok))
        for a, b in zip(passive_events, passive_events_ok):
            self.assertAlmostEqual(a, b, 10, msg)

    def test_configuration_default(self):
        self.func_generator.set_configuration(configuration_positive)
        active_events = self.func_generator.active_events
        active_events_ok = numpy.arange(0, 9, 1).tolist()
        msg = ("Active events mismatch, received: %s, expected: %s" %
               (active_events, active_events_ok))
        for a, b in zip(active_events, active_events_ok):
            self.assertAlmostEqual(a, b, 10, msg)
        passive_events = self.func_generator.passive_events
        passive_events_ok = numpy.arange(.35, 1.25, 0.1).tolist()
        msg = ("Passive events mismatch, received: %s, expected: %s" %
               (passive_events, passive_events_ok))
        for a, b in zip(passive_events, passive_events_ok):
            self.assertAlmostEqual(a, b, 10, msg)

    def tearDown(self):
        self.func_generator.remove_listener(self.listener)
