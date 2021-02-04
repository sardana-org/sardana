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

import os

import PyTango
from taurus.core.util import whichexecutable
from taurus.core.tango.starter import ProcessStarter

from sardana import sardanacustomsettings
from sardana.tango.core.util import (get_free_server, get_free_device)
from sardana.tango.macroserver.MacroServer import MacroServerClass


class BaseMacroServerTestCase(object):
    """Abstract class for macroserver DS testing.
    """
    ms_ds_name = getattr(sardanacustomsettings, 'UNITTEST_MS_DS_NAME',
                         "unittest1")
    ms_name = getattr(sardanacustomsettings, 'UNITTEST_MS_NAME',
                      "macroserver/demo1/1")
    door_name = getattr(sardanacustomsettings, 'UNITTEST_DOOR_NAME',
                        "door/demo1/1")

    def setUp(self, properties=None):
        """
        Start MacroServer DS.

        :param properties: dictionary with the macroserver properies.

        """
        try:
            db = PyTango.Database()
            # Discover the MS launcher script
            msExec = whichexecutable.whichfile("MacroServer")
            # register MS server
            ms_ds_name_base = "MacroServer/" + self.ms_ds_name
            self.ms_ds_name = get_free_server(db, ms_ds_name_base)
            self._msstarter = ProcessStarter(msExec, self.ms_ds_name)
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
            # Add properties
            if properties:
                for key, values in list(properties.items()):
                    db.put_device_property(self.ms_name,
                                           {key: values})
            # start MS server
            self._msstarter.startDs(wait_seconds=20)
            self.door = PyTango.DeviceProxy(self.door_name)
        except Exception as e:
            # force tearDown in order to eliminate the MacroServer
            print(e)
            self.tearDown()

    def tearDown(self):
        """Remove the MacroServer instance and its properties file.
        """

        self._msstarter.cleanDb(force=True)
        self._msstarter = None
        self.macroserver = None
        self.door = None

        db = PyTango.Database()
        prop = db.get_device_property(self.ms_name, "EnvironmentDb")
        ms_properties = prop["EnvironmentDb"]
        if not ms_properties:
            dft_ms_properties = os.path.join(
                MacroServerClass.DefaultEnvBaseDir,
                MacroServerClass.DefaultEnvRelDir)
            ds_inst_name = self.ms_ds_name.split("/")[1]
            ms_properties = dft_ms_properties % {
                "ds_exec_name": "MacroServer",
                "ds_inst_name": ds_inst_name}
        ms_properties = os.path.normpath(ms_properties)
        extensions = [".bak", ".dat", ".dir"]
        for ext in extensions:
            name = ms_properties + ext
            if not os.path.exists(name):
                continue
            try:
                os.remove(name)
            except Exception as e:
                msg = "Not possible to remove macroserver environment file"
                print(msg)
                print(("Details: %s" % e))


if __name__ == '__main__':
    bms = BaseMacroServerTestCase()
    bms.setUp()
    print(bms.door, bms.macroserver)
    bms.tearDown()
