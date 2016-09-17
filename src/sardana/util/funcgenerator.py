import time
import threading
import math
import numpy
import numpy as np
from sardana.sardanaevent import EventGenerator
from sardana.pool.pooltriggergate import TGEventType
from sardana.pool.pooldefs import SynchParam, SynchDomain

class StopException(Exception):
    pass

class FunctionGenerator(EventGenerator):

    MAX_NAP_TIME = 0.1

    def __init__(self):
        EventGenerator.__init__(self)
        self._start_time = None
        self._running = False
        self._stopped = False
        self._started = False
        self._active_domain = SynchDomain.Default
        self._passive_domain = SynchDomain.Default
        self._active_domain_in_use = None
        self._passive_domain_in_use = None
        self._active_events = list()
        self._passive_events = list()
        self._position_event = threading.Event()
        self._position = None
        self._direction = 1
        self._condition = numpy.greater_equal
        self._id = 0

    def set_active_domain(self, domain):
        self._active_domain = domain

    def get_active_domain(self):
        return self._active_domain

    active_domain = property(get_active_domain, set_active_domain)

    def set_passive_domain(self, domain):
        self._passive_domain = domain

    def get_passive_domain(self):
        return self._passive_domain

    passive_domain = property(get_passive_domain, set_passive_domain)

    def set_active_domain_in_use(self, domain):
        self._active_domain_in_use = domain

    def get_active_domain_in_use(self):
        return self._active_domain_in_use

    active_domain_in_use = property(get_active_domain_in_use,
                                    set_active_domain_in_use)

    def set_passive_domain_in_use(self, domain):
        self._passive_domain_in_use = domain

    def get_passive_domain_in_use(self):
        return self._passive_domain_in_use

    passive_domain_in_use = property(get_passive_domain_in_use,
                                     set_passive_domain_in_use)

    def add_active_event(self, event):
        self._active_events.append(event)

    def set_active_events(self, events):
        self._active_events = events

    def get_active_events(self):
        return self._active_events

    active_events = property(get_active_events)

    def add_passive_event(self, event):
        self._passive_events.append(event)

    def set_passive_events(self, events):
        self._passive_events = events

    def get_passive_events(self):
        return self._passive_events

    passive_events = property(get_passive_events)

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
        _, t, v = args
        self._position = v.value
        self._position_event.set()

    def start(self):
        print self.active_events
        print self.passive_events
        self._started = True
        self._start_time = time.time()

    def stop(self):
        self._stopped = True

    def clean(self):
        self._started = False
        self._stopped = False
        self._running = False
        self._start_time = None
        self._id = 0

    def is_started(self):
        return self._started

    def is_stopped(self):
        return self._stopped

    def is_running(self):
        return self._running

    def run(self):
        try:
            self._running = True
            while len(self.active_events) > 0 and not self.is_stopped():
                self.wait_active()
                self.fire_active()
                self.wait_passive()
                self.fire_passive()
        finally:
            self.clean()

    def sleep(self, period):
        if period <= 0:
            return
        necessary_naps = int(math.ceil(period/self.MAX_NAP_TIME))
        if necessary_naps == 0: # avoid zero ZeroDivisionError
            nap = 0
        else:
            nap = period/necessary_naps
        for _ in xrange(necessary_naps):
            if self.is_stopped():
                break
            time.sleep(nap)

    def wait_active(self):
        if self.active_domain_in_use == SynchDomain.Time:
            now = time.time()
            candidate = self._start_time + self.active_events[0]
            self.sleep(candidate - now)
        else:
            while True:
                if self.is_stopped():
                    break
                if self._position_event.isSet():
                    self._position_event.clear()
                    if self._condition(self._position, self.active_events[0]):
                        break
                else:
                    self._position_event.wait(self.MAX_NAP_TIME)

    def fire_active(self):
        i = 0
        while i < len(self.active_events):
            candidate = self.active_events[i]
            if self.active_domain_in_use is SynchDomain.Time:
                candidate += self._start_time
                now = time.time()
            elif self.active_domain_in_use is SynchDomain.Position:
                now = self._position
            print 'now', now
            print 'can', candidate
            if not self._condition(now, candidate):
                break
            i += 1
        self._id += i
        print "Fire Active %d" % (self._id - 1)
        self.fire_event(TGEventType.Active, self._id - 1)
        self.set_active_events(self.active_events[i:])
        self.set_passive_events(self.passive_events[i - 1:])

    def wait_passive(self):
        if self.passive_domain_in_use == SynchDomain.Time:
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
        print "Fire passive %d" % (self._id - 1)
        self.fire_event(TGEventType.Passive, self._id - 1)
        self.set_passive_events(self.passive_events[1:])

    def set_configuration(self, configuration):
        for i, group in enumerate(configuration):
            initial_param = group.get(SynchParam.Initial)
            # Initial is mandatory only when Position domain is forced
            # otherwise fallback to Delay since we will add the absolute
            # timestamp captured in the start method
            if initial_param is None:
                if self.active_domain is SynchDomain.Position:
                    msg = "no initial position in group %d found" % i
                    raise ValueError(msg)
                else:
                    delay = group[SynchParam.Delay][SynchDomain.Time]
                    initial = delay
                    self.active_domain_in_use = SynchDomain.Time
            else:
                if self.active_domain is SynchDomain.Default:
                    initial = initial_param.get(SynchDomain.Position)
                    if initial is None:
                        initial = initial_param.get(SynchDomain.Time)
                        if initial is None:
                            delay = group[SynchParam.Delay][SynchDomain.Time]
                            initial = delay
                        self.active_domain_in_use = SynchDomain.Time
                    else:
                        self.active_domain_in_use = SynchDomain.Position
                else:
                    initial = initial_param.get(self.active_domain)
                    if initial is None:
                        delay = group[SynchParam.Delay][SynchDomain.Time]
                        initial = delay
                    self.active_domain_in_use = self.active_domain
            active_param = group[SynchParam.Active]
            if self.passive_domain is SynchDomain.Default:
                active = active_param[SynchDomain.Time]
                if active is None:
                    active = active_param[SynchDomain.Position]
                    self.passive_domain_in_use = SynchDomain.Position
                else:
                    self.passive_domain_in_use = SynchDomain.Time
            else:
                active = active_param[self.passive_domain]
            total = group[SynchParam.Total][self.active_domain_in_use]
            repeats = group[SynchParam.Repeats]
            active_event = initial
            for _ in xrange(repeats):
                passive_event = active_event + active
                self.add_active_event(active_event)
                self.add_passive_event(passive_event)
                active_event += total


class RectangularFunctionGenerator(EventGenerator):

    id = 0
    max_nap_time = 0.1

    def __init__(self, *args, **kwargs):
        EventGenerator.__init__(self)
        # function characteristics
        self._repetitions = 0
        self._offset = 0
        self._active_interval = 0
        self._active_interval_nap = 0
        self._active_interval_necessary_naps = 1
        self._passive_interval = 0
        self._passive_interval_nap = 0
        self._passive_interval_necessary_naps = 1
        # threading private members
        self.__lock = threading.Lock()
        self.__thread = None # will be allocated in prepare
        self.__stop = False
        self.__alive = False
        self.name = ('RectangularFunctionGenerator-%d' % \
                     RectangularFunctionGenerator.id)
        RectangularFunctionGenerator.id += 1

    def setRepetitions(self, repetitions):
        self._repetitions = repetitions

    def getRepetitions(self):
        return self._repetitions

    def setOffset(self, offset):
        self._offset = offset

    def getOffset(self):
        return self._offset

    def setActiveInterval(self, active_interval):
        self._active_interval = active_interval

    def getActiveInterval(self):
        return self._active_interval

    def setPassiveInterval(self, passive_interval):
        self._passive_interval = passive_interval

    def getPassiveInterval(self):
        return self._passive_interval

    def calculateNap(self, period):
        '''Calculates rough number of naps no longer than max_nap_time
        '''
        necessary_naps = int(math.ceil(period/self.max_nap_time))
        # avoid zero ZeroDivisionError
        if necessary_naps == 0:
            nap = 0
        else:
            nap = period/necessary_naps
        return necessary_naps, nap

    def partialSleep(self, necessary_naps, nap_time):
        '''Performs externally stoppable sleep
        '''
        for _ in xrange(necessary_naps):
            time.sleep(nap_time)
            # check if someone has stopped the generation
            # in the middle of period
            with self.__lock:
                if self.__stop:
                    raise StopException('Function generation stopped')

    def isGenerating(self):
        with self.__lock:
            return self.__alive

    def prepare(self):
        self.__thread = threading.Thread(target=self.__run,
                                         name=self.name)

    def start(self):
        '''Start function generator'''
        with self.__lock:
            if self.__alive:
                msg = '%s is alive hence can not be started.' % self.name
                raise RuntimeError(msg)
            self.__alive = True
            self.__stop = False
            self.__thread.start()

    def stop(self):
        '''Stop function generator'''
        with self.__lock:
            self.__stop = True
        self.__thread.join()

    def __run(self):
        '''Generates Sardana events at requested times'''
        i = 0
        curr_time = time.time()
        next_time = curr_time + self._offset
        necessary_naps, nap_time = self.calculateNap(self._offset)
        try:
            self.partialSleep(necessary_naps, nap_time)
            while i < self._repetitions:
                with self.__lock:
                    if self.__stop:
                        raise StopException('Function generation stopped')
                curr_time = time.time()
                next_time += self._active_interval
                period = max(0, next_time - curr_time)
                necessary_naps, nap_time = self.calculateNap(period)
                self.fire_event(TGEventType.Active, i)
                self.partialSleep(necessary_naps, nap_time)
                curr_time = time.time()
                next_time += self._passive_interval
                period = max(0, next_time - curr_time)
                necessary_naps, nap_time = self.calculateNap(period)
                self.fire_event(TGEventType.Passive, i)
                self.partialSleep(necessary_naps, nap_time)
                i += 1
        except StopException, e:
            pass
        finally:
            self.__alive = False

class PositionFunctionGenerator(EventGenerator):

    id = 0
    max_nap_time = 0.1

    def __init__(self, *args, **kwargs):
        EventGenerator.__init__(self)
        # function characteristics
        self.__event = threading.Event()
        self.event_values = []
        self.event_ids = []
        self.event_types = []
        self.event_conditions = []
        self.last_value = None
        # threading private members
        self.__lock = threading.Lock()
        self.__thread = None # will be allocated in prepare
        self.__stop = False
        self.__alive = False
        self.name = ('PositionFunctionGenerator-%d' % \
                     PositionFunctionGenerator.id)
        PositionFunctionGenerator.id += 1
        self.isStep = True
        self._target = None

    def event_received(self, *args, **kwargs):
        _, t, v = args
        print v.value
        self.last_value = v.value
        self.__event.set()

    def calc_step(self):
        step = (self._active_interval + self._passive_interval) * self._sign
        self._step = step

    def setRepetitions(self, repetitions):
        self._repetitions = repetitions

    def getRepetitions(self):
        return self._repetitions

    def setOffset(self, offset):
        self._offset = offset

    def getOffset(self):
        return self._offset

    def setSign(self, sign):
        self._sign = sign

    def getSign(self):
        return self._sign

    def setInitialPos(self, pos):
        self._initial_pos = pos

    def getInitialPos(self):
        return self._initial_pos

    def setActiveInterval(self, active_interval):
        self._active_interval = active_interval

    def getActiveInterval(self):
        return self._active_interval

    def setPassiveInterval(self, passive_interval):
        self._passive_interval = passive_interval

    def getPassiveInterval(self):
        return self._passive_interval

    def setConfiguration(self, values, conditions, types, ids):
        assert len(values) == len(conditions) == len(types) == len(ids)
        self.event_values = values
        self.event_types = types
        self.event_ids = ids
        self.event_conditions = conditions

    def partialSleep(self, necessary_naps, nap_time):
        '''Performs externally stoppable sleep
        '''
        for _ in xrange(necessary_naps):
            time.sleep(nap_time)
            # check if someone has stopped the generation
            # in the middle of period
            with self.__lock:
                if self.__stop:
                    raise StopException('Function generation stopped')

    def isGenerating(self):
        with self.__lock:
            return self.__alive

    def prepare(self):
        self.__thread = threading.Thread(target=self.__run,
                                         name=self.name)

    def start(self):
        '''Start function generator'''
        with self.__lock:
            if self.__alive:
                msg = '%s is alive hence can not be started.' % self.name
                raise RuntimeError(msg)
            self.__alive = True
            self.__stop = False
            # clear event so we wait for the position updates from now on
            self.__event.clear()
            self.__thread.start()

    def stop(self):
        '''Stop function generator'''
        with self.__lock:
            self.__stop = True
        self.__thread.join()

    def __checkStop(self):
        '''Helper method for stopping generation'''
        with self.__lock:
            if self.__stop:
                raise StopException('Function generation stopped')

    def __run(self):
        '''Generates Sardana events at requested times'''
        try:
            while len(self.event_values) > 0:
                # periodically check if someone has stopped generation
                while not self.__event.isSet():
                    self.__event.wait(0.1)
                    self.__checkStop()
                # reset flag so in next iteration we will wait for a new update
                self.__event.clear()
                idx = 0
                candidate = self.event_values[idx]
                condition = self.event_conditions[idx]
                if condition(self.last_value, candidate):
                    # checking if we need to skip some events
                    while len(self.event_values) > idx + 2:
                        candidate = self.event_values[idx + 1]
                        condition = self.event_conditions[idx + 1]
                        if condition(candidate, self.last_value) and \
                           not candidate == self.last_value:
                            break
                        idx += 1
                    # emit the corresponding event
                    event_id = self.event_ids[idx]
                    event_type = self.event_types[idx]
                    print "Candidate: %f; Update: %f" % (self.event_values[idx],
                                                         self.last_value)
                    self.fire_event(event_type, event_id)
                    # eliminate sent and lost events from the list 
                    self.event_values = self.event_values[idx+1:]
                    self.event_conditions = self.event_conditions[idx+1:]
                    self.event_types = self.event_types[idx+1:]
                    self.event_ids = self.event_ids[idx+1:]
                    # checking if we need to immediatelly emit the last event
                    # cause there will be no more updates 
                    if len(self.event_values) == 1:
                        candidate = self.event_values[-1]
                        condition = self.event_conditions[-1]
                        event_id = self.event_ids[-1]
                        event_type = self.event_types[-1]
                        if condition(self.last_value, candidate):
                            self.fire_event(event_type, event_id)
                            self.event_values = [] 
                            self.event_conditions = []
                            self.event_types = []
                            self.event_ids = []
        except StopException:
            pass
        finally:
            self.__alive = False