#!/usr/bin/env python
from operator import __getitem__

##############################################################################
##
## This file is part of Sardana
##
## http://www.sardana-controls.org/
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

"""This file contains the basic pool definitions."""

__all__ = ["ControllerAPI", "AcqTriggerType", "AcqMode"]

__docformat__ = 'restructuredtext'

from taurus.external.enum import IntEnum
from sardana.taurus.core.tango.sardana import AcqTriggerType, AcqMode

#: A constant defining the controller API version currently supported
ControllerAPI = 1.1

# synchronization domain: Time means that the configuration parameter will be 
# expressed in the time domain, Position means the motor position domain and
# Monitor means the count to monitor domain  
class SynchDomain(IntEnum):

    Time = 0
    Position = 1
    Monitor = 2

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