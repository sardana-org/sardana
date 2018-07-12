.. currentmodule:: sardana.pool.controller

.. _sardana-pseudomotorcontroller-howto-basics:

======================================
How to write a pseudo motor controller
======================================

This chapter describes how to write a valid Python pseudo motor system
class.

Prerequisites
-------------

Before writing the first Python pseudo motor class for your Device
Pool two checks must be performed: 

#. The device pool **PoolPath** property must exist and must point to the
   directory which will contain your Python pseudo motor module. The syntax of
   this **PoolPath** property is one directory per line.

   .. seealso:: Please see :ref:`sardana-pool-api-poolpath` 
                for more information on setting this property.

#. A ``poolpseudomotor.py`` file is part of the Device Pool distribution and is
   located within the :mod:`sardana.pool` module. The directory containing this
   module must be in the PYTHONPATH environment variable or it must be part of
   the **PoolPath** Device Pool property mentioned above.


Rules
-----

A correct pseudo motor system class must obey the following rules:

#. The pseudo motor system class being written must be a subclass of the
   PseudoMotorController class from :mod:`sardana.pool.controller` module
   (see example :ref:`below <pseudomotor-example>`).

#. The class variable **motor_roles** should be a tuple of motor role name.
   The number of elements in this tuple will determine the number of required
   motors for this pseudo motor class. The order in which the roles are defined
   is also important as it will determine the index of the motors in the pseudo 
   motor system.

#. The class variable **pseudo_motor_roles** must be set if the pseudo motor
   class being written represents more than one pseudo motor. This variable
   must contain a tuple of pseudo motor role names.
   The order in which the roles are defined will determine the index of the 
   pseudo motors in the pseudo motor system. If the pseudo motor class 
   represents only one pseudo motor then this operation is optional.
   If omitted, the value of pseudo_motor_roles will be set to the class name.

#. In case the pseudo motor class needs special properties or attributes,
   it exist the possibility of defining them as explained in the section
   :ref:`sardana-controller-howto-axis-attributes` and
   :ref:`sardana-controller-howto-controller-attributes`.

#. The pseudo motor class must implement a **CalcPseudo** method with the
   following signature:

   ::
    
        number = CalcPseudo(index, physical_pos, curr_pseudo_pos)
    
   The method will receive as argument the index of the pseudo motor for
   which the pseudo position calculation is requested. This number refers
   to the index in the pseudo_motor_roles class variable. 

   The physical_pos is a tuple containing the motor positions. 

   The method body should contain a code to translate the given motor
   positions into pseudo motor positions. 

   The method will return a number representing the calculated pseudo
   motor position. 

#. The pseudo motor class must implement a **CalcPhysical** method with the
   following signature:

    ::
    
        number = CalcPhysical(index, pseudo_pos, curr_physical_pos)
    
   The method will receive as argument the index of the motor for which
   the physical position calculation is requested. This number refers to
   the index in the motor_roles class variable. 

   The pseudo_pos is a tuple containing the pseudo motor positions. 

   The method body should contain a code to translate the given pseudo
   motor positions into motor positions. 

   The method will return a number representing the calculated motor position. 

#. Optional implementation of **CalcAllPseudo** method with the following
   signature:

   ::
   
       ()/[]/number = CalcAllPseudo(physical_pos, curr_pseudo_pos)
   
   The method will receive as argument a physical_pos which is a tuple of
   motor positions. 

   The method will return a tuple or a list of calculated pseudo motor
   positions. If the pseudo motor class represents a single pseudo motor
   then the return value could be a single number. 

   .. note:: At the time of writing this documentation, the method
             **CalcAllPseudo** is not used. Is still available for backward
             compatibility.

#. Optional implementation of **CalcAllPhysical** method with the following
   signature:
    
   ::
   
       ()/[]/number = CalcAllPhysical(pseudo_pos, curr_physical_pos)
   
   The method will receive as argument a pseudo_pos which is a tuple of
   pseudo motor positions. 

   The method will return a tuple or a list of calculated motor
   positions. If the pseudo motor class requires a single motor then the
   return value could be a single number. 

   .. note:: The default implementation **CalcAllPhysical** and 
             **CalcAllPseudo** methods will call CalcPhysical and CalcPseudo
             for each motor and physical motor respectively. Overwriting the
             default implementation should only be done if a gain in performance
             can be obtained. 

.. _pseudomotor-example:

Example
~~~~~~~

One of the most basic examples is the control of a slit. The slit has
two blades with one motor each. Usually the user doesn't want to
control the experiment by directly handling these two motor positions
since their have little meaning from the experiments perspective.

.. image:: /_static/gap_offset.png

Instead, it would be more useful for the user to control the
experiment by means of changing the gap and offset values. Pseudo
motors gap and offset will provide the necessary interface for
controlling the experiments gap and offset values respectively.

The calculations that need to be performed are: 

::

    gap = sl2t+sl2b
    offset = (sl2t-sl2b) / 2

::

    sl2t = -offset + gap/2
    sl2b = offset + gap/2


The corresponding Python code would be: 

::

    """This module contains the definition of a slit pseudo motor controller
    for the Sardana Device Pool"""

    __all__ = ["Slit"]

    __docformat__ = 'restructuredtext'

    from sardana import DataAccess
    from sardana.pool.controller import PseudoMotorController
    from sardana.pool.controller import DefaultValue, Description, Access, Type


    class Slit(PseudoMotorController):
        """A Slit pseudo motor controller for handling gap and offset pseudo
        motors. The system uses to real motors sl2t (top slit) and sl2b (bottom
        slit)"""

        gender = "Slit"
        model = "Default Slit"
        organization = "Sardana team"

        pseudo_motor_roles = "Gap", "Offset"
        motor_roles = "sl2t", "sl2b"

        ctrl_properties = {'sign': {Type: float,
                                    Description: 'Gap = sign * calculated gap\nOffset = sign * calculated offet',
                                    DefaultValue: 1}, }

        axis_attributes = {'example': {Type: int,
                                    Access: DataAccess.ReadWrite,
                                    Description: 'test purposes'}, }

        def __init__(self, inst, props, *args, **kwargs):
            PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
            self._log.debug("Created SLIT %s", inst)
            self._example = {}

        def CalcPhysical(self, index, pseudo_pos, curr_physical_pos):
            half_gap = pseudo_pos[0] / 2.0
            if index == 1:
                ret = self.sign * (pseudo_pos[1] + half_gap)
            else:
                ret = self.sign * (half_gap - pseudo_pos[1])
            self._log.debug("Slit.CalcPhysical(%d, %s) -> %f",
                            index, pseudo_pos, ret)
            return ret

        def CalcPseudo(self, index, physical_pos, curr_pseudo_pos):
            gap = physical_pos[1] + physical_pos[0]
            if index == 1:
                ret = self.sign * gap
            else:
                ret = self.sign * (physical_pos[0] - gap / 2.0)
            return ret

        def CalcAllPseudo(self, physical_pos, curr_pseudo_pos):
            """Calculates the positions of all pseudo motors that belong to the
            pseudo motor system from the positions of the physical motors."""
            gap = physical_pos[1] + physical_pos[0]
            return (self.sign * gap,
                    self.sign * (physical_pos[0] - gap / 2.0))

        def SetAxisExtraPar(self, axis, parameter, value):
            self._example[axis] = value

        def GetAxisExtraPar(self, axis, parameter):
            return self._example.get(axis, -1)


.. seealso:: For more details on pseudo motors please refer to
             :ref:`sardana-pseudomotor-api`

.. _Tango: http://www.tango-controls.org/
