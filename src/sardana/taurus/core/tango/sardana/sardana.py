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

"""The sardana submodule. It contains specific part of sardana"""

__all__ = ["BaseSardanaElement", "BaseSardanaElementContainer",
           "PoolElementType", "ChannelView", "PlotType", "Normalization",
           "AcqTriggerType", "AcqMode"]

__docformat__ = 'restructuredtext'

from taurus.core.util.enumeration import Enumeration
from taurus.core.util.containers import CaselessDict
from taurus.core.util.codecs import CodecFactory

PoolElementType = Enumeration("PoolElementType",
                              ("0D", "1D", "2D", "Communication", "CounterTimer", "IORegister",
                               "Motor", "PseudoCounter", "PseudoMotor", "TriggerGate"))

ChannelView = Enumeration("ChannelView",
                          ("Channel", "Enabled", "Output", "PlotType",
                           "PlotAxes", "Timer", "Monitor", "Synchronization",
                           "ValueRefPattern", "ValueRefEnabled",
                           "Conditioning", "Normalization", "NXPath",
                           "DataType", "Unknown", "Synchronizer"))

PlotType = Enumeration("PlotType", ("No", "Spectrum", "Image"))

Normalization = Enumeration("Normalization", ("No", "Avg", "Integ"))

#: an enumeration describing all possible acquisition trigger types
AcqTriggerType = Enumeration("AcqTriggerType", (
    "Software",  # channel triggered by software - start and stop by software
    "Trigger",  # channel triggered by HW - start by external
    "Gate",  # channel triggered by HW - start and stop by external
    "Unknown"))

#: an enumeration describing all possible acquisition mode types
AcqMode = Enumeration("AcqMode", (
    "Timer",
    "Monitor",
    "Unknown"))


class BaseSardanaElement(object):
    """Generic sardana element"""

    def __init__(self, *args, **kwargs):
        self._manager = kwargs.pop('manager')
        self.__dict__.update(kwargs)
        self._data = kwargs
        self._object = None

    def __repr__(self):
        return "{0}({1})".format(self.type, self.full_name)

    def __str__(self):
        return self.name

    def __getattr__(self, name):
        return getattr(self.getObj(), name)

    def __lt__(self, elem):
        return self.name < elem.name

    def getData(self):
        return self._data

    def getName(self):
        return self.name

    def getId(self):
        return self.full_name

    def getType(self):
        return self.getTypes()[0]

    def getTypes(self):
        elem_types = self.type
        if isinstance(elem_types, str):
            return [elem_types]
        return elem_types

    def serialize(self, *args, **kwargs):
        kwargs.update(self._data)
        return kwargs

    def str(self, *args, **kwargs):
        # TODO change and check which is the active protocol to serialize
        # acordingly
        return CodecFactory().encode(('json', self.serialize(*args, **kwargs)))

    def getObj(self):
        obj = self._object
        if obj is None:
            self._object = obj = self._manager.getObject(self)
        return obj


class BaseSardanaElementContainer:

    def __init__(self):
        # dict<str, dict> where key is the type and value is:
        #     dict<str, MacroServerElement> where key is the element full name
        #                                   and value is the Element object
        self._type_elems_dict = CaselessDict()

        # dict<str, container> where key is the interface and value is the set
        # of elements which implement that interface
        self._interfaces_dict = {}

    def addElement(self, elem):
        elem_type = elem.getType()
        elem_full_name = elem.full_name

        # update type_elems
        type_elems = self._type_elems_dict.get(elem_type)
        if type_elems is None:
            self._type_elems_dict[elem_type] = type_elems = CaselessDict()
        type_elems[elem_full_name] = elem

        # update interfaces
        for interface in elem.interfaces:
            interface_elems = self._interfaces_dict.get(interface)
            if interface_elems is None:
                self._interfaces_dict[
                    interface] = interface_elems = CaselessDict()
            interface_elems[elem_full_name] = elem

    def removeElement(self, e):
        elem_type = e.getType()

        # update type_elems
        type_elems = self._type_elems_dict.get(elem_type)
        if type_elems:
            del type_elems[e.full_name]

        # update interfaces
        for interface in e.interfaces:
            interface_elems = self._interfaces_dict.get(interface)
            del interface_elems[e.full_name]

    def removeElementsOfType(self, t):
        for elem in self.getElementsOfType(t):
            self.removeElement(elem)

    def getElementsOfType(self, t):
        elems = self._type_elems_dict.get(t, {})
        return elems

    def getElementNamesOfType(self, t):
        return [e.name for e in list(self.getElementsOfType(t).values())]

    def getElementsWithInterface(self, interface):
        elems = self._interfaces_dict.get(interface, {})
        return elems

    def getElementsWithInterfaces(self, interfaces):
        ret = CaselessDict()
        for interface in interfaces:
            ret.update(self.getElementsWithInterface(interface))
        return ret

    def getElementNamesWithInterface(self, interface):
        return [e.name for e in
                list(self.getElementsWithInterface(interface).values())]

    def hasElementName(self, elem_name):
        return self.getElement(elem_name) is not None

    def getElement(self, elem_name):
        elem_name = elem_name.lower()
        for elems in list(self._type_elems_dict.values()):
            elem = elems.get(elem_name)  # full_name?
            if elem is not None:
                return elem
            for elem in list(elems.values()):
                if elem.name.lower() == elem_name:
                    return elem

    def getElementWithInterface(self, elem_name, interface):
        elem_name = elem_name.lower()
        elems = self._interfaces_dict.get(interface, {})
        if elem_name in elems:
            return elems[elem_name]
        for elem in list(elems.values()):
            if elem.name.lower() == elem_name:
                return elem

    def getElements(self):
        ret = set()
        for elems in list(self._type_elems_dict.values()):
            ret.update(list(elems.values()))
        return ret

    def getInterfaces(self):
        return self._interfaces_dict

    def getTypes(self):
        return self._type_elems_dict
