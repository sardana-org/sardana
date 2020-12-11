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

""""""

__all__ = ["which_python_executable"]


from taurus.core.util.whichexecutable import whichfile


def which_python_executable():
    """Return full path to python executable.

    On some OS Python 3 is executed with python3 but in conda environments it
    is executed with python. Return Python 3 executable regardless of the
    Python installation.
    """
    executable = whichfile("python3")
    if executable is None:
        executable = whichfile("python")
    return executable
