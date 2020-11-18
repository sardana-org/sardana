##############################################################################
##
# This file is part of Sardana
##
# http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
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

from sardana import State
from sardana.util.funcgenerator import FunctionGenerator
from sardana.pool.controller import TriggerGateController
from sardana.sardanathreadpool import get_thread_pool
from sardana.pool.pooldefs import SynchDomain


class DummyTriggerGateController(TriggerGateController):
    """Basic controller intended for demonstration purposes only.
    """
    gender = "Simulation"
    organization = "ALBA-Cells"
    MaxDevice = 1

    def __init__(self, inst, props, *args, **kwargs):
        """Constructor"""
        TriggerGateController.__init__(self, inst, props, *args, **kwargs)
        self.tg = {}
        self.conf = {}

    def SynchOne(self, axis, conf):
        idx = axis - 1
        tg = self.tg[idx]
        tg.set_configuration(conf)
        self.conf[idx] = conf

    def AddDevice(self, axis):
        self._log.debug('AddDevice(%d): entering...' % axis)
        idx = axis - 1
        func_generator = FunctionGenerator()
        func_generator.initial_domain = SynchDomain.Time
        func_generator.active_domain = SynchDomain.Time
        self.tg[idx] = func_generator

    def StateOne(self, axis):
        """Get the dummy trigger/gate state"""
        try:
            self._log.debug('StateOne(%d): entering...' % axis)
            sta = State.On
            status = "Stopped"
            idx = axis - 1
            tg = self.tg[idx]
            if tg.is_running() or tg.is_started():
                sta = State.Moving
                status = "Moving"
            self._log.debug('StateOne(%d): returning (%s, %s)' %
                            (axis, sta, status))
        except Exception as e:
            print(e)
        return sta, status

    def PrepareOne(self, axis, nb_starts):
        self._log.debug('PrepareOne(%d): entering...' % axis)

    def PreStartAll(self):
        pass

    def StartAll(self):
        pass

    def PreStartOne(self, axis, value=None):
        return True

    def StartOne(self, axis):
        """Start the specified trigger
        """
        self._log.debug('StartOne(%d): entering...' % axis)
        idx = axis - 1
        tg = self.tg[idx]
        tg.start()
        get_thread_pool().add(tg.run)

    def AbortOne(self, axis):
        """Start the specified trigger
        """
        self._log.debug('AbortOne(%d): entering...' % axis)
        idx = axis - 1
        self.tg[idx].stop()
