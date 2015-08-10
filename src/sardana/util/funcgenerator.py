import time
import threading
import math
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
        self._event = threading.Event()
        self._intervals = []
        self._sign = 1
        self._initial_pos = 0
        self._repetitions = 0
        self._offset = 0
        self._active_interval = 0
        self._passive_interval = 0
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
        if self._target is not None:
            # Evaluate a target
            if self.isStep:
                if v >= self._target:
                    self._event.set()
                    self._target += self._step
                    self.isStep = False
            # Evaluate if the active_interval has expired
            elif v >= self._target - self._passive_interval * self._sign:
                self._event.set()
                self.isStep = True


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
        self.calc_step()
        self._target = self._initial_pos + self._offset + self._step
        try:
            while i < self._repetitions:
                with self.__lock:
                    if self.__stop:
                        raise StopException('Function generation stopped')
                self._event.wait()
                self.fire_event(TGEventType.Active, i)
                # TODO: Study a better way to do it.
                # Maybe an hardcoded time.sleep is better.
                self._event.wait()
                self.fire_event(TGEventType.Passive, i)
                i += 1
                # TODO: Study if a partial sleep for abort is needed
        except StopException, e:
            pass
        finally:
            self.__alive = False