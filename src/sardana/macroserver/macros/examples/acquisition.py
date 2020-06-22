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

"""This module contains macros that demonstrate the usage of acquisition"""

__all__ = ["acq_meas_async"]

__docformat__ = 'restructuredtext'

from sardana.macroserver.macro import Macro, Type


class acq_meas_async(Macro):
    """A macro that executes an asynchronous acquisition of a measurement
    group. The acquisition can be cancelled by a Ctrl-C signal.

    This macro is part of the examples package. It was written for
    demonstration purposes"""

    param_def = [
        ['meas', Type.MeasurementGroup, None, 'meas. group to be acquired'],
        ['integ_time', Type.Float, None, 'integration time'],
    ]

    def run(self, meas, integ_time):
        self.info('starting acquisition for: {0}'.format(integ_time))
        meas.putIntegrationTime(integ_time)
        meas.setNbStarts(1)
        meas.prepare()
        id_ = meas.startCount()
        try:
            # Do whatever here (while the meas is acquiring)
            self.info('state: {0}'.format(meas.getStateEG().readValue()))
            # End Do whatever here
        finally:
            meas.waitCount(id=id_)
            # this line will not be printed in case of abort (Ctrl-C)
            # due to https://github.com/sardana-org/sardana/issues/10
            self.info('acquired values: {0}'.format(meas.getValues()))


class acq_expchannel_async(Macro):
    """A macro that executes an asynchronous acquisition of an experimental
    channel. The acquisition can be cancelled by a Ctrl-C signal.

    This macro is part of the examples package. It was written for
    demonstration purposes"""

    param_def = [
        ['channel', Type.ExpChannel, None, 'channel to be acquired'],
        ['integ_time', Type.Float, None, 'integration time'],
    ]

    def run(self, channel, integ_time):
        self.info('starting acquisition for: {0}'.format(integ_time))
        channel.putIntegrationTime(integ_time)
        id_ = channel.startCount()
        try:
            # Do whatever here (while the channel is acquiring)
            self.info('state: {0}'.format(channel.getStateEG().readValue()))
            # End Do whatever here
        finally:
            channel.waitCount(id=id_)
            # this line will not be printed in case of abort (Ctrl-C)
            # due to https://github.com/sardana-org/sardana/issues/10
            self.info('acquired value: {0}'.format(channel.getValue()))


class acq_expchannel(Macro):
    """A macro that executes an synchronous acquisition of an experimental
    channel. The acquisition can be cancelled by a Ctrl-C signal.

    This macro is part of the examples package. It was written for
    demonstration purposes"""

    param_def = [
        ['channel', Type.ExpChannel, None, 'channel to be acquired'],
        ['integ_time', Type.Float, None, 'integration time'],
    ]

    def run(self, channel, integ_time):
        self.info('starting acquisition for: {0}'.format(integ_time))
        _, value = channel.count(integ_time)
        self.info('acquired value: {0}'.format(value))
