##############################################################################
##
# This file is part of Sardana
##
# http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
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
import random

from sardana.sardanathreadpool import get_thread_pool
from sardana.util.thread import CountLatch
from unittest import TestCase


def job(i, duration):
    time.sleep(duration)


class CountLatchTestCase(TestCase):

    def test_countlatch(self):
        pool = get_thread_pool()
        latch = CountLatch()
        for i in range(10):
            latch.count_up()
            pool.add(job, latch.count_down, i, random.uniform(0.1, 1))
        latch.wait()
        msg = "some workers are still busy"
        self.assertEqual(pool.getNumOfBusyWorkers(), 0, msg)
        msg = "jobs queue is not empty"
        self.assertEqual(pool.qsize, 0, msg)
