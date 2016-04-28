#!/usr/bin/env python

##############################################################################
##
## This file is part of Sardana
##
## http://www.sardana-controls.org/
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

"""
This module defines the test suite for the whole sardana package
Usage::

  from sardana.test import testsuite
  testsuite.run()

"""

__docformat__ = 'restructuredtext'

import sys, os
from taurus.external import unittest
import sardana


def run():
    '''Runs all tests for the sardana package

    :returns: the test runner result
    :rtype: unittest.result.TestResult
    '''
    # discover all tests within the sardana/src directory
    loader = unittest.defaultTestLoader
    start_dir = os.path.dirname(sardana.__file__)
    suite = loader.discover(start_dir, top_level_dir=os.path.dirname(start_dir))
    # use the basic text test runner that outputs to sys.stderr
    runner = unittest.TextTestRunner(descriptions=True, verbosity=2)
    # run the test suite
    result = runner.run(suite)
    return result

if __name__ == '__main__':
    result = run()
    exit_code = 0
    if not result.wasSuccessful():
        exit_code = 1
    sys.exit(exit_code)