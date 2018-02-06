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

"""
    Macro library containning scan macros for the macros server Tango device
    server as part of the Sardana project.

   Available Macros are:
     ascan family: ascan, a2scan, a3scan, a4scan and amultiscan
     dscan family: dscan, d2scan, d3scan, d4scan and dmultiscan
     mesh
     fscan
     scanhist
"""

__all__ = ["a2scan", "a3scan", "a4scan", "amultiscan", "aNscan", "ascan",
           "d2scan", "d3scan", "d4scan", "dmultiscan", "dNscan", "dscan",
           "fscan", "mesh",
           "a2scanc", "a3scanc", "a4scanc", "ascanc",
           "d2scanc", "d3scanc", "d4scanc", "dscanc",
           "meshc",
           "a2scanct", "a3scanct", "a4scanct", "ascanct",
           "scanhist", "getCallable", "UNCONSTRAINED"]

__docformat__ = 'restructuredtext'

import os
import copy
import datetime

import numpy

from taurus.core.util import SafeEvaluator

from sardana.macroserver.msexception import UnknownEnv
from sardana.macroserver.macro import Hookable, Macro, Type, ParamRepeat, \
    Table, List
from sardana.macroserver.scan.gscan import SScan, CTScan, HScan, \
    MoveableDesc, CSScan, TScan
from sardana.util.motion import MotionPath
from sardana.util.tree import BranchNode

UNCONSTRAINED = "unconstrained"

StepMode = 's'
# TODO: change it to be more verbose e.g. ContinuousSwMode
ContinuousMode = 'c'
ContinuousHwTimeMode = 'ct'
HybridMode = 'h'


def getCallable(repr):
    """
    returns a function .
    Ideas: repr could be an URL for a file where the function is contained,
    or be evaluable code, or a pickled function object,...

    In any case, the return from it should be a callable of the form:
    f(x1,x2) where x1, x2 are points in the moveable space and the return value
    of f is True if the movement from x1 to x2 is allowed. False otherwise
    """
    if repr == UNCONSTRAINED:
        return lambda x1, x2: True
    else:
        return lambda: None


# TODO: remove starts
def _calculate_positions(moveable_node, start, end):
    '''Function to calculate starting and ending positions on the physical
    motors level.
    :param moveable_node: (BaseNode) node representing a moveable.
                          Can be a BranchNode representing a PseudoMotor,
                          or a LeafNode representing a PhysicalMotor).
    :param start: (float) starting position of the moveable
    :param end: (float) ending position of the moveable

    :return: (list<(float,float)>) a list of tuples comprising starting
             and ending positions. List order is important and preserved.'''
    start_positions = []
    end_positions = []
    if isinstance(moveable_node, BranchNode):
        pseudo_node = moveable_node
        moveable = pseudo_node.data
        moveable_nodes = moveable_node.children
        starts = moveable.calcPhysical(start)
        ends = moveable.calcPhysical(end)
        for moveable_node, start, end in zip(moveable_nodes, starts,
                                             ends):
            _start_positions, _end_positions = _calculate_positions(
                moveable_node,
                start, end)
            start_positions += _start_positions
            end_positions += _end_positions
    else:
        start_positions = [start]
        end_positions = [end]

    return start_positions, end_positions


class aNscan(Hookable):

    hints = {'scan': 'aNscan', 'allowsHooks': ('pre-scan', 'pre-move',
                                               'post-move', 'pre-acq',
                                               'post-acq', 'post-step',
                                               'post-scan')}
    # env = ('ActiveMntGrp',)

    """N-dimensional scan. This is **not** meant to be called by the user,
    but as a generic base to construct ascan, a2scan, a3scan,..."""

    def _prepare(self, motorlist, startlist, endlist, scan_length, integ_time,
                 mode=StepMode, latency_time=0, **opts):

        self.motors = motorlist
        self.starts = numpy.array(startlist, dtype='d')
        self.finals = numpy.array(endlist, dtype='d')
        self.mode = mode
        self.integ_time = integ_time
        self.opts = opts
        if len(self.motors) == self.starts.size == self.finals.size:
            self.N = self.finals.size
        else:
            raise ValueError(
                'Moveablelist, startlist and endlist must all be same length')

        moveables = []
        for m, start, final in zip(self.motors, self.starts, self.finals):
            moveables.append(MoveableDesc(moveable=m, min_value=min(
                start, final), max_value=max(start, final)))
        moveables[0].is_reference = True

        env = opts.get('env', {})
        constrains = [getCallable(cns) for cns in opts.get(
            'constrains', [UNCONSTRAINED])]
        extrainfodesc = opts.get('extrainfodesc', [])

        # Hooks are not always set at this point. We will call getHooks
        # later on in the scan_loop
        # self.pre_scan_hooks = self.getHooks('pre-scan')
        # self.post_scan_hooks = self.getHooks('post-scan'

        if mode == StepMode:
            self.nr_interv = scan_length
            self.nr_points = self.nr_interv + 1
            self.interv_sizes = (self.finals - self.starts) / self.nr_interv
            self.name = opts.get('name', 'a%iscan' % self.N)
            self._gScan = SScan(self, self._stepGenerator,
                                moveables, env, constrains, extrainfodesc)
        elif mode in [ContinuousMode, ContinuousHwTimeMode]:
            # TODO: probably not 100% correct,
            #      the idea is to allow passing a list of waypoints
            if isinstance(endlist[0], list):
                self.waypoints = self.finals
            else:
                self.waypoints = [self.finals]
            self.nr_waypoints = len(self.waypoints)
            if mode == ContinuousMode:
                self.slow_down = scan_length
                # aNscans will only have two waypoints (the start and the final
                # positions)
                self.nr_waypoints = 2
                self.way_lengths = (
                    self.finals - self.starts) / (self.nr_waypoints - 1)
                self.name = opts.get('name', 'a%iscanc' % self.N)
                self._gScan = CSScan(self, self._waypoint_generator,
                                     self._period_generator, moveables, env,
                                     constrains, extrainfodesc)
            elif mode == ContinuousHwTimeMode:
                self.nr_interv = scan_length
                self.nr_points = self.nr_interv + 1
                mg_name = self.getEnv('ActiveMntGrp')
                mg = self.getMeasurementGroup(mg_name)
                mg_latency_time = mg.getLatencyTime()
                if mg_latency_time > latency_time:
                    self.info("Choosing measurement group latency time: %f" %
                              mg_latency_time)
                    latency_time = mg_latency_time
                self.latency_time = latency_time
                self.name = opts.get('name', 'a%iscanct' % self.N)
                self._gScan = CTScan(self, self._waypoint_generator_hwtime,
                                     moveables,
                                     env,
                                     constrains,
                                     extrainfodesc)
        elif mode == HybridMode:
            self.nr_interv = scan_length
            self.nr_points = self.nr_interv + 1
            self.interv_sizes = (self.finals - self.starts) / self.nr_interv
            self.name = opts.get('name', 'a%iscanh' % self.N)
            self._gScan = HScan(self, self._stepGenerator,
                                moveables, env, constrains, extrainfodesc)
        else:
            raise ValueError('invalid value for mode %s' % mode)
        # _data is the default member where the Macro class stores the data.
        # Assign the date produced by GScan (or its subclasses) to it so all
        # the Macro infrastructure related to the data works e.g. getter,
        # property, etc. Ideally this should be done by the data setter
        # but this is available in the Macro class and we inherit from it
        # latter. More details in sardana-org/sardana#683.
        self._data = self._gScan.data

    def _stepGenerator(self):
        step = {}
        step["integ_time"] = self.integ_time
        step["pre-move-hooks"] = self.getHooks('pre-move')
        step["post-move-hooks"] = self.getHooks('post-move')
        step["pre-acq-hooks"] = self.getHooks('pre-acq')
        step["post-acq-hooks"] = self.getHooks('post-acq') + self.getHooks(
            '_NOHINTS_')
        step["post-step-hooks"] = self.getHooks('post-step')

        step["check_func"] = []
        for point_no in xrange(self.nr_points):
            step["positions"] = self.starts + point_no * self.interv_sizes
            step["point_id"] = point_no
            yield step

    def _waypoint_generator(self):
        step = {}
        step["pre-move-hooks"] = self.getHooks('pre-move')
        step["post-move-hooks"] = self.getHooks('post-move')
        step["check_func"] = []
        step["slow_down"] = self.slow_down
        for point_no in xrange(self.nr_waypoints):
            step["positions"] = self.starts + point_no * self.way_lengths
            step["waypoint_id"] = point_no
            yield step

    def _waypoint_generator_hwtime(self):

        # CScan in its constructor populates a list of data structures - trees.
        # Each tree represent one Moveables with its hierarchy of inferior
        # moveables.
        moveables_trees = self._gScan.get_moveables_trees()
        step = {}
        step["pre-move-hooks"] = self.getHooks('pre-move')
        post_move_hooks = self.getHooks(
            'post-move') + [self._fill_missing_records]
        step["post-move-hooks"] = post_move_hooks
        step["check_func"] = []
        step["active_time"] = self.nr_points * (self.integ_time +
                                                self.latency_time)
        step["positions"] = []
        step["start_positions"] = []
        starts = self.starts
        for point_no, waypoint in enumerate(self.waypoints):
            for start, end, moveable_tree in zip(starts, waypoint,
                                                 moveables_trees):
                moveable_root = moveable_tree.root()
                start_positions, end_positions = _calculate_positions(
                    moveable_root, start, end)
                step["start_positions"] += start_positions
                step["positions"] += end_positions
                step["waypoint_id"] = point_no
                starts = waypoint
            yield step

    def _period_generator(self):
        step = {}
        step["integ_time"] = self.integ_time
        step["pre-acq-hooks"] = self.getHooks('pre-acq')
        step["post-acq-hooks"] = (self.getHooks('post-acq') +
                                  self.getHooks('_NOHINTS_'))
        step["post-step-hooks"] = self.getHooks('post-step')
        step["check_func"] = []
        step['extrainfo'] = {}
        point_no = 0
        while(True):
            point_no += 1
            step["point_id"] = point_no
            yield step

    def run(self, *args):
        for step in self._gScan.step_scan():
            yield step

    def getTimeEstimation(self):
        gScan = self._gScan
        mode = self.mode
        it = gScan.generator()
        v_motors = gScan.get_virtual_motors()
        curr_pos = gScan.motion.readPosition()
        total_time = 0.0
        if mode == StepMode:
            # calculate motion time
            max_step0_time, max_step_time = 0.0, 0.0
            # first motion takes longer, all others should be "equal"
            step0 = it.next()
            for v_motor, start, stop, length in zip(v_motors, curr_pos,
                                                    step0['positions'],
                                                    self.interv_sizes):
                path0 = MotionPath(v_motor, start, stop)
                path = MotionPath(v_motor, 0, length)
                max_step0_time = max(max_step0_time, path0.duration)
                max_step_time = max(max_step_time, path.duration)
            motion_time = max_step0_time + self.nr_interv * max_step_time
            # calculate acquisition time
            acq_time = self.nr_points * self.integ_time
            total_time = motion_time + acq_time

        elif mode == ContinuousMode:
            total_time = gScan.waypoint_estimation()
        # TODO: add time estimation for ContinuousHwTimeMode
        return total_time

    def getIntervalEstimation(self):
        mode = self.mode
        if mode in [StepMode, ContinuousHwTimeMode, HybridMode]:
            return self.nr_interv
        elif mode == ContinuousMode:
            return self.nr_waypoints

    def _fill_missing_records(self):
        # fill record list with dummy records for the final padding
        nb_of_points = self.nr_points
        scan = self._gScan
        nb_of_records = len(scan.data.records)
        missing_records = nb_of_points - nb_of_records
        scan.data.initRecords(missing_records)


class dNscan(aNscan):
    """
    same as aNscan but it interprets the positions as being relative to the
    current positions and upon completion, it returns the motors to their
    original positions
    """

    hints = copy.deepcopy(aNscan.hints)
    hints['scan'] = 'dNscan'

    def _prepare(self, motorlist, startlist, endlist, scan_length,
                 integ_time, mode=StepMode, **opts):
        self._motion = self.getMotion([m.getName() for m in motorlist])
        self.originalPositions = numpy.array(
            self._motion.readPosition(force=True))
        starts = numpy.array(startlist, dtype='d') + self.originalPositions
        finals = numpy.array(endlist, dtype='d') + self.originalPositions
        aNscan._prepare(self, motorlist, starts, finals,
                        scan_length, integ_time, mode=mode, **opts)

    def do_restore(self):
        self.info("Returning to start positions...")
        self._motion.move(self.originalPositions)


class ascan(aNscan, Macro):
    """
    Do an absolute scan of the specified motor.
    ascan scans one motor, as specified by motor. The motor starts at the
    position given by start_pos and ends at the position given by final_pos.
    The step size is (start_pos-final_pos)/nr_interv. The number of data
    points collected will be nr_interv+1. Count time is given by time which
    if positive, specifies seconds and if negative, specifies monitor counts.
    """

    param_def = [
        ['motor', Type.Moveable, None, 'Moveable to move'],
        ['start_pos', Type.Float, None, 'Scan start position'],
        ['final_pos', Type.Float, None, 'Scan final position'],
        ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float, None, 'Integration time']
    ]

    def prepare(self, motor, start_pos, final_pos, nr_interv, integ_time,
                **opts):
        self._prepare([motor], [start_pos], [final_pos],
                      nr_interv, integ_time, **opts)


class a2scan(aNscan, Macro):
    """two-motor scan.
    a2scan scans two motors, as specified by motor1 and motor2.
    Each motor moves the same number of intervals with starting and ending
    positions given by start_pos1 and final_pos1, start_pos2 and final_pos2,
    respectively. The step size for each motor is:
        (start_pos-final_pos)/nr_interv
    The number of data points collected will be nr_interv+1.
    Count time is given by time which if positive, specifies seconds and
    if negative, specifies monitor counts."""
    param_def = [
        ['motor1', Type.Moveable, None, 'Moveable 1 to move'],
        ['start_pos1', Type.Float, None, 'Scan start position 1'],
        ['final_pos1', Type.Float, None, 'Scan final position 1'],
        ['motor2', Type.Moveable, None, 'Moveable 2 to move'],
        ['start_pos2', Type.Float, None, 'Scan start position 2'],
        ['final_pos2', Type.Float, None, 'Scan final position 2'],
        ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float, None, 'Integration time']
    ]

    def prepare(self, motor1, start_pos1, final_pos1, motor2, start_pos2,
                final_pos2, nr_interv, integ_time, **opts):
        self._prepare([motor1, motor2], [start_pos1, start_pos2], [
                      final_pos1, final_pos2], nr_interv, integ_time, **opts)


class a3scan(aNscan, Macro):
    """three-motor scan .
    a3scan scans three motors, as specified by motor1, motor2 and motor3.
    Each motor moves the same number of intervals with starting and ending
    positions given by start_pos1 and final_pos1, start_pos2 and final_pos2,
    start_pos3 and final_pos3, respectively.
    The step size for each motor is (start_pos-final_pos)/nr_interv.
    The number of data points collected will be nr_interv+1.
    Count time is given by time which if positive, specifies seconds and
    if negative, specifies monitor counts."""
    param_def = [
        ['motor1', Type.Moveable, None, 'Moveable 1 to move'],
        ['start_pos1', Type.Float, None, 'Scan start position 1'],
        ['final_pos1', Type.Float, None, 'Scan final position 1'],
        ['motor2', Type.Moveable, None, 'Moveable 2 to move'],
        ['start_pos2', Type.Float, None, 'Scan start position 2'],
        ['final_pos2', Type.Float, None, 'Scan final position 2'],
        ['motor3', Type.Moveable, None, 'Moveable 3 to move'],
        ['start_pos3', Type.Float, None, 'Scan start position 3'],
        ['final_pos3', Type.Float, None, 'Scan final position 3'],
        ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float, None, 'Integration time']
    ]

    def prepare(self, m1, s1, f1, m2, s2, f2, m3, s3, f3, nr_interv,
                integ_time, **opts):
        self._prepare([m1, m2, m3], [s1, s2, s3], [f1, f2, f3],
                      nr_interv, integ_time, **opts)


class a4scan(aNscan, Macro):
    """four-motor scan .
    a4scan scans four motors, as specified by motor1, motor2, motor3 and
    motor4.
    Each motor moves the same number of intervals with starting and ending
    positions given by start_posN and final_posN (for N=1,2,3,4).
    The step size for each motor is (start_pos-final_pos)/nr_interv.
    The number of data points collected will be nr_interv+1.
    Count time is given by time which if positive, specifies seconds and
    if negative, specifies monitor counts."""
    param_def = [
        ['motor1', Type.Moveable, None, 'Moveable 1 to move'],
        ['start_pos1', Type.Float, None, 'Scan start position 1'],
        ['final_pos1', Type.Float, None, 'Scan final position 1'],
        ['motor2', Type.Moveable, None, 'Moveable 2 to move'],
        ['start_pos2', Type.Float, None, 'Scan start position 2'],
        ['final_pos2', Type.Float, None, 'Scan final position 2'],
        ['motor3', Type.Moveable, None, 'Moveable 3 to move'],
        ['start_pos3', Type.Float, None, 'Scan start position 3'],
        ['final_pos3', Type.Float, None, 'Scan final position 3'],
        ['motor4', Type.Moveable, None, 'Moveable 3 to move'],
        ['start_pos4', Type.Float, None, 'Scan start position 3'],
        ['final_pos4', Type.Float, None, 'Scan final position 3'],
        ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float, None, 'Integration time']
    ]

    def prepare(self, m1, s1, f1, m2, s2, f2, m3, s3, f3, m4, s4, f4,
                nr_interv, integ_time, **opts):
        self._prepare([m1, m2, m3, m4], [s1, s2, s3, s4], [
                      f1, f2, f3, f4], nr_interv, integ_time, **opts)


class amultiscan(aNscan, Macro):
    """
    Multiple motor scan.
    amultiscan scans N motors, as specified by motor1, motor2,...,motorN.
    Each motor moves the same number of intervals with starting and ending
    positions given by start_posN and final_posN (for N=1,2,...).
    The step size for each motor is (start_pos-final_pos)/nr_interv.
    The number of data points collected will be nr_interv+1.
    Count time is given by time which if positive, specifies seconds and
    if negative, specifies monitor counts.
    """

    param_def = [
        ['motor_start_end_list',
         ParamRepeat(['motor', Type.Moveable, None, 'Moveable to move'],
                     ['start', Type.Float, None, 'Starting position'],
                     ['end', Type.Float, None, 'Final position']),
         None, 'List of motor, start and end positions'],
        ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float, None, 'Integration time']
    ]

    def prepare(self, *args, **opts):
        motors = args[0:-2:3]
        starts = args[1:-2:3]
        ends = args[2:-2:3]
        nr_interv = args[-2]
        integ_time = args[-1]

        self._prepare(motors, starts, ends, nr_interv, integ_time, **opts)


class dmultiscan(dNscan, Macro):
    """
    Multiple motor scan relative to the starting positions.
    dmultiscan scans N motors, as specified by motor1, motor2,...,motorN.
    Each motor moves the same number of intervals If each motor is at a
    position X before the scan begins, it will be scanned from X+start_posN
    to X+final_posN (where N is one of 1,2,...)
    The step size for each motor is (start_pos-final_pos)/nr_interv.
    The number of data points collected will be nr_interv+1.
    Count time is given by time which if positive, specifies seconds and
    if negative, specifies monitor counts.
    """

    param_def = [
        ['motor_start_end_list',
         ParamRepeat(['motor', Type.Moveable, None, 'Moveable to move'],
                     ['start', Type.Float, None, 'Starting position'],
                     ['end', Type.Float, None, 'Final position']),
         None, 'List of motor, start and end positions'],
        ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float, None, 'Integration time']
    ]

    def prepare(self, *args, **opts):
        motors = args[0:-2:3]
        starts = args[1:-2:3]
        ends = args[2:-2:3]
        nr_interv = args[-2]
        integ_time = args[-1]

        self._prepare(motors, starts, ends, nr_interv, integ_time, **opts)


class dscan(dNscan, Macro):
    """motor scan relative to the starting position.
    dscan scans one motor, as specified by motor. If motor motor is at a
    position X before the scan begins, it will be scanned from X+start_pos
    to X+final_pos. The step size is (start_pos-final_pos)/nr_interv.
    The number of data points collected will be nr_interv+1. Count time is
    given by time which if positive, specifies seconds and if negative,
    specifies monitor counts. """

    param_def = [
        ['motor', Type.Moveable, None, 'Moveable to move'],
        ['start_pos', Type.Float, None, 'Scan start position'],
        ['final_pos', Type.Float, None, 'Scan final position'],
        ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float, None, 'Integration time']
    ]

    def prepare(self, motor, start_pos, final_pos, nr_interv, integ_time,
                **opts):
        self._prepare([motor], [start_pos], [final_pos],
                      nr_interv, integ_time, **opts)


class d2scan(dNscan, Macro):
    """two-motor scan relative to the starting position.
    d2scan scans two motors, as specified by motor1 and motor2.
    Each motor moves the same number of intervals. If each motor is at a
    position X before the scan begins, it will be scanned from X+start_posN
    to X+final_posN (where N is one of 1,2).
    The step size for each motor is (start_pos-final_pos)/nr_interv.
    The number of data points collected will be nr_interv+1.
    Count time is given by time which if positive, specifies seconds and
    if negative, specifies monitor counts."""
    param_def = [
        ['motor1', Type.Moveable, None, 'Moveable 1 to move'],
        ['start_pos1', Type.Float, None, 'Scan start position 1'],
        ['final_pos1', Type.Float, None, 'Scan final position 1'],
        ['motor2', Type.Moveable, None, 'Moveable 2 to move'],
        ['start_pos2', Type.Float, None, 'Scan start position 2'],
        ['final_pos2', Type.Float, None, 'Scan final position 2'],
        ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float, None, 'Integration time']
    ]

    def prepare(self, motor1, start_pos1, final_pos1, motor2, start_pos2,
                final_pos2, nr_interv, integ_time, **opts):
        self._prepare([motor1, motor2], [start_pos1, start_pos2], [
                      final_pos1, final_pos2], nr_interv, integ_time, **opts)


class d3scan(dNscan, Macro):
    """three-motor scan .
    d3scan scans three motors, as specified by motor1, motor2 and motor3.
    Each motor moves the same number of intervals. If each motor is at a
    position X before the scan begins, it will be scanned from X+start_posN
    to X+final_posN (where N is one of 1,2,3)
    The step size for each motor is (start_pos-final_pos)/nr_interv.
    The number of data points collected will be nr_interv+1.
    Count time is given by time which if positive, specifies seconds and
    if negative, specifies monitor counts."""

    param_def = [
        ['motor1', Type.Moveable, None, 'Moveable 1 to move'],
        ['start_pos1', Type.Float, None, 'Scan start position 1'],
        ['final_pos1', Type.Float, None, 'Scan final position 1'],
        ['motor2', Type.Moveable, None, 'Moveable 2 to move'],
        ['start_pos2', Type.Float, None, 'Scan start position 2'],
        ['final_pos2', Type.Float, None, 'Scan final position 2'],
        ['motor3', Type.Moveable, None, 'Moveable 3 to move'],
        ['start_pos3', Type.Float, None, 'Scan start position 3'],
        ['final_pos3', Type.Float, None, 'Scan final position 3'],
        ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float, None, 'Integration time']
    ]

    def prepare(self, m1, s1, f1, m2, s2, f2, m3, s3, f3, nr_interv,
                integ_time, **opts):
        self._prepare([m1, m2, m3], [s1, s2, s3], [f1, f2, f3],
                      nr_interv, integ_time, **opts)


class d4scan(dNscan, Macro):
    """four-motor scan relative to the starting positions
    a4scan scans four motors, as specified by motor1, motor2, motor3 and
    motor4.
    Each motor moves the same number of intervals. If each motor is at a
    position X before the scan begins, it will be scanned from X+start_posN
    to X+final_posN (where N is one of 1,2,3,4).
    The step size for each motor is (start_pos-final_pos)/nr_interv.
    The number of data points collected will be nr_interv+1.
    Count time is given by time which if positive, specifies seconds and
    if negative, specifies monitor counts.
    Upon termination, the motors are returned to their starting positions.
    """

    param_def = [
        ['motor1', Type.Moveable, None, 'Moveable 1 to move'],
        ['start_pos1', Type.Float, None, 'Scan start position 1'],
        ['final_pos1', Type.Float, None, 'Scan final position 1'],
        ['motor2', Type.Moveable, None, 'Moveable 2 to move'],
        ['start_pos2', Type.Float, None, 'Scan start position 2'],
        ['final_pos2', Type.Float, None, 'Scan final position 2'],
        ['motor3', Type.Moveable, None, 'Moveable 3 to move'],
        ['start_pos3', Type.Float, None, 'Scan start position 3'],
        ['final_pos3', Type.Float, None, 'Scan final position 3'],
        ['motor4', Type.Moveable, None, 'Moveable 3 to move'],
        ['start_pos4', Type.Float, None, 'Scan start position 3'],
        ['final_pos4', Type.Float, None, 'Scan final position 3'],
        ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float, None, 'Integration time']
    ]

    def prepare(self, m1, s1, f1, m2, s2, f2, m3, s3, f3, m4, s4, f4,
                nr_interv, integ_time, **opts):
        self._prepare([m1, m2, m3, m4], [s1, s2, s3, s4], [
                      f1, f2, f3, f4], nr_interv, integ_time, **opts)


class mesh(Macro, Hookable):
    """2d grid scan.
    The mesh scan traces out a grid using motor1 and motor2.
    The first motor scans from m1_start_pos to m1_final_pos using the specified
    number of intervals. The second motor similarly scans from m2_start_pos
    to m2_final_pos. Each point is counted for for integ_time seconds
    (or monitor counts, if integ_time is negative).
    The scan of motor1 is done at each point scanned by motor2. That is, the
    first motor scan is nested within the second motor scan.
    """

    hints = {'scan': 'mesh', 'allowsHooks': ('pre-scan', 'pre-move',
                                             'post-move', 'pre-acq',
                                             'post-acq', 'post-step',
                                             'post-scan')}
    env = ('ActiveMntGrp',)

    param_def = [
        ['motor1', Type.Moveable, None, 'First motor to move'],
        ['m1_start_pos', Type.Float, None, 'Scan start position for first '
                                           'motor'],
        ['m1_final_pos', Type.Float, None, 'Scan final position for first '
                                           'motor'],
        ['m1_nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['motor2', Type.Moveable, None, 'Second motor to move'],
        ['m2_start_pos', Type.Float, None, 'Scan start position for second '
                                           'motor'],
        ['m2_final_pos', Type.Float, None, 'Scan final position for second '
                                           'motor'],
        ['m2_nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['bidirectional', Type.Boolean, False, 'Save time by scanning '
                                               's-shaped']
    ]

    def prepare(self, m1, m1_start_pos, m1_final_pos, m1_nr_interv,
                m2, m2_start_pos, m2_final_pos, m2_nr_interv, integ_time,
                bidirectional, **opts):
        self.motors = [m1, m2]
        self.starts = numpy.array([m1_start_pos, m2_start_pos], dtype='d')
        self.finals = numpy.array([m1_final_pos, m2_final_pos], dtype='d')
        self.nr_intervs = numpy.array([m1_nr_interv, m2_nr_interv], dtype='i')
        self.integ_time = integ_time
        self.bidirectional_mode = bidirectional

        self.name = opts.get('name', 'mesh')

        generator = self._generator
        moveables = self.motors
        env = opts.get('env', {})
        constrains = [getCallable(cns) for cns in opts.get(
            'constrains', [UNCONSTRAINED])]

        # Hooks are not always set at this point. We will call getHooks
        # later on in the scan_loop
        # self.pre_scan_hooks = self.getHooks('pre-scan')
        # self.post_scan_hooks = self.getHooks('post-scan')

        self._gScan = SScan(self, generator, moveables, env, constrains)

        # _data is the default member where the Macro class stores the data.
        # Assign the date produced by GScan (or its subclasses) to it so all
        # the Macro infrastructure related to the data works e.g. getter,
        # property, etc.
        self.setData(self._gScan.data)

    def _generator(self):
        step = {}
        step["integ_time"] = self.integ_time
        step["pre-move-hooks"] = self.getHooks('pre-move')
        step["post-move-hooks"] = self.getHooks('post-move')
        step["pre-acq-hooks"] = self.getHooks('pre-acq')
        step["post-acq-hooks"] = (self.getHooks('post-acq') +
                                  self.getHooks('_NOHINTS_'))
        step["post-step-hooks"] = self.getHooks('post-step')
        step["check_func"] = []
        m1start, m2start = self.starts
        m1end, m2end = self.finals
        points1, points2 = self.nr_intervs + 1
        point_no = 1
        m1_space = numpy.linspace(m1start, m1end, points1)
        m1_space_inv = numpy.linspace(m1end, m1start, points1)

        for i, m2pos in enumerate(numpy.linspace(m2start, m2end, points2)):
            space = m1_space
            if i % 2 != 0 and self.bidirectional_mode:
                space = m1_space_inv
            for m1pos in space:
                step["positions"] = numpy.array([m1pos, m2pos])
                # TODO: maybe another ID would be better? (e.g. "(A,B)")
                step["point_id"] = point_no
                point_no += 1
                yield step

    def run(self, *args):
        for step in self._gScan.step_scan():
            yield step


class dmesh(mesh):
    """
    2d relative grid scan.
    The relative mesh scan traces out a grid using motor1 and motor2.
    If first motor is at the position X before the scan begins, it will
    be scanned from X+m1_start_pos to X+m1_final_pos using the specified
    m1_nr_interv number of intervals. If the second motor is
    at the position Y before the scan begins, it will be scanned
    from Y+m2_start_pos to Y+m2_final_pos using the specified m2_nr_interv
    number of intervals.
    Each point is counted for the integ_time seconds (or monitor counts,
    if integ_time is negative).
    The scan of motor1 is done at each point scanned by motor2. That is, the
    first motor scan is nested within the second motor scan.
    Upon scan completion, it returns the motors to their original positions.
    """

    hints = copy.deepcopy(mesh.hints)
    hints['scan'] = 'dmesh'

    env = copy.deepcopy(mesh.env)

    param_def = [
        ['motor1', Type.Moveable, None, 'First motor to move'],
        ['m1_start_pos', Type.Float, None, 'Scan start position for first '
                                           'motor'],
        ['m1_final_pos', Type.Float, None, 'Scan final position for first '
                                           'motor'],
        ['m1_nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['motor2', Type.Moveable, None, 'Second motor to move'],
        ['m2_start_pos', Type.Float, None, 'Scan start position for second '
                                           'motor'],
        ['m2_final_pos', Type.Float, None, 'Scan final position for second '
                                           'motor'],
        ['m2_nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['bidirectional', Type.Boolean, False, 'Save time by scanning '
                                               's-shaped']
    ]

    def prepare(self, m1, m1_start_pos, m1_final_pos, m1_nr_interv,
                m2, m2_start_pos, m2_final_pos, m2_nr_interv, integ_time,
                bidirectional, **opts):
        self._motion = self.getMotion([m1, m2])
        self.originalPositions = numpy.array(
            self._motion.readPosition(force=True))
        start1 = self.originalPositions[0] + m1_start_pos
        start2 = self.originalPositions[1] + m2_start_pos
        final1 = self.originalPositions[0] + m1_final_pos
        final2 = self.originalPositions[1] + m2_final_pos
        mesh.prepare(self, m1, start1, final1, m1_nr_interv,
                     m2, start2, final2, m2_nr_interv, integ_time,
                     bidirectional, **opts)

    def do_restore(self):
        self.info("Returning to start positions...")
        self._motion.move(self.originalPositions)


class fscan(Macro, Hookable):
    """
    N-dimensional scan along user defined paths.
    The motion path for each motor is defined through the evaluation of a
    user-supplied function that is evaluated as a function of the independent
    variables.
    -independent variables are supplied through the indepvar string.
    The syntax for indepvar is "x=expresion1,y=expresion2,..."
    -If no indep vars need to be defined, write "!" or "*" or "None"
    -motion path for motor is generated by evaluating the corresponding
    function 'func'
    -Count time is given by integ_time. If integ_time is a scalar, then
    the same integ_time is used for all points. If it evaluates as an array
    (with same length as the paths), fscan will assign a different integration
    time to each acquisition point.
    -If integ_time is positive, it specifies seconds and if negative, specifies
    monitor counts.

    IMPORTANT Notes:
    -no spaces are allowed in the indepvar string.
    -all funcs must evaluate to the same number of points

    EXAMPLE:
    fscan x=[1,3,5,7,9],y=arange(5) 0.1 motor1 x**2 motor2 sqrt(y*x+3)
    fscan x=[1,3,5,7,9],y=arange(5) [0.1,0.2,0.3,0.4,0.5] motor1 x**2 motor2
          sqrt(y*x+3)
    """

    # ['integ_time', Type.String,   None, 'Integration time']
    hints = {'scan': 'fscan',
             'allowsHooks': ('pre-scan', 'pre-move', 'post-move', 'pre-acq',
                             'post-acq', 'post-step', 'post-scan')}
    env = ('ActiveMntGrp',)

    param_def = [
        ['indepvars', Type.String, None, 'Independent Variables'],
        ['integ_time', Type.String, None, 'Integration time'],
        ['motor_funcs',
         ParamRepeat(['motor', Type.Moveable, None, 'motor'],
                     ['func', Type.String, None, 'curve defining path']),
         None, 'List of motor and path curves']
    ]

    def prepare(self, *args, **opts):
        if args[0].lower() in ["!", "*", "none", None]:
            indepvars = {}
        else:
            indepvars = SafeEvaluator({'dict': dict}).eval(
                'dict(%s)' % args[0])  # create a dict containing the indepvars

        self.motors = [item[0] for item in args[2]]
        self.funcstrings = [item[1] for item in args[2]]

        globals_lst = [dict(zip(indepvars, values))
                       for values in zip(*indepvars.values())]
        self.paths = [[SafeEvaluator(globals).eval(
            func) for globals in globals_lst] for func in self.funcstrings]

        self.integ_time = numpy.array(eval(args[1]), dtype='d')

        self.opts = opts
        if len(self.motors) == len(self.paths) > 0:
            self.N = len(self.motors)
        else:
            raise ValueError(
                'Moveable and func lists must be non-empty and same length')
        npoints = len(self.paths[0])
        try:
            # if everything is OK, the following lines should return a 2D array
            # n which each motor path is a row.
            # Typical failure is due to shape mismatch due to inconsistent
            # input
            self.paths = numpy.array(self.paths, dtype='d')
            self.paths.reshape((self.N, npoints))
        except Exception:  # shape mismatch?
            # try to give a meaningful description of the error
            for p, fs in zip(self.paths, self.funcstrings):
                if len(p) != npoints:
                    raise ValueError('"%s" and "%s" yield different number '
                                     'of points (%i vs %i)' %
                                     (self.funcstrings[0], fs, npoints,
                                      len(p)))
            raise  # the problem wasn't a shape mismatch
        self.nr_points = npoints

        if self.integ_time.size == 1:
            self.integ_time = self.integ_time * \
                numpy.ones(self.nr_points)  # extend integ_time
        elif self.integ_time.size != self.nr_points:
            raise ValueError('time_integ must either be a scalar or '
                             'length=npoints (%i)' % self.nr_points)

        self.name = opts.get('name', 'fscan')

        generator = self._generator
        moveables = self.motors
        env = opts.get('env', {})
        constrains = [getCallable(cns) for cns in opts.get(
            'constrains', [UNCONSTRAINED])]

        # Hooks are not always set at this point. We will call getHooks
        # later on in the scan_loop
        # self.pre_scan_hooks = self.getHooks('pre-scan')
        # self.post_scan_hooks = self.getHooks('post-scan'

        self._gScan = SScan(self, generator, moveables, env, constrains)

        # _data is the default member where the Macro class stores the data.
        # Assign the date produced by GScan (or its subclasses) to it so all
        # the Macro infrastructure related to the data works e.g. getter,
        # property, etc.
        self.setData(self._gScan.data)

    def _generator(self):
        step = {}
        step["pre-move-hooks"] = self.getHooks('pre-move')
        step["post-move-hooks"] = self.getHooks('post-move')
        step["pre-acq-hooks"] = self.getHooks('pre-acq')
        step["post-acq-hooks"] = (self.getHooks('post-acq') +
                                  self.getHooks('_NOHINTS_'))
        step["post-step-hooks"] = self.getHooks('post-step')

        step["check_func"] = []
        for i in xrange(self.nr_points):
            step["positions"] = self.paths[:, i]
            step["integ_time"] = self.integ_time[i]
            step["point_id"] = i
            yield step

    def run(self, *args):
        for step in self._gScan.step_scan():
            yield step


class ascanh(aNscan, Macro):
    """Do an absolute scan of the specified motor.
    ascan scans one motor, as specified by motor. The motor starts at the
    position given by start_pos and ends at the position given by final_pos.
    The step size is (start_pos-final_pos)/nr_interv. The number of data
    points collected will be nr_interv+1. Count time is given by time which
    if positive, specifies seconds and if negative, specifies monitor
    counts. """

    param_def = [
        ['motor', Type.Moveable, None, 'Moveable to move'],
        ['start_pos', Type.Float, None, 'Scan start position'],
        ['final_pos', Type.Float, None, 'Scan final position'],
        ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float, None, 'Integration time']
    ]

    def prepare(self, motor, start_pos, final_pos, nr_interv, integ_time,
                **opts):
        self._prepare([motor], [start_pos], [final_pos], nr_interv, integ_time,
                      mode=HybridMode, **opts)


class scanhist(Macro):
    """Shows scan history information. Give optional parameter scan number to
    display details about a specific scan"""

    param_def = [
        ['scan number', Type.Integer, -1,
         'scan number. [default=-1 meaning show all scans]'],
    ]

    def run(self, scan_number):
        try:
            hist = self.getEnv("ScanHistory")
        except UnknownEnv:
            print "No scan recorded in history"
            return
        if scan_number < 0:
            self.show_all(hist)
        else:
            self.show_one(hist, scan_number)

    def show_one(self, hist, scan_number):
        item = None
        for h in hist:
            if h['serialno'] == scan_number:
                item = h
                break
        if item is None:
            self.warning("Could not find scan number %s", scan_number)
            return

        serialno, title = h['serialno'], h['title']
        start = datetime.datetime.fromtimestamp(h['startts'])
        end = datetime.datetime.fromtimestamp(h['endts'])
        total_time = end - start
        start, end, total_time = start.ctime(), end.ctime(), str(total_time)
        scan_dir, scan_file = h['ScanDir'], h['ScanFile']
        deadtime = '%.1f%%' % h['deadtime']

        user = h['user']
        store = "Not stored!"
        if scan_dir is not None and scan_file is not None:
            if isinstance(scan_file, str):
                store = os.path.join(scan_dir, scan_file)
            else:
                store = scan_dir + os.path.sep + str(scan_file)

        channels = ", ".join(h['channels'])
        cols = ["#", "Title", "Start time", "End time", "Took", "Dead time",
                "User", "Stored", "Channels"]
        data = [serialno, title, start, end, total_time, deadtime, user, store,
                channels]

        table = Table([data], row_head_str=cols, row_head_fmt='%*s',
                      elem_fmt=['%-*s'],
                      col_sep='  :  ')
        for line in table.genOutput():
            self.output(line)

    def show_all(self, hist):

        cols = "#", "Title", "Start time", "End time", "Stored"
        width = -1, -1, -1, -1, -1
        out = List(cols, max_col_width=width)
        today = datetime.datetime.today().date()
        for h in hist:
            start = datetime.datetime.fromtimestamp(h['startts'])
            if start.date() == today:
                start = start.time().strftime("%H:%M:%S")
            else:
                start = start.strftime("%Y-%m-%d %H:%M:%S")
            end = datetime.datetime.fromtimestamp(h['endts'])
            if end.date() == today:
                end = end.time().strftime("%H:%M:%S")
            else:
                end = end.strftime("%Y-%m-%d %H:%M:%S")
            scan_file = h['ScanFile']
            store = "Not stored!"
            if scan_file is not None:
                store = ", ".join(scan_file)
            row = h['serialno'], h['title'], start, end, store
            out.appendRow(row)
        for line in out.genOutput():
            self.output(line)


class ascanc(aNscan, Macro):
    """Do an absolute continuous scan of the specified motor.
    ascanc scans one motor, as specified by motor."""

    param_def = [
        ['motor', Type.Moveable, None, 'Moveable to move'],
        ['start_pos', Type.Float, None, 'Scan start position'],
        ['final_pos', Type.Float, None, 'Scan final position'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['slow_down', Type.Float, 1, 'global scan slow down factor (0, 1]'],
    ]

    def prepare(self, motor, start_pos, final_pos, integ_time, slow_down,
                **opts):
        self._prepare([motor], [start_pos], [final_pos], slow_down,
                      integ_time, mode=ContinuousMode, **opts)


class a2scanc(aNscan, Macro):
    """two-motor continuous scan"""
    param_def = [
        ['motor1', Type.Moveable, None, 'Moveable 1 to move'],
        ['start_pos1', Type.Float, None, 'Scan start position 1'],
        ['final_pos1', Type.Float, None, 'Scan final position 1'],
        ['motor2', Type.Moveable, None, 'Moveable 2 to move'],
        ['start_pos2', Type.Float, None, 'Scan start position 2'],
        ['final_pos2', Type.Float, None, 'Scan final position 2'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['slow_down', Type.Float, 1, 'global scan slow down factor (0, 1]'],
    ]

    def prepare(self, motor1, start_pos1, final_pos1, motor2, start_pos2,
                final_pos2, integ_time, slow_down, **opts):
        self._prepare([motor1, motor2], [start_pos1, start_pos2],
                      [final_pos1, final_pos2], slow_down, integ_time,
                      mode=ContinuousMode, **opts)


class a3scanc(aNscan, Macro):
    """three-motor continuous scan"""
    param_def = [
        ['motor1', Type.Moveable, None, 'Moveable 1 to move'],
        ['start_pos1', Type.Float, None, 'Scan start position 1'],
        ['final_pos1', Type.Float, None, 'Scan final position 1'],
        ['motor2', Type.Moveable, None, 'Moveable 2 to move'],
        ['start_pos2', Type.Float, None, 'Scan start position 2'],
        ['final_pos2', Type.Float, None, 'Scan final position 2'],
        ['motor3', Type.Moveable, None, 'Moveable 3 to move'],
        ['start_pos3', Type.Float, None, 'Scan start position 3'],
        ['final_pos3', Type.Float, None, 'Scan final position 3'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['slow_down', Type.Float, 1, 'global scan slow down factor (0, 1]'],
    ]

    def prepare(self, m1, s1, f1, m2, s2, f2, m3, s3, f3, integ_time,
                slow_down, **opts):
        self._prepare([m1, m2, m3], [s1, s2, s3], [f1, f2, f3], slow_down,
                      integ_time, mode=ContinuousMode, **opts)


class a4scanc(aNscan, Macro):
    """four-motor continuous scan"""
    param_def = [
        ['motor1', Type.Moveable, None, 'Moveable 1 to move'],
        ['start_pos1', Type.Float, None, 'Scan start position 1'],
        ['final_pos1', Type.Float, None, 'Scan final position 1'],
        ['motor2', Type.Moveable, None, 'Moveable 2 to move'],
        ['start_pos2', Type.Float, None, 'Scan start position 2'],
        ['final_pos2', Type.Float, None, 'Scan final position 2'],
        ['motor3', Type.Moveable, None, 'Moveable 3 to move'],
        ['start_pos3', Type.Float, None, 'Scan start position 3'],
        ['final_pos3', Type.Float, None, 'Scan final position 3'],
        ['motor4', Type.Moveable, None, 'Moveable 3 to move'],
        ['start_pos4', Type.Float, None, 'Scan start position 3'],
        ['final_pos4', Type.Float, None, 'Scan final position 3'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['slow_down', Type.Float, 1, 'global scan slow down factor (0, 1]'],
    ]

    def prepare(self, m1, s1, f1, m2, s2, f2, m3, s3, f3, m4, s4, f4,
                integ_time, slow_down, **opts):
        self._prepare([m1, m2, m3, m4], [s1, s2, s3, s4], [f1, f2, f3, f4],
                      slow_down, integ_time, mode=ContinuousMode, **opts)


class dNscanc(dNscan):

    def do_restore(self):
        # set velocities to maximum and then move to initial positions
        for moveable in self.motors:
            self._gScan.set_max_top_velocity(moveable)
        dNscan.do_restore(self)


class dscanc(dNscanc, Macro):
    """continuous motor scan relative to the starting position."""

    param_def = [
        ['motor', Type.Moveable, None, 'Moveable to move'],
        ['start_pos', Type.Float, None, 'Scan start position'],
        ['final_pos', Type.Float, None, 'Scan final position'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['slow_down', Type.Float, 1, 'global scan slow down factor (0, 1]'],
    ]

    def prepare(self, motor, start_pos, final_pos, integ_time, slow_down,
                **opts):
        self._prepare([motor], [start_pos], [final_pos], slow_down, integ_time,
                      mode=ContinuousMode, **opts)


class d2scanc(dNscanc, Macro):
    """continuous two-motor scan relative to the starting positions"""

    param_def = [
        ['motor1', Type.Moveable, None, 'Moveable 1 to move'],
        ['start_pos1', Type.Float, None, 'Scan start position 1'],
        ['final_pos1', Type.Float, None, 'Scan final position 1'],
        ['motor2', Type.Moveable, None, 'Moveable 2 to move'],
        ['start_pos2', Type.Float, None, 'Scan start position 2'],
        ['final_pos2', Type.Float, None, 'Scan final position 2'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['slow_down', Type.Float, 1, 'global scan slow down factor (0, 1]'],
    ]

    def prepare(self, motor1, start_pos1, final_pos1, motor2, start_pos2,
                final_pos2, integ_time, slow_down, **opts):
        self._prepare([motor1, motor2], [start_pos1, start_pos2],
                      [final_pos1, final_pos2], slow_down, integ_time,
                      mode=ContinuousMode, **opts)


class d3scanc(dNscanc, Macro):
    """continuous three-motor scan"""
    param_def = [
        ['motor1', Type.Moveable, None, 'Moveable 1 to move'],
        ['start_pos1', Type.Float, None, 'Scan start position 1'],
        ['final_pos1', Type.Float, None, 'Scan final position 1'],
        ['motor2', Type.Moveable, None, 'Moveable 2 to move'],
        ['start_pos2', Type.Float, None, 'Scan start position 2'],
        ['final_pos2', Type.Float, None, 'Scan final position 2'],
        ['motor3', Type.Moveable, None, 'Moveable 3 to move'],
        ['start_pos3', Type.Float, None, 'Scan start position 3'],
        ['final_pos3', Type.Float, None, 'Scan final position 3'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['slow_down', Type.Float, 1, 'global scan slow down factor (0, 1]'],
    ]

    def prepare(self, m1, s1, f1, m2, s2, f2, m3, s3, f3, integ_time,
                slow_down, **opts):
        self._prepare([m1, m2, m3], [s1, s2, s3], [f1, f2, f3], slow_down,
                      integ_time, mode=ContinuousMode, **opts)


class d4scanc(dNscanc, Macro):
    """continuous four-motor scan relative to the starting positions"""
    param_def = [
        ['motor1', Type.Moveable, None, 'Moveable 1 to move'],
        ['start_pos1', Type.Float, None, 'Scan start position 1'],
        ['final_pos1', Type.Float, None, 'Scan final position 1'],
        ['motor2', Type.Moveable, None, 'Moveable 2 to move'],
        ['start_pos2', Type.Float, None, 'Scan start position 2'],
        ['final_pos2', Type.Float, None, 'Scan final position 2'],
        ['motor3', Type.Moveable, None, 'Moveable 3 to move'],
        ['start_pos3', Type.Float, None, 'Scan start position 3'],
        ['final_pos3', Type.Float, None, 'Scan final position 3'],
        ['motor4', Type.Moveable, None, 'Moveable 3 to move'],
        ['start_pos4', Type.Float, None, 'Scan start position 3'],
        ['final_pos4', Type.Float, None, 'Scan final position 3'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['slow_down', Type.Float, 1, 'global scan slow down factor (0, 1]'],
    ]

    def prepare(self, m1, s1, f1, m2, s2, f2, m3, s3, f3, m4, s4, f4,
                integ_time, slow_down, **opts):
        self._prepare([m1, m2, m3, m4], [s1, s2, s3, s4], [f1, f2, f3, f4],
                      slow_down, integ_time, mode=ContinuousMode, **opts)


class meshc(Macro, Hookable):
    """2d grid scan. scans continuous"""

    hints = {'scan': 'mesh', 'allowsHooks': ('pre-scan', 'pre-move',
                                             'post-move', 'pre-acq',
                                             'post-acq', 'post-step',
                                             'post-scan')}
    env = ('ActiveMntGrp',)

    param_def = [
        ['motor1', Type.Moveable, None, 'First motor to move'],
        ['m1_start_pos', Type.Float, None, 'Scan start position for first '
                                           'motor'],
        ['m1_final_pos', Type.Float, None, 'Scan final position for first '
                                           'motor'],
        ['slow_down', Type.Float, None, 'global scan slow down factor (0, 1]'],
        ['motor2', Type.Moveable, None, 'Second motor to move'],
        ['m2_start_pos', Type.Float, None, 'Scan start position for second '
                                           'motor'],
        ['m2_final_pos', Type.Float, None, 'Scan final position for second '
                                           'motor'],
        ['m2_nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['bidirectional', Type.Boolean, False, 'Save time by scanning '
                                               's-shaped']
    ]

    def prepare(self, m1, m1_start_pos, m1_final_pos, slow_down,
                m2, m2_start_pos, m2_final_pos, m2_nr_interv, integ_time,
                bidirectional, **opts):
        self.motors = [m1, m2]
        self.slow_down = slow_down
        self.starts = numpy.array([m1_start_pos, m2_start_pos], dtype='d')
        self.finals = numpy.array([m1_final_pos, m2_final_pos], dtype='d')
        self.m2_nr_interv = m2_nr_interv
        self.integ_time = integ_time
        self.bidirectional_mode = bidirectional
        self.nr_waypoints = m2_nr_interv + 1

        self.name = opts.get('name', 'meshc')

        moveables = []
        for m, start, final in zip(self.motors, self.starts, self.finals):
            moveables.append(MoveableDesc(moveable=m, min_value=min(
                start, final), max_value=max(start, final)))
        moveables[0].is_reference = True

        env = opts.get('env', {})
        constrains = [getCallable(cns) for cns in opts.get(
            'constrains', [UNCONSTRAINED])]
        extrainfodesc = opts.get('extrainfodesc', [])

        # Hooks are not always set at this point. We will call getHooks
        # later on in the scan_loop
        # self.pre_scan_hooks = self.getHooks('pre-scan')
        # self.post_scan_hooks = self.getHooks('post-scan'

        self._gScan = CSScan(self, self._waypoint_generator,
                             self._period_generator, moveables, env,
                             constrains, extrainfodesc)
        self._gScan.frozen_motors = [m2]

        # _data is the default member where the Macro class stores the data.
        # Assign the date produced by GScan (or its subclasses) to it so all
        # the Macro infrastructure related to the data works e.g. getter,
        # property, etc.
        self.setData(self._gScan.data)

    def _waypoint_generator(self):
        step = {}
        step["pre-move-hooks"] = self.getHooks('pre-move')
        step["post-move-hooks"] = self.getHooks('post-move')
        step["check_func"] = []
        step["slow_down"] = self.slow_down
        points2 = self.m2_nr_interv + 1
        m1start, m2start = self.starts
        m1end, m2end = self.finals
        point_no = 1
        for i, m2pos in enumerate(numpy.linspace(m2start, m2end, points2)):
            start, end = m1start, m1end
            if i % 2 != 0 and self.bidirectional_mode:
                start, end = m1end, m1start
            step["start_positions"] = numpy.array([start, m2pos])
            step["positions"] = numpy.array([end, m2pos])
            step["point_id"] = point_no
            point_no += 1
            yield step

    def _period_generator(self):
        step = {}
        step["integ_time"] = self.integ_time
        step["pre-acq-hooks"] = self.getHooks('pre-acq')
        step["post-acq-hooks"] = (self.getHooks('post-acq') +
                                  self.getHooks('_NOHINTS_'))
        step["post-step-hooks"] = self.getHooks('post-step')
        step["check_func"] = []
        step['extrainfo'] = {}
        point_no = 0
        while(True):
            point_no += 1
            step["point_id"] = point_no
            yield step

    def run(self, *args):
        for step in self._gScan.step_scan():
            yield step

    def getTimeEstimation(self):
        return self._gScan.waypoint_estimation()

    def getIntervalEstimation(self):
        return self.nr_waypoints


class dmeshc(meshc):
    """2d relative continuous grid scan.
    The relative mesh scan traces out a grid using motor1 and motor2.
    If first motor is at the position X before the scan begins, it will
    be continuously scanned from X+m1_start_pos to X+m1_final_pos.
    If the second motor is at the position Y before the scan begins,
    it will be discrete scanned from Y+m2_start_pos to Y+m2_final_pos
    using the specified m2_nr_interv number of intervals.
    The scan considers the accel. and decel. times of the motor1, so the
    counts (for the integ_time seconds or monitor counts,
    if integ_time is negative) are executed while motor1 is moving
    with the constant velocity.
    Upon scan completion, it returns the motors to their original positions.
    """

    hints = copy.deepcopy(meshc.hints)
    hints['scan'] = 'dmeshc'

    env = copy.deepcopy(meshc.env)

    param_def = [
        ['motor1', Type.Moveable, None, 'First motor to move'],
        ['m1_start_pos', Type.Float, None, 'Scan start position for first '
                                           'motor'],
        ['m1_final_pos', Type.Float, None, 'Scan final position for first '
                                           'motor'],
        ['slow_down', Type.Float, None, 'global scan slow down factor (0, 1]'],
        ['motor2', Type.Moveable, None, 'Second motor to move'],
        ['m2_start_pos', Type.Float, None, 'Scan start position for second '
                                           'motor'],
        ['m2_final_pos', Type.Float, None, 'Scan final position for second '
                                           'motor'],
        ['m2_nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['bidirectional', Type.Boolean, False, 'Save time by scanning '
                                               's-shaped']
    ]

    def prepare(self, m1, m1_start_pos, m1_final_pos, slow_down,
                m2, m2_start_pos, m2_final_pos, m2_nr_interv, integ_time,
                bidirectional, **opts):
        self._motion = self.getMotion([m1, m2])
        self.originalPositions = numpy.array(
            self._motion.readPosition(force=True))
        start1 = self.originalPositions[0] + m1_start_pos
        start2 = self.originalPositions[1] + m2_start_pos
        final1 = self.originalPositions[0] + m1_final_pos
        final2 = self.originalPositions[1] + m2_final_pos
        meshc.prepare(self, m1, start1, final1, slow_down,
                      m2, start2, final2, m2_nr_interv, integ_time,
                      bidirectional, **opts)

    def do_restore(self):
        self.info("Returning to start positions...")
        self._motion.move(self.originalPositions)


class ascanct(aNscan, Macro):
    """Do an absolute continuous scan of the specified motor.
    ascanct scans one motor, as specified by motor. The motor starts before the
    position given by start_pos in order to reach the constant velocity at the
    start_pos and finishes at the position after the final_pos in order to
    maintain the constant velocity until the final_pos."""

    hints = {'scan': 'ascanct', 'allowsHooks': ('pre-configuration',
                                                'post-configuration',
                                                'pre-start',
                                                'pre-cleanup',
                                                'post-cleanup')}

    param_def = [['motor', Type.Moveable, None, 'Moveable name'],
                 ['start_pos', Type.Float, None, 'Scan start position'],
                 ['final_pos', Type.Float, None, 'Scan final position'],
                 ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
                 ['integ_time', Type.Float, None, 'Integration time'],
                 ['latency_time', Type.Float, 0, 'Latency time']]

    def prepare(self, motor, start_pos, final_pos, nr_interv,
                integ_time, latency_time, **opts):
        self._prepare([motor], [start_pos], [final_pos], nr_interv,
                      integ_time, mode=ContinuousHwTimeMode,
                      latency_time=latency_time, **opts)


class a2scanct(aNscan, Macro):
    """Two-motor continuous scan.
    a2scanct scans two motors, as specified by motor1 and motor2. Each motor
    starts before the position given by its start_pos in order to reach the
    constant velocity at its start_pos and finishes at the position after
    its final_pos in order to maintain the constant velocity until its
    final_pos."""

    hints = {'scan': 'a2scanct', 'allowsHooks': ('pre-configuration',
                                                 'post-configuration',
                                                 'pre-start',
                                                 'pre-cleanup',
                                                 'post-cleanup')}

    param_def = [
        ['motor1', Type.Moveable, None, 'Moveable 1 to move'],
        ['start_pos1', Type.Float, None, 'Scan start position 1'],
        ['final_pos1', Type.Float, None, 'Scan final position 1'],
        ['motor2', Type.Moveable, None, 'Moveable 2 to move'],
        ['start_pos2', Type.Float, None, 'Scan start position 2'],
        ['final_pos2', Type.Float, None, 'Scan final position 2'],
        ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['latency_time', Type.Float, 0, 'Latency time']]

    def prepare(self, m1, s1, f1, m2, s2, f2, nr_interv,
                integ_time, latency_time, **opts):
        self._prepare([m1, m2], [s1, s2], [f1, f2], nr_interv,
                      integ_time, mode=ContinuousHwTimeMode,
                      latency_time=latency_time, **opts)


class a3scanct(aNscan, Macro):
    """Three-motor continuous scan.
    a2scanct scans three motors, as specified by motor1, motor2 and motor3.
    Each motor starts before the position given by its start_pos in order to
    reach the constant velocity at its start_pos and finishes at the position
    after its final_pos in order to maintain the constant velocity until its
    final_pos."""

    hints = {'scan': 'a2scanct', 'allowsHooks': ('pre-configuration',
                                                 'post-configuration',
                                                 'pre-start',
                                                 'pre-cleanup',
                                                 'post-cleanup')}

    param_def = [
        ['motor1', Type.Moveable, None, 'Moveable 1 to move'],
        ['start_pos1', Type.Float, None, 'Scan start position 1'],
        ['final_pos1', Type.Float, None, 'Scan final position 1'],
        ['motor2', Type.Moveable, None, 'Moveable 2 to move'],
        ['start_pos2', Type.Float, None, 'Scan start position 2'],
        ['final_pos2', Type.Float, None, 'Scan final position 2'],
        ['motor3', Type.Moveable, None, 'Moveable 3 to move'],
        ['start_pos3', Type.Float, None, 'Scan start position 3'],
        ['final_pos3', Type.Float, None, 'Scan final position 3'],
        ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['latency_time', Type.Float, 0, 'Latency time']]

    def prepare(self, m1, s1, f1, m2, s2, f2, m3, s3, f3, nr_interv,
                integ_time, latency_time, **opts):
        self._prepare([m1, m2, m3], [s1, s2, s3], [f1, f2, f3], nr_interv,
                      integ_time, mode=ContinuousHwTimeMode,
                      latency_time=latency_time, **opts)


class a4scanct(aNscan, Macro):
    """Four-motor continuous scan.
    a2scanct scans four motors, as specified by motor1, motor2, motor3 and
    motor4. Each motor starts before the position given by its start_pos in
    order to reach the constant velocity at its start_pos and finishes at the
    position after its final_pos in order to maintain the constant velocity
    until its final_pos."""

    hints = {'scan': 'a2scanct', 'allowsHooks': ('pre-configuration',
                                                 'post-configuration',
                                                 'pre-start',
                                                 'pre-cleanup',
                                                 'post-cleanup')}

    param_def = [
        ['motor1', Type.Moveable, None, 'Moveable 1 to move'],
        ['start_pos1', Type.Float, None, 'Scan start position 1'],
        ['final_pos1', Type.Float, None, 'Scan final position 1'],
        ['motor2', Type.Moveable, None, 'Moveable 2 to move'],
        ['start_pos2', Type.Float, None, 'Scan start position 2'],
        ['final_pos2', Type.Float, None, 'Scan final position 2'],
        ['motor3', Type.Moveable, None, 'Moveable 3 to move'],
        ['start_pos3', Type.Float, None, 'Scan start position 3'],
        ['final_pos3', Type.Float, None, 'Scan final position 3'],
        ['motor4', Type.Moveable, None, 'Moveable 4 to move'],
        ['start_pos4', Type.Float, None, 'Scan start position 4'],
        ['final_pos4', Type.Float, None, 'Scan final position 4'],
        ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['latency_time', Type.Float, 0, 'Latency time']]

    def prepare(self, m1, s1, f1, m2, s2, f2, m3, s3, f3, m4, s4, f4,
                nr_interv, integ_time, latency_time, **opts):
        self._prepare([m1, m2, m3, m4], [s1, s2, s3, s4], [f1, f2, f3, f4],
                      nr_interv, integ_time, mode=ContinuousHwTimeMode,
                      latency_time=latency_time, **opts)


class dscanct(dNscan, Macro):
    """Do an a relative continuous motor scan,
    dscanct scans a motor, as specified by motor1.
    The Motor starts before the position given by its start_pos in order to
    reach the constant velocity at its start_pos and finishes at the position
    after its final_pos in order to maintain the constant velocity until its
    final_pos."""

    param_def = [['motor', Type.Moveable, None, 'Moveable name'],
                 ['start_pos', Type.Float, None, 'Scan start position'],
                 ['final_pos', Type.Float, None, 'Scan final position'],
                 ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
                 ['integ_time', Type.Float, None, 'Integration time'],
                 ['latency_time', Type.Float, 0, 'Latency time']]

    def prepare(self, motor, start_pos, final_pos, nr_interv,
                integ_time, latency_time, **opts):
        self._prepare([motor], [start_pos], [final_pos], nr_interv,
                      integ_time, mode=ContinuousHwTimeMode,
                      latency_time=latency_time, **opts)


class d2scanct(dNscan, Macro):
    """continuous two-motor scan relative to the starting positions,
    d2scanct scans three motors, as specified by motor1 and motor2.
    Each motor starts before the position given by its start_pos in order to
    reach the constant velocity at its start_pos and finishes at the position
    after its final_pos in order to maintain the constant velocity until its
    final_pos.
    """
    param_def = [
        ['motor1', Type.Moveable, None, 'Moveable 1 to move'],
        ['start_pos1', Type.Float, None, 'Scan start position 1'],
        ['final_pos1', Type.Float, None, 'Scan final position 1'],
        ['motor2', Type.Moveable, None, 'Moveable 2 to move'],
        ['start_pos2', Type.Float, None, 'Scan start position 2'],
        ['final_pos2', Type.Float, None, 'Scan final position 2'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['slow_down', Type.Float, 1, 'global scan slow down factor (0, 1]'],
    ]

    def prepare(self, m1, s1, f1, m2, s2, f2, integ_time, slow_down, **opts):
        self._prepare([m1, m2], [s1, s2], [f1, f2], slow_down, integ_time,
                      mode=ContinuousHwTimeMode, **opts)


class d3scanct(dNscan, Macro):
    """continuous three-motor scan relative to the starting positions,
    d3scanct scans three motors, as specified by motor1, motor2 and motor3.
    Each motor starts before the position given by its start_pos in order to
    reach the constant velocity at its start_pos and finishes at the position
    after its final_pos in order to maintain the constant velocity until its
    final_pos.
    """
    param_def = [
        ['motor1', Type.Moveable, None, 'Moveable 1 to move'],
        ['start_pos1', Type.Float, None, 'Scan start position 1'],
        ['final_pos1', Type.Float, None, 'Scan final position 1'],
        ['motor2', Type.Moveable, None, 'Moveable 2 to move'],
        ['start_pos2', Type.Float, None, 'Scan start position 2'],
        ['final_pos2', Type.Float, None, 'Scan final position 2'],
        ['motor3', Type.Moveable, None, 'Moveable 3 to move'],
        ['start_pos3', Type.Float, None, 'Scan start position 3'],
        ['final_pos3', Type.Float, None, 'Scan final position 3'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['slow_down', Type.Float, 1, 'global scan slow down factor (0, 1]'],
    ]

    def prepare(self, m1, s1, f1, m2, s2, f2, m3, s3, f3, integ_time,
                slow_down, **opts):
        self._prepare([m1, m2, m3], [s1, s2, s3], [f1, f2, f3], slow_down,
                      integ_time, mode=ContinuousHwTimeMode, **opts)


class d4scanct(dNscan, Macro):
    """continuous four-motor scan relative to the starting positions,
    d4scanct scans three motors, as specified by motor1, motor2, motor3 and
    motor4.
    Each motor starts before the position given by its start_pos in order to
    reach the constant velocity at its start_pos and finishes at the position
    after its final_pos in order to maintain the constant velocity until its
    final_pos."""
    param_def = [
        ['motor1', Type.Moveable, None, 'Moveable 1 to move'],
        ['start_pos1', Type.Float, None, 'Scan start position 1'],
        ['final_pos1', Type.Float, None, 'Scan final position 1'],
        ['motor2', Type.Moveable, None, 'Moveable 2 to move'],
        ['start_pos2', Type.Float, None, 'Scan start position 2'],
        ['final_pos2', Type.Float, None, 'Scan final position 2'],
        ['motor3', Type.Moveable, None, 'Moveable 3 to move'],
        ['start_pos3', Type.Float, None, 'Scan start position 3'],
        ['final_pos3', Type.Float, None, 'Scan final position 3'],
        ['motor4', Type.Moveable, None, 'Moveable 3 to move'],
        ['start_pos4', Type.Float, None, 'Scan start position 3'],
        ['final_pos4', Type.Float, None, 'Scan final position 3'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['slow_down', Type.Float, 1, 'global scan slow down factor (0, 1]'],
    ]

    def prepare(self, m1, s1, f1, m2, s2, f2, m3, s3, f3, m4, s4, f4,
                integ_time, slow_down, **opts):
        self._prepare([m1, m2, m3, m4], [s1, s2, s3, s4], [f1, f2, f3, f4],
                      slow_down, integ_time, mode=ContinuousHwTimeMode, **opts)


class meshct(Macro, Hookable):
    """2d grid scan  .
    The mesh scan traces out a grid using motor1 and motor2.
    The first motor scans  in contiuous mode from m1_start_pos to m1_final_pos
    using the specified number of intervals. The second motor similarly
    scans from m2_start_pos to m2_final_pos but it does not move during the
    continuous scan. Each point is counted for integ_time seconds
    (or monitor counts, if integ_time is negative).
    The scan of motor1 is done at each point scanned by motor2. That is, the
    first motor scan is nested within the second motor scan.
    """

    hints = {'scan': 'meshct', 'allowsHooks': ('pre-scan', 'pre-move',
                                               'post-move', 'pre-acq',
                                               'post-acq', 'post-step',
                                               'post-scan')}
    env = ('ActiveMntGrp',)

    param_def = [
        ['motor1', Type.Moveable, None, 'First motor to move'],
        ['m1_start_pos', Type.Float, None, 'Scan start position for first '
                                           'motor'],
        ['m1_final_pos', Type.Float, None, 'Scan final position for first '
                                           'motor'],
        ['m1_nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['motor2', Type.Moveable, None, 'Second motor to move'],
        ['m2_start_pos', Type.Float, None, 'Scan start position for second '
                                           'motor'],
        ['m2_final_pos', Type.Float, None, 'Scan final position for second '
                                           'motor'],
        ['m2_nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['bidirectional', Type.Boolean, False, 'Save time by scanning '
                                               's-shaped'],
        ['latency_time', Type.Float, 0, 'Latency time']
    ]

    def prepare(self, m1, m1_start_pos, m1_final_pos, m1_nr_interv,
                m2, m2_start_pos, m2_final_pos, m2_nr_interv, integ_time,
                bidirectional, latency_time, **opts):

        self.motors = [m1, m2]
        self.starts = numpy.array([m1_start_pos, m2_start_pos], dtype='d')
        self.finals = numpy.array([m1_final_pos, m2_final_pos], dtype='d')
        self.nr_intervs = numpy.array([m1_nr_interv, m2_nr_interv], dtype='i')

        # Number of intervals of the first motor which is doing the
        # continuous scan.
        self.nr_interv = m1_nr_interv
        self.nr_points = self.nr_interv + 1
        self.integ_time = integ_time
        self.bidirectional_mode = bidirectional

        self.name = opts.get('name', 'meshct')

        moveables = []
        for m, start, final in zip(self.motors, self.starts, self.finals):
            moveables.append(MoveableDesc(moveable=m, min_value=min(
                start, final), max_value=max(start, final)))
        moveables[0].is_reference = True

        env = opts.get('env', {})
        mg_name = self.getEnv('ActiveMntGrp')
        mg = self.getMeasurementGroup(mg_name)
        mg_latency_time = mg.getLatencyTime()
        if mg_latency_time > latency_time:
            self.info("Choosing measurement group latency time: %f" %
                      mg_latency_time)
            latency_time = mg_latency_time

        self.latency_time = latency_time

        constrains = [getCallable(cns) for cns in opts.get('constrains',
                                                           [UNCONSTRAINED])]

        extrainfodesc = opts.get('extrainfodesc', [])

        # Hooks are not always set at this point. We will call getHooks
        # later on in the scan_loop
        # self.pre_scan_hooks = self.getHooks('pre-scan')
        # self.post_scan_hooks = self.getHooks('post-scan')

        self._gScan = CTScan(self, self._generator, moveables, env, constrains,
                             extrainfodesc)
        # _data is the default member where the Macro class stores the data.
        # Assign the date produced by GScan (or its subclasses) to it so all
        # the Macro infrastructure related to the data works e.g. getter,
        # property, etc.
        self.setData(self._gScan.data)

    def _generator(self):
        moveables_trees = self._gScan.get_moveables_trees()
        step = {}
        step["pre-move-hooks"] = self.getHooks('pre-move')
        post_move_hooks = self.getHooks(
            'post-move') + [self._fill_missing_records]
        step["post-move-hooks"] = post_move_hooks
        step["check_func"] = []
        step["active_time"] = self.nr_points * (self.integ_time +
                                                self.latency_time)

        m1start, m2start = self.starts
        m1end, m2end = self.finals
        points1, points2 = self.nr_intervs + 1

        m2_space = numpy.linspace(m2start, m2end, points2)
        self.waypoints = []
        starts_points = []
        for i, m2pos in enumerate(m2_space):
            starts_points.append([m1start, m2pos])
            self.waypoints.append([m1end, m2pos])
            if self.bidirectional_mode:
                m1start, m1end = m1end, m1start

        for i, waypoint in enumerate(self.waypoints):
            self.point_id = points1 * i
            step["waypoint_id"] = i
            self.starts = starts_points[i]
            self.finals = waypoint
            step["positions"] = []
            step["start_positions"] = []

            for start, end, moveable_tree in zip(self.starts, self.finals,
                                                 moveables_trees):
                moveable_root = moveable_tree.root()
                start_positions, end_positions = _calculate_positions(
                    moveable_root, start, end)
                step["start_positions"] += start_positions
                step["positions"] += end_positions

            yield step

    def run(self, *args):
        for step in self._gScan.step_scan():
            yield step

    def getTimeEstimation(self):
        return 0.0

    def getIntervalEstimation(self):
        return self.nr_intervs

    def _fill_missing_records(self):
        # fill record list with dummy records for the final padding
        nb_of_points = self.nr_points
        scan = self._gScan
        nb_of_total_records = len(scan.data.records)
        nb_of_records = nb_of_total_records - self.point_id
        missing_records = nb_of_points - nb_of_records
        scan.data.initRecords(missing_records)


class timescan(Macro, Hookable):
    """Do a time scan over the specified time intervals. The scan starts
    immediately. The number of data points collected will be nr_interv + 1.
    Count time is given by integ_time. Latency time will be the longer one
    of latency_time and measurement group latency time.
    """

    param_def = [
        ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['latency_time', Type.Float, 0, 'Latency time']]

    def prepare(self, nr_interv, integ_time, latency_time):
        self.nr_interv = nr_interv
        self.nr_points = nr_interv + 1
        self.integ_time = integ_time
        self.latency_time = latency_time
        self._gScan = TScan(self)

        # _data is the default member where the Macro class stores the data.
        # Assign the date produced by GScan (or its subclasses) to it so all
        # the Macro infrastructure related to the data works e.g. getter,
        # property, etc.
        self.setData(self._gScan.data)

    def run(self, *args):
        for step in self._gScan.step_scan():
            yield step

    def getTimeEstimation(self):
        mg_latency_time = self._gScan.measurement_group.getLatencyTime()
        latency_time = max(self.latency_time, mg_latency_time)
        return self.nr_points * (self.integ_time + latency_time)

    def getIntervalEstimation(self):
        return self.nr_interv
