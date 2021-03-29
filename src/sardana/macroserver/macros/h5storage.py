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

"""HDF5 storage macros"""
import os
import contextlib

from sardana.sardanautils import is_non_str_seq
from sardana.macroserver.macro import macro, Type, Optional
from sardana.macroserver.msexception import UnknownEnv
from sardana.macroserver.recorders.h5storage import NXscanH5_FileRecorder
from sardana.macroserver.recorders.h5util import _h5_file_handler


def _get_h5_scan_files(macro):
    scan_dir = macro._getEnv("ScanDir")
    scan_files = macro._getEnv("ScanFile")
    if not is_non_str_seq(scan_files):
        scan_files = [scan_files]
    h5_scan_files = []
    for scan_file in scan_files:
        file_name, file_ext = os.path.splitext(scan_file)
        if file_ext not in NXscanH5_FileRecorder.formats.values():
            continue
        h5_scan_files.append(os.path.join(scan_dir, scan_file))
    return h5_scan_files


def _h5_start_session(macro, path=None, swmr_mode=None):
    if path is None:
        paths = _get_h5_scan_files(macro)
    else:
        paths = [path]
    if swmr_mode is None:
        try:
            swmr_mode = macro._getEnv("ScanH5SWMR")
        except UnknownEnv:
            swmr_mode = False
    for file_path in paths:
        fd = _h5_file_handler.open_file(file_path, swmr_mode)
        macro.print("H5 session open for '{}'".format(file_path))
        macro.print("\t SWMR mode: {}".format(swmr_mode))
        macro.print("\t HDF5 version compatibility: {}".format(fd.libver))


@macro([["swmr_mode", Type.Boolean, Optional, "Enable SWMR mode"]])
def h5_start_session(self, swmr_mode):
    """Start write session for HDF5 scan file(s)

    Open HDF5 scan files in write mode and keep them for the needs of
    recorders until the session is closed by ``h5_end_session``.

    The session file path is obtained by inspecting ScanDir and ScanFile
    environment variables. If you want to use a different file path, use
    ``h5_start_session_path``

    Optionally, enable SWMR mode (either with ``swmr_mode`` parameter or
    with ``ScanH5SWMR`` environment variable)
    """
    sessions = _h5_file_handler.files
    if sessions:
        self.print("Session(s) already started. Can be ended with: ")
        for p in sessions:
            self.print("\th5_end_session_path " + p )
        self.print("")
    _h5_start_session(self, None, swmr_mode)


@macro([["path", Type.String, None,
         "File name for which the session should be started"],
        ["swmr_mode", Type.Boolean, Optional, "Enable SWMR mode"]])
def h5_start_session_path(self, path, swmr_mode):
    """Start write session for HDF5 file path

    Open HDF5 files in write mode and keep them for the needs of
    recorders until the session is closed by ``h5_end_session``.

    Optionally, enable SWMR mode (either with ``swmr_mode`` parameter or
    with ``ScanH5SWMR`` environment variable)
    """
    sessions = _h5_file_handler.files
    if sessions:
        self.print("Session(s) already started. Can be ended with: ")
        for p in sessions:
            self.print("\th5_end_session_path " + p)
        self.print("")
    _h5_start_session(self, path, swmr_mode)


def _h5_end_session(macro, path=None):
    if path is None:
        paths = _get_h5_scan_files(macro)
    else:
        paths = [path]
    for file_path in paths:
        _h5_file_handler.close_file(file_path)


@macro()
def h5_end_session(self):
    """End write session for HDF5 scan file(s)

    Close previously opened HDF5 scan files with the use ``h5_start_session``
    or ``h5_start_session_path``.

    The session file path is obtained by inspecting ScanDir and ScanFile
    environment variables. If you want to close a different file path, use
    ``h5_end_session_path``
    """
    _h5_end_session(self, path=None)


@macro([["path", Type.String, Optional,
         "File name for which the session should be ended"]])
def h5_end_session_path(self, path):
    """End write session for HDF5 file path

    Close previously opened HDF5 scan files with the use ``h5_start_session``
    or ``h5_start_session_path``.
    """
    _h5_end_session(self, path)


@macro()
def h5_ls_session(self):
    """List scan files opened for write session with ``h5_start_session``
    """
    for file_path in _h5_file_handler.files:
        self.print(file_path)


@contextlib.contextmanager
def h5_write_session(macro, path=None, swmr_mode=False):
    """Context manager for HDF5 file write session.

    Maintains HDF5 file opened for the context lifetime.
    Optionally, open the file as SWMR writer.

    Resolve configured H5 scan file names by inspecting ScanDir and ScanFile
    environment variables.

    Example of macro executing multiple scans within the same write session::

        @macro()
        def experiment(self):
            with h5_write_session(macro=self, swmr_mode=True):
                for i in range(10)
                    self.execMacro("ascan", "mot01", 0, 10, 10, 0.1)

    :param macro: macro object
    :type macro: `~sardana.macroserver.macro.Macro`
    :param path: file path (or None to use ScanDir and ScanFile)
    :type path: str
    :param swmr_mode: Use SWMR write mode
    :type swmr_mode: bool
    """
    _h5_start_session(macro, path, swmr_mode)
    try:
        yield None
    finally:
        _h5_end_session(macro, path)





