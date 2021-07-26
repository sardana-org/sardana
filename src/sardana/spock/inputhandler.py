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

"""Spock submodule. It contains an input handler"""

__all__ = ['SpockInputHandler']

__docformat__ = 'restructuredtext'

import threading

from sardana.util.thread import raise_in_thread
from sardana.taurus.core.tango.sardana.macroserver import BaseInputHandler

from sardana.spock import genutils


class SpockInputHandler(BaseInputHandler):

    def __init__(self):
        # don't call super __init__ on purpose
        self._input = genutils.spock_input
        self._input_thread = None

    def input(self, input_data=None):
        self._input_thread = threading.current_thread()
        if input_data is None:
            input_data = {}
        prompt = input_data.get('prompt')
        if 'data_type' in input_data:
            if input_data['data_type'] != 'String':
                print(("Accepted input:  %s" % input_data['data_type']))
        ret = dict(input=None, cancel=False)
        try:
            if prompt is None:
                ret['input'] = self._input()
            else:
                ret['input'] = self._input(prompt)
        except:
            ret['cancel'] = True
        return ret

    def input_timeout(self, input_data):
        raise_in_thread(KeyboardInterrupt, self._input_thread)
        print("Input timeout reached!")
