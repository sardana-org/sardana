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

"""This is the macro server scan data output recorder module"""

__all__ = ["BaseSharedMemoryRecorder", "SharedMemoryRecorder"]

__docformat__ = 'restructuredtext'

from sardana.macroserver.scan.recorder.datarecorder import DataRecorder


class BaseSharedMemoryRecorder(DataRecorder):

    def __init__(self, **pars):
        DataRecorder.__init__(self, **pars)

_SharedMemoryRecorder = BaseSharedMemoryRecorder  # for backwards compatibility


def SharedMemoryRecorder(type, macro, **pars):
    """Factory to create shared memory recorders based on the type
    """
    rec_manager = macro.getMacroServer().recorder_manager
    if type == 'sps':
        klass = rec_manager.getRecorderClass('SPSRecorder')
    else:
        raise Exception('SharedMemory %s is not supported.' % type)
    return klass(**pars)
