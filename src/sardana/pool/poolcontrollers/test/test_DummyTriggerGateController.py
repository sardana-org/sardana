import time
import numpy

from taurus.test.base import insertTest
from taurus.external import unittest

from sardana.pool.pooltggeneration import PoolTGGeneration
from sardana.pool.pooltriggergate import TGEventType

from sardana.pool.test import (FakePool, createPoolController,
                               createPoolTriggerGate, dummyPoolTGCtrlConf01,
                               dummyTriggerGateConf01, 
                               createPoolTGGenerationConfiguration)

class TriggerGateReceiver(object):
    '''Dummy TriggerGateReceiver which captures timestamps whenever an event
    comes. Provides useful methods for calculating the event generation 
    performance
    '''
    #TODO: add more jitter measurements e.g. drift
    def __init__(self):
        self.active_events = {}
        self.passive_events = {}
        
    def getCount(self):
        count = len(self.passive_events.keys())
        return count
    
    count = property(getCount)
        
    def event_received(self, *args, **kwargs):
        # store also a timestamp of the start event when it will be implemented
        timestamp = time.time()
        _, t, v = args
        if t == TGEventType.Active:
            self.active_events[v] = timestamp
        elif t == TGEventType.Passive:
            self.passive_events[v] = timestamp
        else:
            raise ValueError('Unknown EventType')
        
    def calc_characteristics(self):
        #TODO: refactor the characteristics calculation method to use numpy
        i = 0
        count = self.count
        characteristics = {}
        while i < count:            
            t1 = self.active_events[i]
            t2 = self.passive_events[i]
            t3 = self.active_events[i+1]
            active_period = t2 - t1
            passive_period = t3 - t2
            characteristics[i] = (active_period, passive_period)
            i += 1
        return characteristics
    
    def calc_cycletocycle(self):
        '''Calculate the cycle-to-cycle jitter characteristics: mean, std and max.
        Cycle-to-cycle jitter is a difference between a cycle period and a cycle 
        period before it. To calculate one cycle-to-cycle jitter one needs 
        exactly 3 active events:
        
        c2c_jitter_1 = cycle_2 - cycle_1
        cycle_2 = active_3 - active_2
        cycle_1 = active_2 - active_1
        '''
        i = 0
        count = self.count
        periods = []
        mean_c2c, std_c2c, max_c2c = 0, 0, 0 
        while i < count:            
            t1 = self.active_events[i]
            t2 = self.active_events[i+1]
            period = t2 - t1
            periods.append(period)
            i += 1
        if len(periods) > 0:
            periods_array = numpy.array(periods)
            c2c = numpy.diff(periods_array)
            mean_c2c = c2c.mean()
            std_c2c = c2c.std()
            max_c2c = c2c.max()
        return mean_c2c, std_c2c, max_c2c
            
        
@insertTest(helper_name='generation', offset=0, active_period=.1,
                                              passive_period=.1, repetitions=0)
@insertTest(helper_name='generation', offset=0, active_period=.01,
                                              passive_period=.01, repetitions=10)
@insertTest(helper_name='generation', offset=0, active_period=.01,
                                             passive_period=.02, repetitions=10)
@insertTest(helper_name='generation', offset=0, active_period=.01,
                                             passive_period=.05, repetitions=10)
class PoolDummyTriggerGateTestCase(unittest.TestCase):
    """Parameterizable integration test of the PoolTGGeneration action and
    the DummTriggerGateController.
    
    Using insertTest decorator, one can add tests of a particular trigger/gate
    characteristic.    
    """

    def setUp(self):
        """Create a Controller, TriggerGate and PoolTGGeneration objects from 
        dummy configurations
        """
        unittest.TestCase.setUp(self)
        pool = FakePool()
        
        dummy_tg_ctrl = createPoolController(pool, dummyPoolTGCtrlConf01)        
        self.dummy_tg = createPoolTriggerGate(pool, dummy_tg_ctrl, 
                                                        dummyTriggerGateConf01)
        # marrying the element with the controller
        dummy_tg_ctrl.add_element(self.dummy_tg)
        
        # TODO: at the moment of writing this test, the configuration of 
        # TGGenerationAction s
        self.cfg = createPoolTGGenerationConfiguration((dummy_tg_ctrl,), 
                                        (dummyPoolTGCtrlConf01,),
                                        ((self.dummy_tg,),),
                                        ((dummyTriggerGateConf01,),))
        
        # marrying the element with the action
        self.tg_action = PoolTGGeneration(self.dummy_tg)
        self.tg_action.add_element(self.dummy_tg)
        
        # creating a dummy trigger gate receiver, it will serve to determine if
        # the triggers were correctly generated
        # TODO: For the moment the insertion of the receiver is very "nasty"
        # refactor it, whenever a correct EventChannel mechanism is
        self.tg_receiver = TriggerGateReceiver()        
        dummy_tg_ctrl._ctrl.add_listener(self.tg_receiver)

    def generation(self, offset, active_period, passive_period, repetitions):
        """Verify that the created PoolTGAction start_action starts correctly 
        the involved controller."""
        args = ()
        kwargs = {'config': self.cfg}
        self.dummy_tg.set_repetitions(repetitions)
        self.dummy_tg.set_offset(offset)
        self.dummy_tg.set_active_period(active_period)
        self.dummy_tg.set_passive_period(passive_period)
        self.tg_action.start_action(*args, **kwargs)
        self.tg_action.action_loop()
        
        # testing number of received triggers
        received_triggers = self.tg_receiver.count
        msg = ('Received triggers: %d does not correspond to generated: %d' %\
               (received_triggers, repetitions))
        self.assertEqual(received_triggers, repetitions, msg)
        
        # testing cycle-to-cycle jitter
        c2c_mean_limit = 0.00001
        c2c_std_limit = 0.00001
        c2c_max_limit = 0.00001
        c2c_mean, c2c_std, c2c_max = self.tg_receiver.calc_cycletocycle()
        msg = 'Mean cycle-to-cycle jitter (%f) is higher than limit (%f)' %\
                                                      (c2c_mean, c2c_mean_limit)
        self.assertLess(c2c_mean, c2c_mean_limit, msg)
        msg = 'Std cycle-to-cycle jitter (%f) is higher than limit (%f)' %\
                                                      (c2c_std, c2c_std_limit)
        self.assertLess(c2c_mean, c2c_mean_limit, msg)
        msg = 'Max cycle-to-cycle jitter (%f) is higher than limit (%f)' %\
                                                      (c2c_max, c2c_max_limit)
        self.assertLess(c2c_mean, c2c_mean_limit, msg)
        
        # testing characteristics
        characteristics = self.tg_receiver.calc_characteristics()
        i = 0
        while i < repetitions:
            periods = characteristics[i]
            measured_active_period = periods[0]
            measured_passive_period = periods[1]
            msg = ('Measured active period: %f does not correspond to ' +\
                   'generated: %f' ) % (measured_active_period, active_period)
            self.assertAlmostEqual(measured_active_period, active_period, 
                                   delta=.001, msg=msg) 
            msg = ('Measured passive period: %f does not correspond to ' +\
                   'generated: %f') % (measured_passive_period, passive_period)
            self.assertAlmostEqual(measured_passive_period, passive_period,
                                   delta=.001, msg=msg)
            i += 1
        
    def tearDown(self):
        unittest.TestCase.tearDown(self)