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

import time
from sardana import State
from sardana.pool.controller import CounterTimerController, Type, Description, DefaultValue

import re
import warnings
import numpy as np
from scipy.stats import sem

import zhinst.ziPython as zh
import zhinst.utils as utils


class boxcars:
    def __init__(self, ip='127.0.01', port=8004, api_level=6, repRate = 1500, timeOut = 30):
        # Create a connection to a Zurich Instruments Data Server
	
        print 'connecting ...'

        self.daq = zh.ziDAQServer(ip, port, api_level)
        self.daq.connect()
        self.repRate = repRate
        self.timeOut = timeOut
        self.acqStartTime = None
        self.acqEndTime   = None
    
        # Detect a device
        self.device = utils.autoDetect(self.daq)
        # Find out whether the device is an HF2 or a UHF
        self.devtype = self.daq.getByte('/%s/features/devtype' % self.device)
        self.options = self.daq.getByte('/%s/features/options' % self.device)
        self.clock   = self.daq.getDouble('/%s/clockbase' % self.device)

        if not re.search('BOX', self.options):
            raise Exception("This example can only be ran on a UHF with the BOX option enabled.")

        if self.daq.getConnectionAPILevel() != 6:
            warnings.warn("ziDAQServer is using API Level 1, it is strongly recommended " * \
                "to use API Level 6 in order to obtain boxcar data with timestamps.")
    
        self.daq.sync()

        self.dacq = self.daq.dataAcquisitionModule()
        
        self.dacq.set('dataAcquisitionModule/device', self.device)
        self.dacq.set('dataAcquisitionModule/endless', 0)
        
        grid_mode = 4;
        self.dacq.set('dataAcquisitionModule/grid/mode', grid_mode)
                
        self.dacq.subscribe('/%s/boxcars/%d/sample' % (self.device, 0))
        self.dacq.subscribe('/%s/boxcars/%d/sample' % (self.device, 1))
        
        print 'connected'

    def startAcq(self,int_time=1):
        # Poll the data
        #define number of samples that shall be recorded
        
        nbSamples = self.repRate*int_time
        
        self.daq.sync()
        self.dacq.set('dataAcquisitionModule/grid/cols', nbSamples)
        
        self.dacq.execute()
        self.dacq.set('dataAcquisitionModule/forcetrigger', 1)
        self.acqStartTime = time.time()
        
        
    def isFinished(self):
        finished = self.dacq.progress()
        now = time.time()
        hasTimeout = ((now-self.acqStartTime) > self.timeOut)
        time.sleep(0.01)
        return (finished, hasTimeout)
    
    def readData(self):
        
        data = self.dacq.read()
        self.acqEndTime = time.time()
        
        [boxcar1_value]     = data[self.device]['boxcars']['0']['sample'][0]['value']
        [boxcar1_timestamp] = data[self.device]['boxcars']['0']['sample'][0]['timestamp']

        [boxcar2_value]     = data[self.device]['boxcars']['1']['sample'][0]['value']
        [boxcar2_timestamp] = data[self.device]['boxcars']['1']['sample'][0]['timestamp']
        
        select = (~np.isnan(boxcar1_value)) & (~np.isnan(boxcar2_value))
        freq   = 1/(np.mean((np.diff(boxcar1_timestamp[select])))/self.clock)
        duration = self.acqEndTime-self.acqStartTime
        
        
        	
        return (np.mean(boxcar1_value[select], dtype=np.float64), np.mean(boxcar2_value[select], dtype=np.float64),
                sem(boxcar1_value[select]),sem(boxcar2_value[select]), len(boxcar1_value[select]), freq, duration,
                np.mean((boxcar1_value[select]/boxcar2_value[select]), dtype=np.float64))
        

    def close(self):
        # Unsubscribe from all paths
        self.dacq.finish()
        self.dacq.unsubscribe('*')
        del self.dacq
        self.daq.unsubscribe('*')
        del self.daq

class zhiCounterTimerController(CounterTimerController):
    """The most basic controller intended from demonstration purposes only.
    This is the absolute minimum you have to implement to set a proper counter
    controller able to get a counter value, get a counter state and do an
    acquisition.

    This example is so basic that it is not even directly described in the
    documentation"""
    ctrl_properties = {'IP': {Type: str, Description: 'The IP of the ZHI controller', DefaultValue: '127.0.0.1'},
						     'port': {Type: int, Description: 'The port of the ZHI controller', DefaultValue: 8004},
                       'repRate': {Type: int, Description: 'RepRate of the acquisition', DefaultValue: 1500},
                       'timeOut': {Type: int, Description: 'Timeout of the acquisition in s', DefaultValue: 30}}
       
    
    def AddDevice(self, axis):
        pass

    def DeleteDevice(self, axis):
        pass

    def __init__(self, inst, props, *args, **kwargs):
        """Constructor"""
        super(zhiCounterTimerController,
              self).__init__(inst, props, *args, **kwargs)
        self.zhi = boxcars(self.IP, self.port, api_level=6, repRate=self.repRate, timeOut=self.timeOut)
        self.data = []
        self.isAquiring = False

    def ReadOne(self, axis):
        """Get the specified counter value"""
        if axis == 0:
            self.data = self.zhi.readData()
                   
        return self.data[axis]

    def StateOne(self, axis):
        """Get the specified counter state"""
        
        (finished, hasTimeout) = self.zhi.isFinished()
        if finished or hasTimeout:
            return State.On, "Counter is stopped"
        else:
            return State.Moving, "Counter is acquiring"
        
    def StartOne(self, axis, value=None):
        """acquire the specified counter"""
                
        if axis == 0:
            self.data = []
            self.zhi.startAcq(value)
    
    def StartAll(self):
        pass
    
    def LoadOne(self, axis, value, repetitions):
        pass

    def StopOne(self, axis):
        """Stop the specified counter"""
        pass