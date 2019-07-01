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

from sardana.pool.controller import PseudoCounterController, Type, MaxDimSize


class TwoDROI(PseudoCounterController):
    """A simple pseudo counter which receives an image from a 2D experimental
       channel and returns [1,1] quadrant"""

    counter_roles = "2D",
    pseudo_counter_roles = "Q1",

    def GetAxisAttributes(self, axis):
        axis_attrs = PseudoCounterController.GetAxisAttributes(self, axis)
        axis_attrs = dict(axis_attrs)
        axis_attrs['Value'][Type] = ((float,),)
        axis_attrs['Value'][MaxDimSize] = (256, 256)
        return axis_attrs

    def Calc(self, axis, counter_values):
        self._log.debug("Calc entering...")
        img = counter_values[0]
        if axis == 1:
            quadrant = img[0:255, 0:255]
        else:
            raise NotImplementedError("only first quadrant is implemented")
        self._log.debug("Calc returning: %r" % quadrant)
        return quadrant
