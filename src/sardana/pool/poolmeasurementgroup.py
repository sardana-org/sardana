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


class MeasurementConfiguration(object):

    DFT_DESC = 'General purpose measurement group'

    def __init__(self, parent=None):
        self._parent = None
        if parent is not None:
            self._parent = weakref.ref(parent)()
        self._config = None
        self.use_fqdn = True
        self._clean_variables()

    def _clean_variables(self):
        # list of controller with channels enabled.
        self.enabled_ctrls = []
        # list of timers and monitors by synchronization type.
        self.sw_sync_timers_enabled = []
        self.sw_sync_monitors_enabled = []
        self.sw_start_timers_enabled = []
        self.sw_start_monitors_enabled = []
        self.hw_sync_timers_enabled = []
        self.hw_sync_monitors_enabled = []
        # dict with channel and its acquisition synchronization
        # key: PoolBaseChannel; value: AcqSynch
        self.channel_to_acq_synch = {}
        # dict with controller and its acquisition synchronization
        # key: PoolController; value: AcqSynch
        self.ctrl_to_acq_synch = {}
        # TODO: Do the documentation
        self.ctrl_sw_sync = {}
        self.ctrl_hw_sync = {}
        self.ctrl_sw_start = {}
        self.ctrl_0d_sync = {}
        self.ctrl_tg_sync = {}
        # TODO: Do the documentation
        self.sw_sync_timer = None
        self.sw_sync_monitor = None
        self.sw_start_timer = None
        self.sw_start_monitor = None
        self.hw_sync_timer = None
        self.hw_sync_monitor = None

    def __check_config(func):
        def wrapper(self, *args, **kwargs):
            if self._config is None:
                raise RuntimeError('The configuration is empty.')
            return func(self, *args, **kwargs)
        return wrapper

    def __getitem__(self, item):
        return self._config.__getitem__(item)

    @property
    @__check_config
    def controllers(self):
        return self._config['controllers']

    @property
    @__check_config
    def configuration(self):
        return self._config

    @configuration.setter
    def configuration(self, config=None):
        self._build_configuration(config)

    def set_configuration_from_user(self, cfg, to_fqdn=True):
        config = {}
        user_elements = self._parent.get_user_elements()
        pool = self._parent.pool
        if len(user_elements) == 0:
            # All timers were disabled
            default_timer = None
        else:
            default_timer = user_elements[0].full_name

        timer_name = cfg.get('timer', default_timer)
        monitor_name = cfg.get('monitor', default_timer)
        if to_fqdn:
            timer_name = _to_fqdn(timer_name, logger=self._parent)
        config['timer'] = pool.get_element_by_full_name(timer_name)
        if to_fqdn:
            monitor_name = _to_fqdn(monitor_name, logger=self._parent)
        config['monitor'] = pool.get_element_by_full_name(monitor_name)
        config['controllers'] = controllers = {}

        for c_name, c_data in cfg['controllers'].items():
            # backwards compatibility for measurement groups created before
            # implementing feature-372:
            # https://sourceforge.net/p/sardana/tickets/372/
            # WARNING: this is one direction backwards compatibility - it just
            # reads channels from the units, but does not write channels to the
            # units back
            if 'units' in c_data:
                c_data = c_data['units']['0']
            # discard controllers which don't have items (garbage)
            ch_count = len(c_data['channels'])
            if ch_count == 0:
                continue

            external = c_name.startswith('__')
            if external:
                ctrl = c_name
            else:
                if to_fqdn:
                    c_name = _to_fqdn(c_name, logger=self._parent)
                ctrl = pool.get_element_by_full_name(c_name)
                assert ctrl.get_type() == ElementType.Controller
            controllers[ctrl] = ctrl_data = {}

            # exclude external and not timerable elements
            if not external and ctrl.is_timerable():
                timer_name = c_data['timer']
                if to_fqdn:
                    timer_name = _to_fqdn(timer_name, logger=self._parent)
                timer = pool.get_element_by_full_name(timer_name)
                ctrl_data['timer'] = timer
                monitor_name = c_data['monitor']
                if to_fqdn:
                    monitor_name = _to_fqdn(monitor_name, logger=self._parent)
                monitor = pool.get_element_by_full_name(monitor_name)
                ctrl_data['monitor'] = monitor
                synchronizer = c_data.get('synchronizer')
                # for backwards compatibility purposes
                # protect measurement groups without synchronizer defined
                if synchronizer is None:
                    synchronizer = 'software'
                elif synchronizer != 'software':
                    if to_fqdn:
                        synchronizer = _to_fqdn(synchronizer,
                                                logger=self._parent)
                    synchronizer = pool.get_element_by_full_name(synchronizer)
                ctrl_data['synchronizer'] = synchronizer
                try:
                    synchronization = c_data['synchronization']
                except KeyError:
                    # backwards compatibility for configurations before SEP6
                    synchronization = c_data['trigger_type']
                    msg = ("trigger_type configuration parameter is deprecated"
                           " in favor of synchronization. Re-apply "
                           "configuration in order to upgrade.")
                    self._parent.warning(msg)
                ctrl_data['synchronization'] = synchronization
            ctrl_data['channels'] = channels = {}
            for ch_name, ch_data in c_data['channels'].items():
                if external:
                    validator = TangoAttributeNameValidator()
                    params = validator.getParams(ch_data['full_name'])
                    params['pool'] = self._parent.pool
                    channel = PoolExternalObject(**params)
                else:
                    if to_fqdn:
                        ch_name = _to_fqdn(ch_name, logger=self._parent)
                    channel = pool.get_element_by_full_name(ch_name)
                channels[channel] = dict(ch_data)

        config['label'] = cfg.get('label', self._parent.name)
        config['description'] = cfg.get('description', self.DFT_DESC)
        self.use_fqdn = to_fqdn
        self._build_configuration(config)

    def get_configuration_for_user(self):
        cfg = self._config
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
                if 'timer' in c_data:
                    ctrl_data['timer'] = c_data['timer'].full_name
                if 'monitor' in c_data:
                    ctrl_data['monitor'] = c_data['monitor'].full_name
                if 'synchronizer' in c_data:
                    synchronizer = c_data['synchronizer']
                    if synchronizer != 'software':
                        synchronizer = synchronizer.full_name
                    ctrl_data['synchronizer'] = synchronizer
                if 'synchronization' in c_data:
                    ctrl_data['synchronization'] = c_data['synchronization']
            ctrl_data['channels'] = channels = {}
            for ch, ch_data in c_data['channels'].items():
                channels[ch.full_name] = dict(ch_data)

        config['label'] = cfg['label']
        config['description'] = cfg['description']
        return config

    def _build_channel_defaults(self, channel_data, channel):
        """
        Fills the channel default values for the given channel dictionary
        """

        external_from_name = isinstance(channel, (str, unicode))
        ndim = None
        if external_from_name:
            name = full_name = source = channel
            ndim = 0  # TODO: this should somehow verify the dimension
        else:
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
        channel_data['index'] = channel_data['index']
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
        channel_data['normalization'] = channel_data.get(
            'normalization', Normalization.No)

        return channel_data

    def _build_configuration(self, config=None):
        """Builds a configuration object from the list of elements"""
        self._clean_variables()

        if config is None:
            config = {}
            user_elements = self._parent.get_user_elements()
            ctrls = self._parent.get_pool_controllers()

            # find the first CT
            first_timerable = None
            for elem in user_elements:
                if elem.get_type() in TYPE_TIMERABLE_ELEMENTS:
                    first_timerable = elem
                    break
            if first_timerable is None:
                raise Exception("It is not possible to construct a "
                                "measurement group without at least one "
                                "timer able channel (Counter/timer, 1D or 2D)")
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
                # include all controller in the enabled list
                self.enabled_ctrls.append(ctrl)
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
                        ctrl_data['synchronization'] = AcqSynchType.Trigger
                        ctrl_data['synchronizer'] = 'software'
                        self.ctrl_to_acq_synch[ctrl] = AcqSynch.SoftwareTrigger
                        self.channel_to_acq_synch[
                            element] = AcqSynch.SoftwareTrigger
                else:
                    channels = ctrl_data['channels']
                channels[element] = channel_data = {}
                channel_data['index'] = user_elements.index(element)
                channel_data = self._build_channel_defaults(channel_data,
                                                            element)

            config['label'] = self._parent.name
            config['description'] = self.DFT_DESC

            if len(external_user_elements) > 0:
                controllers['__tango__'] = ctrl_data = {}
                ctrl_data['channels'] = channels = {}
                for index, element in external_user_elements:
                    channels[element] = channel_data = {}
                    channel_data['index'] = index
                    channel_data = self._build_channel_defaults(channel_data,
                                                                element)
        else:
            # create a configuration based on a new configuration
            user_elem_ids = {}
            tg_elem_ids = []
            pool = self._parent.pool
            for c, c_data in config['controllers'].items():
                synchronizer = c_data.get('synchronizer')
                acq_synch_type = c_data.get('synchronization')
                software = synchronizer == 'software'
                external = isinstance(c, (str, unicode))
                # only timerable elements are configured with acq_synch
                acq_synch = None
                ctrl_enabled = False
                ctrl_to_acq_synch = False
                if not external and c.is_timerable():
                    acq_synch = AcqSynch.from_synch_type(
                        software, acq_synch_type)
                for channel_data in c_data['channels'].values():
                    if external:
                        element = _id = channel_data['full_name']
                        channel_data['source'] = _id
                    else:
                        full_name = channel_data['full_name']
                        if self.use_fqdn:
                            full_name = _to_fqdn(full_name,
                                                 logger=self._parent)
                        element = pool.get_element_by_full_name(full_name)
                        _id = element.id
                    channel_data = self._build_channel_defaults(
                        channel_data, element)
                    if channel_data["enabled"]:
                        ctrl_enabled = True
                        if acq_synch is not None:
                            ctrl_to_acq_synch = True
                            self.channel_to_acq_synch[element] = acq_synch
                            if not software:
                                tg_elem_ids.append(synchronizer.id)
                        user_elem_ids[channel_data['index']] = _id

                if ctrl_to_acq_synch:
                    self.ctrl_to_acq_synch[c] = acq_synch
                if ctrl_enabled:
                    self.enabled_ctrls.append(c)

            # sorted ids may not be consecutive (if a channel is disabled)
            indexes = sorted(user_elem_ids.keys())
            user_elem_ids_list = [user_elem_ids[idx] for idx in indexes]
            user_elem_ids_list.extend(tg_elem_ids)
            self._parent.set_user_element_ids(user_elem_ids_list)

            g_timer, g_monitor = config['timer'], config['monitor']

            timer_ctrl_data = config['controllers'][g_timer.controller]
            if timer_ctrl_data['timer'] != g_timer:
                self._parent.warning('controller timer and global timer '
                                     'mismatch. Using global timer')
                self._parent.debug('For controller %s, timer is defined as '
                                   'channel %s. The global timer is set to '
                                   'channel %s which belongs to the same '
                                   'controller', g_timer.controller.name,
                                   timer_ctrl_data['timer'].name, g_timer.name)
                timer_ctrl_data['timer'] = g_timer

            monitor_ctrl_data = config['controllers'][g_monitor.controller]
            if monitor_ctrl_data['monitor'] != g_monitor:
                self._parent.warning('controller monitor and global '
                                     'monitor mismatch. Using global monitor')
                self._parent.debug('For controller %s, monitor is defined as '
                                   'channel %s. The global timer is set to '
                                   'channel %s which belongs to the same '
                                   'controller', g_monitor.controller.name,
                                   monitor_ctrl_data['monitor'].name,
                                   g_monitor.name)

        self._config = config
        self._split_sync()
        self._split_tg()

    def _split_sync(self):
        """
        Split MeasurementGroup configuration with channels
        triggered by SW Trigger and channels triggered by HW trigger

        """

        ctrls_in = self._config['controllers']
        for ctrl, ctrl_info in ctrls_in.items():
            external = isinstance(ctrl, str) and ctrl.startswith('__')
            # skipping external controllers e.g. Tango attributes
            if external:
                continue
            # splitting ZeroD based on the type
            if ctrl.get_ctrl_types()[0] == ElementType.ZeroDExpChannel:
                self.ctrl_0d_sync[ctrl] = ctrl_info
            # ignoring PseudoCounter
            elif ctrl.get_ctrl_types()[0] == ElementType.PseudoCounter:
                pass
            # splitting rest of the channels based on the assigned trigger
            else:
                synchronizer = ctrl_info.get('synchronizer')
                if synchronizer is None or synchronizer == 'software':
                    synchronization = ctrl_info.get('synchronization')
                    if synchronization in [AcqSynch.SoftwareTrigger,
                                           AcqSynch.SoftwareGate]:
                        self.ctrl_sw_sync[ctrl] = ctrl_info
                    else:
                        self.ctrl_sw_start[ctrl] = ctrl_info
                else:
                    self.ctrl_hw_sync[ctrl] = ctrl_info

        def get_master_enables(ctrls, role):
            master_idx = float("+inf")
            master = None
            elements = []
            for ctrl_info in ctrls.values():
                element = ctrl_info[role]
                if element in ctrl_info["channels"]:
                    element_idx = ctrl_info["channels"][element]["index"]
                    element_enabled = ctrl_info["channels"][element]["enabled"]
                    # Find master only if is enabled
                    if element_enabled:
                        elements.append(element)
                        if element_idx < master_idx:
                            master = element
                            master_idx = element_idx
            return master, elements

        if len(self.ctrl_sw_sync):
            timer, timers = get_master_enables(self.ctrl_sw_sync, "timer")
            self.sw_sync_timer = timer
            self.sw_sync_timers_enabled = timers

            monitor, monitors = get_master_enables(self.ctrl_sw_sync,
                                                   "monitor")
            self.sw_sync_monitor = monitor
            self.sw_sync_monitors_enabled = monitors

        if len(self.ctrl_sw_start):
            timer, timers = get_master_enables(self.ctrl_sw_start, "timer")
            self.sw_start_timer = timer
            self.sw_start_timers_enabled = timers

            monitor, monitors = get_master_enables(self.ctrl_sw_start,
                                                   "monitor")
            self.sw_start_monitor = monitor
            self.sw_start_monitors_enabled = monitors

        if len(self.ctrl_hw_sync):
            timer, timers = get_master_enables(self.ctrl_hw_sync, "timer")
            self.hw_sync_timer = timer
            self.hw_sync_timers_enabled = timers

            monitor, monitors = get_master_enables(self.ctrl_hw_sync,
                                                   "monitor")
            self.hw_sync_monitor = monitor
            self.hw_sync_monitors_enabled = monitors

    def _split_tg(self):
        """
        Build TG configuration from complete configuration.
        """

        # Create list with not repeated elements
        _tg_element_list = []

        for ctrl in self._config["controllers"]:
            tg_element = self._config["controllers"][ctrl].get('synchronizer',
                                                               None)
            if (tg_element is not None and
                    tg_element != "software" and
                    tg_element not in _tg_element_list):
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
        for ctrl in ctrl_tgelem_dict:
            self.ctrl_tg_sync[ctrl] = ctrls = {}
            ctrls['channels'] = {}
            for tg_elem in ctrl_tgelem_dict[ctrl]:
                ch = ctrls['channels'][tg_elem] = {}
                ch['full_name'] = tg_elem.full_name


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
        self._config.use_fqdn = to_fqdn
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
        for ctrl, ctrl_data in self._config.controllers.items():
            if isinstance(ctrl, str):  # skip external channels
                continue
            if not ctrl.is_online():
                continue
            if ctrl not in self._config.enabled_ctrls:
                continue

            ctrl.set_ctrl_par('acquisition_mode', self.acquisition_mode)
            # @TODO: fix optimization and enable it again
            if ctrl.operator == self and not force and not self._config_dirty:
                continue
            ctrl.operator = self
            if ctrl.is_timerable():
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
        return self._config.timer

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
