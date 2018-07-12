.. currentmodule:: sardana.pool.controller

.. _sardana-pseudomotorcontroller-howto-basics:

======================================
How to write a pseudo motor controller
======================================

This chapter describes how to write a valid python pseudo motor system
class. 

Prerequisites
-------------

Before writing the first python pseudo motor class for your device
pool two checks must be performed: 

1. The device pool **PoolPath** property must exist and must point to the
   directory which will contain your python pseudo motor module. The syntax of
   this PseudoPath property is the same used in the PATH or PYTHONPATH
   environment variables.

   .. seealso:: Please see :ref:`sardana-pool-api-poolpath` 
                for more information on setting this property.

2. A *PseudoMotor.py* file is part of the device pool distribution and is
   located within the *sardana/pool* module. The directory containing this
   module must be in the PYTHONPATH environment variable or it must be part of
   the **PoolPath** device pool property mentioned above.

Rules
-----

A correct pseudo motor system class must obey the following rules: 

#. The python class PseudoMotor of the PseudoMotor module must be
   imported into the current namespace by using one of the python import
   statements:

    
    
    ::
    
        from PseudoMotor import *

    ::

        import PseudoMotor

   or
   
    ::

        from PseudoMotor import PseudoMotor
    
    
#. The pseudo motor system class being written must be a subclass of the
   PseudoMotor class (see example :ref:`below <pseudomotor-example>`)


#. The class variable **motor_roles** must be set to be a tuple of text
   descriptions containing each motor role description. It is crucial that all
   necessary motors contain a textual description even if it is an empty one.
   This is because the number of elements in this tuple will determine the
   number of required motors for this pseudo motor class. The order in which
   the roles are defined is also important as it will determine the index of
   the motors in the pseudo motor system.


#. The class variable **pseudo_motor_roles** must be set if the pseudo motor
   class being written represents more than one pseudo motor. The order in
   which the roles are defined will determine the index of the pseudo motors
   in the pseudo motor system. If the pseudo motor class represents only one
   pseudo motor then this operation is optional. If omitted, the value of
   pseudo_motor_roles will be set with the class name.

    
#. If the pseudo motor class needs some special parameters then the class
   variable parameters must be set to be a dictionary of 
   
   ::

   <parameter name>: { <property> : <value> } 
   
   where:

   * <parameter name> is a string representing the name of the parameter.
   
   * <property> is one of the following mandatory properties:
   
        * 'Description'
   
        * 'Type'

     The 'Default Value' property is optional. 
    
   * <value> is the corresponding value of the property. The
     'Description' can contain any text value.
     The 'Type' must be one of available Tango_ property data types and
     'Default Value' must be a string containing a valid value for the
     corresponding 'Type' value. 


#. The pseudo motor class must implement a **calc_pseudo** method with the
   following signature:

   ::
    
        number = calc_pseudo(index, physical_pos, params = None)
    
   The method will receive as argument the index of the pseudo motor for
   which the pseudo position calculation is requested. This number refers
   to the index in the pseudo_motor_roles class variable. 
   
   The physical_pos is a tuple containing the motor positions. 
   
   The params argument is optional and will contain a dictionary of
   <parameter name> : <value>. 
   
   The method body should contain a code to translate the given motor
   positions into pseudo motor positions. 
   
   The method will return a number representing the calculated pseudo
   motor position. 


#. The pseudo motor class must implement a **calc_physical** method with the
   following signature:

    ::
    
        number = calc_physical(index, pseudo_pos, params = None)
    
   The method will receive as argument the index of the motor for which
   the physical position calculation is requested. This number refers to
   the index in the motor_roles class variable. 
   
   The pseudo_pos is a tuple containing the pseudo motor positions. 
   
   The params argument is optional and will contain a dictionary of
   <parameter name> : <value>. 
   
   The method body should contain a code to translate the given pseudo
   motor positions into motor positions. 
   
   The method will return a number representing the calculated motor position. 
    

#. Optional implementation of **calc_all_pseudo** method with the following
   signature:

   ::
   
       ()/[]/number = calc_all_pseudo(physical_pos,params = None)
   
   The method will receive as argument a physical_pos which is a tuple of
   motor positions. 
   
   The params argument is optional and will contain a dictionary of
   <parameter name> : <value>. 
   
   The method will return a tuple or a list of calculated pseudo motor
   positions. If the pseudo motor class represents a single pseudo motor
   then the return value could be a single number. 
   
   .. note:: At the time of writing this documentation, the method
             **calc_all_pseudo** is not used. Is still available for backward
             compatibility.

    
#. Optional implementation of **calc_all_physical** method with the following
   signature:
    
   ::
   
       ()/[]/number = calc_all_physical(pseudo_pos, params = None)
   
   The method will receive as argument a pseudo_pos which is a tuple of
   pseudo motor positions. 
   
   The params argument is optional and will contain a dictionary of
   <parameter name> : <value>. 
   
   The method will return a tuple or a list of calculated motor
   positions. If the pseudo motor class requires a single motor then the
   return value could be a single number. 

   .. note:: The default implementation **calc_all_physical** and 
             **calc_all_pseudo** methods will call calc_physical and calc_pseudo
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


The corresponding python code would be: 

::
    
      class Slit(PseudoMotor):
          """A Slit system for controlling gap and offset pseudo motors."""
    
          pseudo_motor_roles = ("Gap", "Offset")
          motor_roles = ("Motor on blade 1", "Motor on blade 2")
    
      def calc_physical(self,index,pseudo_pos,params = None):
          half_gap = pseudo_pos[0]/2.0
          if index == 0:
              return -pseudo_pos[1] + half_gap
          else
              return pseudo_pos[1] + half_gap
    
      def calc_pseudo(self,index,physical_pos,params = None):
          if index == 0:
              return physical_pos[1] + physical_pos[0]
          else:
              return (physical_pos[1] - physical_pos[0])/2.0


Read Gap Position Diagram
-------------------------

The following diagram shows the sequence of operations performed when
the position is requested from the gap pseudo motor: 

.. image:: /_static/gap_read.png


Write Gap Position Diagram
--------------------------

The following diagram shows the sequence of operations performed when
a new position is written to the gap pseudo motor: 


.. image:: /_static/gap_write.png


.. seealso:: For more details on pseudo motors please refer to
             :ref:`sardana-pseudomotor-api`

.. _Tango: http://www.tango-controls.org/