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

"""This are the macroserver dummy data recorders"""

__all__ = ["DumbRecorder"]

__docformat__ = 'restructuredtext'

from sardana.macroserver.scan.recorder import BaseFileRecorder


class DumbRecorder(BaseFileRecorder):

    def __init__(self, filename=None, macro=None, overwrite=False, **pars):
        BaseFileRecorder.__init__(self, **pars)

        self.macro = macro
        self.overwrite = overwrite
        if filename:
            self.filename = filename

    def _startRecordList(self, recordlist):
        self.fd = open(self.filename, "a")
        self.fd.write("Starting new recording\n")
        self.fd.write("# Title :     %s\n" % recordlist.getEnvironValue('title'))
        env = recordlist.getEnviron()
        for envky in list(env.keys()):
            if envky != 'title' and envky != 'labels':
                self.fd.write("# %8s :    %s \n" % (envky, str(env[envky])))
        self.fd.write("# Started:    %s\n" % env['starttime'])
        self.fd.write("# L:  ")
        self.fd.write("  ".join([desc.label for desc in env['datadesc']]) + "\n")

    def _writeRecord(self, record):
        self.fd.write("%s\n" % record.data)

    def _endRecordList(self, recordlist):
        self.fd.write("Ending recording\n")
        env = recordlist.getEnviron()
        self.fd.write("Recording ended at: %s\n" % env['endtime'])
        self.fd.close()
