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

"""This is the standard macro module"""

from __future__ import print_function

__all__ = ["sar_demo", "sar_demo_hkl", "clear_sar_demo_hkl"]

import PyTango

from sardana.macroserver.macro import macro, Type
from sardana.macroserver.msexception import UnknownEnv

_ENV = "_SAR_DEMO"

_ENV_HKL = "_SAR_DEMO_HKL"

def get_free_names(db, prefix, nb, start_at=1):
    ret = []
    i = start_at
    failed = 96
    while len(ret) < nb and failed > 0:
        name = "%s%02d" % (prefix, i)
        try:
            db.get_device_alias(name)
            failed -= 1
        except:
            ret.append(name)
        i += 1
    if len(ret) < nb or failed == 0:
        raise Exception("Too many sardana demos registered on this system.\n"
                        "Please try using a different tango system")
    return ret

@macro()
def clear_sar_demo(self):
    """Undoes changes done with sar_demo"""
    try:
        SAR_DEMO = self.getEnv(_ENV)
    except:
        self.error("No demo has been prepared yet on this sardana!")
        return

    try:
        _ActiveMntGrp = self.getEnv("ActiveMntGrp")
    except UnknownEnv:
        _ActiveMntGrp = None

    self.print("Removing measurement groups...")
    for mg in SAR_DEMO.get("measurement_groups", ()):
        self.udefmeas(mg)
        if mg == _ActiveMntGrp:
            self.print("Unsetting ActiveMntGrp (was: %s)" % _ActiveMntGrp)
            self.unsetEnv("ActiveMntGrp")
    
    self.print("Removing elements...")
    elements =  SAR_DEMO.get("elements", ())
    if len(elements) > 0:
        self.udefelem(elements)
    
    self.print("Removing controllers...")
    for ctrl in SAR_DEMO.get("controllers", ()):
        self.udefctrl(ctrl)
    
    self.unsetEnv(_ENV)
    
    self.print("DONE!")
    
@macro()
def sar_demo(self):
    """Sets up a demo environment. It creates many elements for testing"""
    
    try:
        SAR_DEMO = self.getEnv(_ENV)
        self.error("A demo has already been prepared on this sardana")
        return
    except:
        pass
    
    db = PyTango.Database()
    
    mot_ctrl_name = get_free_names(db, "motctrl", 1)[0]
    ct_ctrl_name = get_free_names(db, "ctctrl", 1)[0]
    zerod_ctrl_name = get_free_names(db, "zerodctrl", 1)[0]
    oned_ctrl_name = get_free_names(db, "onedctrl", 1)[0]
    twod_ctrl_name = get_free_names(db, "twodctrl", 1)[0]
    pm_ctrl_name = get_free_names(db, "slitctrl", 1)[0]
    ior_ctrl_name = get_free_names(db, "iorctrl", 1)[0]

    motor_names = get_free_names(db, "mot", 4)
    ct_names = get_free_names(db, "ct", 4)
    zerod_names = get_free_names(db, "zerod", 4)
    oned_names = get_free_names(db, "oned", 1)
    twod_names = get_free_names(db, "twod", 1)
    gap, offset = get_free_names(db, "gap", 1) + get_free_names(db, "offset", 1)
    ior_names = get_free_names(db, "ior", 2)
    mg_name = get_free_names(db, "mntgrp", 1)[0]
    
    pools = self.getPools()
    if not len(pools):
        self.error('This is not a valid sardana demonstration system.\n'
                   'Sardana demonstration systems must be connect to at least '
                   'one Pool')
        return
    pool = pools[0]
    
    self.print("Creating motor controller", mot_ctrl_name, "...")
    self.defctrl("DummyMotorController", mot_ctrl_name)
    for axis, motor_name in enumerate(motor_names, 1):
        self.print("Creating motor", motor_name, "...")
        self.defelem(motor_name , mot_ctrl_name, axis)
        
    self.print("Creating counter controller", ct_ctrl_name, "...")
    self.defctrl("DummyCounterTimerController", ct_ctrl_name)
    for axis, ct_name in enumerate(ct_names, 1):
        self.print("Creating counter channel", ct_name, "...")
        self.defelem(ct_name , ct_ctrl_name, axis)
    
    self.print("Creating 0D controller", zerod_ctrl_name, "...")
    self.defctrl("DummyZeroDController", zerod_ctrl_name)
    for axis, zerod_name in enumerate(zerod_names, 1):
        self.print("Creating 0D channel", zerod_name, "...")
        self.defelem(zerod_name , zerod_ctrl_name, axis)

    self.print("Creating 1D controller", oned_ctrl_name, "...")
    self.defctrl("DummyOneDController", oned_ctrl_name)
    for axis, oned_name in enumerate(oned_names, 1):
        self.print("Creating 1D channel", oned_name, "...")
        self.defelem(oned_name , oned_ctrl_name, axis)

    self.print("Creating 2D controller", twod_ctrl_name, "...")
    self.defctrl("DummyTwoDController", twod_ctrl_name)
    for axis, twod_name in enumerate(twod_names, 1):
        self.print("Creating 2D channel", twod_name, "...")
        self.defelem(twod_name , twod_ctrl_name, axis)
    
    self.print("Creating Slit", pm_ctrl_name, "with", gap, ",", offset, "...")
    sl2t, sl2b = motor_names[:2]
    self.defctrl("Slit", pm_ctrl_name, ["sl2t="+sl2t, "sl2b="+sl2b,
                 "Gap="+gap, "Offset="+offset])

    self.print("Creating IORegister controller", ior_ctrl_name, "...")
    self.defctrl("DummyIORController", ior_ctrl_name)
    for axis, ior_name in enumerate(ior_names, 1):
        self.print("Creating IORegister", ior_name, "...")
        self.defelem(ior_name, ior_ctrl_name, axis)

    self.print("Creating measurement group", mg_name, "...")
    self.defmeas(mg_name, ct_names)

    try:
        self.getEnv("ActiveMntGrp")
    except UnknownEnv:
        self.print("Setting %s as ActiveMntGrp" % mg_name)
        self.setEnv("ActiveMntGrp", mg_name)

    controllers = pm_ctrl_name, mot_ctrl_name, ct_ctrl_name, \
            zerod_ctrl_name, oned_ctrl_name, twod_ctrl_name, ior_ctrl_name
    elements = [gap, offset] + motor_names + ct_names + \
            zerod_names + oned_names + twod_names + ior_names
    d = dict(controllers=controllers, elements=elements,
             measurement_groups=[mg_name])
    
    self.setEnv(_ENV, d)
    
    self.print("DONE!")

@macro([["motor", Type.Moveable, None, '']])
def mym2(self, pm):
    self.output(pm.getMotorNames())
    elements = map(self.getMoveable, pm.elements)
    self.output(elements)
    self.output(type(pm))
    self.output(type(elements[0]))
 

@macro()
def clear_sar_demo_hkl(self):
    """Undoes changes done with sar_demo"""
    try:
        SAR_DEMO_HKL = self.getEnv(_ENV_HKL)
    except:
        self.error("No hkl demo has been prepared yet on this sardana!")
        return

    self.print("Removing hkl demo elements...")
    for elem in SAR_DEMO_HKL.get("elements", ()):
        self.udefelem(elem)

    self.print("Removing hkl demo controllers...")
    for ctrl in SAR_DEMO_HKL.get("controllers", ()):
        self.udefctrl(ctrl)

    self.unsetEnv(_ENV_HKL)

    self.clear_sar_demo()

    self.print("DONE!")


@macro()
def sar_demo_hkl(self):
    """Sets up a demo environment. It creates many elements for testing"""

    self.sar_demo()

    try:
        SAR_DEMO_HKL = self.getEnv(_ENV_HKL)
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
                 ["mu=" + motor_names[0],  # motor role
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
                  "diffractometertype", "E6C"])

    controllers = motor_ctrl_name, hkl_ctrl_name
    elements = pseudo_names + motor_names
    d = dict(controllers=controllers, elements=elements)
    self.setEnv(_ENV_HKL, d)

    self.print("DONE!")
