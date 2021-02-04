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

"""This is the lists macro module"""


__all__ = ["ls0d", "ls1d", "ls2d", "lsa", "lscom", "lsct", "lsctrl",
           "lsctrllib", "lsdef", "lsexp", "lsi", "lsior", "lsm", "lsmeas",
           "lspc", "lspm", "lsmac", "lsmaclib", "lstg"]

__docformat__ = 'restructuredtext'

from taurus.console import Alignment
from taurus.console.list import List
from sardana.macroserver.macro import Macro, Type, ViewOption

Left, Right, HCenter = Alignment.Left, Alignment.Right, Alignment.HCenter

#~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
# List of elements related macros
#~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-


class _ls(Macro):
    # TODO: duplication of the default value definition is a workaround
    # for #427. See commit message cc3331a for more details.
    param_def = [
        ['filter', [['filter', Type.String, ".*",
                     'a regular expression filter'], {'min': 1}],
         [".*"], 'a regular expression filter'],
    ]

    def get_column_names(self):
        cols = []
        for col in self.cols:
            if isinstance(col, tuple):
                col = col[0]
            cols.append(col)
        return cols

    def get_column_members(self):
        cols = []
        for col in self.cols:
            if isinstance(col, tuple):
                col = col[1]
            cols.append(col.lower())
        return cols

    def run(self, *filter):
        self.warning('This macro is not intended to be executed directly by '
                     'the user')
        return


class lsdef(_ls):
    """List all macro definitions"""

    cols = 'Name', 'Module', 'Brief Description'
    width = -1,       -1,                  -1
    align = Right,    Right,                Left

    def run(self, filter):
        # TODO: passing a list causes TypeError: unhashable type: 'list'
        # uncomment it when bug-473 is fixed:
        # https://sourceforge.net/p/sardana/tickets/473/
        filter = filter[0]
        cols = self.get_column_names()
        out = List(cols, text_alignment=self.align,
                   max_col_width=self.width)

        for m in self.getMacros(filter):
            if m.name.startswith("_"):
                continue
            desc_length = self.getViewOption(ViewOption.DescriptionLength)
            description = m.get_brief_description(max_chars=desc_length)
            if len(description) < 61:
                out.appendRow([m.name, m.module_name, description])
            else:
                out.appendRow([m.name, m.module_name, description[0:60]])
                for i in range(1, len(description)/60 + 1):
                    out.appendRow(["", "", description[60*i:60*(i+1)]])

        for line in out.genOutput():
            self.output(line)


class _lsobj(_ls):

    subtype = Macro.All

    cols = 'Name', 'Type', 'Controller', 'Axis'  # , 'State'
    width = -1,     -1,           -1,     -1  # ,      -1
    align = Right,  Right,        Right,  Right  # ,   Right

    show_overwritten_msg = False

    def objs(self, filter):
        return self.findObjs(filter, type_class=self.type, subtype=self.subtype,
                             reserve=False)

    def obj2Row(self, o, cols=None):
        cols = cols or self.get_column_members()
        ret = []
        for col in cols:
            if col == 'controller':
                value = self.getController(o.controller).name
            elif col == 'name':
                isoverwritten = getattr(o, "isoverwritten", False)
                value = getattr(o, col)
                if isoverwritten is True:
                    value = "[*] " + value
                    if self.show_overwritten_msg is False:
                        self.show_overwritten_msg = True
            else:
                value = getattr(o, col)
                if value is None:
                    value = '-----'
            ret.append(value)
        return ret

    def run(self, filter):
        objs = self.objs(filter)
        nb = len(objs)
        if nb == 0:
            if self.subtype is Macro.All:
                if isinstance(self.type, str):
                    t = self.type.lower()
                else:
                    t = ", ".join(self.type).lower()
            else:
                t = self.subtype.lower()
            self.output('No %ss defined' % t)
            return

        cols = self.get_column_names()
        out = List(cols, text_alignment=self.align,
                   max_col_width=self.width)
        objs.sort()
        for obj in objs:
            try:
                out.appendRow(self.obj2Row(obj))
            except:
                pass

        for line in out.genOutput():
            self.output(line)

        if (self.show_overwritten_msg is True
            and hasattr(self, "overwritten_msg")):
            self.warning(self.overwritten_msg)


class lsm(_lsobj):
    """Lists all motors"""
    type = Type.Moveable


class lspm(lsm):
    """Lists all existing motors"""
    subtype = 'PseudoMotor'


class lscom(_lsobj):
    """Lists all communication channels"""
    type = Type.ComChannel


class lsior(_lsobj):
    """Lists all IORegisters"""
    type = Type.IORegister


class lsexp(_lsobj):
    """Lists all experiment channels"""
    type = Type.ExpChannel


class lsct(lsexp):
    """Lists all Counter/Timers"""
    subtype = 'CTExpChannel'


class ls0d(lsexp):
    """Lists all 0D experiment channels"""
    subtype = 'ZeroDExpChannel'


class ls1d(lsexp):
    """Lists all 1D experiment channels"""
    subtype = 'OneDExpChannel'


class ls2d(lsexp):
    """Lists all 2D experiment channels"""
    subtype = 'TwoDExpChannel'


class lspc(lsexp):
    """Lists all pseudo counters"""
    subtype = 'PseudoCounter'


class lstg(_lsobj):
    """Lists all trigger/gate elements"""
    type = Type.TriggerGate


class lsctrllib(_lsobj):
    """Lists all existing controller classes"""
    type = Type.ControllerClass
    cols = 'Name', ('Type', 'main_type'), ('Library',
                                           'module'), ('Family', 'gender')


class lsctrl(_lsobj):
    """Lists all existing controllers"""
    type = Type.Controller
    cols = 'Name', ('Type', 'main_type'), ('Class', 'klass'), 'Module'


class lsi(_lsobj):
    """Lists all existing instruments"""
    type = Type.Instrument
    cols = 'Name', 'Type', ('Parent', 'parent_instrument')


class lsa(_lsobj):
    """Lists all existing objects"""
    type = Type.Moveable, Type.ComChannel, Type.ExpChannel, Type.IORegister,\
        Type.TriggerGate


class lsmeas(_lsobj):
    """List existing measurement groups"""

    type = Type.MeasurementGroup

    cols = 'Active', 'Name', 'Timer', 'Experim. channels'
    width = -1,     -1,      -1,                  60
    align = HCenter,  Right,   Right,                Left

    def prepare(self, filter, **opts):
        try:
            self.mnt_grp = self.getEnv('ActiveMntGrp').lower() or None
        except:
            self.mnt_grp = None

    def obj2Row(self, o):
        if self.mnt_grp and (o.getName().lower() == self.mnt_grp):
            active = '*'
        else:
            active = ' '
        return active, o.name, o.getTimerName(), ", ".join(o.getChannelLabels())


class lsmac(_lsobj):
    """Lists existing macros"""

    type = Type.MacroCode
    cols = 'Name', ('Location', 'file_path')
    overwritten_msg = ("\nNote: if [*] is present together with the macro "
                       + "name means that a macro with the same name \nis "
                       + "defined in other module with less precedence and "
                       + "it has been overwritten.")


class lsmaclib(_lsobj):
    """Lists existing macro libraries."""

    type = Type.MacroLibrary
    cols = 'Name', ('Location', 'file_path')
