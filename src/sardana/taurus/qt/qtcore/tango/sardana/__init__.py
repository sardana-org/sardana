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

"""Taurus Qt extensions for Sardana devices.

Objects obtained with :func:`taurus.Device` expose standard interfaces
e.g., allow to interact with their attributes, check their state, etc.
This module defines classes for enriched interaction with Sardana devices
(also for other elements not exported as devices), e.g. synchronous move
of a sardana motor with
:meth:`~sardana.taurus.core.tango.sardana.pool.Motor.move`
method instead of writing motor's position attribute and then waiting for its
state change. The difference between these classes with respect to the ones
from the :mod:`sardana.taurus.core.tango.sardana` module is the Qt friendly
interface e.g. the Sardana events are translated to Qt signals.

To obtain these enriched objects with :func:`taurus.Device` you need to first
register the extension classes with
the :obj:`~sardana.taurus.qt.qtcore.tango.sardana.registerExtensions` function.

The registration needs to be done before the first access to the given
:func:`taurus.Device`.

.. note:: If you are using
  :class:`~taurus.qt.qtgui.application.TaurusApplication`
  then the registration is done behind the scene at the moment of
  :class:`~taurus.qt.qtgui.application.TaurusApplication` construction.
"""

__docformat__ = 'restructuredtext'


def registerExtensions():
    from . import pool
    from . import macroserver

    pool.registerExtensions()
    macroserver.registerExtensions()
