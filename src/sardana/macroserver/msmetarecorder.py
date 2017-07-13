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

"""This module contains the class definition for the MacroServer meta recorder
information"""

__all__ = ["RECORDER_TEMPLATE", "RecorderLibrary", "RecorderClass"]

__docformat__ = 'restructuredtext'

from sardana import InvalidId, ElementType
from sardana.sardanameta import SardanaLibrary, SardanaClass

#: String containing template code for a controller class
RECORDER_TEMPLATE = """class @recorder_name@(BaseFileRecorder):
    \"\"\"@recorder_name@ description.\"\"\"

"""


class RecorderLibrary(SardanaLibrary):
    """Object representing a python module containing recorder classes and/or
    recorder functions. Public members:

        - module - reference to python module
        - file_path - complete (absolute) path (with file name at the end)
        - file_name - file name (including file extension)
        - path - complete (absolute) path
        - name - (=module name) module name (without file extension)
        - recorder_list - list<RecorderClass>
        - exc_info - exception information if an error occurred when loading
                    the module"""

    def __init__(self, **kwargs):
        kwargs['manager'] = kwargs.pop('macro_server')
        kwargs['elem_type'] = ElementType.RecorderLibrary
        SardanaLibrary.__init__(self, **kwargs)

    def serialize(self, *args, **kwargs):
        kwargs = SardanaLibrary.serialize(self, *args, **kwargs)
        kwargs['macro_server'] = self.get_manager().name
        kwargs['id'] = InvalidId
        return kwargs

    add_recorder = SardanaLibrary.add_meta_class
    get_recorder = SardanaLibrary.get_meta_class
    get_recorders = SardanaLibrary.get_meta_classes
    has_recorder = SardanaLibrary.has_meta_class

    @property
    def recorders(self):
        return self.meta_classes


class RecorderClass(SardanaClass):
    """Object representing a python recorder class.
       Public members:

           - name - class name
           - klass - python class object
           - lib - RecorderLibrary object representing the module where the
             recorder is."""

    def __init__(self, **kwargs):
        kwargs['manager'] = kwargs.pop('macro_server')
        kwargs['elem_type'] = ElementType.RecorderClass
        SardanaClass.__init__(self, **kwargs)

    def serialize(self, *args, **kwargs):
        kwargs = SardanaClass.serialize(self, *args, **kwargs)
        kwargs['id'] = InvalidId
        kwargs['hints'] = self.code_object.hints
        kwargs['macro_server'] = self.get_manager().name
        return kwargs

    @property
    def recorder_class(self):
        return self.klass
