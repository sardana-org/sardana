#!/usr/bin/env python

##############################################################################
##
## This file is part of Sardana
##
## http://www.sardana-controls.org/
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
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

"""This are the macroserver dummy data recorders"""

__all__ = ["DumbRecorder"]

__docformat__ = 'restructuredtext'

import time

from sardana.macroserver.scan.recorder import DataRecorder

class DumbRecorder(DataRecorder):

    def _startRecordList(self, recordlist):
        print "Starting new recording"
        print "# Title :     ", recordlist.getEnvironValue('title')
        env = recordlist.getEnviron()
        for envky in env.keys():
            if envky != 'title' and envky != 'labels':
                print "# %8s :    %s " % (envky, str(env[envky]))
        print "# Started:    ", time.ctime(env['starttime'])
        print "# L:  ",
        print "  ".join(env['labels'])

    def _writeRecord(self, record):
        print record.data

    def _endRecordList(self, recordlist):
        print "Ending recording"
        env = recordlist.getEnviron()
        print "Recording ended at: ", time.ctime(env['endtime'])