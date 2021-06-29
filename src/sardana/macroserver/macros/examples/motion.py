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

"""This module contains macros that demonstrate the usage of motion"""

__all__ = ["move_async"]

__docformat__ = 'restructuredtext'

from sardana.macroserver.macro import *


class move_async(Macro):
    """A macro that executes an asynchronous movement of a motor. The movement
    can be cancelled by a Ctrl-C signal.

    This macro is part of the examples package. It was written for
    demonstration purposes"""

    param_def = [['moveable', Type.Moveable, None, 'moveable to be moved'],
                 ['pos', Type.Float, None, 'target position'],
                 ]

    def run(self, moveable, pos):
        motion = self.getMotion([moveable])
        self.info('initial position: %s' % motion.readPosition())
        _id = motion.startMove([pos])
        try:
            # Do whatever here (while the moveable is moving)
            self.info('state: %s' % motion.readState())
            # End Do whatever here
        finally:
            motion.waitMove(id=_id)
            # this line will not be printed in case of abort (Ctrl-C)
            # due to https://sourceforge.net/p/sardana/tickets/9/
            self.info('final position: %s' % motion.readPosition())
