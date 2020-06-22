from taurus.test.base import insertTest
import unittest

from sardana.pool.poolsynchronization import PoolSynchronization
from sardana.pool.pooldefs import SynchDomain, SynchParam

from sardana.pool.test import FakePool, createPoolController, \
    createPoolTriggerGate, dummyPoolTGCtrlConf01, dummyTriggerGateConf01, \
    createControllerConfiguration

synch_description1 = [{SynchParam.Delay: {SynchDomain.Time: 0},
                       SynchParam.Active: {SynchDomain.Time: .03},
                       SynchParam.Total: {SynchDomain.Time: .1},
                       SynchParam.Repeats: 0}]

synch_description2 = [{SynchParam.Delay: {SynchDomain.Time: 0},
                       SynchParam.Active: {SynchDomain.Time: .01},
                       SynchParam.Total: {SynchDomain.Time: .02},
                       SynchParam.Repeats: 10}]


@insertTest(helper_name='generation', synch_description=synch_description1)
@insertTest(helper_name='generation', synch_description=synch_description2)
class PoolDummyTriggerGateTestCase(unittest.TestCase):
    """Parameterizable integration test of the PoolSynchronization action and
    the DummTriggerGateController.

    Using insertTest decorator, one can add tests of a particular trigger/gate
    characteristic.
    """

    def setUp(self):
        """Create a Controller, TriggerGate and PoolSynchronization objects from
        dummy configurations
        """
        unittest.TestCase.setUp(self)
        pool = FakePool()

        dummy_tg_ctrl = createPoolController(pool, dummyPoolTGCtrlConf01)
        self.dummy_tg = createPoolTriggerGate(pool, dummy_tg_ctrl,
                                              dummyTriggerGateConf01)
        # marrying the element with the controller
        dummy_tg_ctrl.add_element(self.dummy_tg)

        self.ctrl_conf = createControllerConfiguration(dummy_tg_ctrl,
                                                       [self.dummy_tg])

        # marrying the element with the action
        self.tg_action = PoolSynchronization(self.dummy_tg)
        self.tg_action.add_element(self.dummy_tg)

    def generation(self, synch_description):
        """Verify that the created PoolTGAction start_action starts correctly
        the involved controller."""
        args = ([self.ctrl_conf], synch_description)
        self.tg_action.start_action(*args)
        self.tg_action.action_loop()
        # TODO: add asserts applicable to a dummy controller e.g. listen to
        # state changes and verify if the change ON->MOVING-ON was emitted

    def tearDown(self):
        unittest.TestCase.tearDown(self)
