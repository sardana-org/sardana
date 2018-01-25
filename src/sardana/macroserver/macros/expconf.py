import time

from sardana.macroserver.macro import Macro, Type, ParamRepeat


class MGManager(object):
    """
    Class to manages the measurement group
    """

    def __init__(self, macro_obj, mnt_grp, channels=None):
        self.macro = macro_obj
        self.mnt_grp = mnt_grp
        self.__filterMntChannels(channels)

    def __filterMntChannels(self, channels):
        # Check if the channels exit in the mntGrp
        self.all_channels_names = self.mnt_grp.getChannelNames()
        if channels is None:
            return
        channels_names = []
        for channel in channels:
            if isinstance(channel, str):
                channel_name = channel
            else:
                channel_name = channel.name

            if channel_name in self.all_channels_names:
                channels_names.append(channel_name)
            else:
                msg = 'The channel {0} is not in {1}'.format(channel_name,
                                                             self.mnt_grp)
                self.macro.warning(msg)
        self.channels_names = channels_names

    def enable_channels(self):
        self.mnt_grp.enableChannels(self.channels_names)
        self.macro.output('Channels enabled')

    def enable_only_channels(self):
        dis_ch = list(set(self.all_channels_names) - set(self.channels_names))
        self.disable_only_channels(dis_ch)
        self.macro.output('Enabled only the selected channels')

    def disable_channels(self):
        self.mnt_grp.disableChannels(self.channels_names)
        self.macro.output('Channels disabled')

    def disable_only_channels(self, dis_ch=None):
        self.mnt_grp.enableChannels(self.all_channels_names)
        time.sleep(0.2)
        if dis_ch is None:
            dis_ch = self.channels_names
        self.mnt_grp.disableChannels(dis_ch)
        self.macro.output('Disable only the selected channels')

    def enable_all(self):
        self.mnt_grp.enableChannels(self.all_channels_names)
        self.macro.output('Enable all the channels')

    def status(self):
        out_line = '{0:<15} {1:^10} {2:^10} {3:^10} {4:^10}'
        self.macro.output(out_line.format('Channel', 'Enabled', 'Plot_type',
                                          'Plot axes', 'Output'))
        for channel in self.mnt_grp.getChannels():
            name = channel['name']
            enabled = ['False', 'True'][channel['enabled']]
            plot_type = ['No', 'Spectrum', 'Image'][channel['plot_type']]
            plot_axis = channel['plot_axes']
            output = ['False', 'True'][channel['output']]
            self.macro.output(out_line.format(name, enabled, plot_type,
                                              plot_axis, output))


class meas_enable_ch(Macro):
    """
    Enable the Counter Timers selected

    """

    param_def = [
        ['MeasurementGroup', Type.MeasurementGroup, None,
         "Measurement Group to work"],
        ['ChannelState',
         ParamRepeat(['channel', Type.ExpChannel, None, 'Channel to change '
                                                        'state'], min=1),
         None, 'List of channels to Enable'],
    ]

    def run(self, mntGrp, channels):
        mg_manager = MGManager(self, mntGrp, channels)
        mg_manager.enable_channels()


class meas_enable_ch_only(Macro):
    """
    Enable the Counter Timers selected

    """

    param_def = [
        ['MeasurementGroup', Type.MeasurementGroup, None,
         "Measurement Group to work"],
        ['ChannelState',
         ParamRepeat(['channel', Type.ExpChannel, None, 'Channel to change '
                                                        'state'], min=1),
         None, 'List of channels to Enable'],
    ]

    def run(self, mntGrp, channels):
        mg_manager = MGManager(self, mntGrp, channels)
        mg_manager.enable_only_channels()


class meas_disable_ch(Macro):
    """
    Enable the Counter Timers selected

    """

    param_def = [
        ['MeasurementGroup', Type.MeasurementGroup, None,
         "Measurement Group to work"],
        ['ChannelState',
         ParamRepeat(['channel', Type.ExpChannel, None, 'Channel to change '
                                                        'state'], min=1),
         None, 'List of channels to Enable'],
    ]

    def run(self, mntGrp, channels):
        mg_manager = MGManager(self, mntGrp, channels)
        mg_manager.disable_channels()


class meas_disable_ch_only(Macro):
    """
    Enable the Counter Timers selected

    """

    param_def = [
        ['MeasurementGroup', Type.MeasurementGroup, None,
         "Measurement Group to work"],
        ['ChannelState',
         ParamRepeat(['channel', Type.ExpChannel, None, 'Channel to change '
                                                        'state'], min=1),
         None, 'List of channels to Enable'],
    ]

    def run(self, mntGrp, channels):
        mg_manager = MGManager(self, mntGrp, channels)
        mg_manager.disable_only_channels()


class meas_enable_all(Macro):
    """
    Enable all counter channels of the measurement group
    """

    param_def = [
        ['MeasurementGroup', Type.MeasurementGroup, None, "Measurement"], ]

    def run(self, mntGrp):
        mg_manager = MGManager(self, mntGrp)
        mg_manager.enable_all()


class meas_status(Macro):
    """
    Shows the current configuration of the measurementGroup,
    if the parameter is empty it shows the state of the ActiveMeasurementGroup
    """
    param_def = [
        ['MeasurementGroup', Type.MeasurementGroup, None, "Measurement"], ]

    def run(self, mntGrp):
        mg_manager = MGManager(self, mntGrp)
        mg_manager.status()


class select_mntGrp(Macro):
    param_def = [
       ['mntGrp', Type.MeasurementGroup, None, 'mntGroup name']]

    def run(self, mntGrp):
        self.setEnv('ActiveMntGrp', str(mntGrp))
        self.info("Active Measurement Group : %s" % str(mntGrp))
