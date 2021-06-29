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

"""Environment related macros"""

__all__ = ["dumpenv", "load_env", "lsenv", "senv", "usenv", "genv",
           "lsvo", "setvo", "usetvo",
           "lsgh", "defgh", "udefgh"]

__docformat__ = 'restructuredtext'

from taurus.core.tango.tangovalidator import TangoDeviceNameValidator
from taurus.console.list import List
from sardana.macroserver.macro import Macro, Type
from sardana.macroserver.msexception import UnknownEnv

##########################################################################
#
# Environment related macros
#
##########################################################################

from lxml import etree


def reprValue(v, max=74):
    # cut long strings
    v = str(v)
    if len(v) > max:
        v = v[:max] + ' [...]'
    return v


class dumpenv(Macro):
    """Dumps the complete environment"""

    def run(self):
        env = self.getGlobalEnv()
        out = List(['Name', 'Value', 'Type'])
        for k, v in env.items():
            str_v = reprValue(v)
            type_v = type(v).__name__
            out.appendRow([str(k), str_v, type_v])

        for line in out.genOutput():
            self.output(line)


class lsvo(Macro):
    """Lists the view options"""

    def run(self):
        vo = self.getViewOptions()
        out = List(['View option', 'Value'])
        for key, value in list(vo.items()):
            out.appendRow([key, str(value)])

        for line in out.genOutput():
            self.output(line)


class setvo(Macro):
    """Sets the given view option to the given value.

    Available view options:

    - **ShowDial**: used by macro wm, pwm and wa. Default value ``False``
    - **ShowCtrlAxis**: used by macro wm, pwm and wa. Default value ``False``
    - **PosFormat**: used by macro wm, pwm, wa and umv. Default value ``-1``
    - **OutputBlock**: used by scan macros. Default value ``False``
    - **DescriptionLength**: used by lsdef. Default value ``60``


    """



    param_def = [['name', Type.String, None, 'View option name'],
                 ['value', Type.String, None, 'View option value']]

    def run(self, name, value):
        try:
            value = eval(value)
        except:
            pass
        self.setViewOption(name, value)


class usetvo(Macro):
    """Resets the value of the given view option.

    Available view options:

    - **ShowDial**: used by macro wm, pwm and wa. Default value ``False``
    - **ShowCtrlAxis**: used by macro wm, pwm and wa. Default value ``False``
    - **PosFormat**: used by macro wm, pwm, wa and umv. Default value ``-1``
    - **OutputBlock**: used by scan macros. Default value ``False``
    - **DescriptionLength**: used by lsdef. Default value ``60``

    """

    param_def = [['name', Type.String, None, 'View option name']]

    def run(self, name):
        self.resetViewOption(name)


class lsenv(Macro):
    """Lists the environment in alphabetical order"""

    param_def = [
        ['macro_list', [['macro', Type.MacroClass, None, 'macro name'],
                        {'min': 0}],
         None, 'List of macros to show environment'],
    ]

    def prepare(self, macro_list, **opts):
        self.table_opts = opts

    def run(self, macro_list):
        # list the environment for the current door
        if len(macro_list) == 0:
            # list All the environment for the current door
            out = List(['Name', 'Value', 'Type'])
            env = self.getAllDoorEnv()
            names_list = list(env.keys())
            names_list.sort(key=str.lower)
            for k in names_list:
                str_val = self.reprValue(env[k])
                type_name = type(env[k]).__name__
                out.appendRow([k, str_val, type_name])
        # list the environment for the current door for the given macros
        else:
            out = List(['Macro', 'Name', 'Value', 'Type'])
            for macro in macro_list:
                env = self.getEnv(key=None, macro_name=macro.name)
                names_list = list(env.keys())
                names_list.sort(key=str.lower)
                for k in names_list:
                    str_val = self.reprValue(env[k])
                    type_name = type(env[k]).__name__
                    out.appendRow([macro.name, k, str_val, type_name])

        for line in out.genOutput():
            self.output(line)

    def reprValue(self, v, max=54):
        # cut long strings
        v = str(v)
        if len(v) > max:
            v = '%s [...]' % v[:max]
        return v


class senv(Macro):
    """Sets the given environment variable to the given value"""

    param_def = [
        ['name', Type.Env, None,
         'Environment variable name. Can be one of the following:\n'
         ' - <name> - global variable\n'
         ' - <full door name>.<name> - variable value for a specific door\n'
         ' - <macro name>.<name> - variable value for a specific macro\n'
         ' - <full door name>.<macro name>.<name> - variable value for a '
         'specific macro running on a specific door'],
        ['value_list', [['value', Type.String, None,
                         'environment value item'], {'min': 1}],
         None, 'value(s). one item will eval to a single element. More than '
               'one item will eval to a tuple of elements'],
    ]

    def run(self, env, value):
        if len(value) == 1:
            value = value[0]
        else:
            value = '(%s)' % ', '.join(value)
        k, v = self.setEnv(env, value)
        line = '%s = %s' % (k, str(v))
        self.output(line)


class genv(Macro):
    """Gets the given environment variable"""

    param_def = [
        ["name", Type.Env, None,
         "Environment variable name. Can be one of the following:\n"
         " - <name> - global variable\n"
         " - <full door name>.<name> - variable value for a specific "
         "door\n"
         " - <macro name>.<name> - variable value for a specific"
         " macro\n"
         " - <full door name>.<macro name>.<name> - variable value"
         " for a specific macro running on a specific door"],
                 ]

    def run(self, var):
        pars = var.split(".")
        door_name = None
        macro_name = None
        if len(pars) == 1:
            key = pars[0]
        elif len(pars) > 1:
            _, door_name, _ = TangoDeviceNameValidator().getNames(pars[0])
            if door_name is None:  # first string is a Macro name
                macro_name = pars[0]
            if len(pars) == 3:
                macro_name = pars[1]
                key = pars[2]
            else:
                key = pars[1]

        env = self.getEnv(key=key,
                          macro_name=macro_name,
                          door_name=door_name)

        self.output("{:s} = {:s}".format(str(key), str(env)))


class usenv(Macro):
    """Unsets the given environment variable"""
    param_def = [
        ['environment_list', [['env', Type.Env, None,
                               'Environment variable name'], {'min': 1}],
         None, 'List of environment items to be removed'],
    ]

    def run(self, env):
        self.unsetEnv(env)
        self.output("Success!")


class load_env(Macro):
    """ Read environment variables from config_env.xml file"""

    def run(self):
        doc = etree.parse("config_env.xml")
        root = doc.getroot()
        for element in root:
            if element.find("./name").text == "auto_filter":
                self.output("Loading auto_filter variables:")
                filter_max_elem = element.find(".//FilterMax")
                if filter_max_elem is not None:
                    filter_max = filter_max_elem.text
                    self.setEnv("FilterMax", filter_max)
                    self.output("FilterMax loaded")
                else:
                    self.output("FilterMax not found")
                filter_min_elem = element.find(".//FilterMin")
                if filter_min_elem is not None:
                    filter_min = filter_max_elem.text
                    self.setEnv("FilterMin", filter_min)
                    self.output("FilterMin loaded")
                else:
                    self.output("FilterMin not found")
                filter_delta_elem = element.find(".//FilterDelta")
                if filter_delta_elem is not None:
                    filter_delta = filter_delta_elem.text
                    self.setEnv("FilterDelta", filter_delta)
                    self.output("FilterDelta loaded")
                else:
                    self.output("FilterDelta not found")
                filter_signal_elem = element.find(".//FilterSignal")
                if filter_signal_elem is not None:
                    filter_signal = filter_signal_elem.text
                    self.setEnv("FilterSignal", filter_signal)
                    self.output("FilterSignal loaded")
                else:
                    self.output("FilterSignal not found")
                filter_absorber_elem = element.find(".//FilterAbsorber")
                if filter_absorber_elem is not None:
                    filter_absorber = filter_absorber_elem.text
                    self.setEnv("FilterAbsorber", filter_absorber)
                    self.output("FilterAbsorber loaded")
                else:
                    self.output("FilterAbsorber not found")
                auto_filter_elem = element.find(".//AutoFilter")
                if auto_filter_elem is not None:
                    auto_filter = auto_filter_elem.text
                    self.setEnv("AutoFilter", auto_filter)
                    self.output("AutoFilter loaded")
                else:
                    self.output("AutoFilter not found")
            if element.find("./name").text == "auto_beamshutter":
                self.output("Loading auto_beamshutter variables:")
                auto_beamshutter_elem = element.find(".//AutoBeamshutter")
                if auto_beamshutter_elem is not None:
                    auto_beamshutter = auto_beamshutter_elem.text
                    self.setEnv("AutoBeamshutter", auto_beamshutter)
                    self.output("AutoBeamshutter loaded")
                else:
                    self.output("AutoBeamshutter not found")
                beamshutter_limit_elem = element.find(".//BeamshutterLimit")
                if beamshutter_limit_elem is not None:
                    beamshutter_limit = beamshutter_limit_elem.text
                    self.setEnv("BeamshutterLimit", beamshutter_limit)
                    self.output("BeamshutterLimit loaded")
                else:
                    self.output("BeamshutterLimit not found")
                beamshutter_signal_elem = element.find(".//BeamshutterSignal")
                if beamshutter_signal_elem is not None:
                    beamshutter_signal = beamshutter_signal_elem.text
                    self.setEnv("BeamshutterSignal", beamshutter_signal)
                    self.output("BeamshutterSignal loaded")
                else:
                    self.output("BeamshutterSignal not found")
                beamshutter_time_elem = element.find(".//BeamshutterTime")
                if beamshutter_time_elem is not None:
                    beamshutter_time = beamshutter_time_elem.text
                    self.setEnv("BeamshutterTime", beamshutter_time)
                    self.output("BeamshutterTime loaded")
                else:
                    self.output("BeamshutterTime not found")
            if element.find("./name").text == "exafs":
                self.output("Loading exafs variables:")
                exafs_int_times_elem = element.find(".//ExafsIntTimes")
                if exafs_int_times_elem is not None:
                    exafs_int_times = exafs_int_times_elem.text
                    self.setEnv("ExafsIntTimes", exafs_int_times)
                    self.output("ExafsIntTimes loaded")
                else:
                    self.output("ExafsIntTimes not found")
                exafs_nb_intervals_elem = element.find(".//ExafsNbIntervals")
                if exafs_nb_intervals_elem is not None:
                    exafs_nb_intervals = exafs_nb_intervals_elem.text
                    self.setEnv("ExafsNbIntervals", exafs_nb_intervals)
                    self.output("ExafsNbIntervals loaded")
                else:
                    self.output("ExafsNbIntervals not found")
                exafs_regions_elem = element.find(".//ExafsRegions")
                if exafs_regions_elem is not None:
                    exafs_regions = exafs_regions_elem.text
                    self.setEnv("ExafsRegions", exafs_regions)
                    self.output("ExafsRegions loaded")
                else:
                    self.output("ExafsRegions not found")
        misc_tree = root.find("./miscellaneous")
        if misc_tree is not None:
            for parameter in misc_tree:
                if parameter.tag != "name":
                    self.setEnv(parameter.tag, parameter.text)


class lsgh(Macro):
    """List general hooks.

    .. note::
        The `lsgh` macro has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including its removal) may occur if
        deemed necessary by the core developers.
    """

    def run(self):
        try:
            general_hooks = self.getEnv("_GeneralHooks")
        except UnknownEnv:
            self.output("No general hooks")
            return

        out = List(['Hook place', 'Hook(s)'])
        default_dict = {}
        for hook in general_hooks:
            name = hook[0]
            places = hook[1]
            for place in places:
                if place not in list(default_dict.keys()):
                    default_dict[place] = []
                default_dict[place].append(name)
        for pos in list(default_dict.keys()):
            pos_set = 0
            for hook in default_dict[pos]:
                if pos_set:
                    out.appendRow(["", hook])
                else:
                    out.appendRow([pos, hook])
                pos_set = 1
        for line in out.genOutput():
            self.output(line)


class defgh(Macro):
    """Define general hook:

    >>> defgh "mv [[mot02 9]]" pre-scan
    >>> defgh "ct 0.1" pre-scan
    >>> defgh lsm pre-scan
    >>> defgh "mv mot03 10" pre-scan
    >>> defgh "Print 'Hello world'" pre-scan

    .. note::
        The `defgh` macro has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including its removal) may occur if
        deemed necessary by the core developers.

    """

    param_def = [
        ['macro_name', Type.String, None, ('Macro name with parameters. '
                                           'Ex.: "mv exp_dmy01 10"')],
        ['hookpos_list', [['position', Type.String, None, 'macro name'],
                          {'min': 1}],
         None, 'List of positions where the hook has to be executed'],
    ]

    def run(self, macro_name, position):

        self.info("Defining general hook")
        self.output(macro_name)
        try:
            macros_list = self.getEnv("_GeneralHooks")
        except UnknownEnv:
            macros_list = []

        hook_tuple = (macro_name, position)
        self.debug(hook_tuple)
        macros_list.append(hook_tuple)
        self.setEnv("_GeneralHooks", macros_list)
        self.debug("General hooks:")
        self.debug(macros_list)


class udefgh(Macro):
    """Undefine general hook. Without arguments undefine all.

    .. note::
        The `lsgh` macro has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including its removal) may occur if
        deemed necessary by the core developers.
    """

    param_def = [
        ['macro_name', Type.String, "all", 'General hook to be undefined'],
        ['hook_pos', Type.String, "all", ('Position to undefine the general '
                                          'hook from')],
    ]

    def run(self, macro_name, hook_pos):
        try:
            gh_macros_list = self.getEnv("_GeneralHooks")
        except UnknownEnv:
            return

        if macro_name == "all":
            self.unsetEnv("_GeneralHooks")
            self.info("Undefine all general hooks")
        else:
            macros_list = []
            for el in gh_macros_list:
                if el[0] != macro_name:
                    macros_list.append(el)
                else:
                    self.info("Hook %s is undefineed" % macro_name)

            self.setEnv("_GeneralHooks", macros_list)
