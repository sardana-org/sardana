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

__all__ = ['createPoolController', 'createPoolCounterTimer',
           'createPoolZeroDExpChannel', 'createPoolTwoDExpChannel',
           'createPoolTriggerGate',
           'createPoolMotor', 'createPoolPseudoCounter',
           'createPoolPseudoMotor', 'createPoolMeasurementGroup',
           'createControllerConfiguration',
           'createTimerableControllerConfiguration',
           'createCTAcquisitionConfiguration',
           'createElemConf', 'createCtrlConf', 'createConfbyCtrlKlass',
           'createMGUserConfiguration']
import copy

from sardana.sardanadefs import ElementType
from sardana.pool.poolcontroller import PoolController,\
    PoolPseudoMotorController, PoolPseudoCounterController
from sardana.pool.poolcountertimer import PoolCounterTimer
from sardana.pool.poolzerodexpchannel import Pool0DExpChannel
from sardana.pool.pooltwodexpchannel import Pool2DExpChannel
from sardana.pool.pooltriggergate import PoolTriggerGate
from sardana.pool.poolmotor import PoolMotor
from sardana.pool.poolpseudocounter import PoolPseudoCounter
from sardana.pool.poolpseudomotor import PoolPseudoMotor
from sardana.pool.poolmeasurementgroup import PoolMeasurementGroup, \
    MeasurementConfiguration, ControllerConfiguration, ChannelConfiguration


def createPoolController(pool, conf):
    '''Method to create a PoolController using a configuration dictionary
    '''
    kwargs = copy.deepcopy(conf)

    ctrl_manager = pool.ctrl_manager
    ctrl_class_info = None
    ctrl_lib_info = ctrl_manager.getControllerLib(kwargs['library'])
    if ctrl_lib_info is not None:
        ctrl_class_info = ctrl_lib_info.get_controller(kwargs['klass'])
    main_type = ctrl_class_info.type_names[0]
    # check if all controller properties are present in conf.
    # in case of missing prop. and existing default value, use the default
    properties = kwargs['properties']
    if ctrl_class_info:
        ctrl_properties = ctrl_class_info.ctrl_properties
    else:
        ctrl_properties = {}
    for prop_info in list(ctrl_properties.values()):
        prop_name = prop_info.name
        prop_value = properties.get(prop_name)
        if prop_value is None:
            if prop_info.default_value is None:
                class_name = ctrl_class_info.get_name()
                raise Exception("Controller class '%s' needs property '%s'"
                                % (class_name, prop_name))
            properties[prop_name] = prop_info.default_value
    kwargs['pool'] = pool
    kwargs['lib_info'] = ctrl_lib_info
    kwargs['class_info'] = ctrl_class_info
    if main_type == "PseudoMotor":
        klass = PoolPseudoMotorController
    elif main_type == "PseudoCounter":
        klass = PoolPseudoCounterController
    else:
        klass = PoolController
    return klass(**kwargs)


def createPoolCounterTimer(pool, poolcontroller, conf):
    '''Method to create a PoolCounterTimer using a configuration dictionary
    '''
    kwargs = copy.deepcopy(conf)
    kwargs['pool'] = pool
    kwargs['ctrl'] = poolcontroller
    ct = PoolCounterTimer(**kwargs)
    poolcontroller.add_element(ct)
    return ct


def createPoolZeroDExpChannel(pool, poolcontroller, conf):
    '''Method to create a ZeroDExpChannel using a configuration dictionary
    '''
    kwargs = copy.deepcopy(conf)
    kwargs['pool'] = pool
    kwargs['ctrl'] = poolcontroller
    return Pool0DExpChannel(**kwargs)


def createPoolTwoDExpChannel(pool, poolcontroller, conf):
    '''Method to create a ZeroDExpChannel using a configuration dictionary
    '''
    kwargs = copy.deepcopy(conf)
    kwargs['pool'] = pool
    kwargs['ctrl'] = poolcontroller
    return Pool2DExpChannel(**kwargs)


def createPoolTriggerGate(pool, poolcontroller, conf):
    '''Method to create a PoolTriggerGate using a configuration dictionary
    '''
    kwargs = copy.deepcopy(conf)
    kwargs['pool'] = pool
    kwargs['ctrl'] = poolcontroller
    return PoolTriggerGate(**kwargs)


def createPoolMotor(pool, poolcontroller, conf):
    '''Method to create a PoolMotor using a configuration dictionary
    '''
    kwargs = copy.deepcopy(conf)
    kwargs['pool'] = pool
    kwargs['ctrl'] = poolcontroller
    return PoolMotor(**kwargs)


def createPoolPseudoCounter(pool, poolcontroller, conf, elements=()):
    '''Method to create a PoolPseudoCounter using a configuration dictionary
    '''
    kwargs = copy.deepcopy(conf)
    kwargs['pool'] = pool
    kwargs['ctrl'] = poolcontroller
    kwargs['user_elements'] = elements
    return PoolPseudoCounter(**kwargs)


def createPoolPseudoMotor(pool, poolcontroller, conf, elements=()):
    '''Method to create a PoolPseudoMotor using a configuration dictionary
    '''
    kwargs = copy.deepcopy(conf)
    kwargs['pool'] = pool
    kwargs['ctrl'] = poolcontroller
    kwargs['user_elements'] = elements
    return PoolPseudoMotor(**kwargs)


def createPoolMeasurementGroup(pool, conf):
    '''Method to create a PoolMeasurementGroup using a configuration dictionary
    '''
    kwargs = copy.deepcopy(conf)
    id = kwargs.get('id')
    if id is None:
        kwargs['id'] = pool.get_free_id()
    kwargs['pool'] = pool
    return PoolMeasurementGroup(**kwargs)


def createControllerConfiguration(pool_ctrl, pool_channels):
    conf_ctrl = ControllerConfiguration(pool_ctrl)
    for pool_channel in pool_channels:
        channel = ChannelConfiguration(pool_channel)
        channel.controller = conf_ctrl
        conf_ctrl.add_channel(channel)
    return conf_ctrl


def createTimerableControllerConfiguration(pool_ctrl, pool_channels):
    conf_ctrl = createControllerConfiguration(pool_ctrl, pool_channels)
    channel = conf_ctrl.get_channels(enabled=True)[0]
    conf_ctrl.timer = channel
    conf_ctrl.monitor = channel
    return conf_ctrl


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
    configuration['timer'] = timer = ctrl_channels[master_ctrl_idx][master_idx]
    for ctrl, channels in zip(ctrls, ctrl_channels):
        ctrl_data = createConfFromObj(ctrl)
        ctrl_data['channels'] = {}
        for channel in channels:
            channel_conf = createConfFromObj(channel)
            ctrl_data['channels'][channel] = channel_conf
        ctrl_data['timer'] = channels[master_idx]
        ctrls_configuration[ctrl] = ctrl_data
    configuration['controllers'] = ctrls_configuration
    mg_cfg = MeasurementConfiguration()
    mg_cfg._config = configuration
    mg_cfg.hw_sync_monitor = timer
    mg_cfg.hw_sync_timer = timer
    mg_cfg.sw_sync_timer = timer
    mg_cfg.sw_sync_monitor = timer
    mg_cfg.ctrl_hw_sync = ctrls_configuration
    mg_cfg.ctrl_sw_sync = ctrls_configuration

    return mg_cfg


def createMGUserConfiguration(pool, channels):
    '''Method to create MeasurementGroup configuration using strings.


    :param channels: Each tuple: (expchan, associated_trigger, synchronization)
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
    index = 0  # index represents the order of the channels
    for i in range(len(channels)):
        channels_in_ctrl = channels[i]
        master_channel_str = channels[i][0][0]
        master_channel = pool.get_element_by_full_name(master_channel_str)
        ctrl = master_channel.get_controller()
        ctrl_full_name = ctrl.full_name

        ctrl_d = {}
        ctrl_d.update({ctrl_full_name: {}})

        ctrl_data = {}
        ctrl_data['monitor'] = master_channel_str
        ctrl_data['timer'] = master_channel_str
        ctrl_data['synchronization'] = channels[i][0][2]
        ctrl_data['synchronizer'] = channels[i][0][1]
        channels_d = {}
        for chan_idx in range(len(channels_in_ctrl)):
            channel_name_str = channels_in_ctrl[chan_idx][0]
            channel_names.append(channel_name_str)
            channel_element = pool.get_element_by_full_name(channel_name_str)
            channel_ids.append(channel_element.id)
            one_channel_d = {}
            one_channel_d.update({'full_name': channel_name_str})
            one_channel_d.update({'index': index})
            channels_d.update({channel_name_str: one_channel_d})
            index += 1
        ctrl_data['channels'] = {}
        ctrl_data['channels'].update(channels_d)
        ctrl_d[ctrl_full_name] = ctrl_data
        all_ctrls_d.update(ctrl_d)

    MG_configuration.update({'controllers': all_ctrls_d})
    return MG_configuration, channel_ids, channel_names


def createConfbyCtrlKlass(pool, ctrl_klass, ctrl_name):
    pool_mng = pool.get_manager()
    klass = ctrl_klass
    meta = pool_mng.getControllerMetaClass(klass)
    _lib = meta.lib
    # TODO check is is a valid name
    # raise Exception("The %s ctrl exists." % ctrl_name)
    name = full_name = ctrl_name
    ctrl_id = pool.get_free_id()
    lib_name = _lib.full_name
    ctrl_type = ElementType[meta.get_type()]

    cfg = dict({'class_info': None,
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


def createCtrlConf(pool, name, klass, lib, props={}):
    cfg = dict({'class_info': None,
                'full_name': None,
                'id': None,
                'klass': None,
                'lib_info': None,
                'library': lib,
                'name': name,
                'pool': None,
                'properties': props,
                'role_ids': '',
                'type': 'ControllerClass'})
    cfg['id'] = pool.get_free_id()
    cfg['name'] = cfg['full_name'] = name
    cfg['klass'] = klass
    cfg['library'] = lib
    return cfg


def createElemConf(pool, axis, name):
    cfg = dict({'axis': None,
                'ctrl': None,
                'full_name': '',
                'id': None,
                'name': '',
                'pool': None})
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
