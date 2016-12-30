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

import os
import imp
from setuptools import setup, find_packages


def get_release_info():
    name = "release"
    setup_dir = os.path.dirname(os.path.abspath(__file__))
    release_dir = os.path.join(setup_dir, "src", "sardana")
    data = imp.find_module(name, [release_dir])
    release = imp.load_module(name, *data)
    return release

release = get_release_info()

package_dir = {"": "src"}

packages = find_packages(where="src")

provides = [
    'sardana',
    'sardana.pool',
    'sardana.macroserver',
    'sardana.spock',
    'sardana.tango',
]

requires = [
    'PyTango (>=7.2.3)',
    # when using PyTango < 9 the dependency is >= 0.0.1 and < 0.1.0
    # when using PyTango >= 9 the dependency is >= 0.1.6
    'itango (>=0.0.1)',
    'taurus (>= 3.6.0)',
    'lxml (>=2.1)',
]

console_scripts = [
    "MacroServer = sardana.tango.macroserver:main",
    "Pool = sardana.tango.pool:main",
    "Sardana = sardana.tango:main",
    "sardanatestsuite = sardana.test.testsuite:main",
    "spock = sardana.spock:main",
]

gui_scripts = [
    "diffractometeralignment = sardana.taurus.qt.qtgui.extra_hkl.diffractometeralignment:main",
    "hklscan = sardana.taurus.qt.qtgui.extra_hkl.hklscan:main",
    "macroexecutor = sardana.taurus.qt.qtgui.extra_macroexecutor.macroexecutor:main",
    "sequencer = sardana.taurus.qt.qtgui.extra_macroexecutor.sequenceeditor:main",
    "ubmatrix = sardana.taurus.qt.qtgui.extra_hkl.ubmatrix:main"
]

entry_points={'console_scripts': console_scripts,
              'gui_scripts': gui_scripts,
}

classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: No Input/Output (Daemon)',
        'Environment :: Win32 (MS Windows)',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries',
]

setup(name='sardana',
      version=release.version,
      description=release.description,
      long_description=release.long_description,
      author=release.authors['Tiago_et_al'][0],
      maintainer=release.authors['Community'][0],
      maintainer_email=release.authors['Community'][1],
      url=release.url,
      download_url=release.download_url,
      platforms=release.platforms,
      license=release.license,
      keywords=release.keywords,
      packages=packages,
      package_dir=package_dir,
      include_package_data=True,
      classifiers=classifiers,
      entry_points=entry_points,
      provides=provides,
      requires=requires,
      test_suite='sardana.test.testsuite.get_sardana_unitsuite',
)
