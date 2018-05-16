from PyTango import AttrQuality
from PyTango import AttributeProxy
from PyTango import DevFailed

from sardana import State, DataAccess
from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Access, Description

import math
import time

TANGO_ATTR = 'TangoAttribute'
FORMULA_READ = 'FormulaRead'
FORMULA_WRITE = 'FormulaWrite'
TANGO_ATTR_ENC = 'TangoAttributeEncoder'
TANGO_ATTR_ENC_THRESHOLD = 'TangoAttributeEncoderThreshold'
TANGO_ATTR_ENC_SPEED = 'TangoAttributeEncoderSpeed'

TAU_ATTR = 'TauAttribute'
TAU_ATTR_ENC = 'TauAttributeEnc'
MOVE_TO = 'MoveTo'
MOVE_TIMEOUT = 'MoveTimeout'


class TangoAttrMotorController(MotorController):
    """This controller offers as many motors as the user wants.

    Each motor has three _MUST_HAVE_ extra attributes:
    +) TangoAttribute - Tango attribute used to simulate the motor's position
        (moving the motor writes this attribute)
    +) FormulaRead - Formula evaluate using 'VALUE' as the Tango read attribute
        value
    +) FormulaWrite - Formula to evaluate using 'VALUE' as the motor position

    As examples you could have:
        ch1.TangoAttribute = 'my/tango/device/attribute1'
        ch1.FormulaRead = '-1 * VALUE'
        ch2.FormulaWrite = '-1 * VALUE'
        ch2.TangoAttribute = 'my/tango/device/attribute2'
        ch2.FormulaRead = 'math.sqrt(VALUE)'
        ch2.FormulaWrite = 'math.pow(VALUE,2)'

    Each motor could use the following optional extra attributes:
    +) TangoAttributeEncoder - Used in case you want to use another attribute
        (different than the TangoAttribute) when the motor's position is to be
        read.
    +) TangoAttributeEncoderThreshold - Threshold used for the 'MOVING' state.
    +) TangoAttributeEncoderSpeed - Speed in units/second of the encoder so
        'MOVING' state is computed (sec).
    """

    gender = ""
    model = ""
    organization = "CELLS - ALBA"
    image = ""
    icon = ""
    logo = "ALBA_logo.png"

    MaxDevice = 1024

    axis_attributes = {
        TANGO_ATTR: {
            Type: str,
            Description: 'The first Tango Attribute to read'\
                ' (e.g. my/tango/dev/attr)',
            Access: DataAccess.ReadWrite
        },
        FORMULA_READ: {
            Type: str,
            Description: 'The Formula to get the desired position from'\
                ' attribute value.\ne.g. "math.sqrt(VALUE)"',
            Access: DataAccess.ReadWrite
        },
        FORMULA_WRITE: {
            Type: str,
            Description: 'The Formula to set the desired value from motor'\
                ' position.\ne.g. "math.pow(VALUE,2)"',
            Access: DataAccess.ReadWrite
        },
        TANGO_ATTR_ENC: {
            Type: str,
            Description: 'The Tango Attribute used as encoder"',
            Access: DataAccess.ReadWrite
        },
        TANGO_ATTR_ENC_THRESHOLD: {
            Type: float,
            Description: 'Maximum difference for considering the motor'\
                ' stopped"',
            Access: DataAccess.ReadWrite
        },
        TANGO_ATTR_ENC_SPEED: {
            Type: float,
            Description: 'Units per second used to wait encoder value within'\
                ' threshold after a movement."',
            Access: DataAccess.ReadWrite
        }
    }

    def __init__(self, inst, props, *args, **kwargs):
        MotorController.__init__(self, inst, props, *args, **kwargs)
        self.axisAttributes = {}

    def AddDevice(self, axis):
        self.axisAttributes[axis] = {}
        self.axisAttributes[axis][TAU_ATTR] = None
        self.axisAttributes[axis][FORMULA_READ] = 'VALUE'
        self.axisAttributes[axis][FORMULA_WRITE] = 'VALUE'
        self.axisAttributes[axis][TAU_ATTR_ENC] = None
        self.axisAttributes[axis][TANGO_ATTR_ENC_THRESHOLD] = 0
        self.axisAttributes[axis][TANGO_ATTR_ENC_SPEED] = 1e-6
        self.axisAttributes[axis][MOVE_TO] = None
        self.axisAttributes[axis][MOVE_TIMEOUT] = None

    def DeleteDevice(self, axis):
        del self.axisAttributes[axis]

    def StateOne(self, axis):
        try:
            state = State.On
            status = 'ok'
            switch_state = 0
            tau_attr = self.axisAttributes[axis][TAU_ATTR]
            if tau_attr is None:
                return (State.Alarm, "attribute proxy is None", 0)

            if tau_attr.read().quality == AttrQuality.ATTR_CHANGING:
                state = State.Moving

            elif self.axisAttributes[axis][MOVE_TIMEOUT] != None:
                tau_attr_enc = self.axisAttributes[axis][TAU_ATTR_ENC]
                enc_threshold = self.axisAttributes[
                    axis][TANGO_ATTR_ENC_THRESHOLD]
                move_to = self.axisAttributes[axis][MOVE_TO]
                move_timeout = self.axisAttributes[axis][MOVE_TIMEOUT]

                current_pos = self.ReadOne(axis)

                if abs(move_to - current_pos) <= abs(enc_threshold):
                    self.axisAttributes[axis][MOVE_TIMEOUT] = None
                    self.axisAttributes[axis][MOVE_TO] = None
                    # Allow last event for position
                    state = State.On
                elif time.time() < move_timeout:
                    state = State.Moving
                else:
                    state = State.Alarm
                    status = ('Motor did not reach the desired position. %f not'
                              ' in [%f,%f]' % (current_pos,
                                               move_to - enc_threshold,
                                               move_to + enc_threshold))

            # SHOULD DEAL ALSO ABOUT LIMITS
            switch_state = 0
            return (state, status, switch_state)
        except Exception, e:
            self._log.error(" (%d) error getting state: %s" % (axis, str(e)))
            return (State.Alarm, "Exception: %s" % str(e), 0)

    def PreReadAll(self):
        pass

    def PreReadOne(self, axis):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self, axis):
        try:
            tau_attr = self.axisAttributes[axis][TAU_ATTR]
            if tau_attr is None:
                raise Exception("attribute proxy is None")

            if self.axisAttributes[axis][TAU_ATTR_ENC] is not None:
                tau_attr = self.axisAttributes[axis][TAU_ATTR_ENC]

            formula = self.axisAttributes[axis][FORMULA_READ]
            VALUE = tau_attr.read().value
            # just in case 'VALUE' has been written in lowercase in the
            # formula...
            value = VALUE
            evaluated_value = eval(formula)
            return evaluated_value
        except Exception, e:
            self._log.error("(%d) error reading: %s" % (axis, str(e)))
            raise e

    def PreStartAll(self):
        pass

    def PreStartOne(self, axis, pos):
        return not self.axisAttributes[axis][TAU_ATTR] is None

    def StartOne(self, axis, pos):
        try:
            tau_attr = self.axisAttributes[axis][TAU_ATTR]
            formula = self.axisAttributes[axis][FORMULA_WRITE]
            VALUE = pos
            # just in case 'VALUE' has been written in lowercase in the
            # formula...
            value = VALUE
            evaluated_value = eval(formula)

            try:
                self.axisAttributes[axis][MOVE_TO] = pos
                move_time = 0.5
                if self.axisAttributes[axis][TANGO_ATTR_ENC_SPEED] > 0:
                    move_time = abs(self.ReadOne(axis) - pos) / \
                        self.axisAttributes[axis][TANGO_ATTR_ENC_SPEED]
                self.axisAttributes[axis][
                    MOVE_TIMEOUT] = time.time() + move_time
            except Exception, e:
                self._log.error(
                    "(%d) error calculating time to wait: %s" % (axis, str(e)))

            tau_attr.write(evaluated_value)

        except Exception, e:
            self._log.error("(%d) error writing: %s" % (axis, str(e)))

    def StartAll(self):
        pass

    def AbortOne(self, axis):
        pass

    def StopOne(self, axis):
        pass

    def SetPar(self, axis, name, value):
        self.axisAttributes[axis][name] = value

    def GetPar(self, axis, name):
        return self.axisAttributes[axis][name]

    def GetAxisExtraPar(self, axis, name):
        return self.axisAttributes[axis][name]

    def SetAxisExtraPar(self, axis, name, value):
        try:
            self._log.debug(
                "SetExtraAttributePar [%d] %s = %s" % (axis, name, value))
            self.axisAttributes[axis][name] = value
            if name in [TANGO_ATTR, TANGO_ATTR_ENC]:
                key = TAU_ATTR
                if name == TANGO_ATTR_ENC:
                    key = TAU_ATTR_ENC
                try:
                    self.axisAttributes[axis][key] = AttributeProxy(value)
                except Exception, e:
                    self.axisAttributes[axis][key] = None
                    raise e
        except DevFailed, df:
            de = df[0]
            self._log.error("SetExtraAttribute DevFailed: (%s) %s" %
                            (de.reason, de.desc))
            self._log.error("SetExtraAttribute DevFailed: %s" % str(df))
            #raise df
        except Exception, e:
            self._log.error("SetExtraAttribute Exception: %s" % str(e))
            #raise e

    def SendToCtrl(self, in_data):
        return ""
