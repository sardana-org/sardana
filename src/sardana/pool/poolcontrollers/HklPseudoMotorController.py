# -*- coding: utf-8 -*-

##############################################################################
##
## This file is part of Sardana
##
## http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
##
## Copyright: 2013 PetraIII,
##            2013 Synchrotron-Soleil
##                 L'Orme des Merisiers Saint-Aubin
##                 BP 48 91192 GIF-sur-YVETTE CEDEX
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

"""This module contains the definition of an Hkl pseudo motor controller
for the Sardana Device Pool"""

__author__ = ("Maria-Teresa Nunez-Pardo-de-Verra <tnunez@mail.desy.de>, "
              "Picca Frédéric-Emmanuel <picca@synchrotron-soleil.fr>")
__copyright__ = ("Copyright (c) 2013 DESY "
                 "Copyright (c) 2013 Synchrotron-Soleil "
                 "L'Orme des Merisiers Saint-Aubin "
                 "BP 48 91192 GIF-sur-YVETTE CEDEX")
__license__ = 'LGPL-3+'

__all__ = ["Diffrac6C", "DiffracE6C", "DiffracK6C",
           "Diffrac4C", "DiffracE4C", "DiffracK4C", "Diffrac4CZAXIS",
           "Diffrac2C"]

__docformat__ = 'restructuredtext'

import math
import os
import time

from gi.repository import GLib
from gi.repository import Hkl

from sardana import DataAccess
from sardana.pool.controller import PseudoMotorController
from sardana.pool.controller import Type, Access, Description
from sardana.pool.controller import Memorize, MemorizedNoInit

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class DiffracBasis(PseudoMotorController):

    """ The PseudoMotor controller for the diffractometer"""

    class_prop = {'DiffractometerType':
                 {Type: str, Description: 'Type of the diffractometer, e.g. E6C'}, }

    ctrl_attributes = {'Crystal': {Type: str, 
                                   Memorize: MemorizedNoInit,
                                   Access: ReadWrite},
                       'AffineCrystal': {Type: int,
                                         Memorize: MemorizedNoInit,
                                         Description: "Affine current crystal. Add a new crystal with the post fix (affine)",
                                         Access: ReadWrite},
                       'Wavelength': {Type: float, 
                                      Memorize: MemorizedNoInit,
                                      Access: ReadWrite},
                       'EngineMode': {Type: str, Access: ReadWrite},
                       'EngineModeList': {Type: (str,), Access: ReadOnly},
                       'HKLModeList': {Type: (str,), Access: ReadOnly},
                       'UBMatrix': {Type: ((float,), ),
                                    Description: "The reflection matrix",
                                    Access: ReadOnly},
                       'Ux': {Type: float, Access: ReadWrite},
                       'Uy': {Type: float, Access: ReadWrite},
                       'Uz': {Type: float, Access: ReadWrite},
                       'ComputeU': {Type: (int,),
                                    Description: "Compute reflection matrix using two given reflections",
                                    Access: ReadWrite},
                       'LatticeReciprocal': {Type: (float,),
                                             Description: "The reciprocal lattice parameters of the sample",
                                             Access: ReadOnly},
                       'A': {Type: float,
                             Description: "a parameter of the lattice",
                             Memorize: MemorizedNoInit,
                             Access: ReadWrite},
                       'B': {Type: float,
                             Description: "b parameter of the lattice",
                             Memorize: MemorizedNoInit,
                             Access: ReadWrite},
                       'C': {Type: float,
                             Description: "c parameter of the lattice",
                             Memorize: MemorizedNoInit,
                             Access: ReadWrite},
                       'Alpha': {Type: float,
                                 Description: "alpha parameter of the lattice",
                                 Memorize: MemorizedNoInit,
                                 Access: ReadWrite},
                       'Beta': {Type: float,
                                Description: "beta parameter of the lattice",
                                Memorize: MemorizedNoInit,
                                Access: ReadWrite},
                       'Gamma': {Type: float,
                                 Description: "gamma parameter of the lattice",
                                 Memorize: MemorizedNoInit,
                                 Access: ReadWrite},
                       'AFit': {Type: int,
                                Description: "Fit value of the a parameter of the lattice",
                                Memorize: MemorizedNoInit,
                                Access: ReadWrite},
                       'BFit': {Type: int,
                                Description: "Fit value of the b parameter of the lattice",
                                Memorize: MemorizedNoInit,
                                Access: ReadWrite},
                       'CFit': {Type: int,
                                Description: "Fit value of the c parameter of the lattice",
                                Memorize: MemorizedNoInit,
                                Access: ReadWrite},
                       'AlphaFit': {Type: int,
                                    Description: "Fit value of the alpha parameter of the lattice",
                                    Memorize: MemorizedNoInit,
                                    Access: ReadWrite},
                       'BetaFit': {Type: int,
                                   Description: "Fit value of the beta parameter of the lattice",
                                   Memorize: MemorizedNoInit,
                                   Access: ReadWrite},
                       'GammaFit': {Type: int,
                                    Description: "Fit value of the gamma parameter of the lattice",
                                    Memorize: MemorizedNoInit,
                                    Access: ReadWrite},
                       'TrajectoryList': {Type: ((float,), (float,)),
                                          Description: "List of trajectories for hklSim",
                                          Access: ReadOnly},
                       'SelectedTrajectory': {Type: int,
                                              Description: "Index of the trajectory you want to take for the given hkl values. 0 (by default) if first.",
                                              Access: ReadWrite},
                       'ComputeTrajectoriesSim': {Type: (float,),
                                                  Description: "Pseudo motor values to compute the list of trajectories (1, 2 or 3 args)",
                                                  Access: ReadWrite},
                       'Engine': {Type: str, Access: ReadWrite},
                       'EngineList': {Type: (str,), Access: ReadOnly},
                       'CrystalList': {Type: (str,), Access: ReadOnly},
                       'AddCrystal': {Type: str, 
                                      Memorize: MemorizedNoInit,
                                      Access: ReadWrite},
                       'DeleteCrystal': {Type: str, 
                                         Memorize: MemorizedNoInit,
                                         Access: ReadWrite},
                       'AddReflection': {Type: (float,),
                                         Description: "Add reflection to current sample",
                                         Access: ReadWrite},
                       'AddReflectionWithIndex': {Type: (float,),
                                         Description: "Add reflection to current sample with given index",
                                         Access: ReadWrite},
                       'SwapReflections01': {Type: int,
                                         Description: "Swap primary and secondary reflections",
                                         Access: ReadWrite},
                       'ReflectionList': {Type: ((float,), (float,)),
                                          Description: "List of reflections for current sample",
                                          Access: ReadOnly},
                       'RemoveReflection': {Type: int,
                                            Memorize: MemorizedNoInit,
                                            Description: "Remove reflection with given index",
                                            Access: ReadWrite},
                       'LoadReflections': {Type: str,
                                           Description: "Load the reflections from the file given as argument",
                                           Memorize: MemorizedNoInit, 
                                           Access: ReadWrite},
                       'SaveReflections': {Type: str,
                                           Description: "Save current reflections to file",
                                           Memorize: MemorizedNoInit,
                                           Access: ReadWrite},
                       'LoadCrystal':     {Type: str,
                                           Description: "Load the lattice parameters and reflections from the file corresponding to the given crystal",
                                           Access: ReadWrite},
                       'SaveCrystal': {Type: str,
                                           Description: "Save current crystal parameters and reflections to file",
                                           Memorize: MemorizedNoInit,
                                           Access: ReadWrite},
                       'AdjustAnglesToReflection': {Type: (float,),
                                                    Description: "Set the given angles to the reflection with given index",
                                                    Access: ReadWrite},
                       'ReflectionAngles': {Type: ((float,), (float,)),
                                            Description: "Angles between reflections",
                                            Access: ReadOnly},
                       'ModeParametersNames': {Type: (str,),
                                               Description: "Name of the parameters of the current mode (if any)",
                                               Access: ReadOnly},
                       'ModeParametersValues': {Type: (float,),
                                                Description: "Value of the parameters of the current mode (if any)",
                                                Access: ReadWrite},
                       'PsiRefH': {Type: float,
                             Description: "x coordinate of the psi reference vector (-999 if not applicable)",
                             Access: ReadWrite},
                       'PsiRefK': {Type: float,
                             Description: "y coordinate of the psi reference vector (-999 if not applicable)",
                             Access: ReadWrite},
                       'PsiRefL': {Type: float,
                             Description: "z coordinate of the psi reference vector (-999 if not applicable)",
                             Access: ReadWrite},
                       'MotorList': {Type: (str,),
                                     Description: "Name of the real motors",
                                     Access: ReadOnly},
                       'HKLPseudoMotorList': {Type: (str,),
                                              Description: "Name of the hkl pseudo motors",
                                              Access: ReadOnly},
                       }

    MaxDevice = 1

    def __init__(self, inst, props, *args, **kwargs):
        """ Do the default init plus the specific diffractometer
        staff.
        @param properties of the controller
        """
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)

        self.first_crystal_set = 1
        self.samples_list = {}

        self.samples_list[
            "default_crystal"] = Hkl.Sample.new("default_crystal")
#    self.sample = Hkl.Sample.new("default_crystal")
        self.sample = self.samples_list["default_crystal"]
        lattice = self.sample.lattice_get()
        lattice.set(1.5, 1.5, 1.5,
                    math.radians(90.0),
                    math.radians(90.0),
                    math.radians(90.))
        self.sample.lattice_set(lattice)
        self._a = 1.5
        self._b = 1.5
        self._c = 1.5
        self._alpha = 90.
        self._beta  = 90.
        self._gamma = 90.

        self.crystallist = []
        self.crystallist.append("default_crystal")

        self.detector = Hkl.Detector.factory_new(Hkl.DetectorType(0))
        self.detector.idx_set(1)

        for key, factory in Hkl.factories().iteritems():
            if key == self.DiffractometerType:
                self.geometry = factory.create_new_geometry()
                self.engines = factory.create_new_engine_list()

        if self.DiffractometerType in ("E6C", "K6C", "SOLEIL SIXS MED2+2", "PETRA3 P09 EH2"):
            self.nb_ph_axes = 6
        elif self.DiffractometerType in ("E4CV", "K4CV", "E4CH", "SOLEIL MARS", "ZAXIS"):  # "SOLEIL SIXS MED1+2" also here ???
            self.nb_ph_axes = 4
        elif self.DiffractometerType in ("TwoC"):
            self.nb_ph_axes = 2

            # here we set the detector arm with only positive values for
            # now tth or delta arm
        for axis in self.geometry.axes():
            if axis.name_get() in ["tth", "delta"]:
                axis.min_max_unit_set(0, 180.)

        self.engines.init(self.geometry, self.detector, self.sample)
        engines_names = [engine.name() for engine in self.engines.engines()]
        print str(engines_names)

        # Engine hkl -> it has not effect, it will be set the last value set
        # (stored in DB)
        self.engine = self.engines.get_by_name("hkl")

        self.trajectorylist = []
        self.lastpseudopos = [0] * 3
        self.selected_trajectory = 0

        # Put to -1 the attributes that are actually commands
        self._affinecrystal = -1
        self._removereflection = -1
        self._deletecrystal = 'nothing'
        self._addcrystal = 'nothing'
        self._addreflection = [-1.]
        self._addreflectionwithindex = [-1.]
        self._swapreflections01 = -1
        self._loadreflections = " "  # Only to create the member, the value will be overwritten by the one in stored in the database
        self._savereflections = " "  # Only to create the member, the value will be overwritten by the one in stored in the database

    def calc_physical(self, index, pseudos):
        return self.calc_all_physical(pseudos)[index - 1]

    def calc_pseudo(self, index, physicals):
        pos = self.calc_all_pseudo(physicals)[index - 1]
        return pos

    def calc_all_physical(self, pseudos):

        h = pseudos[0]
        k = pseudos[1]
        l = pseudos[2]

        try:
            if self.nb_ph_axes == 4:  # "E4CV", "E4CH", "SOLEIL MARS": hkl(3), psi(1), q(1); "K4CV": hkl(3), psi(1), q(1), eulerians(3); "SOLEIL SIXS MED1+2": hkl(3), q2(2), qper_qpar(2)
                if self.engine.name() == "hkl":
                    self.engine.set_values_unit(
                        [pseudos[0], pseudos[1], pseudos[2]])  # compute the HklGeometry angles for this HklEngine
                elif self.engine.name() == "psi":
                    self.engine.set_values_unit([pseudos[3]])
                elif self.engine.name() == "q":
                    self.engine.set_values_unit([pseudos[4]])
                elif self.engine.name() == "eulerians":
                    self.engine.set_values_unit(
                        [pseudos[5], pseudos[6], pseudos[7]])
                elif self.engine.name() == "q2":
                    self.engine.set_values_unit([pseudos[3], pseudos[4]])
                elif self.engine.name() == "qper_qpar":
                    self.engine.set_values_unit([pseudos[5], pseudos[6]])
            elif self.nb_ph_axes == 6:  # "E6C", "SOLEIL SIXS MED2+2": hkl(3), psi(1), q2(2), qper_qpar(2); "K6C":  hkl(3), psi(1), q2(2), qper_qpar(2), eulerians(3); "PETRA3 P09 EH2": hkl(3)
                if self.engine.name() == "hkl":
                    self.engine.set_values_unit(
                        [pseudos[0], pseudos[1], pseudos[2]])
                elif self.engine.name() == "psi":
                    self.engine.set_values_unit([pseudos[3]])
                elif self.engine.name() == "q2":
                    self.engine.set_values_unit([pseudos[4], pseudos[5]])
                elif self.engine.name() == "qper_qpar":
                    self.engine.set_values_unit([pseudos[6], pseudos[7]])
                elif self.engine.name() == "eulerians":
                    self.engine.set_values_unit(
                        [pseudos[8], pseudos[9], pseudos[10]])
            else:
                if self.engine.name() == "hkl":
                    self.engine.set_values_unit(
                        [pseudos[0], pseudos[1], pseudos[2]])

        # Read the positions
            for i, item in enumerate(self.engine.engines().geometries().items()):
                if i == self.selected_trajectory:
                    values = item.geometry().get_axes_values_unit()

        except GLib.GError, err:
            raise Exception("Not solution for this mode")

        return tuple(values)

    def calc_all_pseudo(self, physicals):
        print "calc_all_pseudo"

        mu = physicals[0]
        th = physicals[1]
        if self.nb_ph_axes > 2:
            chi = physicals[2]
            phi = physicals[3]
        if self.nb_ph_axes == 6:
            gamma = physicals[4]
            delta = physicals[5]

        # Calcular hkl
        if self.nb_ph_axes == 6:
            self.geometry.set_axes_values_unit(
                [mu, th, chi, phi, gamma, delta])
        elif self.nb_ph_axes == 4:
            self.geometry.set_axes_values_unit([mu, th, chi, phi])
        else:
            self.geometry.set_axes_values_unit([mu, th])

        self.engines.get()

        values = []
        for tmp_engine in self.engines.engines():
            values = values + tmp_engine.pseudo_axes().values_unit_get()

        return tuple(values)

    def getCrystal(self):
        print " getCrystal"
        return self.sample.name_get()

    def setCrystal(self, value):
        print " setCrystal"
        if self.first_crystal_set == 0:
            if value in self.crystallist:
                self.sample = self.samples_list[value]
        else:            
            self.crystallist.append(value)
            self.samples_list[value] = Hkl.Sample.new(
                value)  # By default a crystal is created with lattice parameters 1.54, 1.54, 1.54, 90., 90., 90.
            self.sample = self.samples_list[value]
            lattice = self.sample.lattice_get()
            lattice.set(self._a, self._b, self._c,
                        math.radians(self._alpha),
                        math.radians(self._gamma),
                        math.radians(self._beta))
            self.sample.lattice_set(lattice)
            # For getting the UB matrix changing
            self.sample.lattice_set(lattice)
            
            self.first_crystal_set = 0

    def setAffineCrystal(self, value):
        print " setAffineCrystal"
        new_sample_name = self.sample.name_get() + " (affine)"
        if new_sample_name not in self.crystallist:
            self.crystallist.append(new_sample_name)
            self.samples_list[new_sample_name] = self.sample.copy()
            self.samples_list[new_sample_name].name_set(new_sample_name)
            self.samples_list[new_sample_name].affine()
            self.sample = self.samples_list[new_sample_name]

    def getWavelength(self):
        print " getWavelength"
        return self.geometry.wavelength_get()

    def setWavelength(self, value):
        print " setWavelength"
        self.geometry.wavelength_set(value)

    def getEngineMode(self):
#        print " getEngineMode"
        return self.engine.mode().name()

    def setEngineMode(self, value):
        print " setEngineMode"
        for mode in self.engine.modes():
            if value == mode.name():
                self.engine.select_mode(mode)

    def getEngineModeList(self):
        print " getEngineModeList"
        engine_mode_names = []
        i = 0
        for mode in self.engine.modes():
            engine_mode_names.append(mode.name())
        return engine_mode_names

    def getHKLModeList(self):
        print " getHKLModeList"
        hkl_mode_names = []
        for key, factory in Hkl.factories().iteritems():
            if key == self.DiffractometerType:
                new_engines = factory.create_new_engine_list()
        new_engines.init(self.geometry, self.detector, self.sample)
        hkl_engine = new_engines.get_by_name("hkl")
        for mode in hkl_engine.modes():
            hkl_mode_names.append(mode.name())
        return hkl_mode_names

    def getUBMatrix(self):
        print " getUBMatrix"
        arr = []
        arr.append([])
        arr[0].append(self.sample.UB_get().get(0, 0))
        arr[0].append(self.sample.UB_get().get(0, 1))
        arr[0].append(self.sample.UB_get().get(0, 2))
        arr.append([])
        arr[1].append(self.sample.UB_get().get(1, 0))
        arr[1].append(self.sample.UB_get().get(1, 1))
        arr[1].append(self.sample.UB_get().get(1, 2))
        arr.append([])
        arr[2].append(self.sample.UB_get().get(2, 0))
        arr[2].append(self.sample.UB_get().get(2, 1))
        arr[2].append(self.sample.UB_get().get(2, 2))
        return arr

    def getUx(self):
        print " getUx"
        return self.sample.ux_get().value_unit_get()

    def setUx(self, value):
        print " setUx"
        self.sample.ux_get().value_unit_set(value, None)
        # This is required to make the change visible in the UB matrix
        U = self.sample.U_get()
        UB = self.sample.UB_get()
        self.sample.UB_set(UB)

    def getUy(self):
        print " getUy"
        return self.sample.uy_get().value_unit_get()

    def setUy(self, value):
        print " setUy"
        self.sample.uy_get().value_unit_set(value, None)
        # This is required to make the change visible in the UB matrix
        U = self.sample.U_get()
        UB = self.sample.UB_get()
        self.sample.UB_set(UB)

    def getUz(self):
        print " getUz"
        return self.sample.uz_get().value_unit_get()

    def setUz(self, value):
        print " setUz"
        self.sample.uz_get().value_unit_set(value, None)
        # This is required to make the change visible in the UB matrix
        U = self.sample.U_get()
        UB = self.sample.UB_get()
        self.sample.UB_set(UB)

    def setComputeU(self, value):
        print " setComputeU"
        if len(value) < 2:
            print "Two reflections are need"
            return
        nb_reflections = len(self.sample.reflections_get())
        if value[0] > nb_reflections or value[1] > nb_reflections:
            print "Reflections with the given indexes does not exit"
            return
        i = 0
        for ref in self.sample.reflections_get():
            if value[0] == i:
                ref1 = ref
            if value[1] == i:
                ref2 = ref
            i = i + 1
        self.sample.compute_UB_busing_levy(ref1, ref2)

    def getLatticeReciprocal(self):
        print " getLatticeReciprocal"
        lattice = self.sample.lattice_get()
        reciprocal = lattice.copy()
        lattice.reciprocal(reciprocal)
        lattice_parameters = []
        ic = 0
        for val in reciprocal.get():
            if (ic < 3):
                lattice_parameters.append(val)
            else:
                lattice_parameters.append(math.degrees(val))
            ic = ic + 1
        return lattice_parameters

    def getA(self):
        print " getA"
        apar = self.sample.lattice_get().a_get()
        return apar.value_unit_get()

    def setA(self, value):
        print " setA"
        lattice = self.sample.lattice_get()
        apar = lattice.a_get()
        apar.value_unit_set(value, None)
        self._a = value
        # For getting the UB matrix changing
        self.sample.lattice_set(lattice)

    def getB(self):
        print " getB"
        bpar = self.sample.lattice_get().b_get()
        return bpar.value_unit_get()

    def setB(self, value):
        print " setB"
        lattice = self.sample.lattice_get()
        bpar = lattice.b_get()
        bpar.value_unit_set(value, None)
        self._b = value
        # For getting the UB matrix changing
        self.sample.lattice_set(lattice)

    def getC(self):
        print " getC"
        cpar = self.sample.lattice_get().c_get()
        return cpar.value_unit_get()

    def setC(self, value):
        print " setC"
        lattice = self.sample.lattice_get()
        cpar = lattice.c_get()
        cpar.value_unit_set(value, None)
        self._c = value
        # For getting the UB matrix changing
        self.sample.lattice_set(lattice)

    def getAlpha(self):
        print " getAlpha"
        alphapar = self.sample.lattice_get().alpha_get()
        return alphapar.value_unit_get()

    def setAlpha(self, value):
        print " setAlpha"
        lattice = self.sample.lattice_get()
        alphapar = lattice.alpha_get()
        alphapar.value_unit_set(value, None)
        self._alpha = value
        # For getting the UB matrix changing
        self.sample.lattice_set(lattice)

    def getBeta(self):
        print " getBeta"
        betapar = self.sample.lattice_get().beta_get()
        return betapar.value_unit_get()

    def setBeta(self, value):
        print " setBeta"
        lattice = self.sample.lattice_get()
        betapar = lattice.beta_get()
        betapar.value_unit_set(value, None)
        self._beta = value
        # For getting the UB matrix changing
        self.sample.lattice_set(lattice)

    def getGamma(self):
        print " getGamma"
        gammapar = self.sample.lattice_get().gamma_get()
        return gammapar.value_unit_get()

    def setGamma(self, value):
        print " setGamma"
        lattice = self.sample.lattice_get()
        gammapar = lattice.gamma_get()
        gammapar.value_unit_set(value, None)
        self._gamma = value
        # For getting the UB matrix changing
        self.sample.lattice_set(lattice)

    def getAFit(self):
        print " getAFit"
        apar = self.sample.lattice_get().a_get()
        return apar.fit_get()

    def setAFit(self, value):
        print " setAFit"
        apar = self.sample.lattice_get().a_get()
        apar.fit_set(value)

    def getBFit(self):
        print " getBFit"
        bpar = self.sample.lattice_get().b_get()
        return bpar.fit_get()

    def setBFit(self, value):
        print " setBFit"
        bpar = self.sample.lattice_get().b_get()
        bpar.fit_set(value)

    def getCFit(self):
        print " getCFit"
        cpar = self.sample.lattice_get().c_get()
        return cpar.fit_get()

    def setCFit(self, value):
        print " setCFit"
        cpar = self.sample.lattice_get().c_get()
        cpar.fit_set(value)

    def getAlphaFit(self):
        print " getAlphaFit"
        alphapar = self.sample.lattice_get().alpha_get()
        return alphapar.fit_get()

    def setAlphaFit(self, value):
        print " setAlphaFit"
        alphapar = self.sample.lattice_get().alpha_get()
        alphapar.fit_set(value)

    def getBetaFit(self):
        print " getBetaFit"
        betapar = self.sample.lattice_get().beta_get()
        return betapar.fit_get()

    def setBetaFit(self, value):
        print " setBetaFit"
        betapar = self.sample.lattice_get().beta_get()
        betapar.fit_set(value)

    def getGammaFit(self):
        print " getGammaFit"
        gammapar = self.sample.lattice_get().gamma_get()
        return gammapar.fit_get()

    def setGammaFit(self, value):
        print " setGammaFit"
        gammapar = self.sample.lattice_get().gamma_get()
        gammapar.fit_set(value)

    def getComputeTrajectoriesSim(self):
        print " getcomputeTrajectoriesSim"
        return self.lastpseudopos

    def setComputeTrajectoriesSim(self, value):
        print " setcomputeTrajectoriesSim"
        if self.engine.name() == "hkl":
            if len(value) < 3:
                raise Exception(
                    "Not enough parameters given. Three are necessary: h, k, l ")
            else:
                try:
                    self.engine.set_values_unit(
                        [value[0], value[1], value[2]])  # compute the HklGeometry angles for this HklEngine
                except GLib.GError, err:
                    raise Exception("Not solution for current mode")
        elif self.engine.name() == "psi":
            try:
                self.engine.set_values_unit([value[0]])
            except GLib.GError, err:
                raise Exception("Not solution for current mode")
        elif self.engine.name() == "q":
            try:
                self.engine.set_values_unit([value[0]])
            except GLib.GError, err:
                raise Exception("Not solution for current mode")
        elif self.engine.name() == "eulerians":
            if len(value) < 3:
                raise Exception(
                    "Not enough parameters given. Three are necessary for eulerians mode")
            else:
                try:
                    self.engine.set_values_unit([value[0], value[1], value[2]])
                except GLib.GError, err:
                    raise Exception("Not solution for current mode")
        elif self.engine.name() == "q2":
            if len(value) < 2:
                raise Exception(
                    "Not enough parameters given. Three are necessary for q2 mode")
            else:
                try:
                    self.engine.set_values_unit([value[0], value[1]])
                except GLib.GError, err:
                    raise Exception("Not solution for current mode")
        elif self.engine.name() == "qper_qpar":
            if len(value) < 2:
                raise Exception(
                    "Not enough parameters given. Three are necessary for qper_qpar mode")
            else:
                try:
                    self.engine.set_values_unit([value[0], value[1]])
                except GLib.GError, err:
                    raise Exception("Not solution for current mode")

        self.trajectorylist = []
        for i, item in enumerate(self.engine.engines().geometries().items()):
            self.trajectorylist.append(item.geometry().get_axes_values_unit())

        for i in range(0, 3):
            self.lastpseudopos[i] = 0
        i = 0
        for myv in value:
            self.lastpseudopos[i] = myv
            i = i + 1
        print self.trajectorylist

    def getTrajectoryList(self):
        print " getTrajectoryList"
        return self.trajectorylist

    def getSelectedTrajectory(self):
        print " getSelectedTrajectory"
        return self.selected_trajectory

    def setSelectedTrajectory(self, value):
        print " setSelectedTrajectory"
        self.selected_trajectory = value

    def getEngine(self):
#        print " getEngine"
        return self.engine.name()

    def setEngine(self, value):
        print " setEngine"
        self.engine = self.engines.get_by_name(value)

    def getEngineList(self):
        print " getEngineList"
        engine_names = []
        for engine in self.engines.engines():
            engine_names.append(engine.name())
        return engine_names

    def setAddCrystal(self, value):
        print " setAddCrystal"
        if value not in self.crystallist:
            self.crystallist.append(value)
            self.samples_list[value] = Hkl.Sample.new(value)  # By default a crystal is created with lattice parameters 1.54, 1.54, 1.54, 90., 90., 90.
            self._addcrystal = value

    def getCrystalList(self):
        print " getCrsytalList"
        return self.crystallist

    def setDeleteCrystal(self, value):
        print " setDeleteCrystal"
        if value in self.crystallist:
            del self.samples_list[value]
            i = self.crystallist.index(value)
            del self.crystallist[i]
            self._deletecrystal = value

    def setAddReflection(self, value):
        print " setAddReflection"
        # Parameters: h, k, l, [affinement], angles are the current ones
        # Read current motor positions
        motor_position = []
        for i in range(0, self.nb_ph_axes):
            motor = self.GetMotor(i)
            motor_position.append(motor.position.value)
        self.geometry.set_axes_values_unit(motor_position)
        newref = self.sample.add_reflection(
            self.geometry, self.detector, value[0], value[1], value[2])
        # Set affinement if given (by default reflections are created with
        # affinement = 1)
        if len(value) > 3:
            newref.flag_set(value[3])

    def setAddReflectionWithIndex(self, value):
#        print " setAddReflectionWithIndex"
        # Parameters: index, h, k, l, [affinement], angles are the current ones
        # Read current reflections
        old_reflections = self.sample.reflections_get()
        nb_old_ref = len(old_reflections)
        hkla = []
        ihkla = 0
        angles = []
        for ref in old_reflections:
            hkla.append([])
            hkla[ihkla].append(ref.hkl_get()[0])
            hkla[ihkla].append(ref.hkl_get()[1])
            hkla[ihkla].append(ref.hkl_get()[2])            
            hkla[ihkla].append(ref.flag_get())
            angles.append([])
            angles[ihkla].append(ihkla)
            for angle in ref.geometry_get().get_axes_values_unit():
                angles[ihkla].append(angle)
            ihkla = ihkla + 1

        # Remove reflections with index bigger than the inserted one
        if value[0] < nb_old_ref:
            for j in range(int(value[0]), nb_old_ref):
                # The index are shifted so we have to remove always de first index
                self.setRemoveReflection(int(value[0]))


        # Check if the index is bigger than existing ones
        if value[0] < nb_old_ref:
            for i in range(0, nb_old_ref):
                if i < value[0]:
                    pass
                elif i == value[0]:
                    # add new reflection
                    self.setAddReflection(value[1:])
                elif i > value[0]:
                    self.setAddReflection(hkla[i])
                    self.setAdjustAnglesToReflection(angles[i])
            
        else: # add the new one
            self.setAddReflection(value[1:])

    def setSwapReflections01(self, value):
#        print " setSwapReflections01"
        # Read current reflections
        reflections = self.sample.reflections_get()
        nb_ref = len(reflections)
        
        if nb_ref < 2:
            print "Only " + str(nb_ref) + " reflection(s) defined. Swap not possible"
            return

        hkla = []
        ihkla = 0
        angles = []
        for ref in reflections:
            if ihkla < 2:
                hkla.append([])
                if ihkla == 1:
                    hkla[ihkla].append(0)
                else:
                    hkla[ihkla].append(1)
                hkla[ihkla].append(ref.hkl_get()[0])
                hkla[ihkla].append(ref.hkl_get()[1])
                hkla[ihkla].append(ref.hkl_get()[2])            
                hkla[ihkla].append(ref.flag_get())
                angles.append([])
                # swap the index
                if ihkla == 1:
                    angles[ihkla].append(0)
                else:
                    angles[ihkla].append(1)
                for angle in ref.geometry_get().get_axes_values_unit():
                    angles[ihkla].append(angle)
            ihkla = ihkla + 1

        # Remove reflection 0
        self.setRemoveReflection(0)

        # Insert old ref 1 to 0

        self.setAddReflectionWithIndex(hkla[1])
        self.setAdjustAnglesToReflection(angles[1])
        
        # Remove reflection 1

        self.setRemoveReflection(1)

        # Insert old ref 0 to 1

        self.setAddReflectionWithIndex(hkla[0])
        self.setAdjustAnglesToReflection(angles[0])


    def getReflectionList(self):
        print " getReflectionList"
        reflectionslist = []
        i = 0
        for ref in self.sample.reflections_get():
            reflectionslist.append([])
            reflectionslist[i].append(i)  # Reflection index
            reflectionslist[i].append(ref.hkl_get()[0])
            reflectionslist[i].append(ref.hkl_get()[1])
            reflectionslist[i].append(ref.hkl_get()[2])
            reflectionslist[i].append(0)  # Relevance
            reflectionslist[i].append(ref.flag_get())  # Affinement
            for value in ref.geometry_get().get_axes_values_unit():
                reflectionslist[i].append(value)
            i = i + 1
        return reflectionslist

    def setRemoveReflection(self, value):  # value: reflexion index
        print " setRemoveReflection"
        i = 0
        for ref in self.sample.reflections_get():
            if i == value:
                self.sample.del_reflection(ref)
            i = i + 1

    def setLoadReflections(self, value):  # value: complete path of the file with the reflections to set
        print " setLoadReflections"
        # Read the file
        try:
            reflections_file = open(value, 'r')
            self._loadreflections = value
        except:
            raise Exception("Not able to open reflections file")
        print reflections_file
        # Remove all reflections
        for ref in self.sample.reflections_get():
            self.sample.del_reflection(ref)
        # Read the reflections from the file
        for line in reflections_file:
            ref_values = []
            for value in line.split(' '):
                ref_values.append(
                    float(value))  # index 0 -> reflec. index; index 1,2, 3 hkl; 4 relevance; 5 affinement; last ones (2, 4 or 6) angles
            # Set hkl values to the reflection
            newref = self.sample.add_reflection(
                self.geometry, self.detector, ref_values[1], ref_values[2], ref_values[3])
            # Set affinement
            newref.flag_set(ref_values[5])
            # Adjust angles
            new_angles = []
            for i in range(6, len(ref_values)):
                new_angles.append(ref_values[i])
            geometry = newref.geometry_get()
            geometry.set_axes_values_unit(new_angles)
            newref.geometry_set(geometry)

    def setLoadCrystal(self, value):  # value: complete path of the file with the crystal to set
        print " setLoadCrystal"
        # Read the file
        try:
            crystal_file = open(value, 'r')
            self._loadcrystal = value
        except:
            raise Exception("Not able to open crystal file")

        line_nb = 0
        nb_ref = 0

        #print crystal_file

        for line in crystal_file:
            if line_nb == 0:
                # Add crystal if not in the list
                crystal = line[0:len(line)-1]
                self.setAddCrystal(crystal)
                # Set crystal
                self.sample = self.samples_list[crystal]
                # Remove all reflections from crystal (there should not be any ... but just in case)
                for ref in self.sample.reflections_get():
                    self.sample.del_reflection(ref)
            elif line_nb == 1:
                wavelength = float(line) # The value will be set after creating the new geometry with the reflections
                self.geometry.wavelength_set(wavelength)
            elif line_nb == 2:
                # Set parameters
                par_values = []
                for value in line.split(' '):
                    par_values.append(float(value))
                
                lattice = self.sample.lattice_get()
                apar = lattice.a_get()
                apar.value_unit_set(par_values[0], None)
                self._a = par_values[0]
                bpar = lattice.b_get()
                bpar.value_unit_set(par_values[1], None)
                self._b = par_values[1]
                cpar = lattice.c_get()
                cpar.value_unit_set(par_values[2], None)
                self._c = par_values[2]
                alphapar = lattice.alpha_get()
                alphapar.value_unit_set(par_values[3], None)
                self._alpha = par_values[3]
                betapar = lattice.beta_get()
                betapar.value_unit_set(par_values[4], None)
                self._beta = par_values[4]
                gammapar = lattice.gamma_get()
                gammapar.value_unit_set(par_values[5], None)
                self._gamma = par_values[5]
                # For getting the UB matrix changing
                self.sample.lattice_set(lattice)
            else:
                # Set reflections
                ref_values = []
                for value in line.split(' '):
                    ref_values.append(
                        float(value))  # index 0 -> reflec. index; index 1,2, 3 hkl; 4 relevance; 5 affinement; last ones (2, 4 or 6) angles
                # Set hkl values to the reflection
                newref = self.sample.add_reflection(
                    self.geometry, self.detector, ref_values[1], ref_values[2], ref_values[3])
                # Set affinement
                newref.flag_set(ref_values[5])
                # Adjust angles
                new_angles = []
                for i in range(6, len(ref_values)):
                    new_angles.append(ref_values[i])
                geometry = newref.geometry_get()
                geometry.set_axes_values_unit(new_angles)
                newref.geometry_set(geometry)
                nb_ref = nb_ref + 1
                       
            line_nb = line_nb + 1
        
        if nb_ref > 1:
            values = [0,1]
            self.setComputeU(values)
        

    def setSaveReflections(self, value):  # value: directory, the file would be given by the name of the sample
        print "setSaveReflections"
        complete_file_name = value + str(self.sample.name_get()) + ".ref"
        complete_file_name = complete_file_name.replace(' ', '')
        complete_file_name = complete_file_name.replace('(', '_')
        complete_file_name = complete_file_name.replace(')', '_')
        try:
            open(complete_file_name)
            new_file_name = complete_file_name + "_" + str(time.time())
            cmd = "mv " + str(complete_file_name) + " " + str(new_file_name)
            os.system(cmd)
        except:
            pass
        ref_file = open(complete_file_name, 'w')
        reflections = self.getReflectionList()
        for ref in reflections:
            ref_str = ""
            for val in ref:
                ref_str = ref_str + str(val) + " "
            ref_str = ref_str[:-1]
            ref_str = ref_str + '\n'
            ref_file.write(ref_str)
        ref_file.close()

    def setSaveCrystal(self, value):  # value: directory + filename
        print "setSaveCrystal"
        complete_file_name = value
        self._savecrystal = complete_file_name
        try:
            open(complete_file_name)
            new_file_name = complete_file_name + "_" + str(time.time())
            cmd = "mv " + str(complete_file_name) + " " + str(new_file_name)
            os.system(cmd)
        except:
            pass
        crys_file = open(complete_file_name, 'w')

        # write crystal name
        
        crystal_name = self.sample.name_get()
        crys_str = crystal_name + "\n"
        crys_file.write(crys_str)

        # write wavelength
        
        wavelength = self.geometry.wavelength_get()
        wl_str = str(wavelength) + "\n"
        crys_file.write(wl_str)
        

        # write lattice parameters
        apar = self.sample.lattice_get().a_get()
        a = apar.value_unit_get()
        bpar = self.sample.lattice_get().b_get()
        b = bpar.value_unit_get()
        cpar = self.sample.lattice_get().c_get()
        c = cpar.value_unit_get()
        alphapar = self.sample.lattice_get().alpha_get()
        alpha = alphapar.value_unit_get()
        betapar = self.sample.lattice_get().beta_get()
        beta = betapar.value_unit_get()
        gammapar = self.sample.lattice_get().gamma_get()
        gamma = gammapar.value_unit_get()
        par_str = str(a) + " " + str(b) + " " + str(c) + " " + str(alpha) + " " + str(beta) + " " + str(gamma) + "\n"
        crys_file.write(par_str)

        # write reflections
        reflections = self.getReflectionList()
        for ref in reflections:
            ref_str = ""
            for val in ref:
                ref_str = ref_str + str(val) + " "
            ref_str = ref_str[:-1]
            ref_str = ref_str + '\n'
            crys_file.write(ref_str)

        crys_file.close()

    def setAdjustAnglesToReflection(self, value):  # value: reflexion index + new angles
        print " setAdjustAnglesToReflection"
        ref_index = value[0]
        new_angles = []
        for i in range(1, len(value)):
            new_angles.append(value[i])
        i = 0
        for ref in self.sample.reflections_get():
            if i == ref_index:
                geometry = ref.geometry_get()
                geometry.set_axes_values_unit(new_angles)
                ref.geometry_set(geometry)
            i = i + 1

    def getReflectionAngles(self):
        print " getReflectionAngles"
        reflectionsangles = []
        i = -1
        for ref1 in self.sample.reflections_get():
            i = i + 1
            j = -1
            reflectionsangles.append([])
            for ref2 in self.sample.reflections_get():
                j = j + 1
                angle = 0
                if i < j:
                    angle = self.sample.get_reflection_mesured_angle(
                        ref1, ref2)
                elif j < i:
                    angle = self.sample.get_reflection_theoretical_angle(
                        ref1, ref2)
                reflectionsangles[i].append(angle)
        return reflectionsangles

    def getModeParametersNames(self):
        parameters_names = []
        current_mode = self.engine.mode()
        parameters = current_mode.parameters()
        for parameter in parameters.parameters():
            parameters_names.append(parameter.name_get())
        return parameters_names

    def getModeParametersValues(self):
        parameters_values = []
        current_mode = self.engine.mode()
        parameters = current_mode.parameters()
        for parameter in parameters.parameters():
            parameters_values.append(parameter.value_unit_get())
        return parameters_values

    def setModeParametersValues(self, value):
        parameters_values = []
        current_mode = self.engine.mode()
        parameters = current_mode.parameters()
        i = 0
        for parameter in parameters.parameters():
            if i < len(value):
                parameter.value_unit_set(value[i], None)
            i = i + 1

    def getPsiRefH(self):
        value = -999
        current_mode = self.engine.mode()
        parameters = current_mode.parameters()
        for parameter in parameters.parameters():
            if parameter.name_get() in ["h1","h2","x"]:
                value = parameter.value_unit_get()
        return value

    def setPsiRefH(self, value):
        current_mode = self.engine.mode()
        parameters = current_mode.parameters()
        for parameter in parameters.parameters():
            if parameter.name_get() in ["h1","h2","x"]:
                parameter.value_unit_set(value, None)

    def getPsiRefK(self):
        value = -999
        current_mode = self.engine.mode()
        parameters = current_mode.parameters()
        for parameter in parameters.parameters():
            if parameter.name_get() in ["k1","k2","y"]:
                value = parameter.value_unit_get()
        return value

    def setPsiRefK(self, value):
        current_mode = self.engine.mode()
        parameters = current_mode.parameters()
        for parameter in parameters.parameters():
            if parameter.name_get() in ["k1","k2","y"]:
                parameter.value_unit_set(value, None)

    def getPsiRefL(self):
        value = -999
        current_mode = self.engine.mode()
        parameters = current_mode.parameters()
        for parameter in parameters.parameters():
            if parameter.name_get() in ["l1","l2","z"]:
                value = parameter.value_unit_get()
        return value

    def setPsiRefL(self, value):
        current_mode = self.engine.mode()
        parameters = current_mode.parameters()
        for parameter in parameters.parameters():
            if parameter.name_get() in ["l1","l2","z"]:
                parameter.value_unit_set(value, None)

    def getMotorList(self):
        motor_names = []
        for i in range(0, self.nb_ph_axes):
            motor = self.GetMotor(i)
            mot_info = motor.name + "  (" + motor.full_name + ")"
            motor_names.append(mot_info)
        return motor_names

    def getHKLPseudoMotorList(self):
        hkl_pm_names = []
        for i in range(0, 3):
            motor = self.GetPseudoMotor(i)
            mot_info = motor.name + "  (" + motor.full_name + ")"
            hkl_pm_names.append(mot_info)
        return hkl_pm_names

# 6C Diffractometers ####################


class Diffrac6C(DiffracBasis):  # DiffractometerType: "PETRA3 P09 EH2"

    """ The PseudoMotor controller for the diffractometer"""

    pseudo_motor_roles = "h", "k", "l"
    motor_roles = "mu", "th", "chi", "phi", "gamma", "delta"

    def __init__(self, inst, props, *args, **kwargs):
        """ Do the default init plus the specific diffractometer
        staff.
        @param properties of the controller
        """

        DiffracBasis.__init__(self, inst, props, *args, **kwargs)


class DiffracE6C(DiffracBasis):  # DiffractometerType: "E6C", "SOLEIL SIXS MED2+2"

    """ The PseudoMotor controller for the diffractometer"""

    pseudo_motor_roles = "h", "k", "l", "psi", "q21", "q22", "qperqpar1", "qperpar2"
    motor_roles = "mu", "th", "chi", "phi", "gamma", "delta"

    def __init__(self, inst, props, *args, **kwargs):
        """ Do the default init plus the specific diffractometer
        staff.
        @param properties of the controller
        """

        DiffracBasis.__init__(self, inst, props, *args, **kwargs)


class DiffracK6C(DiffracBasis):  # DiffractometerType: "K6C"

    """ The PseudoMotor controller for the diffractometer"""

    pseudo_motor_roles = "h", "k", "l", "psi", "q21", "q22", "qperqpar1", "qperpar2", "eulerians1", "eulerians2", "eulerians3"
    motor_roles = "mu", "th", "chi", "phi", "gamma", "delta"

    def __init__(self, inst, props, *args, **kwargs):
        """ Do the default init plus the specific diffractometer
        staff.
        @param properties of the controller
        """

        DiffracBasis.__init__(self, inst, props, *args, **kwargs)

# 4C Diffractometers ####################


class Diffrac4C(DiffracBasis):

    """ The PseudoMotor controller for the diffractometer"""

    pseudo_motor_roles = "h", "k", "l"
    motor_roles = "omega", "chi", "phi", "tth"

    def __init__(self, inst, props, *args, **kwargs):
        """ Do the default init plus the specific diffractometer
        staff.
        @param properties of the controller
        """

        DiffracBasis.__init__(self, inst, props, *args, **kwargs)


class DiffracE4C(DiffracBasis):  # DiffractometerType: "E4CV", "E4CH", "SOLEIL MARS"

    """ The PseudoMotor controller for the diffractometer"""

    pseudo_motor_roles = "h", "k", "l", "psi", "q"
    motor_roles = "omega", "chi", "phi", "tth"

    def __init__(self, inst, props, *args, **kwargs):
        """ Do the default init plus the specific diffractometer
        staff.
        @param properties of the controller
        """

        DiffracBasis.__init__(self, inst, props, *args, **kwargs)


class DiffracK4C(DiffracBasis):  # DiffractometerType: "K4CV"

    """ The PseudoMotor controller for the diffractometer"""

    pseudo_motor_roles = "h", "k", "l", "psi", "q", "eulerians1", "eulerians2", "eulerians3"
    motor_roles = "omega", "chi", "phi", "tth"

    def __init__(self, inst, props, *args, **kwargs):
        """ Do the default init plus the specific diffractometer
        staff.
        @param properties of the controller
        """

        DiffracBasis.__init__(self, inst, props, *args, **kwargs)


class Diffrac4CZAXIS(DiffracBasis):  # DiffractometerType: "ZAXIS", "SOLEIL SIXS MED1+2"

    """ The PseudoMotor controller for the diffractometer"""

    pseudo_motor_roles = "h", "k", "l", "q21", "q22", "qperqpar1", "qperqpar2"
    motor_roles = "omega", "chi", "phi", "tth"

    def __init__(self, inst, props, *args, **kwargs):
        """ Do the default init plus the specific diffractometer
        staff.
        @param properties of the controller
        """

        DiffracBasis.__init__(self, inst, props, *args, **kwargs)


# 2C Diffractometers ####################


class Diffrac2C(DiffracBasis):

    """ The PseudoMotor controller for the diffractometer"""

    pseudo_motor_roles = "h", "k", "l"
    motor_roles = "omega", "tth"

    def __init__(self, inst, props, *args, **kwargs):
        """ Do the default init plus the specific diffractometer
        staff.
        @param properties of the controller
        """

        DiffracBasis.__init__(self, inst, props, *args, **kwargs)
