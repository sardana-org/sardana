import time
import threading
import math
import numpy as np
from sardana.sardanaevent import EventGenerator
from sardana.pool.pooltriggergate import TGEventType

class StopException(Exception):
    pass

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

    def __run(self):
        '''Generates Sardana events at requested times'''
        try:
            while len(self.event_values) > 0:
                with self.__lock:
                    if self.__stop:
                        raise StopException('Function generation stopped')
                self.__event.wait()
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
                    print "Candidate: %f; Update: %f" % (self.event_values[idx], self.last_value)
                    self.fire_event(event_type, event_id)
                    # eliminate sent and lost events from the list 
                    self.event_values = self.event_values[idx+1:]
                    self.event_conditions = self.event_conditions[idx+1:]
                    self.event_types = self.event_types[idx+1:]
                    self.event_ids = self.event_ids[idx+1:]
        except StopException:
            pass
        finally:
            self.__alive = False