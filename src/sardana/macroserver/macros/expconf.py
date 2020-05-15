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

"""Experiment configuration related macros"""

__all__ = ["get_meas", "get_meas_conf", "set_meas", "set_meas_conf"]

__docformat__ = 'restructuredtext'

from collections import OrderedDict

from taurus.console import Alignment
from taurus.console.list import List

from sardana.macroserver.msexception import UnknownEnv
from sardana.taurus.core.tango.sardana import PlotType
from sardana.macroserver.macro import macro, Type, Optional


def sanitizer(values):
    return ["n/a" if v is None else v for v in values]


def plot_type_sanitizer(values):
    return [PlotType.whatis(v) for v in values]


def plot_axes_sanitizer(values):
    return ["n/a" if len(v) == 0 else v[0] for v in values]


def plot_axes_validator(value):
    value = value.lower()
    if value in ("idx", "<idx>"):
        value = ["<idx>"]
    elif value in ("mov", "<mov>"):
        value = ["<mov>"]
    return value


def bool_validator(value):
    value = value.lower()
    if value in ['true', '1']:
        value = True
    elif value in ['false', '0']:
        value = False
    else:
        raise ValueError('{0} is not a boolean'.format(value))
    return value


# if sanitizers and validators evolve to sth too complicated refactor this
# to use classes
parameter_map = OrderedDict([
    ("enabled", ("Enabled", None, bool_validator)),
    ("output", ("Output", None, bool_validator)),
    ("plottype", ("PlotType", plot_type_sanitizer, None)),
    ("plotaxes", ("PlotAxes", plot_axes_sanitizer, plot_axes_validator)),
    ("timer", ("Timer", sanitizer, None)),
    ("monitor", ("Monitor", sanitizer, None)),
    ("synchronizer", ("Synchronizer", sanitizer, None)),
    ("valuerefenabled", ("ValueRefEnabled", sanitizer, bool_validator)),
    ("valuerefpattern", ("ValueRefPattern", sanitizer, None))
])


simple_parameters = ("enabled", "plottype", "plotaxes")


@macro([
    ["detail", Type.String, Optional,
        "Detail level of parameters. If omitted or \"simple\" then "
        "get simple parameters. If \"all\" then get all parameters."],
    ["meas_grp", Type.MeasurementGroup, Optional, "Measurement group"]
])
def get_meas_conf(self, detail, meas_grp):
    """Print measurement group configuration in form of a table.

    Examples of usage:

    >>> get_meas_conf  # get <ActiveMntGrp> simple configuration
    >>> get_meas_conf all  # get <ActiveMntGrp> complete configuration
    >>> get_meas_conf simple mntgrp01  # get mntgrp01 simple configuration
    >>> get_meas_conf all mntgrp01  # get mntgrp01 complete configuration
    """
    if detail is None or detail == "simple":
        parameters = simple_parameters
    elif detail == "all":
        parameters = parameter_map.keys()
    else:
        raise ValueError("wrong detail level: {}".format(detail))
    if meas_grp is None:
        meas_grp = self.getEnv("ActiveMntGrp")
        self.print("ActiveMntGrp = {}".format(meas_grp))
        meas_grp = self.getMeasurementGroup(meas_grp)
    col_headers = ["Channel"]
    width = [-1]
    align = [Alignment.Right]
    cols = []
    for parameter in parameters:
        parameter, sanitizer, _ = parameter_map[parameter]
        getter = getattr(meas_grp, "get" + parameter)
        ret = getter()
        if len(cols) == 0:
            # add channel names as first column
            cols.append(ret.keys())
        values = ret.values()
        if sanitizer is not None:
            values = sanitizer(values)
        cols.append(values)
        col_headers.append(parameter)
        width.append(-1)
        align.append(Alignment.Right)
    out = List(col_headers, text_alignment=align, max_col_width=width)
    for row in zip(*cols):
        out.appendRow(row)
    for line in out.genOutput():
        self.output(line)


@macro([
    ["parameter", Type.String, None, "Parameter (case insensitive) to set."],
    ["value", Type.String, None, "Parameter value to set"],
    ["items", [
        ["item", Type.String, None, "Experimental channel/controller"],
        {"min": 0}], None,
        "Experimental channels (also external e.g. Tango attribute: "
        "sys/tg_test/1/ampli) or their controllers"
     ],
    ["meas_grp", Type.MeasurementGroup, Optional, "Measurement group"],
])
def set_meas_conf(self, parameter, value, items, meas_grp):
    """Set measurement group configuration parameter.

    Available configuration parameters and values:

    - **Enabled**: True/1 or False/0
    - **Output**: True/1 or False/0
    - **PlotType**: No, Spectrum or Image
    - **PlotAxes**: idx, mov or a <channel name> e.g. ct01
      (for image use "|" as separator of axes e.g. idx|ct01)
    - **Timer**: <channel name> e.g. ct01
    - **Monitor**: <channel name> e.g. ct01
    - **Synchronizer**: software or <trigger/gate name> e.g. tg01
    - **ValueRefEnabled** - True/1 or False/0
    - **ValueRefPattern** - URI e.g. file:///tmp/img_{index}.tiff

    Examples of usage:

    >>> set_meas_conf enabled True  # enable all channels in <ActiveMntGrp>
    >>> set_meas_conf plottype spectrum ct01  # enable spectrum plotting for ct01 on <ActiveMntGrp>
    >>> set_meas_conf plotaxes mov  # set plot x-axis to <moveable> for all channels of <ActiveMntGrp>  #noqa
    >>> set_meas_conf plottype spectrum [] mntgrp01  # enable spectrum plotting for all mntgrp01  # noqa
    """
    try:
        parameter, _, validator = parameter_map[parameter.lower()]
    except KeyError:
        raise ValueError("wrong parameter: {}".format(parameter))
    if meas_grp is None:
        meas_grp = self.getEnv("ActiveMntGrp")
        self.print("ActiveMntGrp = {}".format(meas_grp))
        meas_grp = self.getMeasurementGroup(meas_grp)
    setter = getattr(meas_grp, "set" + parameter)
    if validator is not None:
        value = validator(value)
    setter(value, *items)


@macro([
    ["meas_grp", Type.MeasurementGroup, None,
        "Measurement group to activate"],
    ["macro", Type.Macro, Optional,
        "Activate measurement group on this macro."
        "If omitted activate on all."],
])
def set_meas(self, meas_grp, macro):
    """Activate measurement group.

    It sets the ActiveMntGrp environment variable.
    """
    var = "ActiveMntGrp"
    if macro is not None:
        var = "{}.{}".format(macro.name, var)
    self.setEnv(var, meas_grp.getName())


@macro([
    ["macro", Type.Macro, Optional,
        "Get active measurement group set for this macro."
        "If omitted get the one set for all."],
])
def get_meas(self, macro):
    """Activate measurement group.

    It gets the ActiveMntGrp environment variable.
    """
    if macro is not None:
        macro_name = macro.name
    else:
        macro_name = None
    var = "ActiveMntGrp"
    try:
        value = self.getEnv(var, macro_name=macro_name)
    except UnknownEnv:
        self.warning("Active measurement group is not set. "
                     "Hint: use `set_meas` macro to set it.")
    else:
        self.print("{} = {}".format(var, value))
