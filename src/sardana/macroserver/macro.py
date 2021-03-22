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


import collections
import numbers

__all__ = ["OverloadPrint", "PauseEvent", "Hookable", "ExecMacroHook",
           "MacroFinder", "Macro", "macro", "iMacro", "imacro",
           "MacroFunc", "Type", "Table", "List", "ViewOption",
           "LibraryError", "Optional", "StopException", "AbortException",
           "InterruptException"]

__docformat__ = 'restructuredtext'

import sys
import time
import copy
import types
import ctypes
import weakref
import operator
import io
import threading
import traceback

from taurus.core.util.log import Logger
from taurus.core.util.prop import propertx
from taurus.console.table import Table
from taurus.console.list import List

from sardana.sardanadefs import State
from sardana.util.wrap import wraps
from sardana.util.thread import _asyncexc

from sardana.macroserver.msparameter import Type, ParamType, Optional
from sardana.macroserver.msexception import StopException, AbortException, \
    ReleaseException, MacroWrongParameterType, UnknownEnv, UnknownMacro, \
    LibraryError, InterruptException
from sardana.macroserver.msoptions import ViewOption

from sardana.taurus.core.tango.sardana.pool import PoolElement


class OverloadPrint(object):
    """ """

    def __init__(self, m):
        self._macro = m
        self._accum = ""

    def __enter__(self):
        self.stdout = sys.stdout
        sys.stdout = self

    def __exit__(self, exc_type, exc_value, traceback):
        self.flush()
        sys.stdout = self.stdout

    def write(self, s):
        """

        Parameters
        ----------
        s :
            

        Returns
        -------

        """
        self._accum += s
        # while there is no new line, just accumulate the buffer
        try:
            if s[-1] == '\n' or s.index('\n') >= 0:
                self.flush()
        except ValueError:
            pass

    def flush(self):
        """ """
        b = self._accum
        if b is None or len(b) == 0:
            return
        # take the '\n' because the output is a list of strings, each to be
        # interpreted as a separate line in the client
        if b[-1] == '\n':
            b = b[:-1]
        self._macro.output(b)
        self._accum = ""


class PauseEvent(Logger):
    """ """

    def __init__(self, macro_obj, abort_timeout=0.2):
        self._name = self.__class__.__name__
        self._pause_cb = None
        self._resume_cb = None
        self._macro_obj_wr = weakref.ref(macro_obj)
        self._macro_name = macro_obj._getName()
        self._wait_for_abort_exception = False
        self._wait_for_abort_timeout = abort_timeout
        Logger.__init__(self, "Macro_%s %s" % (self._macro_name, self._name))
        # we create an event object that is automatically set
        self._event = threading.Event()
        self._event.set()

    @property
    def macro_obj(self):
        """ """
        return self._macro_obj_wr()

    def pause(self, cb=None):
        """

        Parameters
        ----------
        cb :
             (Default value = None)

        Returns
        -------

        """
        self.debug("[START] Pause")
        self._pause_cb = cb
        self._event.clear()
        self.debug("[ END ] Pause")

    def resume(self, cb=None):
        """

        Parameters
        ----------
        cb :
             (Default value = None)

        Returns
        -------

        """
        if self.isPaused():
            self.debug("[START] Resume")
            self._resume_cb = cb
            self._event.set()
            self.debug("[ END ] Resume")

    def resumeForAbort(self):
        """ """
        if self.isPaused():
            self.debug("[RESUME] (Abort)")
            self._wait_for_abort_exception = True
            self._event.set()

    def wait(self, timeout=None):
        """

        Parameters
        ----------
        timeout :
             (Default value = None)

        Returns
        -------

        """
        pauseit = not self._event.isSet()
        if pauseit and self._pause_cb is not None:
            self._pause_cb(self.macro_obj)
        self._event.wait(timeout)
        # if an event is set because an abort has been issued during a paused
        # macro wait for the ashyncronous AbortException to arrive at this
        # thread
        if self._wait_for_abort_exception:
            self._wait_for_abort_exception = False
            time.sleep(self._wait_for_abort_timeout)
            self.debug('Abort exception did not occured in pause for %ss.'
                       'Performing a Forced Abort.' % self._wait_for_abort_timeout)
            raise AbortException("Forced")
        if pauseit and self._resume_cb is not None:
            self._resume_cb(self.macro_obj)

    def isPaused(self):
        """ """
        return not self._event.isSet()


class Hookable(Logger):
    """ """

    # avoid creating an __init__

    def _getHooks(self):
        """ """
        try:
            return self._hooks
        except:
            self._hooks = []
        return self._hooks

    def _getHookHintsDict(self):
        """ """
        try:
            return self._hookHintsDict
        except:
            self._hookHintsDict = {'_ALL_': [], '_NOHINTS_': []}
        return self._hookHintsDict

    def getAllowedHookHints(self):
        """ """
        return self.__class__.hints.get('allowsHooks')

    def getHints(self):
        """ """
        return list(self._getHookHintsDict().keys())

    def getHooks(self, hint=None):
        """This will return a list of hooks that have the given hint. Two reserved
        hints are always valid:
        
        - "_ALL_": which contains all the hooks
        - "_NOHINTS_": which contains the hooks that don't provide any hint

        Parameters
        ----------
        hint :
            str) a hint. If None is passed, it returns a list of
            (hook,hints) tuples (Default value = None)

        Returns
        -------
        type
            list) an ordered list of hooks that have the given hint

        """
        if hint is None:
            return self._getHooks()
        else:
            return self._getHookHintsDict().get(hint, [])

    def appendHook(self, hook_info):
        """Append a hook according to the hook information

        Parameters
        ----------
        hook_info :
            sequence of two elements, the first one is the hook
            and its optional parameters/arguments, the second one is the list
            of hints e.g. hook places

        Returns
        -------

        """
        self._getHooks().append(hook_info)
        hook = hook_info[0]
        hints = hook_info[1]
        allowed_hookhints = self.getAllowedHookHints()
        if len(hints) == 0:
            self._getHookHintsDict()['_ALL_'].append(hook)
            self._hookHintsDict['_NOHINTS_'].append(hook)
            return
        for hint in hints:
            if hint in allowed_hookhints:
                self._getHookHintsDict()['_ALL_'].append(hook)
                break
        for hint in hints:
            if hint in allowed_hookhints:
                try:
                    self._hookHintsDict[hint].append(hook)
                except KeyError:
                    self._hookHintsDict[hint] = [hook]

    @property
    def hooks(self):
        """Hooks (callables) attached to the macro object together with the
        hook places (places where they will be called).
        
        :getter: Return all hooks attached to the macro object (including
            general hooks).
        :setter: Set hooks to the object. **This may override eventual
            general hooks.**
            Use :meth:`~sardana.macroserver.macro.Hookable.appendHook`
            if the general hooks want to be kept. For backwards compatibility
            accepts hook in the :obj:`list`\<callable\> format.

        Parameters
        ----------

        Returns
        -------

        """
        return self._getHooks()

    @hooks.setter
    def hooks(self, hooks):
        """Sets hooks. Internally two variables instance members are created:
        
        - _hooks (list<callable,list<str>>) (will be a tuple regardless of
          what was passed)
        - _hookHintsDict (dict<str,list>) a dict of key=hint and value=list
          of hooks with that hint. _hookHintsDict also stores two special
          keys: "_ALL_": which contains all the hooks "_NOHINTS_": which
          contains the hooks that don't provide hints

        Parameters
        ----------
        hooks :
            

        Returns
        -------

        """
        if not isinstance(hooks, list):
            self.error(
                'the hooks must be passed as a list<callable,list<str>>')
            return

        if len(self.hooks) > 0:
            msg = ("This macro defines its own hooks. Previously defined "
                   "hooks, including the general ones, would be only called "
                   "if these own hooks were added using the appendHook "
                   "method or appended to the self.hooks.")
            self.warning(msg)
        # store self._hooks, making sure it is of type:
        # list<callable,list<str>>
        self._hooks = []
        for h in hooks:
            if isinstance(h, (tuple, list)) and len(h) == 2:
                self._hooks.append(h)
            else:  # we assume that hooks is a list<callable>
                self._hooks.append((h, []))
                msg = ("Deprecation warning: hooks should be set with a"
                       " list of hints. See Hookable API docs")
                self.info(msg)

        # delete _hookHintsDict to force its recreation on the next access
        if hasattr(self, '_hookHintsDict'):
            del self._hookHintsDict
        if len(self._hooks) == 0:
            return
        # create _hookHintsDict
        self._getHookHintsDict()['_ALL_'] = list(zip(*self._hooks))[0]
        nohints = self._hookHintsDict['_NOHINTS_']
        for hook, hints in self._hooks:
            if len(hints) == 0:
                nohints.append(hook)
            else:
                for hint in hints:
                    try:
                        self._hookHintsDict[hint].append(hook)
                    except KeyError:
                        self._hookHintsDict[hint] = [hook]


class ExecMacroHook(object):
    """A speciallized callable hook for executing a sub macro inside another
    macro as a hook.
    
    In order to attach macro with parameters pass all of them in form of
    a list (repeat parameters are allowed) e.g.
    - ExecMacroHook(self, "ct", 0.1)
    - ExecMacroHook(self, ["ct", 0.1])
    - ExecMacroHook(self, "mv", "mot01", 0, "mot02", 0)
    - ExecMacroHook(self, "mv", [["mot01", 0], ["mot02", 0]])
    - ExecMacroHook(self, ["mv", [["mot01", 0], ["mot02", 0]]])
    The API basically follows the :meth:`Macro.execMacro`.

    Parameters
    ----------

    Returns
    -------

    """

    def __init__(self, parent_macro, *pars, **kwargs):
        self._macro_obj_wr = weakref.ref(parent_macro)
        self._pars = pars
        self._opts = kwargs

    @property
    def macro_obj(self):
        """ """
        return self._macro_obj_wr()

    def __call__(self):
        self.macro_obj.execMacro(*self._pars, **self._opts)


class MacroFinder:
    """ """

    def __init__(self, macro_obj):
        self._macro_obj_wr = weakref.ref(macro_obj)

    @property
    def macro_obj(self):
        """ """
        return self._macro_obj_wr()

    def __getattr__(self, name):

        def f(*args, **kwargs):
            """

            Parameters
            ----------
            *args :
                
            **kwargs :
                

            Returns
            -------

            """
            p_m = self.macro_obj
            p_m.syncLog()
            opts = {'parent_macro': p_m,
                    'executor': p_m.executor}
            kwargs.update(opts)
            eargs = [name]
            eargs.extend(args)
            return p_m.execMacro(*eargs, **kwargs)

        setattr(self, name, f)

        return f


def mAPI(fn):
    """Wraps the given Macro method as being protected by the stop procedure.
    To be used by the :class:`Macro` as a decorator for all methods.

    Parameters
    ----------
    fn :
        

    Returns
    -------
    type
        wrapped macro method

    """
    @wraps(fn)
    def new_fn(*args, **kwargs):
        """

        Parameters
        ----------
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        self = args[0]
        if not self.isProcessingStop():
            is_macro_th = self._macro_thread == threading.current_thread()
            if self._shouldRaiseStopException():
                if is_macro_th:
                    self.setProcessingStop(True)
                self.executor._waitStopDone()
                raise StopException("stopped before calling %s" % fn.__name__)
        ret = fn(*args, **kwargs)
        if not self.isProcessingStop():
            if self._shouldRaiseStopException():
                if is_macro_th:
                    self.setProcessingStop(True)
                self.executor._waitStopDone()
                raise StopException("stopped after calling %s" % fn.__name__)
        return ret
    return new_fn


class macro(object):
    """Class designed to decorate a python function to transform it into a
    macro. Examples::
    
        @macro()
        def my_macro1(self):
            self.output("Executing %s", self.getName())
    
        @macro([ ["moveable", Type.Moveable, None, "motor to watch"] ])
        def where_moveable(self, moveable):
            self.output("Moveable %s is at %s", moveable.getName(), moveable.getPosition())

    Parameters
    ----------

    Returns
    -------

    """

    param_def = []
    result_def = []
    env = ()
    hints = {}
    interactive = False

    def __init__(self, param_def=None, result_def=None, env=None, hints=None,
                 interactive=None):
        if param_def is not None:
            self.param_def = param_def
        if result_def is not None:
            self.result_def = result_def
        if env is not None:
            self.env = env
        if hints is not None:
            self.hints = hints
        if interactive is not None:
            self.interactive = interactive

    def __call__(self, fn):
        fn.macro_data = {}
        fn.param_def = self.param_def
        fn.result_def = self.result_def
        fn.hints = self.hints
        fn.env = self.env
        fn.interactive = self.interactive
        return fn


from functools import partial
imacro = partial(macro, interactive=True)


class Macro(Logger):
    """The Macro base class. All macros should inherit directly or indirectly
    from this class.

    Parameters
    ----------

    Returns
    -------

    """

    #: internal variable
    Init = State.Init

    #: internal variable
    Running = State.Running

    #: internal variable
    Pause = State.Standby

    #: internal variable
    Stop = State.Standby

    #: internal variable
    Fault = State.Fault

    #: internal variable
    Finished = State.On

    #: internal variable
    Ready = State.On

    #: internal variable
    Abort = State.On

    #: internal variable
    Exception = State.Alarm

    #: Constant used to specify all elements in a parameter
    All = ParamType.All

    #: internal variable
    BlockStart = '<BLOCK>'

    #: internal variable
    BlockFinish = '</BLOCK>'

    #: This property holds the macro parameter description.
    #: It consists of a sequence of parameter information objects.
    #: A parameter information object is either:
    #:
    #:    #. a simple parameter object
    #:    #. a parameter repetition object
    #:
    #: A simple parameter object is a sequence of:
    #:
    #:    #. a string representing the parameter name
    #:    #. a member of :obj:`Macro.Type` representing the parameter data type
    #:    #. a default value for the parameter or None if there is no default value
    #:    #. a string with the parameter description
    #:
    #: Example::
    #:
    #:     param_def = ( ('value', Type.Float, None, 'a float parameter' ) )
    #:
    #: A parameter repetition object is a sequence of:
    #:
    #:    #. a string representing the parameter repetition name
    #:    #. a sequence of parameter information objects
    #:    #. a dictionary representing the parameter repetition semantics or None
    #:       to use the default parameter repetition semantics. Dictionary keys are:
    #:
    #:           * *min* - integer representing minimum number of repetitions or None
    #:             for no minimum.
    #:           * *max* - integer representing maximum number of repetitions or None
    #:             for no maximum.
    #:
    #:       Default parameter repetition semantics is ``{ 'min': 1, 'max' : None }``
    #:       (in other words, "at least one repetition" semantics)
    #:
    #: Example::
    #:
    #:     param_def = (
    #:         ( 'motor_list', ( ( 'motor', Type.Motor, None, 'motor name') ), None, 'List of motors')
    #:     )
    param_def = []

    #: This property holds the macro result description.
    #: It a single parameter information object.
    #:
    #: .. seealso:: :obj:`~sardana.macroserver.macro.Macro.param_def`
    result_def = []

    #: Hints to give a client to perform special tasks.
    #: Example: scan macros give hints on the types of hooks they support. A
    #: :term:`GUI` can use this information to allow a scan to have sub-macros
    #: executed as hooks.
    hints = {}

    #: a set of mandatory environment variable names without which your macro
    #: cannot run
    env = ()

    #: decide if the macro should be able to receive input from the user
    #: [default: False]. A macro which asks input but has this flag set to False
    #: will print a warning message each time it is executed
    interactive = False

    def __init__(self, *args, **kwargs):
        """Constructor"""
        self._name = kwargs.get('as', self.__class__.__name__)
        self._in_pars = args
        self._out_pars = None
        self._aborted = False
        self._stopped = False
        self._processingStop = False
        self._parent_macro = kwargs.get('parent_macro')
        self._executor = kwargs.get('executor')
        self._macro_line = kwargs.get('macro_line')
        self._interactive_mode = kwargs.get('interactive', True)
        self._macro_thread = None
        self._id = kwargs.get('id')
        self._desc = "Macro '%s'" % self._macro_line
        self._macro_status = {'id': self._id,
                              'name': self._name,
                              'macro_line': self._macro_line,
                              'range': (0.0, 100.0),
                              'state': 'start',
                              'step': 0.0}
        self._pause_event = PauseEvent(self)
        log_parent = self.parent_macro or self.door
        Logger.__init__(self, "Macro[%s]" % self._name, log_parent)
        self._reserveObjs(args)

    # @name Official Macro API
    #  This list contains the set of methods that are part of the official macro
    #  API. This means that they can be safely used inside any macro.
    #@{

    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # Methods to be implemented by the actual macros
    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    def run(self, *args):
        """**Macro API**. Runs the macro. **Overwrite MANDATORY!** Default implementation
        raises RuntimeError.

        Parameters
        ----------
        *args :
            

        Returns
        -------

        """
        raise RuntimeError(
            "Macro %s does not implement run method" % self.getName())

    def prepare(self, *args, **kwargs):
        """**Macro API**. Prepare phase. Overwrite as necessary.
        Default implementation does nothing

        Parameters
        ----------
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        pass

    def on_abort(self):
        """**Macro API**. Hook executed when an abort occurs.
        Overwrite as necessary. Default implementation does nothing

        Parameters
        ----------

        Returns
        -------

        """
        pass

    def on_pause(self):
        """**Macro API**. Hook executed when a pause occurs.
        Overwrite as necessary. Default implementation does nothing

        Parameters
        ----------

        Returns
        -------

        """
        pass

    def on_stop(self):
        """**Macro API**. Hook executed when a stop occurs.
        Overwrite as necessary. Default implementation calls
        :meth:`~Macro.on_abort`

        Parameters
        ----------

        Returns
        -------

        """
        return self.on_abort()

    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # API
    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    @mAPI
    def checkPoint(self):
        """**Macro API**.
        Empty method that just performs a checkpoint. This can be used
        to check for the stop. Usually you won't need to call this method

        Parameters
        ----------

        Returns
        -------

        """
        pass

    @mAPI
    def pausePoint(self, timeout=None):
        """**Macro API**.
        Will establish a pause point where called. If an external source as
        invoked a pause then, when this this method is called, it will be block
        until the external source calls resume.
        You may want to call this method if your macro takes a considerable time
        to execute and you may whish to pause it at some time. Example::
        
            for i in range(10000):
                time.sleep(0.1)
                self.output("At step %d/10000", i)
                self.pausePoint()

        Parameters
        ----------
        timeout : obj:`float
            timeout in seconds [default: None, meaning wait forever]

        Returns
        -------

        """
        return self._pausePoint(timeout=timeout)

    @property
    def macros(self):
        """**Macro API**.
        An object that contains all macro classes as members. With
        the returning object you can invoke other macros. Example::
        
            m = self.macros.ascan('th', '0', '90', '10', '2')
            scan_data = m.data

        Parameters
        ----------

        Returns
        -------

        """
        self.checkPoint()
        if not hasattr(self, '_macros'):
            self._macros = MacroFinder(self)
        return self._macros

    @mAPI
    def getMacroStatus(self):
        """**Macro API**.
        Returns the current macro status. Macro status is a :obj:`dict` where
        keys are the strings:
        
            * *id* - macro ID (internal usage only)
            * *range* - the full progress range of a macro (usually a
              :obj:`tuple` of two numbers (0, 100))
            * *state* - the current macro state, a string which can have values
              *start*, *step*, *stop* and *abort*
            * *step* - the current step in macro. Should be a value inside the
              allowed macro range

        Parameters
        ----------

        Returns
        -------
        obj:`dict`
            the macro status

        """
        return self._macro_status

    @mAPI
    def getName(self):
        """**Macro API**.
        Returns this macro name

        Parameters
        ----------

        Returns
        -------
        obj:`str`
            the macro name

        """
        return self._name

    @mAPI
    def getID(self):
        """**Macro API**.
        Returns this macro id

        Parameters
        ----------

        Returns
        -------
        obj:`str`
            the macro id

        """
        return self._id

    @mAPI
    def getParentMacro(self):
        """**Macro API**.
        Returns the parent macro reference.

        Parameters
        ----------

        Returns
        -------
        class:`~sardana.macroserver.macro.Macro`
            the parent macro reference or None if there is no parent macro

        """
        return self._parent_macro

    @mAPI
    def getDescription(self):
        """**Macro API**.
        Returns a string description of the macro.

        Parameters
        ----------

        Returns
        -------
        obj:`str`
            the string description of the macro

        """
        return self._desc

    @mAPI
    def getParameters(self):
        """**Macro API**.
        Returns a the macro parameters. It returns a list containning the
        parameters with which the macro was executed

        Parameters
        ----------

        Returns
        -------
        obj:`list`
            the macro parameters

        """
        return self._in_pars

    @mAPI
    def getExecutor(self):
        """**Macro API**.
        Returns the reference to the object that invoked this macro. Usually
        is a MacroExecutor object.

        Parameters
        ----------

        Returns
        -------
        class:`~sardana.macroserver.macromanager.MacroExecutor`
            the reference to the object that invoked this macro

        """
        return self._executor

    @mAPI
    def getDoorObj(self):
        """**Macro API**.
        Returns the reference to the Door that invoked this macro.
        
        :return: the reference to the Door that invoked this macro.
        :rype: :class:`~sardana.macroserver.door.Door`

        Parameters
        ----------

        Returns
        -------

        """
        return self.executor.getDoor()

    @mAPI
    def getManager(self):
        """**Macro API**.
        Returns the manager for this macro (usually a MacroServer)

        Parameters
        ----------

        Returns
        -------
        class:`~sardana.macroserver.macroserver.MacroServer`
            the MacroServer

        """
        return self.door.manager

    manager = property(getManager)

    @mAPI
    def getMacroServer(self):
        """**Macro API**.
        Returns the MacroServer for this macro

        Parameters
        ----------

        Returns
        -------
        class:`~sardana.macroserver.macroserver.MacroServer`
            the MacroServer

        """
        return self.door.macro_server

    macro_server = property(getMacroServer)

    @mAPI
    def getDoorName(self):
        """**Macro API**.
        Returns the string with the name of the Door that invoked this macro.

        Parameters
        ----------

        Returns
        -------
        obj:`str`
            the string with the name of the Door that invoked this macro.

        """
        return self.door.name

    @mAPI
    def getCommand(self):
        """**Macro API**.
        Returns the string used to execute the macro.
        Ex.: 'ascan M1 0 1000 100 0.8'

        Parameters
        ----------

        Returns
        -------
        obj:`str`
            the macro command.

        """
        return '%s %s' % (self.getName(), ' '.join([str(p) for p in self._in_pars]))

    @mAPI
    def getDateString(self, time_format='%a %b %d %H:%M:%S %Y'):
        """**Macro API**.
        Helper method. Returns the current date in a string.

        Parameters
        ----------
        time_format : obj:`str`
            the format in which the date should be
            returned (optional, default value is
            '%a %b %d %H:%M:%S %Y'

        Returns
        -------
        obj:`str`
            the current date

        """
        return time.strftime(time_format)

    @mAPI
    def outputDate(self, time_format='%a %b %d %H:%M:%S %Y'):
        """**Macro API**.
        Helper method. Outputs the current date into the output buffer

        Parameters
        ----------
        time_format : obj:`str
            str) the format in which the date should be
            returned (optional, default value is
            '%a %b %d %H:%M:%S %Y'

        Returns
        -------

        """
        self.output(self.getDateString(time_format=time_format))

    @mAPI
    def sendRecordData(self, data, codec=None):
        """**Macro API**.
        Sends the given data to the RecordData attribute of the Door

        Parameters
        ----------
        data : object
            data to be sent (must be compatible with the codec)
        codec : str or None
            codec to encode data (in Tango server None defaults
            to "utf8_json")

        Returns
        -------

        """
        self._sendRecordData(data, codec)

    def _sendRecordData(self, data, codec=None):
        """

        Parameters
        ----------
        data :
            
        codec :
             (Default value = None)

        Returns
        -------

        """
        self.executor.sendRecordData(data, codec=codec)

    @mAPI
    def plot(self, *args, **kwargs):
        """**Macro API**.
        Sends the plot command to the client using the 'RecordData' DevEncoded
        attribute. The data is encoded using the pickle -> BZ2 codec.

        Parameters
        ----------
        args :
            the plotting args
        kwargs :
            the plotting keyword arg
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        self.pyplot.plot(*args, **kwargs)
#        data = dict(args=args, kwargs=kwargs)
#        self.sendRecordData(data, codec='bz2_pickle_plot')

    @property
    @mAPI
    def pylab(self):
        """ """
        try:
            pylab = self._pylab
        except AttributeError:
            self._pylab = pylab = self.door.pylab
        return pylab

    @property
    @mAPI
    def pyplot(self):
        """ """
        try:
            pyplot = self._pyplot
        except AttributeError:
            self._pyplot = pyplot = self.door.pyplot
        return pyplot

    @mAPI
    def getData(self):
        """**Macro API**.
        Returns the data produced by the macro.

        Parameters
        ----------

        Returns
        -------
        object
            the data produced by the macro

        """
        if not hasattr(self, "_data"):
            raise Exception(
                "Macro '%s' does not produce any data" % self.getName())
        return self._data

    @mAPI
    def setData(self, data):
        """**Macro API**. Sets the data for this macro

        Parameters
        ----------
        object :
            data: new data to be associated with this macr
        data :
            

        Returns
        -------

        """
        self._data = data

    data = property(getData, setData, doc="macro data")

    @mAPI
    def print(self, *args, **kwargs):
        """**Macro API**.
        Prints a message. Accepted *args* and
        *kwargs* are the same as :func:`print`. Example::
        
            self.print("this is a print for macro", self.getName())
        
        .. note::
            you will need python >= 3.0. If you have python 2.x then you must
            include at the top of your file the statement::
        
                from __future__ import print_function

        Parameters
        ----------
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        fd = kwargs.get('file', sys.stdout)
        if fd in (sys.stdout, sys.stderr):
            out = io.StringIO()
            kwargs['file'] = out
            end = kwargs.get('end', '\n')
            if end == '\n':
                kwargs['end'] = ''
            ret = print(*args, **kwargs)
            self.output(out.getvalue())
        else:
            ret = print(*args, **kwargs)
        return ret

    @mAPI
    def input(self, msg, *args, **kwargs):
        """**Macro API**.
        If args is present, it is written to standard output without a trailing
        newline. The function then reads a line from input, converts it to a
        string (stripping a trailing newline), and returns that.
        
        Depending on which type of application you are running, some of the
        keywords may have no effect (ex.: spock ignores decimals when a number
        is asked).
        
        Recognized kwargs:
        
            - data_type : [default: Type.String] specific input type. Can also
              specify a sequence of strings with possible values (use
              allow_multiple=True to say multiple values can be selected)
            - key : [default: no default] variable/label to assign to this input
            - unit: [default: no default] units (useful for GUIs)
            - timeout : [default: None, meaning wait forever for input]
            - default_value : [default: None, meaning no default value]
              When given, it must be compatible with data_type
            - allow_multiple : [default: False] in case data_type is a
              sequence of values, allow multiple selection
            - minimum : [default: None] When given, must be compatible with data_type (useful for GUIs)
            - maximum : [default: None] When given, must be compatible with data_type (useful for GUIs)
            - step : [default: None] When given, must be compatible with data_type (useful for GUIs)
            - decimals : [default: None] When given, must be compatible with data_type (useful for GUIs)
        
        Examples::
        
            device_name = self.input("Which device name (%s)?", "tab separated")
        
            point_nb = self.input("How many points?", data_type=Type.Integer)
        
            calc_mode = self.input("Which algorithm?", data_type=["Average", "Integral", "Sum"],
                                   default_value="Average", allow_multiple=False)

        Parameters
        ----------
        msg :
            
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        if not self.interactive:
            self.warning("Non interactive macro '%s' is asking for input "
                         "(please set this macro interactive to True)",
                         self.getName())
        if self._interactive_mode:
            kwargs['data_type'] = kwargs.get('data_type', Type.String)
            kwargs['allow_multiple'] = kwargs.get('allow_multiple', False)
            kwargs['macro_id'] = self.getID()
            kwargs['macro_name'] = self.getName()
            kwargs['macro'] = self
            return self.getDoorObj().input(msg, *args, **kwargs)
        else:
            if 'default_value' not in kwargs:
                if 'key' not in kwargs:
                    self.warning("%s running in non attended mode was asked "
                                 "for input without default value or key. "
                                 "Returning None")
                    return None
                else:
                    return self.getEnv(kwargs['key'])
            return kwargs['default_value']

    @mAPI
    def output(self, msg, *args, **kwargs):
        """**Macro API**.
        Record a log message in this object's output. Accepted *args* and
        *kwargs* are the same as :meth:`logging.Logger.log`.
        Example::
        
            self.output("this is a print for macro %s", self.getName())

        Parameters
        ----------
        msg : obj:`str`
            the message to be recorded
        args :
            list of arguments
        kwargs :
            list of keyword argument
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        return Logger.output(self, msg, *args, **kwargs)

    @mAPI
    def log(self, level, msg, *args, **kwargs):
        """**Macro API**.
        Record a log message in this object's logger. Accepted *args* and
        *kwargs* are the same as :meth:`logging.Logger.log`.
        Example::
        
            self.debug(logging.INFO, "this is a info log message for macro %s", self.getName())

        Parameters
        ----------
        level : obj:`int`
            the record level
        msg : obj:`str`
            the message to be recorded
        args :
            list of arguments
        kwargs :
            list of keyword argument
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        return Logger.log(self, level, msg, *args, **kwargs)

    @mAPI
    def debug(self, msg, *args, **kwargs):
        """**Macro API**.
        Record a debug message in this object's logger. Accepted *args* and
        *kwargs* are the same as :meth:`logging.Logger.debug`.
        Example::
        
            self.debug("this is a log message for macro %s", self.getName())

        Parameters
        ----------
        msg : obj:`str`
            the message to be recorded
        args :
            list of arguments
        kw :
            list of keyword argument
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        return Logger.debug(self, msg, *args, **kwargs)

    @mAPI
    def info(self, msg, *args, **kwargs):
        """**Macro API**.
        Record an info message in this object's logger. Accepted *args* and
        *kwargs* are the same as :meth:`logging.Logger.info`.
        Example::
        
            self.info("this is a log message for macro %s", self.getName())

        Parameters
        ----------
        msg : obj:`str`
            the message to be recorded
        args :
            list of arguments
        kwargs :
            list of keyword argument
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        return Logger.info(self, msg, *args, **kwargs)

    @mAPI
    def warning(self, msg, *args, **kwargs):
        """**Macro API**.
        Record a warning message in this object's logger. Accepted *args* and
        *kwargs* are the same as :meth:`logging.Logger.warning`.
        Example::
        
            self.warning("this is a log message for macro %s", self.getName())

        Parameters
        ----------
        msg : obj:`str`
            the message to be recorded
        args :
            list of arguments
        kwargs :
            list of keyword argument
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        return Logger.warning(self, msg, *args, **kwargs)

    @mAPI
    def error(self, msg, *args, **kwargs):
        """**Macro API**.
        Record an error message in this object's logger. Accepted *args* and
        *kwargs* are the same as :meth:`logging.Logger.error`.
        Example::
        
            self.error("this is a log message for macro %s", self.getName())

        Parameters
        ----------
        msg : obj:`str`
            the message to be recorded
        args :
            list of arguments
        kwargs :
            list of keyword arguments
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        return Logger.error(self, msg, *args, **kwargs)

    @mAPI
    def critical(self, msg, *args, **kwargs):
        """**Macro API**.
        Record a critical message in this object's logger. Accepted *args* and
        *kwargs* are the same as :meth:`logging.Logger.critical`.
        Example::
        
            self.critical("this is a log message for macro %s", self.getName())

        Parameters
        ----------
        msg : obj:`str`
            the message to be recorded
        args :
            list of arguments
        kwargs :
            list of keyword argument
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        return Logger.critical(self, msg, *args, **kwargs)

    @mAPI
    def trace(self, msg, *args, **kwargs):
        """**Macro API**. Record a trace message in this object's logger.

        Parameters
        ----------
        msg :
            str) the message to be recorded
        args :
            list of arguments
        kw :
            list of keyword argument
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        return Logger.trace(self, msg, *args, **kwargs)

    @mAPI
    def traceback(self, *args, **kwargs):
        """**Macro API**.
        Logs the traceback with level TRACE on the macro logger.

        Parameters
        ----------
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        return Logger.traceback(self, *args, **kwargs)

    @mAPI
    def stack(self, *args, **kwargs):
        """**Macro API**.
        Logs the stack with level TRACE on the macro logger.

        Parameters
        ----------
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        return Logger.stack(self, *args, **kwargs)

    @mAPI
    def report(self, msg, *args, **kwargs):
        """**Macro API**.
        Record a log message in the sardana report (if enabled) with default
        level **INFO**. The msg is the message format string, and the args are
        the arguments which are merged into msg using the string formatting
        operator. (Note that this means that you can use keywords in the
        format string, together with a single dictionary argument.)
        
        *kwargs* are the same as :meth:`logging.Logger.debug` plus an optional
        level kwargs which has default value **INFO**
        
        Example::
        
            self.report("this is an official report of macro %s", self.getName())

        Parameters
        ----------
        msg : obj:`str`
            the message to be recorded
        args :
            list of arguments
        kwargs :
            list of keyword argument
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        return self.getDoorObj().report(msg, *args, **kwargs)

    @mAPI
    def flushOutput(self):
        """**Macro API**.
        Flushes the output buffer.

        Parameters
        ----------

        Returns
        -------

        """
        return Logger.flushOutput(self)

    @mAPI
    def getMacroThread(self):
        """**Macro API**.
        Returns the python thread where this macro is running

        Parameters
        ----------

        Returns
        -------
        threading.Thread
            the python thread where this macro is running

        """
        return self._macro_thread

    @mAPI
    def getMacroThreadID(self):
        """**Macro API**.
        Returns the python thread id where this macro is running

        Parameters
        ----------

        Returns
        -------
        obj:`int`
            the python thread id where this macro is running

        """
        return self.getMacroThread().ident

    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # Hook helper API
    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    @mAPI
    def createExecMacroHook(self, par_str_sequence, parent_macro=None):
        """**Macro API**.
        Creates a hook that executes the macro given as a sequence of strings
        where the first string is macro name and the following strings the
        macro parameters

        Parameters
        ----------
        par_str_sequence :
            the macro parameters
        parent_macro :
            the parent macro object. If None is given (default) then the
            parent macro is this macro

        Returns
        -------
        type
            a ExecMacroHook object (which is a callable object)

        """
        return ExecMacroHook(parent_macro or self, par_str_sequence)

    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # Handle child macro execution
    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    @mAPI
    def createMacro(self, *pars):
        """**Macro API**. Create a new macro and prepare it for execution
        Several different parameter formats are supported::
        
            # several parameters:
            self.createMacro('ascan', 'th', '0', '100', '10', '1.0')
            self.createMacro('mv', [[motor.getName(), '0']])
            self.createMacro('mv', motor.getName(), '0') # backwards compatibility - see note
            self.createMacro('ascan', 'th', 0, 100, 10, 1.0)
            self.createMacro('mv', [[motor.getName(), 0]])
            self.createMacro('mv', motor.getName(), 0) # backwards compatibility - see note
            th = self.getObj('th')
            self.createMacro('ascan', th, 0, 100, 10, 1.0)
            self.createMacro('mv', [[th, 0]])
            self.createMacro('mv', th, 0) # backwards compatibility - see note
        
            # a sequence of parameters:
            self.createMacro(['ascan', 'th', '0', '100', '10', '1.0'])
            self.createMacro(['mv', [[motor.getName(), '0']]])
            self.createMacro(['mv', motor.getName(), '0']) # backwards compatibility - see note
            self.createMacro(('ascan', 'th', 0, 100, 10, 1.0))
            self.createMacro(['mv', [[motor.getName(), 0]]])
            self.createMacro(['mv', motor.getName(), 0]) # backwards compatibility - see note
            th = self.getObj('th')
            self.createMacro(['ascan', th, 0, 100, 10, 1.0])
            self.createMacro(['mv', [[th, 0]]])
            self.createMacro(['mv', th, 0]) # backwards compatibility - see note
        
        
            # a space separated string of parameters (this is not compatible
            # with multiple or nested repeat parameters, furthermore the repeat
            # parameter must be the last one):
            self.createMacro('ascan th 0 100 10 1.0')
            self.createMacro('mv %s 0' % motor.getName())
        
        .. note:: From Sardana 2.0 the repeat parameter values must be passed
            as lists of items. An item of a repeat parameter containing more
            than one member is a list. In case when a macro defines only one
            repeat parameter and it is the last parameter, for the backwards
            compatibility reasons, the plain list of items' members is allowed.

        Parameters
        ----------
        pars :
            the command parameters as explained above
        *pars :
            

        Returns
        -------
        obj:`tuple`\<:class:`~sardana.macroserver.macro.Macro`\, seq<obj>>
            a sequence of two elements: the macro object and the result of
            preparing the macro

        """
        return self.prepareMacro(*pars)

    @mAPI
    def prepareMacroObj(self, macro_name_or_klass, *args, **kwargs):
        """**Macro API**. Prepare a new macro for execution

        Parameters
        ----------
        macro_name_or_klass :
            name: name of the macro to be prepared or
            the macro class itself
        pars :
            list of parameter objects
        init_opts :
            keyword parameters for the macro constructor
        prepare_opts :
            keyword parameters for the macro prepare
        *args :
            
        **kwargs :
            

        Returns
        -------
        type
            a sequence of two elements: the macro object and the result of
            preparing the macro

        """
        # sync our log before calling the child macro prepare in order to avoid
        # mixed outputs between this macro and the child macro
        self.syncLog()
        init_opts = {'parent_macro': self}
        return self.executor.prepareMacroObj(macro_name_or_klass, args,
                                             init_opts, kwargs)

    @mAPI
    def prepareMacro(self, *args, **kwargs):
        """**Macro API**. Prepare a new macro for execution
        Several different parameter formats are supported::
        
            # several parameters:
            self.prepareMacro('ascan', 'th', '0', '100', '10', '1.0')
            self.prepareMacro('mv', [[motor.getName(), '0']])
            self.prepareMacro('mv', motor.getName(), '0') # backwards compatibility - see note
            self.prepareMacro('ascan', 'th', 0, 100, 10, 1.0)
            self.prepareMacro('mv', [[motor.getName(), 0]])
            self.prepareMacro('mv', motor.getName(), 0) # backwards compatibility - see note
            th = self.getObj('th')
            self.prepareMacro('ascan', th, 0, 100, 10, 1.0)
            self.prepareMacro('mv', [[th, 0]])
            self.prepareMacro('mv', th, 0) # backwards compatibility - see note
        
            # a sequence of parameters:
            self.prepareMacro(['ascan', 'th', '0', '100', '10', '1.0'])
            self.prepareMacro(['mv', [[motor.getName(), '0']]])
            self.prepareMacro(['mv', motor.getName(), '0']) # backwards compatibility - see note
            self.prepareMacro(('ascan', 'th', 0, 100, 10, 1.0))
            self.prepareMacro(['mv', [[motor.getName(), 0]]])
            self.prepareMacro(['mv', motor.getName(), 0]) # backwards compatibility - see note
            th = self.getObj('th')
            self.prepareMacro(['ascan', th, 0, 100, 10, 1.0])
            self.prepareMacro(['mv', [[th, 0]]])
            self.prepareMacro(['mv', th, 0]) # backwards compatibility - see note
        
            # a space separated string of parameters (this is not compatible
            # with multiple or nested repeat parameters, furthermore the repeat
            # parameter must be the last one):
            self.prepareMacro('ascan th 0 100 10 1.0')
            self.prepareMacro('mv %s 0' % motor.getName())
        
        .. note:: From Sardana 2.0 the repeat parameter values must be passed
            as lists of items. An item of a repeat parameter containing more
            than one member is a list. In case when a macro defines only one
            repeat parameter and it is the last parameter, for the backwards
            compatibility reasons, the plain list of items' members is allowed.

        Parameters
        ----------
        args :
            the command parameters as explained above
        kwargs :
            keyword optional parameters for prepare
        *args :
            
        **kwargs :
            

        Returns
        -------
        type
            a sequence of two elements: the macro object and the result of
            preparing the macro

        """
        # sync our log before calling the child macro prepare in order to avoid
        # mixed outputs between this macro and the child macro
        self.syncLog()
        init_opts = {'parent_macro': self}
        return self.executor.prepareMacro(args, init_opts, kwargs)

    @mAPI
    def runMacro(self, macro_obj):
        """**Macro API**. Runs the macro. This the lower level version of
        :meth:`~sardana.macroserver.macro.Macro.execMacro`. The method only
        returns after the macro is completed or an exception is thrown.
        It should be used instead of execMacro when some operation needs to
        be done between the macro preparation and the macro execution.
        Example::
        
            macro = self.prepareMacro("mymacro", "myparam")
            self.do_my_stuff_with_macro(macro)
            self.runMacro(macro)

        Parameters
        ----------
        macro_obj :
            macro object

        Returns
        -------
        type
            macro result

        """
        # sync our log before calling the child macro prepare in order to avoid
        # mixed outputs between this macro and the child macro
        self.syncLog()
        return self.executor.runMacro(macro_obj)

    @mAPI
    def execMacroObj(self, name, *args, **kwargs):
        """**Macro API**. Execute a macro in this macro. The method only returns
        after the macro is completed or an exception is thrown. This is a
        higher level version of runMacro method. It is the same as::
        
            macro = self.prepareMacroObjs(name, *args, **kwargs)
            self.runMacro(macro)
            return macro

        Parameters
        ----------
        name : obj:`str`
            name of the macro to be prepared
        args :
            list of parameter objects
        kwargs :
            list of keyword parameters
        *args :
            
        **kwargs :
            

        Returns
        -------
        type
            a macro object

        """
        self.debug("Executing macro: %s" % name)
        macro_obj, prepare_result = self.prepareMacroObj(name, *args, **kwargs)
        self.runMacro(macro_obj)
        return macro_obj

    @mAPI
    def execMacro(self, *args, **kwargs):
        """**Macro API**. Execute a macro in this macro. The method only
        returns after the macro is completed or an exception is thrown. Several
        different parameter formats are supported::
        
            # several parameters:
            self.execMacro('ascan', 'th', '0', '100', '10', '1.0')
            self.execMacro('mv', [[motor.getName(), '0']])
            self.execMacro('mv', motor.getName(), '0') # backwards compatibility - see note
            self.execMacro('ascan', 'th', 0, 100, 10, 1.0)
            self.execMacro('mv', [[motor.getName(), 0]])
            self.execMacro('mv', motor.getName(), 0) # backwards compatibility - see note
            th = self.getObj('th')
            self.execMacro('ascan', th, 0, 100, 10, 1.0)
            self.execMacro('mv', [th, 0]])
            self.execMacro('mv', th, 0) # backwards compatibility - see note
        
            # a sequence of parameters:
            self.execMacro(['ascan', 'th', '0', '100', '10', '1.0')
            self.execMacro(['mv', [[motor.getName(), '0']]])
            self.execMacro(['mv', motor.getName(), '0']) # backwards compatibility - see note
            self.execMacro(('ascan', 'th', 0, 100, 10, 1.0))
            self.execMacro(['mv', [[motor.getName(), 0]]])
            self.execMacro(['mv', motor.getName(), 0]) # backwards compatibility - see note
            th = self.getObj('th')
            self.execMacro(['ascan', th, 0, 100, 10, 1.0])
            self.execMacro(['mv', [[th, 0]]])
            self.execMacro(['mv', th, 0]) # backwards compatibility - see note
        
            # a space separated string of parameters (this is not compatible
            # with multiple or nested repeat parameters, furthermore the repeat
            # parameter must be the last one):
            self.execMacro('ascan th 0 100 10 1.0')
            self.execMacro('mv %s 0' % motor.getName())
        
        .. note:: From Sardana 2.0 the repeat parameter values must be passed
            as lists of items. An item of a repeat parameter containing more
            than one member is a list. In case when a macro defines only one
            repeat parameter and it is the last parameter, for the backwards
            compatibility reasons, the plain list of items' members is allowed.

        Parameters
        ----------
        pars :
            the command parameters as explained above
        *args :
            
        **kwargs :
            

        Returns
        -------
        type
            a macro object

        """
        # obtaining macro name
        macro_name = None
        arg0 = args[0]
        if len(args) == 1:
            if isinstance(arg0, str):
                # dealing with sth like args = ('ascan th 0 100 10 1.0',)
                macro_name = arg0.split()[0]
            elif isinstance(arg0, collections.Sequence):
                # dealing with sth like args = (['ascan', 'th', '0', '100',
                # '10', '1.0'],)
                macro_name = arg0[0]
        else:
            # dealing with sth like args = ('ascan', 'th', '0', '100', '10',
            # '1.0')
            macro_name = args[0]
        self.debug("Executing macro: %s" % macro_name)
        macro_obj, _ = self.prepareMacro(*args, **kwargs)
        self.runMacro(macro_obj)
        return macro_obj

    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # taurus helpers
    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    @mAPI
    def getTangoFactory(self):
        """**Macro API**. Helper method that returns the tango factory.

        Parameters
        ----------

        Returns
        -------
        class:`~taurus.core.tango.TangoFactory`
            the tango factory singleton

        """
        import taurus
        return taurus.Factory()

    @mAPI
    def getDevice(self, dev_name):
        """**Macro API**. Helper method that returns the device for the given
        device name

        Parameters
        ----------
        dev_name :
            

        Returns
        -------
        class:`~taurus.core.TaurusDevice`
            the taurus device for the given device name

        """
        import taurus
        return taurus.Device(dev_name)

    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # Handle parameter objects
    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    @mAPI
    def setLogBlockStart(self):
        """**Macro API**. Specifies the begining of a block of data. Basically
        it outputs the 'BLOCK' tag

        Parameters
        ----------

        Returns
        -------

        """
        self.output(Macro.BlockStart)

    @mAPI
    def setLogBlockFinish(self):
        """**Macro API**. Specifies the end of a block of data. Basically it
        outputs the '/BLOCK' tag

        Parameters
        ----------

        Returns
        -------

        """
        self.output(Macro.BlockFinish)

    @mAPI
    def outputBlock(self, line):
        """**Macro API**. Sends an line tagged as a block to the output

        Parameters
        ----------
        line :
            

        Returns
        -------

        """
        if isinstance(line, str):
            o = line
        elif isinstance(line, collections.Sequence):
            o = "\n".join(line)
        else:
            o = str(line)
        self.output("%s\n%s\n%s" % (Macro.BlockStart, o, Macro.BlockFinish))

    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # Handle parameter objects
    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    @mAPI
    def getPools(self):
        """**Macro API**. Returns the list of known device pools.

        Parameters
        ----------

        Returns
        -------
        seq<Pool>
            the list of known device pools

        """
        return self.door.get_pools()

    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # Handle parameter objects
    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    @mAPI
    def addObj(self, obj, priority=0):
        """**Macro API**. Adds the given object to the list of controlled
        objects of this macro. In practice it means that if a stop is
        executed the stop method of the given object will be called.

        Parameters
        ----------
        obj : object
            the object to be controlled
        priority : obj:`int
            wheater or not reserve with priority [default: 0 meaning no
            priority ]

        Returns
        -------

        """
        self.executor.reserveObj(obj, self, priority=priority)

    @mAPI
    def addObjs(self, obj_list):
        """**Macro API**. Adds the given objects to the list of controlled
        objects of this macro. In practice it means that if a stop is
        executed the stop method of the given object will be called.

        Parameters
        ----------
        obj_list : obj_list: :obj:`collections.Sequence`
            list of objects to be controlled

        Returns
        -------

        """
        for o in obj_list:
            self.addObj(o)

    def returnObj(self, obj):
        """Removes the given objects to the list of controlled objects of this
        macro.

        Parameters
        ----------
        obj :
            object to be released from the control

        Returns
        -------

        """
        self.executor.returnObj(obj)

    @mAPI
    def getObj(self, name, type_class=All, subtype=All, pool=All, reserve=True):
        """**Macro API**. Gets the object of the given type belonging to the
        given pool with the given name. The object (if found) will automatically
        become controlled by the macro.

        Parameters
        ----------
        name : obj:`str`
            string representing the name of the object. Can be a regular
            expression
        type_class :
            the type of object [default: All]
        subtype :
            a string representing the subtype [default: All]
            Ex.: if type_class is Type.ExpChannel, subtype could be
            'CTExpChannel'
        pool :
            the pool to which the object should belong [default: All]
        reserve :
            automatically reserve the object for this macro [default: True]

        Returns
        -------
        type
            the object or None if no compatible object is found

        """
        if not isinstance(name, str):
            raise self._buildWrongParamExp("getObj", "name", "string",
                                           str(type(name)))

        obj = self.door.get_object(name, type_class=type_class,
                                   subtype=subtype, pool=pool)
        if obj and reserve:
            self.addObj(obj)
        return obj

    @mAPI
    def getObjs(self, names, type_class=All, subtype=All, pool=All, reserve=True):
        """**Macro API**. Gets the objects of the given type belonging to the
           given pool with the given names. The objects (if found) will
           automatically become controlled by the macro.

        Parameters
        ----------
        names :
            a string or a sequence of strings representing the
            names of the objects. Each string can be a regular
            expression
        type_class :
            the type of object (optional, default is All).
            Example: Type.Motor, Type.ExpChannel
        subtype :
            a string representing the subtype (optional,
            default is All)
            Ex.: if type_class is Type.ExpChannel, subtype could
            be 'CTExpChannel'
        pool :
            the pool to which the object should belong (optional,
            default is All)
        reserve :
            automatically reserve the object for this macro
            (optional, default is True)

        Returns
        -------
        type
            a list of objects or empty list if no compatible object is
            found

        """
        obj_list = self.door.get_objects(names, type_class=type_class,
                                         subtype=subtype, pool=pool)
        if reserve:
            self.addObjs(obj_list)
        return obj_list or []

    @mAPI
    def findObjs(self, names, type_class=All, subtype=All, pool=All,
                 reserve=True):
        """**Macro API**. Gets the objects of the given type belonging to the
        given pool with the given names. The objects (if found) will
        automatically become controlled by the macro.

        Parameters
        ----------
        names :
            a string or a sequence of strings representing the names of the
            objects. Each string can be a regular expression
        type_class :
            the type of object (optional, default is All)
        subtype :
            a string representing the subtype [default: All]
            Ex.: if type_class is Type.ExpChannel, subtype could be
            'CTExpChannel'
        pool :
            the pool to which the object should belong [default: All]
        reserve :
            automatically reserve the object for this macro [default: True]

        Returns
        -------
        type
            a list of objects or empty list if no compatible object is found

        """
        obj_list = self.door.find_objects(names, type_class=type_class,
                                          subtype=subtype, pool=pool)
        if reserve:
            self.addObjs(obj_list)
        return obj_list

    @mAPI
    def getMacroNames(self):
        """**Macro API**. Returns a list of strings containing the names of all
        known macros

        Parameters
        ----------

        Returns
        -------
        seq<:obj:`str`\>
            a sequence of macro names

        """
        return self.door.get_macro_names()

    @mAPI
    def getMacros(self, filter=None):
        """**Macro API**. Returns a sequence of
        :class:`~sardana.macroserver.msmetamacro.MacroClass`
        /:class:`~sardana.macroserver.msmetamacro.MacroFunction` objects for all
        known macros that obey the filter expression.

        Parameters
        ----------
        filter :
            a regular expression for the macro name (optional, default is None
            meaning match all macros)

        Returns
        -------
        seq<:class:`~sardana.macroserver.msmetamacro.MacroClass`
        /:class:`~sardana.macroserver.msmetamacro.MacroFunction`\>
            a sequence of :class:`~sardana.macroserver.msmetamacro.MacroClass`
            /:class:`~sardana.macroserver.msmetamacro.MacroFunction`
            objects

        """
        ret = sorted(self.door.get_macros(filter=filter).values())
        return ret

    @mAPI
    def getMacroLibraries(self, filter=None):
        """**Macro API**. Returns a sequence of
        :class:`~sardana.macroserver.msmetamacro.MacroLibrary` objects for all
        known macros that obey the filter expression.

        Parameters
        ----------
        filter :
            a regular expression for the macro library [default: None meaning
            match all macro libraries)

        Returns
        -------
        seq<:class:`~sardana.macroserver.msmetamacro.MacroLibrary`\>
            a sequence of :class:`~sardana.macroserver.msmetamacro.MacroLibrary`
            objects

        """
        ret = sorted(self.door.get_macro_libs(filter=filter).values())
        return ret

    @mAPI
    def getMacroLibrary(self, lib_name):
        """**Macro API**. Returns a
        :class:`~sardana.macroserver.msmetamacro.MacroLibrary` object for the
        given library name.

        Parameters
        ----------
        lib_name : obj:`str`
            library name

        Returns
        -------
        class:`~sardana.macroserver.msmetamacro.MacroLibrary`
            a macro library :class:`~sardana.macroserver.msmetamacro.MacroLibrary`

        """
        ret = self.door.get_macro_lib(lib_name)
        return ret

    getMacroLib = getMacroLibrary
    getMacroLibs = getMacroLibraries

    @mAPI
    def getMacroInfo(self, macro_name):
        """**Macro API**. Returns the corresponding
        :class:`~sardana.macroserver.msmetamacro.MacroClass`
        /:class:`~sardana.macroserver.msmetamacro.MacroFunction` object.

        Parameters
        ----------
        macro_name : obj:`str`
            a string with the desired macro name.

        Returns
        -------
        class:`~sardana.macroserver.msmetamacro.MacroClass`
        /:class:`~sardana.macroserver.msmetamacro.MacroFunction`
            a :class:`~sardana.macroserver.msmetamacro.MacroClass`
            /:class:`~sardana.macroserver.msmetamacro.MacroFunction` object or
            None if the macro with the given name was not found

        """
        return self.door.get_macro(macro_name)

    @mAPI
    def getMotion(self, elems, motion_source=None, read_only=False, cache=True):
        """**Macro API**. Returns a new Motion object containing the given
        elements.

        Parameters
        ----------
        elems :
            list of moveable object names
        motion_source :
            obj or list of objects containing moveable elements. Usually this
            is a Pool object or a list of Pool objects (optional, default is
            None, meaning all known pools will be searched for the given
            moveable items
        read_only :
            not used. Reserved for future use (Default value = False)
        cache :
            not used. Reserved for future use (Default value = True)

        Returns
        -------
        type
            a Motion object

        """

        decoupled = False
        try:
            decoupled = self.getEnv("MotionDecoupled")
        except UnknownEnv:
            pass

        motion = self.door.get_motion(elems, motion_source=motion_source,
                                      read_only=read_only, cache=cache,
                                      decoupled=decoupled)
        if motion is not None:
            self.addObj(motion, priority=1)
        return motion

    @mAPI
    def getElementsWithInterface(self, interface):
        """

        Parameters
        ----------
        interface :
            

        Returns
        -------

        """
        return self.door.get_elements_with_interface(interface)

    @mAPI
    def getControllers(self):
        """ """
        return self.door.get_controllers()

    @mAPI
    def getMoveables(self):
        """ """
        return self.door.get_moveables()

    @mAPI
    def getMotors(self):
        """ """
        return self.door.get_motors()

    @mAPI
    def getPseudoMotors(self):
        """ """
        return self.door.get_pseudo_motors()

    @mAPI
    def getIORegisters(self):
        """ """
        return self.door.get_io_registers()

    @mAPI
    def getMeasurementGroups(self):
        """ """
        return self.door.get_measurement_groups()

    @mAPI
    def getExpChannels(self):
        """ """
        return self.door.get_exp_channels()

    @mAPI
    def getCounterTimers(self):
        """ """
        return self.door.get_counter_timers()

    @mAPI
    def get0DExpChannels(self):
        """ """
        return self.door.get_0d_exp_channels()

    @mAPI
    def get1DExpChannels(self):
        """ """
        return self.door.get_1d_exp_channels()

    @mAPI
    def get2DExpChannels(self):
        """ """
        return self.door.get_2d_exp_channels()

    @mAPI
    def getPseudoCounters(self):
        """ """
        return self.door.get_pseudo_counters()

    @mAPI
    def getInstruments(self):
        """ """
        return self.door.get_instruments()

    @mAPI
    def getElementWithInterface(self, interface, name):
        """

        Parameters
        ----------
        interface :
            
        name :
            

        Returns
        -------

        """
        return self.door.get_element_with_interface(interface, name)

    @mAPI
    def getController(self, name):
        """

        Parameters
        ----------
        name :
            

        Returns
        -------

        """
        return self.door.get_controller(name)

    @mAPI
    def getMoveable(self, name):
        """

        Parameters
        ----------
        name :
            

        Returns
        -------

        """
        return self.door.get_moveable(name)

    @mAPI
    def getMotor(self, name):
        """

        Parameters
        ----------
        name :
            

        Returns
        -------

        """
        return self.door.get_motor(name)

    @mAPI
    def getPseudoMotor(self, name):
        """

        Parameters
        ----------
        name :
            

        Returns
        -------

        """
        return self.door.get_pseudo_motor(name)

    @mAPI
    def getIORegister(self, name):
        """

        Parameters
        ----------
        name :
            

        Returns
        -------

        """
        return self.door.get_io_register(name)

    @mAPI
    def getMeasurementGroup(self, name):
        """

        Parameters
        ----------
        name :
            

        Returns
        -------

        """
        return self.door.get_measurement_group(name)

    @mAPI
    def getExpChannel(self, name):
        """

        Parameters
        ----------
        name :
            

        Returns
        -------

        """
        return self.door.get_exp_channel(name)

    @mAPI
    def getCounterTimer(self, name):
        """

        Parameters
        ----------
        name :
            

        Returns
        -------

        """
        return self.door.get_counter_timer(name)

    @mAPI
    def get0DExpChannel(self, name):
        """

        Parameters
        ----------
        name :
            

        Returns
        -------

        """
        return self.door.get_0d_exp_channel(name)

    @mAPI
    def get1DExpChannel(self, name):
        """

        Parameters
        ----------
        name :
            

        Returns
        -------

        """
        return self.door.get_1d_exp_channel(name)

    @mAPI
    def get2DExpChannel(self, name):
        """

        Parameters
        ----------
        name :
            

        Returns
        -------

        """
        return self.door.get_2d_exp_channel(name)

    @mAPI
    def getPseudoCounter(self, name):
        """

        Parameters
        ----------
        name :
            

        Returns
        -------

        """
        return self.door.get_pseudo_counter(name)

    @mAPI
    def getInstrument(self, name):
        """

        Parameters
        ----------
        name :
            

        Returns
        -------

        """
        return self.door.get_instrument(name)

    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # Handle macro environment
    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    @mAPI
    def getEnv(self, key=None, macro_name=None, door_name=None):
        """**Macro API**. Gets the local environment matching the given
        parameters:
        
           - door_name and macro_name define the context where to look for
             the environment. If both are None, the global environment is
             used. If door name is None but macro name not, the given macro
             environment is used and so on...
           - If key is None it returns the complete environment, otherwise
             key must be a string containing the environment variable name.

        Parameters
        ----------
        key : obj:`str`
            environment variable name [default: None, meaning all environment]
        door_name : obj:`str`
            local context for a given door [default: None, meaning no door
            context is used]
        macro_name : obj:`str`
            local context for a given macro [default: None, meaning no macro
            context is used]

        Returns
        -------
        obj:`dict`
            a :obj:`dict` containing the environment

        """
        door_name = door_name or self.getDoorName()
        macro_name = macro_name or self._name

        return self.macro_server.get_env(key=key, macro_name=macro_name,
                                         door_name=door_name)

    @mAPI
    def getGlobalEnv(self):
        """**Macro API**. Returns the global environment.

        Parameters
        ----------

        Returns
        -------
        obj:`dict`
            a :obj:`dict` containing the global environment

        """
        return self.macro_server.get_env()

    @mAPI
    def getAllEnv(self):
        """**Macro API**. Returns the enviroment for the macro.

        Parameters
        ----------

        Returns
        -------
        obj:`dict`
            a :obj:`dict` containing the environment for the macro

        """
        return self.getEnv(None)

    @mAPI
    def getAllDoorEnv(self):
        """**Macro API**. Returns the enviroment for the door where the macro
        is running.

        Parameters
        ----------

        Returns
        -------
        obj:`dict`
            a :obj:`dict` containing the environment

        """
        return self.door.get_env()

    @mAPI
    def setEnv(self, key, value):
        """**Macro API**. Sets the environment key to the new value and
        stores it persistently.

        Parameters
        ----------
        key :
            
        value :
            

        Returns
        -------
        obj:`tuple`\<:obj:`str`\, object>
            a :obj:`tuple` with the key and value objects stored

        """
        return self.door.set_env(key, value)

    @mAPI
    def unsetEnv(self, key):
        """**Macro API**. Unsets the given environment variable.

        Parameters
        ----------
        key : obj:`str
            the environment variable name

        Returns
        -------

        """
        return self.macro_server.unset_env(key)

    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # Reload API
    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    @mAPI
    def reloadLibrary(self, lib_name):
        """**Macro API**. Reloads the given library(=module) names

        Parameters
        ----------
        lib_name : obj:`str`
            library(=module) name

        Returns
        -------
        type
            the reloaded python module object

        """
        return self.door.reload_lib(lib_name)

    @mAPI
    def reloadMacro(self, macro_name):
        """**Macro API**. Reloads the module corresponding to the given macro
        name

        Parameters
        ----------
        macro_name : obj:`str
            macro name

        Returns
        -------

        """
        return self.door.reload_macro(macro_name)

    @mAPI
    def reloadMacros(self, macro_names):
        """**Macro API**. Reloads the modules corresponding to the given macro
        names.

        Parameters
        ----------
        macro_names : sequence<:obj:`str`\
            a list of macro names

        Returns
        -------

        """
        return self.reload_macros(macro_names)

    @mAPI
    def reloadMacroLibrary(self, lib_name):
        """**Macro API**. Reloads the given library(=module) names

        Parameters
        ----------
        lib_name : obj:`str`
            library(=module) name

        Returns
        -------
        class:`~sardana.macroserver.metamacro.MacroLibrary`
            the :class:`~sardana.macroserver.metamacro.MacroLibrary` for the
            reloaded library

        """
        return self.door.reload_macro_lib(lib_name)

    @mAPI
    def reloadMacroLibraries(self, lib_names):
        """**Macro API**. Reloads the given library(=module) names

        Parameters
        ----------
        lib_names :
            

        Returns
        -------
        seq<:class:`~sardana.macroserver.metamacro.MacroLibrary`\>
            a sequence of :class:`~sardana.macroserver.metamacro.MacroLibrary`
            objects for the reloaded libraries

        """
        return self.door.reload_macro_libs(lib_names)

    reloadMacroLib = reloadMacroLibrary
    reloadMacroLibs = reloadMacroLibraries

    @mAPI
    def getViewOption(self, name):
        """

        Parameters
        ----------
        name :
            

        Returns
        -------

        """
        return self._getViewOption(name)

    @mAPI
    def getViewOptions(self):
        """ """
        vo = self._getViewOptions()
        # ensure that all view options known by sardana are present, in case
        # there were missing ones, update _ViewOptions dictionary after
        # initializing missing options with the default values
        ivo = copy.deepcopy(vo)
        ViewOption.init_options(ivo)
        if vo != ivo:
            self.setEnv('_ViewOptions', vo)
        return ivo

    @mAPI
    def setViewOption(self, name, value):
        """

        Parameters
        ----------
        name :
            
        value :
            

        Returns
        -------

        """
        vo = self._getViewOptions()
        vo[name] = value
        self.setEnv('_ViewOptions', vo)

    @mAPI
    def resetViewOption(self, name):
        """

        Parameters
        ----------
        name :
            

        Returns
        -------

        """
        vo = self._getViewOptions()
        ViewOption.reset_option(vo, name)
        self.setEnv('_ViewOptions', vo)
        return vo.get(name)

    #@}

    # @name Unofficial Macro API
    #    This list contains the set of methods that are <b>NOT</b> part of the
    #  the macro developer knows what he is doing.
    #    Please check before is there is an official API that does the samething
    #  before executing any of these methods.
    #    If you see that your macro needs to execute any of these methods please
    #  consider informing the MacroServer developer so he may expose this in a
    #  safe way.
    #@{
    def _getViewOptions(self):
        """Gets _ViewOption dictionary. If it is not defined in the environment,
        sets it with the default values dictionary and returns it.

        Parameters
        ----------

        Returns
        -------

        """
        try:
            vo = self.getEnv('_ViewOptions')
        except UnknownEnv:
            vo = ViewOption.init_options(dict())
            self.setEnv('_ViewOptions', vo)
        return vo

    def _getViewOption(self, name):
        """Gets _ViewOption of a given name. If it is not defined in
        the environment, sets it to a default value and returns it.

        Parameters
        ----------
        name :
            

        Returns
        -------

        """
        view_options = self._getViewOptions()
        if name not in view_options:
            ViewOption.reset_option(view_options, name)
            self.setEnv('_ViewOptions', view_options)
        return view_options[name]

    def _input(self, msg, *args, **kwargs):
        """**Unofficial Macro API**.
        If args is present, it is written to standard output without a trailing
        newline. The function then reads a line from input, converts it to a
        string (stripping a trailing newline), and returns that.
        
        Depending on which type of application you are running, some of the
        keywords may have no effect (ex.: spock ignores decimals when a number
        is asked).
        
        Recognized kwargs:
        
            - data_type : [default: Type.String] specific input type. Can also
              specify a sequence of strings with possible values (use
              allow_multiple=True to say multiple values can be selected)
            - key : [default: no default] variable/label to assign to this input
            - unit: [default: no default] units (useful for GUIs)
            - timeout : [default: None, meaning wait forever for input]
            - default_value : [default: None, meaning no default value]
              When given, it must be compatible with data_type
            - allow_multiple : [default: False] in case data_type is a
              sequence of values, allow multiple selection
            - minimum : [default: None] When given, must be compatible with data_type (useful for GUIs)
            - maximum : [default: None] When given, must be compatible with data_type (useful for GUIs)
            - step : [default: None] When given, must be compatible with data_type (useful for GUIs)
            - decimals : [default: None] When given, must be compatible with data_type (useful for GUIs)
        
        Examples::
        
            device_name = self.input("Which device name (%s)?", "tab separated")
        
            point_nb = self.input("How many points?", data_type=Type.Integer)
        
            calc_mode = self.input("Which algorithm?", data_type=["Average", "Integral", "Sum"],
                                   default_value="Average", allow_multiple=False)

        Parameters
        ----------
        msg :
            
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        if not self.interactive:
            self.warning("Non interactive macro '%s' is asking for input "
                         "(please set this macro interactive to True)",
                         self.getName())
        if self._interactive_mode:
            kwargs['data_type'] = kwargs.get('data_type', Type.String)
            kwargs['allow_multiple'] = kwargs.get('allow_multiple', False)
            kwargs['macro_id'] = self.getID()
            kwargs['macro_name'] = self.getName()
            kwargs['macro'] = self
            return self.getDoorObj().input(msg, *args, **kwargs)
        else:
            if 'default_value' not in kwargs:
                if 'key' not in kwargs:
                    self.warning("%s running in non attended mode was asked "
                                 "for input without default value or key. "
                                 "Returning None")
                    return None
                else:
                    return self.getEnv(kwargs['key'])
            return kwargs['default_value']

    def _output(self, msg, *args, **kwargs):
        """****Unofficial Macro API**.
        Record a log message in this object's output. Accepted *args* and
        *kwargs* are the same as :meth:`logging.Logger.log`.
        Example::
        
            self.output("this is a print for macro %s", self.getName())

        Parameters
        ----------
        msg : obj:`str`
            the message to be recorded
        args :
            list of arguments
        kwargs :
            list of keyword argument
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        return Logger.output(self, msg, *args, **kwargs)

    def _outputBlock(self, line):
        """**Unofficial Macro API**.
        Sends a line tagged as a block to the output

        Parameters
        ----------
        line :
            

        Returns
        -------

        """
        if isinstance(line, str):
            o = line
        elif isinstance(line, collections.Sequence):
            o = "\n".join(line)
        else:
            o = str(line)
        self._output("%s\n%s\n%s" % (Macro.BlockStart, o, Macro.BlockFinish))

    def _log(self, level, msg, *args, **kwargs):
        """**Unofficial Macro API**.
        Record a log message in this object's logger. Accepted *args* and
        *kwargs* are the same as :meth:`logging.Logger.log`.
        Example::
        
            self.debug(logging.INFO, "this is a info log message for macro %s", self.getName())

        Parameters
        ----------
        level : obj:`int`
            the record level
        msg : obj:`str`
            the message to be recorded
        args :
            list of arguments
        kwargs :
            list of keyword argument
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        return Logger.log(self, level, msg, *args, **kwargs)

    def _debug(self, msg, *args, **kwargs):
        """**Unofficial Macro API**.
        Record a debug message in this object's logger. Accepted *args* and
        *kwargs* are the same as :meth:`logging.Logger.debug`.
        Example::
        
            self.debug("this is a log message for macro %s", self.getName())

        Parameters
        ----------
        msg : obj:`str`
            the message to be recorded
        args :
            list of arguments
        kw :
            list of keyword argument
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        return Logger.debug(self, msg, *args, **kwargs)

    def _info(self, msg, *args, **kwargs):
        """**Unofficial Macro API**.
        Record an info message in this object's logger. Accepted *args* and
        *kwargs* are the same as :meth:`logging.Logger.info`.
        Example::
        
            self.info("this is a log message for macro %s", self.getName())

        Parameters
        ----------
        msg : obj:`str`
            the message to be recorded
        args :
            list of arguments
        kwargs :
            list of keyword argument
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        return Logger.info(self, msg, *args, **kwargs)

    @mAPI
    def _warning(self, msg, *args, **kwargs):
        """**Unofficial Macro API**.
        Record a warning message in this object's logger. Accepted *args* and
        *kwargs* are the same as :meth:`logging.Logger.warning`.
        Example::
        
            self.warning("this is a log message for macro %s", self.getName())

        Parameters
        ----------
        msg : obj:`str`
            the message to be recorded
        args :
            list of arguments
        kwargs :
            list of keyword argument
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        return Logger.warning(self, msg, *args, **kwargs)

    def _error(self, msg, *args, **kwargs):
        """**Unofficial Macro API**.
        Record an error message in this object's logger. Accepted *args* and
        *kwargs* are the same as :meth:`logging.Logger.error`.
        Example::
        
            self.error("this is a log message for macro %s", self.getName())

        Parameters
        ----------
        msg : obj:`str`
            the message to be recorded
        args :
            list of arguments
        kwargs :
            list of keyword arguments
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        return Logger.error(self, msg, *args, **kwargs)

    def _critical(self, msg, *args, **kwargs):
        """**Unofficial Macro API**.
        Record a critical message in this object's logger. Accepted *args* and
        *kwargs* are the same as :meth:`logging.Logger.critical`.
        Example::
        
            self.critical("this is a log message for macro %s", self.getName())

        Parameters
        ----------
        msg : obj:`str`
            the message to be recorded
        args :
            list of arguments
        kwargs :
            list of keyword argument
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        return Logger.critical(self, msg, *args, **kwargs)

    def _trace(self, msg, *args, **kwargs):
        """**Unofficial Macro API**. Record a trace message in this object's logger.

        Parameters
        ----------
        msg :
            str) the message to be recorded
        args :
            list of arguments
        kw :
            list of keyword argument
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        return Logger.trace(self, msg, *args, **kwargs)

    def _traceback(self, *args, **kwargs):
        """**Unofficial Macro API**.
        Logs the traceback with level TRACE on the macro logger.

        Parameters
        ----------
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        return Logger.traceback(self, *args, **kwargs)

    def _stack(self, *args, **kwargs):
        """**Unofficial Macro API**.
        Logs the stack with level TRACE on the macro logger.

        Parameters
        ----------
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        return Logger.stack(self, *args, **kwargs)

    def _report(self, msg, *args, **kwargs):
        """**Unofficial Macro API**.
        Record a log message in the sardana report (if enabled) with default
        level **INFO**. The msg is the message format string, and the args are
        the arguments which are merged into msg using the string formatting
        operator. (Note that this means that you can use keywords in the
        format string, together with a single dictionary argument.)
        
        *kwargs* are the same as :meth:`logging.Logger.debug` plus an optional
        level kwargs which has default value **INFO**
        
        Example::
        
            self.report("this is an official report of macro %s", self.getName())

        Parameters
        ----------
        msg : obj:`str`
            the message to be recorded
        args :
            list of arguments
        kwargs :
            list of keyword argument
        *args :
            
        **kwargs :
            

        Returns
        -------

        """
        return self.door.report(msg, *args, **kwargs)

    def _flushOutput(self):
        """**Unofficial Macro API**.
        Flushes the output buffer.

        Parameters
        ----------

        Returns
        -------

        """
        return Logger.flushOutput(self)

    @property
    def executor(self):
        """**Unofficial Macro API**. Alternative to :meth:`getExecutor` that
        does not throw StopException in case of a Stop. This should be
        called only internally

        Parameters
        ----------

        Returns
        -------

        """
        return self._executor

    @property
    def door(self):
        """**Unofficial Macro API**. Alternative to :meth:`getDoorObj` that
        does not throw StopException in case of a Stop. This should be
        called only internally

        Parameters
        ----------

        Returns
        -------

        """
        return self.executor.getDoor()

    @property
    def parent_macro(self):
        """**Unofficial Macro API**. Alternative to getParentMacro that does not
        throw StopException in case of a Stop. This should be called only
        internally by the *Executor*

        Parameters
        ----------

        Returns
        -------

        """
        return self._parent_macro

    @property
    def description(self):
        """**Unofficial Macro API**. Alternative to :meth:`getDescription` that
        does not throw StopException in case of a Stop. This should be
        called only internally by the *Executor*

        Parameters
        ----------

        Returns
        -------

        """
        return self._desc

    def isAborted(self):
        """**Unofficial Macro API**."""
        return self._aborted

    def isStopped(self):
        """**Unofficial Macro API**."""
        return self._stopped

    def isPaused(self):
        """**Unofficial Macro API**."""
        return self._pause_event.isPaused()

    def hasResult(self):
        """**Unofficial Macro API**. Returns True if the macro should return
        a result or False otherwise

        Parameters
        ----------

        Returns
        -------
        bool
            True if the macro should return a result or False otherwise

        """
        return len(self.result_def) > 0

    def getResult(self):
        """**Unofficial Macro API**. Returns the macro result object (if any)
        
        :return: the macro result object or None

        Parameters
        ----------

        Returns
        -------

        """
        return self._out_pars

    def setResult(self, result):
        """**Unofficial Macro API**. Sets the result of this macro

        Parameters
        ----------
        result :
            object) the result for this macr

        Returns
        -------

        """
        self._out_pars = result

    # @name Internal methods
    #  This list contains the set of methods that are for INTERNAL macro usage.
    #  Macro developers should never call any of these methods
    #@{

    @staticmethod
    def _buildWrongParamExp(method_name, param_name, expected, found):
        """**Internal method**.

        Parameters
        ----------
        method_name :
            
        param_name :
            
        expected :
            
        found :
            

        Returns
        -------

        """
        s = "Macro.%s called with wrong parameter type in '%s'. " \
            "Expected %s got %s" % (method_name, param_name, expected, found)
        return MacroWrongParameterType(s)

    def _getName(self):
        """**Internal method**."""
        return self._name

    def _getDescription(self):
        """**Internal method**."""
        return self._desc

    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-
    # Macro execution methods
    #-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-~-

    def _getMacroStatus(self):
        """**Internal method**.
        Returns the current macro status. Macro status is a :obj:`dict` where
        keys are the strings:
        
            * *id* - macro ID (internal usage only)
            * *range* - the full progress range of a macro (usually a
              :obj:`tuple` of two numbers (0, 100))
            * *state* - the current macro state, a string which can have values
              *start*, *step*, *stop* and *abort*
            * *step* - the current step in macro. Should be a value inside the
              allowed macro range

        Parameters
        ----------

        Returns
        -------
        obj:`dict`
            the macro status

        """
        return self._macro_status

    def _shouldRaiseStopException(self):
        """ """
        return self.isStopped() and not self.isProcessingStop()

    def _reserveObjs(self, args):
        """**Internal method**. Used to reserve a set of objects for this
        macro

        Parameters
        ----------
        args :
            

        Returns
        -------

        """
        for obj in args:
            # isiterable
            if not type(obj) in list(map(type, ([], ()))):
                # if not operator.isSequenceType(obj) or type(obj) in
                # types.StringTypes:
                obj = (obj,)
            for sub_obj in obj:
                if isinstance(sub_obj, PoolElement):
                    self.addObj(sub_obj)

    def exec_(self):
        """**Internal method**. Execute macro as an iterator"""
        self._macro_thread = threading.current_thread()
        macro_status = self.getMacroStatus()

        # make sure a 0.0 progress is sent
        yield macro_status

        # Avoid repeating same information on subsequent events. If, in the
        # future, clients that connect in the middle of macro execution need
        # this information, just simply remove the lines below
        del macro_status['name']
        del macro_status['macro_line']

        # allow any macro to be paused at the beginning of its execution
        self.pausePoint()

        # Run the macro or obtain a generator
        res = self.run(*self._in_pars)

        # If macro returns a generator then running the macro means go through
        # the generator steps, otherwise the macro has already ran
        if isinstance(res, types.GeneratorType):
            it = iter(res)
            for i in it:
                if isinstance(i, collections.Mapping):
                    new_range = i.get('range')
                    if new_range is not None:
                        macro_status['range'] = new_range
                    new_step = i.get('step')
                    if new_step is not None:
                        macro_status['step'] = new_step
                elif isinstance(i, numbers.Number):
                    macro_status['step'] = i
                macro_status['state'] = 'step'
                yield macro_status
            # make sure a 'stop' progress is sent in case an exception occurs
            macro_status['state'] = 'stop'
        else:
            self._out_pars = res
            macro_status['step'] = 100.0
        macro_status['state'] = 'finish'
        yield macro_status

    def __prepareResult(self, out):
        """**Internal method**. Decodes the given output in order to be able to
        send to the result channel

        :param out: output value

        :return: the output as a sequence of strings
        """
        if out is None:
            out = ()
        if isinstance(out, collections.Sequence) and not type(out) in str:
            out = list(map(str, out))
        else:
            out = (str(out),)
        return out

    def _stopOnError(self):
        """**Internal method**. The stop procedure. Calls the user 'on_abort'
        protecting it against exceptions

        Parameters
        ----------

        Returns
        -------

        """
        try:
            self.on_stop()
        except Exception:
            Logger.error(self, "Error in on_stop(): %s",
                         traceback.format_exc())
            Logger.debug(self, "Details: ", exc_info=1)

    def _abortOnError(self):
        """**Internal method**. The stop procedure. Calls the user 'on_abort'
        protecting it against exceptions

        Parameters
        ----------

        Returns
        -------

        """
        try:
            self.on_abort()
        except ReleaseException:
            pass
        except Exception:
            Logger.error(self, "Error in on_abort(): %s",
                         traceback.format_exc())
            Logger.debug(self, "Details: ", exc_info=1)

    def _pausePoint(self, timeout=None):
        """**Internal method**.

        Parameters
        ----------
        timeout :
             (Default value = None)

        Returns
        -------

        """
        if self._pause_event.isPaused():
            self.on_pause()
        self._pause_event.wait(timeout)

    def stop(self):
        """**Internal method**. Activates the stop flag on this macro."""
        self._stopped = True

    def abort(self):
        """**Internal method**. Aborts the macro abruptly."""
        # carefull: Inside this method never call a method that has the
        # mAPI decorator
        Logger.debug(self, "Aborting...")
        self._aborted = True
        ret, i = 0, 0
        while ret != 1:
            self.__resumeForAbort()
            th = self._macro_thread
            th_id = ctypes.c_long(th.ident)
            Logger.debug(self, "Sending AbortException to %s", th.name)
            ret = _asyncexc(th_id, ctypes.py_object(AbortException))
            i += 1
            if ret == 0:
                # try again
                if i > 2:
                    self.error("Failed to abort after three tries!")
                    break
                time.sleep(0.1)
            if ret > 1:
                # if it returns a number greater than one, you're in trouble,
                # and you should call it again with exc=NULL to revert the
                # effect
                asyncexc(th_id, None)
                Logger.error(
                    self, "Failed to abort (unknown error code %d)" % ret)
                break

    def setProcessingStop(self, yesno):
        """**Internal method**. Activates the processing stop flag on this
        macro

        Parameters
        ----------
        yesno :
            

        Returns
        -------

        """
        self._processingStop = yesno

    def isProcessingStop(self):
        """**Internal method**. Checks if this macro is processing stop"""
        return self._processingStop

    def pause(self, cb=None):
        """**Internal method**. Pauses the macro execution. To be called by the
        Door running the macro to pause the current macro

        Parameters
        ----------
        cb :
             (Default value = None)

        Returns
        -------

        """
        self._pause_event.pause(cb=cb)

    def resume(self, cb=None):
        """**Internal method**. Resumes the macro execution. To be called by
        the Door running the macro to resume the current macro

        Parameters
        ----------
        cb :
             (Default value = None)

        Returns
        -------

        """
        self._pause_event.resume(cb=cb)

    def __resumeForAbort(self):
        """Called internally to resume the macro execution in case of an abort.
        The macro is resumed but instead of allowing the next user instruction
        to proceed it just waits for an ashyncronous AbortException to be
        thrown"""
        self._pause_event.resumeForAbort()

    #@}

    def __getattr__(self, name):
        try:
            self.door.get_macro(name)
        except UnknownMacro:
            raise AttributeError("%r object has no attribute %r" %
                                 (type(self).__name__, name))

        def f(*args, **kwargs):
            """

            Parameters
            ----------
            *args :
                
            **kwargs :
                

            Returns
            -------

            """
            self.syncLog()
            opts = dict(parent_macro=self, executor=self.executor)
            kwargs.update(opts)
            eargs = [name]
            eargs.extend(args)
            return self.execMacro(*eargs, **kwargs)

        setattr(self, name, f)
        return f


class iMacro(Macro):
    """ """

    interactive = True


class MacroFunc(Macro):
    """ """

    def __init__(self, *args, **kwargs):
        function = kwargs['function']
        self._function = function
        kwargs['as'] = self._function.__name__
        if function.param_def is not None:
            self.param_def = function.param_def
        if function.result_def is not None:
            self.result_def = function.result_def
        if function.env is not None:
            self.env = function.env
        if function.hints is not None:
            self.hints = function.hints
        if function.interactive is not None:
            self.interactive = function.interactive
        Macro.__init__(self, *args, **kwargs)

    def run(self, *args):
        """

        Parameters
        ----------
        *args :
            

        Returns
        -------

        """
        return self._function(self, *args)
