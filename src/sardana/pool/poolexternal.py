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

"""This module is part of the Python Pool libray. It defines the base classes
for external objects to the pool (like tango objects)"""

__all__ = ["PoolBaseExternalObject", "PoolTangoObject", "PoolExternalObject"]

__docformat__ = 'restructuredtext'

import PyTango

from sardana import ElementType
import sardana
from sardana.pool.poolbaseobject import PoolBaseObject
from taurus.core.tango.tangovalidator import TangoAttributeNameValidator

class PoolBaseExternalObject(PoolBaseObject):
    """TODO"""

    def __init__(self, **kwargs):
        kwargs['elem_type'] = ElementType.External
        PoolBaseObject.__init__(self, **kwargs)

    def get_source(self):
        return self.full_name

    def get_config(self):
        raise NotImplementedError


class PoolTangoObject(PoolBaseExternalObject):
    """TODO"""

    def __init__(self, pool, name):
        validator = TangoAttributeNameValidator()
        params = validator.getUriGroups(name)
        full_name = "{}:{}{}".format(params['scheme'], params['authority'], params['path'])
        name = "{}/{}".format(params['devname'], params['_shortattrname'])
        self._device_name = params['devname']
        self._attribute_name = params['_shortattrname']
        self._config = None
        self._device = None

        # TODO evaluate to use alias instead of device_name
        kwargs = {}
        kwargs['scheme'] = params['scheme']
        kwargs['pool'] = pool
        kwargs['name'] = name
        kwargs['full_name'] = full_name
        PoolBaseExternalObject.__init__(self, **kwargs)

    def get_device_name(self):
        return self._device_name

    def get_attribute_name(self):
        return self._attribute_name

    def get_device(self):
        device = self._device
        if device is None:
            try:
                self._device = device = PyTango.DeviceProxy(self._device_name)
            except:
                pass
        return device

    def get_config(self):
        config = self._config
        if config is None:
            try:
                self._config = config = \
                    self._device.get_attribute_config(self._attribute_name)
            except:
                pass
        return config

    device_name = property(get_device_name)
    attribute_name = property(get_attribute_name)


_SCHEME_CLASS = {'tango': PoolTangoObject,
                 None: PoolTangoObject}


def PoolExternalObject(pool, name):
    """
    Factory of Pool external objects.

    :param pool: The pool object.
    :type pool: `sardana.pool.Pool`
    :param name: The name of the external object (Any name accepted by Taurus
        validators.).
    :type name: `str`
    :return: Pool external object.
    :rtype: `sardana.pool.poolexternal.PoolBaseExternalObject`
    """

    scheme = name.split(":")[0]
    klass = _SCHEME_CLASS.get(scheme, PoolTangoObject)
    return klass(pool, name)
