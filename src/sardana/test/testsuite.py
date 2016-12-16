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

import os
import re
from taurus.external import unittest
import sardana


def _filter_suite(suite, exclude_pattern, ret=None):
    """removes TestCases from a suite based on regexp matching on the Test id"""
    if ret is None:
        ret = unittest.TestSuite()
    for e in suite:
        if isinstance(e, unittest.TestCase):
            if re.match(exclude_pattern, e.id()):
                print "Excluded %s" % e.id()
                continue
            ret.addTest(e)
        else:
            _filter_suite(e, exclude_pattern, ret=ret)
    return ret


def get_sardana_suite(exclude_pattern='(?!)'):
    """discover all tests in sardana, except those matching `exclude_pattern`"""
    loader = unittest.defaultTestLoader
    start_dir = os.path.dirname(sardana.__file__)
    suite = loader.discover(start_dir, top_level_dir=os.path.dirname(start_dir))
    return _filter_suite(suite, exclude_pattern)

def get_sardana_unitsuite():
    """Provide test suite with only unit tests. These exclude:
        - functional tests of macros that requires the "sar_demo environment"
    """
    return get_sardana_suite(exclude_pattern='sardana\.macroserver\.macros\.test*')

def run(exclude_pattern='(?!)'):
    '''Runs all tests for the sardana package

    :returns: the test runner result
    :rtype: unittest.result.TestResult
    '''
    # discover all tests within the sardana/src directory
    suite = get_sardana_suite(exclude_pattern=exclude_pattern)
    # use the basic text test runner that outputs to sys.stderr
    runner = unittest.TextTestRunner(descriptions=True, verbosity=2)
    # run the test suite
    result = runner.run(suite)
    return result


def main():
    import sys
    from taurus.external import argparse
    from sardana import Release

    parser = argparse.ArgumentParser(description='Main test suite for Sardana')
    # TODO: Define the default exclude patterns as a sardanacustomsettings
    # variable.
    help = """regexp pattern matching test ids to be excluded.
    (e.g. 'sardana\.pool\..*' would exclude sardana.pool tests)
    """
    parser.add_argument('-e', '--exclude-pattern',
                        dest='exclude_pattern',
                        default='(?!)',
                        help=help)
    parser.add_argument('--version', action='store_true', default=False,
                        help="show program's version number and exit")
    args = parser.parse_args()

    if args.version:
        print Release.version
        sys.exit(0)

    ret = run(exclude_pattern=args.exclude_pattern)

    # calculate exit code (0 if OK and 1 otherwise)
    if ret.wasSuccessful():
        exit_code = 0
    else:
        exit_code = 1
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
