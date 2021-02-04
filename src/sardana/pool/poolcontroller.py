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

"""This module is part of the Python Pool library. It defines the base classes
for"""

__all__ = ["PoolController", "PoolPseudoMotorController",
           "PoolPseudoCounterController"]

__docformat__ = 'restructuredtext'

import sys
import weakref
import io
import traceback
import functools

from taurus.core.util.containers import CaselessDict

from sardana import State, ElementType, TYPE_TIMERABLE_ELEMENTS,\
    TYPE_PSEUDO_ELEMENTS
from sardana.sardanaevent import EventType
from sardana.sardanavalue import SardanaValue
from sardana.sardanautils import is_non_str_seq, is_number

from sardana.pool.poolextension import translate_ctrl_value
from sardana.pool.poolbaseelement import PoolBaseElement
from sardana.pool.controller import Referable, Access, DataAccess,\
    Description, Type


class PoolBaseController(PoolBaseElement):
    """Base class for all controllers"""

    def __init__(self, **kwargs):
        self._ctrl = None
        self._ctrl_error = None
        self._element_ids = {}
        self._pending_element_ids = {}
        self._element_axis = {}
        self._pending_element_axis = {}
        self._element_names = CaselessDict()
        self._pending_element_names = CaselessDict()
        self._operator = None
        kwargs['elem_type'] = ElementType.Controller
        super(PoolBaseController, self).__init__(**kwargs)

    def get_ctrl_types(self):
        raise NotImplementedError

    def get_ctrl_type_names(self):
        return list(map(ElementType.whatis, self.get_ctrl_types()))

    def is_online(self):
        return True

    def get_ctrl_error(self):
        return self._ctrl_error

    def get_ctrl_error_str(self):
        """"""
        err = self._ctrl_error
        if err is None:
            return ""
        sio = io.StringIO()
        traceback.print_exception(err[0], err[1], err[2], None, sio)
        s = sio.getvalue()
        sio.close()
        if s[-1:] == "\n":
            s = s[:-1]
        return s

    def add_element(self, elem, propagate=1):
        name, axis, eid = elem.get_name(), elem.get_axis(), elem.get_id()
        if self.is_online():
            try:
                self._ctrl.AddDevice(axis)
            except:
                self.error("Unable to add %s(%s)", name, axis, exc_info=1)
                self._pending_element_ids[eid] = elem
                self._pending_element_axis[axis] = elem
                self._pending_element_names[name] = elem
            self._element_ids[eid] = elem
            self._element_axis[axis] = elem
            self._element_names[name] = elem
        else:
            # TODO: raise exception
            self._pending_element_ids[eid] = elem
            self._pending_element_axis[axis] = elem
            self._pending_element_names[name] = elem
        if propagate:
            elements = self.get_elements()
            elements = [elements[_id].name for _id in sorted(elements)]
            self.fire_event(EventType("elementlist", priority=propagate),
                            elements)

    def remove_element(self, elem, propagate=1):
        name, axis, eid = elem.get_name(), elem.get_axis(), elem.get_id()
        f = eid in self._element_ids
        if not f:
            f = eid in self._pending_element_ids
            if not f:
                raise Exception("element '%s' is not in controller")
            del self._pending_element_ids[eid]
            del self._pending_element_axis[axis]
            del self._pending_element_names[name]
        else:
            del self._element_ids[eid]
            del self._element_axis[axis]
            del self._element_names[name]
            try:
                self._ctrl.DeleteDevice(axis)
            except:
                self.error("Unable to delete %s(%s)", name, axis, exc_info=1)
        if propagate:
            elements = self.get_elements()
            elements = [elements[_id].name for _id in sorted(elements)]
            self.fire_event(EventType("elementlist", priority=propagate),
                            elements)

    def rename_element(self, old_name, new_name, propagate=1):
        """Rename element in the controller.

        :param old_name: old name of the element
        :type old_name: :obj:`str`
        :param new_name: new name of the element
        :type new_name: :obj:`str`
        :param propagate: 0 for not propagating, 1 to propagate,
               2 propagate with priority
        :type propagate: :obj:`int`
        """
        element = self._element_names.pop(old_name, None)
        if element is None:
            raise KeyError('There is no element with name %s' % old_name)
        self._element_names[new_name] = element
        if propagate:
            elements = self.get_elements()
            elements = [elements[_id].name for _id in sorted(elements)]
            self.fire_event(EventType("elementlist", priority=propagate),
                            elements)

    def remove_axis(self, axis, propagate=1):
        f = axis in self._element_axis
        if not f:
            f = axis in self._pending_element_axis
            if not f:
                raise Exception("element '%s' is not in controller")
            elem = self._pending_element_axis[axis]
        else:
            elem = self._element_axis[axis]
        self.remove_element(elem, propagate=propagate)

    def get_elements(self):
        return self._element_ids

    def get_element_ids(self):
        return self._element_ids

    def get_element_axis(self):
        return self._element_axis

    def get_element(self, **kwargs):
        k = kwargs.get('axis')
        if k is None:
            k = kwargs.get('name')
            if k is None:
                k = kwargs.get('id')
                if k is None:
                    raise Exception("Must give either name, id or axis")
                d, pd = self._element_ids, self._pending_element_ids
            else:
                d, pd = self._element_names, self._pending_element_names
        else:
            d, pd = self._element_axis, self._pending_element_axis

        elem = d.get(k)
        if elem is None:
            elem = pd.get(k)
        return elem

    def read_axis_states(self, axes=None):
        """Reads the state for the given axes. If axes is None, reads the
        state of all active axes.

        :param axes: the list of axis to get the state. Default is None meaning
                       all active axis in this controller
        :type axes: seq<int> or None
        :return: a map containing the controller state information for each axis
        :rtype: dict<PoolElement, state info>
        """
        raise NotImplementedError

    def read_axis_values(self, axes=None):
        """Reads the value for the given axes. If axes is None, reads the
        value of all active axes.

        :param axes: the list of axis to get the value. Default is None meaning
                       all active axis in this controller
        :type axes: seq<int> or None
        :return: a map containing the controller value information for each axis
        :rtype: dict<PoolElement, value>
        """
        raise NotImplementedError

    def get_status(self, cache=True, propagate=1):
        """Returns the status for this object. If cache is True (default) it
        returns the current status stored in cache (it will force an update if
        cache is empty). If propagate > 0 and if the status changed since last
        read, it will propagate the status event to all listeners.

        :param cache:
            tells if return value from local cache or update from HW read
            [default: True]
        :type cache: bool
        :param propagate:
            if > 0 propagates the event in case it changed since last HW read.
            Values bigger that mean the event if sent should be a priority event
            [default: 1]
        :type propagate: int
        :return: the current object status
        :rtype: str"""
        if not cache or self._status is None:
            state_info = None
            self._set_state_info(state_info, propagate=propagate)
        return self._status

    _STD_STATUS = '{name} is {state}'

    def calculate_state_info(self, status_info=None):
        """Transforms the given state information. This specific base
        implementation transforms the given state,status tuple into a
        state, new_status tuple where new_status is "*self.name* is *state*.

        :param status_info:
            given status information [default: None, meaning use current state status.
        :type status_info: tuple<State, str>
        :return: a transformed state information
        :rtype: tuple<State, str>"""
        if status_info is None:
            status_info = self._state, self._status
        state, _ = status_info
        state_str = State[state]
        new_status = self._STD_STATUS.format(name=self.name, state=state_str)
        return status_info[0], new_status


def check_ctrl(fn):
    @functools.wraps(fn)
    def wrapper(pool_ctrl, *args, **kwargs):
        if not pool_ctrl.is_online():
            raise Exception("Cannot execute '%s' because '%s' is offline" %
                            (fn.__name__, pool_ctrl.name))
        return fn(pool_ctrl, *args, **kwargs)
    return wrapper


def ctrl_access(fn):
    @functools.wraps(fn)
    def wrapper(pool_ctrl, *args, **kwargs):
        with pool_ctrl:
            return fn(pool_ctrl, *args, **kwargs)
    return wrapper


class PoolController(PoolBaseController):
    """Controller class mediator for sardana controller plugins"""

    def __init__(self, **kwargs):
        self._lib_info = kwargs.pop('lib_info')
        self._ctrl_info = kwargs.pop('class_info')
        self._lib_name = kwargs.pop('library')
        self._class_name = kwargs.pop('klass')
        self._properties = kwargs.pop('properties')
        super(PoolController, self).__init__(**kwargs)
        self.re_init()

    def serialize(self, *args, **kwargs):
        kwargs = PoolBaseController.serialize(self, *args, **kwargs)
        ctrl_info = self._ctrl_info
        if ctrl_info is None:
            kwargs['module'] = self._lib_name
            kwargs['klass'] = self._class_name
            kwargs['language'] = 'Python'
            kwargs['file_name'] = None
            kwargs['types'] = None
            kwargs['main_type'] = None
            kwargs['parent'] = self._class_name
        else:
            types = self.get_ctrl_type_names()
            kwargs['module'] = ctrl_info.module_name
            kwargs['klass'] = ctrl_info.name
            kwargs['language'] = 'Python'
            kwargs['file_name'] = ctrl_info.file_name
            kwargs['types'] = types
            kwargs['parent'] = ctrl_info.name
            if len(types):
                kwargs['main_type'] = types[0]
            else:
                kwargs['main_type'] = None
        return kwargs

    def _create_ctrl_args(self):
        name = self.name
        klass = self._ctrl_info.klass
        props = dict(self._properties)
        args, kwargs = [], dict(pool_controller=weakref.ref(self))
        return name, klass, props, args, kwargs

    def _create_controller(self):
        name, klass, props, args, kwargs = self._create_ctrl_args()
        api = self._ctrl_info.api_version
        if api == 0:
            ctrl = klass(name, props)
            ctrl._args = args
            ctrl._kwargs = kwargs
        elif api == 1:
            ctrl = klass(name, props, *args, **kwargs)
        return ctrl

    def _init(self):
        if self._ctrl_info is None:
            if self._lib_info is not None:
                self._ctrl_error = self._lib_info.get_error()
            return
        try:
            self._ctrl = self._create_controller()
        except:
            self._ctrl = None
            self._ctrl_error = sys.exc_info()

    def re_init(self):
        self.set_state(State.Init, propagate=2)
        status = "{0} is Initializing (temporarily unavailable)".format(
            self.name)
        self.set_status(status, propagate=2)
        manager = self.pool.ctrl_manager
        old_e_ids = self._element_ids
        old_p_e_ids = self._pending_element_ids

        elem_axis = dict(self._element_axis)
        for axis in elem_axis:
            self.remove_axis(axis, propagate=0)

        if self._lib_info is None:
            mod_name = self.get_library_name()
        else:
            mod_name = self._lib_info.name

        if self._ctrl_info is None:
            class_name = self.get_class_name()
        else:
            class_name = self._ctrl_info.name

        self._ctrl_error = None
        self._ctrl_info = None
        self._lib_info = manager.getControllerLib(mod_name)
        if self._lib_info is not None:
            self._ctrl_info = self._lib_info.get_controller(class_name)
        self._init()

        for elem in list(elem_axis.values()):
            self.add_element(elem, propagate=0)

        state, status = State.Fault, ""
        if self.is_online():
            state = State.On
        else:
            status = "\n" + self.get_ctrl_error_str()

        status = "{0} is {1}".format(self.name, State[state]) + status
        self.set_status(status, propagate=2)
        self.set_state(state, propagate=2)

    def get_ctrl_types(self):
        return self._ctrl_info.types

    def is_timerable(self):
        for t in self._ctrl_info.types:
            if t in TYPE_TIMERABLE_ELEMENTS:
                return True
        return False

    def is_referable(self):
        return isinstance(self.ctrl, Referable)

    def is_pseudo(self):
        for t in self._ctrl_info.types:
            if t in TYPE_PSEUDO_ELEMENTS:
                return True
        return False

    def is_online(self):
        return self._ctrl_error is None and self._ctrl is not None

    def get_ctrl(self):
        return self._ctrl

    def set_ctrl(self, ctrl):
        self._ctrl = ctrl

    ctrl = property(fget=get_ctrl, fset=set_ctrl,
                    doc="actual controller object")

    def get_ctrl_info(self):
        return self._ctrl_info

    ctrl_info = property(fget=get_ctrl_info,
                         doc="controller information object")

    def set_operator(self, operator):
        """Defines the current operator object for this controller.
           For example, in acquisition, it should be a :class:`PoolMeasurementGroup`
           object.

           :param operator: the new operator object
           :type operator: object"""
        self._operator = operator

    def get_operator(self):
        return self._operator

    operator = property(fget=get_operator, fset=set_operator,
                        doc="current controller operator")

    # START API WHICH ACCESSES CONTROLLER API --------------------------------

    @check_ctrl
    def set_log_level(self, level):
        self.ctrl._log.log_obj.setLevel(level)

    @check_ctrl
    def get_log_level(self):
        return self.ctrl._log.log_obj.level

    def get_library_name(self):
        return self._lib_name

    def get_class_name(self):
        return self._class_name

    @check_ctrl
    def get_axis_attributes(self, axis):
        axis_attrs = self.ctrl.GetAxisAttributes(axis)
        if self.is_referable():
            referable_axis_attrs = {
                "ValueRef": {Type: str,
                             Access: DataAccess.ReadOnly,
                             Description: "Value reference", },
                # TODO: in case of Tango ValueBuffer type is overridden
                # by DevEncoded
                "ValueRefBuffer": {Type: str,
                                   Access: DataAccess.ReadOnly,
                                   Description: "Value reference buffer", },
                "ValueRefPattern": {Type: str,
                                    Access: DataAccess.ReadWrite,
                                    Description: "Value reference template"},
                "ValueRefEnabled": {Type: bool,
                                    Access: DataAccess.ReadWrite,
                                    Description: "Value reference enabled"}
                }
            axis_attrs.update(referable_axis_attrs)
        return axis_attrs

    @check_ctrl
    def get_ctrl_attr(self, name):
        ctrl_info = self.ctrl_info
        attr_info = ctrl_info.ctrl_attributes[name]
        if hasattr(self.ctrl, attr_info.fget):
            return getattr(self.ctrl, attr_info.fget)()
        else:
            return self.ctrl.GetCtrlPar(name)

    @check_ctrl
    def set_ctrl_attr(self, name, value):
        ctrl_info = self.ctrl_info
        attr_info = ctrl_info.ctrl_attributes[name]
        if hasattr(self.ctrl, attr_info.fset):
            return getattr(self.ctrl, attr_info.fset)(value)
        else:
            return self.ctrl.SetCtrlPar(name, value)

    @check_ctrl
    def get_axis_attr(self, axis, name):
        ctrl_info = self.ctrl_info
        axis_attr_info = ctrl_info.axis_attributes[name]
        if hasattr(self.ctrl, axis_attr_info.fget):
            ret = getattr(self.ctrl, axis_attr_info.fget)(axis)
        else:
            ret = self.ctrl.GetAxisExtraPar(axis, name)
        return ret

    @check_ctrl
    def set_axis_attr(self, axis, name, value):
        ctrl_info = self.ctrl_info
        axis_attr_info = ctrl_info.axis_attributes[name]
        try:
            return getattr(self.ctrl, axis_attr_info.fset)(axis, value)
        except AttributeError:
            return self.ctrl.SetAxisExtraPar(axis, name, value)

    @check_ctrl
    def set_ctrl_par(self, name, value):
        return self.ctrl.SetCtrlPar(name, value)

    @check_ctrl
    def get_ctrl_par(self, name):
        return self.ctrl.GetCtrlPar(name)

    @check_ctrl
    def set_axis_par(self, axis, name, value):
        return self.ctrl.SetAxisPar(axis, name, value)

    @check_ctrl
    def get_axis_par(self, axis, name):
        return self.ctrl.GetAxisPar(axis, name)

    # END API WHICH ACCESSES CONTROLLER API ----------------------------------

    # START API WHICH ACCESSES CRITICAL CONTROLLER API (like StateOne) -------

    def __build_exc_info(self, ctrl_states, axes, exc_info):
        status = "".join(traceback.format_exception(*exc_info))
        state_info = State.Fault, status
        for axis in axes:
            element = self.get_element(axis=axis)
            ctrl_states[element] = state_info

    @staticmethod
    def _format_exception(exc_info):
        fmt_exc = traceback.format_exception_only(*exc_info[:2])
        fmt_exc = "".join(fmt_exc)
        if fmt_exc.endswith("\n"):
            fmt_exc = fmt_exc[:-1]
        return fmt_exc

    def raw_read_axis_states(self, axes=None, ctrl_states=None):
        """**Unsafe method**. Reads the state for the given axes. If axes
        is None, reads the state of all active axes.

        :param axes: the list of axis to get the state. Default is None meaning
                       all active axis in this controller
        :type axes: seq<int> or None
        :return:
            a tuple of two elements: a map containing the controller state
            information for each axis and a boolean telling if an error occured
        :rtype: dict<PoolElement, state info>, bool"""
        if axes is None:
            axes = list(self._element_axis.keys())
        if ctrl_states is None:
            ctrl_states = {}

        ctrl = self.ctrl

        try:
            ctrl.PreStateAll()
            for axis in axes:
                ctrl.PreStateOne(axis)
            ctrl.StateAll()
        except:
            exc_info = sys.exc_info()
            status = self._format_exception(exc_info)
            state_info = (State.Fault, status), exc_info
            for axis in axes:
                element = self.get_element(axis=axis)
                ctrl_states[element] = state_info
            return ctrl_states, True

        error = False
        for axis in axes:
            element = self.get_element(axis=axis)
            try:
                state_info = ctrl.StateOne(axis)
                if state_info is None:
                    raise Exception("%s.StateOne(%s(%d)) returns 'None'"
                                    % (self.name, element.name, axis))
                if state_info in State:
                    state_info = (state_info, None)
                state_info = state_info, None
            except:
                exc_info = sys.exc_info()
                status = self._format_exception(exc_info)
                state_info = (State.Fault, status), exc_info
                error = True
            ctrl_states[element] = state_info
        return ctrl_states, error

    @check_ctrl
    def read_axis_states(self, axes=None):
        """Reads the state for the given axes. If axes is None, reads the
        state of all active axes.

        :param axes: the list of axis to get the state. Default is None
                       meaning all active axis in this controller
        :type axes: seq<int> or None
        :return: a map containing the controller state information for each axis
        :rtype: dict<PoolElement, state info>"""
        return self.raw_read_axis_states(axes=axes)

    def _read_axis_value(self, element):

        def is_chunk(type_, obj):
            if not is_non_str_seq(obj):
                return False
            if type_ == ElementType.CTExpChannel:
                return True
            elif type_ == ElementType.OneDExpChannel:
                # empty list is also considered as chunk
                if len(obj) == 0 or not is_number(obj[0]):
                    return True
            elif type_ == ElementType.TwoDExpChannel:
                # empty list is also considered as chunk
                if len(obj) == 0 or not is_number(obj[0][0]):
                    return True
            return False

        try:
            axis = element.get_axis()
            type_ = element.get_type()
            ctrl_value = self.ctrl.ReadOne(axis)
            if ctrl_value is None:
                msg = '%s.ReadOne(%s[%d]) return error: Expected value(s), ' \
                      'got None instead' % (self.name, element.name, axis)
                raise ValueError(msg)

            if is_chunk(type_, ctrl_value):
                value = [translate_ctrl_value(v) for v in ctrl_value]
            else:
                value = translate_ctrl_value(ctrl_value)
        except:
            value = SardanaValue(exc_info=sys.exc_info())
        return value

    def raw_read_axis_values(self, axes=None, ctrl_values=None):
        """**Unsafe method**. Reads the value for the given axes. If axes
        is None, reads the value of all active axes.

        :param axes: the list of axis to get the value. Default is None
                       meaning all active axis in this controller
        :type axes: seq<int> or None
        :return: a map containing the controller value information for each axis
        :rtype: dict<PoolElement, SardanaValue>"""
        if axes is None:
            axes = list(self._element_axis.keys())
        if ctrl_values is None:
            ctrl_values = {}

        ctrl = self.ctrl

        try:
            ctrl.PreReadAll()
            for axis in axes:
                ctrl.PreReadOne(axis)
            ctrl.ReadAll()
        except:
            exc_info = sys.exc_info()
            for axis in axes:
                element = self.get_element(axis=axis)
                ctrl_values[element] = SardanaValue(exc_info=exc_info)
            return ctrl_values

        for axis in axes:
            element = self.get_element(axis=axis)
            ctrl_values[element] = self._read_axis_value(element)

        return ctrl_values

    @check_ctrl
    def read_axis_values(self, axes=None):
        """Reads the value for the given axes. If axes is None, reads the
        value of all active axes.

        :param axes: the list of axis to get the value. Default is None meaning
                       all active axis in this controller
        :type axes: seq<int> or None
        :return: a map containing the controller value information for each axis
        :rtype: dict<PoolElement, SardanaValue>

        """
        return self.raw_read_axis_values(axes=axes)

    def _read_axis_value_refs(self, element):

        def is_chunk(obj):
            if is_non_str_seq(obj):
                return True
            return False

        try:
            axis = element.get_axis()
            ctrl_value = self.ctrl.RefOne(axis)
            if ctrl_value is None:
                msg = ('%s.RefOne(%s[%d]) return error: Expected value '
                       'ref(s), got None instead' % (self.name,
                                                     element.name, axis))
                raise ValueError(msg)

            if is_chunk(ctrl_value):
                value = [translate_ctrl_value(v) for v in ctrl_value]
            else:
                value = translate_ctrl_value(ctrl_value)
        except Exception:
            value = SardanaValue(exc_info=sys.exc_info())
        return value

    def raw_read_axis_value_refs(self, axes=None, ctrl_values=None):
        """**Unsafe method**. Reads the value refs for the given axes. If axes
        is None, reads the value of all active axes.

        .. note::
            The raw_read_axis_value_refs method has been included in Sardana
            on a provisional basis. Backwards incompatible changes (up to
            and including removal of the class) may occur if deemed
            necessary by the core developers.

        .. todo::
            This method should be available only on the controllers which
            are *referable*.

        :param axes: the list of axis to get the value. Default is None
            meaning all active axis in this controller
        :type axes: seq<int> or None
        :return: a map containing the controller value information for each
            axis
        :rtype: dict<PoolElement, SardanaValue>
        """
        if axes is None:
            axes = list(self._element_axis.keys())
        if ctrl_values is None:
            ctrl_values = {}

        for axis in axes:
            element = self.get_element(axis=axis)
            ctrl_values[element] = self._read_axis_value_refs(element)

        return ctrl_values

    def stop_axes(self, axes):
        """Stops the given axes.

        :param axes: the list of axes to stopped.
        :type axes: list<axes>
        :return: list of axes that could not be stopped
        :rtype: list<int>
        """
        ctrl = self.ctrl

        # PreStopAll
        try:
            ctrl.PreStopAll()
        except Exception:
            msg = "%s.PreStopAll has failed" % self.name
            self.warning(msg, exc_info=True)
            return axes

        error_axes = []
        for axis in axes:
            # PreStopOne
            msg = "%s.PreStopOne(%d) has failed" % (self.name, axis)
            try:
                ret = ctrl.PreStopOne(axis)
            except Exception:
                error_axes.append(axis)
                self.warning(msg, exc_info=True)
                continue
            if not ret:
                error_axes.append(axis)
                self.warning(msg)
                continue
            # StopOne
            try:
                ctrl.StopOne(axis)
            except Exception:
                msg = "%s.StopOne(%d) has failed" % (self.name, axis)
                error_axes.append(axis)
                self.warning(msg, exc_info=True)
        # StopAll
        try:
            ctrl.StopAll()
        except Exception:
            msg = "%s.StopAll(%d) has failed" % self.name
            self.warning(msg, exc_info=True)
            return axes

        return error_axes

    @check_ctrl
    def stop_element(self, element):
        """Stops the given element.

        :param element: element to stop
        :type element: ~sardana.pool.poolelement.PoolElement
        :raises Exception: not able to stop element
        """

        axes = [element.axis]
        error_axes = self.stop_axes(axes)
        if len(error_axes):
            raise Exception("Stop of element %s failed" % element.name)

    @check_ctrl
    def stop_elements(self, elements=None):
        """Stops the given elements. If elements is None, stops all
        active elements.

        :param elements: the list of elements to stop. Default is None
                         meaning all active elements in this controller
        :type elements: seq<PoolElement> or None
        :return: list of elements that could not be stopped
        :rtype: list<PoolElements>
        """

        if elements is None:
            axes = list(self.get_element_axis().keys())
        else:
            axes = [e.axis for e in elements]
        error_axes = self.stop_axes(axes)
        error_elements = [self.get_element(axis=axis) for axis in error_axes]
        return error_elements

    stop = stop_elements

    @check_ctrl
    def abort_axes(self, axes):
        """Aborts the given axes.

        :param axes: the list of axes to aborted.
        :type axes: list<axes>
        :return: list of axes that could not be aborted
        :rtype: list<int>
        """

        ctrl = self.ctrl

        # PreAbortAll
        try:
            ctrl.PreAbortAll()
        except Exception:
            msg = "%s.PreAbortAll has failed" % self.name
            self.warning(msg, exc_info=True)
            return axes

        error_axes = []
        for axis in axes:
            # PreStopOne
            msg = "%s.PreAbortOne(%d) has failed" % (self.name, axis)
            try:
                ret = ctrl.PreAbortOne(axis)
            except Exception:
                error_axes.append(axis)
                self.warning(msg, exc_info=True)
                continue
            if not ret:
                error_axes.append(axis)
                self.warning(msg)
            # AbortOne
            try:
                ctrl.AbortOne(axis)
            except Exception:
                msg = "%s.AbortOne(%d) has failed" % (self.name, axis)
                error_axes.append(axis)
                self.warning(msg, exc_info=True)
        # AbortAll
        try:
            ctrl.AbortAll()
        except Exception:
            msg = "%s.AbortAll(%d) has failed" % self.name
            self.warning(msg, exc_info=True)
            return axes

        return error_axes

    @check_ctrl
    def abort_element(self, element):
        """Aborts the given elements.

        :param element: element to abort
        :type element: ~sardana.pool.poolelement.PoolElement
        :raises Exception: not able to abort element
        """

        axes = [element.axis]
        error_axes = self.abort_axes(axes)
        if len(error_axes):
            raise Exception("Abort of element %s failed" % element.name)

    @check_ctrl
    def abort_elements(self, elements=None):
        """Abort the given elements. If elements is None, stops all
        active elements.

        :param elements: the list of elements to stop. Default is None
                         meaning all active elements in this controller
        :type elements: seq<PoolElement> or None
        :return: list of elements that could not be aborted
        :rtype: list<PoolElements>
        """

        if elements is None:
            axes = list(self.get_element_axis().keys())
        else:
            axes = [e.axis for e in elements]
        error_axes = self.abort_axes(axes)
        error_elements = [self.get_element(axis=axis) for axis in error_axes]
        return error_elements

    abort = abort_elements

    @check_ctrl
    def emergency_break(self, elements=None):
        """Stops the given elements. If elements is None,
        stops all active elements.
        If stop could not be executed, an abort is attempted.

        :param elements: the list of elements to stop. Default is None
                         meaning all active elements in this controller
        :type axes: seq<PoolElement> or None
        :return: elements that could neither be stopped nor aborted
        :rtype: list<PoolElement>
        """
        if elements is None:
            elements = self.ctrl.get_elements()

        error_elements = self.stop_elements(elements)
        if not error_elements:
            return []
        element_names = [elem.name for elem in error_elements]
        msg = ("Emergency break could not stop element(s): %s. "
               + "Trying to abort...") % element_names
        self.warning(msg)
        # trying to abort elements that could not be stopped
        error_elements = self.abort_elements(error_elements)
        if error_elements:
            element_names = [elem.name for elem in error_elements]
            msg = ("Emergency break could not abort element(s): %s"
                   % element_names)
            self.warning(msg)
        else:
            element_names = [elem.name for elem in elements]
            msg = ("Emergency break stopped/aborted element(s): %s"
                   % element_names)
            self.warning(msg)
        return error_elements

    @check_ctrl
    def send_to_controller(self, stream):
        return self.ctrl.SendToCtrl(stream)

    # END API WHICH ACCESSES CRITICAL CONTROLLER API (like StateOne) ---------

    # START SPECIFIC TO MOTOR CONTROLLER -------------------------------------

    def raw_move(self, axis_pos):
        ctrl = self.ctrl
        ctrl.PreStartAll()
        for axis, dial_position in list(axis_pos.items()):
            ret = ctrl.PreStartOne(axis, dial_position)
            if not ret:
                raise Exception("%s.PreStartOne(%d, %f) returns False"
                                % (self.name, axis, dial_position))

        for axis, dial_position in list(axis_pos.items()):
            ctrl.StartOne(axis, dial_position)

        ctrl.StartAll()

    @check_ctrl
    def move(self, axis_pos):
        return self.raw_move(axis_pos)

    def has_backlash(self):
        return "Backlash" in self._ctrl.ctrl_features

    def wants_rounding(self):
        return "Rounding" in self._ctrl.ctrl_features

    @check_ctrl
    def define_position(self, axis, position):
        return self.ctrl.DefinePosition(axis, position)

    # END SPECIFIC TO MOTOR CONTROLLER ---------------------------------------

    # START SPECIFIC TO IOR CONTROLLER ---------------------------------------

    def write_one(self, axis, value):
        self.ctrl.WriteOne(axis, value)

    # END SPECIFIC TO IOR CONTROLLER -----------------------------------------

    # START SPECIFIC TO TIMERABLE CONTROLLER ---------------------------------

    def get_default_timer(self):
        """Get default timer as announced by the controller (plug-in).

        Only for *Timerable* controllers, e.g.
        :class:`~sardana.pool.controller.CounterTimerController`,
        :class:`~sardana.pool.controller.OneDController`,
        :class:`~sardana.pool.controller.TwoDController`.

        :return: axis of the default timer or :obj:`None` if not defined
        :rtype: :obj:`int` or :obj:`None`
        """
        if not self.is_timerable():
            raise TypeError("non-timerable controller")
        try:
            return self.ctrl.default_timer
        except AttributeError:
            return None

    # END SPECIFIC TO IOR CONTROLLER -----------------------------------------


class PoolPseudoMotorController(PoolController):

    def __init__(self, **kwargs):
        self._motor_ids = kwargs.pop('role_ids')
        super(PoolPseudoMotorController, self).__init__(**kwargs)

    def serialize(self, *args, **kwargs):
        kwargs = PoolController.serialize(self, *args, **kwargs)
        kwargs['type'] = 'Controller'
        return kwargs

    def _create_ctrl_args(self):
        pars = PoolController._create_ctrl_args(self)
        kwargs = pars[4]
        kwargs['motor_ids'] = tuple(self._motor_ids)
        return pars

    def _read_axis_value(self, element):
        try:
            axis = element.get_axis()
            ctrl_value = self.ctrl.ReadOne(axis)
            if ctrl_value is None:
                msg = '%s.ReadOne(%s[%d]) return error: Expected value, ' \
                      'got None instead' % (self.name, element.name, axis)
                raise ValueError(msg)
            value = translate_ctrl_value(ctrl_value)
        except:
            value = SardanaValue(exc_info=sys.exc_info())
        return value

    @check_ctrl
    def calc_all_pseudo(self, physical_pos, curr_pseudo_pos):
        ctrl = self.ctrl
        try:
            ctrl_value = ctrl.CalcAllPseudo(physical_pos, curr_pseudo_pos)
            if ctrl_value is None:
                msg = '%s.CalcAllPseudo() return error: Expected value, ' \
                      'got None instead' % (self.name,)
                raise ValueError(msg)
            value = translate_ctrl_value(ctrl_value)
        except:
            value = SardanaValue(exc_info=sys.exc_info())
        return value

    @check_ctrl
    def calc_all_physical(self, pseudo_pos, curr_physical_pos):
        ctrl = self.ctrl
        try:
            ctrl_value = ctrl.CalcAllPhysical(pseudo_pos, curr_physical_pos)
            if ctrl_value is None:
                msg = '%s.CalcAllPhysical() return error: Expected value, ' \
                      'got None instead' % (self.name,)
                raise ValueError(msg)
            value = translate_ctrl_value(ctrl_value)
        except:
            value = SardanaValue(exc_info=sys.exc_info())
        return value

    @check_ctrl
    def calc_pseudo(self, axis, physical_pos, curr_pseudo_pos):
        ctrl = self.ctrl
        try:
            ctrl_value = ctrl.CalcPseudo(axis, physical_pos, curr_pseudo_pos)
            if ctrl_value is None:
                msg = '%s.CalcPseudo() return error: Expected value, ' \
                      'got None instead' % (self.name,)
                raise ValueError(msg)
            value = translate_ctrl_value(ctrl_value)
        except:
            value = SardanaValue(exc_info=sys.exc_info())
        return value

    @check_ctrl
    def calc_physical(self, axis, pseudo_pos, curr_physical_pos):
        ctrl = self.ctrl
        try:
            ctrl_value = ctrl.CalcPhysical(axis, pseudo_pos, curr_physical_pos)
            if ctrl_value is None:
                msg = '%s.CalcPhysical() return error: Expected value, ' \
                      'got None instead' % (self.name,)
                raise ValueError(msg)
            value = translate_ctrl_value(ctrl_value)
        except:
            value = SardanaValue(exc_info=sys.exc_info())
        return value


class PoolPseudoCounterController(PoolController):

    def __init__(self, **kwargs):
        self._counter_ids = kwargs.pop('role_ids')
        super(PoolPseudoCounterController, self).__init__(**kwargs)

    def serialize(self, *args, **kwargs):
        kwargs = PoolController.serialize(self, *args, **kwargs)
        kwargs['type'] = 'Controller'
        return kwargs

    def _create_ctrl_args(self):
        pars = PoolController._create_ctrl_args(self)
        kwargs = pars[4]
        kwargs['counter_ids'] = tuple(self._counter_ids)
        return pars

    @check_ctrl
    def calc(self, axis, values):
        ctrl = self.ctrl
        try:
            ctrl_value = ctrl.Calc(axis, values)
            if ctrl_value is None:
                msg = '%s.Calc() return error: Expected value, ' \
                      'got None instead' % (self.name,)
                raise ValueError(msg)
            value = translate_ctrl_value(ctrl_value)
        except:
            value = SardanaValue(exc_info=sys.exc_info())
        return value

    def calc_all(self, values):
        ctrl = self.ctrl
        try:
            ctrl_value = ctrl.CalcAll(values)
            if ctrl_value is None:
                msg = '%s.CalcAll() return error: Expected value, ' \
                      'got None instead' % (self.name,)
                raise ValueError(msg)
            value = translate_ctrl_value(ctrl_value)
        except:
            value = SardanaValue(exc_info=sys.exc_info())
        return value
