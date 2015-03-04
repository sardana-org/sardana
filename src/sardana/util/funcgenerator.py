import time
import threading
from sardana.sardanaevent import EventGenerator
from sardana.pool.pooltriggergate import TGEventType

class RectangularFunctionGenerator(EventGenerator):
    
    id = 0
    
    def __init__(self, *args, **kwargs):
        EventGenerator.__init__(self)
        # function characteristics
        self._repetitions = 0
        self._offset = 0
        self._active_period = 0
        self._passive_period = 0
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
    
    def __run(self):
        '''Generates Sardana events at requested times'''
        #TODO: now the generation can be interrupted only at the end of a cycle
        # allow breakage between the active/passive periods or event during 
        # sleeping
        i = 0
        time.sleep(self._offset)
        while i < self._repetitions and self.__work:
            self.fire_event(TGEventType.Active, i)
            time.sleep(self._active_period)            
            self.fire_event(TGEventType.Passive, i)
            time.sleep(self._passive_period)
            i += 1
#         self.fire_event(TGEventType.Active, i)
        self.__alive = False
