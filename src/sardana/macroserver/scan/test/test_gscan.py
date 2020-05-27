#!/usr/bin/env python

##############################################################################
##
# This file is part of Sardana
##
# http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
##
# Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
##
# Sardana is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
##
# Sardana is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
##
# You should have received a copy of the GNU Lesser General Public License
# along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################

import sys

import unittest
from taurus.test import insertTest


@insertTest(helper_name='prepare_waypoint', conf={"acc_time": 0.5,
                                                  "dec_time": 0.5,
                                                  "base_rate": 10,
                                                  "start_user_pos": 0,
                                                  "final_user_pos": 50},
            expected={"initial_pos": -60,
                      "final_pos": 135})
@insertTest(helper_name='prepare_waypoint', conf={"acc_time": 0.1,
                                                  "dec_time": 0.1,
                                                  "base_rate": 25,
                                                  "start_user_pos": 0,
                                                  "final_user_pos": 10},
            expected={"initial_pos": -1.25,
                      "final_pos": 16.25})
@insertTest(helper_name='prepare_waypoint', conf={"acc_time": 0.1,
                                                  "dec_time": 0.1,
                                                  "base_rate": 0,
                                                  "start_user_pos": 0,
                                                  "final_user_pos": 10},
            expected={"initial_pos": -2.5,
                      "final_pos": 17.5})
class CTScanTestCase(unittest.TestCase):

    def setUp(self):
        self.skipTest("CTScanTest is not ready to be run as part of testsuite")
#         modules = []
#         for mod in sys.modules.iterkeys():
#             if "sardana" in mod:
#                 modules.append(mod)
#         for mod in modules:
#             try:
#                 del sys.modules[mod]
#             except KeyError:
#                 pass

    @staticmethod
    def getEnv(name):
        if name == "ActiveMntGrp":
            return "MockMntGrp"
        elif name == "ScanID":
            return 1
        elif name == "ScanDir":
            return "/tmp"
        elif name == "ScanFile":
            return "MockFile.dat"
        from sardana.macroserver.msexception import UnknownEnv
        raise UnknownEnv

    def prepare_waypoint(self, conf, expected):
        try:
            from mock import MagicMock, patch
        except ImportError:
            self.skipTest("mock module is not available")
        with patch("sardana.macroserver.msparameter.Type"):
            from sardana.taurus.core.tango.sardana.pool import Motor
            from sardana.macroserver.scan.gscan import CTScan
            mock_motor = MagicMock(Motor)
            mock_motor.getBaseRate = MagicMock(return_value=conf["base_rate"])

            macro = MagicMock()
            macro.getMinAccTime
            macro.getEnv = self.getEnv
            macro.nr_interv = 2
            scan = CTScan(macro)
            scan.get_min_acc_time = MagicMock(return_value=conf["acc_time"])
            scan.get_min_dec_time = MagicMock(return_value=conf["dec_time"])
            scan._physical_moveables = [mock_motor]
            waypoint = {
                "positions": [conf["final_user_pos"]],
                "active_time": 0.3
            }
            start_positions = [conf["start_user_pos"]]
            ideal_paths, _, _ = scan.prepare_waypoint(
                waypoint, start_positions)
            path = ideal_paths[0]
            # Asserts
            msg = 'Initial positions do not match. (expected={0}, got={1})'.format(
                expected["initial_pos"], path.initial_pos)
            self.assertEqual(path.initial_pos, expected["initial_pos"], msg)
            msg = 'Final positions do not match. (expected={0}, got={1})'.format(
                expected["final_pos"], path.final_pos)
            self.assertEqual(path.final_pos, expected["final_pos"], msg)
