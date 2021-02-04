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

"""Taurus extensions for Sardana devices.

Objects obtained with :func:`taurus.Device` expose standard interfaces
e.g., allow to interact with their attributes, check their state, etc.
This module defines classes for enriched interaction with Sardana devices
(also for other elements not exported as devices), e.g. synchronous move
of a sardana motor with
:meth:`~sardana.taurus.core.tango.sardana.pool.Motor.move`
method instead of writing motor's position attribute and then waiting for its
state change.

To obtain these enriched objects with :func:`taurus.Device` you need to first
register the extension classes with
the :obj:`~sardana.taurus.core.tango.sardana.registerExtensions` function.

The registration needs to be done before the first access to the given
:func:`taurus.Device`.

When you would like to get back to the default :func:`taurus.Device` behavior
you need to unregister the extension classes with the
:obj:`~sardana.taurus.core.tango.sardana.unregisterExtensions` function.

Note that the unregistration will not remove the already created devices from
the :func:`taurus.Factory` cache.
"""

__docformat__ = 'restructuredtext'

from .sardana import *


def registerExtensions():
    from . import pool
    from . import macroserver

    pool.registerExtensions()
    macroserver.registerExtensions()


def unregisterExtensions():
    from . import pool
    from . import macroserver

    pool.unregisterExtensions()
    macroserver.unregisterExtensions()
