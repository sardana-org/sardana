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
           'createPoolTGGenerationConfiguration',
           'createCTAcquisitionConfiguration', 'createMGConfiguration',
           'getTGConfiguration']

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


def createCTAcquisitionConfiguration(ctrls, ctrls_conf, 
                                    ctrl_channels, ctrl_channels_conf):
    '''Method to create CTAcquisition configuration. Order of the sequences is 
    important. For all sequences, the element of a given position refers 
    the same controller. 
    
    :param ctrls: sequence of the controllers used by the action
    :type ctrls: seq<sardana.pool.PoolController>
    :param ctrls_conf: sequence of the controllers configuration dictionaries
    :type ctrls_conf: dict
    :param ctrl_channels: sequence of the sequences of the channels 
    corresponding to the controllers 
    :type ctrl_channels: seq<seq<sardana.pool.PoolCounterTimer>>
    :param ctrl_channels_conf: sequence of the sequences of the channels 
    configuration dictionaries
    :type ctrl_channels_conf: seq<seq<dict>>
    :return: a configuration dictionary
    :rtype: dict<>
    '''

    master_ctrl_idx = 0
    master_idx = 0
    configuration = {}
    ctrls_configuration = {}
    configuration['timer'] = ctrl_channels[master_ctrl_idx][master_idx]
    for ctrl, ctrl_conf, channels, channels_conf in zip(ctrls, ctrls_conf, 
                                    ctrl_channels, ctrl_channels_conf):
        ctrl_conf['units'] = {}
        ctrl_conf['units']['0'] = main_unit_data = {}
        ctrl_conf['units']['0']['channels'] = {}
        for channel, channel_conf in zip(channels, channels_conf):
            main_unit_data['channels'][channel] = channel_conf
        main_unit_data['timer'] = channels[master_idx]
        ctrls_configuration[ctrl] = ctrl_conf
    configuration['controllers'] = ctrls_configuration
    return configuration 

def createMGConfiguration(ctrls, ctrls_conf, ctrl_channels, ctrl_channels_conf,
                          ctrl_trigger_elements, ctrl_trigger_modes):
    '''Method to create general MeasurementGroup (and CT) configuration. 
    Order of the sequences is important. For all sequences, the element of a 
    given position refers the same controller. 
    
    :param ctrls: sequence of the controllers used by the action
    :type ctrls: seq<sardana.pool.PoolController>
    :param ctrls_conf: sequence of the controllers configuration dictionaries
    :type ctrls_conf: dict
    :param ctrl_channels: sequence of the sequences of the channels 
    corresponding to the controllers 
    :type ctrl_channels: seq<seq<sardana.pool.PoolCounterTimer>>
    :param ctrl_channels_conf: sequence of the sequences of the channels 
    configuration dictionaries
    :type ctrl_channels_conf: seq<seq<dict>>
    :param trigger_elements: sequence of the sequences of the trigger elements
    :type trigger_elements: seq<seq<sardana.pool.PoolTriggerGate>>
    :param trigger_modes: sequence of the sequences of the trigger elements
    :type trigger_modes: seq<seq<str>>
    :return: a configuration dictionary
    :rtype: dict<>
    '''

    _tg_elements = []
    master_ctrl_idx = 0
    master_idx = 0
    MG_configuration = {}
    MG_configuration['sw_position'] = False
    MG_configuration['sw_time'] = False

    ctrls_configuration = {}
    MG_configuration['timer'] = ctrl_channels[master_ctrl_idx][master_idx]
    for ctrl, ctrl_conf, channels, channels_conf, trigger_elements, \
            trigger_modes in zip(ctrls, ctrls_conf, ctrl_channels, 
            ctrl_channels_conf, ctrl_trigger_elements, ctrl_trigger_modes):
        ctrl_conf['units'] = {}
        ctrl_conf['units']['0'] = main_unit_data = {}
        ctrl_conf['units']['0']['channels'] = {}
        for channel, channel_conf, trigger_element, trigger_mode in \
              zip(channels, channels_conf, trigger_elements, trigger_modes):
            main_unit_data['channels'][channel] = channel_conf
            main_unit_data['channels'][channel]['trigger_element'] = \
                                                                trigger_element
            main_unit_data['channels'][channel]['trigger_mode'] = trigger_mode
            if trigger_element not in _tg_elements:
                _tg_elements.append(trigger_element)            

        main_unit_data['timer'] = channels[master_idx]
        ctrls_configuration[ctrl] = ctrl_conf
    MG_configuration['controllers'] = ctrls_configuration

    if 'sw_position' in _tg_elements:
        MG_configuration['sw_position'] = True
    if 'sw_time' in _tg_elements:
        MG_configuration['sw_time'] = True    

    return MG_configuration


def getTGConfiguration(MGcfg):
    '''Build TG configuration from complete MG configuration.

    :param MGcfg: configuration dictionary of the whole Measurement Group.
    :type MGcfg: dict<>
    :return: a configuration dictionary of TG elements organized by controller
    :rtype: dict<>
    '''

    # Create list with not repeated elements
    _tg_element_list = []

    for ctrl in MGcfg["controllers"]:
        channels_dict = MGcfg["controllers"][ctrl]['units']['0']['channels']
        for channel in channels_dict:
            tg_element = channels_dict[channel]['trigger_element']
            if tg_element not in _tg_element_list:
                _tg_element_list.append(tg_element)

    # Intermediate dictionary to organize each ctrl with its elements.
    ctrl_tgelem_dict = {}
    for tgelem in _tg_element_list:
        tg_ctrl = tgelem.get_controller()
        if tg_ctrl not in ctrl_tgelem_dict.keys():
            ctrl_tgelem_dict[tg_ctrl] = [tgelem]
        else:
            ctrl_tgelem_dict[tg_ctrl].append(tgelem)

    # Build TG configuration dictionary.
    TGcfg = {}
    TGcfg['controllers'] = {}

    for ctrl in ctrl_tgelem_dict:
        TGcfg['controllers'][ctrl] = {}
        TGcfg['controllers'][ctrl]['units'] = {}
        TGcfg['controllers'][ctrl]['units']['0'] = {}
        TGcfg['controllers'][ctrl]['units']['0']['channels'] = {}
        unit = TGcfg['controllers'][ctrl]['units']['0']
        for tg_elem in ctrl_tgelem_dict[ctrl]:
            ch = unit['channels'][tg_elem] = {}
            ch['full_name']= tg_elem.full_name

    return TGcfg




"""
def walk(dictionary, foundkey, answer=None, sofar=None):
    if sofar is None:
        sofar = []
    if answer is None:
        answer = []
    for k,v in dictionary.iteritems():
        if k == foundkey:
            answer.append(sofar + [k])
        if isinstance(v, dict):
            walk(v, foundkey, answer, sofar+[k])
    return answer

def delKeys(dictionary, removekey):
    for path in walk(dictionary, removekey):
        dd = dictionary
        while len(path) > 1:
            dd = dd[path[0]]
            path.pop(0)
        dd.pop(path[0])


def getCTConfiguration(MGcfg):
    Extract CT configuration from complete MG configuration.

    CTcfg = copy.deepcopy(MGcfg)
    delKeys(CTcfg, 'trigger_element')
    delKeys(CTcfg, 'trigger_mode')
    #if 'sw_position' in CTcfg: del CTcfg['sw_position']
    #if 'sw_time' in CTcfg: del CTcfg['sw_time']
    return CTcfg
"""

