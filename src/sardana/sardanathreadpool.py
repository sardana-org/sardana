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

"""This module contains the function to access sardana thread pool"""




__all__ = ["get_thread_pool"]

__docformat__ = 'restructuredtext'

import threading

from taurus.core.util.threadpool import ThreadPool, Worker


__thread_pool_lock = threading.Lock()
__thread_pool = None


class OmniWorker(Worker):

    def run(self):
        try:
            import tango
        except ImportError:
            Worker.run(self)
        # Tango is not thread safe when using threading.Thread. One must
        # use omni threads instead. This was confirmed for parallel
        # event subscriptions in PyTango#307. Use EnsureOmniThread introduced
        # in PyTango#327 whenever available.
        else:
            if hasattr(tango, "EnsureOmniThread"):
                with tango.EnsureOmniThread():
                    Worker.run(self)
            else:
                import taurus
                taurus.warning("Your Sardana system is affected by bug "
                               "tango-controls/pytango#307. Please use "
                               "PyTango with tango-controls/pytango#327.")
                Worker.run(self)


def get_thread_pool():
    """Returns the global pool of threads for Sardana

    :return: the global pool of threads object
    :rtype: taurus.core.util.ThreadPool"""

    global __thread_pool
    global __thread_pool_lock
    with __thread_pool_lock:
        if __thread_pool is None:
            # protect older versions of Taurus (without the worker_cls
            # argument) remove it whenever we bump Taurus dependency
            try:
                __thread_pool = ThreadPool(name="SardanaTP", Psize=10,
                                           worker_cls=OmniWorker)
            except TypeError:
                import taurus
                taurus.warning("Your Sardana system is affected by bug "
                               "tango-controls/pytango#307. Please use "
                               "Taurus with taurus-org/taurus#1081.")
                __thread_pool = ThreadPool(name="SardanaTP", Psize=10)

        return __thread_pool
