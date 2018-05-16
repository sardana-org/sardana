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


from epics import caget

from sardana import State
from sardana.pool.controller import ZeroDController
from sardana.pool.controller import Type, Description, DefaultValue, Access, DataAccess, Memorize, Memorized

class Channel:

    def __init__(self, idx):
        self.idx = idx            # 1 based index
        self.value = 0.0
        self.active = False
        self.PVname = None


class epicsZeroDController(ZeroDController):
    """This class represents a dummy Sardana 0D controller."""

    MaxDevice = 1024
    
    axis_attributes  = {'PVname': {Type: str, Description: 'PV name of channel', DefaultValue: None,  Access: DataAccess.ReadWrite, Memorized: Memorize},}

    def __init__(self, inst, props, *args, **kwargs):
        ZeroDController.__init__(self, inst, props, *args, **kwargs)

        self.channels = [Channel(i + 1) for i in xrange(self.MaxDevice)]
        self.read_channels = {}

    def AddDevice(self, ind):
        self.channels[ind].active = True

    def DeleteDevice(self, ind):
        self.channels[ind].active = False

    def StateOne(self, ind):
        return State.On, "OK"

    def _setChannelValue(self, channel):
        channel.value = caget(channel.PVname)

    def PreReadAll(self):
        self.read_channels = {}

    def PreReadOne(self, ind):
        channel = self.channels[ind - 1]
        self.read_channels[ind] = channel

    def ReadAll(self):
        for channel in self.read_channels.values():
            self._setChannelValue(channel)

    def ReadOne(self, ind):
        v = self.read_channels[ind].value
        return v
    
    def GetAxisExtraPar(self, ind, name):
        """ Get Smaract axis particular parameters.
        @param axis to get the parameter
        @param name of the parameter to retrive
        @return the value of the parameter
        """
        name = name.lower()
        
        if name == 'pvname':
            result = self.channels[ind - 1].PVname
        else:
            raise ValueError('There is not %s attribute' % name)
        return result

    def SetAxisExtraPar(self, ind, name, value):
        """ Set Smaract axis particular parameters.
        @param axis to set the parameter
        @param name of the parameter
        @param value to be set
        """
        name = name.lower()
        if name == 'pvname':
            self.channels[ind - 1].PVname = value
        else:
            raise ValueError('There is not %s attribute' % name)
