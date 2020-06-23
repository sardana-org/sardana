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

import time
import ctypes
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


_asyncexc = ctypes.pythonapi.PyThreadState_SetAsyncExc
# first define the async exception function args. This is
# absolutely necessary for 64 bits machines.
_asyncexc.argtypes = (ctypes.c_long, ctypes.py_object)


def raise_in_thread(exception, thread, logger=None):
    """Raise exception in a thread.

    Inspired on :meth:sardana.macroserver.macro.Macro.abort

    :param exception: Exception to be raised
    :param thread: thread in which raise the exception.
    """
    ret, i = 0, 0
    while ret != 1:
        th_id = ctypes.c_long(thread.ident)
        if logger:
            logger.debug("Sending AbortException to %s", thread.name)
        ret = _asyncexc(th_id, ctypes.py_object(exception))
        i += 1
        if ret == 0:
            # try again
            if i > 2:
                if logger:
                    logger.error("Failed to abort after three tries!")
                break
            time.sleep(0.1)
        if ret > 1:
            # if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the
            # effect
            _asyncexc(th_id, None)
            if logger:
                logger.error("Failed to abort (unknown error code {})".
                             format(ret))
            break
