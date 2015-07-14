import time
import threading
import math
from sardana.sardanaevent import EventGenerator
from sardana.pool.pooltriggergate import TGEventType

class RectangularFunctionGenerator(EventGenerator):

    id = 0
    max_nap_time = 0.1

    def __init__(self, *args, **kwargs):
        EventGenerator.__init__(self)
        # function characteristics
        self._repetitions = 0
        self._offset = 0
        self._active_period = 0
        self._active_period_nap = 0
        self._active_period_necessary_naps = 1
        self._passive_period = 0
        self._passive_period_nap = 0
        self._passive_period_necessary_naps = 1
        # threading private members
        self.__lock = threading.Lock()
        self.__work = False
        self.__alive = False

    def setRepetitions(self, repetitions):
        self._repetitions = repetitions

    def getRepetitions(self):
        return self._repetitions

    def setOffset(self, offset):
        self._offset = offset

    def getOffset(self):
        return self._offset

    def setActivePeriod(self, active_period):
        self._active_period = active_period

    def getActivePeriod(self):
        return self._active_period

    def setPassivePeriod(self, passive_period):
        self._passive_period = passive_period
    
    def calculateNap(self, period):
        # calculate rough number of naps no longer than max_nap_time
        necessary_naps = int(math.ceil(period/self.max_nap_time))
        # avoid zero ZeroDivisionError
        if necessary_naps == 0:
            nap = 0
        else:
            nap = period/necessary_naps
        return necessary_naps, nap

    def getPassivePeriod(self):
        return self._passive_period

    def isGenerating(self):
        return self.__alive

    def prepare(self):
        thread_name = 'RectangularFunctionGenerator-%d' % (self.id)
        self.__thread = threading.Thread(target=self.__run, name = thread_name)

    def start(self):
        '''Start function generator'''
        self.__lock.acquire()
        try:
            if not self.__alive:
                self.__alive = True
                self.__work = True
                self.__thread.start()
        finally:
            self.__lock.release()

    def stop(self):
        '''Stop function generator'''
        self.__lock.acquire()
        self.__work = False
        self.__lock.release()
        self.__thread.join()

    def __run(self):
        '''Generates Sardana events at requested times'''
        i = 0
        next_time = time.time() + self._offset
        time.sleep(self._offset)
        while i < self._repetitions and self.__work:
            curr_time = time.time()
            next_time += self._active_period
            period = max(0, next_time - curr_time)
            necessary_naps, nap_time = self.calculateNap(period)
            self.fire_event(TGEventType.Active, i)
            for _ in xrange(necessary_naps):
                time.sleep(nap_time)
                # check if someone has stopped the generation
                # in the middle of period
                if not self.__work:
                    self.__alive = False
                    return
            curr_time = time.time()
            next_time += self._passive_period
            period = max(0, next_time - curr_time)
            necessary_naps, nap_time = self.calculateNap(period)
            self.fire_event(TGEventType.Passive, i)
            for _ in xrange(necessary_naps):
                time.sleep(nap_time)
                # check if someone has stopped the generation
                # in the middle of period
                if not self.__work:
                    self.__alive = False
                    return
            i += 1
#         self.fire_event(TGEventType.Active, i)
        self.__alive = False
