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

"""Device pool extension for taurus Qt"""

__all__ = ["QPool", "QMeasurementGroup",
           "registerExtensions"]

import json

from taurus.external.qt import Qt

from taurus.core.taurusbasetypes import TaurusEventType
from sardana.taurus.core.tango.sardana.pool import Pool, MeasurementGroup

CHANGE_EVTS = TaurusEventType.Change, TaurusEventType.Periodic


class QPool(Qt.QObject, Pool):

    def __init__(self, name='', qt_parent=None, **kw):        
        self.call__init__(Pool, name, **kw)
        self.call__init__(Qt.QObject, qt_parent, name=name)


class QMeasurementGroup(Qt.QObject, MeasurementGroup):

    configurationChanged = Qt.pyqtSignal()

    def __init__(self, name='', qt_parent=None, **kw):
        self.call__init__(MeasurementGroup, name, **kw)
        self.call__init__(Qt.QObject, qt_parent, name=name)
        # emitting from the MeasurementGroup.__init__() failed 
        # because QObject was not initilized yet - re-emit here
        self.configurationChanged.emit()

    def __getattr__(self, name):
        try:
            return Qt.QObject.__getattr__(self, name)        
        except AttributeError:
            return MeasurementGroup.__getattr__(self, name)
        except RuntimeError:
            # we can not access QObject if it was not initialized
            # this raises a RuntimError;
            # use this if-else just for the initialization phase
            # when QObject is initilized after MeasurementGroup
            if "QObject" in self.inited_class_list:
                raise
            else:
                return MeasurementGroup.__getattr__(self, name)
    
    def on_configuration_changed(self, evt_src, evt_type, evt_value):
        MeasurementGroup.on_configuration_changed(self, evt_src, evt_type, evt_value)
        try:
            self.configurationChanged.emit()
        except RuntimeError:
            # we can not access QObject if it was not initialized
            # this raises a RuntimError when MeasurementGroup will call addListener()
            # ignore exception if we have still not initialized QObject
            if "QObject" in self.inited_class_list:
                raise


def registerExtensions():
    """Registers the pool extensions in the :class:`taurus.core.tango.TangoFactory`"""
    import taurus
    #import sardana.taurus.core.tango.sardana.pool
    # sardana.taurus.core.tango.sardana.pool.registerExtensions()
    factory = taurus.Factory()
    #factory.registerDeviceClass('Pool', QPool)
    factory.registerDeviceClass('MeasurementGroup', QMeasurementGroup)
