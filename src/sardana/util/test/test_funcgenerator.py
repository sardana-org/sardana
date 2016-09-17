import time
import timeit
import numpy
from threading import Event

from taurus.external.unittest import TestCase
from taurus.core.util import ThreadPool
from sardana.util.funcgenerator import FunctionGenerator
from sardana.pool.pooldefs import SynchDomain, SynchParam
from sardana.sardanaevent import EventGenerator, EventType, EventReceiver
from sardana.pool.pooltriggergate import TGEventType


configuration_negative = [{SynchParam.Initial: {SynchDomain.Position: 0.},
                           SynchParam.Delay: {SynchDomain.Time: 0.1},
                           SynchParam.Active: {SynchDomain.Position: -.1,
                                               SynchDomain.Time: .01,},
                           SynchParam.Total: {SynchDomain.Position: -.2,
                                              SynchDomain.Time: 0.1},
                           SynchParam.Repeats: 10}]

configuration_positive = [{SynchParam.Initial: {SynchDomain.Position: 0.},
                           SynchParam.Delay: {SynchDomain.Time: 0.1},
                           SynchParam.Active: {SynchDomain.Position: .1,
                                               SynchDomain.Time: .1,},
                           SynchParam.Total: {SynchDomain.Position: .2,
                                              SynchDomain.Time: .2},
                           SynchParam.Repeats: 10}]

class Position(EventGenerator):

    def __init__(self):
        EventGenerator.__init__(self)
        self.value = None

    def run(self, start=0, end=2, step=0.01, sleep=0.01):
        for position in numpy.arange(start, end, step):
            self.value = position
            self.fire_event(EventType("Position"), self)
            time.sleep(sleep)

class Listener(EventReceiver):

    def __init__(self):
        EventReceiver.__init__(self)
        self.active_event_ids = list()
        self.passive_event_ids = list()

    def event_received(self, *args, **kwargs):
        _, t, v = args
        if t is TGEventType.Active:
            self.active_event_ids.append(v)
        elif t is TGEventType.Passive:
            self.passive_event_ids.append(v)
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

    def test_sleep(self):
        for i in [0.01, 0.13, 1.2]:
            stmt = "fg.sleep(%f)" % i
            setup = "from sardana.util.funcgenerator import FunctionGenerator;\
                     fg = FunctionGenerator()"
            period = timeit.timeit(stmt, setup , number=1)
            period_ok = i
            msg = "sleep period: %f, expected: >=%f" % (period, period_ok)
            self.assertGreaterEqual(period, period_ok, msg)

    def test_run_time(self):
        self.func_generator.active_domain = SynchDomain.Time
        self.func_generator.set_configuration(configuration_positive)
        self.func_generator.start()
        self.thread_pool.add(self.func_generator.run, self._done)
        self.event.wait(100)
        active_event_ids = self.listener.active_event_ids
        active_event_ids_ok = range(0,10)
        msg = "Received active event ids: %s, expected: %s" % (active_event_ids,
                                                              active_event_ids_ok)
        self.assertListEqual(active_event_ids, active_event_ids_ok, msg)

    def test_run_position_negative(self):
        position = Position()
        position.add_listener(self.func_generator)
        self.func_generator.active_domain = SynchDomain.Position
        self.func_generator.passive_domain = SynchDomain.Position
        self.func_generator.direction = -1
        self.func_generator.set_configuration(configuration_negative)
        self.thread_pool.add(self.func_generator.run, self._done)
        while not self.func_generator.is_running():
            time.sleep(0.1)
        self.thread_pool.add(position.run, None, 0, -2, -.01)
        self.event.wait(3)
        position.remove_listener(self.func_generator)
        active_event_ids = self.listener.active_event_ids
        active_event_ids_ok = range(0,10)
        msg = "Received active event ids: %s, expected: %s" % (active_event_ids,
                                                              active_event_ids_ok)
        self.assertListEqual(active_event_ids, active_event_ids_ok, msg)

    def test_run_position_positive(self):
        position = Position()
        position.add_listener(self.func_generator)
        self.func_generator.active_domain = SynchDomain.Position
        self.func_generator.passive_domain = SynchDomain.Position
        self.func_generator.direction = 1
        self.func_generator.set_configuration(configuration_positive)
        self.thread_pool.add(self.func_generator.run, self._done)
        while not self.func_generator.is_running():
            time.sleep(0.1)
        self.thread_pool.add(position.run, None, 0, 2, .01)
        self.event.wait(3)
        position.remove_listener(self.func_generator)
        active_event_ids = self.listener.active_event_ids
        active_event_ids_ok = range(0,10)
        msg = "Received active event ids: %s, expected: %s" % (active_event_ids,
                                                              active_event_ids_ok)
        self.assertListEqual(active_event_ids, active_event_ids_ok, msg)

    def test_configuration_position(self):
        self.func_generator.active_domain = SynchDomain.Position
        self.func_generator.passive_domain = SynchDomain.Position
        self.func_generator.set_configuration(configuration_negative)
        active_events = self.func_generator.active_events
        active_events_ok = numpy.arange(0, -2, -0.2).tolist()
        msg = "Active events are wrong: %s" % active_events
        for a, b in zip(active_events, active_events_ok):
            self.assertAlmostEqual(a, b, 10, msg)
        passive_events = self.func_generator.passive_events
        passive_events_ok = numpy.arange(-.1, -2.1, -0.2).tolist()
        msg = "Passive events are wrong: %s" % passive_events
        for a, b in zip(passive_events, passive_events_ok):
            self.assertAlmostEqual(a, b, 10, msg)

    def test_configuration_time(self):
        self.func_generator.active_domain = SynchDomain.Time
        self.func_generator.passive_domain = SynchDomain.Time
        self.func_generator.set_configuration(configuration_positive)
        active_events = self.func_generator.active_events
        active_events_ok = numpy.arange(.1, 2.1, 0.2).tolist()
        msg = ("Active events mismatch, received: %s, expected: %s" %
               (active_events, active_events_ok))
        for a, b in zip(active_events, active_events_ok):
            self.assertAlmostEqual(a, b, 10, msg)
        passive_events = self.func_generator.passive_events
        passive_events_ok = numpy.arange(.2, 2.2, 0.2).tolist()
        msg = ("Passive events mismatch, received: %s, expected: %s" %
            (passive_events, passive_events_ok))
        for a, b in zip(passive_events, passive_events_ok):
            self.assertAlmostEqual(a, b, 10, msg)

    def tearDown(self):
        self.func_generator.remove_listener(self.listener)