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

"""This file contains the basic pool definitions."""

__all__ = ["ControllerAPI", "AcqTriggerType", "AcqMode", "SynchDomain",
           "SynchParam", "AcqSynch", "AcqSynchType"]

__docformat__ = 'restructuredtext'

from operator import __getitem__
from taurus.external.enum import IntEnum
from taurus.core.util.enumeration import Enumeration
from sardana.taurus.core.tango.sardana import AcqTriggerType, AcqMode

#: A constant defining the controller API version currently supported
ControllerAPI = 1.1

# synchronization domain: Time means that the configuration parameter will be
# expressed in the time domain, Position means the motor position domain and
# Monitor means the count to monitor domain


class SynchEnum(IntEnum):

    @classmethod
    def fromStr(cls, string):
        '''Convert string representation of SynchDomain enum e.g.
        'SynchDomain.Time' to SynchDomain objects. It also works with just
        domain strings like 'Time'. The following expressions are True:

        SynchDomain.fromStr(str(SynchDomain.Time)) == SynchDomain.Time
        SynchDomain.fromStr('Time') == SynchDomain.Time
        '''
        domain = string.split('.')
        if len(domain) == 1:
            return __getitem__(cls, domain[0])
        elif len(domain) == 2:
            return __getitem__(cls, domain[1])
        else:
            raise ValueError('Can not convert %s to SynchDomain' % string)


class SynchDomain(SynchEnum):
    """Enumeration of synchronization domains.

    - Time - describes the synchronization in time domain
    - Position - describes the synchronization in position domain
    - Monitor - not used at the moment but foreseen for synchronization on monitor

    .. note::
        The SynchDomain class has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the class) may occur if
        deemed necessary by the core developers.
    """
    Time = 0
    Position = 1
    Monitor = 2
#     - Default - the controller selects the most appropriate domain:
#       for active events the precedence should be first Position and then Time
#       for passive events the precedence should be first Time and then Position
#    Default = 3


class SynchParam(SynchEnum):
    """Enumeration of synchronization's group parameters.

    - Delay - initial delay (relative to the synchronization start)
    - Total - total interval
    - Active - active interval (part of the total interval)
    - Repeats - number of repetitions within the group
    - Initial - initial point (absolute)

    .. note::
        The SynchParam class has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the class) may occur if
        deemed necessary by the core developers.

    """
    Delay = 0
    Total = 1
    Active = 2
    Repeats = 3
    Initial = 4

# TODO: convert to to python enums, but having in ming problems with
# JSON serialization: https://bugs.python.org/issue18264
# class AcqSynchType(Enumeration):
#
#     Trigger = 0
#     Gate = 1

AcqSynchType = Enumeration("AcqSynchType", ["Trigger", "Gate"])


# TODO: convert to to python enums, but having in ming problems with
# JSON serialization: https://bugs.python.org/issue18264
class AcqSynch(Enumeration):

    SoftwareTrigger = 0
    HardwareTrigger = 1
    SoftwareGate = 2
    HardwareGate = 3

    @classmethod
    def from_synch_type(self, software, synch_type):
        """Helper obtain AcqSynch from information about software/hardware
        nature of synchronization element and AcqSynchType
        """
        if synch_type is AcqSynchType.Trigger:
            if software:
                return AcqSynch.SoftwareTrigger
            else:
                return AcqSynch.HardwareTrigger
        elif synch_type is AcqSynchType.Gate:
            if software:
                return AcqSynch.SoftwareGate
            else:
                return AcqSynch.HardwareGate
        else:
            raise ValueError("Unable to determine AcqSynch from %s" %
                             synch_type)
