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

"""
This module provides a recorder for NXscans implemented with h5py (no nxs)
"""

import os
import h5py
import atexit


def _open_h5_file(fname, libver='earliest'):
    mode = 'w-'
    if os.path.exists(fname):
        mode = 'r+'
    fd = h5py.File(fname, mode=mode, libver=libver)
    return fd


class _H5FileHandler:

    def __init__(self):
        self._files = {}

    def __getitem__(self, fname):
        return self._files[fname]

    @property
    def files(self):
        return self._files.keys()

    def open_file(self, fname, swmr_mode=False):
        if swmr_mode:
            try:
                fd = _open_h5_file(fname, libver='latest')
                fd.swmr_mode = True
            except ValueError as e:
                raise ValueError(
                    "Cannot open '{}' in swmr mode".format(fname)
                ) from e
        else:
            fd = _open_h5_file(fname)
        if not self._files:
            atexit.register(self.clean_up)
        self._files[fname] = fd
        return fd

    def close_file(self, fname):
        try:
            fd = self._files.pop(fname)
        except KeyError:
            raise ValueError('{} is not opened'.format(fname))
        if not self._files:
            atexit.unregister(self.clean_up)
        fd.close()

    def clean_up(self):
        for file in self.files:
            self.close_file(file)


_h5_file_handler = _H5FileHandler()
