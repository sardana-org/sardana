import numpy as np
import scipy.constants

from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoMotorController


class DelayPseudoMotorController(PseudoMotorController):
    """A Slit pseudo motor controller for handling gap and offset pseudo 
       motors. The system uses to real motors sl2t (top slit) and sl2b (bottom
       slit)."""
    
    pseudo_motor_roles = ("OutputMotor",)
    motor_roles = ("InputMotor",)
    
    def __init__(self, inst, props):  
        PseudoMotorController.__init__(self, inst, props)
    
    def CalcPhysical(self, axis, pseudo_pos, curr_physical_pos):
        c_in_mm_ps = scipy.constants.c*1000*1e-12
        return pseudo_pos[axis-1]*c_in_mm_ps/2
    
    def CalcPseudo(self, axis, physical_pos, curr_pseudo_pos):
        c_in_mm_ps = scipy.constants.c*1000*1e-12
        return physical_pos[axis-1]/c_in_mm_ps*2