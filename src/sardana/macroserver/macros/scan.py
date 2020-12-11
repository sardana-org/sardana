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
"""

__all__ = ["a2scan", "a3scan", "a4scan", "amultiscan", "aNscan", "ascan",
           "d2scan", "d3scan", "d4scan", "dmultiscan", "dNscan", "dscan",
           "fscan", "mesh", "timescan",
           "a2scanc", "a3scanc", "a4scanc", "ascanc",
           "d2scanc", "d3scanc", "d4scanc", "dscanc",
           "meshc",
           "a2scanct", "a3scanct", "a4scanct", "ascanct", "meshct",
           "scanhist", "getCallable", "UNCONSTRAINED",
           "scanstats"]

__docformat__ = 'restructuredtext'

import os
import copy
import datetime

import numpy

from taurus.core.util import SafeEvaluator

from sardana.macroserver.msexception import UnknownEnv
from sardana.macroserver.macro import Hookable, Macro, Type, Table, List
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
    """N-dimensional scan. This is **not** meant to be called by the user,
    but as a generic base to construct ascan, a2scan, a3scan,..."""

    hints = {'scan': 'aNscan', 'allowsHooks': ('pre-scan', 'pre-move',
                                               'post-move', 'pre-acq',
                                               'post-acq', 'post-step',
                                               'post-scan')}
    # env = ('ActiveMntGrp',)

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
            self.nb_points = self.nr_interv + 1
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
                self.nb_points = self.nr_interv + 1
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
            self.nb_points = self.nr_interv + 1
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
        for point_no in range(self.nb_points):
            step["positions"] = self.starts + point_no * self.interv_sizes
            step["point_id"] = point_no
            yield step

    def _waypoint_generator(self):
        step = {}
        step["pre-move-hooks"] = self.getHooks('pre-move')
        step["post-move-hooks"] = self.getHooks('post-move')
        step["check_func"] = []
        step["slow_down"] = self.slow_down
        for point_no in range(self.nr_waypoints):
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
        step["pre-acq-hooks"] = self.getHooks('pre-acq')
        step["post-acq-hooks"] = self.getHooks('post-acq') + self.getHooks(
            '_NOHINTS_')
        step["check_func"] = []
        step["active_time"] = self.nb_points * (self.integ_time
                                                + self.latency_time)
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
            step0 = next(it)
            for v_motor, start, stop, length in zip(v_motors, curr_pos,
                                                    step0['positions'],
                                                    self.interv_sizes):
                path0 = MotionPath(v_motor, start, stop)
                path = MotionPath(v_motor, 0, length)
                max_step0_time = max(max_step0_time, path0.duration)
                max_step_time = max(max_step_time, path.duration)
            motion_time = max_step0_time + self.nr_interv * max_step_time
            # calculate acquisition time
            acq_time = self.nb_points * self.integ_time
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
        nb_of_points = self.nb_points
        scan = self._gScan
        nb_of_records = len(scan.data.records)
        missing_records = nb_of_points - nb_of_records
        scan.data.initRecords(missing_records)

    def _get_nr_points(self):
        msg = ("nr_points is deprecated since version 3.0.3. "
               "Use nb_points instead.")
        self.warning(msg)
        return self.nb_points

    nr_points = property(_get_nr_points)

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
    """
    two-motor scan.
    a2scan scans two motors, as specified by motor1 and motor2.
    Each motor moves the same number of intervals with starting and ending
    positions given by start_pos1 and final_pos1, start_pos2 and final_pos2,
    respectively. The step size for each motor is:
    (start_pos-final_pos)/nr_interv
    The number of data points collected will be nr_interv+1.
    Count time is given by time which if positive, specifies seconds and
    if negative, specifies monitor counts.
    """
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
         [['motor', Type.Moveable, None, 'Moveable to move'],
          ['start', Type.Float, None, 'Starting position'],
          ['end', Type.Float, None, 'Final position']],
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
         [['motor', Type.Moveable, None, 'Moveable to move'],
          ['start', Type.Float, None, 'Starting position'],
          ['end', Type.Float, None, 'Final position']],
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
        self.nb_points = (m1_nr_interv + 1) * (m2_nr_interv + 1)
        self.integ_time = integ_time
        self.bidirectional_mode = bidirectional

        self.name = opts.get('name', 'mesh')

        generator = self._generator
        moveables = []
        for m, start, final in zip(self.motors, self.starts, self.finals):
            moveables.append(MoveableDesc(moveable=m,
                                          min_value=min(start, final),
                                          max_value=max(start, final)))
        moveables[0].is_reference = True
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


    >>> fscan x=[1,3,5,7,9],y=arange(5) 0.1 motor1 x**2 motor2 sqrt(y*x+3)
    >>> fscan x=[1,3,5,7,9],y=arange(5) [0.1,0.2,0.3,0.4,0.5] motor1 x**2 \
motor2 sqrt(y*x+3)
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
         [['motor', Type.Moveable, None, 'motor'],
          ['func', Type.String, None, 'curve defining path']],
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

        globals_lst = [dict(list(zip(indepvars, values)))
                       for values in zip(*list(indepvars.values()))]
        self.paths = [[SafeEvaluator(globals).eval(
            func) for globals in globals_lst] for func in self.funcstrings]

        self._integ_time = numpy.array(eval(args[1]), dtype='d')

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
        self._nb_points = npoints

        if self._integ_time.size == 1:
            self._integ_time = self._integ_time * \
                numpy.ones(self._nb_points)  # extend integ_time
        elif self._integ_time.size != self._nb_points:
            raise ValueError('time_integ must either be a scalar or '
                             'length=npoints (%i)' % self._nb_points)

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
        for i in range(self._nb_points):
            step["positions"] = self.paths[:, i]
            step["integ_time"] = self._integ_time[i]
            step["point_id"] = i
            yield step

    def run(self, *args):
        for step in self._gScan.step_scan():
            yield step

    def _get_nr_points(self):
        msg = ("nr_points is deprecated since version 3.0.3. "
               "Use nb_points instead.")
        self.warning(msg)
        return self.nb_points

    nr_points = property(_get_nr_points)



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
            print("No scan recorded in history")
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


class aNscanct(aNscan):
    """N-dimensional continuous scan. This is **not** meant to be called by
    the user, but as a generic base to construct ascanct, a2scanct, a3scanct,
    ..."""

    hints = {"scan": "aNscanct",
             "allowsHooks": ("pre-scan", "pre-configuration",
                             "post-configuration", "pre-move",
                             "post-move", "pre-acq", "pre-start",
                             "post-acq", "pre-cleanup", "post-cleanup",
                             "post-scan")}


class ascanct(aNscanct, Macro):
    """Do an absolute continuous scan of the specified motor.
    ascanct scans one motor, as specified by motor. The motor starts before the
    position given by start_pos in order to reach the constant velocity at the
    start_pos and finishes at the position after the final_pos in order to
    maintain the constant velocity until the final_pos."""

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


class a2scanct(aNscanct, Macro):
    """Two-motor continuous scan.
    a2scanct scans two motors, as specified by motor1 and motor2. Each motor
    starts before the position given by its start_pos in order to reach the
    constant velocity at its start_pos and finishes at the position after
    its final_pos in order to maintain the constant velocity until its
    final_pos."""

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


class a3scanct(aNscanct, Macro):
    """Three-motor continuous scan.
    a2scanct scans three motors, as specified by motor1, motor2 and motor3.
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


class dNscanct(dNscan):
    """N-dimensional continuous scan. This is **not** meant to be called by
    the user, but as a generic base to construct ascanct, a2scanct, a3scanct,
    ..."""

    hints = {"scan": "dNscanct",
             "allowsHooks": ("pre-scan", "pre-configuration",
                             "post-configuration", "pre-move",
                             "post-move", "pre-acq", "pre-start",
                             "post-acq", "pre-cleanup", "post-cleanup",
                             "post-scan")}


class dscanct(dNscanct, Macro):
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


class d2scanct(dNscanct, Macro):
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


class d3scanct(dNscanct, Macro):
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


class d4scanct(dNscanct, Macro):
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

    hints = {"scan": "meshct",
             "allowsHooks": ("pre-scan", "pre-configuration",
                             "post-configuration", "pre-move",
                             "post-move", "pre-acq", "pre-start",
                             "post-acq", "pre-cleanup", "post-cleanup",
                             "post-scan")}
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
        self.nb_points = self.nr_interv + 1
        self.integ_time = integ_time
        self.bidirectional_mode = bidirectional

        # Prepare the waypoints
        m1start, m2start = self.starts
        m1end, m2end = self.finals
        points1, points2 = self.nr_intervs + 1

        m2_space = numpy.linspace(m2start, m2end, points2)
        self.waypoints = []
        self.starts_points = []
        for i, m2pos in enumerate(m2_space):
            self.starts_points.append(numpy.array([m1start, m2pos], dtype='d'))
            self.waypoints.append(numpy.array([m1end, m2pos], dtype='d'))
            if self.bidirectional_mode:
                m1start, m1end = m1end, m1start

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
        step["active_time"] = self.nb_points * (self.integ_time
                                                + self.latency_time)

        points1, _ = self.nr_intervs + 1
        for i, waypoint in enumerate(self.waypoints):
            self.point_id = points1 * i
            step["waypoint_id"] = i
            self.starts = self.starts_points[i]
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
        return len(self.waypoints)

    def _fill_missing_records(self):
        # fill record list with dummy records for the final padding
        nb_of_points = self.nb_points
        scan = self._gScan
        nb_of_total_records = len(scan.data.records)
        nb_of_records = nb_of_total_records - self.point_id
        missing_records = nb_of_points - nb_of_records
        scan.data.initRecords(missing_records)

    def _get_nr_points(self):
        msg = ("nr_points is deprecated since version 3.0.3. "
               "Use nb_points instead.")
        self.warning(msg)
        return self.nb_points

    nr_points = property(_get_nr_points)


class timescan(Macro, Hookable):
    """Do a time scan over the specified time intervals. The scan starts
    immediately. The number of data points collected will be nr_interv + 1.
    Count time is given by integ_time. Latency time will be the longer one
    of latency_time and measurement group latency time.
    """

    hints = {'scan': 'timescan', 'allowsHooks': ('pre-scan', 'pre-acq',
                                                 'post-acq', 'post-scan')}

    param_def = [
        ['nr_interv', Type.Integer, None, 'Number of scan intervals'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['latency_time', Type.Float, 0, 'Latency time']]

    def prepare(self, nr_interv, integ_time, latency_time):
        self.nr_interv = nr_interv
        self.nb_points = nr_interv + 1
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
        return self.nb_points * (self.integ_time + latency_time)

    def getIntervalEstimation(self):
        return self.nr_interv

    def _get_nr_points(self):
        msg = ("nr_points is deprecated since version 3.0.3. "
               "Use nb_points instead.")
        self.warning(msg)
        return self.nb_points

    nr_points = property(_get_nr_points)


class scanstats(Macro):
    """Calculate basic statistics of the enabled and plotted channels in
    the active measurement group for the last scan. If no channel is selected
    for plotting it fallbacks to the first enabled channel. Print stats and
    publish them in the env.
    The macro must be hooked in the post-scan hook place.
    """

    env = ("ActiveMntGrp", )

    param_def = [
        ["channel",
         [["channel", Type.ExpChannel, None, ""], {"min": 0}],
         None,
         "List of channels for statistics calculations"
         ]
        ]

    def run(self, channel):
        parent = self.getParentMacro()
        if not parent:
            self.warning("for now the scanstats macro can only be executed as"
                         " a post-scan hook")
            return
        if not hasattr(parent, "motors"):
            self.warning("scan must involve at least one moveable "
                         "to calculate statistics")
            return

        active_meas_grp = self.getEnv("ActiveMntGrp")
        meas_grp = self.getMeasurementGroup(active_meas_grp)
        calc_channels = []
        enabled_channels = meas_grp.getEnabled()
        if channel:
            stat_channels = [chan.name for chan in channel]
        else:
            stat_channels = [key for key in enabled_channels.keys()]

        for chan in stat_channels:
            enabled = enabled_channels.get(chan)
            if enabled is None:
                self.warning("{} not in {}".format(chan, meas_grp.name))
            else:
                if not enabled and channel:
                    self.warning("{} not enabled".format(chan))
                elif enabled and channel:
                    # channel was given as parameters
                    calc_channels.append(chan)
                elif enabled and meas_grp.getPlotType(chan)[chan] == 1:
                    calc_channels.append(chan)

        if len(calc_channels) == 0:
            # fallback is first enabled channel in meas_grp
            calc_channels.append(next(iter(enabled_channels)))

        scalar_channels = []
        for _, chan in self.getExpChannels().items():
            if chan.type in ("OneDExpChannel", "TwoDExpChannel"):
                continue
            scalar_channels.append(chan.name)
        calc_channels = [ch for ch in calc_channels if ch in scalar_channels]

        if len(calc_channels) == 0:
            self.warning("measurement group must contain at least one "
                         "enabled scalar channel to calculate statistics")
            return

        selected_motor = str(parent.motors[0])
        stats = {}
        col_header = []
        cols = []

        motor_data = []
        channels_data = {}
        for channel_name in calc_channels:
            channels_data[channel_name] = []

        for idx, rc in parent.data.items():
            motor_data.append(rc[selected_motor])
            for channel_name in calc_channels:
                channels_data[channel_name].append(rc[channel_name])

        motor_data = numpy.array(motor_data)
        for channel_name, data in channels_data.items():
            channel_data = numpy.array(data)

            (_min, _max, min_at, max_at, half_max, com, mean, _int,
             fwhm, cen) = self._calcStats(motor_data, channel_data)
            stats[channel_name] = {
                "min": _min,
                "max": _max,
                "minpos": min_at,
                "maxpos": max_at,
                "mean": mean,
                "int": _int,
                "com": com,
                "fwhm": fwhm,
                "cen": cen}

            col_header.append([channel_name])
            cols.append([
                stats[channel_name]["min"],
                stats[channel_name]["max"],
                stats[channel_name]["minpos"],
                stats[channel_name]["maxpos"],
                stats[channel_name]["mean"],
                stats[channel_name]["int"],
                stats[channel_name]["com"],
                stats[channel_name]["fwhm"],
                stats[channel_name]["cen"],
                        ])
        self.info("Statistics for movable: {:s}".format(selected_motor))

        table = Table(elem_list=cols, elem_fmt=["%*g"],
                      row_head_str=["MIN", "MAX", "MIN@", "MAX@",
                                    "MEAN", "INT", "COM", "FWHM", "CEN"],
                      col_head_str=col_header, col_head_sep="-")
        out = table.genOutput()

        for line in out:
            self.info(line)
        self.setEnv("{:s}.ScanStats".format(self.getDoorName()),
                    {"Stats": stats,
                     "Motor": selected_motor,
                     "ScanID": self.getEnv("ScanID")})

    @staticmethod
    def _calcStats(x, y):
        # max and min
        _min = numpy.min(y)
        _max = numpy.max(y)

        min_idx = numpy.argmin(y)
        min_at = x[min_idx]
        max_idx = numpy.argmax(y)
        max_at = x[max_idx]

        # center of mass (com)
        try:
            com = numpy.sum(y*x)/numpy.sum(y)
        except ZeroDivisionError:
            com = 0

        mean = numpy.mean(y)
        _int = numpy.sum(y)

        # determine if it is a peak- or erf-like function
        half_max = (_max-_min)/2+_min

        lower_left = False
        lower_right = False

        if numpy.any(y[0:max_idx] < half_max):
            lower_left = True
        if numpy.any(y[max_idx:] < half_max):
            lower_right = True

        if lower_left and lower_right:
            # it is a peak-like function
            y_data = y
        elif lower_left:
            # it is an erf-like function
            # use the gradient for further calculation
            y_data = numpy.gradient(y)
            # use also the half maximum of the gradient
            half_max = (numpy.max(y_data)-numpy.min(y_data)) \
                / 2+numpy.min(y_data)
        else:
            # it is an erf-like function
            # use the gradient for further calculation
            y_data = -1*numpy.gradient(y)
            # use also the half maximum of the gradient
            half_max = (numpy.max(y_data)-numpy.min(y_data)) \
                / 2+numpy.min(y_data)

        # cen and fwhm
        # this part is adapted from:
        #
        # The PyMca X-Ray Fluorescence Toolkit
        #
        # Copyright (c) 2004-2014 European Synchrotron Radiation Facility
        #
        # This file is part of the PyMca X-ray Fluorescence Toolkit developed
        # at the ESRF by the Software group.

        max_idx_data = numpy.argmax(y_data)
        idx = max_idx_data
        try:
            while y_data[idx] >= half_max:
                idx = idx-1

            x0 = x[idx]
            x1 = x[idx+1]
            y0 = y_data[idx]
            y1 = y_data[idx+1]

            lhmx = (half_max*(x1-x0) - (y0*x1)+(y1*x0)) / (y1-y0)
        except ZeroDivisionError:
            lhmx = 0
        except IndexError:
            lhmx = x[0]

        idx = max_idx_data
        try:
            while y_data[idx] >= half_max:
                idx = idx+1

            x0 = x[idx-1]
            x1 = x[idx]
            y0 = y_data[idx-1]
            y1 = y_data[idx]

            uhmx = (half_max*(x1-x0) - (y0*x1)+(y1*x0)) / (y1-y0)
        except ZeroDivisionError:
            uhmx = 0
        except IndexError:
            uhmx = x[-1]

        fwhm = uhmx - lhmx
        cen = (uhmx + lhmx)/2

        return (_min, _max, min_at, max_at, half_max, com, mean, _int,
                fwhm, cen)
