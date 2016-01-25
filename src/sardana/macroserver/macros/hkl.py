# -*- coding: utf-8 -*-
##############################################################################
##
## This file is part of Sardana
##
## http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
##           2013 Synchrotron SOLEIL, Saint Aubin, France
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

"""This is the hkl macro module"""

from __future__ import print_function

import PyTango

from sardana.macroserver.macro import macro

__author__ = ("Picca Frédéric-Emmanuel <picca@synchrotron-soleil.fr>")
__copyright__ = ("2011 CELLS / ALBA Synchrotron, Bellaterra, Spain "
                 "Copyright (c) 2013 Synchrotron-Soleil "
                 "L'Orme des Merisiers Saint-Aubin "
                 "BP 48 91192 GIF-sur-YVETTE CEDEX")
__license__ = 'LGPL-3+'

__all__ = ["sar_demo_hkl", "clear_sar_demo_hkl"]

_ENV = "_SAR_DEMO_HKL"


def get_free_names(db, prefix, nb, start_at=1):
    ret = []
    i = start_at
    failed = 96
    while len(ret) < nb and failed > 0:
        name = "%s%02d" % (prefix, i)
        try:
            db.get_device_alias(name)
            failed -= 1
        except PyTango.DevFailed:
            ret.append(name)
        i += 1
    if len(ret) < nb or failed == 0:
        raise Exception("Too many sardana demos registered on this system.\n"
                        "Please try using a different tango system")
    return ret


@macro()
def clear_sar_demo_hkl(self):
    """Undoes changes done with sar_demo"""
    try:
        SAR_DEMO_HKL = self.getEnv(_ENV)
    except:
        self.error("No hkl demo has been prepared yet on this sardana!")
        return

    self.print("Removing hkl demo elements...")
    for elem in SAR_DEMO_HKL.get("elements", ()):
        self.udefelem(elem)

    self.print("Removing hkl demo controllers...")
    for ctrl in SAR_DEMO_HKL.get("controllers", ()):
        self.udefctrl(ctrl)

    self.unsetEnv(_ENV)

    self.clear_sar_demo()

    self.print("DONE!")


@macro()
def sar_demo_hkl(self):
    """Sets up a demo environment. It creates many elements for testing"""

    self.sar_demo()

    try:
        SAR_DEMO_HKL = self.getEnv(_ENV)
        self.error("An hkl demo has already been prepared on this sardana")
        return
    except:
        pass

    db = PyTango.Database()

    motor_ctrl_name = get_free_names(db, "motctrl", 1)[0]
    hkl_ctrl_name = get_free_names(db, "hklctrl", 1)[0]

    motor_names = []
    for motor in ["mu", "omega", "chi", "phi", "gamma", "delta"]:
        motor_names += get_free_names(db, motor, 1)

    pseudo_names = []
    for pseudo in ["h", "k", "l",
                   "psi",
                   "q", "alpha",
                   "qper", "qpar"]:
        pseudo_names += get_free_names(db, pseudo, 1)

    pools = self.getPools()
    if not len(pools):
        self.error('This is not a valid sardana demonstration system.\n'
                   'Sardana demonstration systems must be connect to at least '
                   'one Pool')
        return
    pool = pools[0]

    self.print("Creating motor controller", motor_ctrl_name, "...")
    self.defctrl("DummyMotorController", motor_ctrl_name)
    for axis, motor_name in enumerate(motor_names, 1):
        self.print("Creating motor", motor_name, "...")
        self.defelem(motor_name, motor_ctrl_name, axis)

    self.print("Creating hkl controller", hkl_ctrl_name, "...")
    self.defctrl("DiffracE6C", hkl_ctrl_name,
                 "mu=" + motor_names[0],  # motor role
                 "omega=" + motor_names[1],
                 "chi=" + motor_names[2],
                 "phi=" + motor_names[3],
                 "gamma=" + motor_names[4],
                 "delta=" + motor_names[5],
                 "h=" + pseudo_names[0],  # pseudo role
                 "k=" + pseudo_names[1],
                 "l=" + pseudo_names[2],
                 "psi=" + pseudo_names[3],
                 "q=" + pseudo_names[4],
                 "alpha=" + pseudo_names[5],
                 "qper=" + pseudo_names[6],
                 "qpar=" + pseudo_names[7],
                 "diffractometertype", "E6C")

    controllers = motor_ctrl_name, hkl_ctrl_name
    elements = pseudo_names + motor_names
    d = dict(controllers=controllers, elements=elements)
    self.setEnv(_ENV, d)

    self.print("DONE!")
