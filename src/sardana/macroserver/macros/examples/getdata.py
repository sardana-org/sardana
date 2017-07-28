##############################################################################
##
# This file is part of Sardana
##
# http://www.sardana-controls.org/
##
# Copyright 2017 CELLS / ALBA Synchrotron, Bellaterra, Spain
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

"""This module contains macros that demonstrate how to execute a macro
from inside another macro, get its data and calculate a result thanks
to this data"""

__all__ = ["get_data"]

__docformat__ = 'restructuredtext'

from sardana.macroserver.macro import *


class get_data(Macro):
    """A macro that executes another macro from within it, get its data,
    and calculates a result using this data.

    This macro is part of the examples package. It was written for
    demonstration purposes"""

    param_def = [['mot', Type.Moveable, None, 'moveable to be moved']]
    result_def = [["result", Type.Float, None,
                   "the max of the motor positions"]]

    def run(self, mot):
        start = 0
        end = 2
        intervals = 2
        integtime = 0.1
        positions = []
        dscan1 = self.createMacro('dscan',
                                  mot, start, end, intervals, integtime)
        self.runMacro(dscan1[0])
        x1 = [None] * len(dscan1[0].data)  # motor positions during the scan
        n_positions = 0
        for i in range(len(dscan1[0].data)):
            x1[i] = dscan1[0].data[i].data[mot.getName()]
            print(x1[i])
            positions.append(x1[i])
            n_positions = n_positions + 1

        average_positions = max(positions) - min(positions) / n_positions
        result = average_positions
        return result
