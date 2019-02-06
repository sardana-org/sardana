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
for experiment channels"""

__all__ = ["Value", "PoolBaseChannel"]

__docformat__ = 'restructuredtext'

from sardana.sardanaattribute import SardanaAttribute
from sardana.sardanabuffer import SardanaBuffer
from sardana.pool.poolelement import PoolElement
from sardana.pool.poolacquisition import PoolAcquisitionSoftware,\
    get_timerable_items
from sardana.pool.poolmeasurementgroup import ChannelConfiguration,\
    ControllerConfiguration
from sardana.sardanaevent import EventType

from sardana.pool import AcqSynch, AcqMode

class ValueBuffer(SardanaBuffer):

    def is_value_required(self, idx):
        """Check whether any of pseudo elements still still requires
        this value.

        :param idx: value's index
        :type idx: int
        :return: whether value is required or can be freely removed
        :rtype: bool
        """
        for element in self.obj.get_pseudo_elements():
            if element.get_value_buffer().next_idx <= idx:
                return True
        return False


class Value(SardanaAttribute):

    def __init__(self, *args, **kwargs):
        super(Value, self).__init__(*args, **kwargs)

    def update(self, cache=True, propagate=1):
        if not cache or not self.has_value():
            value = self.obj.read_value()
            self.set_value(value, propagate=propagate)


class PoolBaseChannel(PoolElement):

    ValueAttributeClass = Value
    ValueBufferClass = ValueBuffer
    AcquisitionClass = PoolAcquisitionSoftware

    def __init__(self, **kwargs):
        PoolElement.__init__(self, **kwargs)
        self._value = self.ValueAttributeClass(self, listeners=self.on_change)
        self._value_buffer = self.ValueBufferClass(self,
                                                   listeners=self.on_change)
        self._pseudo_elements = []
        if not self.AcquisitionClass is None:
            acq_name = "%s.Acquisition" % self._name
            self.set_action_cache(self.AcquisitionClass(self, name=acq_name))
        self._integration_time = 0

    def has_pseudo_elements(self):
        """Informs whether this channel forms part of any pseudo element
        e.g. pseudo counter.

        :return: has pseudo elements
        :rtype: bool
        """
        return len(self._pseudo_elements) > 0

    def get_pseudo_elements(self):
        """Returns list of pseudo elements e.g. pseudo counters that this
        channel belongs to.

        :return: pseudo elements
        :rtype: seq<:class:`~sardana.pool.poolpseudocounter.PoolPseudoCounter`>
        """
        return self._pseudo_elements

    def add_pseudo_element(self, element):
        """Adds pseudo element e.g. pseudo counter that this channel
        belongs to.

        :param element: pseudo element
        :type element:
            :class:`~sardana.pool.poolpseudocounter.PoolPseudoCounter`
        """
        if not self.has_pseudo_elements():
            self.get_value_buffer().persistent = True
        self._pseudo_elements.append(element)

    def remove_pseudo_element(self, element):
        """Removes pseudo element e.g. pseudo counters that this channel
        belongs to.

        :param element: pseudo element
        :type element:
            :class:`~sardana.pool.poolpseudocounter.PoolPseudoCounter`
        """

        self._pseudo_elements.remove(element)
        if not self.has_pseudo_elements():
            self.get_value_buffer().persistent = False

    def get_value_attribute(self):
        """Returns the value attribute object for this experiment channel

        :return: the value attribute
        :rtype: :class:`~sardana.sardanaattribute.SardanaAttribute`"""
        return self._value

    def get_value_buffer(self):
        """Returns the value attribute object for this experiment channel

        :return: the value attribute
        :rtype: :class:`~sardana.sardanaattribute.SardanaAttribute`"""
        return self._value_buffer

    # --------------------------------------------------------------------------
    # Event forwarding
    # --------------------------------------------------------------------------

    def on_change(self, evt_src, evt_type, evt_value):
        # forward all events coming from attributes to the listeners
        self.fire_event(evt_type, evt_value)

    # --------------------------------------------------------------------------
    # default acquisition channel
    # --------------------------------------------------------------------------

    def get_default_attribute(self):
        return self.get_value_attribute()

    # --------------------------------------------------------------------------
    # acquisition
    # --------------------------------------------------------------------------

    def get_acquisition(self):
        return self.get_action_cache()

    acquisition = property(get_acquisition, doc="acquisition object")

    # --------------------------------------------------------------------------
    # value
    # --------------------------------------------------------------------------

    def read_value(self):
        """Reads the channel value from hardware.

        :return:
            a :class:`~sardana.sardanavalue.SardanaValue` containing the channel
            value
        :rtype:
            :class:`~sardana.sardanavalue.SardanaValue`"""
        return self.acquisition.read_value()[self]

    def put_value(self, value, propagate=1):
        """Sets a value.

        :param value:
            the new value
        :type value:
            :class:`~sardana.sardanavalue.SardanaValue`
        :param propagate:
            0 for not propagating, 1 to propagate, 2 propagate with priority
        :type propagate:
            int
        """
        val_attr = self._value
        val_attr.set_value(value, propagate=propagate)
        return val_attr

    def get_value(self, cache=True, propagate=1):
        """Returns the channel value.

        :param cache:
            if ``True`` (default) return value in cache, otherwise read value
            from hardware
        :type cache:
            bool
        :param propagate:
            0 for not propagating, 1 to propagate, 2 propagate with priority
        :type propagate:
            int
        :return:
            the channel value
        :rtype:
            :class:`~sardana.sardanaattribute.SardanaAttribute`"""
        return self._get_value(cache=cache, propagate=propagate)

    def _get_value(self, cache=True, propagate=1):
        value = self.get_value_attribute()
        value.update(cache=cache, propagate=propagate)
        return value

    def set_value(self, value):
        """Starts an acquisition on this channel

        :param value:
            the value to count
        :type value:
            :class:`~numbers.Number`"""
        return self._set_value(value)

    def _set_value(self, value):
        self.start_acquisition(value)

    value = property(get_value, set_value, doc="channel value")

    def extend_value_buffer(self, values, idx=None, propagate=1):
        """Extend value buffer with new values assigning them consecutive
        indexes starting with idx. If idx is omitted, then the new values will
        be added right after the last value in the buffer. Also update the read
        value of the attribute with the last element of values.

        :param values:
            values to be added to the buffer
        :type values:
            :class:`~sardana.sardanavalue.SardanaValue`
        :param propagate:
            0 for not propagating, 1 to propagate, 2 propagate with priority
        :type propagate: int
        """
        if len(values) == 0:
            return
        # fill value buffer
        val_buffer = self._value_buffer
        val_buffer.extend(values, idx)
        # update value attribute
        val_attr = self._value
        val_attr.set_value(values[-1], propagate=propagate)
        return val_buffer

    def append_value_buffer(self, value, idx=None, propagate=1):
        """Extend value buffer with new values assigning them consecutive
        indexes starting with idx. If idx is omitted, then the new value will
        be added with right after the last value in the buffer. Also update
        the read value.

        :param value:
            value to be added to the buffer
        :type value:
            :class:`~sardana.sardanavalue.SardanaValue`
        :param propagate:
            0 for not propagating, 1 to propagate, 2 propagate with priority
        :type propagate: int
        """
        # fill value buffer
        val_buffer = self._value_buffer
        val_buffer.append(value, idx)
        # update value attribute
        val_attr = self._value
        val_attr.set_value(value, propagate=propagate)
        return val_buffer

    def clear_value_buffer(self):
        val_attr = self._value_buffer
        val_attr.clear()

        # --------------------------------------------------------------------------
        # integration time
        # --------------------------------------------------------------------------

    def get_integration_time(self):
        """Return the integration time for this object.

        :return: the current integration time
        :rtype: :obj:`float`"""
        return self._integration_time

    def set_integration_time(self, integration_time, propagate=1):
        """Set the integration time for this object.

        :param integration_time: integration time in seconds to set
        :type integration_time: :obj:`float`
        :param propagate:
            0 for not propagating, 1 to propagate, 2 propagate with priority
        :type propagate: :obj:`int`
        """
        if integration_time == self._integration_time:
            # integration time is not changed. Do nothing
            return
        self._integration_time = integration_time
        if not propagate:
            return
        self.fire_event(EventType("integration_time", priority=propagate),
                        integration_time)

    integration_time = property(get_integration_time, set_integration_time,
                                doc="channel integration time")

    def start_acquisition(self):
        msg = "{0} does not support independent acquisition".format(
            self.__class__.__name__)
        raise NotImplementedError(msg)


class PoolTimerableChannel(PoolBaseChannel):

    def __init__(self, **kwargs):
        PoolBaseChannel.__init__(self, **kwargs)
        # TODO: part of the configuration could be moved to the base class
        # so other experimental channels could reuse it
        self._conf_channel = ChannelConfiguration(self)
        self._conf_ctrl = ControllerConfiguration(self.controller)
        self._conf_ctrl.add_channel(self._conf_channel)
        self._timer = "__default"
        self._conf_timer = None

    # ------------------------------------------------------------------------
    # timer
    # ------------------------------------------------------------------------

    def get_timer(self):
        """Return the timer for this object.

        :return: the current timer
        :rtype: :obj:`str`
        """
        return self._timer

    def set_timer(self, timer, propagate=1):
        """Set timer for this object.

        :param timer: new timer to set
        :type timer: :obj:`str`
        :param propagate:
            0 for not propagating, 1 to propagate, 2 propagate with priority
        :type propagate: :obj:`int`
        """
        if timer == self._timer:
            return
        if self._conf_timer is not None:
            timer_elem = self._conf_timer.element
            if timer_elem is not self:
                self.acquisition.remove_element(timer_elem)
                self._conf_ctrl.remove_channel(self._conf_timer)
        self._timer = timer
        self._conf_timer = None
        if not propagate:
            return
        self.fire_event(EventType("timer", priority=propagate), timer)

    timer = property(get_timer, set_timer,
                     doc="timer for the timerable channel")

    def _configure_timer(self):
        timer = self.timer
        if timer == "__self":
            conf_timer = self._conf_channel
        else:
            ctrl = self.get_controller()
            if timer == "__default":
                axis = ctrl.get_default_timer()
                if axis is None:
                    msg = "default_timer not defined in controller"
                    raise ValueError(msg)
                timer_elem = ctrl.get_element(axis=axis)
            else:
                timer_elem = self.pool.get_element_by_name(timer)
            if timer_elem is self:
                conf_timer = self._conf_channel
            else:
                self.acquisition.add_element(timer_elem)
                conf_timer = ChannelConfiguration(timer_elem)
                self._conf_ctrl.add_channel(conf_timer)
        self._conf_ctrl.timer = conf_timer
        self._conf_timer = conf_timer

    def start_acquisition(self):
        """Start software triggered acquisition"""
        self._aborted = False
        self._stopped = False
        if self._simulation_mode:
            return
        if self.timer is None:
            msg = "no timer configured - acquisition is not possible"
            raise RuntimeError(msg)

        if self._conf_timer is None:
            self._configure_timer()
        self.controller.set_ctrl_par("synchronization",
                                     AcqSynch.SoftwareTrigger)
        ctrls, master = get_timerable_items(
            [self._conf_ctrl], self._conf_timer, AcqMode.Timer)
        self.acquisition.run(ctrls, self.integration_time, master, None)
