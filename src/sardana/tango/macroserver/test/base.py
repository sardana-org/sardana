#!/usr/bin/env python

##############################################################################
##
# This file is part of Sardana
##
# http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
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

"""Base classes for the macroserver tests"""

__all__ = ['BaseMacroServerTestCase']

import PyTango
from taurus.core.tango.starter import ProcessStarter
from sardana import sardanacustomsettings
from sardana.tango.core.util import (get_free_server, get_free_device)
from taurus.core.util import whichexecutable


class BaseMacroServerTestCase(object):
    """Abstract class for macroserver DS testing.
    """
    ms_ds_name = getattr(sardanacustomsettings, 'UNITTEST_MS_DS_NAME',
                         "unittest1")
    ms_name = getattr(sardanacustomsettings, 'UNITTEST_MS_NAME',
                      "macroserver/demo1/1")
    door_name = getattr(sardanacustomsettings, 'UNITTEST_DOOR_NAME',
                        "door/demo1/1")

    def setUp(self, pool_name):
        """Start MacroServer DS.
        """
        try:
            db = PyTango.Database()
            # Discover the MS launcher script
            msExec = whichexecutable.whichfile("MacroServer")
            # register MS server
            ms_ds_name = "MacroServer/" + self.ms_ds_name
            ms_free_ds_name = get_free_server(db, ms_ds_name)
            self._msstarter = ProcessStarter(msExec, ms_free_ds_name)
            # register MS device
            dev_name_parts = self.ms_name.split('/')
            prefix = '/'.join(dev_name_parts[0:2])
            start_from = int(dev_name_parts[2])
            self.ms_name = get_free_device(
                db, prefix, start_from)
            self._msstarter.addNewDevice(self.ms_name, klass='MacroServer')
            # register Door device
            dev_name_parts = self.door_name.split('/')
            prefix = '/'.join(dev_name_parts[0:2])
            start_from = int(dev_name_parts[2])
            self.door_name = get_free_device(db, prefix, start_from)
            self._msstarter.addNewDevice(self.door_name, klass='Door')
            db.put_device_property(self.ms_name, {'PoolNames': pool_name})
            # start MS server
            self._msstarter.startDs()
            self.door = PyTango.DeviceProxy(self.door_name)
        except Exception, e:
            # force tearDown in order to eliminate the MacroServer
            print e
            self.tearDown()

    def tearDown(self):
        """Remove the Pool instance.
        """
        self._msstarter.cleanDb(force=True)
        self._msstarter = None
        self.macroserver = None
        self.door = None

if __name__ == '__main__':
    bms = BaseMacroServerTestCase()
    bms.setUp()
    print bms.door, bms.macroserver
    bms.tearDown()
