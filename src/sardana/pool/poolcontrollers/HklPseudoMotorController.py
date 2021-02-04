# -*- coding: utf-8 -*-

##############################################################################
#
# This file is part of Sardana
#
# http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
#
# Copyright: 2013 PetraIII,
#            2013 Synchrotron-Soleil
#                 L'Orme des Merisiers Saint-Aubin
#                 BP 48 91192 GIF-sur-YVETTE CEDEX
#
# Sardana is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sardana is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
#
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

__all__ = ["Diffrac6C", "DiffracE6C", "DiffracE4C", "Diffractometer"]

__docformat__ = 'restructuredtext'

import os
import time

import PyTango

from itertools import chain

from gi.repository import GLib
from gi.repository import Hkl

from taurus.core.util.codecs import CodecFactory

from sardana import DataAccess
from sardana.pool.controller import PseudoMotorController
from sardana.pool.controller import Type, Access, Description
from sardana.pool.controller import Memorize, Memorized, MemorizedNoInit, NotMemorized  # noqa

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite
USER = Hkl.UnitEnum.USER
DEFAULT_CRYSTAL = "default_crystal"


from taurus.core.util.log import Logger

logger = Logger.getLogger("ControllerManager")

logger.info("The diffractometer controller is at early stage. Controller attributes and commands can slightly change.")


class AxisPar(object):

    def __init__(self, engine, name):
        self.engine = engine
        self.name = name
        self._modes = None

    @property
    def mode(self):
        return self.engine.current_mode_get()

    @mode.setter
    def mode(self, value):
        self.engine.current_mode_set(value)

    @property
    def modes(self):
        if self._modes is None:
            self._modes = self.engine.modes_names_get()
        return self._modes

    @property
    def modeparameters(self):
        return self.engine.parameters_names_get()

    @property
    def modeparametersvalues(self):
        return [p.value_get(USER)
                for p in [self.engine.parameter_get(n)
                          for n in self.modeparameters]]

    @modeparametersvalues.setter
    def modeparametersvalues(self, value):
        for parameter, v in zip(self.modeparameters,
                                value):
            p = self.engine.parameter_get(parameter)
            p.value_set(v, USER)
            self.engine.parameter_set(parameter, p)

# TODO: all the fit attributes (AFit or GammaFit)should change its type to bool


class DiffracBasis(PseudoMotorController):

    """ The PseudoMotor controller for the diffractometer"""

    ctrl_properties = {
        'DiffractometerType': {
            Type: str,
            Description: 'Type of the diffractometer, e.g. E6C'},
    }

    ctrl_attributes = {'Crystal': {Type: str,
                                   Memorize: MemorizedNoInit,  # noqa If Crystal is changed to memorized. The changes commented with "memcrystal"
                                   Access: ReadWrite},
                       'AffineCrystal': {Type: int,
                                         Memorize: MemorizedNoInit,
                                         Description: "Fine tunning of lattice parameters and UB matrix based on current crystal reflections. Reflections with affinement set to 0 are not used. A new crystal with the post fix (affine) is created and set as current crystal",  # noqa
                                         Access: ReadWrite},
                       'Wavelength': {Type: float,
                                      Memorize: MemorizedNoInit,
                                      Access: ReadWrite},
                       'EngineMode': {Type: str,  # TODO delete
                                      Memorize: MemorizedNoInit,
                                      Access: ReadWrite},
                       'EngineModeList': {Type: (str,), Access: ReadOnly},
                       # TODO delete
                       'HKLModeList': {Type: (str,), Access: ReadOnly},
                       'UBMatrix': {Type: ((float,), ),
                                    Description: "The reflection matrix",
                                    Access: ReadOnly},
                       'Ux': {Type: float, Access: ReadWrite},
                       'Uy': {Type: float, Access: ReadWrite},
                       'Uz': {Type: float, Access: ReadWrite},
                       'ComputeUB': {Type: (int,),
                                    Description: "Compute reflection matrix using two given reflections",  # noqa
                                    Access: ReadWrite},
                       'LatticeReciprocal': {Type: (float,),
                                             Description: "The reciprocal lattice parameters of the sample",  # noqa
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
                                Description: "Fit value of the a parameter of the lattice",  # noqa
                                Memorize: MemorizedNoInit,
                                Access: ReadWrite},
                       'BFit': {Type: int,
                                Description: "Fit value of the b parameter of the lattice",  # noqa
                                Memorize: MemorizedNoInit,
                                Access: ReadWrite},
                       'CFit': {Type: int,
                                Description: "Fit value of the c parameter of the lattice",  # noqa
                                Memorize: MemorizedNoInit,
                                Access: ReadWrite},
                       'AlphaFit': {Type: int,
                                    Description: "Fit value of the alpha parameter of the lattice",  # noqa
                                    Memorize: MemorizedNoInit,
                                    Access: ReadWrite},
                       'BetaFit': {Type: int,
                                   Description: "Fit value of the beta parameter of the lattice",  # noqa
                                   Memorize: MemorizedNoInit,
                                   Access: ReadWrite},
                       'GammaFit': {Type: int,
                                    Description: "Fit value of the gamma parameter of the lattice",  # noqa
                                    Memorize: MemorizedNoInit,
                                    Access: ReadWrite},
                       'TrajectoryList': {Type: ((float,), (float,)),
                                          Description: "List of trajectories for hklSim",  # noqa
                                          Access: ReadOnly},
                       'SelectedTrajectory': {Type: int,
                                              Description: "Index of the trajectory you want to take for the given hkl values. 0 (by default) if first.",  # noqa
                                              Access: ReadWrite},
                       'ComputeTrajectoriesSim': {Type: (float,),
                                                  Description: "Pseudo motor values to compute the list of trajectories (1, 2 or 3 args)",  # noqa
                                                  Access: ReadWrite},
                       'Engine': {Type: str,
                                  Memorize: MemorizedNoInit,
                                  Access: ReadWrite},
                       'EngineList': {Type: (str,), Access: ReadOnly},
                       'EnginesConf': {Type: str, Access: ReadOnly},
                       'CrystalList': {Type: (str,), Access: ReadOnly},
                       'AddCrystal': {Type: str,
                                      Memorize: MemorizedNoInit,
                                      Access: ReadWrite},
                       'DeleteCrystal': {Type: str,
                                         Memorize: MemorizedNoInit,
                                         Access: ReadWrite},
                       'AddReflection': {Type: (float,),
                                         Description: "Add reflection to current sample",  # noqa
                                         Access: ReadWrite},
                       'SubstituteReflection': {Type: (float,),
                                                  Description: "Substitute reflexion with the given index by the given one",  # noqa
                                                  Access: ReadWrite},
                       'SwapReflections01': {Type: int,
                                             Description: "Swap primary and secondary reflections",  # noqa
                                             Access: ReadWrite},
                       'ReflectionList': {Type: ((float,), (float,)),
                                          Description: "List of reflections for current sample",  # noqa
                                          Access: ReadOnly},
                       'RemoveReflection': {Type: int,
                                            Memorize: MemorizedNoInit,
                                            Description: "Remove reflection with given index",  # noqa
                                            Access: ReadWrite},
                       'LoadReflections': {Type: str,
                                           Description: "Load the reflections from the file given as argument",  # noqa
                                           Memorize: MemorizedNoInit,
                                           Access: ReadWrite},
                       'SaveReflections': {Type: str,
                                           Description: "Save current reflections to file",  # noqa
                                           Memorize: MemorizedNoInit,
                                           Access: ReadWrite},
                       'LoadCrystal':     {Type: str,
                                           Description: "Load the lattice parameters and reflections from the file corresponding to the given crystal",  # noqa
                                           Memorize: MemorizedNoInit,
                                           Access: ReadWrite},
                       'SaveCrystal': {Type: int,
                                       Description: "Save current crystal parameters and reflections",  # noqa
                                       Memorize: NotMemorized,
                                       Access: ReadWrite},
                       'SaveDirectory': {Type: str,
                                         Description: "Directory to save the crystal files to",  # noqa
                                         Memorize: Memorized,
                                         Access: ReadWrite},
                       'AdjustAnglesToReflection': {Type: (float,),
                                                    Description: "Set the given angles to the reflection with given index",  # noqa
                                                    Access: ReadWrite},
                       'ReflectionAngles': {Type: ((float,), (float,)),
                                            Description: "Angles between reflections",  # noqa
                                            Access: ReadOnly},
                       'ModeParametersNames': {Type: (str,),  # TODO delete
                                               Description: "Name of the parameters of the current mode (if any)",  # noqa
                                               Access: ReadOnly},
                       'ModeParametersValues': {Type: (float,),  # TODO delete
                                                Description: "Value of the parameters of the current mode (if any)",  # noqa
                                                Access: ReadWrite},
                       'PsiRefH': {Type: float,
                                   Description: "x coordinate of the psi reference vector (-999 if not applicable)",  # noqa
                                   Memorize: MemorizedNoInit,
                                   Access: ReadWrite},
                       'PsiRefK': {Type: float,
                                   Description: "y coordinate of the psi reference vector (-999 if not applicable)",  # noqa
                                   Memorize: MemorizedNoInit,
                                   Access: ReadWrite},
                       'PsiRefL': {Type: float,
                                   Description: "z coordinate of the psi reference vector (-999 if not applicable)",  # noqa
                                   Memorize: MemorizedNoInit,
                                   Access: ReadWrite},
                       'MotorList': {Type: (str,),
                                     Description: "Name of the real motors",
                                     Access: ReadOnly},
                       'HKLPseudoMotorList': {Type: (str,),
                                              Description: "Name of the hkl pseudo motors",  # noqa
                                              Access: ReadOnly},
                       'MotorRoles': {Type: (str,),
                                          Description: "Name of the motor roles",  # noqa
                                          Access: ReadOnly},
                       'EnergyDevice': {Type: str,
                                        Description: "Name of the energy device to read the energy from",
                                        Memorize: Memorized,
                                        Access: ReadWrite},
                       'AutoEnergyUpdate': {Type: int,
                                            Description: "If 1 wavelength is read from EnergyDevice",
                                            Memorize: Memorized,
                                            Access: ReadWrite},
                       'ComputeHKL': {Type: (float,),
                                            Description: "Compute hkl for given angles",
                                            Memorize: NotMemorized,
                                            Access: ReadWrite},
    }

    axis_attributes = {
        'Mode': {
            Type: str,
            Memorize: MemorizedNoInit,
            Access: ReadWrite
        },
        'Modes': {
            Type: (str,),
            Access: ReadOnly
        },
        'ModeParameters': {
            Type: (str,),
            Description: "Name of the parameters of the current mode (if any)",  # noqa
            Access: ReadOnly
        },
        'ModeParametersValues': {
            Type: (float,),
            Description: "Value of the parameters of the current mode (if any)",  # noqa
            Access: ReadWrite
        },
    }

    def GetAxisExtraPar(self, axis, name):
        return getattr(self.axispar[axis - 1], name.lower())

    def SetAxisExtraPar(self, axis, name, value):
        setattr(self.axispar[axis - 1], name.lower(), value)

    MaxDevice = 1

    def __init__(self, inst, props, *args, **kwargs):
        """ Do the default init plus the specific diffractometer
        staff.
        @param properties of the controller
        """
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)

        # Comment out if memorized crystal (memcrystal)
        # self.first_crystal_set = 1
        self.samples = {}
        self.samples[DEFAULT_CRYSTAL] = self.sample = Hkl.Sample.new(DEFAULT_CRYSTAL)  # noqa

        lattice = self.sample.lattice_get()
        self._a = self._b = self._c = 1.5
        self._alpha = self._beta = self._gamma = 90.
        lattice.set(self._a, self._b, self._c,
                    self._alpha, self._beta, self._gamma, USER)
        self.sample.lattice_set(lattice)

        self.detector = Hkl.Detector.factory_new(Hkl.DetectorType(0))

        for key, factory in Hkl.factories().items():
            if key == self.DiffractometerType:
                self.geometry = factory.create_new_geometry()
                self.engines = factory.create_new_engine_list()

        self.nb_ph_axes = len(self.geometry.axis_names_get())

        self.engines.init(self.geometry, self.detector, self.sample)

        # Engine hkl -> it has not effect, it will be set the last value set
        # (stored in DB)
        self.engine = self.engines.engine_get_by_name("hkl")

        self.engine_list = []
        self.axispar = []
        for engine in self.engines.engines_get():
            self.engine_list.append(engine.name_get())
            for pseudo in engine.pseudo_axis_names_get():
                self.axispar.append(AxisPar(engine, pseudo))

        self.engine_list = tuple(self.engine_list)
        self.engines_conf = None  # defered because it does not work in the __init__

        self.trajectorylist = []

        # simulation part
        self.lastpseudopos = [0] * 3
        self.selected_trajectory = 0

        # Put to -1 the attributes that are actually commands
        self._affinecrystal = -1
        self._removereflection = -1
        self._deletecrystal = 'nothing'
        self._addcrystal = 'nothing'
        self._addreflection = [-1.]
        self._substitutereflection = [-1.]
        self._swapreflections01 = -1
        self._loadreflections = " "  # Only to create the member, the
        # value will be overwritten by
        # the one in stored in the
        # database
        self._savereflections = " "  # Only to create the member, the
        # value will be overwritten by
        # the one in stored in the
        # database
        self._loadcrystal = " "  # Only to create the member, the
        # value will be overwritten by the
        # one in stored in the database
        self._savecrystal = -1
        self._savedirectory = " "  # Only to create the member, the
        # value will be overwritten by the
        # one in stored in the database
        self._energydevice = " "  # Only to create the member, the
        # value will be overwritten by the
        # one in stored in the database
        self._autoenergyupdate = 0  # Only to create the member, the
        # value will be overwritten by the
        # one in stored in the database
        self._computehkl = []

        self.energy_device = None
        self.lambda_to_e = 12398.424  # Amstrong * eV

    def _solutions(self, values, curr_physical_position):
        # set all the motor min and max to restrain the solutions
        # with only valid positions.
        for role, current in zip(self.motor_roles, curr_physical_position):
            motor = self.GetMotor(role)
            axis = self.geometry.axis_get(role)
            axis.value_set(current, USER)
            try:
                config = PyTango.AttributeProxy(motor.get_full_name() + '/position').get_config()  # noqa
                mini, maxi = float(config.min_value), float(config.max_value)
                axis.min_max_set(mini, maxi, USER)
            except ValueError:
                pass
            self.geometry.axis_set(role, axis)

        # computation and select the expected solution
        return self.engine.pseudo_axis_values_set(values, USER)

    def CalcPhysical(self, axis, pseudo_pos, curr_physical_pos):
        return self.CalcAllPhysical(pseudo_pos, curr_physical_pos)[axis - 1]

    def CalcPseudo(self, axis, physical_pos, curr_pseudo_pos):
        return self.CalcAllPseudo(physical_pos, curr_pseudo_pos)[axis - 1]

    def CalcAllPhysical(self, pseudo_pos, curr_physical_pos):
        # TODO it should work with all the kind of engine ? or only
        # with the hkl engine ? What I understand from this is that
        # the pseudos values contain all the values from all the
        # engines. This is not generic at all. If I add new engines
        # this code should be fixed. worse the engine names is
        # hardcoded. for now I will just rewrite the code with the
        # same logic but with the new hkl API.

        engine_name = self.engine.name_get()
        values = None
        if engine_name == "hkl":
            values = [pseudo_pos[0], pseudo_pos[1], pseudo_pos[2]]
        elif self.nb_ph_axes == 4:  # noqa "E4CV", "E4CH", "SOLEIL MARS": hkl(3), psi(1), q(1); "K4CV": hkl(3), psi(1), q(1), eulerians(3); "SOLEIL SIXS MED1+2": hkl(3), q2(2), qper_qpar(2); "PETRA3 P23 4C": hkl(3), q2(2), qper_qpar(2), tth2(2), petra3_p23_4c_incidence(1), _petra3_p23_4c_emergence(1)
            if engine_name == "psi":
                values = [pseudo_pos[3]]
            elif engine_name == "q":
                values = [pseudo_pos[4]]
            elif engine_name == "eulerians":
                values = [pseudo_pos[5], pseudo_pos[6], pseudo_pos[7]]
            elif engine_name == "q2":
                values = [pseudo_pos[3], pseudo_pos[4]]
            elif engine_name == "qper_qpar":
                values = [pseudo_pos[5], pseudo_pos[6]]
            elif engine_name == "tth2":
                values = [pseudo_pos[7], pseudo_pos[8]]
            elif engine_name == "petra3_p23_4c_incidence":
                values = [pseudo_pos[9]]
            elif engine_name == "petra3_p23_4c_emergence":
                values = [pseudo_pos[10]]
        elif self.nb_ph_axes == 6:  # noqa "E6C", "SOLEIL SIXS MED2+2": hkl(3), psi(1), q2(2), qper_qpar(2); "K6C":  hkl(3), psi(1), q2(2), qper_qpar(2), eulerians(3); "PETRA3 P09 EH2": hkl(3), "PETRA3 P23 6C": hkl(3), psi(1), q2(2), qper_qpar(2), tth2(2), petra3_p23_6c_incidence(1), _petra3_p23_6c_emergence(1)
            if engine_name == "psi":
                values = [pseudo_pos[3]]
            elif engine_name == "q2":
                values = [pseudo_pos[4], pseudo_pos[5]]
            elif engine_name == "qper_qpar":
                values = [pseudo_pos[6], pseudo_pos[7]]
            elif engine_name == "eulerians":
                values = [pseudo_pos[8], pseudo_pos[9], pseudo_pos[10]]
            elif engine_name == "tth2":
                values = [pseudo_pos[8], pseudo_pos[9]]
            elif engine_name == "petra3_p23_6c_incidence":
                values = [pseudo_pos[10]]
            elif engine_name == "petra3_p23_6c_emergence":
                values = [pseudo_pos[11]]

        # getWavelength updates wavelength in the library in case automatic
        # energy update is set. Needed before computing trajectories.

        self.getWavelength()

        solutions = self._solutions(values, curr_physical_pos)
        if self.selected_trajectory > len(list(solutions.items())):
            self.selected_trajectory = len(list(solutions.items())) - 1
        for i, item in enumerate(solutions.items()):
            if i == self.selected_trajectory:
                angles = item.geometry_get().axis_values_get(USER)

        # TODO why replace this by a tuple ?
        return tuple(angles)

    def CalcAllPseudo(self, physical_pos, curr_pseudo_pos):
        # TODO howto avoid this nb_ph_axes, does the length of the
        # physical values are not equal to the expected len of the
        # geometry axes.

        # getWavelength updates wavelength in the library in case automatic
        # energy update is set. Needed before computing trajectories.

        self.getWavelength()

        # write the physical motor into the geometry
        self.geometry.axis_values_set(physical_pos[:self.nb_ph_axes], USER)
        self.engines.get()

        # extract all the pseudo axes values
        values = []
        for engine in self.engines.engines_get():
            values = values + engine.pseudo_axis_values_get(USER)

        return tuple(values)

    def getCrystal(self):
        return self.sample.name_get()

    def setCrystal(self, value):
        self.sample = self.samples[value]
        # Used this part and comment the above one out if memorized crystal (memcrystal)
        # if self.first_crystal_set == 0:
        #    if value in self.samples:
        #        self.sample = self.samples[value]
        # else:
        #    self.samples[value] = Hkl.Sample.new(
        #        value)  # By default a crystal is created with lattice parameters 1.54, 1.54, 1.54, 90., 90., 90.
        #    self.sample = self.samples[value]
        #    lattice = self.sample.lattice_get()
        #    lattice.set(self._a, self._b, self._c, self._alpha, self._beta, self._gamma, USER)
        #    self.sample.lattice_set(lattice)
        #    # For getting the UB matrix changing
        #    self.sample.lattice_set(lattice)

        #   self.first_crystal_set = 0
        self.engines.init(self.geometry, self.detector, self.sample)

    def setAffineCrystal(self, value):
        new_sample_name = self.sample.name_get() + " (affine)"
        if new_sample_name not in self.samples:
            sample = self.sample.copy()
            sample.name_set(new_sample_name)
            sample.affine()
            self.sample = self.samples[new_sample_name] = sample

    def getWavelength(self):
        if self._energydevice != " " and self._autoenergyupdate:
            try:
                if self.energy_device is None:
                    self.energy_device = PyTango.DeviceProxy(
                        self._energydevice)
                energy = self.energy_device.Position
                wavelength = self.lambda_to_e / energy
                self.setWavelength(wavelength)
            except:
                self._log.warning("Not able to get energy from energy device")
        return self.geometry.wavelength_get(USER)

    def setWavelength(self, value):
        self.geometry.wavelength_set(value, USER)

    def getEngineMode(self):
        return self.engine.current_mode_get()

    def setEngineMode(self, value):
        # TODO why not throw the exception when the mode name is
        # wrong. The hkl library return an usefull Exception for this.
        for mode in self.engine.modes_names_get():
            if value == mode:
                self.engine.current_mode_set(mode)

    def getEngineModeList(self):
        return self.engine.modes_names_get()

    def getHKLModeList(self):
        # TODO seems to me complicate... why this Hkl specific part.
        # It seems that this controleur mix all the engines and does
        # something special with the hkl one ???   neverthless I would
        # be possible to create a self.engines instead of recomputing
        # it all the time.
        for key, factory in Hkl.factories().items():
            if key == self.DiffractometerType:
                new_engines = factory.create_new_engine_list()
        new_engines.init(self.geometry, self.detector, self.sample)
        hkl_engine = new_engines.engine_get_by_name("hkl")
        return hkl_engine.modes_names_get()

    def getUBMatrix(self):
        UB = self.sample.UB_get()
        return [[UB.get(i, j) for j in range(3)] for i in range(3)]

    def getUx(self):
        return self.sample.ux_get().value_get(USER)

    def setUx(self, value):
        ux = self.sample.ux_get()
        ux.value_set(value, USER)
        self.sample.ux_set(ux)

    def getUy(self):
        return self.sample.uy_get().value_get(USER)

    def setUy(self, value):
        uy = self.sample.uy_get()
        uy.value_set(value, USER)
        self.sample.uy_set(uy)

    def getUz(self):
        return self.sample.uz_get().value_get(USER)

    def setUz(self, value):
        uz = self.sample.uz_get()
        uz.value_set(value, USER)
        self.sample.uz_set(uz)

    def setComputeUB(self, value):
        if len(value) < 2:
            return
        nb_reflections = len(self.sample.reflections_get())
        if value[0] >= nb_reflections or value[1] >= nb_reflections:
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
        lattice = self.sample.lattice_get()
        reciprocal = lattice.copy()
        lattice.reciprocal(reciprocal)
        return reciprocal.get(USER)

    def getA(self):
        lattice = self.sample.lattice_get()
        a, _b, _c, _alpha, _beta, _gamma = lattice.get(USER)
        return a

    def setA(self, value):
        lattice = self.sample.lattice_get()
        a, b, c, alpha, beta, gamma = lattice.get(USER)
        lattice.set(value, b, c, alpha, beta, gamma, USER)
        self.sample.lattice_set(lattice)
        self._a = value

    def getB(self):
        lattice = self.sample.lattice_get()
        _a, b, _c, _alpha, _beta, _gamma = lattice.get(USER)
        return b

    def setB(self, value):
        lattice = self.sample.lattice_get()
        a, b, c, alpha, beta, gamma = lattice.get(USER)
        lattice.set(a, value, c, alpha, beta, gamma, USER)
        self.sample.lattice_set(lattice)
        self._b = value

    def getC(self):
        lattice = self.sample.lattice_get()
        _a, _b, c, _alpha, _beta, _gamma = lattice.get(USER)
        return c

    def setC(self, value):
        lattice = self.sample.lattice_get()
        a, b, c, alpha, beta, gamma = lattice.get(USER)
        lattice.set(a, b, value, alpha, beta, gamma, USER)
        self.sample.lattice_set(lattice)
        self._c = value

    def getAlpha(self):
        lattice = self.sample.lattice_get()
        _a, _b, _c, alpha, _beta, _gamma = lattice.get(USER)
        return alpha

    def setAlpha(self, value):
        lattice = self.sample.lattice_get()
        a, b, c, alpha, beta, gamma = lattice.get(USER)
        lattice.set(a, b, c, value, beta, gamma, USER)
        self.sample.lattice_set(lattice)
        self._alpha = value

    def getBeta(self):
        lattice = self.sample.lattice_get()
        _a, _b, _c, _alpha, beta, _gamma = lattice.get(USER)
        return beta

    def setBeta(self, value):
        lattice = self.sample.lattice_get()
        a, b, c, alpha, beta, gamma = lattice.get(USER)
        lattice.set(a, b, c, alpha, value, gamma, USER)
        self.sample.lattice_set(lattice)
        self._beta = value

    def getGamma(self):
        lattice = self.sample.lattice_get()
        _a, _b, _c, _alpha, _beta, gamma = lattice.get(USER)
        return gamma

    def setGamma(self, value):
        lattice = self.sample.lattice_get()
        a, b, c, alpha, beta, gamma = lattice.get(USER)
        lattice.set(a, b, c, alpha, beta, value, USER)
        self.sample.lattice_set(lattice)
        self._gamma = value

    def getAFit(self):
        apar = self.sample.lattice_get().a_get()
        return apar.fit_get()

    def setAFit(self, value):
        apar = self.sample.lattice_get().a_get()
        apar.fit_set(value)

    def getBFit(self):
        bpar = self.sample.lattice_get().b_get()
        return bpar.fit_get()

    def setBFit(self, value):
        bpar = self.sample.lattice_get().b_get()
        bpar.fit_set(value)

    def getCFit(self):
        cpar = self.sample.lattice_get().c_get()
        return cpar.fit_get()

    def setCFit(self, value):
        cpar = self.sample.lattice_get().c_get()
        cpar.fit_set(value)

    def getAlphaFit(self):
        alphapar = self.sample.lattice_get().alpha_get()
        return alphapar.fit_get()

    def setAlphaFit(self, value):
        alphapar = self.sample.lattice_get().alpha_get()
        alphapar.fit_set(value)

    def getBetaFit(self):
        betapar = self.sample.lattice_get().beta_get()
        return betapar.fit_get()

    def setBetaFit(self, value):
        betapar = self.sample.lattice_get().beta_get()
        betapar.fit_set(value)

    def getGammaFit(self):
        gammapar = self.sample.lattice_get().gamma_get()
        return gammapar.fit_get()

    def setGammaFit(self, value):
        gammapar = self.sample.lattice_get().gamma_get()
        gammapar.fit_set(value)

    def getComputeTrajectoriesSim(self):
        return self.lastpseudopos

    def setComputeTrajectoriesSim(self, values):
        # TODO the hkl library should return these informations
        # assert (len(values) == len(self.engine.pseudo_axis_names_get()),
        #         "Not the right number of parameters given (%d, %d expected)"
        #         " for the \"%s\" engine" %
        #         (len(values),
        #          len(self.engine.pseudo_axis_names_get()),
        #          self.engine.name_get())
        # getWavelength updates wavelength in the library in case automatic
        # energy update is set. Needed before computing trajectories.

        self.getWavelength()

        # Read current motor positions
        motor_position = []
        for i in range(0, self.nb_ph_axes):
            motor = self.GetMotor(i)
            motor_position.append(motor.get_position(cache=False).value)
        self.geometry.axis_values_set(motor_position, USER)

        curr_physical_pos = self.geometry.axis_values_get(USER)
        solutions = self._solutions(values, curr_physical_pos)
        self.trajectorylist = [item.geometry_get().axis_values_get(USER)
                               for item in list(solutions.items())]
        self.lastpseudos = tuple(values)

    def getTrajectoryList(self):
        return self.trajectorylist

    def getSelectedTrajectory(self):
        return self.selected_trajectory

    def setSelectedTrajectory(self, value):
        self.selected_trajectory = value

    def getEngine(self):
        return self.engine.name_get()

    def setEngine(self, value):
        self.engine = self.engines.engine_get_by_name(value)

    def getEngineList(self):
        return self.engine_list

    def getEnginesConf(self):
        if self.engines_conf is None:
            elements = []
            for engine in self.engines.engines_get():
                name = engine.name_get()
                motors = tuple([self.GetPseudoMotor(pseudo)
                                for pseudo in engine.pseudo_axis_names_get()])
                elements.append((name, motors))
            json_codec = CodecFactory().getCodec(format)
            f, conf = json_codec.encode(('', tuple(elements)))[1]
            self.engines_conf = conf

    def setAddCrystal(self, value):
        if value not in self.samples:
            self.samples[value] = Hkl.Sample.new(value)
            # value returned when the attribute is read
            self._addcrystal = value

    def getCrystalList(self):
        return list(self.samples)

    def setDeleteCrystal(self, value):
        if value in self.samples:
            self.samples.pop(value)
            # value returned when the attribute is read
            self._deletecrystal = value

    def setAddReflection(self, value):
        # Parameters: h, k, l, [affinement], angles are the current ones
        # Read current motor positions
        motor_position = []
        for i in range(0, self.nb_ph_axes):
            motor = self.GetMotor(i)
            motor_position.append(motor.get_position(cache=False).value)
        self.geometry.axis_values_set(motor_position, USER)
        newref = self.sample.add_reflection(
            self.geometry, self.detector, value[0], value[1], value[2])
        # Set affinement if given (by default reflections are created with
        # affinement = 1)
        if len(value) > 3:
            newref.flag_set(value[3])

    def setSubstituteReflection(self, value):
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
            for angle in ref.geometry_get().axis_values_get(USER):
                angles[ihkla].append(angle)
            ihkla = ihkla + 1

        # Remove reflections with index bigger than the inserted one
        if value[0] < nb_old_ref:
            for j in range(int(value[0]), nb_old_ref):
                # The index are shifted so we have to remove always de
                # first index
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
        else:  # add the new one
            self.setAddReflection(value[1:])

    def setSwapReflections01(self, value):
        # Read current reflections
        reflections = self.sample.reflections_get()
        nb_ref = len(reflections)

        if nb_ref < 2:
            self._log.warning(
                "Only %d reflection(s) defined. Swap not possible" % (nb_ref,))
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
                for angle in ref.geometry_get().axis_values_get(USER):
                    angles[ihkla].append(angle)
            ihkla = ihkla + 1

        # Remove reflection 0
        self.setRemoveReflection(0)

        # Insert old ref 1 to 0

        self.setSubstituteReflection(hkla[1])
        self.setAdjustAnglesToReflection(angles[1])

        # Remove reflection 1

        self.setRemoveReflection(1)

        # Insert old ref 0 to 1

        self.setSubstituteReflection(hkla[0])
        self.setAdjustAnglesToReflection(angles[0])

    def getReflectionList(self):
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
            for value in ref.geometry_get().axis_values_get(USER):
                reflectionslist[i].append(value)
            i = i + 1
        return reflectionslist

    def setRemoveReflection(self, value):  # value: reflexion index
        i = 0
        for ref in self.sample.reflections_get():
            if i == value:
                self.sample.del_reflection(ref)
            i = i + 1

    # value: complete path of the file with the reflections to set
    def setLoadReflections(self, value):
        # Read the file
        with open(value, 'r') as f:
            self._loadreflections = value

            # Remove all reflections
            for reflection in self.sample.reflections_get():
                self.sample.del_reflection(reflection)

            # add one reflection per line (no check for now)
            # TODO it seems that the wavelength is missing in the file.
            for line in f:
                # the reflection line is structured like this
                # index 0 -> reflec. index;
                # index 1, 2, 3 -> hkl;
                # index 4 -> relevance
                # index 5 -> affinement;
                # last ones (2, 4 or 6) -> geometry axes values
                values = [float(v) for v in line.split(' ')]

                # create the reflection
                reflection = self.sample.add_reflection(self.geometry, self.detector,
                                                        values[1], values[2], values[3])
                # set the affinement
                reflection.flag_set(values[5])

                # set the axes values
                geometry = reflection.geometry_get()
                geometry.axis_values_set(values[6:], USER)
                reflection.geometry_set(geometry)

    def setLoadCrystal(self, value):
        """Load crystal information from a file. Ignore wavelength information.

        :param value: complete path of the file with the crystal to set
        :type value: :obj:`str`
        """
        # Read the file
        with open(value, 'r') as crystal_file:
            self._loadcrystal = value

            nb_ref = 0

            for line in crystal_file:
                line = line.replace("\n", "")
                if line.find("Crystal") != -1:
                    # Add crystal
                    line = line.replace(" ", "")
                    crystal = line.split("Crystal", 1)[1]
                    self.setAddCrystal(crystal)
                    # Set crystal
                    self.sample = self.samples[crystal]
                    self.engines.init(
                        self.geometry, self.detector, self.sample)
                    # Remove all reflections from crystal (there should not be
                    # any ... but just in case)
                    for ref in self.sample.reflections_get():
                        self.sample.del_reflection(ref)
                elif line.find("A") != -1 and line.find("B") != -1 and line.find("C") != -1:
                    par_line = line.split(" ")
                    avalue = float(par_line[1])
                    bvalue = float(par_line[3])
                    cvalue = float(par_line[5])
                    lattice = self.sample.lattice_get()
                    a, b, c, alpha, beta, gamma = lattice.get(USER)
                    lattice.set(avalue, bvalue, cvalue,
                                alpha, beta, gamma, USER)
                    # For getting the UB matrix changing
                    self.sample.lattice_set(lattice)
                    self._a = avalue
                    self._b = bvalue
                    self._c = cvalue
                elif line.find("Alpha") != -1 and line.find("Beta") != -1 and line.find("Gamma") != -1:
                    par_line = line.split(" ")
                    alphavalue = float(par_line[1])
                    betavalue = float(par_line[3])
                    gammavalue = float(par_line[5])
                    lattice = self.sample.lattice_get()
                    a, b, c, alpha, beta, gamma = lattice.get(USER)
                    lattice.set(a, b, c, alphavalue,
                                betavalue, gammavalue, USER)
                    # For getting the UB matrix changing
                    self.sample.lattice_set(lattice)
                    self._alpha = alphavalue
                    self._beta = betavalue
                    self._gamma = gammavalue
                elif line.find("Engine") != -1:
                    line = line.split(" ")
                    engine = line[1]
                    self.setEngine(engine)
                elif line.find("Mode") != -1:
                    line = line.split(" ")
                    mode = line[1]
                    self.setEngineMode(mode)
                elif line.find("PsiRef") != -1:
                    if line.find("PsiRef not available") == -1:
                        psiref_line = line.split(" ")
                        psirefh = float(psiref_line[1])
                        psirefk = float(psiref_line[2])
                        psirefl = float(psiref_line[3])
                        try:
                            self.setPsiRefH(psirefh)
                        except:
                            self._log.warning(
                                "PsiRefH not set. Psi not available in current mode")
                        try:
                            self.setPsiRefK(psirefk)
                        except:
                            self._log.warning(
                                "PsiRefK not set. Psi not available in current mode")
                        try:
                            self.setPsiRefL(psirefl)
                        except:
                            self._log.warning(
                                "PsiRefL not set. Psi not available in current mode")
                elif line.find("R0") != -1 or line.find("R1") != -1:
                    if line.find("R0") != -1:
                        line = line.split("R0 ")[1]
                    else:
                        line = line.split("R1 ")[1]
                    # Set reflections
                    ref_values = []
                    for value in line.split(' '):
                        try:
                            # index 0 -> reflec. index; index 1,2, 3 hkl; 4
                            # relevance; 5 affinement; last ones (2, 4 or 6)
                            # angles
                            ref_values.append(float(value))
                        except:
                            pass
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
                    geometry.axis_values_set(new_angles, USER)
                    newref.geometry_set(geometry)
                    nb_ref = nb_ref + 1
                elif line.find("SaveDirectory") != -1:
                    line = line.split(" ")
                    if self._savedirectory == " " or self._savedirectory == "":
                        self._savedirectory = line[1]
                elif line.find("AutoEnergyUpdate") != -1:
                    line = line.split(" ")
                    self._autoenergyupdate = int(line[1])

        if nb_ref > 1:
            values = [0, 1]
            self.setComputeUB(values)

    # value: directory, the file would be given by the name of the sample
    def setSaveReflections(self, value):
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
        with open(complete_file_name, 'w') as ref_file:
            reflections = self.getReflectionList()
            for ref in reflections:
                ref_str = ""
                for val in ref:
                    ref_str = ref_str + str(val) + " "
                ref_str = ref_str[:-1]
                ref_str = ref_str + '\n'
                ref_file.write(ref_str)

    def setSaveCrystal(self, value):  # value: not used
        default_file_name = self._savedirectory + "/defaultcrystal.txt"
        crystal_file_name = self._savedirectory + "/" + self.sample.name_get() + ".txt"

        with open(default_file_name, 'w') as crys_file:
            # date

            date_str = "Created at " + time.strftime("%Y-%m-%d %H:%M") + "\n\n"
            crys_file.write(date_str)

            # diffractometer type

            difftype_str = ("DiffractometerType " + self.DiffractometerType +
                            "\n\n")
            crys_file.write(difftype_str)

            # write crystal name

            crystal_name = self.sample.name_get()
            crys_str = "Crystal    " + crystal_name + "\n\n"
            crys_file.write(crys_str)

            # write wavelength

            wavelength = self.geometry.wavelength_get(USER)
            wl_str = "Wavelength " + str(wavelength) + "\n\n"
            crys_file.write(wl_str)

            # write lattice parameters
            apar = self.sample.lattice_get().a_get()
            a = apar.value_get(USER)
            bpar = self.sample.lattice_get().b_get()
            b = bpar.value_get(USER)
            cpar = self.sample.lattice_get().c_get()
            c = cpar.value_get(USER)
            alphapar = self.sample.lattice_get().alpha_get()
            alpha = alphapar.value_get(USER)
            betapar = self.sample.lattice_get().beta_get()
            beta = betapar.value_get(USER)
            gammapar = self.sample.lattice_get().gamma_get()
            gamma = gammapar.value_get(USER)
            par_str = "A " + str(a) + " B " + str(b) + " C " + str(c) + "\n"
            crys_file.write(par_str)
            par_str = "Alpha " + str(alpha) + " Beta " + \
                str(beta) + " Gamma " + str(gamma) + "\n\n"
            crys_file.write(par_str)

            # write reflections
            reflections = self.getReflectionList()
            ref_in = 0
            for ref in reflections:
                ref_str = ""
                for val in ref:
                    ref_str = ref_str + str(val) + " "
                ref_str = ref_str[:-1]
                ref_str = "R" + str(ref_in) + " " + ref_str + '\n'
                if ref_in < 2:
                    crys_file.write(ref_str)
                ref_in = ref_in + 1
            if ref_in == 0:
                ref_str = "No reflections\n"
                crys_file.write(ref_str)
            crys_file.write("\n")

            # write engine
            engine_str = "Engine " + self.engine.name_get() + "\n\n"
            crys_file.write(engine_str)

            # write mode
            mode_str = "Mode " + self.engine.current_mode_get() + "\n\n"
            crys_file.write(mode_str)

            # write psiref (if available in mode)

            psirefh = self.getPsiRefH()
            psirefk = self.getPsiRefK()
            psirefl = self.getPsiRefL()
            if psirefh != -999 or psirefk != -999 or psirefl != -999:
                psi_str = "PsiRef " + \
                    str(psirefh) + " " + str(psirefk) + \
                    " " + str(psirefl) + "\n\n"
            else:
                psi_str = "PsiRef not available in current engine mode\n\n"

            crys_file.write(psi_str)

            # write autoenergyupdate value

            autoenergyupdate_str = "AutoEnergyUpdate " + \
                str(self._autoenergyupdate) + "\n\n"
            crys_file.write(autoenergyupdate_str)

            # Only for info in the file but not for loading:

            # write ub matrix
            for i in range(0, 3):
                ub_str = ""
                for j in range(0, 3):
                    #ub_str = ub_str + "U" + str(i) + str(j) + " " + str(self.sample.UB_get().get(i, j)) + " "
                    ub_str = ub_str + "U" + \
                        str(i) + str(j) + \
                        " %.3f" % self.sample.UB_get().get(i, j) + " "
                ub_str = ub_str + "\n"
                crys_file.write(ub_str)
            crys_file.write("\n")

            # write u vector
            u_str = "Ux " + str(self.sample.ux_get().value_get(USER)) + " Uy " + str(self.sample.uy_get(
            ).value_get(USER)) + " Uz " + str(self.sample.uz_get().value_get(USER)) + "\n\n"
            crys_file.write(u_str)

            # write directory where the file is saved

            dir_str = "SaveDirectory " + self._savedirectory + "\n"
            crys_file.write(dir_str)

        cmd = "cp " + str(default_file_name) + " " + str(crystal_file_name)
        os.system(cmd)

    def setSaveDirectory(self, value):
        self._savedirectory = value

    # value: reflexion index + new angles
    def setAdjustAnglesToReflection(self, value):
        ref_index = value[0]
        new_angles = value[1:]
        i = 0
        for ref in self.sample.reflections_get():
            if i == ref_index:
                geometry = ref.geometry_get()
                geometry.axis_values_set(new_angles, USER)
                ref.geometry_set(geometry)
            i = i + 1

    def getReflectionAngles(self):
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
                    angle = self.sample.get_reflection_measured_angle(
                        ref1, ref2)
                elif j < i:
                    angle = self.sample.get_reflection_theoretical_angle(
                        ref1, ref2)
                reflectionsangles[i].append(angle)
        return reflectionsangles

    def getModeParametersNames(self):
        return self.engine.parameters_names_get()

    def getModeParametersValues(self):
        return [p.value_get(USER)
                for p in [self.engine.parameter_get(n)
                          for n in self.engine.parameters_names_get()]]

    def setModeParametersValues(self, value):
        for parameter, v in zip(self.engine.parameters_names_get(), value):
            p = self.engine.parameter_get(parameter)
            p.value_set(v, USER)
            self.engine.parameter_set(parameter, p)

    def _getPsiRef(self, parameters):
        # TODO I do not understand this method. check that the
        # parameters names are ok. I changed one.
        value = -999
        for parameter in self.engine.parameters_names_get():
            if parameter in parameters:
                value = self.engine.parameter_get(parameter).value_get(USER)
        return value

    def getPsiRefH(self):
        return self._getPsiRef(["h1", "h2", "x"])

    def getPsiRefK(self):
        return self._getPsiRef(["k1", "k2", "y"])

    def getPsiRefL(self):
        return self._getPsiRef(["l1", "l2", "z"])

    def _setPsiRef(self, parameters, value):
        # TODO idem here :)
        value_set = False
        for parameter in self.engine.parameters_names_get():
            if parameter in parameters:
                p = self.engine.parameter_get(parameter)
                p.value_set(value, USER)
                self.engine.parameter_set(parameter, p)
                value_set = True
        if not value_set:
            raise Exception("psiref not available in this mode")

    def setPsiRefH(self, value):
        self._setPsiRef(["h1", "h2", "x"], value)

    def setPsiRefK(self, value):
        self._setPsiRef(["k1", "k2", "y"], value)

    def setPsiRefL(self, value):
        self._setPsiRef(["l1", "l2", "z"], value)

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

    def getMotorRoles(self):
        roles_names = tuple(self.geometry.axis_names_get())
        return roles_names

    def setEnergyDevice(self, value):
        self._energydevice = value
        try:
            self.energy_device = PyTango.DeviceProxy(self._energydevice)
        except:
            self.energy_device = None
            self._log.warning("Not able to create proxy to energydevice")

    def setAutoEnergyUpdate(self, value):
        self._autoenergyupdate = value

    def setComputeHKL(self, value):

        # getWavelength updates wavelength in the library in case automatic
        # energy update is set. Needed before computing trajectories.

        self.getWavelength()

        # write the physical motor into the geometry
        if len(value) >= self.nb_ph_axes:
            self.geometry.axis_values_set(value[:self.nb_ph_axes], USER)
            self.engines.get()
        else:
            raise Exception("Not enough arguments. %d are need " %
                            (self.nb_ph_axes))

        # extract hkl  values
        values = []
        engine = self.engines.engine_get_by_name("hkl")
        values = engine.pseudo_axis_values_get(USER)

        self._computehkl = values


# 6C Diffractometers ####################


class Diffrac6Cp23(DiffracBasis):  # DiffractometerType: "PETRA3 P23 6C"

    """ The PseudoMotor controller for the diffractometer"""

    pseudo_motor_roles = "h", "k", "l", "psi", "q", "alpha", "tth2",
    "alpha_tth2", "incidence", "emergence"
    motor_roles = "omega_t", "mu", "omega", "chi", "phi", "gamma", "delta"

    def __init__(self, inst, props, *args, **kwargs):
        """ Do the default init plus the specific diffractometer
        staff.
        @param properties of the controller
        """

        DiffracBasis.__init__(self, inst, props, *args, **kwargs)

class Diffrac6C(DiffracBasis):  # DiffractometerType: "PETRA3 P09 EH2"

    """ The PseudoMotor controller for the diffractometer"""

    pseudo_motor_roles = "h", "k", "l"
    motor_roles = "mu", "omega", "chi", "phi", "delta", "gamma"

    def __init__(self, inst, props, *args, **kwargs):
        """ Do the default init plus the specific diffractometer
        staff.
        @param properties of the controller
        """

        DiffracBasis.__init__(self, inst, props, *args, **kwargs)


class DiffracE6C(DiffracBasis):

    """ The PseudoMotor controller for the diffractometer"""

    pseudo_motor_roles = "h", "k", "l", "psi", "q", "alpha", "qper", "qpar"
    motor_roles = "mu", "omega", "chi", "phi", "gamma", "delta"

    def __init__(self, inst, props, *args, **kwargs):
        """ Do the default init plus the specific diffractometer
        staff.
        @param properties of the controller
        """

        DiffracBasis.__init__(self, inst, props, *args, **kwargs)

# 4C Diffractometers ####################


class Diffrac4Cp23(DiffracBasis):  # DiffractometerType: "PETRA3 P23 4C"

    """ The PseudoMotor controller for the diffractometer"""

    pseudo_motor_roles = "h", "k", "l", "q", "alpha", "qper", "qpar",
    "tth2", "alpha_tth2", "incidence", "emergence"
    motor_roles = "omega_t", "mu", "gamma", "delta"

    def __init__(self, inst, props, *args, **kwargs):
        """ Do the default init plus the specific diffractometer
        staff.
        @param properties of the controller
        """

        DiffracBasis.__init__(self, inst, props, *args, **kwargs)

class DiffracE4C(DiffracBasis):

    """ The PseudoMotor controller for the diffractometer"""

    pseudo_motor_roles = "h", "k", "l", "psi", "q"
    motor_roles = "omega", "chi", "phi", "tth"

    def __init__(self, inst, props, *args, **kwargs):
        """ Do the default init plus the specific diffractometer
        staff.
        @param properties of the controller
        """

        DiffracBasis.__init__(self, inst, props, *args, **kwargs)


# wip Generic diffractometer

class Diffractometer(DiffracBasis):
    """ The PseudoMotor controller for the diffractometer"""

    def __init__(self, inst, props, *args, **kwargs):
        """ Do the default init plus the specific diffractometer
        staff.
        @param properties of the controller
        """
        DiffracBasis.__init__(self, inst, props, *args, **kwargs)

        factory = Hkl.factories()[self.DiffractometerType]
        self.geometry = factory.create_new_geometry()
        self.engines = factory.create_new_engine_list()

        # dynamically set the roles using the hkl library
        Diffractometer.motor_roles = tuple(self.geometry.axis_names_get())
        Diffractometer.pseudo_motor_roles = tuple(
            chain.from_iterable(
                [engine.pseudo_axis_names_get()
                 for engine in self.engines.engines_get()]))
