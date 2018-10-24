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

"""This module is part of the Python Pool library. It defines the base classes
for"""

__all__ = ["PoolMeasurementGroup"]

__docformat__ = 'restructuredtext'

import threading
import weakref

try:
    from taurus.core.taurusvalidator import AttributeNameValidator as\
        TangoAttributeNameValidator
except ImportError:
    # TODO: For Taurus 4 compatibility
    from taurus.core.tango.tangovalidator import TangoAttributeNameValidator

from sardana import State, ElementType, \
    TYPE_EXP_CHANNEL_ELEMENTS, TYPE_TIMERABLE_ELEMENTS
from sardana.sardanaevent import EventType
from sardana.pool.pooldefs import (AcqMode, AcqSynchType, SynchParam, AcqSynch,
                                   SynchDomain)
from sardana.pool.poolgroupelement import PoolGroupElement
from sardana.pool.poolacquisition import PoolAcquisition
from sardana.pool.poolsynchronization import SynchronizationDescription
from sardana.pool.poolexternal import PoolExternalObject

from sardana.taurus.core.tango.sardana import PlotType, Normalization


# ----------------------------------------------
# Measurement Group Configuration information
# ----------------------------------------------
# dict <str, obj> with (at least) keys:
#    - 'timer' : the timer channel name / timer channel id
#    - 'monitor' : the monitor channel name / monitor channel id
#    - 'controllers' : dict<Controller, dict> where:
#        - key: ctrl
#        - value: dict<str, dict> with (at least) keys:
#                - 'timer' : the timer channel name / timer channel id
#                - 'monitor' : the monitor channel name / monitor channel id
#                - 'synchronization' : 'Gate'/'Software'
#                - 'channels' where value is a dict<str, obj> with (at least)
#                   keys:
#                    - 'id' : the channel name ( channel id )
#                    optional keys:
#                    - 'enabled' : True/False (default is True)
#                    any hints:
#                    - 'output' : True/False (default is True)
#                    - 'plot_type' : 'No'/'1D'/'2D' (default is 'No')
#                    - 'plot_axes' : list<str> 'where str is channel
#                                    name/'step#/'index#' (default is [])
#                    - 'label' : prefered label (default is channel name)
#                    - 'scale' : <float, float> with min/max (defaults to
#                                channel range if it is defined
#                    - 'plot_color' : int representing RGB
#    optional keys:
#    - 'label' : measurement group label (defaults to measurement group name)
#    - 'description' : measurement group description

# <MeasurementGroupConfiguration>
#  <timer>UxTimer</timer>
#  <monitor>CT1</monitor>
# </MeasurementGroupConfiguration>

# Example: 2 NI cards, where channel 1 of card 1 is wired to channel 1 of
# card 2 at configuration time we should set:

# ni0ctrl.setCtrlPar(0, 'synchronization', AcqSynch.SoftwareTrigger)
# ni0ctrl.setCtrlPar(0, 'timer', 1) # channel 1 is the timer
# ni0ctrl.setCtrlPar(0, 'monitor', 4) # channel 4 is the monitor
# ni1ctrl.setCtrlPar(0, 'synchronization', AcqSynch.HardwareTrigger)
# ni1ctrl.setCtrlPar(0, 'master', 0)

# when we count for 1.5 seconds:
# ni1ctrl.Load(1.5)
# ni0ctrl.Load(1.5)
# ni1ctrl.Start()
# ni0ctrl.Start()

"""

"""


def _to_fqdn(name, logger=None):
    full_name = name
    # try to use Taurus 4 to retrieve FQDN
    try:
        from taurus.core.tango.tangovalidator import TangoDeviceNameValidator
        full_name, _, _ = TangoDeviceNameValidator().getNames(name)
    # if Taurus3 in use just continue
    except ImportError:
        pass
    if full_name != name and logger:
        msg = ("PQDN full name is deprecated in favor of FQDN full name."
               " Re-apply configuration in order to upgrade.")
        logger.warning(msg)
    return full_name


class ConfigurationItem(object):
    def __init__(self, element, conf=None):
        self._element = weakref.ref(element)
        self.enabled = True

        if conf is not None:
            self.__dict__.update(conf)

    def __getattr__(self, item):
        return getattr(self.element, item)

    def get_config(self):
        """ Returns the configuration dictionary"""
        raise NotImplementedError()

    def get_element(self):
        """Returns the element associated with this item"""
        return self._element()

    def set_element(self, element):
        """Sets the element for this item"""
        self._element = weakref.ref(element)

    element = property(get_element)


class ControllerConfiguration(ConfigurationItem):
    """Configuration: 'timer', 'monitor', 'synchronization', 'channels'"""

    def __init__(self, element, conf=None):
        ConfigurationItem.__init__(self, element, conf)
        self.enabled = False
        self._channels = []
        self._channels_enabled = []
        self._channels_disabled = []

    def add_channel(self, channel_item):
        self._channels.append(channel_item)
        if channel_item.enabled:
            self.enabled = True
            if self._channels_enabled is None:
                self._channels_enabled = []
            self._channels_enabled.append(channel_item)
        else:
            if self._channels_disabled is None:
                self._channels_disabled = []
            self._channels_disabled.append(channel_item)

    def update_state(self):
        self.enabled = False
        self._channels_enabled = []
        self._channels_disabled = []
        for channel_item in self._channels:
            if channel_item.enabled:
                self.enabled = True
                self._channels_enabled.append(channel_item)
            else:
                self._channels_disabled.append(channel_item)

    def get_channels(self, enabled=None):
        if enabled is None:
            return list(self.channels)
        elif enabled:
            return list(self._channels_enabled)
        else:
            return list(self._channels_disabled)


class ChannelConfiguration(ConfigurationItem):
    """Configuration: 'index', 'enabled', 'output', 'plot_type', 'plot_axes',
                      'label', 'scale', 'plot_color'"""


class SynchronizerConfiguration(ConfigurationItem):

    def __init__(self, element, conf=None):
        ConfigurationItem.__init__(self, element, conf)
        self.enabled = False



class MeasurementConfiguration(object):
    """
    .. todo: Reject configuration with errors:
             * Controllers with timer and monitor disable
    """

    DFT_DESC = 'General purpose measurement group'

    def __init__(self, parent=None):
        self._parent = None
        if parent is not None:
            self._parent = weakref.proxy(parent)

        self._config = None
        self._use_fqdn = True

        # Structure to store the controllers and their channels
        self._timerable_ctrls = {}
        self._zerod_ctrls = []
        self._synch_ctrls = {}
        self._other_ctrls = []
        self._master_timer_sw = None
        self._master_monitor_sw = None
        self._master_timer_sw_start = None
        self._master_monitor_sw_start = None
        self._label = None
        self._description = None
        self._master_timer = None
        self._master_monitor = None
        self._user_confg = {}
        self._element_acq_synch = {}

    def get_acq_synch_by_element(self, element):
        return self._element_acq_synch[element.id]

    def _filter_ctrls(self, ctrls, enabled):
        if enabled is None:
            return ctrls

        filtered_ctrls = []
        for ctrl in ctrls:
            if ctrl.enabled == enabled:
                filtered_ctrls.append(ctrl)
        return filtered_ctrls

    def get_timerable_ctrls(self, acq_synch=None, enabled=None):
        timerable_ctrls = []
        if acq_synch is None:
            for ctrls in self._timerable_ctrls.values():
                timerable_ctrls += ctrls
        elif isinstance(acq_synch, list):
            acq_synch_list = acq_synch
            for acq_synch in acq_synch_list:
                timerable_ctrls += self._timerable_ctrls[acq_synch]
        else:
            timerable_ctrls = list(self._timerable_ctrls[acq_synch])

        return self._filter_ctrls(timerable_ctrls, enabled)

    def get_zerod_ctrls(self, enabled=None):
        return self._filter_ctrls(self._zerod_ctrls, enabled)

    def get_synch_ctrls(self, enabled=None):
        return self._filter_ctrls(self._synch_ctrls, enabled)

    def get_master_timer_software(self):
        return self._master_timer_sw

    def get_master_monitor_software(self):
        return self._master_monitor_sw

    def get_master_timer_software_start(self):
        return self._master_monitor_sw_start

    def get_master_monitor_software_start(self):
        return self._master_timer_sw_start

    def get_configuration_for_user(self):
        return self._user_confg

    def set_configuration_from_user(self, cfg, to_fqdn=True):
        user_elements = self._parent.get_user_elements()
        if len(user_elements) == 0:
            # All channels were disabled
            raise ValueError('The configuration has all the channels disabled')

        pool = self._parent.pool

        label = cfg.get('label', self._parent.name)
        description = cfg.get('description', self.DFT_DESC)

        timerable_ctrls = {AcqSynch.HardwareGate: [],
                           AcqSynch.HardwareStart: [],
                           AcqSynch.HardwareTrigger: [],
                           AcqSynch.SoftwareStart: [],
                           AcqSynch.SoftwareTrigger: [],
                           AcqSynch.SoftwareGate: []}
        zerod_ctrls = []
        synch_ctrls = []
        other_ctrls = []
        master_timer_sw = None
        master_monitor_sw = None
        master_timer_sw_start = None
        master_monitor_sw_start = None
        master_timer = None
        master_monitor = None
        element_acq_synch = {}
        master_timer_idx_sw = float("+inf")
        master_monitor_idx_sw = float("+inf")
        user_elem_ids = {}
        user_config = {}

        # Update the configuration for user
        user_config['controllers'] = {}
        user_config = {}
        if 'timer' in cfg:
            user_config['timer'] = cfg['timer']
        if 'monitor' in cfg:
            user_config['monitor'] = cfg['monitor']
        user_config['controllers'] = {}
        user_config['label'] = label
        user_config['description'] = description

        for ctrl_name, ctrl_data in cfg['controllers'].items():
            # backwards compatibility for measurement groups created before
            # implementing feature-372:
            # https://sourceforge.net/p/sardana/tickets/372/
            # WARNING: this is one direction backwards compatibility - it just
            # reads channels from the units, but does not write channels to the
            # units back
            if 'units' in ctrl_data:
                ctrl_data = ctrl_data['units']['0']
            # discard controllers which don't have items (garbage)
            ch_count = len(ctrl_data['channels'])
            if ch_count == 0:
                continue

            external = ctrl_name.startswith('__')
            if external:
                ctrl = ctrl_name
            else:
                if to_fqdn:
                    ctrl_name = _to_fqdn(ctrl_name, logger=self._parent)
                ctrl = pool.get_element_by_full_name(ctrl_name)
                assert ctrl.get_type() == ElementType.Controller

            user_config['controllers'][ctrl_name] = user_config_ctrl = {}
            ctrl_conf = {}

            synchronizer = ctrl_data.get('synchronizer', None)
            conf_synch = None
            if synchronizer is None or synchronizer == 'software':
                ctrl_conf['synchronizer'] = 'software'
                user_config_ctrl['synchronizer'] = 'software'
            else:
                if to_fqdn:
                    synchronizer = _to_fqdn(synchronizer,
                                            logger=self._parent)

                user_config_ctrl['synchronizer'] = synchronizer
                pool_synch = pool.get_element_by_full_name(synchronizer)
                pool_synch_ctrl = pool_synch.controller
                conf_synch = SynchronizerConfiguration(pool_synch)
                conf_synch_ctrl = None
                if len(synch_ctrls) > 0:
                    conf_synch_ctrl = None
                    for conf_ctrl in synch_ctrls:
                        if pool_synch_ctrl == conf_ctrl.element:
                            conf_synch_ctrl = conf_ctrl
                if conf_synch_ctrl is None:
                    conf_synch_ctrl = ControllerConfiguration(pool_synch_ctrl)
                conf_synch_ctrl.add_channel(conf_synch)
                synch_ctrls.append(conf_synch_ctrl)
                ctrl_conf['synchronizer'] = conf_synch

            try:
                synchronization = ctrl_data['synchronization']
            except KeyError:
                # backwards compatibility for configurations before SEP6
                try:
                    synchronization = ctrl_data['trigger_type']
                    msg = ("trigger_type configuration parameter is deprecated"
                           " in favor of synchronization. Re-apply "
                           "configuration in order to upgrade.")
                    self._parent.warning(msg)
                except KeyError:
                    synchronization = None

            ctrl_conf['synchronization'] = synchronization
            user_config_ctrl['synchronization'] = synchronization
            ctrl_conf['timer'] = None
            ctrl_conf['monitor'] = None
            ctrl_item = ControllerConfiguration(ctrl, ctrl_conf)

            acq_synch = None
            if not external and ctrl.is_timerable():
                is_software = synchronizer == 'software'
                acq_synch = AcqSynch.from_synch_type(is_software,
                                                     synchronization)
                element_acq_synch[ctrl.id] = acq_synch

            ctrl_enabled = False
            if 'channels' in ctrl_data:
                user_config_ctrl['channels'] = user_config_channel = {}
            for ch_name, ch_data in ctrl_data['channels'].items():

                if external:
                    validator = TangoAttributeNameValidator()
                    params = validator.getParams(ch_data['full_name'])
                    params['pool'] = pool
                    channel = PoolExternalObject(**params)
                else:
                    if to_fqdn:
                        ch_name = _to_fqdn(ch_name, logger=self._parent)
                    channel = pool.get_element_by_full_name(ch_name)

                ch_data = self._fill_channel_data(channel, ch_data)
                user_config_channel[ch_name] = ch_data
                ch_item = ChannelConfiguration(channel, ch_data)
                ch_item.controller = ctrl_item
                ctrl_item.add_channel(ch_item)
                if ch_item.enabled:
                    user_elem_ids[ch_item.index] = channel.id

                # Update controller timer
                if ch_name == ctrl_data['timer']:
                    ctrl_item.timer = ch_item

                # Update controller monitor
                if ch_name == ctrl_data['monitor']:
                    ctrl_item.monitor = ch_item

                # Update measurement configuration master timer
                if ch_name == cfg.get('timer', None):
                    master_timer = ch_item

                # Update measurement configuration master timer
                if ch_name == cfg.get('monitor', None):
                    master_monitor = ch_item

                if ch_item.enabled:
                    ctrl_enabled = True

                if acq_synch is not None:
                   element_acq_synch[channel.id] = acq_synch

            # Update syncrhonizer state
            if conf_synch is not None:
                conf_synch.enabled = ctrl_enabled

            # validate if the timer and monitor are disabled if the
            # controller is enabled
            if ctrl_enabled and not ctrl_item.timer.enabled and \
                    not ctrl_item.monitor.enabled:
                timer_label = ctrl_item.timer.label
                monitor_label = ctrl_item.monitor.label

                err_msg = 'The channel {0} used as timer and the channel ' \
                          '{1} used as monitor are disabled. One of them ' \
                          'must be enabled'.format(timer_label, monitor_label)
                raise ValueError(err_msg)

            if not external and ctrl.is_timerable():
                timerable_ctrls[acq_synch].append(ctrl_item)
                # Find master timer/monitor the system take the channel with
                # less index
                if ctrl_item.synchronizer == 'software':
                    if ctrl_item.timer.index < master_timer_idx_sw:
                        master_timer_sw = ctrl_item.timer
                        master_timer_idx_sw = ctrl_item.timer.index
                    if ctrl_item.monitor.index < master_monitor_idx_sw:
                        master_monitor_sw = ctrl_item.monitor
                        master_monitor_idx_sw = ctrl_item.monitor.index
            elif ctrl.get_ctrl_types()[0] == ElementType.ZeroDExpChannel:
                zerod_ctrls.append(ctrl_item)
            else:
                other_ctrls.append(ctrl_item)

        # Update synchronizer controller states
        for conf_synch_ctrl in synch_ctrls:
            conf_synch_ctrl.update_state()


        # Update internals values
        self._master_monitor = master_monitor
        self._master_timer = master_timer
        self._label = label
        self._description = description
        self._timerable_ctrls = timerable_ctrls
        self._zerod_ctrls = zerod_ctrls
        self._synch_ctrls = synch_ctrls
        self._other_ctrls = other_ctrls
        self._master_timer_sw = master_timer_sw
        self._master_monitor_sw = master_monitor_sw
        self._element_acq_synch = element_acq_synch
        self._user_confg = user_config

        # sorted ids may not be consecutive (if a channel is disabled)
        indexes = sorted(user_elem_ids.keys())
        user_elem_ids_list = [user_elem_ids[idx] for idx in indexes]
        for conf_synch_ctrl in synch_ctrls:
            for conf_synch in conf_synch_ctrl.get_channels(enabled=True):
                user_elem_ids_list.append(conf_synch.id)
        self._parent.set_user_element_ids(user_elem_ids_list)

    def _fill_channel_data(self, channel, channel_data):
        """
        Fills the channel default values for the given channel dictionary
        """

        name = channel.name
        full_name = channel.full_name
        source = channel.get_source()
        ndim = None
        ctype = channel.get_type()
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
        channel_data['index'] = channel_data.get('index', None)
        channel_data['name'] = channel_data.get('name', name)
        channel_data['full_name'] = channel_data.get('full_name', full_name)
        channel_data['source'] = channel_data.get('source', source)
        channel_data['enabled'] = channel_data.get('enabled', True)
        channel_data['label'] = channel_data.get('label', channel_data['name'])
        channel_data['ndim'] = ndim
        # Probably should be initialized by measurement group
        channel_data['output'] = channel_data.get('output', True)

        # Perhaps should NOT be initialized by measurement group
        channel_data['plot_type'] = channel_data.get('plot_type', PlotType.No)
        channel_data['plot_axes'] = channel_data.get('plot_axes', [])
        channel_data['conditioning'] = channel_data.get('conditioning', '')
        channel_data['normalization'] = channel_data.get('normalization',
                                                         Normalization.No)
        # TODO use real values
        channel_data['data_type'] = channel_data.get('data_type', None)
        channel_data['data_units'] = channel_data.get('data_units', None)
        channel_data['nexus_path'] = channel_data.get('nexus_path', '')
        channel_data['shape'] = channel_data.get('shape', [])

        return channel_data


class PoolMeasurementGroup(PoolGroupElement):

    def __init__(self, **kwargs):
        self._state_lock = threading.Lock()
        self._monitor_count = None
        self._nr_of_starts = 1
        self._pending_starts = 0
        self._acquisition_mode = AcqMode.Timer
        self._config = MeasurementConfiguration(self)
        self._config_dirty = True
        self._moveable = None
        self._moveable_obj = None
        # by default software synchronizer initial domain is set to Position
        self._sw_synch_initial_domain = SynchDomain.Position

        self._synchronization = SynchronizationDescription()

        kwargs['elem_type'] = ElementType.MeasurementGroup
        PoolGroupElement.__init__(self, **kwargs)
        configuration = kwargs.get("configuration")
        self.set_configuration(configuration)
        # if the configuration was never "really" written e.g. newly created MG
        # just sets it now so the _channe_to_acq_synch and ctrl_to_acq_synch
        # are properly populated
        # TODO: make it more elegant
        if configuration is None:
            configuration = self.configuration.configuration
            self.set_configuration(configuration, propagate=0, to_fqdn=False)

    def _create_action_cache(self):
        acq_name = "%s.Acquisition" % self._name
        return PoolAcquisition(self, acq_name)

    def _calculate_states(self, state_info=None):
        state, status = PoolGroupElement._calculate_states(self, state_info)
        # check if software synchronizer is occupied
        synch_soft = self.acquisition._synch._synch_soft
        acq_sw = self.acquisition._sw_acq
        acq_0d = self.acquisition._0d_acq
        if state in (State.On, State.Unknown) \
            and (synch_soft.is_started() or
                 acq_sw._is_started() or
                 acq_0d._is_started()):
            state = State.Moving
            status += "/nSoftware synchronization is in progress"
        return state, status

    def on_element_changed(self, evt_src, evt_type, evt_value):
        name = evt_type.name
        if name == 'state':
            with self._state_lock:
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
    # -------------------------------------------------------------------------
    # configuration
    # -------------------------------------------------------------------------

    def _is_managed_element(self, element):
        element_type = element.get_type()
        return (element_type in TYPE_EXP_CHANNEL_ELEMENTS or
                element_type is ElementType.TriggerGate)

    @property
    def configuration(self):
        return self._config

    def set_configuration(self, config=None, propagate=1, to_fqdn=True):
        self._config._use_fqdn = to_fqdn
        self._config.configuration = config
        self._config_dirty = True
        if not propagate:
            return
        self.fire_event(EventType("configuration", priority=propagate), config)

    def set_configuration_from_user(self, cfg, propagate=1, to_fqdn=True):
        self._config.set_configuration_from_user(cfg, to_fqdn)
        self._config_dirty = True
        if not propagate:
            return
        self.fire_event(EventType("configuration", priority=propagate),
                        self._config.configuration)

    def get_user_configuration(self):
        return self._config.get_configuration_for_user()

    def load_configuration(self, force=False):
        """Loads the current configuration to all involved controllers"""

        # g_timer, g_monitor = cfg['timer'], cfg['monitor']
        for ctrl in self._config.enabled_ctrls:
            if isinstance(ctrl, str):  # skip external channels
                continue
            if not ctrl.is_online():
                continue

            ctrl.set_ctrl_par('acquisition_mode', self.acquisition_mode)
            # @TODO: fix optimization and enable it again
            if ctrl.operator == self and not force and not self._config_dirty:
                continue
            ctrl.operator = self
            if ctrl.is_timerable():
                # TODO: Implement API to extract controller data
                ctrl_data = self._config.configuration['controllers'][ctrl]
                # if ctrl == g_timer.controller:
                #    ctrl.set_ctrl_par('timer', g_timer.axis)
                # if ctrl == g_monitor.controller:
                #    ctrl.set_ctrl_par('monitor', g_monitor.axis)
                ctrl.set_ctrl_par('timer', ctrl_data['timer'].axis)
                ctrl.set_ctrl_par('monitor', ctrl_data['monitor'].axis)
                synchronization = self._config.ctrl_to_acq_synch.get(ctrl)
                self.debug('load_configuration: setting trigger_type: %s '
                           'to ctrl: %s' % (synchronization, ctrl))
                ctrl.set_ctrl_par('synchronization', synchronization)

        self._config_dirty = False

    def get_timer(self):
        # TODO: Adapt to the new future MeasurementConfiguration API
        return self._config.configuration['timer']

    timer = property(get_timer)

    # -------------------------------------------------------------------------
    # integration time
    # -------------------------------------------------------------------------

    def get_integration_time(self):
        integration_time = self._synchronization.integration_time
        if type(integration_time) == float:
            return integration_time
        elif len(integration_time) == 0:
            raise Exception("The synchronization group has not been"
                            " initialized")
        elif len(integration_time) > 1:
            raise Exception("There are more than one synchronization groups")

    def set_integration_time(self, integration_time, propagate=1):
        total_time = integration_time + self.latency_time
        synch = [{SynchParam.Delay: {SynchDomain.Time: 0},
                  SynchParam.Active: {SynchDomain.Time: integration_time},
                  SynchParam.Total: {SynchDomain.Time: total_time},
                  SynchParam.Repeats: 1}]
        self.set_synchronization(synch)
        self._integration_time = integration_time
        if not propagate:
            return
        self.fire_event(EventType("integration_time", priority=propagate),
                        integration_time)

    integration_time = property(get_integration_time, set_integration_time,
                                doc="the current integration time")

    # -------------------------------------------------------------------------
    # monitor count
    # -------------------------------------------------------------------------

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

    # -------------------------------------------------------------------------
    # acquisition mode
    # -------------------------------------------------------------------------

    def get_acquisition_mode(self):
        return self._acquisition_mode

    def set_acquisition_mode(self, acquisition_mode, propagate=1):
        self._acquisition_mode = acquisition_mode
        self._config_dirty = True  # acquisition mode goes to configuration
        if not propagate:
            return
        self.fire_event(EventType("acquisition_mode", priority=propagate),
                        acquisition_mode)

    acquisition_mode = property(get_acquisition_mode, set_acquisition_mode,
                                doc="the current acquisition mode")

    # -------------------------------------------------------------------------
    # synchronization
    # -------------------------------------------------------------------------

    def get_synchronization(self):
        return self._synchronization

    def set_synchronization(self, synchronization, propagate=1):
        self._synchronization = SynchronizationDescription(synchronization)
        self._config_dirty = True  # acquisition mode goes to configuration
        if not propagate:
            return
        self.fire_event(EventType("synchronization", priority=propagate),
                        synchronization)

    synchronization = property(get_synchronization, set_synchronization,
                               doc="the current acquisition mode")

    # -------------------------------------------------------------------------
    # moveable
    # -------------------------------------------------------------------------

    def get_moveable(self):
        return self._moveable

    def set_moveable(self, moveable, propagate=1, to_fqdn=True):
        self._moveable = moveable
        if self._moveable != 'None' and self._moveable is not None:
            if to_fqdn:
                moveable = _to_fqdn(moveable, logger=self)
            self._moveable_obj = self.pool.get_element_by_full_name(moveable)
        self.fire_event(EventType("moveable", priority=propagate),
                        moveable)

    moveable = property(get_moveable, set_moveable,
                        doc="moveable source used in synchronization")

    # -------------------------------------------------------------------------
    # latency time
    # -------------------------------------------------------------------------

    def get_latency_time(self):
        latency_time = 0
        pool_ctrls = self.acquisition.get_pool_controllers()
        for pool_ctrl in pool_ctrls:
            if not pool_ctrl.is_timerable():
                continue
            candidate = pool_ctrl.get_ctrl_par("latency_time")
            if candidate > latency_time:
                latency_time = candidate
        return latency_time

    latency_time = property(get_latency_time,
                            doc="latency time between two consecutive "
                                "acquisitions")

    # -------------------------------------------------------------------------
    # software synchronizer initial domain
    # -------------------------------------------------------------------------

    def get_sw_synch_initial_domain(self):
        return self._sw_synch_initial_domain

    def set_sw_synch_initial_domain(self, domain):
        self._sw_synch_initial_domain = domain

    sw_synch_initial_domain = property(
        get_sw_synch_initial_domain,
        set_sw_synch_initial_domain,
        doc="software synchronizer initial domain (SynchDomain.Time "
            "or SynchDomain.Position)"
    )

    # -------------------------------------------------------------------------
    # number of starts
    # -------------------------------------------------------------------------

    def get_nr_of_starts(self):
        return self._nr_of_starts

    def set_nr_of_starts(self, nr_of_starts, propagate=1):
        self._nr_of_starts = nr_of_starts
        if not propagate:
            return
        self.fire_event(EventType("nr_of_starts", priority=propagate),
                        nr_of_starts)

    nr_of_starts = property(get_nr_of_starts, set_nr_of_starts,
                            doc="current number of starts")

    # -------------------------------------------------------------------------
    # acquisition
    # -------------------------------------------------------------------------

    def prepare(self):
        # load configuration into controller(s) if necessary
        self.load_configuration()
        config = self.configuration
        nr_of_starts = self.nr_of_starts
        self._pending_starts = nr_of_starts
        self.acquisition.prepare(config, nr_of_starts)

    def start_acquisition(self, value=None, multiple=1):
        if self._pending_starts == 0:
            msg = "starting acquisition without prior preparing is " \
                  "deprecated since version Jan18."
            self.warning(msg)
            self.debug("Preparing with number_of_starts equal to 1")
            nr_of_starts = self.nr_of_starts
            self.set_nr_of_starts(1, propagate=0)
            try:
                self.prepare()
            finally:
                self.set_nr_of_starts(nr_of_starts, propagate=0)
        self._aborted = False
        self._pending_starts -= 1
        if not self._simulation_mode:
            # determining the acquisition parameters
            kwargs = dict(head=self, config=self._config, multiple=multiple)
            acquisition_mode = self.acquisition_mode
            if acquisition_mode is AcqMode.Timer:
                kwargs['integ_time'] = self.get_integration_time()
            elif acquisition_mode is AcqMode.Monitor:
                kwargs['monitor'] = self._monitor
            kwargs['synchronization'] = self._synchronization
            kwargs['moveable'] = self._moveable_obj
            kwargs['sw_synch_initial_domain'] = self._sw_synch_initial_domain
            # start acquisition
            self.acquisition.run(**kwargs)

    def set_acquisition(self, acq_cache):
        self.set_action_cache(acq_cache)

    def get_acquisition(self):
        return self.get_action_cache()

    acquisition = property(get_acquisition, doc="acquisition object")

    def stop(self):
        self._pending_starts = 0
        self.acquisition._synch._synch_soft.stop()
        PoolGroupElement.stop(self)

    def abort(self):
        self._pending_starts = 0
        PoolGroupElement.abort(self)
