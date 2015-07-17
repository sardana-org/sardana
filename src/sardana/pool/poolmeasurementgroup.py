#!/usr/bin/env python

##############################################################################
##
## This file is part of Sardana
##
## http://www.sardana-controls.org/
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

"""This module is part of the Python Pool library. It defines the base classes
for"""

__all__ = ["PoolMeasurementGroup"]

__docformat__ = 'restructuredtext'

from taurus.core.taurusvalidator import AttributeNameValidator

from sardana import State, ElementType, \
    TYPE_EXP_CHANNEL_ELEMENTS, TYPE_TIMERABLE_ELEMENTS
from sardana.sardanaevent import EventType
from sardana.pool.pooldefs import AcqMode, AcqTriggerType
from sardana.pool.poolgroupelement import PoolGroupElement
from sardana.pool.poolacquisition import PoolAcquisition
from sardana.pool.poolexternal import PoolExternalObject
from sardana.pool.pooltggeneration import PoolTGGeneration

from sardana.taurus.core.tango.sardana import PlotType, Normalization

#----------------------------------------------
# Measurement Group Configuration information
#----------------------------------------------
# dict <str, obj> with (at least) keys:
#    - 'timer' : the timer channel name / timer channel id
#    - 'monitor' : the monitor channel name / monitor channel id
#    - 'controllers' : dict<Controller, dict> where:
#        - key: ctrl
#        - value: dict<str, dict> with (at least) keys:
#                - 'timer' : the timer channel name / timer channel id
#                - 'monitor' : the monitor channel name / monitor channel id
#                - 'trigger_type' : 'Gate'/'Software'
#                - 'channels' where value is a dict<str, obj> with (at least) keys:
#                    - 'id' : the channel name ( channel id )
#                    optional keys:
#                    - 'enabled' : True/False (default is True)
#                    any hints:
#                    - 'output' : True/False (default is True)
#                    - 'plot_type' : 'No'/'1D'/'2D' (default is 'No')
#                    - 'plot_axes' : list<str> 'where str is channel name/'step#/'index#' (default is [])
#                    - 'label' : prefered label (default is channel name)
#                    - 'scale' : <float, float> with min/max (defaults to channel
#                                range if it is defined
#                    - 'plot_color' : int representing RGB
#    optional keys:
#    - 'label' : measurement group label (defaults to measurement group name)
#    - 'description' : measurement group description

# <MeasurementGroupConfiguration>
#  <timer>UxTimer</timer>
#  <monitor>CT1</monitor>
# </MeasurementGroupConfiguration>

# Example: 2 NI cards, where channel 1 of card 1 is wired to channel 1 of card 2
# at configuration time we should set:
# ni0ctrl.setCtrlPar(0, 'trigger_type', AcqTriggerType.Software)
# ni0ctrl.setCtrlPar(0, 'timer', 1) # channel 1 is the timer
# ni0ctrl.setCtrlPar(0, 'monitor', 4) # channel 4 is the monitor
# ni1ctrl.setCtrlPar(0, 'trigger_type', AcqTriggerType.ExternalTrigger)
# ni1ctrl.setCtrlPar(0, 'master', 0)

# when we count for 1.5 seconds:
# ni1ctrl.Load(1.5)
# ni0ctrl.Load(1.5)
# ni1ctrl.Start()
# ni0ctrl.Start()

"""

"""

class PoolMeasurementGroup(PoolGroupElement):

    DFT_DESC = 'General purpose measurement group'

    def __init__(self, **kwargs):
        self._integration_time = None
        self._monitor_count = None
        self._offset = 0
        self._repetitions = 1
        self._acquisition_mode = AcqMode.Timer
        self._config = None
        self._config_dirty = True
        kwargs['elem_type'] = ElementType.MeasurementGroup
        PoolGroupElement.__init__(self, **kwargs)
        self.set_configuration(kwargs.get('configuration'))

    def _create_action_cache(self):
        acq_name = "%s.Acquisition" % self._name        
        return PoolAcquisition(self, acq_name)

    def _calculate_element_state(self, elem, elem_state_info):
        if elem.get_type() == ElementType.ZeroDExpChannel:
            if elem_state_info[0] == State.Moving:
                elem_state_info = State.On, elem_state_info[1]
        return PoolGroupElement._calculate_element_state(self, elem,
                                                         elem_state_info)

    def on_element_changed(self, evt_src, evt_type, evt_value):
        name = evt_type.name
        if name == 'state':
            if evt_src.get_type() == ElementType.ZeroDExpChannel:
                # 0D channels are "passive", which means they cannot contribute
                # to set the measurement group into a moving state
                if evt_value in (State.On, State.Moving):
                    return
            state, status = self._calculate_states()
            self.set_state(state, propagate=2)
            self.set_status("\n".join(status))

    def get_pool_controllers(self):
        return self.get_acquisition().get_pool_controllers()

    def get_pool_controller_by_name(self, name):
        name = name.lower()
        for ctrl in self.get_pool_controllers():
            if ctrl.name.lower() == name or ctrl.full_name.lower() == name:
                return ctrl
            
    def add_user_element(self, element, index=None):
        '''Override the base behavior, so the TriggerGate elements are silently 
        skipped if used multiple times in the group'''
        user_elements = self._user_elements
        if element in user_elements:
            # skipping TriggerGate element if already present  
            if element.get_type() is ElementType.TriggerGate:
                return
        return PoolGroupElement.add_user_element(self, element, index)
    # --------------------------------------------------------------------------
    # configuration
    # --------------------------------------------------------------------------

    def _is_managed_element(self, element):
        element_type = element.get_type()
        # TODO: TriggerGate elements are treated as managed elements,
        # this was not yet 100% tested
        return element_type in TYPE_EXP_CHANNEL_ELEMENTS or\
               element_type is ElementType.TriggerGate
                

        """Fills the channel default values for the given channel dictionary"""
    def _build_channel_defaults(self, channel_data, channel):

        external_from_name = isinstance(channel, (str, unicode))
        ndim = None
        instrument = None
        if external_from_name:
            name = full_name = source = channel
        else:
            name = channel.name
            full_name = channel.full_name
            source = channel.get_source()
            ndim = None
            instrument = None
            ctype = channel.get_type()
            if ctype != ElementType.External:
                instrument = channel.instrument
            if ctype == ElementType.CTExpChannel:
                ndim = 0
            elif ctype == ElementType.PseudoCounter:
                ndim = 0
            elif ctype == ElementType.ZeroDExpChannel:
                ndim = 0
            elif ctype == ElementType.OneDExpChannel:
                ndim = 1
            elif ctype == ElementType.TwoDExpChannel:
                ndim = 2
            elif ctype == ElementType.External:
                config = channel.get_config()
                if config is not None:
                    ndim = int(config.data_format)
            elif ctype == ElementType.IORegister:
                ndim = 0

        # Definitively should be initialized by measurement group
        # index MUST be here already (asserting this in the following line)
        channel_data['index'] = channel_data['index']
        channel_data['name'] = channel_data.get('name', name)
        channel_data['full_name'] = channel_data.get('full_name', full_name)
        channel_data['source'] = channel_data.get('source', source)
        channel_data['enabled'] = channel_data.get('enabled', True)
        channel_data['label'] = channel_data.get('label', channel_data['name'])
        channel_data['instrument'] = channel_data.get('instrument', getattr(instrument, 'name', None))
        channel_data['ndim'] = ndim
        # Probably should be initialized by measurement group
        channel_data['output'] = channel_data.get('output', True)

        # Perhaps should NOT be initialized by measurement group
        channel_data['plot_type'] = channel_data.get('plot_type', PlotType.No)
        channel_data['plot_axes'] = channel_data.get('plot_axes', [])
        channel_data['conditioning'] = channel_data.get('conditioning', '')
        channel_data['normalization'] = channel_data.get('normalization', Normalization.No)

        return channel_data

    def _build_configuration(self):
        """Builds a configuration object from the list of elements"""
        config = {}
        user_elements = self.get_user_elements()
        ctrls = self.get_pool_controllers()

        # find the first CT
        first_timerable = None
        for elem in user_elements:
            if elem.get_type() in TYPE_TIMERABLE_ELEMENTS:
                first_timerable = elem
                break
        if first_timerable is None:
            raise Exception("It is not possible to construct a measurement "
                            "group without at least one timer able channel "
                            "(Counter/timer, 1D or 2D)")
        g_timer = g_monitor = first_timerable
        config['timer'] = g_timer
        config['monitor'] = g_monitor
        config['controllers'] = controllers = {}

        external_user_elements = []
        for index, element in enumerate(user_elements):
            elem_type = element.get_type()
            if elem_type == ElementType.External:
                external_user_elements.append((index, element))
                continue

            ctrl = element.controller
            ctrl_data = controllers.get(ctrl)

            if ctrl_data is None:
                controllers[ctrl] = ctrl_data = {}
                ctrl_data['channels'] = channels = {}
                if elem_type in TYPE_TIMERABLE_ELEMENTS:
                    elements = ctrls[ctrl]
                    if g_timer in elements:
                        ctrl_data['timer'] = g_timer
                    else:
                        ctrl_data['timer'] = elements[0]
                    if g_monitor in elements:
                        ctrl_data['monitor'] = g_monitor
                    else:
                        ctrl_data['monitor'] = elements[0]
                    ctrl_data['trigger_type'] = AcqTriggerType.Software
            else:
                channels = ctrl_data['channels']
            channels[element] = channel_data = {}
            channel_data['index'] = user_elements.index(element)
            channel_data = self._build_channel_defaults(channel_data, element)
        config['label'] = self.name
        config['description'] = self.DFT_DESC

        if len(external_user_elements) > 0:
            controllers['__tango__'] = ctrl_data = {}
            ctrl_data['channels'] = channels = {}
            for index, element in external_user_elements:
                channels[element] = channel_data = {}
                channel_data['index'] = index
                channel_data = self._build_channel_defaults(channel_data, element)
        return config

    def set_configuration(self, config=None, propagate=1):
        if config is None:
            config = self._build_configuration()
        else:
            # create a configuration based on a new configuration
            user_elem_ids = {}
            tg_elem_ids = []
            pool = self.pool
            for c, c_data in config['controllers'].items():
                external = isinstance(c, (str, unicode))
                for channel_data in c_data['channels'].values():
                    if external:
                        element = id = channel_data['full_name']
                        channel_data['source'] = id
                    else:
                        element = pool.get_element_by_full_name(channel_data['full_name'])
                        id = element.id
                    user_elem_ids[channel_data['index']] = id
                    channel_data = self._build_channel_defaults(channel_data, element)
                    # creating TG information
                trigger_name = c_data.get('trigger_element')
                # TODO: protecting measurement groups which do not have trigger_element
                # if trigger_element will have a default value we could remove this protection
                if not trigger_name:
                    continue
                trigger_element = pool.get_element_by_full_name(trigger_name)
                c_data['trigger_element'] = trigger_element
                tg_elem_ids.append(trigger_element.id)
            indexes = sorted(user_elem_ids.keys())
            assert indexes == range(len(indexes))
            user_elem_ids_list = [ user_elem_ids[idx] for idx in indexes ]
            user_elem_ids_list.extend(tg_elem_ids)
            self.set_user_element_ids(user_elem_ids_list)

        g_timer, g_monitor = config['timer'], config['monitor']

        timer_ctrl_data = config['controllers'][g_timer.controller]
        if timer_ctrl_data['timer'] != g_timer:
            self.warning('controller timer and global timer mismatch. '
                         'Using global timer')
            self.debug('For controller %s, timer is defined as channel %s. '
                       'The global timer is set to channel %s which belongs '
                       'to the same controller', g_timer.controller.name,
                       timer_ctrl_data['timer'].name, g_timer.name)
            timer_ctrl_data['timer'] = g_timer

        monitor_ctrl_data = config['controllers'][g_monitor.controller]
        if monitor_ctrl_data['monitor'] != g_monitor:
            self.warning('controller monitor and global monitor mismatch. '
                         'Using global monitor')
            self.debug('For controller %s, monitor is defined as channel %s. '
                       'The global timer is set to channel %s which belongs '
                       'to the same controller', g_monitor.controller.name,
                       monitor_ctrl_data['monitor'].name, g_monitor.name)
            monitor_ctrl_data['monitor'] != g_monitor

        self._config = config
        self._config_dirty = True
        if not propagate:
            return
        self.fire_event(EventType("configuration", priority=propagate), config)

    def set_configuration_from_user(self, cfg, propagate=1):
        self.debug('set_configuration_from_user: entering...')
        config = {}
        user_elements = self.get_user_elements()
        pool = self.pool
        timer_name = cfg.get('timer', user_elements[0].full_name)
        monitor_name = cfg.get('monitor', user_elements[0].full_name)
        config['timer'] = pool.get_element_by_full_name(timer_name)
        config['monitor'] = pool.get_element_by_full_name(monitor_name)
        config['controllers'] = controllers = {}

        for c_name, c_data in cfg['controllers'].items():
            # discard controllers which don't have items (garbage)
            ch_count = len(c_data['channels'])
            if ch_count == 0:
                continue

            external = c_name.startswith('__')
            if external:
                ctrl = c_name
            else:
                ctrl = pool.get_element_by_full_name(c_name)
                assert ctrl.get_type() == ElementType.Controller
            controllers[ctrl] = ctrl_data = {}
            if not external and ctrl.is_timerable():
                ctrl_data['timer'] = pool.get_element_by_full_name(c_data['timer'])
                ctrl_data['monitor'] = pool.get_element_by_full_name(c_data['monitor'])
                ctrl_data['trigger_type'] = c_data['trigger_type']
                _ctrl = cfg['controllers'][c_name]
                if _ctrl.has_key('trigger_element'):
                    trigger_element = _ctrl['trigger_element'] #pool.get_element_by_full_name(_ctrl['trigger_element'])
                    ctrl_data['trigger_element'] = trigger_element

            ctrl_data['channels'] = channels = {}
            for ch_name, ch_data in c_data['channels'].items():
                if external:
                    validator = AttributeNameValidator()
                    params = validator.getParams(ch_data['full_name'])
                    params['pool'] = self.pool
                    channel = PoolExternalObject(**params)
                else:
                    channel = pool.get_element_by_full_name(ch_name)
                channels[channel] = dict(ch_data)

        config['label'] = cfg.get('label', self.name)
        config['description'] = cfg.get('description', self.DFT_DESC)

        self.set_configuration(config, propagate=propagate)

    def get_configuration(self):
        return self._config

    def get_user_configuration(self):
        cfg = self.get_configuration()
        config = {}

        config['timer'] = cfg['timer'].full_name
        config['monitor'] = cfg['monitor'].full_name
        config['controllers'] = controllers = {}

        for c, c_data in cfg['controllers'].items():
            ctrl_name = c
            if not isinstance(c, (str, unicode)):
                ctrl_name = c.full_name
            external = ctrl_name.startswith('__')
            controllers[ctrl_name] = ctrl_data = {}
            if not external and c.is_timerable():
                if c_data.has_key('timer'):
                    ctrl_data['timer'] = c_data['timer'].full_name
                if c_data.has_key('monitor'):
                    ctrl_data['monitor'] = c_data['monitor'].full_name
                if c_data.has_key('trigger_type'):
                    ctrl_data['trigger_type'] = c_data['trigger_type']
                if c_data.has_key('trigger_element'):
                    # use trigger_element with string instead of objects
                    # otherwise JSON serialization errors are raised
                    tg_full_name = c_data['trigger_element'].full_name
                    ctrl_data['trigger_element'] = tg_full_name
            ctrl_data['channels'] = channels = {}
            for ch, ch_data in c_data['channels'].items():
                channels[ch.full_name] = dict(ch_data)

        config['label'] = cfg['label']
        config['description'] = cfg['description']
        return config

    def load_configuration(self, force=False):
        """Loads the current configuration to all involved controllers"""
        cfg = self.get_configuration()
        g_timer, g_monitor = cfg['timer'], cfg['monitor']
        for ctrl, ctrl_data in cfg['controllers'].items():
            # skip external channels
            if type(ctrl) is str:
                continue
            # telling controller in which acquisition mode it will participate
            ctrl.set_ctrl_par('acquisition_mode', self.acquisition_mode)
            #@TODO: fix optimization and enable it again
            if ctrl.operator == self and not force and not self._config_dirty:
                continue
            ctrl.operator = self
            if ctrl.is_timerable():
                #if ctrl == g_timer.controller:
                #    ctrl.set_ctrl_par('timer', g_timer.axis)
                #if ctrl == g_monitor.controller:
                #    ctrl.set_ctrl_par('monitor', g_monitor.axis)
                ctrl.set_ctrl_par('timer', ctrl_data['timer'].axis)
                ctrl.set_ctrl_par('monitor', ctrl_data['monitor'].axis)
                trigger_type = ctrl_data['trigger_type']
                # TODO: mixing units with ctrl data concepts
                trigger_element = ctrl_data.get('trigger_element')
                if trigger_element:
                    tg_pool_ctrl = trigger_element.get_controller()
                    tg_ctrl = tg_pool_ctrl._ctrl
                    # checking if we are using software or hardware trigger
                    # TODO: this check is not generic !!!
                    if hasattr(tg_ctrl, 'add_listener'):
                        trigger_type = AcqTriggerType.Software
                self.debug('load_configuration: setting trigger_type: %s to ctrl: %s' % (trigger_type, ctrl))
                ctrl.set_ctrl_par('trigger_type', trigger_type)

        self._config_dirty = False

    def get_timer(self):
        return self.get_configuration()['timer']

    timer = property(get_timer)
    
    # --------------------------------------------------------------------------
    # repetitions
    # --------------------------------------------------------------------------

    def get_repetitions(self):
        return self._repetitions

    def set_repetitions(self, repetitions, propagate=1):
        self._repetitions = repetitions
        if not propagate:
            return
        self.fire_event(EventType("repetitions", priority=propagate),
                        repetitions)

    repetitions = property(get_repetitions, set_repetitions,
                                doc="repetitions used in synchronized acquisition")
    
    # --------------------------------------------------------------------------
    # offset
    # --------------------------------------------------------------------------

    def get_offset(self):
        return self._offset

    def set_offset(self, offset, propagate=1):
        self._offset = offset
        if not propagate:
            return
        self.fire_event(EventType("offset", priority=propagate),
                        offset)

    offset = property(get_offset, set_offset,
                                doc="offset used in synchronized acquisition")

    # --------------------------------------------------------------------------
    # integration time
    # --------------------------------------------------------------------------

    def get_integration_time(self):
        return self._integration_time

    def set_integration_time(self, integration_time, propagate=1):
        self._integration_time = integration_time
        if not propagate:
            return
        self.fire_event(EventType("integration_time", priority=propagate),
                        integration_time)

    integration_time = property(get_integration_time, set_integration_time,
                                doc="the current integration time")

    # --------------------------------------------------------------------------
    # monitor count
    # --------------------------------------------------------------------------

    def get_monitor_count(self):
        return self._monitor_count

    def set_monitor_count(self, monitor_count, propagate=1):
        self._monitor_count = monitor_count
        if not propagate:
            return
        self.fire_event(EventType("monitor_count", priority=propagate),
                        monitor_count)

    monitor_count = property(get_monitor_count, set_monitor_count,
                             doc="the current monitor count")

    # --------------------------------------------------------------------------
    # acquisition mode
    # --------------------------------------------------------------------------

    def get_acquisition_mode(self):
        return self._acquisition_mode

    def set_acquisition_mode(self, acquisition_mode, propagate=1):
        self._acquisition_mode = acquisition_mode
        self._config_dirty = True #acquisition mode goes to configuration
        if not propagate:
            return
        self.fire_event(EventType("acquisition_mode", priority=propagate),
                        acquisition_mode)

    acquisition_mode = property(get_acquisition_mode, set_acquisition_mode,
                                doc="the current acquisition mode")

    # --------------------------------------------------------------------------
    # acquisition
    # --------------------------------------------------------------------------

    def start_acquisition(self, value=None, multiple=1):
        self._aborted = False
        if not self._simulation_mode:
            # load configuration into controller(s) if necessary
            self.load_configuration()
            # determining the acquisition parameters
            kwargs = dict(head=self, config=self._config, multiple=multiple)
            acquisition_mode = self.acquisition_mode
            integration_time = self._integration_time
            if acquisition_mode in (AcqMode.Timer, AcqMode.ContTimer):
                kwargs['integ_time'] = integration_time
            elif acquisition_mode in (AcqMode.Monitor, AcqMode.ContMonitor):
                kwargs['monitor'] = self._monitor
            if acquisition_mode in (AcqMode.ContTimer, AcqMode.ContMonitor):
                self._action_cache = None
                # TODO: calculate the active_period, based on the involved elements
                # hardcoding the active_period to 1 us
                active_period = 1e-6
                if active_period > integration_time:
                    raise ValueError('IntegrationTime must be higher than 1 us')
                passive_period = integration_time - active_period
                kwargs['active_period'] = active_period
                kwargs['passive_period'] = passive_period
                kwargs['offset'] = self._offset
                kwargs['repetitions'] = self._repetitions
                kwargs['synchronized'] = True
            elif self.acquisition_mode in (AcqMode.Timer, AcqMode.Monitor):
                kwargs['synchronized'] = False            
            # start acquisition
            self.acquisition.run(**kwargs)

    def set_acquisition(self, acq_cache):
        self.set_action_cache(acq_cache)

    def get_acquisition(self):
        return self.get_action_cache()

    acquisition = property(get_acquisition, doc="acquisition object")
