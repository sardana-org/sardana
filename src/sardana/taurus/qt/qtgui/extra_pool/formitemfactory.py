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
This module provides TaurusValue item factories to be registered as providers
of custom TaurusForm item widgets.
"""

from . import PoolMotorTV, PoolChannelTV, PoolIORegisterTV, _PoolChannelTV

T_FORM_POOL_WIDGET_MAP = {
    "SimuMotor": PoolMotorTV,
    "Motor": PoolMotorTV,
    "PseudoMotor": PoolMotorTV,
    "PseudoCounter": _PoolChannelTV,
    "CTExpChannel": PoolChannelTV,
    "ZeroDExpChannel": _PoolChannelTV,
    "OneDExpChannel": PoolChannelTV,
    "TwoDExpChannel": PoolChannelTV,
    "IORegister": PoolIORegisterTV,
}


def pool_item_factory(model):
    """
    Taurus Value Factory to be registered as a TaurusForm item factory plugin

    :param model: taurus model object

    :return: custom TaurusValue class
    """
    # TODO: use sardana element types instead of tango classes
    try:
        key = model.getDeviceProxy().info().dev_class
        klass = T_FORM_POOL_WIDGET_MAP[key]
    except Exception:
        return None
    return klass()
