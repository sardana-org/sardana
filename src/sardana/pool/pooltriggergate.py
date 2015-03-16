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

"""This module is part of the Python Pool library. It defines the base classes
for PoolTriggerGate"""

__all__ = ["PoolTriggerGate"]

__docformat__ = 'restructuredtext'

from taurus.core.util.enumeration import Enumeration

from sardana import ElementType
from sardana.sardanaevent import EventType

from sardana.pool.poolelement import PoolElement
from sardana.sardanaattribute import SardanaAttribute
from sardana.pool.pooltggeneration import PoolTGGeneration

TGEventType = Enumeration(
'TGEventType', (
    'Active',
    'Passive'
))

class Index(SardanaAttribute):

    def __init__(self, *args, **kwargs):
        super(Index, self).__init__(*args, **kwargs)

class PoolTriggerGate(PoolElement):

    def __init__(self, **kwargs):
        kwargs['elem_type'] = ElementType.TriggerGate
        PoolElement.__init__(self, **kwargs)
        tggen_name = "%s.TGGeneration" % self._name
        self.set_action_cache(PoolTGGeneration(self, name=tggen_name))
        self._index = Index(self)

    # --------------------------------------------------------------------------
    # offset
    # --------------------------------------------------------------------------

    def get_offset(self, cache=True, propagate=1):
        if not cache or self._velocity is None:
            offset = self.read_offset()
            self._set_offset(offset, propagate=propagate)
        return self._offset

    def set_offset(self, offset, propagate=1):
        self.controller.set_axis_par(self.axis, "offset", offset)
        self._set_offset(offset, propagate=propagate)

    def _set_offset(self, offset, propagate=1):
        self._offset = offset
        if not propagate:
            return
        self.fire_event(EventType("offset", priority=propagate), 
                                                                    offset)

    def read_offset(self):
        offset = self.controller.get_axis_par(self.axis, "offset")
        assert_type(int, offset)
        return offset

    offset = property(get_offset, set_offset,
                        doc="trigger/gate events offset")

    # --------------------------------------------------------------------------
    # active_period
    # --------------------------------------------------------------------------

    def get_active_period(self, cache=True, propagate=1):
        if not cache or self._velocity is None:
            active_period = self.read_active_period()
            self._set_active_period(active_period, propagate=propagate)
        return self._active_period

    def set_active_period(self, active_period, propagate=1):
        self.controller.set_axis_par(self.axis, "active_period", active_period)
        self._set_active_period(active_period, propagate=propagate)

    def _set_active_period(self, active_period, propagate=1):
        self._active_period = active_period
        if not propagate:
            return
        self.fire_event(EventType("active_period", priority=propagate), 
                                                                    active_period)

    def read_active_period(self):
        active_period = self.controller.get_axis_par(self.axis, "active_period")
        assert_type(int, active_period)
        return active_period

    active_period = property(get_active_period, set_active_period,
                        doc="trigger/gate events active_period")

# --------------------------------------------------------------------------
    # passive_period
    # --------------------------------------------------------------------------

    def get_passive_period(self, cache=True, propagate=1):
        if not cache or self._velocity is None:
            passive_period = self.read_passive_period()
            self._set_passive_period(passive_period, propagate=propagate)
        return self._passive_period

    def set_passive_period(self, passive_period, propagate=1):
        self.controller.set_axis_par(self.axis, "passive_period", passive_period)
        self._set_passive_period(passive_period, propagate=propagate)

    def _set_passive_period(self, passive_period, propagate=1):
        self._passive_period = passive_period
        if not propagate:
            return
        self.fire_event(EventType("passive_period", priority=propagate), 
                                                                    passive_period)

    def read_passive_period(self):
        passive_period = self.controller.get_axis_par(self.axis, "passive_period")
        assert_type(int, passive_period)
        return passive_period

    passive_period = property(get_passive_period, set_passive_period,
                        doc="trigger/gate events passive_period")

    # --------------------------------------------------------------------------
    # repetitions
    # --------------------------------------------------------------------------

    def get_repetitions(self, cache=True, propagate=1):
        if not cache or self._velocity is None:
            repetitions = self.read_repetitions()
            self._set_repetitions(repetitions, propagate=propagate)
        return self._repetitions

    def set_repetitions(self, repetitions, propagate=1):
        self.controller.set_axis_par(self.axis, "repetitions", repetitions)
        self._set_repetitions(repetitions, propagate=propagate)

    def _set_repetitions(self, repetitions, propagate=1):
        self._repetitions = repetitions
        if not propagate:
            return
        self.fire_event(EventType("repetitions", priority=propagate), 
                                                                    repetitions)

    def read_repetitions(self):
        repetitions = self.controller.get_axis_par(self.axis, "repetitions")
        assert_type(int, repetitions)
        return repetitions

    repetitions = property(get_repetitions, set_repetitions,
                        doc="trigger/gate events repetitions")

    # --------------------------------------------------------------------------
    # index
    # --------------------------------------------------------------------------
    
    def get_index_attribute(self):
        """Returns the index attribute object for this trigger/gate
        
        :return: the index attribute
        :rtype: :class:`~sardana.sardanaattribute.SardanaAttribute`"""
        return self._index
    
    # --------------------------------------------------------------------------
    # default acquisition channel
    # --------------------------------------------------------------------------

    def get_default_attribute(self):
        return self.get_index_attribute()
