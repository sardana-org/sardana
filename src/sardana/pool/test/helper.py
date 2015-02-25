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
           'getTGConfiguration', 'getSWtg_MGConfiguration',
           'getHWtg_MGConfiguration', 'createElemConf',
           'createCtrlConf', 'createConfbyCtrlKlass', 
           'createMGuserConfiguration']

from sardana.sardanadefs import ElementType
from sardana.pool.poolcontroller import PoolController
from sardana.pool.poolcountertimer import PoolCounterTimer
from sardana.pool.pooltriggergate import PoolTriggerGate
from sardana.pool.poolmeasurementgroup import PoolMeasurementGroup

def createPoolController(pool, conf):
    '''Method to create a PoolController using a configuration dictionary
    '''
    kwargs = dict(conf)

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
    kwargs = dict(conf)
    kwargs['pool'] = pool
    kwargs['ctrl'] = poolcontroller
    return PoolCounterTimer(**kwargs)

def createPoolTriggerGate(pool, poolcontroller, conf):
    '''Method to create a PoolTriggerGate using a configuration dictionary
    '''
    kwargs = dict(conf)
    kwargs['pool'] = pool
    kwargs['ctrl'] = poolcontroller
    return PoolTriggerGate(**kwargs)

def createPoolMeasurementGroup(pool, conf):
    '''Method to create a PoolMeasurementGroup using a configuration dictionary
    '''
    kwargs = dict(conf)
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
        ctrl_conf = dict(ctrl_conf)
        ctrl_conf['units'] = {}
        ctrl_conf['units']['0'] = main_unit_data = {}
        ctrl_conf['units']['0']['channels'] = {}
        for channel, channel_conf in zip(channels, channels_conf):
            channel_conf = dict(channel_conf)
            main_unit_data['channels'][channel] = channel_conf
        main_unit_data['timer'] = channels[master_idx]
        ctrls_configuration[ctrl] = ctrl_conf
    configuration['controllers'] = ctrls_configuration
    return configuration 


def createMGuserConfiguration(pool, MGchannels):
    '''Method to create MeasurementGroup configuration using strings. 
 
    
    :param MGelems: Each tuple: (expchan, associated_trigger, trigger_type) 
                    First element of the list of lists is the master 
                    counter/timer.
                    First element of each list is the master counter/timer 
                    from the controller.
    :type MGelems: seq<seq<tuple(str)>>
    :return: measurement group configuration dictionary of strings.
    :rtype: dict<>
    '''

    MG_configuration = {}
    main_master_channel = pool.get_element_by_full_name(MGchannels[0][0][0])
    MG_configuration['timer'] = main_master_channel.full_name
    MG_configuration['monitor'] = main_master_channel.full_name
    
    all_ctrls_d = {}
    for i in range(len(MGchannels)):
        MGchannels_in_ctrl = MGchannels[i]
        master_channel_str = MGchannels[i][0][0]
        master_channel = pool.get_element_by_full_name(master_channel_str)
        ctrl = master_channel.get_controller()
        ctrl_full_name = ctrl.full_name

        ctrl_d = {}
        ctrl_d.update({ctrl_full_name:{}})

        unit_dict = {}
        unit_dict['monitor'] = master_channel_str
        unit_dict['timer'] = master_channel_str
        unit_dict['trigger_type'] = MGchannels[i][0][2]
        channels_d = {}
        for chan_idx in range(len(MGchannels_in_ctrl)):
            channel_name_str = MGchannels_in_ctrl[chan_idx][0]
            channel_element = pool.get_element_by_full_name(channel_name_str)
            one_channel_d = {}
            one_channel_d.update({'plot_type': 1})
            one_channel_d.update({'plot_axes': ['<mov>']})
            one_channel_d.update({'data_type': 'float64'})
            one_channel_d.update({'index': 0})
            one_channel_d.update({'enabled':True})
            one_channel_d.update({'nexus_path': ''})
            one_channel_d.update({'shape': []})
            ctrl_from_channel = channel_element.get_controller()
            ctrl_name = ctrl_from_channel.full_name
            one_channel_d.update({'_controller_name':ctrl_name})
            one_channel_d.update({'conditioning': ''})
            one_channel_d.update({'full_name':channel_name_str})
            one_channel_d.update({'_unit_id': '0'})
            one_channel_d.update({'id':channel_element.id})
            one_channel_d.update({'normalization': 0})
            one_channel_d.update({'output': True})
            one_channel_d.update({'label':channel_element.name})
            one_channel_d.update({'data_units': 'No unit'})
            one_channel_d.update({'name':channel_element.name})
            trig_elem_d = {'trigger_element': MGchannels_in_ctrl[chan_idx][1]}
            one_channel_d.update(trig_elem_d)
            trigger_type_d = {'trigger_type': MGchannels_in_ctrl[chan_idx][2]}
            one_channel_d.update(trigger_type_d)
            channels_d.update({channel_name_str:one_channel_d})

        unit_dict['channels'] = {}
        unit_dict['channels'].update(channels_d)    
        ctrl_d[ctrl_full_name]['units'] = {}
        ctrl_d[ctrl_full_name]['units']['0'] = unit_dict
        all_ctrls_d.update(ctrl_d)
    
    MG_configuration.update({'controllers':all_ctrls_d})
    return MG_configuration


def createMGConfiguration(ctrls, ctrls_conf, ctrl_channels, ctrl_channels_conf,
                          ctrl_trigger_elements, ctrl_trigger_types):
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
    :param trigger_types: sequence of the sequences of the trigger elements
    :type trigger_types: seq<seq<str>>
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
    MG_configuration['monitor'] = ctrl_channels[master_ctrl_idx][master_idx]
    for ctrl, ctrl_conf, channels, channels_conf, trigger_elements, \
            trigger_types in zip(ctrls, ctrls_conf, ctrl_channels, 
            ctrl_channels_conf, ctrl_trigger_elements, ctrl_trigger_types):
        ctrl_conf['units'] = {}
        ctrl_conf['units']['0'] = main_unit_data = {}
        ctrl_conf['units']['0']['channels'] = {}
        index = 0
        for channel, channel_conf, trigger_element, trigger_type in \
              zip(channels, channels_conf, trigger_elements, trigger_types):
            main_unit_data['channels'][channel] = channel_conf
            main_unit_data['channels'][channel]['trigger_element'] = \
                                                                trigger_element
            # TODO: decide if trigger_type (trigger_type) should be global for 
            # the controller or be channel specific
            main_unit_data['channels'][channel]['trigger_type'] = trigger_type
            # this way we are forcing the trigger_type of the last channel
            main_unit_data['trigger_type'] = trigger_type
            # TODO: investigate why we need the index!
            # adding a dummy index
            main_unit_data['channels'][channel]['index'] = index
            if trigger_element not in _tg_elements:
                _tg_elements.append(trigger_element)
            index += 1           

        main_unit_data['timer'] = channels[master_idx]
        main_unit_data['monitor'] = channels[master_idx]
        ctrls_configuration[ctrl] = ctrl_conf
    MG_configuration['controllers'] = ctrls_configuration

    if 'sw_position' in _tg_elements:
        MG_configuration['sw_position'] = True
    if 'sw_time' in _tg_elements:
        MG_configuration['sw_time'] = True    

    return MG_configuration


def getSWtg_MGConfiguration(MGCfg):
    """Get Measurement group configuration with only the channel elements
    triggered by a SW Trigger"""

    # Get all trigger_elements ('sw_time', 'sw_position', 'hw_tg_element') 
    #sw_hw_tg list organized by controller 
    #ex: sw_hw_tg = [[sw_time, sw_position, tg1],[sw_time],[tg1, tg2]]
    # organized in a list by controller.
    # This part of code is common to look for sw and for hw triggered counters
    sw_hw_tg = []
    ctr = MGCfg['controllers']
    
    for idx_ctrl in range(len(ctr)):
        sw_hw_tg.append([])
        channels = ctr[ctr.keys()[idx_ctrl]]['units']['0']['channels']
        for channel in channels:
            trigger_element = channels[channel].get('trigger_element', None)
            if trigger_element != None:
                sw_hw_tg[idx_ctrl].append(trigger_element)
           
    # Get index of controllers which contains SW tg elements
    ctrl_sw_list = []
    for ctr_i in range(len(sw_hw_tg)):
        for ch_j in range(len(sw_hw_tg[ctr_i])):
            if (sw_hw_tg[ctr_i][ch_j] == 'sw_time' or
                sw_hw_tg[ctr_i][ch_j] == 'sw_position'):
                ctrl_sw_list.append(ctr_i)
                break

    # Build the new dictionary with only SW_tg elements
    swtg_MGcfg = {}
    ctr_sw = {}
    for ctrl_num in ctrl_sw_list:
        key_ctr = ctr.keys()[ctrl_num]
        single_unit = ctr[key_ctr]['units']['0']
        ch_orig = single_unit['channels']
        ctr_sw[key_ctr] = {}
        for key in ctr[key_ctr]:
            if key != 'units':
                ctr_sw[key_ctr][key] = ctr[key_ctr][key]
        ctr_sw[key_ctr]['units'] = {}
        new_single_unit = ctr_sw[key_ctr]['units']['0'] = {}
        ch_dict = new_single_unit['channels'] = {}

        for key in single_unit.keys():
            if key != 'channels':
                new_single_unit[key] = single_unit[key]

        elem_from_ctrl = 0
        for elem_type in sw_hw_tg[ctrl_num]:
            if (elem_type == 'sw_time' or elem_type == 'sw_position'):
                ch_dict[ch_orig.keys()[elem_from_ctrl]] = \
                            ch_orig[ch_orig.keys()[elem_from_ctrl]]
            elem_from_ctrl = elem_from_ctrl + 1
            
    swtg_MGcfg['controllers'] = ctr_sw
    for key in MGCfg:
        if key != 'controllers':
            swtg_MGcfg[key] = MGCfg[key]
    
    return swtg_MGcfg


def getHWtg_MGConfiguration(MGCfg):
    """Get Measurement group configuration with only the channel elements
    triggered by a HW Trigger"""

    # Get all trigger_elements ('sw_time', 'sw_position', 'hw_tg_element') 
    #sw_hw_tg list organized by controller 
    #ex: sw_hw_tg = [[sw_time, sw_position, tg1],[hw_time],[tg1, tg2]]
    # organized in a list by controller.
    # This part of code is common to look for hw and for hw triggered counters
    sw_hw_tg = []
    ctr = MGCfg['controllers']
    
    for idx_ctrl in range(len(ctr)):
        sw_hw_tg.append([])
        channels = ctr[ctr.keys()[idx_ctrl]]['units']['0']['channels']
        for channel in channels:
            trigger_element = channels[channel].get('trigger_element', None)
            if trigger_element != None:
                sw_hw_tg[idx_ctrl].append(trigger_element)
           
    # Get index of controllers which contains HW tg elements
    ctrl_hw_list = []
    for ctr_i in range(len(sw_hw_tg)):
        for ch_j in range(len(sw_hw_tg[ctr_i])):
            if (sw_hw_tg[ctr_i][ch_j] != 'sw_time' and
                sw_hw_tg[ctr_i][ch_j] != 'sw_position'):
                ctrl_hw_list.append(ctr_i)
                break

    # Build the new dictionary with only HW_tg elements
    hwtg_MGcfg = {}
    ctr_hw = {}
    for ctrl_num in ctrl_hw_list:
        key_ctr = ctr.keys()[ctrl_num]
        single_unit = ctr[key_ctr]['units']['0']
        ch_orig = single_unit['channels']
        ctr_hw[key_ctr] = {}
        for key in ctr[key_ctr]:
            if key != 'units':
                ctr_hw[key_ctr][key] = ctr[key_ctr][key]
        ctr_hw[key_ctr]['units'] = {}
        new_single_unit = ctr_hw[key_ctr]['units']['0'] = {}
        ch_dict = new_single_unit['channels'] = {}

        for key in single_unit.keys():
            if key != 'channels':
                new_single_unit[key] = single_unit[key]

        elem_from_ctrl = 0
        for elem_type in sw_hw_tg[ctrl_num]:
            if (elem_type != 'sw_time' and elem_type != 'sw_position'):
                ch_dict[ch_orig.keys()[elem_from_ctrl]] = \
                            ch_orig[ch_orig.keys()[elem_from_ctrl]]
            elem_from_ctrl = elem_from_ctrl + 1
            
    hwtg_MGcfg['controllers'] = ctr_hw
    for key in MGCfg:
        if key != 'controllers':
            hwtg_MGcfg[key] = MGCfg[key]
    
    return hwtg_MGcfg


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
            tg_element = channels_dict[channel].get('trigger_element', None)
            if (tg_element != None and tg_element not in _tg_element_list and 
                tg_element != 'sw_time' and tg_element != 'sw_position'):
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

def createConfbyCtrlKlass(pool, ctrl_klass, ctrl_name):
    pool_mng = pool.get_manager()
    klass = ctrl_klass
    meta = pool_mng.getControllerMetaClass(klass)
    _lib = meta.lib
    #TODO check is is a valid name
    # raise Exception("The %s ctrl exists." % ctrl_name)
    name = full_name = ctrl_name
    ctrl_id =  pool.get_free_id()
    lib_name = _lib.full_name
    ctrl_type = ElementType[meta.get_type()]

    cfg = dict({ 'class_info': None,
                 'full_name': full_name,
                 'id': ctrl_id,
                 'klass': klass,
                 'lib_info': None,
                 'library': lib_name,
                 'name': name,
                 'pool': None,
                 'properties': {},
                 'role_ids': '',
                 'type': ctrl_type})
    return cfg

def createCtrlConf(pool, name, klass, lib):
    cfg = dict({ 'class_info': None,
                 'full_name': None,
                 'id': None,
                 'klass': None,
                 'lib_info': None,
                 'library': lib,
                 'name': name,
                 'pool': None,
                 'properties': {},
                 'role_ids': '',
                 'type': 'ControllerClass'})
    cfg['id'] = pool.get_free_id()
    cfg['name'] = cfg['full_name'] = name
    cfg['klass'] = klass
    cfg['library'] = lib
    return cfg

def createElemConf(pool, axis, name):
    cfg = dict({ 'axis': None,
                 'ctrl': None,
                 'full_name': '',
                 'id': None,
                 'name': '',
                 'pool': None })
    cfg['id'] = pool.get_free_id()
    cfg['axis'] = axis
    cfg['name'] = cfg['full_name'] = name
    return cfg

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

# This cannot be used without modifying the MGcfg. 
# Delete elements of MGcfg deletes it as well the elements in original MGcfg.
def getCTConfiguration(MGcfg):
    Extract CT configuration from complete MG configuration.

    CTcfg = copy.deepcopy(MGcfg)
    delKeys(CTcfg, 'trigger_element')
    delKeys(CTcfg, 'trigger_type')
    #if 'sw_position' in CTcfg: del CTcfg['sw_position']
    #if 'sw_time' in CTcfg: del CTcfg['sw_time']
    return CTcfg
"""

