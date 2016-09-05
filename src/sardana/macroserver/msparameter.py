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

"""This module contains the definition of the macroserver parameters for
macros"""

__all__ = ["WrongParam", "MissingParam", "SupernumeraryParam",
           "UnknownParamObj", "WrongParamType", "MissingRepeat",
           "SupernumeraryRepeat", "TypeNames", "Type", "ParamType",
           "ParamRepeat", "ElementParamType", "ElementParamInterface",
           "AttrParamType", "AbstractParamTypes", "ParamDecoder"]

__docformat__ = 'restructuredtext'

from copy import deepcopy
from lxml import etree

from taurus.core.util.containers import CaselessDict

from sardana import ElementType, INTERFACES_EXPANDED
from sardana.macroserver.msbase import MSBaseObject
from sardana.macroserver.msexception import MacroServerException, \
    UnknownMacro, UnknownMacroLibrary


class WrongParam(MacroServerException):

    def __init__(self, *args):
        MacroServerException.__init__(self, *args)
        self.type = 'Wrong parameter'


class MissingParam(WrongParam):

    def __init__(self, *args):
        WrongParam.__init__(self, *args)
        self.type = 'Missing parameter'


class SupernumeraryParam(WrongParam):

    def __init__(self, *args):
        WrongParam.__init__(self, *args)
        self.type = 'Supernumerary parameter'


class UnknownParamObj(WrongParam):

    def __init__(self, *args):
        WrongParam.__init__(self, *args)
        self.type = 'Unknown parameter'


class WrongParamType(WrongParam):

    def __init__(self, *args):
        WrongParam.__init__(self, *args)
        self.type = 'Unknown parameter type'


class MissingRepeat(WrongParam):

    def __init__(self, *args):
        WrongParam.__init__(self, *args)
        self.type = 'Missing repeat'


class SupernumeraryRepeat(WrongParam):

    def __init__(self, *args):
        WrongParam.__init__(self, *args)
        self.type = 'Supernumerary repeat'


class TypeNames:
    """Class that holds the list of registered macro parameter types"""

    def __init__(self):
        self._type_names = {}
        self._pending_type_names = {}

    def addType(self, name):
        """Register a new macro parameter type"""
        setattr(self, name, name)
        self._type_names[name] = name
        if name in self._pending_type_names:
            del self._pending_type_names[name]

    def removeType(self, name):
        """remove a macro parameter type"""
        delattr(self, name)
        try:
            del self._type_names[name]
        except ValueError:
            pass

    def __str__(self):
        return str(self._type_names.keys())

#    def __getattr__(self, name):
#        if name not in self._pending_type_names:
#            self._pending_type_names[name] = name
#        return self._pending_type_names[name]


# This instance of TypeNames is intended to provide access to types to the
# Macros in a "Type.Motor" fashion
Type = TypeNames()


class ParamType(MSBaseObject):

    All = 'All'

    # Capabilities
    ItemList = 'ItemList'
    ItemListEvents = 'ItemListEvents'

    capabilities = []

    type_class = str

    def __init__(self, macro_server, name):
        MSBaseObject.__init__(self, name=name, full_name=name,
                              macro_server=macro_server,
                              elem_type=ElementType.ParameterType)

    def getName(self):
        return self.name

    def getObj(self, str_repr):
        return self.type_class(str_repr)

    @classmethod
    def hasCapability(cls, cap):
        return cap in cls.capabilities

    def serialize(self, *args, **kwargs):
        kwargs = MSBaseObject.serialize(self, *args, **kwargs)
        kwargs['composed'] = False
        return kwargs


class ParamRepeat(object):
    # opts: min, max
    def __init__(self, *param_def, **opts):
        self.param_def = param_def
        self.opts = {'min': 1, 'max': None}
        self.opts.update(opts)
        self._obj = list(param_def)
        self._obj.append(self.opts)

    def items(self):
        return self.opts.items()

    def __getattr__(self, name):
        return self.opts[name]

    def obj(self):
        return self._obj


class ElementParamType(ParamType):

    capabilities = ParamType.ItemList, ParamType.ItemListEvents

    def __init__(self, macro_server, name):
        ParamType.__init__(self, macro_server, name)

    def accepts(self, elem):
        return elem.getType() == self._name

    def getObj(self, name, pool=ParamType.All, cache=False):
        macro_server = self.macro_server
        if pool == ParamType.All:
            pools = macro_server.get_pools()
        else:
            pools = macro_server.get_pool(pool),
        for pool in pools:
            elem_info = pool.getObj(name, elem_type=self._name)
            if elem_info is not None and self.accepts(elem_info):
                return elem_info
        # not a pool object, maybe it is a macro server object (perhaps a macro
        # code or a macro library
        try:
            return macro_server.get_macro(name)
        except UnknownMacro:
            pass

        try:
            return macro_server.get_macro_lib(name)
        except UnknownMacroLibrary:
            pass
        # neither pool nor macroserver contains any element with this name
        raise UnknownParamObj('%s with name %s does not exist' % \
                              (self._name, name))

    def getObjDict(self, pool=ParamType.All, cache=False):
        macro_server = self.macro_server
        objs = CaselessDict()
        if pool == ParamType.All:
            pools = macro_server.get_pools()
        else:
            pools = macro_server.get_pool(pool),
        for pool in pools:
            for elem_info in pool.getElements():
                if self.accepts(elem_info):
                    objs[elem_info.name] = elem_info
        for macro_lib_name, macro_lib in macro_server.get_macros().items():
            if self.accepts(macro_lib):
                objs[macro_lib_name] = macro_lib
        for macro_name, macro in macro_server.get_macros().items():
            if self.accepts(macro):
                objs[macro_name] = macro

        return objs

    def getObjListStr(self, pool=ParamType.All, cache=False):
        obj_dict = self.getObjDict(pool=pool, cache=cache)
        return obj_dict.keys()

    def getObjList(self, pool=ParamType.All, cache=False):
        obj_dict = self.getObjDict(pool=pool, cache=cache)
        return obj_dict.values()

    def serialize(self, *args, **kwargs):
        kwargs = ParamType.serialize(self, *args, **kwargs)
        kwargs['composed'] = True
        return kwargs


class ElementParamInterface(ElementParamType):

    def __init__(self, macro_server, name):
        ElementParamType.__init__(self, macro_server, name)
        bases, doc = INTERFACES_EXPANDED.get(name)
        self._interfaces = bases

    def accepts(self, elem):
        elem_type = elem.getType()
        elem_interfaces = INTERFACES_EXPANDED.get(elem_type)[0]
        if elem_interfaces is None:
            return ElementParamType.accepts(self, elem)
        return self._name in elem_interfaces

    def getObj(self, name, pool=ParamType.All, cache=False):
        macro_server = self.macro_server
        if pool == ParamType.All:
            pools = macro_server.get_pools()
        else:
            pools = macro_server.get_pool(pool),
        for pool in pools:
            elem_info = pool.getElementWithInterface(name, self._name)
            if elem_info is not None and self.accepts(elem_info):
                return elem_info
        # not a pool object, maybe it is a macro server object (perhaps a macro
        # class or a macro library
        try:
            return macro_server.get_macro(name)
        except UnknownMacro:
            pass

        try:
            return macro_server.get_macro_lib(name)
        except UnknownMacroLibrary:
            pass
        # neither pool nor macroserver contains any element with this name
        raise UnknownParamObj('%s with name %s does not exist' % \
                              (self._name, name))

    def getObjDict(self, pool=ParamType.All, cache=False):
        macro_server = self.macro_server
        objs = CaselessDict()
        if macro_server.is_macroserver_interface(self._name):
            return macro_server.get_elements_with_interface(self._name)

        if pool == ParamType.All:
            pools = macro_server.get_pools()
        else:
            pools = macro_server.get_pool(pool),
        for pool in pools:
            for elem_info in pool.getElementsWithInterface(self._name).values():
                if self.accepts(elem_info):
                    objs[elem_info.name] = elem_info
        return objs

    def getObjListStr(self, pool=ParamType.All, cache=False):
        obj_dict = self.getObjDict(pool=pool, cache=cache)
        return obj_dict.keys()

    def getObjList(self, pool=ParamType.All, cache=False):
        obj_dict = self.getObjDict(pool=pool, cache=cache)
        return obj_dict.values()


class AttrParamType(ParamType):
    pass


AbstractParamTypes = ParamType, ElementParamType, ElementParamInterface, AttrParamType


class ParamDecoder:

    def __init__(self, type_manager, params_def, raw_params):
        """Create ParamDecorder object and decode macro parameters

        :param type_manager: (sardana.macroserver.mstypemanager.TypeManager)
            type manager object
        :param params_def: list<list> macro parameter definition
        :param raw_params: (lxml.etree._Element or list) xml element
            representing macro with subelements representing parameters or list
            with parameter values
        """
        self.type_manager = type_manager
        self.params_def = params_def
        self.raw_params = raw_params
        self.params = None
        self.decode()

    def decode(self):
        """Decode raw representation of parameters to parameters as passed
        to the prepare or run methods.
        """
        # make a copy since in case of XML it could be necessary to modify
        # the raw_params - filter out elements different than params
        raw_params = deepcopy(self.raw_params)
        params_def = self.params_def
        # ignore other tags than "param" and "paramRepeat"
        # e.g. sequencer may create tags like "hookPlace"
        if isinstance(raw_params, etree._Element):
            for raw_param in raw_params:
                if not raw_param.tag in ("param", "paramrepeat"):
                    raw_params.remove(raw_param)

        params = []
        # check if too many parameters were passed
        len_params_def = len(params_def)
        if len(raw_params) > len_params_def:
            msg = ("%r are supernumerary with respect to definition" %
                   raw_params[len_params_def:])
            raise SupernumeraryParam, msg
        # iterate over definition since missing values may just mean using
        # the default values
        for i, param_def in enumerate(params_def):
            try:
                raw_param = raw_params[i]
            except IndexError:
                raw_param = None
            obj = self.decodeNormal(raw_param, param_def)
            params.append(obj)
        self.params = params
        return self.params

    def decodeNormal(self, raw_param, param_def):
        """Decode and validate parameter

        :param raw_param: (lxml.etree._Element or list) xml element
            representing parameter
        :param param_def: (dict) parameter definition

        :return: (list): list with decoded parameter repetitions
        """
        param_type = param_def["type"]
        name = param_def["name"]
        if isinstance(param_type, list):
            param = self.decodeRepeat(raw_param, param_def)
        else:
            type_manager = self.type_manager
            param_type = type_manager.getTypeObj(param_type)
            try:
                if isinstance(raw_param, etree._Element):
                    value = raw_param.get("value")
                else:
                    value = raw_param
                if value is None:
                    value = param_def['default_value']
                if value is None:
                    raise MissingParam, "'%s' not specified" % name
                else:
                    # cast to sting to fulfill with ParamType API
                    value = str(value)
                param = param_type.getObj(value)
            except ValueError, e:
                raise WrongParamType, e.message
            except UnknownParamObj, e:
                raise WrongParam, e.message
            if param is None:
                msg = 'Could not create %s parameter "%s" for "%s"' % \
                      (param_type.getName(), name, raw_param)
                raise WrongParam, msg
        return param

    def decodeRepeat(self, raw_param_repeat, param_repeat_def):
        """Decode and validate repeat parameter

        :param raw_param_repeat: (lxml.etree._Element or list) xml element
            representing param repeat with subelements representing repetitions
            or list representing repetitions
        :param param_repeat_def: (dict) repeat parameter definition

        :return: (list): list with decoded parameter repetitions
        """
        name = param_repeat_def['name']
        param_type = param_repeat_def['type']
        min_rep = param_repeat_def['min']
        max_rep = param_repeat_def['max']
        param_repeat = []
        if raw_param_repeat is None:
            raw_param_repeat = param_repeat_def['default_value']
        if raw_param_repeat is None:
            raw_param_repeat = []
        len_rep = len(raw_param_repeat)
        if min_rep and len_rep < min_rep:
            msg = 'Found %d repetitions of param %s, min is %d' % \
                  (len_rep, name, min_rep)
            raise MissingRepeat, msg
        if  max_rep and len_rep > max_rep:
            msg = 'Found %d repetitions of param %s, max is %d' % \
                  (len_rep, name, max_rep)
            raise SupernumeraryRepeat, msg
        for raw_repeat in raw_param_repeat:
            if len(param_type) > 1:
                repeat = []
                for i, member_raw in enumerate(raw_repeat):
                    member_type = param_type[i]
                    member = self.decodeNormal(member_raw, member_type)
                    repeat.append(member)
            else:
                # if the repeat parameter is composed of just one member
                # do not encapsulate it in list and pass directly the item
                if isinstance(raw_repeat, etree._Element):
                    raw_repeat = raw_repeat[0]
                repeat = self.decodeNormal(raw_repeat, param_type[0])
            param_repeat.append(repeat)
        return param_repeat

    def getParamList(self):
        return self.params

    def __getattr__(self, name):
        return getattr(self.params, name)


class FlatParamDecoder:
    """Parameter decoder useful for macros with only one repeat parameter
    located at the very last place. It requires that the raw parameters are
    passed as a flat list of strings.
    """
    def __init__(self, type_manager, params_def, raw_params):
        self.type_manager = type_manager
        self.params_def = params_def
        self.raw_params = raw_params
        self.params = None
        if not self.isPossible(params_def):
            msg = ("%s parameter definition is not compatible with"
                   " FlatParamDecoder" % params_def)
            raise AttributeError, msg
        self.decode()

    @staticmethod
    def isPossible(params_def):
        for param_def in params_def:
            param_type = param_def["type"]
            if isinstance(param_type, list):
                if param_def != params_def[-1]:
                    # repeat parameter is not the last one
                    # it won't be possible to decode it
                    return False
                else:
                    for sub_param_def in param_type:
                        if isinstance(sub_param_def, list):
                            # nested repeat parameter
                            # it won't be possible to decode it
                            return False
        return True

    def decode(self):
        params_def = self.params_def
        raw_params = self.raw_params
        _, self.params = self.decodeNormal(raw_params, params_def)
        return self.params

    def decodeNormal(self, raw_params, params_def):
        str_len = len(raw_params)
        obj_list = []
        str_idx = 0
        for i, par_def in enumerate(params_def):
            name = par_def['name']
            type_class = par_def['type']
            def_val = par_def['default_value']
            if str_idx == str_len:
                if def_val is None:
                    if not isinstance(type_class, list):
                        raise MissingParam, "'%s' not specified" % name
                    elif isinstance(type_class, list):
                        min_rep = par_def['min']
                        if min_rep > 0:
                            msg = "'%s' demands at least %d values" %\
                                  (name, min_rep)
                            raise WrongParam, msg
                if not def_val is None:
                    new_obj = def_val
            else:
                if isinstance(type_class, list):
                    data = self.decodeRepeat(raw_params[str_idx:], par_def)
                    dec_token, new_obj = data
                else:
                    type_manager = self.type_manager
                    type_name = type_class
                    type_class = type_manager.getTypeClass(type_name)
                    par_type = type_manager.getTypeObj(type_name)
                    par_str = raw_params[str_idx]
                    try:
                        val = par_type.getObj(par_str)
                    except ValueError, e:
                        raise WrongParamType, e.message
                    except UnknownParamObj, e:
                        raise WrongParam, e.message
                    if val is None:
                        msg = 'Could not create %s parameter "%s" for "%s"' % \
                              (par_type.getName(), name, par_str)
                        raise WrongParam, msg
                    dec_token = 1
                    new_obj = val
                str_idx += dec_token
            obj_list.append(new_obj)
        return str_idx, obj_list

    def decodeRepeat(self, raw_params, par_def):
        name = par_def['name']
        param_def = par_def['type']
        min_rep = par_def['min']
        max_rep = par_def['max']

        dec_token = 0
        obj_list = []
        rep_nr = 0
        while dec_token < len(raw_params):
            if max_rep is not None and rep_nr == max_rep:
                break
            new_token, new_obj_list = self.decodeNormal(raw_params[dec_token:],
                                                        param_def)
            dec_token += new_token
            if len(new_obj_list) == 1:
                new_obj_list = new_obj_list[0]
            obj_list.append(new_obj_list)
            rep_nr += 1
        if rep_nr < min_rep:
            msg = 'Found %d repetitions of param %s, min is %d' % \
                  (rep_nr, name, min_rep)
            raise MissingRepeat, msg
        return dec_token, obj_list

    def getParamList(self):
        return self.params

    def __getattr__(self, name):
        return getattr(self.params, name)
