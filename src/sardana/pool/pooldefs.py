#!/usr/bin/env python

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

from taurus.core.util.enumeration import Enumeration
from sardana.taurus.core.tango.sardana import AcqTriggerType, AcqMode

#: A constant defining the controller API version currently supported
ControllerAPI = 1.1

# synchronization domain: Time means that the configuration parameter will be 
# expressed in the time domain, Position means the motor position domain and
# Monitor means the count to monitor domain  
SynchDomain = Enumeration(
'SynchDomain', (
    'Time',
    'Position',
    'Monitor'
))

SynchSource = 0
SynchValue = 1