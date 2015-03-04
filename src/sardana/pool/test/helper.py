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
           'getTGConfiguration', 'split_MGConfigurations',
           'createElemConf', 'createCtrlConf', 'createConfbyCtrlKlass', 
           'createMGUserConfiguration']

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
    id = kwargs.get('id')
    if id == None:
        kwargs['id'] = pool.get_free_id()            
    kwargs['pool'] = pool
    return PoolMeasurementGroup(**kwargs)

def createPoolTGGenerationConfiguration(ctrls, ctrl_channels):
    '''Method to create TGGeneration configuration. Order of the sequences is 
    important. For all sequences, the element of a given position refers 
    the same controller. 
    
    :param ctrls: sequence of the controllers used by the action
    :type ctrls: seq<sardana.pool.PoolController>
    :param ctrl_channels: sequence of the sequences of the channels 
    corresponding to the controllers 
    :type ctrl_channels: seq<seq<sardana.pool.PoolTriggerGate>>

    :return: a configuration dictionary
    :rtype: dict<>
    '''

    ctrls_configuration = {}
    for ctrl, channels in zip(ctrls, ctrl_channels):
        ctrl_conf = createConfFromObj(ctrl)
        ctrl_conf['units'] = {}
        ctrl_conf['units']['0'] = main_unit_data = {}
        ctrl_conf['units']['0']['channels'] = {}
        for channel in channels:
            channel_conf = createConfFromObj(channel)
            main_unit_data['channels'][channel] = channel_conf
        ctrls_configuration[ctrl] = ctrl_conf
    configuration = {'controllers': ctrls_configuration}
    return configuration 


def createCTAcquisitionConfiguration(ctrls, ctrl_channels):
    '''Method to create CTAcquisition configuration. Order of the sequences is 
    important. For all sequences, the element of a given position refers 
    the same controller. 
    
    :param ctrls: sequence of the controllers used by the action
    :type ctrls: seq<sardana.pool.PoolController>
    :param ctrl_channels: sequence of the sequences of the channels 
    corresponding to the controllers 
    :type ctrl_channels: seq<seq<sardana.pool.PoolCounterTimer>>

    :return: a configuration dictionary
    :rtype: dict<>
    '''

    master_ctrl_idx = 0
    master_idx = 0
    configuration = {}
    ctrls_configuration = {}
    configuration['timer'] = ctrl_channels[master_ctrl_idx][master_idx]
    for ctrl, channels in zip(ctrls, ctrl_channels):
        ctrl_conf = createConfFromObj(ctrl)
        ctrl_conf['units'] = {}
        ctrl_conf['units']['0'] = main_unit_data = {}
        ctrl_conf['units']['0']['channels'] = {}
        for channel in channels:
            channel_conf = createConfFromObj(channel)
            main_unit_data['channels'][channel] = channel_conf
        main_unit_data['timer'] = channels[master_idx]
        ctrls_configuration[ctrl] = ctrl_conf
    configuration['controllers'] = ctrls_configuration
    return configuration 


def createMGUserConfiguration(pool, channels):
    '''Method to create MeasurementGroup configuration using strings. 
 
    
    :param channels: Each tuple: (expchan, associated_trigger, trigger_type) 
                    First element of the list of lists is the master 
                    counter/timer.
                    First element of each list is the master counter/timer 
                    from the controller.
    :type channels: seq<seq<tuple(str)>>
    :return: a tuple of three elements: measurement group configuration 
             dictionary of strings, sequence of channel ids, sequence of channel
             names
    :rtype: tupe(dict<>, seq<int>, seq<string>
    '''

    channel_ids = []
    channel_names = []
    MG_configuration = {}
    main_master_channel = pool.get_element_by_full_name(channels[0][0][0])
    MG_configuration['timer'] = main_master_channel.full_name
    MG_configuration['monitor'] = main_master_channel.full_name
    
    all_ctrls_d = {}
    index = 0 # index represents the order of the channels
    for i in range(len(channels)):
        channels_in_ctrl = channels[i]
        master_channel_str = channels[i][0][0]
        master_channel = pool.get_element_by_full_name(master_channel_str)
        ctrl = master_channel.get_controller()
        ctrl_full_name = ctrl.full_name

        ctrl_d = {}
        ctrl_d.update({ctrl_full_name:{}})

        unit_dict = {}
        unit_dict['monitor'] = master_channel_str
        unit_dict['timer'] = master_channel_str
        unit_dict['trigger_type'] = channels[i][0][2]
        channels_d = {}
        for chan_idx in range(len(channels_in_ctrl)):
            channel_name_str = channels_in_ctrl[chan_idx][0]
            channel_names.append(channel_name_str)
            channel_element = pool.get_element_by_full_name(channel_name_str)
            channel_ids.append(channel_element.id)
            one_channel_d = {}
            one_channel_d.update({'plot_type': 1})
            one_channel_d.update({'plot_axes': ['<mov>']})
            one_channel_d.update({'data_type': 'float64'})
            one_channel_d.update({'index': index})
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
            trig_elem_d = {'trigger_element': channels_in_ctrl[chan_idx][1]}
            one_channel_d.update(trig_elem_d)
            trigger_type_d = {'trigger_type': channels_in_ctrl[chan_idx][2]}
            one_channel_d.update(trigger_type_d)
            channels_d.update({channel_name_str:one_channel_d})
            index += 1

        unit_dict['channels'] = {}
        unit_dict['channels'].update(channels_d)    
        ctrl_d[ctrl_full_name]['units'] = {}
        ctrl_d[ctrl_full_name]['units']['0'] = unit_dict
        all_ctrls_d.update(ctrl_d)
    
    MG_configuration.update({'controllers':all_ctrls_d})
    return (MG_configuration, channel_ids, channel_names)


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

    return MG_configuration

def split_MGConfigurations(mg_cfg_in):
    """Split MeasurementGroup configuration with channels
    triggered by SW Trigger and channels triggered by HW trigger"""

    ctrls_in = mg_cfg_in['controllers']
    mg_sw_cfg_out = {}
    mg_hw_cfg_out = {}
    mg_sw_cfg_out['controllers'] = ctrls_sw_out = {}
    mg_hw_cfg_out['controllers'] = ctrls_hw_out = {}
    for ctrl, ctrl_info in ctrls_in.items():        
        tg_element = ctrl_info.get('trigger_element')
        if tg_element != None:
            tg_pool_ctrl = tg_element.get_controller() 
            tg_ctrl = tg_pool_ctrl._ctrl
            # TODO: filtering software and HW TG controllers on 
            # add_listener attribute, this is not generic!
            if hasattr(tg_ctrl, 'add_listener'):
                ctrls_sw_out[ctrl] = ctrl_info
            if not hasattr(tg_ctrl, 'add_listener'):
                ctrls_hw_out[ctrl] = ctrl_info
    # TODO: timer and monitor are just random elements!!!
    if len(ctrls_sw_out):
        mg_sw_cfg_out['timer'] = ctrls_sw_out.values()[0]['units']['0']['timer'] 
        mg_sw_cfg_out['monitor'] = ctrls_sw_out.values()[0]['units']['0']['monitor']  
    if len(ctrls_hw_out):
        mg_hw_cfg_out['timer'] = ctrls_hw_out.values()[0]['units']['0']['timer'] 
        mg_hw_cfg_out['monitor'] = ctrls_hw_out.values()[0]['units']['0']['monitor']    
    return (mg_sw_cfg_out, mg_hw_cfg_out)

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
            if (tg_element != None and tg_element not in _tg_element_list):
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
    #TODO: temporary returning tg_elements
    return TGcfg, _tg_element_list

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

def createConfFromObj(obj):
    cfg = dict({
            'name': obj.name,
            'full_name': obj.full_name,
            'id': obj.id
        })
    # TODO:
    #  enabling the channel - normally done when applying the MG conf.
    #  see poolmeasurementgroup.PoolMeasurementGroup._build_channel_defaults
    if ElementType[obj.get_type()] == 'CTExpChannel':
        cfg['enabled'] = True
    return cfg


