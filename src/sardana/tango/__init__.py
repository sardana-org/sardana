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

""" """

__docformat__ = 'restructuredtext'

SERVER_NAME = "Sardana"


def prepare_sardana(util):
    import pool
    import macroserver
    pool.prepare_pool(util)
    macroserver.prepare_macroserver(util)


def main_sardana(args=None, start_time=None, mode=None):
    import core.util
    # pass server name so the scripts generated with setuptools work on Windows
    return core.util.run(prepare_sardana, args=args, start_time=start_time,
                         mode=mode, name=SERVER_NAME)

run = main_sardana


def main():
    import datetime
    run(start_time=datetime.datetime.now())
