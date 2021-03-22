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

"""This module is part of the Python Sardana libray. It defines the base
classes for MetaLibrary and MetaClass"""



__all__ = ["SardanaLibrary", "SardanaClass", "SardanaFunction"]

__docformat__ = 'restructuredtext'

import os
import inspect
import weakref
import linecache
import traceback

from sardana.sardanabase import SardanaBaseObject


# ----------------------------------------------------------------------------
# Start patch around inspect issue http://bugs.python.org/issue993580

def findsource(obj):
    """

    Parameters
    ----------
    obj :
        

    Returns
    -------
    type
        The argument may be a module, class, method, function, traceback, frame,
        or code object.  The source code is returned as a list of all the lines
        in the file and the line number indexes a line in that list.  An IOError
        is raised if the source code cannot be retrieved.

    """
    filename = inspect.getsourcefile(obj)
    if filename:
        linecache.checkcache(filename)
    return inspect.findsource(obj)


def getsourcelines(object):
    """

    Parameters
    ----------
    object :
        

    Returns
    -------
    type
        The argument may be a module, class, method, function, traceback, frame,
        or code object.  The source code is returned as a list of the lines
        corresponding to the object and the line number indicates where in the
        original source file the first line of code was found.  An IOError is

    """
    lines, lnum = findsource(object)

    if inspect.ismodule(object):
        return lines, 0
    else:
        return inspect.getblock(lines[lnum:]), lnum + 1


def getsource(object):
    """

    Parameters
    ----------
    object :
        

    Returns
    -------
    type
        The argument may be a module, class, method, function, traceback, frame,
        or code object.  The source code is returned as a single string.  An
        IOError is raised if the source code cannot be retrieved.

    """
    lines, lnum = getsourcelines(object)
    return str.join('', lines)

# End patch around inspect issue http://bugs.python.org/issue993580
# ----------------------------------------------------------------------------


class SardanaLibrary(SardanaBaseObject):
    """Object representing a python module containing sardana classes.
       Public members:
    
           - module - reference to python module
           - file_path - complete (absolute) path (with file name at the end)
           - file_name - file name (including file extension)
           - path - complete (absolute) path
           - name - (=module name) module name (without file extension)
           - meta_classes - dict<str, SardanMetaClass>
           - exc_info - exception information if an error occurred when loading
                        the module

    Parameters
    ----------

    Returns
    -------

    """

    description = '<Undocumented>'

    def __init__(self, **kwargs):
        self.module = module = kwargs.pop('module', None)
        self.file_path = file_path = kwargs.pop('file_path', None)
        self.exc_info = kwargs.pop('exc_info', None)
        if module is not None:
            file_path = os.path.abspath(module.__file__)
        self.file_path = file_path
        if file_path is None:
            self.path = kwargs.get('path', None)
            self.file_name = kwargs.get('file_name', None)
            name = kwargs.get('name', None)
        else:
            if self.file_path.endswith(".pyc"):
                self.file_path = self.file_path[:-1]
            self.path, self.file_name = os.path.split(self.file_path)
            name, _ = os.path.splitext(self.file_name)
        self.meta_classes = {}
        self.meta_functions = {}
        if module is not None:
            if module.__doc__ is not None:
                self.description = module.__doc__
            self._code = getsourcelines(module)[0]
        else:
            self.description = name + " in error!"
            self._code = None
        kwargs['name'] = name
        kwargs['full_name'] = file_path or name
        SardanaBaseObject.__init__(self, **kwargs)

    def __lt__(self, o):
        return self.full_name < o.full_name

    def __str__(self):
        return self.name

    @property
    def module_name(self):
        """Returns the module name for this library.

        Parameters
        ----------

        Returns
        -------
        obj:`str`
            the module name

        """
        return self.name

    @property
    def code(self):
        """Returns a sequence of sourcelines corresponding to the module code.

        Parameters
        ----------

        Returns
        -------
        list<str>
            list of source code lines

        """
        code = self._code
        if code is None:
            raise IOError('source code not available')
        return code

    def add_meta_class(self, meta_class):
        """Adds a new :class:~`sardana.sardanameta.SardanaClass` to this
        library.

        Parameters
        ----------
        meta_class : class: :class:~`sardana.sardanameta.SardanaClass
            the meta class to be added to this library

        Returns
        -------

        """
        self.meta_classes[meta_class.name] = meta_class

    def get_meta_class(self, meta_class_name):
        """Returns a :class:~`sardana.sardanameta.SardanaClass` for the
        given meta class name or None if the meta class does not exist in this
        library.

        Parameters
        ----------
        meta_class_name : obj:`str`
            the meta class name

        Returns
        -------
        class:~`sardana.sardanameta.SardanaClass`
            a meta class or None

        """
        return self.meta_classes.get(meta_class_name)

    def get_meta_classes(self):
        """Returns a sequence of the meta classes that belong to this library.

        Parameters
        ----------

        Returns
        -------
        seq<:class:~`sardana.sardanameta.SardanaClass`>
            a sequence of meta classes that belong to this library

        """
        return list(self.meta_classes.values())

    def has_meta_class(self, meta_class_name):
        """Returns True if the given meta class name belongs to this library
        or False otherwise.

        Parameters
        ----------
        meta_class_name : obj:`str`
            the meta class name

        Returns
        -------
        bool
            True if the given meta class name belongs to this library
            or False otherwise

        """
        return meta_class_name in self.meta_classes

    def add_meta_function(self, meta_function):
        """Adds a new :class:~`sardana.sardanameta.SardanaFunction` to this
        library.

        Parameters
        ----------
        meta_function : class:~`sardana.sardanameta.SardanaFunction
            the meta function to be added to this library

        Returns
        -------

        """
        self.meta_functions[meta_function.name] = meta_function

    def get_meta_function(self, meta_function_name):
        """Returns a :class:~`sardana.sardanameta.SardanaFunction` for the
        given meta function name or None if the meta function does not exist in
        this library.

        Parameters
        ----------
        meta_function_name : obj:`str`
            the meta function name

        Returns
        -------
        class:~`sardana.sardanameta.SardanaFunction`
            a meta function or None

        """
        return self.meta_functions.get(meta_function_name)

    def get_meta_functions(self):
        """Returns a sequence of the meta functions that belong to this library.

        Parameters
        ----------

        Returns
        -------
        seq<:class:~`sardana.sardanameta.SardanaFunction`>
            a sequence of meta functions that belong to this library

        """
        return list(self.meta_functions.values())

    def has_meta_function(self, meta_function_name):
        """Returns True if the given meta function name belongs to this library
        or False otherwise.

        Parameters
        ----------
        meta_function_name : obj:`str`
            the meta function name

        Returns
        -------
        bool
            True if the given meta function name belongs to this library
            or False otherwise

        """
        return meta_function_name in self.meta_functions

    def get_meta(self, meta_name):
        """Returns a :class:~`sardana.sardanameta.SardanaCode` for the
        given meta name or None if the meta does not exist in this library.

        Parameters
        ----------
        meta_name : obj:`str`
            the meta name (class, function)

        Returns
        -------
        class:~`sardana.sardanameta.SardanaCode`
            a meta or None

        """
        ret = self.get_meta_class(meta_name)
        if ret is None:
            ret = self.get_meta_function(meta_name)
        return ret

    def has_meta(self, meta_name):
        """Returns True if the given meta name belongs to this library
        or False otherwise.

        Parameters
        ----------
        meta_name : obj:`str`
            the meta name

        Returns
        -------
        bool
            True if the given meta (class or function) name belongs to this
            library or False otherwise

        """
        return self.has_meta_class(meta_name) or \
            self.has_meta_function(meta_name)

    def has_metas(self):
        """Returns True if any meta object exists in the library
        or False otherwise.

        Parameters
        ----------

        Returns
        -------
        bool
            True if any meta object (class or function) exists
            in the library or False otherwise

        """
        has_metas_bool = False
        if (len(self.get_meta_classes()) > 0 or
                len(self.get_meta_functions()) > 0):
            has_metas_bool = True
        return has_metas_bool

    def get_metas(self):
        """Returns a sequence of the meta (class and functions) that belong to
        this library.

        Parameters
        ----------

        Returns
        -------
        seq<:class:~`sardana.sardanameta.SardanaCode`>
            a sequence of meta (class and functions) that belong to this library

        """
        return self.get_meta_classes() + self.get_meta_functions()

    def get_name(self):
        """Returns the module name for this library (same as
        :meth:~sardana.sardanameta.SardanaLibrary.get_module_name).

        Parameters
        ----------

        Returns
        -------
        obj:`str`
            the module name

        """
        return self.name

    def get_module_name(self):
        """Returns the module name for this library (same as
        :meth:~sardana.sardanameta.SardanaLibrary.get_name).

        Parameters
        ----------

        Returns
        -------
        obj:`str`
            the module name

        """
        return self.module_name

    def get_module(self):
        """Returns the python module for this library.

        Parameters
        ----------

        Returns
        -------
        object
            the python module

        """
        return self.module

    def get_description(self):
        """Returns the this library documentation or "<Undocumented>" if no
        documentation exists.

        Parameters
        ----------

        Returns
        -------
        obj:`str`
            this library documentation or None

        """
        return self.description

    def get_code(self):
        """Returns a sequence of sourcelines corresponding to the module code.

        Parameters
        ----------

        Returns
        -------
        list<str>
            list of source code lines

        """
        return self.code

    def get_file_path(self):
        """Returns the file path for this library. On posix systems is something
        like: /abs/path/filename.py

        Parameters
        ----------

        Returns
        -------
        obj:`str`
            this library file path

        """
        if self.file_path is None:
            return None
        if self.file_path.endswith('.pyc'):
            return self.file_path[:-1]
        return self.file_path

    def get_file_name(self):
        """Returns the file name for this library. On posix systems is something
        like: filename.py

        Parameters
        ----------

        Returns
        -------
        obj:`str`
            this library file name

        """
        return self.file_name

    def has_errors(self):
        """Returns True if this library has syntax errors or False otherwise.

        Parameters
        ----------

        Returns
        -------
        bool
            True if this library has syntax errors or False otherwise

        """
        return self.exc_info is not None

    def set_error(self, exc_info):
        """Sets the error information for this library

        Parameters
        ----------
        exc_info : tuple<type, value, traceback
            error information. It must be an object similar to the
            one returned by :func:`sys.exc_info`

        Returns
        -------

        """
        self.exc_info = exc_info
        if exc_info is None:
            self.meta_classes = {}
            self.meta_functions = {}

    def get_error(self):
        """Gets the error information for this library or None if no error
        exists

        Parameters
        ----------

        Returns
        -------
        tuple<type, value, traceback>
            error information. An object similar to the one returned by
            :func:`sys.exc_info`

        """
        return self.exc_info

    def serialize(self, *args, **kwargs):
        """Returns a serializable object describing this object.

        Parameters
        ----------
        *args :
            
        **kwargs :
            

        Returns
        -------
        dict
            a serializable dict

        """
        kwargs = SardanaBaseObject.serialize(self, *args, **kwargs)
        kwargs['id'] = 0
        kwargs['module'] = self.name
        kwargs['file_path'] = self.file_path
        kwargs['file_name'] = self.file_name
        kwargs['path'] = self.path
        kwargs['description'] = self.description
        kwargs['elements'] = list(self.meta_classes.keys()) + \
            list(self.meta_functions.keys())
        if self.exc_info is None:
            kwargs['exc_summary'] = None
            kwargs['exc_info'] = None
        else:
            kwargs['exc_summary'] = "".join(
                traceback.format_exception_only(*self.exc_info[:2]))
            kwargs['exc_info'] = "".join(
                traceback.format_exception(*self.exc_info))
        return kwargs


class SardanaCode(SardanaBaseObject):
    """Object representing a python code (base for class and function)."""

    description = '<Undocumented>'

    def __init__(self, **kwargs):
        lib = kwargs.pop('lib')
        self._lib = weakref.ref(lib)
        self._code_obj = kwargs.pop('code')
        doc = self._code_obj.__doc__
        if doc:
            self.description = doc
        self._code = getsourcelines(self._code_obj)
        name = kwargs['name']
        kwargs['full_name'] = "{0}.{1}".format(lib.name, name)
        kwargs['parent'] = kwargs.pop('parent', self.lib)
        SardanaBaseObject.__init__(self, **kwargs)

    @property
    def code_object(self):
        """ """
        return self._code_obj

    @property
    def lib(self):
        """Returns the library :class:~`sardana.sardanameta.SardanaLibrary`
        for this class.

        Parameters
        ----------

        Returns
        -------
        class:~`sardana.sardanameta.SardanaLibrary`
            a reference to the library where this class is located

        """
        return self._lib()

    @property
    def module(self):
        """Returns the python module for this class.

        Parameters
        ----------

        Returns
        -------
        object
            the python module

        """
        return self.lib.module

    @property
    def module_name(self):
        """Returns the module name for this class.

        Parameters
        ----------

        Returns
        -------
        obj:`str`
            the module name

        """
        return self.lib.get_module_name()

    @property
    def file_path(self):
        """Returns the file path for for the library where this class is. On
        posix systems is something like: /abs/path/filename.py

        Parameters
        ----------

        Returns
        -------
        obj:`str`
            the file path for for the library where this class is

        """
        return self.lib.file_path

    @property
    def file_name(self):
        """Returns the file name for the library where this class is. On posix
        systems is something like: filename.py

        Parameters
        ----------

        Returns
        -------
        obj:`str`
            the file name for the library where this class is

        """
        return self.lib.file_name

    @property
    def path(self):
        """Returns the absolute path for the library where this class is. On
        posix systems is something like: /abs/path

        Parameters
        ----------

        Returns
        -------
        obj:`str`
            the absolute path for the library where this class is

        """
        return self.lib.path

    @property
    def code(self):
        """Returns a tuple (sourcelines, firstline) corresponding to the
        definition of this code object. sourcelines is a list of source code
        lines. firstline is the line number of the first source code line.

        Parameters
        ----------

        Returns
        -------

        """
        code = self._code
        if code is None:
            raise IOError('source code not available')
        return code

    def get_code(self):
        """Returns a tuple (sourcelines, firstline) corresponding to the
        definition of the controller class. sourcelines is a list of source code
        lines. firstline is the line number of the first source code line.

        Parameters
        ----------

        Returns
        -------

        """
        return self.code

    def serialize(self, *args, **kwargs):
        """Returns a serializable object describing this object.

        Parameters
        ----------
        *args :
            
        **kwargs :
            

        Returns
        -------
        dict
            a serializable dict

        """
        kwargs = SardanaBaseObject.serialize(self, *args, **kwargs)
        kwargs['id'] = 0
        kwargs['module'] = self.module_name
        kwargs['file_name'] = self.file_name
        kwargs['file_path'] = self.file_path
        kwargs['path'] = self.path
        kwargs['description'] = self.description
        return kwargs

    def get_brief_description(self, max_chars=60):
        """

        Parameters
        ----------
        max_chars :
             (Default value = 60)

        Returns
        -------

        """
        desc = self.description.replace('\n', ' ')
        if len(desc) > (max_chars - 5):
            desc = desc[:max_chars - 5] + '[...]'
        return desc


class SardanaClass(SardanaCode):
    """Object representing a python class."""

    def __init__(self, **kwargs):
        klass = kwargs.pop('klass')
        kwargs['code'] = klass
        kwargs['name'] = kwargs.pop('name', klass.__name__)
        SardanaCode.__init__(self, **kwargs)

    @property
    def klass(self):
        """ """
        return self.code_object


class SardanaFunction(SardanaCode):
    """Object representing a python function."""

    def __init__(self, **kwargs):
        function = kwargs.pop('function')
        kwargs['code'] = function
        kwargs['name'] = kwargs.pop('name', function.__name__)
        SardanaCode.__init__(self, **kwargs)

    @property
    def function(self):
        """ """
        return self.code_object
