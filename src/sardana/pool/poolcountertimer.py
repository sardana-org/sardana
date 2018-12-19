#!/usr/bin/env python

##############################################################################
##
# This file is part of Sardana
##
# http://www.sardana-controls.org/
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

"""This module is part of the Python Pool library. It defines the base classes
for CounterTimer"""

__all__ = ["PoolCounterTimer"]

__docformat__ = 'restructuredtext'

from sardana import ElementType

from sardana.pool.poolbasechannel import PoolBaseChannel


class PoolCounterTimer(PoolBaseChannel):

    def __init__(self, **kwargs):
        self._timer = None
        kwargs['elem_type'] = ElementType.CTExpChannel
        PoolBaseChannel.__init__(self, **kwargs)

    # -------------------------------------------------------------------------
    # value
    # -------------------------------------------------------------------------

    def set_write_value(self, w_value, timestamp=None, propagate=1):
        """Sets a new write value for the value.

        :param w_value:
            the new write value for value
        :type w_value:
            :class:`~numbers.Number`
        :param propagate:
            0 for not propagating, 1 to propagate, 2 propagate with priority
        :type propagate:
            int"""
        self._value.set_write_value(w_value, timestamp=timestamp,
                                    propagate=propagate)

    # -------------------------------------------------------------------------
    # timer
    # -------------------------------------------------------------------------

    def get_timer(self, cache=True, propagate=1):
        """Returns the integration time for this object.

        :param cache: not used [default: True]
        :type cache: bool
        :param propagate: [default: 1]
        :type propagate: int
        :return: the current integration time
        :rtype: bool"""
        return self._timer

    def set_timer(self, timer, propagate=1):
        self._timer = timer
        if not propagate:
            return
        if timer == self._timer:
            # current state is equal to last state_event. Skip event
            return
        self.fire_event(EventType("timer", priority=propagate),
                        timer)

    def put_timer(self, timer):
        self._timer = timers

    timer = property(get_timer, set_timer,
                               doc="timer for the counter/timer channel")
