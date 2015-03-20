import time
import threading
import numpy
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
        # calculate rough number of naps
        necessary_naps = int(active_period/self.max_nap_time)
        if necessary_naps == 0:
            nap = active_period
            necessary_naps = 1
        else:
            # calculate equidistant moments 
            nap_moments = numpy.linspace(0, active_period, necessary_naps)
            # get the final nap period
            nap = nap_moments[1] - nap_moments[0]
        self._active_period_necessary_naps = necessary_naps
        self._active_period_nap = nap

    def getActivePeriod(self):
        return self._active_period

    def setPassivePeriod(self, passive_period):
        self._passive_period = passive_period
        # calculate rough number of naps
        necessary_naps = int(passive_period/self.max_nap_time)
        if necessary_naps == 0:
            nap = passive_period
            necessary_naps = 1
        else:
            # calculate equidistant moments 
            nap_moments = numpy.linspace(0, passive_period, necessary_naps)
            # get the final nap period
            nap = nap_moments[1] - nap_moments[0]
        self._passive_period_necessary_naps = necessary_naps
        self._passive_period_nap = nap

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
        time.sleep(self._offset)
        while i < self._repetitions and self.__work:
            self.fire_event(TGEventType.Active, i)
            for _ in xrange(self._active_period_necessary_naps):
                time.sleep(self._active_period_nap)
                # check if someone has stopped the generation
                # in the middle of period
                if not self.__work:
                    break
            self.fire_event(TGEventType.Passive, i)
            for _ in xrange(self._passive_period_necessary_naps):
                time.sleep(self._passive_period_nap)
                # check if someone has stopped the generation
                # in the middle of period
                if not self.__work:
                    break
            i += 1
#         self.fire_event(TGEventType.Active, i)
        self.__alive = False
