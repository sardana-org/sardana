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

""" """

__docformat__ = 'restructuredtext'

__all__ = ["get_tango_version_str", "get_tango_version_number",
           "get_pytango_version_str", "get_pytango_version_number",
           "exception_str",
           "GenericScalarAttr", "GenericSpectrumAttr", "GenericImageAttr",
           "memorize_write_attribute",
           "tango_protect", "to_tango_state", "to_tango_type_format",
           "to_tango_access", "to_tango_attr_info",
           "from_tango_access", "from_tango_type_format",
           "from_tango_state_to_state",
           "from_deviceattribute_value", "from_deviceattribute",
           "throw_sardana_exception",
           "prepare_logging", "prepare_rconsole", "run_tango_server",
           "run"]

import sys
import time
import string
import logging
import os.path
import traceback
import itertools

import PyTango
from PyTango import Util, Database, WAttribute, DbDevInfo, DevFailed, \
    DevVoid, DevLong64, DevBoolean, DevString, DevDouble, \
    DevState, SCALAR, SPECTRUM, IMAGE, FMT_UNKNOWN, \
    READ_WRITE, READ, Attr, SpectrumAttr, ImageAttr, \
    DeviceClass, Except

import taurus
from taurus.core.util.log import Logger

import sardana
from sardana import State, SardanaServer, DataType, DataFormat, InvalidId, \
    DataAccess, to_dtype_dformat, to_daccess, Release, ServerRunMode, \
    AttrQuality
from sardana.sardanaexception import SardanaException, AbortException
from sardana.sardanavalue import SardanaValue
from sardana.util.wrap import wraps
from sardana.pool.poolmetacontroller import DataInfo


NO_DB_MAP = {
    "Pool": (
        ("pool_demo", "sardana/pool/demo", dict(Version="1.0.0"),),
    ),
    "Controller": (
        ("motctrl", "controller/dummymotorcontroller/motctrl",
         dict(Id=1, Type="Motor", Klass="DummyMotorController",
              Library="DummyMotorController.py", Role_ids=(),),),
        ("iorctrl", "controller/dummyiorcontroller/iorctrl",
         dict(Id=2, Type="IORegister", Klass="DummyIORController",
              Library="DummyIORController.py", Role_ids=(),),),
        ("ctctrl", "controller/dummycountertimercontroller/ctctrl",
         dict(Id=3, Type="CTExpChannel", Klass="DummyCounterTimerController",
              Library="DummyCounterTimerController.py", Role_ids=(),),),
        ("zerodctrl", "controller/dummyzerodcontroller/zerodctrl",
         dict(Id=4, Type="ZeroDExpChannel", Klass="DummyZeroDController",
              Library="DummyZeroDController.py", Role_ids=(),),),
        ("slitctrl", "controller/slit/slitctrl",
         dict(Id=5, Type="PseudoMotor", Klass="Slit",
              Library="Slit.py", Role_ids=(),),),
        ("ioi0ctrl", "controller/ioveri0/ioi0ctrl",
         dict(Id=6, Type="PseudoCounter", Klass="IoverI0",
              Library="IoverI0.py", Role_ids=(),),),
    ),
    "Motor": (
        ("slt", "motor/motctrl/1", dict(Id=101, Axis=1, Ctrl_id=1,
                                        Instrument_id=InvalidId,
                                        Sleep_bef_last_read=0),),
        ("slb", "motor/motctrl/2", dict(Id=102, Axis=2, Ctrl_id=1,
                                        Instrument_id=InvalidId,
                                        Sleep_bef_last_read=0),),
        ("mot1", "motor/motctrl/3", dict(Id=103, Axis=3, Ctrl_id=1,
                                         Instrument_id=InvalidId,
                                         Sleep_bef_last_read=0),),
        ("mot2", "motor/motctrl/4", dict(Id=104, Axis=4, Ctrl_id=1,
                                         Instrument_id=InvalidId,
                                         Sleep_bef_last_read=0),),
        ("mot3", "motor/motctrl/5", dict(Id=105, Axis=5, Ctrl_id=1,
                                         Instrument_id=InvalidId,
                                         Sleep_bef_last_read=0),),
        ("mot4", "motor/motctrl/6", dict(Id=106, Axis=6, Ctrl_id=1,
                                         Instrument_id=InvalidId,
                                         Sleep_bef_last_read=0),),
        ("th", "motor/motctrl/7", dict(Id=107, Axis=7, Ctrl_id=1,
                                       Instrument_id=InvalidId,
                                       Sleep_bef_last_read=0),),
        ("tth", "motor/motctrl/8", dict(Id=108, Axis=8, Ctrl_id=1,
                                        Instrument_id=InvalidId,
                                        Sleep_bef_last_read=0),),
        ("chi", "motor/motctrl/9", dict(Id=109, Axis=9, Ctrl_id=1,
                                        Instrument_id=InvalidId,
                                        Sleep_bef_last_read=0),),
        ("phi", "motor/motctrl/10", dict(Id=110, Axis=10, Ctrl_id=1,
                                         Instrument_id=InvalidId,
                                         Sleep_bef_last_read=0),),
    ),
    "IORegister": (
        ("ior1", "ioregister/iorctrl/1", dict(Id=201,
                                              Axis=1, Ctrl_id=2,
                                              Instrument_id=InvalidId),),
        ("ior2", "ioregister/iorctrl/2", dict(Id=202,
                                              Axis=2, Ctrl_id=2,
                                              Instrument_id=InvalidId),),
        ("ior3", "ioregister/iorctrl/3", dict(Id=203,
                                              Axis=3, Ctrl_id=2,
                                              Instrument_id=InvalidId),),
        ("ior4", "ioregister/iorctrl/4", dict(Id=204,
                                              Axis=4, Ctrl_id=2,
                                              Instrument_id=InvalidId),),
    ),
    "CTExpChannel": (
        ("ct1", "expchan/ctctrl/1", dict(Id=301,
                                         Axis=1, Ctrl_id=3,
                                         Instrument_id=InvalidId),),
        ("ct2", "expchan/ctctrl/2", dict(Id=302,
                                         Axis=2, Ctrl_id=3,
                                         Instrument_id=InvalidId),),
        ("ct3", "expchan/ctctrl/3", dict(Id=303,
                                         Axis=3, Ctrl_id=3,
                                         Instrument_id=InvalidId),),
        ("ct4", "expchan/ctctrl/4", dict(Id=304,
                                         Axis=4, Ctrl_id=3,
                                         Instrument_id=InvalidId),),
    ),
    "ZeroDExpChannel": (
        ("zerod1", "expchan/zerodctrl/1", dict(Id=401,
                                               Axis=1, Ctrl_id=4,
                                               Instrument_id=InvalidId),),
        ("zerod2", "expchan/zerodctrl/2", dict(Id=402,
                                               Axis=2, Ctrl_id=4,
                                               Instrument_id=InvalidId),),
        ("zerod3", "expchan/zerodctrl/3", dict(Id=403,
                                               Axis=3, Ctrl_id=4,
                                               Instrument_id=InvalidId),),
        ("zerod4", "expchan/zerodctrl/4", dict(Id=404,
                                               Axis=4, Ctrl_id=4,
                                               Instrument_id=InvalidId),),
    ),
    "PseudoMotor": (
        ("gap", "pm/slitctrl/1", dict(Id=501, Axis=1, Ctrl_id=5,
                                      Instrument_id=InvalidId,
                                      Elements=("101", "102",)),),
        ("offset", "pm/slitctrl/2", dict(Id=502, Axis=2, Ctrl_id=5,
                                         Instrument_id=InvalidId,
                                         Elements=("101", "102",)),),
    ),
    "PseudoCounter": (
        ("inorm", "pc/ioi0ctrl/1", dict(Id=601, Axis=1, Ctrl_id=6,
                                        Instrument_id=InvalidId,
                                        Elements=("301", "302",)),),
    ),
    "MotorGroup": (
        ("motgrp1", "mg/pool_demo/motgrp1",
         dict(Id=701, Elements=("103", "104",)),),
    ),
    "MeasurementGroup": (
        ("mntgrp1", "mntgrp/pool_demo/mntgrp1",
         dict(Id=701, Elements=("301", "302", "303", "401",)),),
    ),
    "MacroServer": (
        ("MS_demo", "sardana/ms/demo", dict(PoolNames=["sardana/pool/demo"]),),
    ),
    "Door": (
        ("Door_demo", "sardana/door/demo",
         dict(Id=1001, MacroServerName="sardana/ms/demo",
              MaxMsgBufferSize=512),),
    ),
}

# -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~
# PyTango utilities
# -~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~


def get_pytango_version_str():
    try:
        import PyTango
    except:
        return None
    try:
        return PyTango.Release.version
    except:
        return '0.0.0'


def get_pytango_version_number():
    tgver_str = get_pytango_version_str()
    if tgver_str is None:
        return None
    import sardana.sardanautils
    return sardana.sardanautils.translate_version_str2int(tgver_str)


def get_tango_version_str():
    try:
        import PyTango.constants
    except:
        return None
    try:
        return PyTango.constants.TgLibVers
    except:
        return '0.0.0'


def get_tango_version_number():
    tgver_str = get_tango_version_str()
    if tgver_str is None:
        return None
    import sardana.sardanautils
    return sardana.sardanautils.translate_version_str2int(tgver_str)


class GenericScalarAttr(Attr):
    pass


class GenericSpectrumAttr(SpectrumAttr):

    def __init__(self, name, tg_type, tg_access, dim_x=2048):
        SpectrumAttr.__init__(self, name, tg_type, tg_access, dim_x)


class GenericImageAttr(ImageAttr):

    def __init__(self, name, tg_type, tg_access, dim_x=2048, dim_y=2048):
        ImageAttr.__init__(self, name, tg_type, tg_access, dim_x, dim_y)


def clean_device_attribute_memorized(db, dev_name, attr_name):
    props = "__value", "__value_ts"
    db.delete_device_attribute_property(dev_name, {attr_name: props})


def clean_device_memorized(db, dev_name):
    for attr_name in PyTango.DeviceProxy(dev_name).get_attribute_list():
        clean_device_attribute_memorized(db, dev_name, attr_name)


def clean_server_memorized(db, server_name, server_instance):
    server = server_name + "/" + server_instance
    dev_names = db.get_device_class_list(server)[::2]
    for dev_name in dev_names:
        clean_device_memorized(db, dev_name)


def __set_last_write_value(attribute, lrv):
    attribute._last_write_value = lrv
    return lrv


def __get_last_write_value(attribute):
    if hasattr(attribute, '_last_write_value'):
        lrv = attribute._last_write_value
    else:
        attribute._last_write_value = lrv = None
    return lrv


def _check_attr_range(dev_name, attr_name, attr_value):
    util = PyTango.Util.instance()
    dev = util.get_device_by_name(dev_name)
    multi_attr = dev.get_device_attr()
    attr = multi_attr.get_w_attr_by_name(attr_name)
    try:
        min_value = attr.get_min_value()
    # not specified min value raises DevFailed
    except PyTango.DevFailed:
        pass
    else:
        if attr_value < min_value:
            msg = "w_value {} of {}/{} is lower than min_value {}".format(
                  attr_value, dev_name, attr_name, min_value)
            raise ValueError(msg)
    try:
        max_value = attr.get_max_value()
    # not specified max value raises DevFailed
    except PyTango.DevFailed:
        pass
    else:
        if attr_value > max_value:
            msg = "w_value {} of {}/{} is greater than max_value {}".format(
                  attr_value, dev_name, attr_name, max_value)
            raise ValueError(msg)


def memorize_write_attribute(write_attr_func):
    """The main purpose is to use this as a decorator for write_<attr_name>
       device methods.

       Properly memorizes the attribute write value:

           - only memorize if write doesn't throw exception
           - also memorize the timestamp

       :param write_attr_func: the write method
       :type write_attr_func: callable
       :return: a write method safely wrapping the given write method
       :rtype: callable"""

    @wraps(write_attr_func)
    def write_attr_wrapper(self, attribute):
        ts = repr(time.time())
        attr_name = attribute.get_name()
        dev_name = self.get_name()

        if not isinstance(attribute, WAttribute):
            return write_attr_func(self, attribute)

        lwv = __get_last_write_value(attribute)
        wv = attribute.get_write_value(), ts
        store, raises_exc = wv, True
        store_value = False
        try:
            ret = write_attr_func(self, attribute)
            __set_last_write_value(attribute, wv)
            raises_exc = False
        finally:
            # if there is an exception recover from the last write value.
            # (don't catch and raise exceptions to avoid messing up the stack)
            if raises_exc:
                store_value = True
                if lwv is not None:
                    store = lwv
        if store is not None:
            db = self.get_database()
            attr_values = dict(__value_ts=store[1])
            if store_value:
                attr_values['__value'] = store[0]
            db.put_device_attribute_property(
                dev_name, {attr_name: attr_values})
        return ret

    return write_attr_wrapper


def tango_protect(wrapped, *args, **kwargs):
    @wraps(wrapped)
    def wrapper(self, *args, **kwargs):
        with self.tango_lock:
            return wrapped(self, *args, **kwargs)
    return wrapper


def from_deviceattribute_value(da):
    if da.has_failed:
        return
    dtype, dformat, value = da.type, da.data_format, da.value
    if dtype == PyTango.DevState:
        if dformat == PyTango.SCALAR:
            return from_tango_state_to_state(value)
        elif dformat == PyTango.SPECTRUM:
            return list(map(from_tango_state_to_state, value))
        elif dformat == PyTango.IMAGE:
            return [list(map(from_tango_state_to_state, v)) for v in value]
    return value


def from_deviceattribute(da):
    if da.has_failed:
        exc_info = DevFailed(*da.get_err_stack())
        value = None
    else:
        exc_info = None
        value = from_deviceattribute_value(da.value)

    dtype, dformat = from_tango_type_format(da.type, da.data_format)

    ret = SardanaValue(value=value, exc_info=exc_info,
                       timestamp=da.time.totime(), dtype=dtype,
                       dformat=dformat)
    return ret


def to_tango_state(state):
    return DevState(state)


def from_tango_state_to_state(state):
    return int(state)


#: dictionary dict<:class:`sardana.DataType`, :class:`PyTango.CmdArgType`>
TTYPE_MAP = {
    DataType.Integer: DevLong64,
    DataType.Double: DevDouble,
    DataType.String: DevString,
    DataType.Boolean: DevBoolean,
}
R_TTYPE_MAP = dict((v, k) for k, v in list(TTYPE_MAP.items()))

#: dictionary dict<:class:`sardana.DataFormat`, :class:`PyTango.AttrFormat`>
TFORMAT_MAP = {
    DataFormat.Scalar: SCALAR,
    DataFormat.OneD: SPECTRUM,
    DataFormat.TwoD: IMAGE,
}
R_TFORMAT_MAP = dict((v, k) for k, v in list(TFORMAT_MAP.items()))


#: dictionary dict<:class:`sardana.AttrQuality`, :class:`PyTango.AttrQuality`>
TQUALITY_MAP = {
    AttrQuality.Valid: PyTango.AttrQuality.ATTR_VALID,
    AttrQuality.Invalid: PyTango.AttrQuality.ATTR_INVALID,
    AttrQuality.Alarm: PyTango.AttrQuality.ATTR_ALARM,
    AttrQuality.Changing: PyTango.AttrQuality.ATTR_CHANGING,
    AttrQuality.Warning: PyTango.AttrQuality.ATTR_WARNING
}


R_TQUALITY_MAP = dict((v, k) for k, v in list(TQUALITY_MAP.items()))


#: dictionary dict<:class:`sardana.AttrQuality`, :class:`PyTango.AttrQuality`>
TACCESS_MAP = {
    DataAccess.ReadOnly: READ,
    DataAccess.ReadWrite: READ_WRITE,
}

R_TACCESS_MAP = dict((v, k) for k, v in list(TACCESS_MAP.items()))

def exception_str(etype=None, value=None, sep='\n'):
    if etype is None:
        etype, value = sys.exc_info()[:2]
    return sep.join(traceback.format_exception_only(etype, value))


def to_tango_access(access):
    """Transforms a :obj:`~sardana.DataAccess` into a
    :obj:`~PyTango.AttrWriteType`

    :param access: the access to be transformed
    :type access: :obj:`~sardana.DataAccess`
    :return: the tango attribute write type
    :rtype: :obj:`PyTango.AttrWriteType`"""
    return TACCESS_MAP[access]


def from_tango_access(access):
    """Transforms a :obj:`~PyTango.AttrWriteType` into a
    :obj:`~sardana.DataAccess`

    :param access: the tango access to be transformed
    :type access: :obj:`~PyTango.AttrWriteType`
    :return: the sardana attribute write type
    :rtype: :obj:`~sardana.DataAccess`"""
    return R_TACCESS_MAP[access]


def to_tango_type_format(dtype_or_info, dformat=None):
    """Transforms a :obj:`~sardana.DataType` :obj:`~sardana.DataFormat` into a
    :obj:`~PyTango.CmdArgType`, :obj:`~PyTango.AttrDataFormat` tuple

    :param dtype_or_info: the type to be transformed
    :type dtype_or_info: :obj:`~sardana.DataType`
    :param dformat: the format to be transformed
    :type dformat: :obj:`~sardana.DataFormat`

    :return: a tuple of two elements: the tango attribute write type,
    tango data format
    :rtype: tuple< :obj:`PyTango.CmdArgType`, :obj:`PyTango.AttrDataFormat`>"""
    dtype = dtype_or_info
    if dformat is None:
        dtype, dformat = to_dtype_dformat(dtype)
    return TTYPE_MAP.get(dtype, DevVoid), TFORMAT_MAP.get(dformat, FMT_UNKNOWN)


def from_tango_type_format(dtype, dformat=PyTango.SCALAR):
    """Transforms a :obj:`~PyTango.CmdArgType`, :obj:`~PyTango.AttrDataFormat`
    into a :obj:`~sardana.DataType` :obj:`~sardana.DataFormat` tuple

    :param dtype: the type to be transformed
    :type dtype: :obj:`~PyTango.CmdArgType`
    :param dformat: the format to be transformed
    :type dformat: :obj:`~PyTango.AttrDataFormat`

    :return: a tuple of two elements: data type, data format
    :rtype: tuple< :obj:`~sardana.DataType`, :obj:`~sardana.DataFormat` >"""
    return R_TTYPE_MAP[dtype], R_TFORMAT_MAP[dformat]


def to_tango_quality(quality):
    """Transforms a :obj:`~sardana.AttrQuality` into a
    :obj:`~PyTango.AttrQuality`

    :param access: the quality to be transformed
    :type access: :obj:`~sardana.AttrQuality`
    :return: the tango attribute quality
    :rtype: :obj:`PyTango.AttrQuality`"""
    return TQUALITY_MAP[quality]

def to_tango_attr_info(attr_name, attr_info):
    if isinstance(attr_info, DataInfo):
        data_type, data_format = attr_info.dtype, attr_info.dformat
        data_access = attr_info.access
        desc = attr_info.description
        memorized = attr_info.memorized
    else:
        data_type, data_format = to_dtype_dformat(attr_info.get('type'))
        data_access = to_daccess(attr_info.get('r/w type'))
        desc = attr_info.get('description')
        memorized = attr_info.get('memorized')

    tg_type, tg_format = to_tango_type_format(data_type, data_format)
    tg_access = to_tango_access(data_access)
    tg_attr_info = [[tg_type, tg_format, tg_access]]

    extra = {}
    tg_attr_info.append(extra)

    if desc is not None and len(desc) > 0:
        extra['description'] = desc
    extra['memorized'] = memorized
    return attr_name, tg_attr_info


def throw_sardana_exception(exc):
    """Throws an exception as a tango exception"""
    if isinstance(exc, SardanaException):
        if exc.exc_info and None not in exc.exc_info:
            Except.throw_python_exception(*exc.exc_info)
        else:
            tb = "<Unknown>"
            if exc.traceback is not None:
                tb = str(exc.traceback)
            Except.throw_exception(exc.type, exc.msg, tb)
    elif hasattr(exc, 'exc_info'):
        Except.throw_python_exception(*exc.exc_info)
    else:
        raise exc


def ask_yes_no(prompt, default=None):
    """Asks a question and returns a boolean (y/n) answer.

    If default is given (one of 'y','n'), it is used if the user input is
    empty. Otherwise the question is repeated until an answer is given.

    An EOF is treated as the default answer.  If there is no default, an
    exception is raised to prevent infinite loops.

    Valid answers are: y/yes/n/no (match is not case sensitive)."""
    answers = {'y': True, 'n': False, 'yes': True, 'no': False}
    ans = None
    if default is not None:
        d_l = default.lower()
        if d_l in ('y', 'yes'):
            prompt += " (Y/n) ?"
        elif d_l in ('n', 'no'):
            prompt += " (N/y) ?"

    while ans not in list(answers.keys()):
        try:
            ans = input(prompt + ' ').lower()
            if not ans:  # response was an empty string
                ans = default
        except KeyboardInterrupt:
            print()
        except EOFError:
            if default in list(answers.keys()):
                ans = default
                print()
            else:
                raise

    return answers[ans]


def clean_tango_args(args):
    ret, ret_for_tango, ret_for_ORB = [], [], []

    tango_args = "-?", "-nodb", "-file="
    nb_args = len(args)
    i = 0
    while i < nb_args:
        arg = args[i]
        try:
            if arg.startswith("-v") and int(arg[2:]):
                ret_for_tango.append(arg)
                i += 1
                continue
        except:
            pass
        if arg.startswith('-ORB'):
            ret_for_ORB.append(arg)
            ret_for_tango.append(arg)
            i += 1
            if i < nb_args:
                ret_for_ORB.append(args[i])
                ret_for_tango.append(args[i])
                i += 1
            continue
        if arg.startswith(tango_args):
            ret_for_tango.append(arg)
            i += 1
            continue
        if arg == "-dlist":
            ret_for_tango.append(arg)
            i += 1
            while i < nb_args and args[i][0] != "-":
                arg = args[i]
                ret_for_tango.append(arg)
                i += 1
            continue
        ret.append(arg)
        i += 1
    return ret, ret_for_tango, ret_for_ORB


def prepare_cmdline(parser=None, args=None):
    """Prepares the command line separating tango options from server specific
    options.

    :return: a sequence of options, arguments, tango arguments
    :rtype: seq<opt, list<str>, list<str>>"""
    import optparse
    if args is None:
        args = []

    proc_args, tango_args, ORB_args = clean_tango_args(args)

    if parser is None:
        version = "%s" % (Release.version)
        parser = optparse.OptionParser(version=version)

    parser.usage = "usage: %prog instance_name [options]"
    log_level_choices = "critical", "error", "warning", "info", "debug", \
                        "trace", "0", "1", "2", "3", "4", "5"
    help_olog = "log output level. Possible values are (case sensitive): " \
                "critical (or 0), error (1), warning (2), info (3) " \
                "debug (4), trace (5) [default: %default]"
    help_flog = "log file level. Possible values are (case sensitive): " \
                "critical (or 0), error (1), warning (2), info (3) " \
                "debug (4), trace (5) [default: %default]. " \
                "Ignored if --without-log-file is True"
    help_fnlog = "log file name. When given, MUST be absolute file name. " \
        "[default: /tmp/tango/<DS name>/<DS instance name lower " \
                 "case>/log.txt]. Ignored if --without-log-file is True"
    help_wflog = "When set to True disables logging into a file [default: " \
                 "%default]"
    help_rfoo = "rconsole port number. [default: %default meaning rconsole " \
                "NOT active]"
    parser.add_option("--log-level", dest="log_level", metavar="LOG_LEVEL",
                      help=help_olog, type="choice",
                      choices=log_level_choices, default="warning")
    parser.add_option("--log-file-level", dest="log_file_level",
                      metavar="LOG_FILE_LEVEL", help=help_flog,
                      type="choice", choices=log_level_choices,
                      default="debug")
    parser.add_option("--log-file-name", dest="log_file_name",
                      help=help_fnlog, type="str", default=None)
    parser.add_option("--without-log-file", dest="without_log_file",
                      help=help_wflog, default=False)

    parser.add_option("--rconsole-port", dest="rconsole_port",
                      metavar="RCONSOLE_PORT", help=help_rfoo, type="int",
                      default=0)

    res = list(parser.parse_args(proc_args))
    tango_args = res[1][:2] + tango_args
    res.append(tango_args)
    res.append(ORB_args)
    return res


def prepare_ORBendPoint(args, tango_args):
    """Try to get Tango *free property* (object name: ``ORBendPoint``,
    property name: ``<server_name>/<instance_name>``) and set it via
    environment variable only in two occasions:

    - this one was not existing
    - ``-ORBendPoint`` argument was not passed
    """
    log_messages = []
    server_name = args[0]
    try:
        instance_name = args[1]
    except IndexError:
        msg = ("Unknown %s instance name. " % server_name
               + "Skipping ORBendPoint from free property configuration...")
        log_messages.append(msg, )
        return log_messages
    env_name = "ORBendPoint"
    if env_name in os.environ:
        return log_messages
    arg_name = "-" + env_name
    if arg_name in tango_args:
        return log_messages
    db = PyTango.Database()
    property_name = server_name + "/" + instance_name
    env_val = get_free_property(db, env_name, property_name)
    if env_val is not None:
        os.environ[env_name] = env_val
        log_messages.append(("setting %s=%s from Tango DB free property",
                             env_name, env_val))
    return log_messages


def prepare_environment(args, tango_args, ORB_args):
    """Since we have to create a Tango Database object before the Tango Util,
    omniORB doesn't recognize parameters on the command line anymore
    (ORB singleton did not receive cmd args), so we export these parameters as
    environment variables (this workaround seems to work). For Tango >=
    8.0.5 it is not necessary anymore.
    More details in: https://sourceforge.net/p/tango-cs/bugs/495/
    """
    log_messages = []
    ORB_args_len = len(ORB_args)
    for i in range(ORB_args_len):
        arg = ORB_args[i]
        if arg.startswith("-ORB") and i + 1 < ORB_args_len:
            env_name = arg[1:]
            env_val = ORB_args[i + 1]
            os.environ[env_name] = env_val
            log_messages.append(("setting %s=%s", env_name, env_val))
    return log_messages


def prepare_server(args, tango_args):
    """Register a proper server if the user gave an unknown server"""
    log_messages = []
    _, bin_name = os.path.split(args[0])
    server_name, _ = os.path.splitext(bin_name)

    if "-?" in tango_args:
        return log_messages

    nodb = "-nodb" in tango_args
    if nodb and not hasattr(DeviceClass, "device_name_factory"):
        print("In order to start %s with 'nodb' you need PyTango >= 7.2.3" %
              server_name)
        sys.exit(1)

    if len(tango_args) < 2:
        valid = False
        while not valid:
            inst_name = input(
                "Please indicate %s instance name: " % server_name)
            # should be a instance name validator.
            valid_set = string.ascii_letters + string.digits + '_' + '-'
            out = ''.join([c for c in inst_name if c not in valid_set])
            valid = len(inst_name) > 0 and len(out) == 0
            if not valid:
                print("We only accept alphanumeric combinations")
        args.append(inst_name)
        tango_args.append(inst_name)
    else:
        inst_name = tango_args[1].lower()

    if nodb:
        return log_messages

    db = Database()
    if not exists_server_instance(db, server_name, inst_name):
        if ask_yes_no('%s does not exist. Do you wish to create a new '
                      'one' % inst_name, default='y'):
            if server_name == 'MacroServer':
                # build list of pools to which the MacroServer should connect
                # to
                pool_names = []
                pools = get_dev_from_class(db, "Pool")
                all_pools = list(pools.keys())
                for pool in list(pools.values()):
                    pool_alias = pool[2]
                    if pool_alias is not None:
                        all_pools.append(pool_alias)
                all_pools = list(map(str.lower, all_pools))
                pools_for_choosing = []
                for i in pools:
                    pools_for_choosing.append(pools[i][3])
                pools_for_choosing = sorted(pools_for_choosing,
                                            key=lambda s: s.lower())
                no_pool_msg = ("\nMacroServer %s has not been connected to "
                               "any Pool\n" % inst_name)
                if len(pools_for_choosing) == 0:
                    print(no_pool_msg)
                else:
                    print("\nAvailable Pools:")
                    for pool in pools_for_choosing:
                        print(pool)
                    print("")
                    while True:
                        msg = "Please select the Pool to connect to " \
                              "(return to finish): "
                        # user may abort it with Ctrl+C - this will not
                        # register anything in the database and the
                        # KeyboardInterrupt will be raised
                        elem = input(msg).strip()
                        # no pools selected and user ended loop
                        if len(elem) == 0 and len(pool_names) == 0:
                            print(no_pool_msg)
                            break
                        # user ended loop with some pools selected
                        elif len(elem) == 0:
                            print(("\nMacroServer %s has been connected to "
                                  "Pool/s %s\n" % (inst_name, pool_names)))
                            break
                        # user entered unknown pool
                        elif elem.lower() not in all_pools:
                            print("Unknown pool element")
                        else:
                            pool_names.append(elem)
                log_messages += register_sardana(db, server_name, inst_name,
                                                 pool_names)
            else:
                log_messages += register_sardana(db, server_name, inst_name)
        else:
            raise AbortException("%s startup aborted" % server_name)
    return log_messages


def exists_server_instance(db, server_name, server_instance):
    known_inst = list(map(str.lower, db.get_instance_name_list(server_name)))
    return server_instance.lower() in known_inst


def register_sardana(db, bin_name, inst_name, pool_names=None):
    devices = []
    log_messages = []
    if bin_name == 'MacroServer':
        props = {'PoolNames': pool_names}
        ms_alias = get_free_alias(db, "MS_" + inst_name)
        devices.append(('MacroServer', None, ms_alias, props))
        door_alias = get_free_alias(db, "Door_" + inst_name)
        devices.append(("Door", None, door_alias, {}))
    elif bin_name == 'Pool':
        pool_alias = get_free_alias(db, 'Pool_' + inst_name)
        devices.append(('Pool', None, pool_alias, {}))
    elif bin_name == 'Sardana':
        pool_dev_name = get_free_device(db, 'pool/' + inst_name)
        pool_alias = get_free_alias(db, 'Pool_' + inst_name)
        devices.append(('Pool', pool_dev_name, pool_alias, {}))
        ms_alias = get_free_alias(db, "MS_" + inst_name)
        devices.append(('MacroServer', None, ms_alias,
                        {'PoolNames': [pool_dev_name]}))
        door_alias = get_free_alias(db, "Door_" + inst_name)
        devices.append(("Door", None, door_alias, {}))
    register_server_with_devices(db, bin_name, inst_name, devices)
    log_messages.append(("Registered server '%s/%s'", bin_name, inst_name))
    for d in devices:
        dev_class, dev_alias = d[0], d[2]
        log_messages.append(("Registered %s %s", dev_class, dev_alias))
    return log_messages


def register_server_with_devices(db, server_name, server_instance, devices):
    """Registers a new server with some devices in the Database.
       Devices is a seq<tuple<str, str, str, dict>>> where each item is a
       sequence of 4 elements :
        - device class
        - device name prefix
        - device alias
        - dictionary of properties

       :param db: database where to register devices
       :type db: PyTango.Database
       :param server_name: server name
       :type server_name: :obj:`str`
       :param server_instance: server instance name
       :type server_instance: :obj:`str`
       :param devices: map of devices to create.
       :type devices: dict<str, seq<tuple<str, str, dict>>>
    """
    info = DbDevInfo()
    info.server = server_name + "/" + server_instance
    for dev_info in devices:
        dev_class, prefix, alias, props = dev_info
        if prefix is None:
            prefix = dev_class + "/" + server_instance
        if prefix.count("/") == 1:
            prefix = get_free_device(db, prefix)
        info._class = dev_class
        info.name = prefix
        db.add_device(info)
        if alias is None:
            alias_prefix = dev_class + "_" + server_instance
            alias = get_free_alias(db, alias_prefix)
        db.put_device_alias(info.name, alias)
        if props is not None:
            db.put_device_property(info.name, props)


def from_name_to_tango(db, name):
    alias = None

    c = name.count('/')
    # if the db prefix is there, remove it first
    if c == 3 or c == 1:
        name = name[name.index("/") + 1:]

    elems = name.split('/')
    l = len(elems)

    if l == 3:
        try:
            alias = db.get_alias(name)
            if alias.lower() == 'nada':
                alias = None
        except Exception:
            alias = None
    elif l == 1:
        alias = name
        name = db.get_device_alias(alias)
    else:
        raise Exception("Invalid device name '%s'" % name)

    full_name = "tango://%s:%s/%s" % (db.get_db_host(), db.get_db_port(), name)
    return full_name, name, alias


def get_dev_from_class(db, classname):
    """Returns tuple<full device name, device name, alias, ouput string>"""
    server_wildcard = '*'
    try:
        exp_dev_list = db.get_device_exported_for_class(classname)
    except Exception:
        exp_dev_list = []

    res = {}
    dev_list = db.get_device_name(server_wildcard, classname)
    for dev in dev_list:
        full_name, name, alias = from_name_to_tango(db, dev)
        out = alias or name
        if alias:
            out += ' (a.k.a. %s)' % name
        out = "%-25s" % out
        if dev in exp_dev_list:
            out += " (running)"
        res[dev] = full_name, name, alias, out
    return res


def get_dev_from_class_server(db, classname, server):
    """Returns device(s) name for a given class and server"""

    def pairwise(iterable):
        "s -> (s0, s1), (s2, s3), (s4, s5), ..."
        a = iter(iterable)
        return list(zip(a, a))

    devices = []
    device_class_list = db.get_device_class_list(server)
    for dev, cls in pairwise(device_class_list):
        if cls == classname:
            devices.append(dev)
    return devices


def get_free_server(db, prefix, start_from=1):
    prefix = prefix + "_"
    server_members = db.get_server_list(prefix + "*")
    server = server_members.value_string
    while prefix + str(start_from) in server:
        start_from += 1
    return prefix + str(start_from)


def get_free_device(db, prefix, start_from=1):
    members = db.get_device_member(prefix + "/*")
    while str(start_from) in members:
        start_from += 1
    return prefix + "/" + str(start_from)


def get_free_alias(db, prefix, start_from=1):
    '''Iterates until failure, trying to retrieve from the database device of
    the given alias. This way, first which fails is available in the database.

    :param db: database where to look for the free alias
    :type db: PyTango.Database
    :param start_from: alias suffix in form of consecutive number
    :type start_from: int
    '''
    while True:
        name = prefix + "_" + str(start_from)
        try:
            db.get_device_from_alias(name)  # PyTango >= 8.1.0
        except PyTango.DevFailed:
            return name
        except AttributeError:
            try:
                db.get_device_alias(name)  # deprecated since PyTango 8.1.0
            except PyTango.DevFailed:
                return name
        start_from += 1


def get_free_property(db, obj_name, property_name):
    """Get *free property* from Tango database.

    If it is not defined return None.
    """
    value = None
    try:
        prop = db.get_property(obj_name, property_name)
        value = prop[property_name][0]
    except Exception:
        pass
    return value


def prepare_taurus(options, args, tango_args):
    # make sure the polling is not active
    factory = taurus.Factory()
    factory.disablePolling()


def prepare_logstash(args):
    """Prepare logstash handler based on the configuration stored in the Tango
    database.

    :param args: process execution arguments
    :type args: list<str>

    .. note::
        The prepare_logstash function has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including its removal) may occur if
        deemed necessary by the core developers.
    """
    log_messages = []

    try:
        from logstash_async.handler import AsynchronousLogstashHandler
    except ImportError:
        msg = ("Unable to import logstash_async. Skipping logstash "
               + "configuration...", )
        log_messages.append(msg,)
        return log_messages

    def get_logstash_conf(dev_name):
        try:
            props = db.get_device_property(dev_name, "LogstashHost")
            host = props["LogstashHost"][0]
        except IndexError:
            host = None
        try:
            props = db.get_device_property(dev_name, "LogstashPort")
            port = int(props["LogstashPort"][0])
        except IndexError:
            port = None
        try:
            props = db.get_device_property(dev_name, "LogstashCacheDbPath")
            cache_db_path = props["LogstashCacheDbPath"][0]
        except IndexError:
            cache_db_path = None
        return host, port, cache_db_path

    db = Database()

    bin_name = args[0]
    try:
        instance_name = args[1]
    except IndexError:
        msg = ("Unknown %s instance name. " % bin_name
               + "Skipping logstash configuration...")
        log_messages.append(msg, )
        return log_messages
    server_name = bin_name + "/" + instance_name
    if bin_name in ["Pool", "MacroServer"]:
        class_name = bin_name
        dev_name = get_dev_from_class_server(db, class_name, server_name)[0]
        host, port, cache = get_logstash_conf(dev_name)
    else:
        dev_name = get_dev_from_class_server(db, "Pool", server_name)[0]
        host, port, cache = get_logstash_conf(dev_name)
        if host is None:
            dev_name = get_dev_from_class_server(db, "MacroServer",
                                                 server_name)[0]
            host, port, cache = get_logstash_conf(dev_name)

    if host is not None:
        root = Logger.getRootLog()
        handler = AsynchronousLogstashHandler(host, port, database_path=cache)
        # don't use full path for program_name
        handler._create_formatter_if_necessary()
        _, handler.formatter._program_name = os.path.split(handler.formatter._program_name)
        root.addHandler(handler)
        msg = ("Log is being sent to logstash listening on %s:%d",
               host, port)
        log_messages.append(msg)

    return log_messages


def prepare_logging(options, args, tango_args, start_time=None,
                    log_messages=None):

    taurus.setLogLevel(taurus.Debug)
    root = Logger.getRootLog()

    # output logger configuration
    log_output_level = options.log_level
    log_level_map = {"0": taurus.Critical, "critical": taurus.Critical,
                     "1": taurus.Error, "error": taurus.Error,
                     "2": taurus.Warning, "warning": taurus.Warning,
                     "3": taurus.Info, "info": taurus.Info,
                     "4": taurus.Debug, "debug": taurus.Debug,
                     "5": taurus.Trace, "trace": taurus.Trace,
                     }
    log_output_level = log_level_map[log_output_level]
    root.handlers[0].setLevel(log_output_level)

    if not options.without_log_file:
        log_file_level = options.log_file_level
        log_file_level = log_level_map[log_file_level]

        # Create a file handler
        if options.log_file_name is None:
            _, ds_name = os.path.split(args[0])
            ds_name, _ = os.path.splitext(ds_name)
            ds_instance = args[-1].lower()
            import getpass
            try:
                # include the user name to avoid permission errors
                tangodir = 'tango-%s' % getpass.getuser()
            except Exception:
                tangodir = 'tango' % getpass.getuser()
            path = os.path.join(os.sep, "tmp", tangodir, ds_name, ds_instance)
            log_file_name = os.path.join(path, 'log.txt')
        else:
            log_file_name = options.log_file_name
        path = os.path.dirname(log_file_name)

        # because some versions of python have a bug in logging.shutdown (this
        # function is not protected against deleted handlers) we store the
        # handlers we create to make sure a strong reference exists when the
        # logging.shutdown is called
        taurus._handlers = handlers = []
        try:
            if not os.path.exists(path):
                os.makedirs(path, 0o777)

            from sardana import sardanacustomsettings
            maxBytes = getattr(sardanacustomsettings, 'LOG_FILES_SIZE', 1E7)
            backupCount = getattr(sardanacustomsettings, 'LOG_BCK_COUNT', 5)

            fmt = Logger.getLogFormat()
            f_h = logging.handlers.RotatingFileHandler(log_file_name,
                                                       maxBytes=maxBytes,
                                                       backupCount=backupCount)
            f_h.setFormatter(fmt)
            f_h.setLevel(log_file_level)
            root.addHandler(f_h)
            handlers.append(f_h)

            if start_time is not None:
                taurus.info("Started at %s", start_time)
            else:
                taurus.info("Starting up...")
            taurus.info("Log is being stored in %s", log_file_name)
        except Exception:
            if start_time is not None:
                taurus.info("Started at %s", start_time)
            else:
                taurus.info("Starting up...")
            taurus.warning("'%s' could not be created. Logs will not be "
                           "stored", log_file_name)
            taurus.debug("Error description", exc_info=1)

    if log_messages is None:
        log_messages = []
    for log_message in log_messages:
        taurus.info(*log_message)

    taurus.debug("Start args=%s", args)
    taurus.debug("Start tango args=%s", tango_args)
    taurus.debug("Start options=%s", options)
    taurus.debug("Using PyTango %s from %s",
                 PyTango.Release.version, PyTango.__path__[0])
    taurus.debug("Using taurus %s from %s",
                 taurus.Release.version, taurus.__path__[0])
    taurus.debug("Using sardana %s from %s",
                 sardana.Release.version, sardana.__path__[0])


def prepare_rconsole(options, args, tango_args):
    port = options.rconsole_port
    if port is None or port == 0:
        return
    taurus.debug("Setting up rconsole on port %d...", port)
    try:
        import rfoo.utils.rconsole
        rfoo.utils.rconsole.spawn_server(port=port)
        taurus.debug("Finished setting up rconsole")
    except Exception:
        taurus.debug("Failed to setup rconsole", exc_info=1)


def run_tango_server(tango_util=None, start_time=None):
    # Import here to avoid circular import
    from sardana.tango.core.SardanaDevice import SardanaDevice

    try:
        if tango_util is None:
            tango_util = Util(sys.argv)
        util = Util.instance()
        SardanaServer.server_state = State.Init
        util.server_init()

        for device in util.get_device_list("*"):
            if isinstance(device, SardanaDevice):
                device.sardana_init_hook()

        SardanaServer.server_state = State.Running
        if start_time is not None:
            import datetime
            dt = datetime.datetime.now() - start_time
            taurus.info("Ready to accept request in %s", dt)
        else:
            taurus.info("Ready to accept request")
        util.server_run()
        SardanaServer.server_state = State.Off
        taurus.info("Exiting")
    except DevFailed:
        taurus.info("Exiting")
        taurus.critical("Server exited with DevFailed", exc_info=1)
    except KeyboardInterrupt:
        taurus.info("Exiting")
        taurus.critical("Interrupted by keyboard")
    except Exception:
        taurus.info("Exiting")
        taurus.critical("Server exited with unforeseen exception", exc_info=1)
    taurus.info("Exited")


def run(prepare_func, args=None, tango_util=None, start_time=None, mode=None,
        name=None):

    if mode is None:
        mode = ServerRunMode.SynchPure

    if args is None:
        if mode != ServerRunMode.SynchPure:
            raise Exception("When running in separate thread/process, "
                            "'args' must be given")
        args = sys.argv

    if name is None:
        name = args[0]
    else:
        args = [name] + list(args[1:])

    if mode != ServerRunMode.SynchPure:
        if mode in (ServerRunMode.SynchThread, ServerRunMode.AsynchThread):
            import threading

            class task_klass(threading.Thread):

                def terminate(self):
                    if not self.is_alive():
                        return
                    Util.instance().get_dserver_device().kill()
        else:
            import multiprocessing
            task_klass = multiprocessing.Process
            tango_util = None

        task_args = prepare_func,
        task_kwargs = dict(args=args, tango_util=tango_util,
                           start_time=start_time, mode=ServerRunMode.SynchPure)

        task = task_klass(name=name, target=run, args=task_args,
                          kwargs=task_kwargs)
        task.daemon = False
        task.start()
        if mode in (ServerRunMode.SynchThread, ServerRunMode.SynchProcess):
            task.join()
        return task

    log_messages = []
    try:
        options, args, tango_args, ORB_args = prepare_cmdline(args=args)
    except KeyboardInterrupt:
        pass

    try:
        log_messages.extend(prepare_server(args, tango_args))
    except AbortException as e:
        print(e)
        return
    except KeyboardInterrupt:
        print("\nInterrupted by keyboard")
        return

    log_messages.extend(prepare_ORBendPoint(args, tango_args))
    # Tango versions < 8.0.5 are affected by
    # https://sourceforge.net/p/tango-cs/bugs/495/
    tango_version = get_tango_version_number()
    if tango_version < 80005:
        log_messages.extend(prepare_environment(args, tango_args, ORB_args))

    log_messages.extend(prepare_logstash(args))

    if tango_util is None:
        tango_util = Util(tango_args)

    prepare_func(tango_util)
    prepare_taurus(options, args, tango_args)
    prepare_logging(options, args, tango_args, start_time=start_time,
                    log_messages=log_messages)
    prepare_rconsole(options, args, tango_args)

    run_tango_server(tango_util, start_time=start_time)
