#!/usr/bin/env python

##############################################################################
##
## This file is part of Sardana
##
## http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
##
## Sardana is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## Sardana is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################

from taurus.external import unittest
from taurus.test import insertTest
from sardana.pool.pooltggeneration import PoolTGGeneration
from sardana.pool.test import AcquisitionTestCase



@insertTest(helper_name='hw_continuous_acquisition', offset=0, 
            active_period=0.001, passive_period=0.1, repetitions=10,
            integ_time=0.01)
class Ni660XPositionMeasurementCTAcqTestCase(AcquisitionTestCase, unittest.TestCase):
    """Integration test.
    """
    tg_ctrl_name = '_test_nitg_ctrl_1'
    tg_elem_name = '_test_nitg_1_1'
    chn_ctrl_name = '_test_niposmeas_ctrl_1'
    chn_elem_name = '_test_niposmeas_1_1'

    def setUp(self):
        """Create a Controller, TriggerGate and PoolTGGeneration objects from 
        Ni660XTriggerGateController and Ni660XPositionCTCtrl configurations.
        """
        unittest.TestCase.setUp(self)
        AcquisitionTestCase.setUp(self)
        # create TG ctrl and element 
        tg_ctrl_obj = self.createController(tg_ctrl_name,
                                'Ni660XTriggerGateController',
                                'Ni660XTriggerGateController.py')
        self.createTGElement(tg_ctrl_obj, self.tg_elem_name, 1)

        # create Ni660XPositionMeasurementCT ctrl and element
        ch_ctrl_obj = self.createController(self.chn_ctrl_name,
                                'Ni660XPositionCTCtrl',
                                'Ni660XPositionCTCtrl.py')
        self.createCTElement(ch_ctrl_obj, self.chn_elem_name, 1)

        self.channel_names.append(self.chn_elem_name)


    def tearDown(self):
        AcquisitionTestCase.tearDown(self)     
        unittest.TestCase.tearDown(self)
