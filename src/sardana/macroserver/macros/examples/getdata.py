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

__docformat__ = "restructuredtext"

from sardana.macroserver.macro import *


class get_data(Macro):
    """A macro that executes another macro from within it, get its data,
    and calculates a result using this data.

    This macro is part of the examples package. It was written for
    demonstration purposes"""

    param_def = [["mot", Type.Moveable, None, "moveable to be moved"]]
    result_def = [["middle", Type.Float, None,
                   "the middle motor position"]]

    def run(self, mot):
        start = 0
        end = 2
        intervals = 2
        integtime = 0.1
        positions = []
        dscan, _ = self.createMacro('dscan',
                                    mot, start, end, intervals, integtime)
        self.runMacro(dscan)
        
        data = dscan.data
        len_data = len(data)
        for point_nb in xrange(len_data):
            position = data[point_nb].data[mot.getName()]
            positions.append(position)

        middle_pos = max(positions) - min(positions) / len_data
        return middle_pos
