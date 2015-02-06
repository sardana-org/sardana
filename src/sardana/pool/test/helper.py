#!/usr/bin/env python

##############################################################################
##
## This file is part of Sardana
##
## http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
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

__all__ = ['createPoolController', 'createPoolCounterTimer',
           'createPoolTriggerGate', 'createPoolMeasurementGroup',
           'createPoolTGGenerationConfiguration']

from sardana.pool.poolcontroller import PoolController
from sardana.pool.poolcountertimer import PoolCounterTimer
from sardana.pool.pooltriggergate import PoolTriggerGate
from sardana.pool.poolmeasurementgroup import PoolMeasurementGroup

def createPoolController(pool, conf):
    '''Method to create a PoolController using a configuration dictionary
    '''
    kwargs = conf

    ctrl_manager = pool.ctrl_manager
    ctrl_class_info = None
    ctrl_lib_info = ctrl_manager.getControllerLib(kwargs['library'])
    if ctrl_lib_info is not None:
        ctrl_class_info = ctrl_lib_info.get_controller(kwargs['klass'])

    kwargs['pool'] = pool
    kwargs['lib_info'] = ctrl_lib_info
    kwargs['class_info'] = ctrl_class_info
    return PoolController(**kwargs)

def createPoolCounterTimer(pool, poolcontroller, conf):
    '''Method to create a PoolCounterTimer using a configuration dictionary
    '''
    kwargs = conf
    kwargs['pool'] = pool
    kwargs['ctrl'] = poolcontroller
    return PoolCounterTimer(**kwargs)

def createPoolTriggerGate(pool, poolcontroller, conf):
    '''Method to create a PoolTriggerGate using a configuration dictionary
    '''
    kwargs = conf
    kwargs['pool'] = pool
    kwargs['ctrl'] = poolcontroller
    return PoolTriggerGate(**kwargs)

def createPoolMeasurementGroup(pool, conf):
    '''Method to create a PoolMeasurementGroup using a configuration dictionary
    '''
    kwargs = conf
    kwargs['pool'] = pool
    return PoolMeasurementGroup(**kwargs)

def createPoolTGGenerationConfiguration(ctrls, ctrls_conf, 
                                    ctrl_channels, ctrl_channels_conf):
    '''Method to create TGGeneration configuration. Order of the sequences is 
    important. For all sequences, the element of a given position refers 
    the same controller. 
    
    :param ctrls: sequence of the controllers used by the action
    :type ctrls: seq<sardana.pool.PoolController>
    :param ctrls_conf: sequence of the controllers configuration dictionaries
    :type ctrls_conf: dict
    :param ctrl_channels: sequence of the sequences of the channels 
    corresponding to the controllers 
    :type ctrl_channels: seq<seq<sardana.pool.PoolTriggerGate>>
    :param ctrl_channels_conf: sequence of the sequences of the channels 
    configuration dictionaries
    :type ctrl_channels_conf: seq<seq<dict>>
    :return: a configuration dictionary
    :rtype: dict<>
    '''

    ctrls_configuration = {}
    for ctrl, ctrl_conf, channels, channels_conf in zip(ctrls, ctrls_conf, 
                                    ctrl_channels, ctrl_channels_conf):
        ctrl_conf['units'] = {}
        ctrl_conf['units']['0'] = main_unit_data = {}
        ctrl_conf['units']['0']['channels'] = {}
        for channel, channel_conf in zip(channels, channels_conf):
            main_unit_data['channels'][channel] = channel_conf
        ctrls_configuration[ctrl] = ctrl_conf
    configuration = {'controllers': ctrls_configuration}
    return configuration 
