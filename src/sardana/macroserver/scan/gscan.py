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

"""This module contains the class definition for the MacroServer generic
scan"""

__all__ = ["ScanSetupError", "ScanException", "ExtraData", "TangoExtraData",
           "GScan", "SScan", "CScan", "CSScan", "CTScan", "HScan", "TScan"]

__docformat__ = 'restructuredtext'

import os
import datetime
import operator
import time
import threading
import weakref
import numpy as np

import PyTango
import taurus
import collections

from collections import OrderedDict

from taurus.core.util.log import Logger
from taurus.core.util.user import USER_NAME
from taurus.core.tango import FROM_TANGO_TO_STR_TYPE
from taurus.core.util.enumeration import Enumeration
from taurus.core.util.threadpool import ThreadPool
from taurus.core.util.event import CallableRef
from taurus.core.tango.tangovalidator import TangoDeviceNameValidator

from sardana.sardanathreadpool import OmniWorker
from sardana.util.tree import BranchNode, LeafNode, Tree
from sardana.util.motion import Motor as VMotor
from sardana.util.motion import MotionPath
from sardana.util.thread import CountLatch
from sardana.pool.pooldefs import SynchDomain, SynchParam
from sardana.macroserver.msexception import MacroServerException, UnknownEnv, \
    InterruptException, StopException, AbortException
from sardana.macroserver.msparameter import Type
from sardana.macroserver.scan.scandata import ColumnDesc, MoveableDesc, \
    ScanFactory, ScanDataEnvironment
from sardana.macroserver.scan.recorder import (AmbiguousRecorderError,
                                               SharedMemoryRecorder,
                                               FileRecorder)
from sardana.taurus.core.tango.sardana.pool import Ready, TwoDExpChannel


# ScanEndStatus enumeration indicates the reason of the scan end.
ScanEndStatus = Enumeration("ScanEndStatus",
                            ["Normal", "Stop", "Abort", "Exception"])


class ScanSetupError(Exception):
    pass


class ScanException(MacroServerException):
    pass


def _get_shape(channel):
    # internal Sardana channel
    if isinstance(channel, PyTango.DeviceProxy):
        try:
            shape = channel.shape
        except Exception:
            return None
        if shape is None:  # in PyTango empty spectrum is None
            return []
        return shape
    # external channel (Tango attribute)
    elif isinstance(channel, PyTango.AttributeProxy):
        try:
            attr_conf = channel.get_config()
        except Exception:
            return None
        if attr_conf.data_format == PyTango.AttrDataFormat.SCALAR:
            return []
        try:
            value = channel.read().value
        except Exception:
            return [n for n in (attr_conf.max_dim_x,
                                attr_conf.max_dim_y) if n > 0]
        return list(np.shape(value))


class ExtraData(object):

    def __init__(self, **kwargs):
        """Expected keywords are:
            - model (str, mandatory): represents data source (ex.: a/b/c/d)
            - label (str, mandatory): column label
            - name (str, optional): unique name (defaults to model)
            - shape (seq, optional): data shape
            - dtype (numpy.dtype, optional): data type
            - instrument (str, optional): full instrument name"""
        self._label = kwargs['label']
        self._model = kwargs['model']
        if 'dtype' not in kwargs:
            kwargs['dtype'] = self.getType()
        if 'shape' not in kwargs:
            kwargs['shape'] = self.getShape()
        if 'name' not in kwargs:
            kwargs['name'] = self._model
        self._column = ColumnDesc(**kwargs)

    def getLabel(self):
        return self._label

    def getName(self):
        return self._label

    def getColumnDesc(self):
        return self._column

    def getType(self):
        raise Exception("Must be implemented in subclass")

    def getShape(self):
        raise Exception("Must be implemented in subclass")

    def read(self):
        raise Exception("Must be implemented in subclass")


class TangoExtraData(ExtraData):

    def __init__(self, **kwargs):
        self._attribute = None
        ExtraData.__init__(self, **kwargs)

    @property
    def attribute(self):
        if self._attribute is None:
            self._attribute = taurus.Attribute(self._model)
        return self._attribute

    def getType(self):
        t = self.attribute.getType()
        if t is None:
            raise Exception("Could not determine type for unknown attribute "
                            "'%s'" % self._model)
        return FROM_TANGO_TO_STR_TYPE[t]

    def getShape(self):
        s = self.attribute.getShape()
        if s is None:
            raise Exception("Could not determine type for unknown attribute "
                            "'%s'" % self._model)
        return s

    def read(self):
        try:
            return self.attribute.read(cache=False).value
        except InterruptException:
            raise
        except Exception:
            return None


class GScan(Logger):
    """Generic Scan object.
    The idea is that the scan macros create an instance of this Generic Scan,
    supplying in the constructor a reference to the macro that created the
    scan, a generator function pointer, a list of moveable items, an extra
    environment and a sequence of constrains.

    If the referenced macro is hookable, ``pre-scan`` and ``post-scan`` hook
    hints will be used to execute callables before the start and after the
    end of the scan, respectively

    The generator must be a function yielding a dictionary with the following
    content (minimum) at each step of the scan:

    - 'positions' : In a step scan, the position where the moveables
      should go
    - 'integ_time' : In a step scan, a number representing the integration
      time for the step (in seconds)
    - 'integ_time' : In a continuous scan, the time between acquisitions
    - 'pre-move-hooks' : (optional) a sequence of callables to be called
      in strict order before starting to move.
    - 'post-move-hooks': (optional) a sequence of callables to be called
      in strict order after finishing the move.
    - 'pre-acq-hooks' : (optional) a sequence of callables to be called in
      strict order before starting to acquire.
    - 'post-acq-hooks' : (optional) a sequence of callables to be called in
      strict order after finishing acquisition but before recording the step.
    - 'post-step-hooks' : (optional) a sequence of callables to be called in
      strict order after finishing recording the step.
    - 'point_id' : a hashable identifing the scan point.
    - 'check_func' : (optional) a list of callable objects.
      callable(moveables, counters)
    - 'extravalues': (optional) a dictionary containing the values for
      each extra info field. The extra information fields must be described
      in extradesc (passed in the constructor of the Gscan)


    The moveables must be a sequence Motion or MoveableDesc objects.

    The environment is a dictionary of extra environment to be added specific
    to the macro in question.

    Each constrain must be a callable which must receive a two parameters: the
    current point and the next point. It should return True or False

    The extradesc optional argument consists of a list of ColumnDesc objects
    which describe the data fields that will be filled using
    step['extravalues'], where step is what the generator yields.

    The Generic Scan will create:

    - a ScanData
    - DataHandler with the following recorders:
    - OutputRecorder (depends on ``OutputCols`` environment variable)
    - SharedMemoryRecorder (depends on ``SharedMemory`` environment variable)
    - FileRecorder (depends on ``ScanDir``, ``ScanData`` and ``ScanRecorder``
      environment variables)
    - ScanDataEnvironment with the following contents:

        - 'serialno' : a integer identifier for the scan operation
        - 'user' : the user which started the scan
        - 'title' : the scan title (build from macro.getCommand)
        - 'datadesc' : a seq<ColumnDesc> describing each column of data
          (labels, data format, data shape, etc)
        - 'estimatedtime' : a float representing an estimation for the duration
          of the scan (in seconds). Negative means the time estimation is known
          not to be accurate. Anyway, time estimation has 'at least' semantics.
        - 'total_scan_intervals' : total number of scan intervals. Negative
          means the estimation is known not to be accurate. In this case,
          estimation has 'at least' semantics.
        - '' : a datetime.datetime representing the start of the scan
        - 'instrumentlist' : a list of Instrument objects containing info about
          the physical setup of the motors, counters,
        - <extra environment> given in the constructor

        (at the end of the scan, extra keys 'endtime' and 'deadtime' will be
        added representing the time at the end of the scan and the dead time)

        This object is passed to all recorders at the beginning and at the end
        of the scan (when startRecordList and endRecordList is called)

    At each step of the scan, for each Recorder, the writeRecord method will
    be called with a Record object as parameter. The Record.data member will be
    a dictionary containing:

    - 'point_nb' : the point number of the scan
    - for each column of the scan (motor or counter), a key with the
      corresponding column name will contain the value

    """

    MAX_SCAN_HISTORY = 20

    env = ('ActiveMntGrp', 'ExtraColumns' 'ScanDir', 'ScanFile',
           'ScanRecorder', 'SharedMemory', 'OutputCols')

    def __init__(self, macro, generator=None, moveables=[], env={},
                 constraints=[], extrainfodesc=[]):
        self._macro = weakref.ref(macro)
        if generator is not None:
            generator = CallableRef(generator)
        self._generator = generator
        self._extrainfodesc = extrainfodesc

        # nasty hack to make sure macro has access to gScan as soon as
        # possible
        self.macro._gScan = self
        self._rec_manager = macro.getMacroServer().recorder_manager

        self._moveables, moveable_names = [], []
        for moveable in moveables:
            if not isinstance(moveable, MoveableDesc):
                moveable = MoveableDesc(moveable=moveable)
            moveable_names.append(moveable.moveable.getName())
            self._moveables.append(moveable)

        self._check_moveables_limits()

        name = self.__class__.__name__
        self.call__init__(Logger, name)

        # ---------------------------------------------------------------------
        # Setup motion objects
        # ---------------------------------------------------------------------
        if len(moveable_names) > 0:
            self._motion = macro.getMotion(moveable_names)
        else:
            self._motion = None

        # ---------------------------------------------------------------------
        # Find the measurement group
        # ---------------------------------------------------------------------
        try:
            mnt_grp_name = macro.getEnv('ActiveMntGrp')
        except UnknownEnv:
            mnt_grps = macro.getObjs(".*", type_class=Type.MeasurementGroup)
            if len(mnt_grps) == 0:
                raise ScanSetupError('No Measurement Group defined')
            mnt_grp = mnt_grps[0]
            macro.info("ActiveMntGrp not defined. Using %s", mnt_grp)
            macro.setEnv('ActiveMntGrp', mnt_grp.getName())
        else:
            if not isinstance(mnt_grp_name, str):
                t = type(mnt_grp_name).__name__
                raise TypeError("ActiveMntGrp MUST be string. It is '%s'" % t)

            mnt_grp = macro.getObj(mnt_grp_name,
                                   type_class=Type.MeasurementGroup)

        if mnt_grp is None:
            raise ScanSetupError("ActiveMntGrp has invalid value: '%s'"
                                 % mnt_grp_name)

        self._master = mnt_grp.getConfiguration().getTimer()

        if self._master is None:
            raise ScanSetupError('%s has no timer defined' % mnt_grp.getName())

        self._measurement_group = mnt_grp

        # ---------------------------------------------------------------------
        # Setup extra columns
        # ---------------------------------------------------------------------
        self._extra_columns = self._getExtraColumns()

        # ---------------------------------------------------------------------
        # Setup data management
        # ---------------------------------------------------------------------

        # Generate data handler
        data_handler = ScanFactory().getDataHandler()

        # The Scan data object
        try:
            apply_interpol = macro.getEnv('ApplyInterpolation')
        except UnknownEnv:
            apply_interpol = False
        try:
            apply_extrapol = macro.getEnv('ApplyExtrapolation')
        except UnknownEnv:
            apply_extrapol = False
        # The Scan data object
        data = ScanFactory().getScanData(data_handler,
                                         apply_interpolation=apply_interpol,
                                         apply_extrapolation=apply_extrapol)

        # The Output recorder (if any)
        output_recorder = self._getOutputRecorder()

        # The Output recorder (if any)
        json_recorder = self._getJsonRecorder()

        # The File recorders (if any)
        file_recorders = self._getFileRecorders()

        # The Shared memory recorder (if any)
        shm_recorder = self._getSharedMemoryRecorder(0)
        shm_recorder_1d = None
        if shm_recorder is not None:
            shm_recorder_1d = self._getSharedMemoryRecorder(1)

        data_handler.addRecorder(output_recorder)
        data_handler.addRecorder(json_recorder)
        for file_recorder in file_recorders:
            data_handler.addRecorder(file_recorder)
        data_handler.addRecorder(shm_recorder)
        data_handler.addRecorder(shm_recorder_1d)

        self._data = data
        self._data_handler = data_handler

        # ---------------------------------------------------------------------
        # Setup environment
        # ---------------------------------------------------------------------
        self._setupEnvironment(env)

    def _check_moveables_limits(self):
        for m in self._moveables:
            pos_range = m.moveable.getAttribute("Position").range
            try:
                high = float(pos_range[1].magnitude)    # Taurus 4
            except AttributeError:
                try:
                    high = float(pos_range[1])          # Taurus 3
                except ValueError:
                    high = None
            try:
                low = float(pos_range[0].magnitude)     # Taurus 4
            except AttributeError:
                try:
                    low = float(pos_range[0])           # Taurus 3
                except ValueError:
                    low = None

            if any((high, low)) and not any((m.min_value, m.max_value)):
                self.macro.info("Scan range is not defined for %s and could "
                                 "not be verified against motor limits."
                                 % m.moveable.getName())

            for pos in (m.min_value, m.max_value):
                if pos is None:
                    continue
                if high is not None:
                    if float(pos) > high:
                        raise RuntimeError(
                            "requested movement of %s is above its upper limit"
                            % m.moveable.getName())
                if low is not None:
                    if float(pos) < low:
                        raise RuntimeError(
                            "requested movement of %s is below its lower limit"
                            % m.moveable.getName())

    def _getExtraColumns(self):
        ret = []
        try:
            cols = self.macro.getEnv('ExtraColumns')
        except InterruptException:
            raise
        except Exception:
            self.info('ExtraColumns is not defined')
            return ret

        try:
            for i, kwargs in enumerate(cols):
                kw = dict(kwargs)
                try:
                    if 'instrument' in kw:
                        type_class = Type.Instrument
                        instrument = self.macro.getObj(kw['instrument'],
                                                        type_class=type_class)
                        if instrument:
                            kw['instrument'] = instrument
                    ret.append(TangoExtraData(**kw))
                except InterruptException:
                    raise
                except Exception as colexcept:
                    colname = kw.get('label', str(i))
                    self.macro.warning("Extra column %s is invalid: %s",
                                       colname, str(colexcept))
        except InterruptException:
            raise
        except Exception:
            self.macro.warning('ExtraColumns has invalid value. Must be a '
                               'sequence of maps')
        return ret

    def _getJsonRecorder(self):
        try:
            json_enabled = self.macro.getEnv('JsonRecorder')
            if json_enabled:
                return self._rec_manager.getRecorderClass("JsonRecorder")(
                    self.macro)
        except InterruptException:
            raise
        except Exception:
            pass
        self.info('JsonRecorder is not defined. Use "senv JsonRecorder '
                  'True" to enable it')

    def _getOutputRecorder(self):
        cols = None
        output_block = False
        try:
            cols = self.macro.getEnv('OutputCols')
        except InterruptException:
            raise
        except Exception:
            pass

        try:
            output_block = self.macro.getViewOption('OutputBlock')
        except InterruptException:
            raise
        except Exception:
            pass

        return self._rec_manager.getRecorderClass("OutputRecorder")(
            self.macro, cols=cols, number_fmt='%g', output_block=output_block)

    def _getFileRecorders(self):
        macro = self.macro
        try:
            scan_dir = macro.getEnv('ScanDir')
            if scan_dir == '' or None:
                macro.warning('ScanDir value is empty')
                raise Exception('ScanDir value is empty')
        except InterruptException:
            raise
        except Exception:
            macro.warning('ScanDir is not defined. This operation will not be '
                          'stored persistently. Use "expconf" or "newfile" '
                          'to configure data storage (or eventually "senv '
                          'ScanDir <abs directory>")')
            return ()

        if not isinstance(scan_dir, str):
            scan_dir_t = type(scan_dir).__name__
            raise TypeError("ScanDir MUST be string. It is '%s'" % scan_dir_t)

        try:
            file_names = macro.getEnv('ScanFile')
            if file_names == [''] or None:
                macro.warning('ScanFile value is empty')
                raise Exception('ScanFile value is empty')
        except InterruptException:
            raise
        except Exception:
            macro.warning('ScanFile is not defined. This operation will not '
                          'be stored persistently. Use "expconf" or "newfile" '
                          'to configure data storage (or eventually "senv '
                          'ScanFile <scan file(s)>")')
            return ()

        scan_recorders = []
        try:
            scan_recorders = macro.getEnv('ScanRecorder')
        except InterruptException:
            raise
        except UnknownEnv:
            pass

        if isinstance(file_names, str):
            file_names = (file_names,)
        elif not isinstance(file_names, collections.Sequence):
            scan_file_t = type(file_names).__name__
            raise TypeError("ScanFile MUST be string or sequence of strings."
                            " It is '%s'" % scan_file_t)

        if isinstance(scan_recorders, str):
            scan_recorders = (scan_recorders,)
        elif not isinstance(scan_recorders, collections.Sequence):
            scan_recorders_t = type(scan_recorders).__name__
            raise TypeError("ScanRecorder MUST be string or sequence of "
                            "strings. It is '%s'" % scan_recorders_t)

        file_recorders = []
        for i, file_name in enumerate(file_names):
            abs_file_name = os.path.join(scan_dir, file_name)
            try:
                file_recorder = None
                if len(scan_recorders) > i:
                    file_recorder = self._rec_manager.getRecorderClass(
                        scan_recorders[i])(abs_file_name, macro=macro)
                if not file_recorder:
                    file_recorder = FileRecorder(abs_file_name, macro=macro)
                file_recorders.append(file_recorder)
            except InterruptException:
                raise
            except AmbiguousRecorderError as e:
                macro.error('Select recorder that you would like to use '
                            '(i.e. set ScanRecorder environment variable).')
                raise e
            except Exception:
                macro.warning("Error creating recorder for %s", abs_file_name)
                macro.debug("Details:", exc_info=1)

        if len(file_recorders) == 0:
            macro.warning("No valid recorder found. This operation will not "
                          "be stored persistently")
        return file_recorders

    def _getSharedMemoryRecorder(self, eid):
        macro, mg, shm = self.macro, self.measurement_group, False
        shmRecorder = None
        try:
            shm = macro.getEnv('SharedMemory')
        except InterruptException:
            raise
        except Exception:
            self.info('SharedMemory is not defined. Use "senv '
                      'SharedMemory sps" to enable it')
            return

        if not shm:
            return

        kwargs = {}
        # For now we only support SPS shared memory format
        if shm.lower() == 'sps':
            cols = 1                            # Point nb column
            cols += len(self.moveables)          # motor columns
            ch_nb = len(mg.getChannels())
            oned_nb = 0
            array_prefix = mg.getName().upper()

            try:
                oned_nb = len(mg.OneDExpChannels)
            except InterruptException:
                raise
            except Exception:
                oned_nb = 0

            twod_nb = 0
            try:
                twod_nb = len(mg.TwoDExpChannels)
            except InterruptException:
                raise
            except Exception:
                twod_nb = 0

            if eid == 0:
                # counter/timer & 0D channel columns
                cols += (ch_nb - oned_nb - twod_nb)
            elif eid == 1:
                cols = 1024

            if eid == 0:
                kwargs.update({'program': macro.getDoorName(),
                               'array': "%s_0D" % array_prefix,
                               'shape': (cols, 4096)})
            elif eid == 1:
                if oned_nb == 0:
                    return
                else:
                    kwargs.update({'program': macro.getDoorName(),
                                   'array': "%s_1D" % array_prefix,
                                   'shape': (cols, 99)})
        try:
            shmRecorder = SharedMemoryRecorder(shm, macro, **kwargs)
        except Exception:
            macro.warning("Error creating %s SharedMemory recorder." % shm)
            macro.debug("Details:", exc_info=1)

        return shmRecorder

    def _secsToTimedelta(self, secs):
        days, secs = divmod(secs, 86400)
        # we don't have to care about microseconds because if secs is a float
        # timedelta will do it for us
        return datetime.timedelta(days, secs)

    def _timedeltaToSecs(self, td):
        return 86400 * td.days + td.seconds + 1E-6 * td.microseconds

    def _setupEnvironment(self, additional_env):
        try:
            serialno = self.macro.getEnv("ScanID") + 1
        except UnknownEnv:
            serialno = 1
        self.macro.setEnv("ScanID", serialno)

        try:
            user = self.macro.getEnv("ScanUser")
        except UnknownEnv:
            user = USER_NAME

        env = ScanDataEnvironment(
            {'serialno': serialno,
             # TODO: this should be got from
             # self.measurement_group.getChannelsInfo()
             'user': user,
             'title': self.macro.getCommand()})

        # Initialize the data_desc list (and add the point number column)
        data_desc = [
            ColumnDesc(name='point_nb', label='#Pt No', dtype='int64')
        ]

        # add motor columns
        ref_moveables = []
        for moveable in self.moveables:
            data_desc.append(moveable)
            if moveable.is_reference:
                ref_moveables.insert(0, moveable.name)

        if not ref_moveables and len(self.moveables):
            ref_moveables.append(data_desc[-1].name)
        env['ref_moveables'] = ref_moveables

        # add master column
        master = self._master

        # add channels from measurement group
        channels_info = self.measurement_group.getChannelsEnabledInfo()
        counters = []
        for ci in channels_info:
            full_name = ci.full_name
            shape = None
            instrument = ''
            try:
                # Use DeviceProxy instead of taurus to avoid crashes in Py3
                # See: tango-controls/pytango#292
                # channel = taurus.Device(full_name)
                channel = PyTango.DeviceProxy(full_name)
            except Exception:
                try:
                    channel = PyTango.AttributeProxy(full_name)
                except Exception:
                    channel = None
            if channel:
                shape = _get_shape(channel)
                try:
                    instrument = channel.instrument
                except Exception:
                    instrument = ''
            try:
                instrumentFullName = self.macro.findObjs(
                    instrument, type_class=Type.Instrument)[0].getFullName()
            except InterruptException:
                raise
            except Exception:
                instrumentFullName = ''
            if shape is None:
                self.warning("unknown shape of {}, assuming scalar".format(
                    ci.name))
                shape = []
            # substitute the axis placeholder by the corresponding moveable.
            plotAxes = []
            i = 0
            for a in ci.plot_axes:
                if a == '<mov>':
                    # skip plots against moveables in scans that do not involve
                    # them e.g. time scans
                    if len(ref_moveables) == 0:
                        continue
                    plotAxes.append(ref_moveables[i])
                    i += 1
                else:
                    plotAxes.append(a)
            try:
                value_ref_enabled = ci.value_ref_enabled
            except AttributeError:
                value_ref_enabled = False
            # create the ColumnDesc object
            column = ColumnDesc(name=ci.full_name,
                                label=ci.label,
                                dtype=ci.data_type,
                                shape=shape,
                                instrument=instrumentFullName,
                                source=ci.source,
                                output=ci.output,
                                conditioning=ci.conditioning,
                                normalization=ci.normalization,
                                plot_type=ci.plot_type,
                                plot_axes=plotAxes,
                                data_units=ci.unit,
                                value_ref_enabled=value_ref_enabled)
            data_desc.append(column)
            counters.append(column.name)
        try:
            counters.remove(master['full_name'])
        except ValueError:
            # timer may be disabled
            pass
        env['counters'] = counters

        for extra_column in self._extra_columns:
            data_desc.append(extra_column.getColumnDesc())
        # add extra columns
        data_desc += self._extrainfodesc
        data_desc.append(ColumnDesc(name='timestamp',
                                    label='dt', dtype='float64'))

        env['datadesc'] = data_desc

        # set the data compression default
        try:
            env['DataCompressionRank'] = self.macro.getEnv(
                'DataCompressionRank')
        except UnknownEnv:
            env['DataCompressionRank'] = -1

        # set the sample information
        # @todo: use the instrument API to get this info
        try:
            env['SampleInfo'] = self.macro.getEnv('SampleInfo')
        except UnknownEnv:
            env['SampleInfo'] = {}

        # set the source information
        # @todo: use the instrument API to get this info
        try:
            env['SourceInfo'] = self.macro.getEnv('SourceInfo')
        except UnknownEnv:
            env['SourceInfo'] = {}

        # take the pre-scan snapshot
        try:
            preScanSnapShot = self.macro.getEnv('PreScanSnapshot')
        except UnknownEnv:
            preScanSnapShot = []
        env['preScanSnapShot'] = self.takeSnapshot(elements=preScanSnapShot)

        env['macro_id'] = self.macro.getID()
        try:
            env['ScanFile'] = self.macro.getEnv('ScanFile')
        except InterruptException:
            raise
        except Exception:
            env['ScanFile'] = None
        try:
            env['ScanDir'] = self.macro.getEnv('ScanDir')
        except InterruptException:
            raise
        except Exception:
            env['ScanDir'] = None
        env['estimatedtime'], env['total_scan_intervals'] = self._estimate()
        env['instrumentlist'] = self.macro.findObjs(
            '.*', type_class=Type.Instrument)

        # env.update(self._getExperimentConfiguration) #add all the info from
        # the experiment configuration to the environment
        env.update(additional_env)
        self._env = env

        # Give the environment to the ScanData
        self.data.setEnviron(env)

    def takeSnapshot(self, elements=[]):
        """reads the current values of the given elements

        :param elements: (list<str,str>) list of tuples of label,src for the
                         elements to read (can be pool elements or Taurus
                         attribute names).

        :return: (list<ColumnDesc>) a list of :class:`ColumnDesc`,
                 each including a "pre_scan_value" attribute with the read
                 value for that attr
        """
        manager = self.macro.getManager()
        all_elements_info = manager.get_elements_with_interface('Element')
        ret = []
        for src, label in elements:
            try:
                if src in all_elements_info:
                    ei = all_elements_info[src]
                    column = ColumnDesc(name=ei.full_name,
                                        label=label,
                                        instrument=ei.instrument,
                                        source=ei.source)
                else:
                    column = ColumnDesc(name=src,
                                        label=label,
                                        source=src)

                # @Fixme: Tango-centric. It should work for any Taurus
                # Attribute
                v = PyTango.AttributeProxy(column.source).read().value
                column.pre_scan_value = v
                column.shape = np.shape(v)
                column.dtype = getattr(v, 'dtype', np.dtype(type(v))).name
                ret.append(column)
            except Exception:
                self.macro.warning(
                    'Error taking pre-scan snapshot of %s (%s)', label, src)
                self.debug('Details:', exc_info=1)
        return ret

    def get_virtual_motors(self):
        ret = []
        for moveable in self.moveables:
            try:
                v_motor = VMotor.fromMotor(moveable.moveable)
            except Exception:
                # self.debug("Details:", exc_info=1)
                v_motor = VMotor(min_vel=0, max_vel=float('+inf'),
                                 accel_time=0, decel_time=0)
            ret.append(v_motor)
        return ret

    MAX_ITER = 100000

    def _estimate(self, max_iter=None):
        """Estimate time and intervals of a scan.

        Time estimation considers motion time (including going to the start
        position) and acquisition time.

        Interval estimation is a number of scan trajectory intervals.
        """
        with_time = hasattr(self.macro, "getTimeEstimation")
        with_interval = hasattr(self.macro, "getIntervalEstimation")
        if with_time and with_interval:
            t = self.macro.getTimeEstimation()
            i = self.macro.getIntervalEstimation()
            return t, i

        max_iter = max_iter or self.MAX_ITER
        iterator = self.generator()
        total_time = 0.0
        point_nb = 0
        interval_nb = None
        try:
            if not with_time:
                try:
                    start_pos = self.motion.readPosition(force=True)
                    v_motors = self.get_virtual_motors()
                    motion_time, acq_time = 0.0, 0.0
                    while point_nb < max_iter:
                        step = next(iterator)
                        end_pos = step['positions']
                        max_path_duration = 0.0
                        for v_motor, start, stop in zip(v_motors,
                                                        start_pos,
                                                        end_pos):
                            path = MotionPath(v_motor, start, stop)
                            max_path_duration = max(
                                max_path_duration, path.duration)
                        integ_time = step.get("integ_time", 0.0)
                        acq_time += integ_time
                        motion_time += max_path_duration
                        total_time += integ_time + max_path_duration
                        point_nb += 1
                        start_pos = end_pos
                finally:
                    if with_interval:
                        interval_nb = self.macro.getIntervalEstimation()
            else:
                try:
                    while point_nb < max_iter:
                        step = next(iterator)
                        point_nb += 1
                finally:
                    total_time = self.macro.getTimeEstimation()
        except StopIteration:
            pass
        else:
            # max iteration reached.
            total_time = -total_time
            point_nb = -point_nb
        if interval_nb is None:
            if point_nb < 1:
                interval_nb = point_nb + 1
            elif point_nb > 1:
                interval_nb = point_nb - 1
            else:
                interval_nb = 0
                self.warning("Estimation of intervals have not succeeded")
        return total_time, interval_nb

    @property
    def data(self):
        """Scan data."""
        return self._data

    @property
    def data_handler(self):
        return self._data_handler

    @property
    def macro(self):
        return self._macro()

    @property
    def measurement_group(self):
        return self._measurement_group

    @property
    def generator(self):
        """Generator of steps or waypoints used in this scan."""
        return self._generator()

    @property
    def motion(self):
        return self._motion

    @property
    def moveables(self):
        return self._moveables

    @property
    def steps(self):
        if not hasattr(self, '_steps'):
            self._steps = enumerate(self.generator())
        return self._steps

    def start(self):
        self.do_backup()
        env = self._env
        env['startts'] = ts = time.time()
        env['starttime'] = datetime.datetime.fromtimestamp(ts)
        env['acqtime'] = 0
        env['motiontime'] = 0
        env['deadtime'] = 0
        self.data.start()

    def end(self):
        env = self._env
        env['endts'] = end_ts = time.time()
        env['endtime'] = datetime.datetime.fromtimestamp(end_ts)
        total_time = end_ts - env['startts']
        # estimated = env['estimatedtime']
        acq_time = env['acqtime']
        # env['deadtime'] = 100.0 * (total_time - estimated) / total_time

        env['deadtime'] = total_time - acq_time
        if 'delaytime' in env:
            env['motiontime'] = total_time - acq_time - env['delaytime']
        elif 'motiontime' in env:
            env['delaytime'] = total_time - acq_time - env['motiontime']

        self.data.end()
        try:
            scan_history = self.macro.getEnv('ScanHistory')
        except UnknownEnv:
            scan_history = []

        scan_file = env['ScanFile']
        if isinstance(scan_file, str):
            scan_file = scan_file,

        names = [col.name for col in env['datadesc']]
        history = dict(startts=env['startts'], endts=env['endts'],
                       estimatedtime=env['estimatedtime'],
                       deadtime=env['deadtime'], title=env['title'],
                       serialno=env['serialno'], user=env['user'],
                       ScanFile=scan_file, ScanDir=env['ScanDir'],
                       endstatus=ScanEndStatus.whatis(env['endstatus']),
                       channels=names)
        scan_history.append(history)
        while len(scan_history) > self.MAX_SCAN_HISTORY:
            scan_history.pop(0)
        self.macro.setEnv('ScanHistory', scan_history)

    def scan(self):
        for _ in self.step_scan():
            pass

    def step_scan(self):
        macro = self.macro
        if hasattr(macro, 'getHooks'):
            for hook in macro.getHooks('pre-scan'):
                hook()
        self.start()
        try:
            for i in self.scan_loop():
                self.macro.pausePoint()
                yield i
            endstatus = ScanEndStatus.Normal
        except StopException:
            endstatus = ScanEndStatus.Stop
            raise
        except AbortException:
            endstatus = ScanEndStatus.Abort
            raise
        except Exception:
            endstatus = ScanEndStatus.Exception
            raise
        finally:
            self._env["endstatus"] = endstatus
            self.end()
            self.do_restore()
            if endstatus == ScanEndStatus.Normal:
                if hasattr(macro, 'getHooks'):
                    for hook in macro.getHooks('post-scan'):
                        hook()

    def scan_loop(self):
        raise NotImplementedError('Scan method cannot be called by '
                                  'abstract class')

    def do_backup(self):
        try:
            if hasattr(self.macro, 'do_backup'):
                self.macro.do_backup()
        except Exception:
            msg = ("Failed to execute 'do_backup' method of the %s macro" %
                   self.macro.getName())
            self.macro.debug(msg)
            self.macro.debug('Details: ', exc_info=True)
            raise ScanException('error while doing a backup')

    def do_restore(self):
        try:
            if hasattr(self.macro, 'do_restore'):
                self.macro.do_restore()
        except Exception:
            msg = ("Failed to execute 'do_restore' method of the %s macro" %
                   self.macro.getName())
            self.macro.debug(msg)
            self.macro.debug('Details: ', exc_info=True)
            raise ScanException('error while restoring a backup')


class SScan(GScan):
    """Step scan"""

    def __init__(self, macro, generator=None, moveables=[], env={},
                 constraints=[], extrainfodesc=[]):
        GScan.__init__(self, macro, generator=generator, moveables=moveables,
                       env=env, constraints=constraints,
                       extrainfodesc=extrainfodesc)
        self._deterministic_scan = None

    @property
    def deterministic_scan(self):
        """Check if the scan is a deterministic scan.

        Scan is considered as deterministic scan if
        the `~sardana.macroserver.macro.Macro` specialization owning
        the scan object contains ``nb_points`` and ``integ_time`` attributes.

        Scan flow depends on this property (some optimizations are applied).
        These can be disabled by setting this property to `False`.
        """
        if self._deterministic_scan is None:
            macro = self.macro
            if hasattr(macro, "nb_points") and hasattr(macro, "integ_time"):
                self._deterministic_scan = True
            else:
                self._deterministic_scan = False
        return self._deterministic_scan

    @deterministic_scan.setter
    def deterministic_scan(self, value):
        self._deterministic_scan = value

    def scan_loop(self):
        lstep = None
        macro = self.macro
        scream = False

        if hasattr(macro, "nb_points"):
            nb_points = float(macro.nb_points)
            scream = True
        else:
            yield 0.0

        if self.deterministic_scan:
            self.measurement_group.putIntegrationTime(macro.integ_time)
            self.measurement_group.setNbStarts(macro.nb_points)
            self.measurement_group.prepare()

        self._sum_motion_time = 0
        self._sum_acq_time = 0

        for i, step in self.steps:
            # allow scan to be stopped between points
            macro.checkPoint()
            self.stepUp(i, step, lstep)
            lstep = step
            if scream:
                yield ((i + 1) / nb_points) * 100

        if not scream:
            yield 100.0

        self._env['motiontime'] = self._sum_motion_time
        self._env['acqtime'] = self._sum_acq_time

    def stepUp(self, n, step, lstep):
        motion, mg = self.motion, self.measurement_group
        startts = self._env['startts']

        # pre-move hooks
        for hook in step.get('pre-move-hooks', ()):
            hook()
            try:
                step['extrainfo'].update(hook.getStepExtraInfo())
            except InterruptException:
                raise
            except Exception:
                pass

        # Move
        self.debug("[START] motion")
        move_start_time = time.time()
        try:
            state, positions = motion.move(step['positions'])
            self._sum_motion_time += time.time() - move_start_time
            self._env['motiontime'] = self._sum_motion_time
        except InterruptException:
            raise
        except Exception:
            self.dump_information(n, step, self.motion.moveable_list)
            raise
        self.debug("[ END ] motion")

        curr_time = time.time()
        dt = curr_time - startts

        # post-move hooks
        for hook in step.get('post-move-hooks', ()):
            hook()
            try:
                step['extrainfo'].update(hook.getStepExtraInfo())
            except InterruptException:
                raise
            except Exception:
                pass

        # allow scan to be stopped between motion and data acquisition
        self.macro.checkPoint()

        if state != Ready:
            self.dump_information(n, step, self.motion.moveable_list)
            m = "Scan aborted after problematic motion: " \
                "Motion ended with %s\n" % str(state)
            raise ScanException({'msg': m})

        # pre-acq hooks
        for hook in step.get('pre-acq-hooks', ()):
            hook()
            try:
                step['extrainfo'].update(hook.getStepExtraInfo())
            except InterruptException:
                raise
            except Exception:
                pass

        integ_time = step['integ_time']
        # Acquire data
        self.debug("[START] acquisition")
        try:
            if self.deterministic_scan:
                state, data_line = mg.count_raw()
            else:
                state, data_line = mg.count(integ_time)
        except InterruptException:
            raise
        except Exception:
            names = mg.ElementList
            elements = [self.macro.getObj(name) for name in names]
            self.dump_information(n, step, elements)
            raise
        for ec in self._extra_columns:
            data_line[ec.getName()] = ec.read()
        self.debug("[ END ] acquisition")
        self._sum_acq_time += integ_time
        self._env['acqtime'] = self._sum_acq_time

        # post-acq hooks
        for hook in step.get('post-acq-hooks', ()):
            hook()
            try:
                step['extrainfo'].update(hook.getStepExtraInfo())
            except InterruptException:
                raise
            except Exception:
                pass

        # Add final moveable positions
        data_line['point_nb'] = n
        data_line['timestamp'] = dt
        for i, m in enumerate(self.moveables):
            data_line[m.moveable.getName()] = positions[i]

        # Add extra data coming in the step['extrainfo'] dictionary
        if 'extrainfo' in step:
            data_line.update(step['extrainfo'])

        self.data.addRecord(data_line)

        # post-step hooks
        for hook in step.get('post-step-hooks', ()):
            hook()
            try:
                step['extrainfo'].update(hook.getStepExtraInfo())
            except InterruptException:
                raise
            except Exception:
                pass

    def dump_information(self, n, step, elements):
        msg = ["Report: Stopped at step #" + str(n) + " with:"]
        for element in elements:
            msg.append(element.information())
        self.macro.info("\n".join(msg))


class CScan(GScan):
    """Continuous scan abstract class. Implements helper methods."""

    def __init__(self, macro, generator=None, moveables=[],
                 env={}, constraints=[], extrainfodesc=[]):
        GScan.__init__(self, macro, generator=generator,
                       moveables=moveables, env=env, constraints=constraints,
                       extrainfodesc=extrainfodesc)
        self._current_waypoint_finished = False
        self._all_waypoints_finished = False
        self.motion_event = threading.Event()
        self.motion_end_event = threading.Event()
        data_structures = self.populate_moveables_data_structures(moveables)
        self._moveables_trees, \
            physical_moveables_names, \
            self._physical_moveables = data_structures
        # The physical motion object contains only physical motors - no pseudo
        # motors (in case the pseudomotors are involved in the scan,
        # it comprarises the underneath physical motors)
        # This is due to the fact that the CTScan coordinates the
        # pseudomotors' underneeth physical motors on on their constant
        # velocity in contrary to the the CScan which do not coordinate them
        if len(physical_moveables_names) > 0:
            self._physical_motion = self.macro.getMotion(
                physical_moveables_names)
        else:
            self._physical_motion = None

    def populate_moveables_data_structures(self, moveables):
        """Populates moveables data structures.
        :param moveables: (list<Moveable>) data structures will be generated
        for these moveables
        :return (moveable_trees, physical_moveables_names, physical_moveables)

        - moveable_trees (list<Tree>) - each tree represent one Moveable
          with its hierarchy of inferior moveables.
        - physical_moveables_names (list<str> - list of the names of
          the physical moveables. List order is important and preserved.
        - physical_moveables (list<Moveable> - list of the moveable
          objects. List order is important and preserved.

        """

        def generate_moveable_node(macro, moveable):
            """Function to generate a moveable data structures based on
            moveable object. Internally can be recursively called if
            moveable is a PseudoMotor.
            :param moveable: moveable object
            :return (moveable_node, physical_moveables_names,
                    physical_moveables)
                - moveable_node (BaseNode) - can be a BranchNode if moveable
                      is a PseudoMotor or a LeafNode if moveable is a
                      PhysicalMotor.
                - physical_moveables_names (list<str> - list of the names of
                      the physical moveables. List order is important and
                      preserved.
                - physical_moveables (list<Moveable> - list of the moveable
                      objects. List order is important and preserved.
            """
            moveable_node = None
            physical_moveables_names = []
            physical_moveables = []
            moveable_type = moveable.getType()
            if moveable_type == "PseudoMotor":
                moveable_node = BranchNode(moveable)
                moveables_names = moveable.elements
                sub_moveables = [macro.getMoveable(name)
                                 for name in moveables_names]
                for sub_moveable in sub_moveables:
                    sub_moveable_node, \
                        _physical_moveables_names, \
                        _physical_moveables = \
                        generate_moveable_node(macro, sub_moveable)
                    physical_moveables_names += _physical_moveables_names
                    physical_moveables += _physical_moveables
                    moveable_node.addChild(sub_moveable_node)
            elif moveable_type == "Motor":
                moveable_node = LeafNode(moveable)
                moveable_name = moveable.getName()
                physical_moveables_names.append(moveable_name)
                physical_moveables.append(moveable)
            return moveable_node, physical_moveables_names, physical_moveables

        moveable_trees = []
        physical_moveables_names = []
        physical_moveables = []

        for moveable in moveables:
            moveable_root_node, _physical_moveables_names, \
                _physical_moveables = generate_moveable_node(self.macro,
                                                             moveable.moveable)
            moveable_tree = Tree(moveable_root_node)
            moveable_trees.append(moveable_tree)
            physical_moveables_names += _physical_moveables_names
            physical_moveables += _physical_moveables
        return moveable_trees, physical_moveables_names, physical_moveables

    def get_moveables_trees(self):
        """Returns reference to the list of the moveables trees"""
        return self._moveables_trees

    def on_waypoints_end(self, restore_positions=None):
        """To be called by the waypoint thread to handle the end of waypoints
        (either because no more waypoints or because a macro abort was
        triggered)"""
        self.set_all_waypoints_finished(True)
        if restore_positions is not None:
            self._setFastMotions()
            self.macro.info("Correcting overshoot...")
            self.motion.move(restore_positions)
        self.motion_end_event.set()
        self.motion_event.set()

    def go_through_waypoints(self, iterate_only=False):
        """Go through the different waypoints."""
        try:
            self._go_through_waypoints()
        except Exception:
            self.on_waypoints_end()
            raise

    def _go_through_waypoints(self):
        """
        Internal, unprotected method to go through the different waypoints.
        """
        raise NotImplementedError("_go_through_waypoints must be implemented"
                                  " in CScan derived classes")

    def waypoint_estimation(self):
        """
        Internal, unprotected method to go through the different waypoints.
        """
        motion, waypoints = self.motion, self.generator()
        total_duration = 0
        # v_motors = self.get_virtual_motors()
        curr_positions, last_end_positions = motion.readPosition(
            force=True), None
        for i, waypoint in enumerate(waypoints):
            start_positions = waypoint.get(
                'start_positions', last_end_positions)
            positions = waypoint['positions']
            if start_positions is None:
                last_end_positions = positions
                continue

            waypoint_info = self.prepare_waypoint(waypoint, start_positions,
                                                  iterate_only=True)
            motion_paths, delta_start, acq_duration = waypoint_info

            start_path, end_path = [], []
            for path in motion_paths:
                start_path.append(path.initial_user_pos)
                end_path.append(path.final_user_pos)

            # move from last waypoint to start position of this waypoint
            first_duration = 0
            if i == 1:
                # first waypoint means, moving from current position to the
                # start of first waypoint
                initial = curr_positions
            else:
                initial = start_positions
            for _path, start, end in zip(motion_paths, initial, start_path):
                v_motor = _path.motor
                path = MotionPath(v_motor, start, end)
                first_duration = max(first_duration, path.duration)

            # move from waypoint start position to waypoint end position
            second_duration = 0
            for _path, start, end in zip(motion_paths, start_path, end_path):
                v_motor = _path.motor
                path = MotionPath(v_motor, start, end)
                second_duration = max(second_duration, path.duration)

            total_duration += first_duration + second_duration

            last_end_positions = end_path

        # add correct overshoot time
        overshoot_duration = 0
        for _path, start, end in zip(motion_paths, last_end_positions,
                                     positions):
            v_motor = _path.motor
            path = MotionPath(v_motor, start, end)
            overshoot_duration = max(overshoot_duration, path.duration)

        total_duration += overshoot_duration
        return total_duration

    def prepare_waypoint(self, waypoint, start_positions, iterate_only=False):
        raise NotImplementedError("prepare_waypoint must be implemented in " +
                                  "CScan derived classes")

    def set_all_waypoints_finished(self, v):
        self._all_waypoints_finished = v

    def _backup_motor(self):
        """Backup motors initial state (velocity, acceleration and
        deceleration).
        """
        self._backup = backup = []
        for moveable in self._physical_moveables:
            # first backup all motor parameters
            motor = moveable
            try:
                velocity = motor.getVelocity()
                accel_time = motor.getAcceleration()
                decel_time = motor.getDeceleration()
                motor_backup = dict(moveable=moveable, velocity=velocity,
                                    acceleration=accel_time,
                                    deceleration=decel_time)
                self.debug("Backup of %s", motor)
            except AttributeError:
                motor_backup = None
            backup.append(motor_backup)

    def do_backup(self):
        super(CScan, self).do_backup()
        self._backup_motor()

    def _restore_motors(self):
        """Restore changed motors to initial state (velocity, acceleration and
        deceleration).
        """
        for motor_backup in self._backup:
            if motor_backup is None:
                continue
            motor = motor_backup['moveable']
            attributes = OrderedDict(velocity=motor_backup["velocity"],
                                     acceleration=motor_backup["acceleration"],
                                     deceleration=motor_backup["deceleration"])
            try:
                self.configure_motor(motor, attributes)
            except ScanException as e:
                msg = "Error when restoring motor's backup (%s)" % e
                raise ScanException(msg)

    def do_restore(self):
        # Restore motor backups (vel, acc, ...) first so the macro's
        # do_restore finds the system as before GSF found it.
        # This is especially important for dscan macros which must return
        # to inital position at nominal speed even after user stop.
        self._restore_motors()
        super(CScan, self).do_restore()

    def _setFastMotions(self, motors=None):
        '''make given motors go at their max speed and accel'''
        if motors is None:
            motors = [b.get('moveable') for b in self._backup if b is not None]

        for motor in motors:
            attributes = OrderedDict(velocity=self.get_max_top_velocity(motor),
                                     acceleration=self.get_min_acc_time(motor),
                                     deceleration=self.get_min_dec_time(motor))
            try:
                self.configure_motor(motor, attributes)
            except ScanException as e:
                msg = "Error when setting fast motion (%s)" % e
                raise ScanException(msg)

    def get_max_top_velocity(self, motor):
        """Helper method to find the maximum top velocity for the motor.
        If the motor doesn't have a defined range for top velocity,
        then use the current top velocity"""

        top_vel_obj = motor.getVelocityObj()
        _, max_top_vel = top_vel_obj.getRange()
        try:
            max_top_vel = float(max_top_vel)
        except ValueError:
            try:
                # hack to avoid recursive velocity reduction
                self._maxVelDict = getattr(self, '_maxVelDict', {})
                if motor not in self._maxVelDict:
                    self._maxVelDict[motor] = motor.getVelocity()
                max_top_vel = self._maxVelDict[motor]
            except AttributeError:
                pass
        # Taurus4 reports -inf or inf when no limits are defined (NotSpecified)
        if np.isinf(max_top_vel):
            max_top_vel = motor.getVelocity()
        return max_top_vel

    def get_min_acc_time(self, motor):
        """Helper method to find the minimum acceleration time for the motor.
        If the motor doesn't have a defined range for the acceleration time,
        then use the current acceleration time"""

        acc_time_obj = motor.getAccelerationObj()
        min_acc_time, _ = acc_time_obj.getRange()
        try:
            min_acc_time = float(min_acc_time)
        except ValueError:
            min_acc_time = motor.getAcceleration()
        # Taurus4 reports -inf or inf when no limits are defined (NotSpecified)
        if np.isinf(min_acc_time):
            min_acc_time = motor.getAcceleration()
        return min_acc_time

    def get_min_dec_time(self, motor):
        """Helper method to find the minimum deceleration time for the motor.
        If the motor doesn't have a defined range for the acceleration time,
        then use the current acceleration time"""

        dec_time_obj = motor.getDecelerationObj()
        min_dec_time, _ = dec_time_obj.getRange()
        try:
            min_dec_time = float(min_dec_time)
        except ValueError:
            min_dec_time = motor.getDeceleration()
        # Taurus4 reports -inf or inf when no limits are defined (NotSpecified)
        if np.isinf(min_dec_time):
            min_dec_time = motor.getAcceleration()
        return min_dec_time

    def set_max_top_velocity(self, motor):
        """Helper method to set the maximum top velocity for the motor to
        its maximum allowed limit."""

        v = self.get_max_top_velocity(motor)
        try:
            motor.setVelocity(v)
        except Exception:
            pass

    def get_min_pos(self, motor):
        '''Helper method to find the minimum position for a given motor.
        If the motor doesn't define its minimum position, then the negative
        infinite float representation is returned.
        '''
        pos_obj = motor.getPositionObj()
        min_pos, _ = pos_obj.getRange()
        try:
            # Taurus 4 uses quantities however Sardana does not support them
            # yet - use magnitude for the moment.
            min_pos = min_pos.magnitude
        except AttributeError:
            pass
        try:
            min_pos = float(min_pos)
        except ValueError:
            min_pos = float('-Inf')
        return min_pos

    def get_max_pos(self, motor):
        '''Helper method to find the maximum position for a given motor.
        If the motor doesn't define its maximum position, then the positive
        infinite float representation is returned.
        '''
        pos_obj = motor.getPositionObj()
        _, max_pos = pos_obj.getRange()
        try:
            # Taurus 4 uses quantities however Sardana does not support them
            # yet - use magnitude for the moment.
            max_pos = max_pos.magnitude
        except AttributeError:
            pass
        try:
            max_pos = float(max_pos)
        except ValueError:
            max_pos = float('Inf')
        return max_pos

    def configure_motor(self, motor, attributes):
        """Configure motor with a given attribute values.

        :param motor: (Motor or Moveable) motor to be configured
        :param attributes: (OrderedDict) dictionary with attribute names (keys)
            and attribute values (values)
        """
        for param, value in list(attributes.items()):
            try:
                motor._getAttrEG(param).write(value)
            except Exception:
                self.macro.debug("Error when setting %s of %s" %
                                 (param, motor.name), exc_info=True)
                msg = "setting %s of %s to %r failed" %\
                    (param, motor.name, value)
                raise ScanException(msg)


class CSScan(CScan):
    """Continuous scan controlled by software"""

    def __init__(self, macro, waypointGenerator=None, periodGenerator=None,
                 moveables=[], env={}, constraints=[], extrainfodesc=[]):
        CScan.__init__(self, macro, generator=waypointGenerator,
                       moveables=moveables, env=env, constraints=constraints,
                       extrainfodesc=extrainfodesc)
        self._periodGenerator = periodGenerator

    def _calculateTotalAcquisitionTime(self):
        return None

    @property
    def period_generator(self):
        return self._periodGenerator

    @property
    def period_steps(self):
        if not hasattr(self, '_period_steps'):
            self._period_steps = enumerate(self.period_generator())
        return self._period_steps

    def prepare_waypoint(self, waypoint, start_positions, iterate_only=False):
        slow_down = waypoint.get('slow_down', 1)
        positions = waypoint['positions']

        duration, cruise_duration, delta_start = 0, 0, 0
        ideal_paths, real_paths = [], []
        for i, (moveable, position) in enumerate(zip(self.moveables,
                                                     positions)):
            motor = moveable.moveable

            coordinate = True
            try:
                base_vel, top_vel = motor.getBaseRate(), motor.getVelocity()
                accel_time = motor.getAcceleration()
                decel_time = motor.getDeceleration()

                if slow_down > 0:
                    # find and set the maximum top velocity for the motor.
                    # If the motor doesn't have a defined range for top
                    # velocity, then use the current top velocity
                    max_top_vel = self.get_max_top_velocity(motor)
                    if not iterate_only:
                        motor.setVelocity(max_top_vel)
                else:
                    max_top_vel = top_vel
            except AttributeError:
                if not iterate_only:
                    self.macro.warning(
                        "%s motion will not be coordinated", motor)
                base_vel, top_vel, max_top_vel = 0, float(
                    '+inf'), float('+inf')
                accel_time, decel_time = 0, 0
                coordinate = False

            last_user_pos = start_positions[i]

            real_vmotor = VMotor(min_vel=base_vel, max_vel=max_top_vel,
                                 accel_time=accel_time,
                                 decel_time=decel_time)
            real_path = MotionPath(real_vmotor, last_user_pos, position)
            real_path.moveable = moveable
            real_path.apply_correction = coordinate

            # Find the cruise duration of motion at top velocity. For this
            # create a virtual motor which has instantaneous acceleration and
            # deceleration
            ideal_vmotor = VMotor(min_vel=base_vel, max_vel=max_top_vel,
                                  accel_time=0, decel_time=0)

            # create a path which will tell us which is the cruise
            # duration of this motion at top velocity
            ideal_path = MotionPath(ideal_vmotor, last_user_pos, position)
            ideal_path.moveable = moveable
            ideal_path.apply_correction = coordinate

            # if really motor is moving in this waypoint
            if ideal_path.displacement > 0:
                # recalculate time to reach maximum velocity
                delta_start = max(delta_start, accel_time)

            # recalculate cruise duration of motion at top velocity
            cruise_duration = max(cruise_duration, ideal_path.duration)
            duration = max(duration, real_path.duration)

            ideal_paths.append(ideal_path)
            real_paths.append(real_path)

        if slow_down <= 0:
            return real_paths, 0, duration

        # after finding the duration, introduce the slow down factor added
        # by the user
        cruise_duration /= slow_down

        if cruise_duration == 0:
            cruise_duration = float('+inf')

        # now that we have the appropriate top velocity for all motors, the
        # cruise duration of motion at top velocity, and the time it takes to
        # recalculate
        for path in ideal_paths:
            vmotor = path.motor
            # in the case of pseudo motors or not moving a motor...
            if not path.apply_correction or path.displacement == 0:
                continue
            moveable = path.moveable
            motor = moveable.moveable
            new_top_vel = path.displacement / cruise_duration
            vmotor.setMaxVelocity(new_top_vel)
            accel_t, decel_t = motor.getAcceleration(), motor.getDeceleration()
            base_vel = vmotor.getMinVelocity()
            vmotor.setAccelerationTime(accel_t)
            vmotor.setDecelerationTime(decel_t)
            disp_sign = path.positive_displacement and 1 or -1
            new_initial_pos = path.initial_user_pos - accel_t * 0.5 * \
                disp_sign * (new_top_vel + base_vel) - disp_sign * \
                new_top_vel * (delta_start - accel_t)
            path.setInitialUserPos(new_initial_pos)
            new_final_pos = path.final_user_pos + \
                disp_sign * vmotor.displacement_reach_min_vel
            path.setFinalUserPos(new_final_pos)

        return ideal_paths, delta_start, cruise_duration

    def go_through_waypoints(self, iterate_only=False):
        """go through the different waypoints."""
        try:
            self._go_through_waypoints()
        except Exception:
            self.macro.debug('An error occurred moving to waypoints')
            self.macro.debug('Details: ', exc_info=True)
            self.on_waypoints_end()
            raise ScanException('error while moving to waypoints')

    def _go_through_waypoints(self):
        """
        Internal, unprotected method to go through the different waypoints.
        """
        macro, motion, waypoints = self.macro, self.motion, self.steps
        self.macro.debug("_go_through_waypoints() entering...")

        last_positions = None
        for _, waypoint in waypoints:
            self.macro.debug("Waypoint iteration...")
            start_positions = waypoint.get('start_positions')
            positions = waypoint['positions']
            if start_positions is None:
                start_positions = last_positions
            if start_positions is None:
                last_positions = positions
                continue

            waypoint_info = self.prepare_waypoint(waypoint, start_positions)
            motion_paths, delta_start, acq_duration = waypoint_info

            self.acq_duration = acq_duration

            # execute pre-move hooks
            for hook in waypoint.get('pre-move-hooks', []):
                hook()

            start_pos, final_pos = [], []
            for path in motion_paths:
                start_pos.append(path.initial_user_pos)
                final_pos.append(path.final_user_pos)

            if macro.isStopped():
                self.on_waypoints_end()
                return

            # move to start position
            self.macro.debug("Moving to start position: %s" % repr(start_pos))
            motion.move(start_pos)

            if macro.isStopped():
                self.on_waypoints_end()
                return

            # prepare motor(s) with the velocity required for synchronization
            for path in motion_paths:
                if not path.apply_correction:
                    continue
                vmotor = path.motor
                motor = path.moveable.moveable
                motor.setVelocity(vmotor.getMaxVelocity())

            if macro.isStopped():
                self.on_waypoints_end()
                return

            self.timestamp_to_start = time.time() + delta_start
            self.motion_event.set()

            # move to waypoint end position
            motion.move(final_pos)

            self.motion_event.clear()

            if macro.isStopped():
                return self.on_waypoints_end()

            # execute post-move hooks
            for hook in waypoint.get('post-move-hooks', []):
                hook()

            if start_positions is None:
                last_positions = positions

        self.on_waypoints_end(positions)

    def scan_loop(self):
        motion = self.motion
        mg = self.measurement_group
        # waypoints = self.steps
        macro = self.macro
        manager = macro.getManager()
        scream = False
        motion_event = self.motion_event
        startts = self._env['startts']

        sum_delay = 0
        sum_integ_time = 0

        if hasattr(macro, "nb_points"):
            nb_points = float(macro.nb_points)
            scream = True
        else:
            yield 0.0

        # moveables = [m.moveable for m in self.moveables]
        period_steps = self.period_steps
        point_nb, step = -1, None
        # data = self.data

        # start move & acquisition as close as possible
        # from this point on synchronization becomes critical
        manager.add_job(self.go_through_waypoints)

        while not self._all_waypoints_finished:

            # wait for motor to reach start position
            motion_event.wait()

            # allow scan to stop
            macro.checkPoint()

            if self._all_waypoints_finished:
                break

            # wait for motor to reach max velocity
            start_time = time.time()
            deltat = self.timestamp_to_start - start_time
            if deltat > 0:
                time.sleep(deltat)
            curr_time = acq_start_time = time.time()
            integ_time = 0

            # Acquisition loop: acquire consecutively until waypoint asks to
            # stop or we see that we will enter deceleration time in next
            # acquisition
            while motion_event.is_set():

                # allow scan to stop
                macro.checkPoint()

                try:
                    point_nb, step = next(period_steps)
                except StopIteration:
                    self._all_waypoints_finished = True
                    break

                integ_time = step['integ_time']

                # If there is no more time to acquire... stop!
                elapsed_time = time.time() - acq_start_time
                if elapsed_time + integ_time > self.acq_duration:
                    motion_event.clear()
                    break

                # pre-acq hooks
                for hook in step.get('pre-acq-hooks', ()):
                    hook()
                    try:
                        step['extrainfo'].update(hook.getStepExtraInfo())
                    except InterruptException:
                        self._all_waypoints_finished = True
                        raise
                    except Exception:
                        pass

                # allow scan to stop
                macro.checkPoint()

                positions = motion.readPosition(force=True)

                dt = time.time() - startts

                # Acquire data
                self.debug("[START] acquisition")
                state, data_line = mg.count(integ_time)

                sum_integ_time += integ_time

                # allow scan to stop
                macro.checkPoint()

                # After acquisition, test if we are asked to stop, probably
                # because the motor are stopped. In this case discard the last
                # acquisition
                if not self._all_waypoints_finished:
                    for ec in self._extra_columns:
                        data_line[ec.getName()] = ec.read()
                    self.debug("[ END ] acquisition")

                    # post-acq hooks
                    for hook in step.get('post-acq-hooks', ()):
                        hook()
                        try:
                            step['extrainfo'].update(hook.getStepExtraInfo())
                        except InterruptException:
                            self._all_waypoints_finished = True
                            raise
                        except Exception:
                            pass

                    # Add final moveable positions
                    data_line['point_nb'] = point_nb
                    data_line['timestamp'] = dt
                    for i, m in enumerate(self.moveables):
                        data_line[m.moveable.getName()] = positions[i]

                    # Add extra data coming in the step['extrainfo'] dictionary
                    if 'extrainfo' in step:
                        data_line.update(step['extrainfo'])

                    self.data.addRecord(data_line)

                    if scream:
                        yield ((point_nb + 1) / nb_points) * 100
                else:
                    break
                old_curr_time = curr_time
                curr_time = time.time()
                sum_delay += (curr_time - old_curr_time) - integ_time

        self.motion_end_event.wait()

        env = self._env
        env['acqtime'] = sum_integ_time
        env['delaytime'] = sum_delay

        if not scream:
            yield 100.0


class CAcquisition(object):

    def __init__(self):
        # protect older versions of Taurus (without the worker_cls argument)
        # remove it whenever we bump Taurus dependency
        try:
            self._thread_pool = ThreadPool(name="ValueBufferTH",
                                           Psize=1,
                                           Qsize=100000,
                                           worker_cls=OmniWorker)
        except TypeError:
            import taurus
            taurus.warning("Your Sardana system is affected by bug"
                           "tango-controls/pytango#307. Please use "
                           "Taurus with taurus-org/taurus#1081.")
            self._thread_pool = ThreadPool(name="ValueBufferTH",
                                           Psize=1,
                                           Qsize=100000)
        self._countdown_latch = CountLatch()
        self._index_offset = 0

    def value_buffer_changed(self, channel, value_buffer):
        """Delegate processing of value buffer events to a worker thread."""
        # value_buffer is a dictionary with at least keys: data, index
        # and its values are of type sequence
        # e.g. dict(data=seq<float>, index=seq<int>)
        if value_buffer is None:
            return

        full_name = channel.getFullName()

        info = {'label': full_name}
        if self._index_offset != 0:
            idx = np.array(value_buffer['index'])
            idx += self._index_offset
            value_buffer['index'] = idx.tolist()
        info.update(value_buffer)
        # info is a dictionary with at least keys: label, data,
        # index and its values are of type string for label and
        # sequence for data, index
        # e.g. dict(label=str, data=seq<float>, index=seq<int>)
        self._countdown_latch.count_up()
        # only one thread is present in the pool so jobs are serialized
        self._thread_pool.add(self.data.addData,
                              self._countdown_latch.count_down, info)

    def value_ref_buffer_changed(self, channel, value_ref_buffer):
        """Delegate processing of value buffer events to a worker thread."""
        # value_ref_buffer is a dictionary with at least keys:
        # value_ref, index
        # and its values are of type sequence
        # e.g. dict(value_ref=seq<float>, index=seq<int>)
        if value_ref_buffer is None:
            return

        full_name = channel.getFullName()

        info = {'label': full_name}
        if self._index_offset != 0:
            idx = np.array(value_ref_buffer['index'])
            idx += self._index_offset
            value_ref_buffer['index'] = idx.tolist()
        info.update(value_ref_buffer)
        # info is a dictionary with at least keys: label, data,
        # index and its values are of type string for label and
        # sequence for data, index
        # e.g. dict(label=str, data=seq<float>, index=seq<int>)
        self._countdown_latch.count_up()
        # only one thread is present in the pool so jobs are serialized
        # TODO: think if the RecordList.addData is the best API for
        # passing value references
        self._thread_pool.add(self.data.addData,
                              self._countdown_latch.count_down, info)

    def wait_value_buffer(self):
        """Wait until all value buffer events are processed."""
        self._countdown_latch.wait()

    def join_thread_pool(self):
        """Dispose the thread pool. Call it when you finish with processing
        value_buffer events."""
        self._thread_pool.join()

    @staticmethod
    def is_measurement_group_compatible(measurement_group):
        """Check if the given measurement group is compatible with continuous
        acquisition. Non compatible measurement groups are those with channels
        of the following types:
          - external channels (Tango attributes)
          - pseudo counters that are not based on physical channels

        .. todo:: add validation for psuedo counters
        """
        non_compatible_channels = []
        validator = TangoDeviceNameValidator()
        for channel_info in measurement_group.getChannels():
            full_name = channel_info["full_name"]
            name = channel_info["name"]
            if not validator.isValid(full_name):
                non_compatible_channels.append(name)
        is_compatible = len(non_compatible_channels) == 0
        return is_compatible, non_compatible_channels


def generate_timestamps(synch_description, initial_timestamp=0):
    """Generate theoretical timestamps at which the acquisition should take
    place according to the synchronization description

    :param synch_description: synchronization description data
      structure
    :type synch_description: list<dict>
    :param initial_timestamp: initial timestamp to start from
    :type initial_timestamp: float
    """
    ret = dict()
    timestamp = initial_timestamp
    index = 0
    for group in synch_description:
        delay = group[SynchParam.Delay][SynchDomain.Time]
        total = group[SynchParam.Total][SynchDomain.Time]
        repeats = group[SynchParam.Repeats]
        timestamp += delay
        ret[index] = dict(timestamp=timestamp)
        index += 1
        for _ in range(1, repeats):
            timestamp += total
            ret[index] = dict(timestamp=timestamp)
            index += 1
    return ret


def generate_positions(motors, starts, finals, nb_points):
    ret = dict()
    # generate theoretical positions
    moveable_positions = []
    for start, final in zip(starts, finals):
        moveable_positions.append(
            np.linspace(start, final, nb_points))
    # prepare table header from moveables names
    dtype_spec = []
    for motor in motors:
        label = motor.getName()
        dtype_spec.append((label, 'float64'))
    # convert to numpy array for easier handling
    table = np.array(list(zip(*moveable_positions)), dtype=dtype_spec)
    n_rows = table.shape[0]
    for i in range(n_rows):
        row = dict()
        for label in table.dtype.names:
            row[label] = table[label][i]
        ret[i] = row
    return ret


class CTScan(CScan, CAcquisition):
    '''Generic continuous scan class.

    The idea is that the scan macros create an instance of this class,
    supplying in the constructor a reference to the macro that created the
    scan, a waypoint generator function pointer, a list of moveable items,
    an extra environment and a sequence of constrains.

    The generator must be a function yielding a dictionary with the following
    content (minimum) at each step of the scan:
      - 'start_positions' : The user positions where the **physical** motors
                            should start the active region of the waypoint scan
                            (usually during the constant velocity of the
                            **physical** motors)
      - 'positions'  : The user positions where the **physical** motors should
                       end the active region of the waypoint scan (since
                       currently the post-trigger acquisition is assumed this
                       does not mean leaving the constant velocity of the
                       **physical** motors - the constant velocity will be
                       maintained for the last point of the waypoint scan)
      - 'active_time' : Duration of the active region of the waypoint scan,
                        (in contrary to the *positions* configuration this one
                        includes the time necessary for hangling the last point
                        of the waypoint scan with its *latency time*
                        (in seconds)
      - 'pre-move-hooks' : (optional) a sequence of callables to be called
                           in strict order before starting to move
      - 'post-move-hooks': (optional) a sequence of callables to be called
                           in strict order after finishing the move
      - 'waypoint_id' : a hashable identifing the waypoint
      - 'check_func' : (optional) a list of callable objects.
                       callable(moveables, counters)
      - 'extravalues': (optional) a dictionary containing the values for
                       each extra info field. The extra information fields
                       must be described in extradesc (passed in the
                       constructor of the Gscan)

    .. todo::
        - instead of passing the *active_time* pass the synchronization
          description
        - decide whether *positions* should include the real end of the active
          region
        - decide if the *start_positions* and *positions* should operate
          directly on the physical motors or it would be more interesting on
          the pseudo motors

    .. note::
        The CTScan class has been included in Sardana
        on a provisional basis. Backwards incompatible changes
        (up to and including removal of the module) may occur if
        deemed necessary by the core developers.
    '''

    def __init__(self, macro, generator=None,
                 moveables=[], env={}, constraints=[], extrainfodesc=[]):
        CScan.__init__(self, macro, generator=generator,
                       moveables=moveables, env=env, constraints=constraints,
                       extrainfodesc=extrainfodesc)
        CAcquisition.__init__(self)
        self.__mntGrpSubscribed = False

    def prepare_waypoint(self, waypoint, start_positions, iterate_only=False):
        """Prepare list of MotionPath objects per each physical motor.
        :param waypoint: (dict) waypoint dictionary with necessary information
        :param start_positions: (list<
        float>) list of starting position per each
                                 physical motor
        :return (ideal_paths, acc_time, active_time)
                - ideal_paths: (list<MotionPath> representing motion attributes
                               of each physical motor)
                - acc_time: acceleration time which will be used during the
                            scan it corresponds to the longest acceleration
                            time of all the motors
                - active_time: time interval while all the physical motors will
                               maintain constant velocity"""

        positions = waypoint['positions']
        active_time = waypoint["active_time"]

        ideal_paths = []

        max_acc_time, max_dec_time = 0, 0
        for moveable, start_position, end_position in zip(
                self._physical_moveables, start_positions, positions):
            # motors that won't be moved do not participate in the
            # configuration selection
            # TODO: think of not attaching them to the waypoint at all
            if start_position == end_position:
                continue
            motor = moveable
            self.macro.debug("Motor: %s" % motor.getName())
            self.macro.debug("AccTime: %f" % self.get_min_acc_time(motor))
            self.macro.debug("DecTime: %f" % self.get_min_dec_time(motor))
            max_acc_time = max(self.get_min_acc_time(motor), max_acc_time)
            max_dec_time = max(self.get_min_dec_time(motor), max_dec_time)

        acc_time = max_acc_time
        dec_time = max_dec_time

        for moveable, start, end in \
                zip(self._physical_moveables, start_positions, positions):
            total_displacement = abs(end - start)
            direction = 1 if end > start else -1
            interval_displacement = total_displacement / self.macro.nr_interv
            # move further in order to acquire the last point at constant
            # velocity
            end = end + direction * interval_displacement

            base_vel = moveable.getBaseRate()
            ideal_vmotor = VMotor(accel_time=acc_time,
                                  decel_time=dec_time,
                                  min_vel=base_vel)
            ideal_path = MotionPath(ideal_vmotor, start, end, active_time)

            # check if calculated ideal velocity is accepted by hardware
            backup_vel = moveable.getVelocity(force=True)
            ideal_max_vel = try_vel = ideal_path.max_vel
            try:
                while True:
                    moveable.setVelocity(try_vel)
                    get_vel = moveable.getVelocity(force=True)
                    if get_vel < ideal_max_vel:
                        msg = 'Ideal scan velocity {0} of motor {1} cannot ' \
                              'be reached, {2} will be used instead'.format(
                                  ideal_max_vel, moveable.name, get_vel)
                        self.macro.warning(msg)
                        ideal_path.max_vel = get_vel
                        break
                    elif get_vel > ideal_max_vel:
                        try_vel -= (get_vel - try_vel)
                    else:
                        break
            except Exception:
                self.macro.debug("Unknown error when trying if hardware "
                                 "accepts ideal scan velocity", exc_info=1)
                ideal_path.max_vel = ideal_max_vel
            finally:
                moveable.setVelocity(backup_vel)

            ideal_path.moveable = moveable
            ideal_path.apply_correction = True
            ideal_paths.append(ideal_path)

        return ideal_paths, acc_time, active_time

    def _go_through_waypoints(self):
        """Internal, unprotected method to go through the different waypoints.
           It controls all the three objects: motion, trigger and measurement
           group."""
        macro = self.macro
        motion = self._physical_motion
        waypoints = self.steps
        measurement_group = self.measurement_group

        self.macro.debug("_go_through_waypoints() entering...")

        compatible, channels = \
            self.is_measurement_group_compatible(measurement_group)

        if not compatible:
            self.debug("Non compatible channels are: %s" % channels)
            msg = "Measurement group %s is not compatible with %s" %\
                  (measurement_group.getName(), macro.getName())
            raise ScanException(msg)

        # add listener of data events
        measurement_group.subscribeValueBuffer(self.value_buffer_changed)
        # add listener of value ref events
        measurement_group.subscribeValueRefBuffer(
            self.value_ref_buffer_changed)
        # initializing mntgrp subscription control variables
        self.__mntGrpSubscribed = True

        self.data.initial_data = {}
        last_positions = None
        self.macro.warning(
            "Motor positions and relative timestamp (dt) columns contains"
            " theoretical values"
        )
        for i, waypoint in waypoints:
            self.macro.debug("Waypoint iteration...")

            start_positions = waypoint.get('start_positions')
            positions = waypoint['positions']
            if start_positions is None:
                start_positions = last_positions
            if start_positions is None:
                last_positions = positions
                continue

            waypoint_info = self.prepare_waypoint(waypoint, start_positions)
            motion_paths, delta_start, acq_duration = waypoint_info

            self.acq_duration = acq_duration

            # execute pre-move hooks
            for hook in waypoint.get('pre-move-hooks', []):
                hook()
            # parepare list of start and final positions for the motion object
            start_pos, final_pos = [], []
            for path in motion_paths:
                start_pos.append(path.initial_user_pos)
                final_pos.append(path.final_user_pos)
            # validate if start and final positions are within range
            moveables = self._physical_moveables
            for start, final, moveable in zip(start_pos, final_pos, moveables):
                min_pos = self.get_min_pos(moveable)
                max_pos = self.get_max_pos(moveable)
                if start < min_pos or start > max_pos:
                    name = moveable.getName()
                    msg = 'start position of motor %s (%f) ' % (name, start) +\
                          'is out of range (%f, %f)' % (min_pos, max_pos)
                    raise ScanException(msg)
                if final < min_pos or final > max_pos:
                    name = moveable.getName()
                    msg = 'final position of motor %s (%f) ' % (name, final) +\
                          'is out of range (%f, %f)' % (min_pos, max_pos)
                    raise ScanException(msg)

            if macro.isStopped():
                self.on_waypoints_end()
                return

            # at least one motor must have different start and final positions
            if all(self.macro.starts == self.macro.finals):
                if len(self.macro.starts) > 1:
                    msg = "Scan start and end must be different for at " \
                          "least one motor"
                else:
                    msg = "Scan start and end must be different."
                raise ScanException(msg)

            # Set the index offset used in CAcquisition class.
            self._index_offset = i * self.macro.nb_points

            startTimestamp = time.time()

            # extra pre configuration
            if hasattr(macro, 'getHooks'):
                for hook in macro.getHooks('pre-configuration'):
                    hook()
            self.macro.checkPoint()

            # TODO: let a pseudomotor specify which motor should be used as
            # source
            MASTER = 0
            moveable = moveables[MASTER].full_name
            self.measurement_group.setMoveable(moveable)
            path = motion_paths[MASTER]
            repeats = self.macro.nb_points
            active_time = self.macro.integ_time
            active_position = path.max_vel * active_time
            if not path.positive_displacement:
                active_position *= -1
            start = path._initial_user_pos
            final = path._final_user_pos
            total_position = (final - start) / repeats
            initial_position = start
            total_time = abs(total_position) / path.max_vel
            delay_time = path.max_vel_time
            delay_position = start - path.initial_user_pos
            synch = [
                {SynchParam.Delay: {SynchDomain.Time: delay_time,
                                    SynchDomain.Position: delay_position},
                 SynchParam.Initial: {SynchDomain.Position: initial_position},
                 SynchParam.Active: {SynchDomain.Position: active_position,
                                     SynchDomain.Time: active_time},
                 SynchParam.Total: {SynchDomain.Position: total_position,
                                    SynchDomain.Time: total_time},
                 SynchParam.Repeats: repeats}]
            self.debug('SynchDescription: %s' % synch)
            measurement_group.setSynchDescription(synch)
            self.macro.checkPoint()

            # extra post configuration
            if hasattr(macro, 'getHooks'):
                for hook in macro.getHooks('post-configuration'):
                    hook()
            self.macro.checkPoint()

            endTimestamp = time.time()
            self.debug("Configuration took %s time." %
                       repr(endTimestamp - startTimestamp))
            ############
            # try to go as fast as possile to start position
            self._setFastMotions(moveables)
            # move to start position
            self.macro.debug("Moving to start position: %s" % repr(start_pos))
            motion.move(start_pos)

            if macro.isStopped():
                self.on_waypoints_end()
                return

            # prepare motor(s) to move with their maximum velocity
            for path in motion_paths:
                motor = path.moveable
                self.macro.debug("Motor: %s" % motor.getName())
                self.macro.debug('start_user: %f; ' % path._initial_user_pos +
                                 'end_user: %f; ' % path._final_user_pos +
                                 'start: %f; ' % path.initial_pos +
                                 'end: %f; ' % path.final_pos +
                                 'ds: %f' % (path.final_pos -
                                             path.initial_pos))
                attributes = OrderedDict(velocity=path.max_vel,
                                         acceleration=path.max_vel_time,
                                         deceleration=path.min_vel_time)
                # do not configure motors which are not moved in the waypoint
                # TODO: think of not attaching them to the waypoint at all
                if path.initial_user_pos == path.final_user_pos:
                    continue
                try:
                    self.configure_motor(motor, attributes)
                except ScanException as e:
                    msg = "Error when configuring scan motion (%s)" % e
                    raise ScanException(msg)

            if macro.isStopped():
                self.on_waypoints_end()
                return

            # TODO: don't fill theoretical positions but implement the position
            # capture, both hardware and software
            if i == 0:
                dt_timestamp = 0
                first_timestamp = time.time()
            else:
                dt_timestamp = time.time() - first_timestamp
            initial_data = self.data.initial_data

            motors = self.macro.motors
            starts = self.macro.starts
            finals = self.macro.finals
            nb_points = self.macro.nb_points
            theoretical_positions = generate_positions(motors, starts, finals,
                                                       nb_points)
            theoretical_timestamps = generate_timestamps(synch, dt_timestamp)
            for index, data in list(theoretical_positions.items()):
                data.update(theoretical_timestamps[index])
                initial_data[index + self._index_offset] = data
            # TODO: this changes the initial data on-the-fly - seems like not
            # the best practice
            self.data.initial_data = initial_data

            if hasattr(macro, 'getHooks'):
                pre_acq_hooks = waypoint.get('pre-acq-hooks', [])
                for hook in pre_acq_hooks:
                    hook()
            self.macro.checkPoint()

            self.macro.debug("Starting measurement group")
            self.measurement_group.setNbStarts(1)
            self.measurement_group.prepare()
            mg_id = self.measurement_group.start()
            if i == 0:
                first_timestamp = time.time()

            try:
                self.timestamp_to_start = time.time() + delta_start
                end_move = False
                # move to waypoint end position
                self.macro.debug(
                    "Moving to waypoint position: %s" % repr(final_pos))
                motion.move(final_pos)
                end_move = True
            except Exception as e:
                measurement_group.waitFinish(timeout=0, id=mg_id)
                msg = "Motion did not start properly.\n{0}".format(e)
                self.debug(msg)
                raise ScanException("move to final position failed")
            else:
                # wait extra 15 s to for the acquisition to finish
                # if it does not finish, abort the measurement group
                # (this could be due to missed hardware triggers or
                # positioning problems)
                # TODO: allow parametrizing timeout
                timeout = 15
                measurement_group.waitFinish(timeout=timeout, id=mg_id)
            finally:
                state = measurement_group.stateObj.read().rvalue
                if state == PyTango.DevState.MOVING:
                    measurement_group.Stop()
                    if end_move:
                        msg = "Measurement did not finish acquisition within "\
                              "timeout. Stopping it..."
                        self.debug(msg)
                        raise ScanException("acquisition timeout reached")

            for hook in waypoint.get('post-acq-hooks', []):
                hook()

            if macro.isStopped():
                self.on_waypoints_end()
                return
            # execute post-move hooks
            for hook in waypoint.get('post-move-hooks', []):
                hook()

            if start_positions is None:
                last_positions = positions

        self.on_waypoints_end(positions)

    def on_waypoints_end(self, restore_positions=None):
        """To be called by the waypoint thread to handle the end of waypoints
        (either because no more waypoints or because a macro abort was
        triggered)

        .. todo:: Unify this method for all the continuous scans. Hint: use
                  the motion property and return the _physical_motion member
                  instead of _motion or in both cases: CSScan and CTScan
                  coordinate the physical motors' velocit.
        """
        self.macro.debug("on_waypoints_end() entering...")
        self.set_all_waypoints_finished(True)
        if restore_positions is not None:
            self._restore_motors()  # first restore motors backup
            self._setFastMotions()  # then try to go even faster (limits)
            self.macro.info("Correcting overshoot...")
            self._physical_motion.move(restore_positions)
        self.motion_end_event.set()
        self.cleanup()
        self.macro.debug("Waiting for data events to be processed")
        self.wait_value_buffer()
        self.join_thread_pool()
        self.macro.debug("All data events are processed")

    def scan_loop(self):
        macro = self.macro
        # manager = macro.getManager()
        scream = False
        # startts = self._env['startts']

        sum_delay = 0
        sum_integ_time = 0

        if hasattr(macro, "nb_points"):
            # nb_points = float(macro.nb_points)
            scream = True
        else:
            yield 0.0

        # moveables = [m.moveable for m in self.moveables]

        # point_nb, step = -1, None
        # data = self.data

        self.go_through_waypoints()

        env = self._env
        env['acqtime'] = sum_integ_time
        env['delaytime'] = sum_delay

        if not scream:
            yield 100.0

    def cleanup(self):
        '''This method is responsible for restoring state of measurement group
        and trigger to its state before the scan.'''
        startTimestamp = time.time()

        if self.__mntGrpSubscribed:
            self.debug("Unsubscribing from value buffer events")
            try:
                self.measurement_group.unsubscribeValueBuffer(
                    self.value_buffer_changed)
                self.measurement_group.unsubscribeValueRefBuffer(
                    self.value_ref_buffer_changed)
                self.__mntGrpSubscribed = False
            except Exception:
                msg = "Exception occurred trying to remove data listeners"
                self.debug(msg)
                self.debug('Details: ', exc_info=True)
                raise ScanException('removing data listeners failed')

        if hasattr(self.macro, 'getHooks'):
            for hook in self.macro.getHooks('pre-cleanup'):
                self.debug("Executing pre-cleanup hook")
                try:
                    hook()
                except Exception:
                    msg = "Exception while trying to execute a pre-cleanup " \
                          "hook"
                    self.debug(msg)
                    self.debug('Details: ', exc_info=True)
                    raise ScanException('pre-cleanup hook failed')

        if hasattr(self.macro, 'getHooks'):
            for hook in self.macro.getHooks('post-cleanup'):
                self.debug("Executing post-cleanup hook")
                try:
                    hook()
                except Exception:
                    msg = "Exception while trying to execute a " + \
                          "post-cleanup hook"
                    self.debug(msg)
                    self.debug('Details: ', exc_info=True)
                    raise ScanException('post-cleanup hook failed')

        endTimestamp = time.time()
        self.debug("Cleanup took %s time." %
                   repr(endTimestamp - startTimestamp))


class HScan(SScan):
    """Hybrid scan"""

    def stepUp(self, n, step, lstep):
        motion, mg = self.motion, self.measurement_group
        startts = self._env['startts']

        # pre-move hooks
        for hook in step.get('pre-move-hooks', ()):
            hook()
            try:
                step['extrainfo'].update(hook.getStepExtraInfo())
            except InterruptException:
                raise
            except Exception:
                pass

        positions, integ_time = step['positions'], step['integ_time']

        try:
            m_ID = motion.startMove(positions)
            mg_ID = mg.startCount(integ_time)
        except InterruptException:
            raise
        except Exception:
            self.dump_information(n, step, motion.moveable_list)
            raise

        try:
            motion.waitMove(id=m_ID)
            mg.waitCount(id=mg_ID)
        except InterruptException:
            raise
        except Exception:
            self.dump_information(n, step, motion.moveable_list)
            raise
        self._sum_acq_time += integ_time

        curr_time = time.time()
        dt = curr_time - startts

        m_state, m_positions = motion.readState(), motion.readPosition()

        if m_state != Ready:
            self.dump_information(n, step, motion.moveable_list)
            m = "Scan aborted after problematic motion: " \
                "Motion ended with %s\n" % str(m_state)
            raise ScanException({'msg': m})

        data_line = mg.getValues()

        # Add final moveable positions
        data_line['point_nb'] = n
        data_line['timestamp'] = dt
        for i, m in enumerate(self.moveables):
            data_line[m.moveable.getName()] = m_positions[i]

        # Add extra data coming in the step['extrainfo'] dictionary
        if 'extrainfo' in step:
            data_line.update(step['extrainfo'])

        self.data.addRecord(data_line)

        # post-step hooks
        for hook in step.get('post-step-hooks', ()):
            hook()
            try:
                step['extrainfo'].update(hook.getStepExtraInfo())
            except InterruptException:
                raise
            except Exception:
                pass

    def dump_information(self, n, step, elements):
        msg = ["Report: Stopped at step #" + str(n) + " with:"]
        for element in elements:
            msg.append(element.information())
        self.macro.info("\n".join(msg))


class TScan(GScan, CAcquisition):
    """Time scan.

    Macro that employs the time scan must define the synchronization
    description in either of the following two ways:
      - synch_description attribute that follows the synchronization
      description format of the measurement group
      - integ_time, nb_points and latency_time (optional) attributes
    """
    def __init__(self, macro, generator=None,
                 moveables=[], env={}, constraints=[], extrainfodesc=[]):
        GScan.__init__(self, macro, generator=generator,
                       moveables=moveables, env=env, constraints=constraints,
                       extrainfodesc=extrainfodesc)
        CAcquisition.__init__(self)
        self._synch_description = None

    def _create_synch_description(self, active_time, repeats, latency_time=0):
        delay_time = 0
        mg_latency_time = self.measurement_group.getLatencyTime()
        if mg_latency_time > latency_time:
            self.macro.info("Choosing measurement group latency time: %f" %
                            mg_latency_time)
            latency_time = mg_latency_time
        total_time = active_time + latency_time
        synch_description = [
            {SynchParam.Delay: {SynchDomain.Time: delay_time},
             SynchParam.Active: {SynchDomain.Time: active_time},
             SynchParam.Total: {SynchDomain.Time: total_time},
             SynchParam.Repeats: repeats}]
        return synch_description

    def get_synch_description(self):
        if self._synch_description is not None:
            return self._synch_description
        if hasattr(self.macro, "synch_description"):
            synch_description = self.macro.synch_description
        else:
            try:
                active_time = getattr(self.macro, "integ_time")
                repeats = getattr(self.macro, "nb_points")
            except AttributeError:
                msg = "Macro object is missing synchronization description " \
                      "attributes"
                raise ScanSetupError(msg)
            latency_time = getattr(self.macro, "latency_time", 0)
            synch_description = \
                self._create_synch_description(active_time, repeats,
                                               latency_time)
        self._synch_description = synch_description
        return synch_description

    synch_description = property(get_synch_description)

    def scan_loop(self):
        macro = self.macro
        measurement_group = self.measurement_group
        synch_description = self.synch_description

        compatible, channels = \
            self.is_measurement_group_compatible(measurement_group)

        if not compatible:
            self.debug("Non compatible channels are: %s" % channels)
            msg = "Measurement group %s is not compatible with %s" %\
                  (measurement_group.getName(), macro.getName())
            raise ScanException(msg)

        theoretical_timestamps = \
            generate_timestamps(synch_description)
        self.data.initial_data = theoretical_timestamps
        msg = "Relative timestamp (dt) column contains theoretical values"
        self.macro.warning(msg)

        if hasattr(macro, 'getHooks'):
            for hook in macro.getHooks('pre-acq'):
                hook()

        yield 0
        measurement_group.setNbStarts(1)
        measurement_group.count_continuous(synch_description,
                                           self.value_buffer_changed,
                                           self.value_ref_buffer_changed)
        self.debug("Waiting for value buffer events to be processed")
        self.wait_value_buffer()
        self.join_thread_pool()
        self.macro.checkPoint()
        self._fill_missing_records()
        yield 100

        if hasattr(macro, 'getHooks'):
            for hook in macro.getHooks('post-acq'):
                hook()

    def _fill_missing_records(self):
        # fill record list with dummy records for the final padding
        nb_points = self.macro.nb_points
        records = len(self.data.records)
        missing_records = nb_points - records
        self.data.initRecords(missing_records)

    def _estimate(self):
        with_time = hasattr(self.macro, "getTimeEstimation")
        with_interval = hasattr(self.macro, "getIntervalEstimation")
        if with_time and with_interval:
            t = self.macro.getTimeEstimation()
            i = self.macro.getIntervalEstimation()
            return t, i

        if not hasattr(self.macro, "synch_description"):
            raise AttributeError("synch_description is mandatory "
                                 "to estimate")
        synch_description = self.macro.synch_description
        time = 0
        intervals = 0
        for group in synch_description:
            delay = group[SynchParam.Delay][SynchDomain.Time]
            time += delay
            total = group[SynchParam.Total][SynchDomain.Time]
            repeats = group[SynchParam.Repeats]
            time += total * repeats
            intervals += repeats
        return time, intervals
