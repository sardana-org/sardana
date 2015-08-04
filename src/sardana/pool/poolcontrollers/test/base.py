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


class BaseControllerTestCase(object):
    """ Base class for test any controller.
    This class will create a controller instance and define an axis from the
    class member attributes:
        KLASS <type> controller class
        NAME <str> mame of the controller
        CONF <dict> configuration of the controller
        AXIS <int> number of the axis
    """
    KLASS = None
    NAME = ''
    CONF = {}
    AXIS = 1

    def setUp(self):
        if self.KLASS is None:
            raise Exception('Ctrl klass has not been defined')
        if self.NAME == '':
            self.NAME = self.KLASS.__name__
        try:
            self.ctrl = self.KLASS(self.NAME, self.CONF)
            self.ctrl.AddDevice(self.AXIS)
        except:
            self.ctrl = None
            raise Exception('Imposible to create an instance of %s' %self.KLASS)

    def tearDown(self):
        if self.ctrl is not None:
            self.ctrl.DeleteDevice(self.AXIS)

    def axisPar(self, parameter, value):
        axis = self.AXIS
        self.ctrl.SetAxisPar(axis, parameter, value)
        r_value = self.ctrl.GetAxisPar(axis, parameter)
        msg = ('The %s value is %s, and the expected value is %s'
               %(parameter, r_value, value))
        self.assertEqual(value, r_value, msg)
