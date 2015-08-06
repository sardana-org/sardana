#!/usr/bin/env python

##############################################################################
##
## This file is part of Sardana
##
## http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
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

from taurus.test.base import insertTest
from sardana.pool.poolcontrollers.test import TriggerGateControllerTestCase
from sardana.pool.poolcontrollers.SoftwareTriggerGateController import\
                                                  SoftwareTriggerGateController

@insertTest(helper_name='generation', offset=0, active=.1, passive=.1,
            repetitions=10)
@insertTest(helper_name='abort', offset=0, active=.1, passive=.1,
            repetitions=10, abort=.1)
class SoftwareTriggerGateControllerTestCase(TriggerGateControllerTestCase):
    KLASS = SoftwareTriggerGateController