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

"""
    Macro library containning diffractometer related macros for the macros
    server Tango device server as part of the Sardana project.

"""

# TODO: use taurus instead of PyTango API e.g. read_attribute,
# write_attribute. This module is full of PyTango centric calls.

# TODO: use explicit getters to obtain Sardana elements
# (controller - getController, pseudomotor - getPseudoMotor, ...) instead of
# using getDevice. However this getter seems to accept only the elements names
# and not the full names.

__all__ = ["addreflection", "affine", "br", "ca", "caa", "ci", "computeub",
           "freeze", "getmode", "hklscan", "hscan", "kscan", "latticecal",
           "loadcrystal", "lscan", "newcrystal", "or0", "or1", "orswap",
           "pa", "savecrystal", "setaz", "setlat", "setmode", "setor0",
           "setor1", "setorn", "th2th", "ubr", "wh"]

import time
import math
import os
import re
import numpy as np

from sardana.sardanautils import py2_round
from sardana.macroserver.macro import Hookable, Macro, iMacro, Type
from sardana.macroserver.macros.scan import aNscan
from sardana.macroserver.msexception import UnknownEnv

from taurus.core.util.log import Logger

logger = Logger.getLogger("MacroManager")

logger.info(
    "Diffractometer macros are at early stage. They can slightly change. Macro luppsi is not tested.")


class _diffrac:
    """Internal class used as a base class for the diffractometer macros"""

    env = ('DiffracDevice',)

    def prepare(self):

        dev_name = self.getEnv('DiffracDevice')
        self.diffrac = self.getDevice(dev_name)

        try:
            dev_name = self.getEnv('Psi')
            self.psidevice = self.getDevice(dev_name)
        except:
            pass

        motorlist = self.diffrac.motorlist

        pseudo_motor_names = []
        for motor in self.diffrac.hklpseudomotorlist:
            pseudo_motor_names.append(motor.split(' ')[0])

        self.h_device = self.getDevice(pseudo_motor_names[0])
        self.k_device = self.getDevice(pseudo_motor_names[1])
        self.l_device = self.getDevice(pseudo_motor_names[2])

        motor_list = self.diffrac.motorlist

        self.nb_motors = len(motor_list)

        try:
            self.angle_names = self.diffrac.motorroles
        except:  # Only for compatibility
            self.angle_names = []
            if self.nb_motors == 4:
                self.angle_names.append("omega")
                self.angle_names.append("chi")
                self.angle_names.append("phi")
                self.angle_names.append("tth")
            elif self.nb_motors == 6:
                self.angle_names.append("mu")
                self.angle_names.append("omega")
                self.angle_names.append("chi")
                self.angle_names.append("phi")
                self.angle_names.append("gamma")
                self.angle_names.append("delta")

        if self.nb_motors == 4:
            self.labelmotor = {'Omega': "omega",
                               'Chi': "chi", 'Phi': "phi", 'Tth': "tth"}
        elif self.nb_motors == 6:
            self.labelmotor = {'Mu': "mu", 'Theta': "omega", 'Chi': "chi",
                               'Phi': "phi", 'Gamma': "gamma",
                               'Delta': "delta"}

        prop = self.diffrac.get_property(['DiffractometerType'])
        for v in prop['DiffractometerType']:
            self.type = v

        self.angle_device_names = {}

        for i, motor in enumerate(motor_list):
            self.angle_device_names[self.angle_names[i]] = motor.split(' ')[0]

    # TODO: it should not be necessary to implement on_stop methods in the
    # macros in order to stop the moveables. Macro API should provide this kind
    # of emergency stop (if the moveables are correctly reserved with the
    # getMotion method) in case of aborting a macro.
    def on_stop(self):

        for angle in self.angle_names:
            angle_dev = self.getDevice(self.angle_device_names[angle])
            angle_dev.Stop()

    def check_collinearity(self, h0, k0, l0, h1, k1, l1):

        print(h0)
        cpx = k0 * l1 - l0 * k1
        cpy = l0 * h1 - h0 * l1
        cpz = h0 * k1 - k0 * h1
        cp_square = math.sqrt(cpx * cpx + cpy * cpy + cpz * cpz)

        collinearity = False

        if cp_square < 0.01:
            collinearity = True

        return collinearity

    def get_hkl_ref0(self):

        reflections = []
        try:
            reflections = self.diffrac.reflectionlist
        except:
            pass

        hkl = []
        if reflections is not None:
            for i in range(1, 4):
                hkl.append(reflections[0][i])

        return hkl

    def get_hkl_ref1(self):

        reflections = []
        try:
            reflections = self.diffrac.reflectionlist
        except:
            pass

        hkl = []
        if reflections is not None:
            if len(reflections) > 1:
                for i in range(1, 4):
                    hkl.append(reflections[1][i])

        return hkl

    def fl(self, ch,
           regx=re.compile(
            '(?<![\d.])'
            '(?![1-9]\d*(?![\d.])|\d*\.\d*\.)'
            '0*(?!(?<=0)\.)'
            '([\d.]+?)'
            '\.?0*'
            '(?![\d.])'
           ),
           repl=lambda mat: mat.group(mat.lastindex)
           if mat.lastindex != 3
           else '0' + mat.group(3)):
        mat = regx.search(ch)
        if mat:
            return regx.sub(repl, ch)

class br(Macro, _diffrac, Hookable):
    """Move the diffractometer to the reciprocal space coordinates given by
    H, K and L.
    If a fourth parameter is given, the combination of angles to be set is
    the correspondig to the given index. The index of the
    angles combinations are then changed."""

    hints = {'allowsHooks': ('pre-move', 'post-move')}
    param_def = [
        ['H', Type.String, None, "H value"],
        ['K', Type.String, None, "K value"],
        ['L', Type.String, None, "L value"],
        ['AnglesIndex', Type.Integer, -1, "Angles index"],
        ['FlagNotBlocking', Type.Integer,  0,
         "If 1 not block. Return without finish movement"],
        ['FlagPrinting', Type.Integer,  0,
         "If 1 printing. Used by ubr"]
    ]

    def prepare(self, H, K, L, AnglesIndex, FlagNotBlocking, FlagPrinting):
        _diffrac.prepare(self)
        self.motors = []
        for motor_name in self.angle_device_names.values():
            self.motors.append(self.getMotor(motor_name))     

    def run(self, H, K, L, AnglesIndex, FlagNotBlocking, FlagPrinting):
        h_idx = 0
        k_idx = 1
        l_idx = 2

        if AnglesIndex != -1:
            sel_tr = AnglesIndex
        else:
            sel_tr = self.diffrac.selectedtrajectory

        hkl_labels = ["H", "K", "L"]

        if H in hkl_labels or K in hkl_labels or L in hkl_labels:
            try:
                q_vector = self.getEnv('Q')
            except UnknownEnv:
                self.error("Environment Q not defined. Run wh to define it")
                return
            try:
                if H in hkl_labels:
                    H = float(q_vector[h_idx])
                if K in hkl_labels:
                    K = float(q_vector[k_idx])
                if L in hkl_labels:
                    L = float(q_vector[l_idx])
            except:
                self.error("Wrong format of Q vector")
                return
        hkl_values = [float(H), float(K), float(L)]

        self.diffrac.write_attribute("computetrajectoriessim", hkl_values)

        angles_list = self.diffrac.trajectorylist[sel_tr]

        if FlagNotBlocking == 0:
            cmd = "mv"
            for name, angle in zip(self.angle_names, angles_list):
                cmd = cmd + " " + str(self.angle_device_names[name])
                cmd = cmd + " " + str(angle)
            if FlagPrinting == 1:
                cmd = "u" + cmd
            mv, _ = self.createMacro(cmd)
            mv._setHooks(self.hooks)
            self.runMacro(mv)
        else:
            for name, angle in zip(self.angle_names, angles_list):
                angle_dev = self.getObj(self.angle_device_names[name])
                angle_dev.write_attribute("Position", angle)

        self.setEnv('Q', [hkl_values[h_idx], hkl_values[k_idx],
                          hkl_values[l_idx], self.diffrac.WaveLength])


class ubr(Macro, _diffrac, Hookable):
    """Move the diffractometer to the reciprocal space coordinates given by
    H, K and L und update.
    """
    hints = {'allowsHooks': ('pre-move', 'post-move')}
    param_def = [
        ["hh", Type.String, "Not set", "H position"],
        ["kk", Type.String, "Not set", "K position"],
        ["ll", Type.String, "Not set", "L position"],
        ['AnglesIndex', Type.Integer, -1, "Angles index"]
    ]

    def prepare(self, hh, kk, ll, AnglesIndex):
        _diffrac.prepare(self)
        self.motors = []
        for motor_name in self.angle_device_names.values():
            self.motors.append(self.getMotor(motor_name))            

    def run(self, hh, kk, ll, AnglesIndex):
        if ll != "Not set":
            br, _ = self.prepareMacro("br", hh, kk, ll, AnglesIndex, 0, 1)
            br._setHooks(self.hooks)
            self.runMacro(br)
        else:
            self.output("usage:  ubr H K L [Trajectory]")


class _ca(Macro, _diffrac):
    """Calculate motor positions for given H K L according to the current
    operation mode, for all trajectories or for the first one"""

    param_def = [
        ['H', Type.Float, None, "H value for the azimutal vector"],
        ['K', Type.Float, None, "K value for the azimutal vector"],
        ['L', Type.Float, None, "L value for the azimutal vector"],
        ['Trajectory', Type.Float, -1, "If -1, all trajectories"],
    ]

    def prepare(self, H, K, L, Trajectory):
        _diffrac.prepare(self)

    def run(self, H, K, L, Trajectory):

        hkl_values = [H, K, L]

        self.diffrac.write_attribute("computetrajectoriessim", hkl_values)

        if Trajectory == -1:
            start_range = 0
            end_range = len(self.diffrac.trajectorylist)
        else:
            start_range = Trajectory
            end_range = Trajectory + 1

        for i in range(int(start_range), int(end_range)):
            angles_list = self.diffrac.trajectorylist[i]
            self.output("")
            self.output("Trajectory %2d " % i)

            self.output("H K L =  %9.5f %9.5f %9.5f " %
                        (self.h_device.position, self.k_device.position,
                         self.l_device.position))

            try:
                self.output("Azimuth (Psi) = %7.5f" %
                            (self.psidevice.Position))
            except:
                self.warning(
                    "Not able to read psi. Check if environment Psi is defined")

            self.output("Wavelength =  %7.5f" % (self.diffrac.WaveLength))
            self.output("")

            str_pos = {}
            j = 0
            for name in self.angle_names:
                str_pos[name] = "%7.5f" % angles_list[j]
                j = j + 1

            if self.nb_motors == 6:
                self.output("%10s %11s %12s %11s %10s %11s" %
                            ("Delta", "Theta", "Chi", "Phi",
                             "Mu", "Gamma"))
                self.output("%10s %11s %12s %11s %10s %11s" %
                            (str_pos[self.labelmotor["Delta"]],
                             str_pos[self.labelmotor["Theta"]],
                             str_pos[self.labelmotor["Chi"]],
                             str_pos[self.labelmotor["Phi"]],
                             str_pos[self.labelmotor["Mu"]],
                             str_pos[self.labelmotor["Gamma"]]))
            elif self.nb_motors == 4:
                self.output("%10s %11s %12s %11s" %
                            ("Tth", "Omega", "Chi", "Phi"))
                self.output("%10s %11s %12s %11s" %
                            (str_pos[self.labelmotor["Tth"]],
                             str_pos[self.labelmotor["Omega"]],
                             str_pos[self.labelmotor["Chi"]],
                             str_pos[self.labelmotor["Phi"]]))
            elif self.nb_motors == 7:
                self.output("%10s %11s %12s %11s %11s %11s %11s" %
                            (self.angle_names[0],
                             self.angle_names[1],
                             self.angle_names[2],
                             self.angle_names[3],
                             self.angle_names[4],
                             self.angle_names[5],
                             self.angle_names[6]))
                self.output("%10s %11s %12s %11s %11s %11s %11s" %
                            (str_pos[self.angle_names[0]],
                             str_pos[self.angle_names[1]],
                             str_pos[self.angle_names[2]],
                             str_pos[self.angle_names[3]],
                             str_pos[self.angle_names[4]],
                             str_pos[self.angle_names[5]],
                             str_pos[self.angle_names[6]]))



class ca(Macro, _diffrac):
    """Calculate motor positions for given H K L according to the current
    operation mode (trajectory 0)."""

    param_def = [
        ['H', Type.Float, None, "H value for the azimutal vector"],
        ['K', Type.Float, None, "K value for the azimutal vector"],
        ['L', Type.Float, None, "L value for the azimutal vector"],
    ]

    def prepare(self, H, K, L):
        _diffrac.prepare(self)

    def run(self, H, K, L):

        hkl_values = [H, K, L]

        self.execMacro("_ca", H, K, L, 0)


class caa(Macro, _diffrac):
    """Calculate motor positions for given H K L according to the current
    operation mode (all trajectories)"""

    param_def = [
        ['H', Type.Float, None, "H value for the azimutal vector"],
        ['K', Type.Float, None, "K value for the azimutal vector"],
        ['L', Type.Float, None, "L value for the azimutal vector"],
    ]

    def prepare(self, H, K, L):
        _diffrac.prepare(self)

    def run(self, H, K, L):

        hkl_values = [H, K, L]

        self.execMacro("_ca", H, K, L)


class ci(Macro, _diffrac):
    """ Calculate hkl for given angle values """

    param_def = [
        ['mu', Type.Float, None, "Mu value"],
        ['theta', Type.Float, None, "Theta value"],
        ['chi', Type.Float, None, "Chi value"],
        ['phi', Type.Float, None, "Phi value"],
        ['gamma', Type.Float, -999, "Gamma value"],
        ['delta', Type.Float, -999, "Delta value"],
        ['omega_t', Type.Float, -999, "Omega_t value"],
    ]

    def prepare(self, mu, theta, chi, phi, gamma, delta, omega_t):
        _diffrac.prepare(self)

    def run(self, mu, theta, chi, phi, gamma, delta, omega_t):

        if delta == -999 and self.nb_motors == 6:
            self.error("Six angle values are need as argument")
        elif omega_t == -999 and self.nb_motors == 7:
            msg = ("Seven angle values are need as argument (omega_t is "
                   "missed - last argument)")
            self.error(msg)
        else:
            if self.nb_motors != 7:
                angles = [mu, theta, chi, phi, gamma, delta]
            else:
                angles = [omega_t, mu, theta, chi, phi, gamma, delta]

            self.diffrac.write_attribute("computehkl", angles)

            hkl_values = self.diffrac.computehkl

            self.output("h %f k %f l %f" %
                        (hkl_values[0], hkl_values[1], hkl_values[2]))


class pa(Macro, _diffrac):
    """Prints information about the active diffractometer."""

    suffix = ("st", "nd", "rd", "th")

    def prepare(self):
        _diffrac.prepare(self)

    def run(self):

        str_type = "Eulerian 6C"
        if self.type == 'E4CV':
            str_type = "Eulerian 4C Vertical"
        elif self.type == 'E4CH':
            str_type = "Eulerian 4C Horizontal"
        elif self.type == 'K6C':
            str_type = "Kappa 6C"
        elif self.type == 'K4CV':
            str_type = "Kappa 4C Vertical"

        self.output("%s Geometry (%s), %s" %
                    (str_type, self.type, self.diffrac.enginemode))
        #self.output("Sector %s" % "[ToDo]")
        self.output("")

        reflections = self.diffrac.reflectionlist

        nb_ref = 0
        if reflections is not None:
            for ref in reflections:
                if nb_ref < len(self.suffix):
                    sf = self.suffix[nb_ref]
                else:
                    sf = self.suffix[3]
                self.output("  %d%s Reflection (index %d): " %
                            (nb_ref + 1, sf, ref[0]))
                #self.output("    Affinement, Relevance : %d %d" % (ref[4], ref[5]))
                if len(ref) > 10 and len(self.angle_names) == 6:
                    self.output("    %s %s %s %s %s %s: %s %s %s %s %s %s" %
                                (self.angle_names[5], self.angle_names[1],
                                 self.angle_names[2], self.angle_names[3],
                                 self.angle_names[4], self.angle_names[0],
                                 _diffrac.fl(self, str(ref[11])),
                                 _diffrac.fl(self, str(ref[7])),
                                 _diffrac.fl(self, str(ref[8])),
                                 _diffrac.fl(self, str(ref[9])),
                                 _diffrac.fl(self, str(ref[10])),
                                 _diffrac.fl(self, str(ref[6]))))
                elif len(ref) > 10 and len(self.angle_names) == 7:
                    self.output(
                        "    %s %s %s %s %s %s %s: %s %s %s %s %s %s %s" %
                        (self.angle_names[0], self.angle_names[1],
                         self.angle_names[2], self.angle_names[3],
                         self.angle_names[4], self.angle_names[5],
                         self.angle_names[6],
                         _diffrac.fl(self, str(ref[6])),
                         _diffrac.fl(self, str(ref[7])),
                         _diffrac.fl(self, str(ref[8])),
                         _diffrac.fl(self, str(ref[9])),
                         _diffrac.fl(self, str(ref[10])),
                         _diffrac.fl(self, str(ref[11])),
                         _diffrac.fl(self, str(ref[12]))))
                else:
                    self.output("    %s %s %s %s: %s %s %s %s" %
                                (self.angle_names[0], self.angle_names[1],
                                 self.angle_names[2], self.angle_names[3],
                                 _diffrac.fl(self, str(ref[6])),
                                 _diffrac.fl(self, str(ref[7])),
                                 _diffrac.fl(self, str(ref[8])),
                                 _diffrac.fl(self, str(ref[9]))))
                nb_ref = nb_ref + 1
                self.output(" %33s  %s %s %s" % ("H K L =",
                                                 _diffrac.fl(
                                                     self, str(ref[1])),
                                                 _diffrac.fl(
                                                     self, str(ref[2])),
                                                 _diffrac.fl(
                                                     self, str(ref[3]))))
                self.output("")


#        self.output("")
        self.output("  Lattice Constants (lengths / angles):")
        self.output("%32s = %s %s %s / %s %s %s" % ("real space", self.diffrac.a,
                                                    self.diffrac.b, self.diffrac.c, _diffrac.fl(
                                                        self, str(self.diffrac.alpha)),
                                                    _diffrac.fl(self, str(
                                                        self.diffrac.beta)),
                                                    _diffrac.fl(self, str(
                                                        self.diffrac.gamma))))

        self.output("")
        self.output("  Azimuthal reference:")
        self.output("%34s %s %s %s " %
                    ("H K L =", _diffrac.fl(self, str(self.diffrac.psirefh)), _diffrac.fl(self, str(self.diffrac.psirefk)), _diffrac.fl(self, str(self.diffrac.psirefl))))

        self.output("")
        self.output("  Lambda = %s" % (self.diffrac.WaveLength))

        lst = self.diffrac.ubmatrix
        self.output("  UB-Matrix")
        self.output("  %15g %15g %15g" % (lst[0][0], lst[0][1], lst[0][2]))
        self.output("  %15g %15g %15g" % (lst[1][0], lst[1][1], lst[1][2]))
        self.output("  %15g %15g %15g" % (lst[2][0], lst[2][1], lst[2][2]))


class wh(Macro, _diffrac):
    """Show principal axes and reciprocal space positions.

    Prints the current reciprocal space coordinates (H K L) and the user
    positions of the principal motors. Depending on the diffractometer
    geometry, other parameters such as the angles of incidence and
    reflection (ALPHA and BETA) and the incident wavelength (LAMBDA)
    may be displayed."""

    def prepare(self):
        _diffrac.prepare(self)

    def run(self):

        self.output("")
        self.output("Engine: %s" % self.diffrac.engine)
        self.output("")
        self.output("Mode: %s" % self.diffrac.enginemode)

        self.output("")
        self.output("%s %s %3s %9.5f %9.5f %9.5f " %
                    ("H", "K", "L = ", self.h_device.position,
                     self.k_device.position, self.l_device.position))

        if self.diffrac.psirefh == -999:
            self.output("")
        else:
            self.output("%8s %9.5f %9.5f %9.5f " %
                        ("Ref   = ", self.diffrac.psirefh, self.diffrac.psirefk, self.diffrac.psirefl))

            psirefh_in = self.diffrac.psirefh
            psirefk_in = self.diffrac.psirefk
            psirefl_in = self.diffrac.psirefl
            engine_restore = self.diffrac.engine
            mode_restore = self.diffrac.enginemode

            self.diffrac.write_attribute("engine", "psi")

            psirefh_psi = self.diffrac.psirefh
            psirefk_psi = self.diffrac.psirefk
            psirefl_psi = self.diffrac.psirefl

            self.diffrac.write_attribute("engine", engine_restore)
            self.diffrac.write_attribute("enginemode", mode_restore)

            if psirefh_in != psirefh_psi or psirefk_in != psirefk_psi or psirefl_in != psirefl_psi:
                self.warning(
                    "Psiref vector missmatch. Calculated value corresponds to:")
                self.warning("%8s %9.5f %9.5f %9.5f " %
                             ("Ref   = ", psirefh_psi, psirefk_psi, psirefl_psi))
                self.warning("Use setaz for setting it consistently")

        try:
            self.output("%s %7.5f" % (
                "Azimuth (Psi - calculated) = ", self.psidevice.Position))
        except:
            self.warning(
                "Not able to read psi. Check if environment Psi is defined")

        parameter_names = self.diffrac.modeparametersnames

        if parameter_names is not None:
            i = 0
            for par in parameter_names:
                if par == "psi":
                    parameter_values = self.diffrac.modeparametersvalues
                    self.info("%s %7.5f" %
                              ("Azimuth (Psi - set) = ", parameter_values[i]))
                i = i + 1

        self.output("%s %7.5f" % ("Wavelength = ", self.diffrac.WaveLength))
        self.output("")

        if self.nb_motors == 6:
            str_pos1 = "%7.5f" % self.getDevice(
                self.angle_device_names[self.labelmotor["Delta"]]).Position
            str_pos2 = "%7.5f" % self.getDevice(
                self.angle_device_names[self.labelmotor["Theta"]]).Position
            str_pos3 = "%7.5f" % self.getDevice(
                self.angle_device_names[self.labelmotor["Chi"]]).Position
            str_pos4 = "%7.5f" % self.getDevice(
                self.angle_device_names[self.labelmotor["Phi"]]).Position
            str_pos5 = "%7.5f" % self.getDevice(
                self.angle_device_names[self.labelmotor["Mu"]]).Position
            str_pos6 = "%7.5f" % self.getDevice(
                self.angle_device_names[self.labelmotor["Gamma"]]).Position
            self.output("%10s %11s %12s %11s %10s %11s" %
                        ("Delta", "Theta", "Chi", "Phi", "Mu", "Gamma"))
            self.output("%10s %11s %12s %11s %10s %11s" %
                        (str_pos1, str_pos2, str_pos3, str_pos4, str_pos5,
                         str_pos6))
        elif self.nb_motors == 4:
            str_pos1 = "%7.5f" % self.getDevice(
                self.angle_device_names[self.labelmotor["Tth"]]).Position
            str_pos2 = "%7.5f" % self.getDevice(
                self.angle_device_names[self.labelmotor["Omega"]]).Position
            str_pos3 = "%7.5f" % self.getDevice(
                self.angle_device_names[self.labelmotor["Chi"]]).Position
            str_pos4 = "%7.5f" % self.getDevice(
                self.angle_device_names[self.labelmotor["Phi"]]).Position
            self.output("%10s %11s %12s %11s" %
                        ("Tth", "Omega", "Chi", "Phi"))
            self.output("%10s %11s %12s %11s" %
                        (str_pos1, str_pos2, str_pos3, str_pos4))
        elif self.nb_motors == 7:
            str_pos1 = "%7.5f" % self.getDevice(
                self.angle_device_names[self.angle_names[0]]).Position
            str_pos2 = "%7.5f" % self.getDevice(
                self.angle_device_names[self.angle_names[1]]).Position
            str_pos3 = "%7.5f" % self.getDevice(
                self.angle_device_names[self.angle_names[2]]).Position
            str_pos4 = "%7.5f" % self.getDevice(
                self.angle_device_names[self.angle_names[3]]).Position
            str_pos5 = "%7.5f" % self.getDevice(
                self.angle_device_names[self.angle_names[4]]).Position
            str_pos6 = "%7.5f" % self.getDevice(
                self.angle_device_names[self.angle_names[5]]).Position
            str_pos7 = "%7.5f" % self.getDevice(
                self.angle_device_names[self.angle_names[6]]).Position
            self.output("%10s %11s %12s %11s %11s %11s %11s" %
                        (self.angle_names[0],
                         self.angle_names[1],
                         self.angle_names[2],
                         self.angle_names[3],
                         self.angle_names[4],
                         self.angle_names[5],
                         self.angle_names[6]))
            self.output("%10s %11s %12s %11s %11s %11s %11s" %
                        (str_pos1,
                         str_pos2,
                         str_pos3,
                         str_pos4,
                         str_pos5,
                         str_pos6,
                         str_pos7))


        self.setEnv('Q', [self.h_device.position, self.k_device.position,
                          self.l_device.position, self.diffrac.WaveLength])


class freeze(Macro, _diffrac):
    """ Set psi value for psi constant modes """

    param_def = [
        ['parameter', Type.String, None, "Parameter to freeze"],
        ['value',     Type.Float,  None, "Value to be frozen"]
    ]

    def prepare(self, parameter, value):
        _diffrac.prepare(self)

    def run(self, parameter, value):

        if parameter == "psi":
            engine_restore = self.diffrac.engine
            mode_restore = self.diffrac.enginemode

            if mode_restore != "psi_constant_vertical" and mode_restore != "psi_constant_horizontal":
                self.warning(
                    "Psi frozen to set value. But current mode is not set to psi_constant_vertical or psi_constant_horizontal ")

            self.diffrac.write_attribute("engine", "hkl")
            self.diffrac.write_attribute("enginemode", "psi_constant_vertical")
            parameter_values = self.diffrac.modeparametersvalues
            parameter_values[3] = value
            self.diffrac.write_attribute(
                "modeparametersvalues", parameter_values)
            self.diffrac.write_attribute(
                "enginemode", "psi_constant_horizontal")
            parameter_values = self.diffrac.modeparametersvalues
            parameter_values[3] = value
            self.diffrac.write_attribute(
                "modeparametersvalues", parameter_values)

            self.diffrac.write_attribute("engine", engine_restore)
            self.diffrac.write_attribute("enginemode", mode_restore)

        else:
            self.error("Only implemented for parameter psi. Nothing done")


class setmode(iMacro, _diffrac):
    """Set operation mode."""

    param_def = [
        ['new_mode', Type.Integer, -1, "Mode to be set"]
    ]


    def prepare(self, new_mode):
        _diffrac.prepare(self)

    def run(self, new_mode):

        modes = self.diffrac.enginemodelist

        if new_mode == -1:
            self.output("Available modes:")
            imode = 1
            old_mode = self.diffrac.read_attribute("enginemode").value
            for mode in modes:
                if mode == old_mode:
                    def_mode = imode
                self.output(" %d -> %s " % (imode, mode))
                imode = imode + 1
            old_mode = self.diffrac.read_attribute("enginemode").value
            self.output("")
            a = self.input("Your choice?", default_value=def_mode)
            imode = 1
            for mode in modes:
                if imode == int(a):
                    def_mode = imode
                imode = imode + 1

            self.diffrac.write_attribute("enginemode", modes[def_mode - 1])
            self.output("")
            self.output("Now using %s mode" % modes[def_mode - 1])
            return

        if new_mode > len(modes):
            self.output(
                "Wrong index mode -> only from 1 to %d allowed:" % len(modes))
            imode = 1
            for mode in modes:
                self.output(" %d -> %s " % (imode, mode))
                imode = imode + 1
            return
        else:
            self.diffrac.write_attribute("enginemode", modes[new_mode - 1])
            self.output("Now using %s mode" % modes[new_mode - 1])

            self.execMacro('savecrystal')


class getmode(Macro, _diffrac):
    """Get operation mode."""

    def prepare(self):
        _diffrac.prepare(self)

    def run(self):

        self.output(self.diffrac.enginemode)


class setlat(iMacro, _diffrac):
    """Set the crystal lattice parameters a, b, c, alpha, beta and gamma
       for the currently active diffraction pseudo motor controller."""

    param_def = [
        ['a', Type.Float, -999, "Lattice 'a' parameter"],
        ['b', Type.Float, -999, "Lattice 'b' parameter"],
        ['c', Type.Float, -999, "Lattice 'c' parameter"],
        ['alpha', Type.Float, -999, "Lattice 'alpha' parameter"],
        ['beta',  Type.Float, -999, "Lattice 'beta' parameter"],
        ['gamma', Type.Float, -999, "Lattice 'gamma' parameter"]
    ]


    def prepare(self, a, b, c, alpha, beta, gamma):
        _diffrac.prepare(self)

    def run(self, a, b, c, alpha, beta, gamma):

        if gamma == -999:
            a = self.diffrac.a
            b = self.diffrac.b
            c = self.diffrac.c
            alpha = self.diffrac.alpha
            beta = self.diffrac.beta
            gamma = self.diffrac.gamma
            self.output("")
            self.output("Enter real space lattice parameters:")
            a = self.input(" Lattice a?", default_value=a,
                           data_type=Type.String)
            b = self.input(" Lattice b?", default_value=b,
                           data_type=Type.String)
            c = self.input(" Lattice c?", default_value=c,
                           data_type=Type.String)
            alpha = self.input(" Lattice alpha?",
                               default_value=alpha, data_type=Type.String)
            beta = self.input(" Lattice beta?",
                              default_value=beta, data_type=Type.String)
            gamma = self.input(" Lattice gamma?",
                               default_value=gamma, data_type=Type.String)
            self.output("")
            self.diffrac.write_attribute("a", float(a))
            self.diffrac.write_attribute("b", float(b))
            self.diffrac.write_attribute("c", float(c))
            self.diffrac.write_attribute("alpha", float(alpha))
            self.diffrac.write_attribute("beta", float(beta))
            self.diffrac.write_attribute("gamma", float(gamma))
        else:
            self.diffrac.write_attribute("a", a)
            self.diffrac.write_attribute("b", b)
            self.diffrac.write_attribute("c", c)
            self.diffrac.write_attribute("alpha", alpha)
            self.diffrac.write_attribute("beta", beta)
            self.diffrac.write_attribute("gamma", gamma)

        self.execMacro('computeub')


class or0(Macro, _diffrac):
    """Set primary orientation reflection."""

    param_def = [
        ['H', Type.Float, None, "H value"],
        ['K', Type.Float, None, "K value"],
        ['L', Type.Float, None, "L value"],
    ]

    def prepare(self, H, K, L):
        _diffrac.prepare(self)

    def run(self, H, K, L):

        # Check collinearity

        hkl_ref1 = _diffrac.get_hkl_ref1(self)
        if len(hkl_ref1) > 1:
            check = _diffrac.check_collinearity(
                self, H, K, L, hkl_ref1[0], hkl_ref1[1], hkl_ref1[2])
            if check:
                self.warning(
                    "Can not orient: or0 %9.5f %9.5f %9.5f are parallel to or1" % (H, K, L))
                return

        values = [0, H, K, L]
        self.diffrac.write_attribute("SubstituteReflection", values)

        self.execMacro('computeub')


class or1(Macro, _diffrac):
    """Set secondary orientation reflection."""

    param_def = [
        ['H', Type.Float, None, "H value"],
        ['K', Type.Float, None, "K value"],
        ['L', Type.Float, None, "L value"],
    ]

    def prepare(self, H, K, L):
        _diffrac.prepare(self)

    def run(self, H, K, L):

        # Check collinearity

        hkl_ref0 = _diffrac.get_hkl_ref0(self)
        if len(hkl_ref0) > 1:
            check = _diffrac.check_collinearity(
                self, hkl_ref0[0], hkl_ref0[1], hkl_ref0[2], H, K, L)
            if check:
                self.warning(
                    "Can not orient: or0 is parallel to or1 %9.5f %9.5f %9.5f" % (H, K, L))
                return

        values = [1, H, K, L]
        self.diffrac.write_attribute("SubstituteReflection", values)

        self.execMacro('computeub')


class setor0(Macro, _diffrac):
    """Set primary orientation reflection choosing hkl and angle values.
       Run it without any argument to see the order real positions"""

    param_def = [
        ['H', Type.Float, -999, "H value"],
        ['K', Type.Float, -999, "K value"],
        ['L', Type.Float, -999, "L value"],
        ['ang1', Type.Float, -999, "Real position"],
        ['ang2', Type.Float, -999, "Real position"],
        ['ang3', Type.Float, -999, "Real position"],
        ['ang4', Type.Float, -999, "Real position"],
        ['ang5', Type.Float, -999, "Real position"],
        ['ang6', Type.Float, -999, "Real position"],
        ['ang7', Type.Float, -999, "Real position"],
    ]

    def prepare(self, H, K, L, ang1, ang2, ang3, ang4, ang5, ang6, ang7):
        _diffrac.prepare(self)

    def run(self, H, K, L, ang1, ang2, ang3, ang4, ang5, ang6, ang7):
        setorn, pars = self.createMacro(
            "setorn", 0, H, K, L, ang1, ang2, ang3, ang4, ang5, ang6, ang7)

        self.runMacro(setorn)


class setor1(Macro, _diffrac):
    """Set secondary orientation reflection choosing hkl and angle values.
       Run it without any argument to see the order real positions"""

    param_def = [
        ['H', Type.Float, -999, "H value"],
        ['K', Type.Float, -999, "K value"],
        ['L', Type.Float, -999, "L value"],
        ['ang1', Type.Float, -999, "Real position"],
        ['ang2', Type.Float, -999, "Real position"],
        ['ang3', Type.Float, -999, "Real position"],
        ['ang4', Type.Float, -999, "Real position"],
        ['ang5', Type.Float, -999, "Real position"],
        ['ang6', Type.Float, -999, "Real position"],
        ['ang7', Type.Float, -999, "Real position"],
    ]

    def prepare(self, H, K, L, ang1, ang2, ang3, ang4, ang5, ang6, ang7):
        self.output("setor1 prepare")
        self.output(ang3)
        self.output(ang7)
        _diffrac.prepare(self)

    def run(self, H, K, L, ang1, ang2, ang3, ang4, ang5, ang6, ang7):
        setorn, pars = self.createMacro(
            "setorn", 1, H, K, L, ang1, ang2, ang3, ang4, ang5, ang6, ang7)

        self.runMacro(setorn)


class setorn(iMacro, _diffrac):
    """Set orientation reflection indicated by the index.
       Run it without any argument to see the order of the angles to be set"""

    param_def = [
        ['ref_id', Type.Integer, None, "reflection index (starting at 0)"],
        ['H', Type.Float, -999, "H value"],
        ['K', Type.Float, -999, "K value"],
        ['L', Type.Float, -999, "L value"],
        ['ang1', Type.Float, -999, "Real position"],
        ['ang2', Type.Float, -999, "Real position"],
        ['ang3', Type.Float, -999, "Real position"],
        ['ang4', Type.Float, -999, "Real position"],
        ['ang5', Type.Float, -999, "Real position"],
        ['ang6', Type.Float, -999, "Real position"],
        ['ang7', Type.Float, -999, "Real position"],
    ]

    def prepare(self, ref_id, H, K, L, ang1, ang2, ang3, ang4, ang5, ang6,
                ang7):
        _diffrac.prepare(self)

    def run(self, ref_id, H, K, L, ang1, ang2, ang3, ang4, ang5, ang6, ang7):

        if H == -999.0:
            msg = "Order of the real motor positions to be given as argument:"
            self.output(msg)
            for el in self.angle_names:
                self.output(el)
            return

        if ((ang6 == -999 and self.nb_motors == 6)
                or (ang4 == -999 and self.nb_motors == 4)
                or (ang7 == -999 and self.nb_motors == 7)):
            reflections = []
            try:
                reflections = self.diffrac.reflectionlist
            except:
                pass
            tmp_ref = {}
            hkl_names = ["h", "k", "l"]
            if reflections is not None:
                if len(reflections) > ref_id:
                    for i in range(1, 4):
                        tmp_ref[hkl_names[i - 1]] = reflections[ref_id][i]
                    for i in range(6, 6 + self.nb_motors):
                        tmp_ref[
                            self.angle_names[i - 6]] = reflections[ref_id][i]
                else:
                    for i in range(0, 3):
                        tmp_ref[hkl_names[i]] = 0
                    for i in range(0, self.nb_motors):
                        tmp_ref[self.angle_names[i]] = 0
            else:
                for i in range(0, 3):
                    tmp_ref[hkl_names[i]] = 0
                for i in range(0, self.nb_motors):
                    tmp_ref[self.angle_names[i]] = 0

            self.output("")
            if ref_id == 0:
                ref_txt = "primary-reflection"
            elif ref_id == 1:
                ref_txt = "secondary-reflection"
            else:
                ref_txt = "reflection " + str(ref_id)

            self.output("Enter %s angles" % ref_txt)
            angles_to_set = []
            for el in self.angle_names:
                angles_to_set.append(
                    float(self.input(el+"?",
                                     default_value=tmp_ref[el],
                                     data_type=Type.String)
                          )
                )


            self.output("")
            self.output("Enter %s HKL coordinates" % ref_txt)
            H = float(self.input(" H?", default_value=tmp_ref[
                      "h"], data_type=Type.String))
            K = float(self.input(" K?", default_value=tmp_ref[
                      "k"], data_type=Type.String))
            L = float(self.input(" L?", default_value=tmp_ref[
                      "l"], data_type=Type.String))
            self.output("")
        else:
            angles = [ang1, ang2, ang3, ang4, ang5, ang6, ang7]
            angles_to_set = []
            for i in range(0, self.nb_motors):
                angles_to_set.append(angles[i])

        # Check collinearity

        if ref_id == 0:
            hkl_ref = _diffrac.get_hkl_ref1(self)
        if ref_id == 1:
            hkl_ref = _diffrac.get_hkl_ref0(self)
        if ref_id < 2:
            if len(hkl_ref) > 1:
                check = _diffrac.check_collinearity(
                    self, hkl_ref[0], hkl_ref[1], hkl_ref[2], H, K, L)
                if check:
                    self.warning(
                        "Can not orient: ref0 is parallel to ref1 %9.5f %9.5f %9.5f" % (H, K, L))
                    return

        # Set reflection

        values = [ref_id, H, K, L]
        self.diffrac.write_attribute("SubstituteReflection", values)

        values = []
        values.append(ref_id)
        for el in angles_to_set:
            values.append(el)

        self.diffrac.write_attribute("AdjustAnglesToReflection", values)

        # Recompute u

        self.execMacro('computeub')


class setaz(iMacro, _diffrac):
    """ Set hkl values of the psi reference vector"""

    param_def = [
        ['PsiH', Type.Float, -999, "H value of psi reference vector"],
        ['PsiK', Type.Float, -999, "K value of psi reference vector"],
        ['PsiL', Type.Float, -999, "L value of psi reference vector"],
    ]

    def prepare(self, PsiH, PsiK, PsiL):
        _diffrac.prepare(self)

    def run(self, PsiH, PsiK, PsiL):
        engine_restore = self.diffrac.engine
        mode_restore = self.diffrac.enginemode

        if PsiL == -999:
            self.diffrac.write_attribute("engine", "hkl")
            self.diffrac.write_attribute("enginemode", "psi_constant_vertical")
            azh = self.diffrac.read_attribute("psirefh").value
            azk = self.diffrac.read_attribute("psirefk").value
            azl = self.diffrac.read_attribute("psirefl").value
            self.output("")
            self.output("Enter azimuthal reference H K L:")
            a1 = self.input(" Azimuthal H?", default_value=azh,
                            data_type=Type.String)
            a2 = self.input(" Azimuthal K?", default_value=azk,
                            data_type=Type.String)
            a3 = self.input(" Azimuthal L?", default_value=azl,
                            data_type=Type.String)
            PsiH = float(a1)
            PsiK = float(a2)
            PsiL = float(a3)

        self.diffrac.write_attribute("engine", "hkl")
        self.diffrac.write_attribute("enginemode", "psi_constant_vertical")
        self.diffrac.write_attribute("psirefh", PsiH)
        self.diffrac.write_attribute("psirefk", PsiK)
        self.diffrac.write_attribute("psirefl", PsiL)
        self.diffrac.write_attribute("enginemode", "psi_constant_horizontal")
        self.diffrac.write_attribute("psirefh", PsiH)
        self.diffrac.write_attribute("psirefk", PsiK)
        self.diffrac.write_attribute("psirefl", PsiL)
        self.diffrac.write_attribute("engine", "psi")
        self.diffrac.write_attribute("psirefh", PsiH)
        self.diffrac.write_attribute("psirefk", PsiK)
        self.diffrac.write_attribute("psirefl", PsiL)

        self.diffrac.write_attribute("engine", engine_restore)
        self.diffrac.write_attribute("enginemode", mode_restore)
        self.execMacro('savecrystal')


class computeub(Macro, _diffrac):
    """ Compute UB matrix with reflections 0 and 1 """

    def prepare(self):
        _diffrac.prepare(self)

    def run(self):

        reflections = self.diffrac.reflectionlist
        if reflections is not None:
            if len(reflections) > 1:
                self.output("Computing UB with reflections 0 and 1")
                values = [0, 1]
                self.diffrac.write_attribute("ComputeUB", values)
                self.execMacro('savecrystal')
            else:
                self.warning("UB can not be computed. Only one reflection")
        else:
            self.warning("UB can not be computed. No reflection")


class addreflection(Macro, _diffrac):
    """ Add reflection at the botton of reflections list """

    param_def = [
        ['H', Type.Float, None, "H value"],
        ['K', Type.Float, None, "K value"],
        ['L', Type.Float, None, "L value"],
        ['affinement', Type.Float, -999., "Affinement"]
    ]

    def prepare(self, H, K, L, affinement):
        _diffrac.prepare(self)

    def run(self, H, K, L, affinement):

        values = [H, K, L]
        if affinement != -999.:
            values.append(affinement)

        self.diffrac.write_attribute("AddReflection", values)


class affine(Macro, _diffrac):
    """Affine current crystal.
    Fine tunning of lattice parameters and UB matrix based on
    current crystal reflections. Reflections with affinement
    set to 0 are not used. A new crystal with the post fix
    (affine) is created and set as current crystal"""

    def prepare(self):
        _diffrac.prepare(self)

    def run(self):

        self.diffrac.write_attribute("AffineCrystal", 0)


class orswap(Macro, _diffrac):
    """Swap values for primary and secondary vectors."""

    def prepare(self):
        _diffrac.prepare(self)

    def run(self):

        self.diffrac.write_attribute("SwapReflections01", 0)
        self.output("Orientation vectors swapped.")
        self.execMacro('computeub')


class newcrystal(iMacro, _diffrac):
    """ Create a new crystal (if it does not exist) and select it. """

    param_def = [
        ['crystal_name',  Type.String, "", 'Name of the crystal to add and select']
    ]


    def prepare(self, crystal_name):
        _diffrac.prepare(self)

    def run(self, crystal_name):

        crystal_list = self.diffrac.crystallist

        to_add = 1
        i = 1
        if crystal_name == "":
            crystal_name = self.diffrac.crystal
            self.output("Available crystals:")
            for crystal in crystal_list:
                self.output("(%s) %s" % (i, crystal))
                if crystal_name == crystal:
                    iselname = crystal
                i = i + 1
            a = self.input("New crystal?", default_value=iselname,
                           data_type=Type.String)
            try:
                a1 = int(a)
                i = 1
                for crystal in crystal_list:
                    if a1 == i:
                        a = crystal
                    i = i + 1
                if a1 > i - 1:
                    a = iselname
            except:
                pass

            if a != iselname:
                crystal_name = a
            else:
                crystal_name = iselname

        for crystal in crystal_list:
            if crystal_name == crystal:
                to_add = 0

        if to_add:
            self.diffrac.write_attribute("addcrystal", crystal_name)

        self.diffrac.write_attribute("crystal", crystal_name)

        self.output("")
        self.output("Crystal selected: %s " % crystal_name)

        if to_add:
            a = self.input(" Lattice a?", default_value=5.43,
                           data_type=Type.String)
            b = self.input(" Lattice b?", default_value=5.43,
                           data_type=Type.String)
            c = self.input(" Lattice c?", default_value=5.43,
                           data_type=Type.String)
            alpha = self.input(" Lattice alpha?",
                               default_value=90, data_type=Type.String)
            beta = self.input(" Lattice beta?",
                              default_value=90, data_type=Type.String)
            gamma = self.input(" Lattice gamma?",
                               default_value=90, data_type=Type.String)
            self.output("")
            self.diffrac.write_attribute("a", float(a))
            self.diffrac.write_attribute("b", float(b))
            self.diffrac.write_attribute("c", float(c))
            self.diffrac.write_attribute("alpha", float(alpha))
            self.diffrac.write_attribute("beta", float(beta))
            self.diffrac.write_attribute("gamma", float(gamma))


class hscan(aNscan, Macro, _diffrac):
    "Scan h axis"

    param_def = [
        ['start_pos',  Type.Float,   None, 'Scan start position'],
        ['final_pos',  Type.Float,   None, 'Scan final position'],
        ['nr_interv',  Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float,   None, 'Integration time'],
    ]

    def prepare(self, start_pos, final_pos, nr_interv, integ_time):
        _diffrac.prepare(self)
        aNscan._prepare(self, [self.h_device], [start_pos],
                        [final_pos], nr_interv, integ_time)


class kscan(aNscan, Macro, _diffrac):
    "Scan k axis"

    param_def = [
        ['start_pos',  Type.Float,   None, 'Scan start position'],
        ['final_pos',  Type.Float,   None, 'Scan final position'],
        ['nr_interv',  Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float,   None, 'Integration time'],
    ]

    def prepare(self, start_pos, final_pos, nr_interv, integ_time):
        _diffrac.prepare(self)
        aNscan._prepare(self, [self.k_device], [start_pos],
                        [final_pos], nr_interv, integ_time)


class lscan(aNscan, Macro, _diffrac):
    "Scan l axis"

    param_def = [
        ['start_pos',  Type.Float,   None, 'Scan start position'],
        ['final_pos',  Type.Float,   None, 'Scan final position'],
        ['nr_interv',  Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float,   None, 'Integration time'],
    ]

    def prepare(self, start_pos, final_pos, nr_interv, integ_time):
        _diffrac.prepare(self)
        aNscan._prepare(self, [self.l_device], [start_pos],
                        [final_pos], nr_interv, integ_time)


class hklscan(aNscan, Macro, _diffrac):
    "Scan h k l axes"

    param_def = [
        ['h_start_pos',  Type.Float,   None, 'Scan h start position'],
        ['h_final_pos',  Type.Float,   None, 'Scan h final position'],
        ['k_start_pos',  Type.Float,   None, 'Scan k start position'],
        ['k_final_pos',  Type.Float,   None, 'Scan k final position'],
        ['l_start_pos',  Type.Float,   None, 'Scan l start position'],
        ['l_final_pos',  Type.Float,   None, 'Scan l final position'],
        ['nr_interv',  Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float,   None, 'Integration time'],
    ]

    def prepare(self, h_start_pos, h_final_pos, k_start_pos, k_final_pos, l_start_pos, l_final_pos, nr_interv, integ_time):
        _diffrac.prepare(self)
        aNscan._prepare(self, [self.h_device, self.k_device, self.l_device],
                        [h_start_pos, k_start_pos, l_start_pos], [h_final_pos,
                                                                  k_final_pos,
                                                                  l_final_pos],
                        nr_interv, integ_time)



class th2th(Macro):
    """th2th - scan:

    Relative scan around current position in del and th with d_th=2*d_delta
    """

    param_def = [
        ['rel_start_pos',  Type.Float,   -999, 'Scan start position'],
        ['rel_final_pos',  Type.Float,   -999, 'Scan final position'],
        ['nr_interv',  Type.Integer, -999, 'Number of scan intervals'],
        ['integ_time', Type.Float,   -999, 'Integration time']
    ]

    def run(self, rel_start_pos, rel_final_pos, nr_interv, integ_time):

        if ((integ_time != -999)):
            motor_del = self.getObj("del")
            motor_th = self.getObj("th")
            pos_del = motor_del.getPosition()
            pos_th = motor_th.getPosition()
            scan = self.d2scan(motor_del, rel_start_pos, rel_final_pos,
                               motor_th, rel_start_pos / 2, rel_final_pos / 2,
                               nr_interv, integ_time)
        else:
            self.output(
                "Usage:   th2th tth_start_rel tth_stop_rel intervals time")


count_scan = 1


class HookPars:
    pass


def hook_pre_move(self, hook_pars):
    global count_scan

    self.execMacro('freeze', 'psi', hook_pars.psi_save + +
                   hook_pars.angle_start + (count_scan - 1) * hook_pars.angle_interv)
    self.execMacro('ubr', hook_pars.h, hook_pars.k, hook_pars.l)

    count_scan = count_scan + 1


class luppsi(Macro, _diffrac):
    """psi scan:

    Relative scan psi angle

    [TODO] Still not tested
    """

    param_def = [
        ['rel_start_angle',  Type.Float,   -999, 'Relative start scan angle'],
        ['rel_final_angle',  Type.Float,   -999, 'Relative final scan angle'],
        ['nr_interv',  Type.Integer, -999, 'Number of scan intervals'],
        ['integ_time', Type.Float,   -999, 'Integration time']
    ]

    def prepare(self, H, K, L, AnglesIndex):
        _diffrac.prepare(self)

    def run(self, rel_start_angle, rel_final_angle, nr_interv, integ_time):

        global count_scan
        count_scan = 1

        if ((integ_time != -999)):
            self.diffrac.write_attribute("engine", "hkl")
            self.diffrac.write_attribute("enginemode", "psi_constant_vertical")
            h = self.h_device.position
            k = self.k_device.position
            l = self.l_device.position

            psi_positions = []

            try:
                psi_save = self.psidevice.Position
            except:
                self.error(
                    "Not able to read psi. Check if environment Psi is defined")
                return

            angle_interv = abs(rel_final_angle - rel_start_angle) / nr_interv

            # Construct scan macro

            self.output(self.psidevice.alias())
            psi_motor = self.getMotor(self.psidevice.alias())
            self.output(psi_motor)

            macro, pars = self.createMacro('dscan %s %f %f %d %f ' %
                                           (self.psidevice.alias(), rel_start_angle, rel_final_angle, nr_interv, integ_time))

            # Parameters for scan hook function

            hook_pars = HookPars()
            hook_pars.psi_save = psi_save
            hook_pars.angle_interv = angle_interv
            hook_pars.angle_start = rel_start_angle
            hook_pars.h = h
            hook_pars.k = k
            hook_pars.l = l
            f = lambda: hook_pre_move(self, hook_pars)
            macro.hooks = [
                (f, ["pre-move"]),
            ]

            # Start the scan

            self.runMacro(macro)

            # Return to start position

            self.info("Return to start position " + str(psi_save))
            self.execMacro('freeze', 'psi', psi_save)
            self.execMacro('ubr', h, k, l)
            self.psidevice.write_attribute("Position", psi_save)

        else:
            self.output(
                "Usage:  luppsi rel_startangle  rel_stopangle n_intervals time")


class savecrystal(Macro, _diffrac):
    """
         Save crystal information to file
    """

    def prepare(self):
        _diffrac.prepare(self)

    def run(self):

        self.info("Be aware: changes in crystal file format are still possible.")
        self.diffrac.write_attribute("SaveCrystal", 1)


class loadcrystal(iMacro, _diffrac):
    """
         Load crystal information from file
    """

    def prepare(self):
        _diffrac.prepare(self)

    def run(self):
        self.info("Be aware: changes in crystal file format are still possible.")
        active_dir = ""
        try:
            files = os.listdir(os.path.expanduser('~') + '/crystals/')
            active_dir = os.path.expanduser('~') + '/crystals/'
        except:
            self.output(
                "Directory for loading files %s/crystals does not exist" % os.path.expanduser('~'))
            newdir = self.input("Type new directory")
            try:
                files = os.listdir(newdir)
                active_dir = newdir
            except:
                self.output("New directory %s not found" % newdir)
                return

        res = [x for x in files if x.endswith('.txt')]
        if len(res) == 0:
            self.output("No crystals available in set directory. Nothing done")
            return

        i = 1
        for filename in res:
            filename = filename.split('.')[0]
            self.output("(%s) %s" % (i, filename))
            i = i + 1
        a0 = self.input("Your choice? ")
        try:
            a1 = int(a0)
            i = 1
            for filename in res:
                if i == int(a0) and i < len(res) + 1:
                    file = filename
                i = i + 1
            if a1 < len(res) + 1:
                self.output("")
                self.output("File to load %s" % active_dir + file)
            else:
                self.output("Input out of range!")

            self.diffrac.write_attribute("loadcrystal", active_dir + file)
            self.diffrac.read_attribute("loadcrystal")

        except:
            if a0 != "":
                self.output("Wrong input!")
            else:
                self.output("An input file has to be given. Nothing done")


class latticecal(iMacro, _diffrac):
    """
        Calibrate lattice parameters a, b or c to current 2theta value
    """

    param_def = [
        ["parameter", Type.String, "", "Parameter"],
    ]

    def prepare(self, parameter):
        _diffrac.prepare(self)

    def run(self, parameter):
        if parameter != "":
            if parameter == "a" or parameter == "b" or parameter == "c":
                if parameter == "a":
                    a0 = self.diffrac.a
                    self.output("Old lattice parameter %s = %s" %
                                (parameter, a0))
                    h0 = self.h_device.position
                    h1 = py2_round(h0)  # TODO: check if round would be fine?
                    a1 = h1 / h0 * a0
                    self.output("New lattice parameter %s = %s" %
                                (parameter, a1))
                    self.diffrac.write_attribute("a", a1)
                if parameter == "b":
                    a0 = self.diffrac.b
                    self.output("Old lattice parameter %s = %s" %
                                (parameter, a0))
                    h0 = self.k_device.position
                    h1 = py2_round(h0)  # TODO: check if round would be fine?
                    a1 = h1 / h0 * a0
                    self.output("New lattice parameter %s = %s" %
                                (parameter, a1))
                    self.diffrac.write_attribute("b", a1)
                if parameter == "c":
                    a0 = self.diffrac.c
                    self.output("Old lattice parameter %s = %s" %
                                (parameter, a0))
                    h0 = self.l_device.position
                    h1 = py2_round(h0)  # TODO: check if round would be fine?
                    a1 = h1 / h0 * a0
                    self.output("New lattice parameter %s = %s" %
                                (parameter, a1))
                    self.diffrac.write_attribute("c", a1)

                self.execMacro('computeub')

            else:
                self.output("Lattice parameter a, b or c")

        else:
            self.output(
                "Calibration of lattice parameters a, b or c to current 2theta value")
            self.output("usage:  latticecal parameter")


class _blockprintmove(Macro, _diffrac):
    """This macro is internal and reserved to the hkl infrastucture
    """
    param_def = [
        ['flagprint', Type.Integer, 0, '1 for printing']
    ]

    def prepare(self, flagprint):
        _diffrac.prepare(self)

    def run(self, flagprint):

        moving = 1
        tmp_dev = {}
        for angle in self.angle_names:
            tmp_dev[angle] = self.getDevice(self.angle_device_names[angle])
        while(moving):
            moving = 0
            for angle in self.angle_names:
                angle_state = tmp_dev[angle].stateObj.read().rvalue
                if angle_state == 6:
                    moving = 1
            if flagprint == 1:
                self.outputBlock(" %7.5f  %7.5f  %7.5f" % (
                    self.h_device.position, self.k_device.position, self.l_device.position))
                self.flushOutput()
            self.checkPoint()
            time.sleep(1.0)
        if flagprint == 1:
            self.outputBlock(" %7.5f  %7.5f  %7.5f" % (
                self.h_device.position, self.k_device.position, self.l_device.position))
            self.flushOutput()


class _diff_scan(Macro):
    """Perfoms an scan keeping the data for further analysis/moves.
    This macro is internal and reserved to the hkl infrastucture.
    """
    param_def = [
        ['motor',      Type.Motor,   None, 'Motor to move'],
        ['start_pos',  Type.Float,   None, 'Scan start position'],
        ['final_pos',  Type.Float,   None, 'Scan final position'],
        ['nr_interv',  Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float,   None, 'Integration time'],
        ['channel',    Type.ExpChannel,   None, 'Channel to analize']
    ]

    def run(self, motor, start_pos, final_pos, nr_interv, integ_time, channel):

        ascan, pars = self.createMacro(
            "ascan", motor, start_pos, final_pos, nr_interv, integ_time)
        self.runMacro(ascan)

        channel_fullname = channel.getFullName()
        motor_name = motor.getName()

        arr_data = []
        arr_motpos = []
        for record in ascan.data.records:
            record_data = record.data
            arr_data.append(record_data[channel_fullname])
            arr_motpos.append(record_data[motor_name])

        # Find motor position corresponding to the maximum of channel values
        idx_max = np.argmax(arr_data)
        pos_max = arr_motpos[idx_max]

        self.output("Position to move")
        self.output(pos_max)
