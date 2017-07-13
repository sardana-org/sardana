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

from threading import Condition


class CountLatch(object):
    """Synchronization primitive with the capacity to count and latch.
    Counting up latches, while reaching zero when counting down un-latches.

    .. note::
        The CountLatch class has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the module) may occur if
        deemed necessary by the core developers.
    """

    def __init__(self):
        self.count = 0
        self.condition = Condition()

    def count_up(self):
        """Count up."""
        self.condition.acquire()
        self.count += 1
        self.condition.release()

    def count_down(self, _=None):
        """Count down."""
        self.condition.acquire()
        self.count -= 1
        if self.count <= 0:
            self.condition.notifyAll()
        self.condition.release()

    def wait(self):
        """Wait until the counter reaches zero."""
        self.condition.acquire()
        while self.count > 0:
            self.condition.wait()
        self.condition.release()
