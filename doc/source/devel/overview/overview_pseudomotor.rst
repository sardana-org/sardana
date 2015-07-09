.. currentmodule:: sardana.pool

.. _sardana-pseudomotor-overview:

=======================
Pseudo motor overview
=======================

.. todo:: document pseudo motor overview

.. seealso:: 
    
    :ref:`sardana-pseudomotor-api`
        the pseudo motor :term:`API` 
    
    :class:`~sardana.tango.pool.PseudoMotor.PseudoMotor`
        the pseudo motor tango device :term:`API`

Advanced topics
---------------

Drift correction
~~~~~~~~~~~~~~~~

Pseudomotors which have siblings and are based on physical motors with an
inaccurate or a finite precision positioning system could be affected by the
drift effect.

**Why does it happen?**

    Each move of a pseudomotor requires calculation of the physical motors
    positions in accordance with the current positions of its siblings.
    The consecutive movements of a pseudomotor can accumulate errors
    of the positioning system and cause drift of its siblings.

**Who is affected?**

    * **Inaccurate positioning systems** which lead to a discrepancy between 
      the write and the read position of the physical motors. In this case the
      physical motors must have a position sensor e.g. encoder but
      must not be configured in :term:`closed loop` (in some special cases,
      where the closed loop is not precise enough, the drift effect can be
      observed as well). This setup can lead to the situation where write and
      read values of the position attribute of the physical motors are
      different e.g. due to the loosing steps problems or the inaccurate
      *step_per_unit* calibration.

    * **Finite precision physical motors** e.g. :term:`stepper` is affected by
      the rounding error when moving to a position which does not translate
      into a discrete number of steps that must be commanded to the hardware.


**How is it solved in Sardana?**

    Sardana implements the drift correction which use is optional but enabled
    by default for all pseudomotors. It is based on the use of the write
    value, instead of the read value, of the siblings' positions, together with
    the new desired position of the pseudomotor being moved, during the
    calculation of the physical positions. The write value of the
    pseudomotor's position gets updated at each move of the pseudomotor or
    any of the underneath motors.

    .. note:: Movements being stopped unexpectedly: abort by the user,
        over-travel limit or any other exceptional condition may cause
        considerable discrepancy in the motor's write and read positions.
        In the subsequent pseudomotor's move, Sardana will also correct this
        difference by using the write instead of read values.

    The drift correction is configurable with the *DriftCorrection* property
    either globally (on the Pool device level) or locally (on each PseudoMotor
    device level).

**Example**

Let's use the slit pseudomotor controller to visualize the drift effect.
This controller comprises two pseudomotors: gap and offset, each of them based
on the same two physical motors: right and left. In this example we will
simulate the inaccurate positioning of the left motor (loosing of 0.002 unit
every 1 unit move).

*Drift correction disabled*

#. Initial state: gap and offset are at positions 0 (gap totally closed and
   offset at the nominal position)

    .. sourcecode:: spock

        Door_lab_1 [1]: wm right left gap offset
                          right           left            gap         offset
        User
         High     Not specified  Not specified  Not specified  Not specified
         Current          0.000          0.000          0.000          0.000
         Low      Not specified  Not specified  Not specified  Not specified

#. Move gap to 1

    .. sourcecode:: spock

        Door_lab_1 [2]: mv gap 1

   The calculation of the physical motors' positions gives us 0.5 for both right
   and left (in accordance with the current offset of 0)

    .. sourcecode:: spock

        Door_lab_1 [3]: wm right left gap offset
                          right           left            gap         offset
        User
         High     Not specified  Not specified  Not specified  Not specified
         Current          0.500          0.498          0.998          0.001
         Low      Not specified  Not specified  Not specified  Not specified

   We observe that the gap pseudomotor did not reach the desired
   position of 1 due to the left's positioning problem. Left's
   position write and read discrepancy of 0.002 causes that the gap reached
   only 0.998 and that the offset drifted to 0.001.


#. Move gap to 2

    .. sourcecode:: spock

        Door_lab_1 [4]: mv gap 2

   The calculation of the physical motors' positions gives us 1.001 for right
   and 0.999 for left (in accordance with the current offset of 0.001).

    .. sourcecode:: spock

        Door_lab_1 [5]: wm right left gap offset
                          right           left            gap         offset
        User
         High     Not specified  Not specified  Not specified  Not specified
         Current          1.001          0.997          1.998          0.002
         Low      Not specified  Not specified  Not specified  Not specified

   We observe that the gap pseudomotor did not reach the desired position of 2
   due to the left's positioning problem. Left's position write and
   read discrepancy of 0.002 causes that the gap reached only 1.998 and that
   the offset drifted again by 0.001 and the total accumulated drift is 0.002.

#. Move gap to 3

   The calculation of the physical motors' positions gives us 1.502 for right
   and 1.498 for left (in accordance with the current offset of 0.002).

    .. sourcecode:: spock

        Door_lab_1 [6]: mv gap 3

        Door_lab_1 [7]: wm right left gap offset
                          right           left            gap         offset
        User
         High     Not specified  Not specified  Not specified  Not specified
         Current          1.502          1.496          2.998          0.003
         Low      Not specified  Not specified  Not specified  Not specified

   We observe that the gap pseudomotor did not reach the desired position of 3
   due to the left's positioning problem. Left's position write and
   read discrepancy of 0.002 causes that the gap reached only 2.998 and that
   the offset drifted by 0.001 and the total accumulated drift is 0.003.

.. figure:: /_static/drift_correction_disabled.png
  :align: center
  :width: 680

  This sketch demonstrates the above example where offset drifted by 0.003.

*Drift correction enabled*

#. Initial state: gap and offset are at positions 0 (gap totally closed and
   offset at the nominal position)

    .. sourcecode:: spock

        Door_lab_1 [1]: wm right left gap offset
                          right           left            gap         offset
        User
         High     Not specified  Not specified  Not specified  Not specified
         Current          0.000          0.000          0.000          0.000
         Low      Not specified  Not specified  Not specified  Not specified

#. Move gap to 1

    .. sourcecode:: spock

        Door_lab_1 [2]: mv gap 1

   The calculation of the physical motors' positions gives us 0.5 for both right
   and left (in accordance with the **last set** offset of 0).

    .. sourcecode:: spock

        Door_lab_1 [3]: wm right left gap offset
                          right           left            gap         offset
        User
         High     Not specified  Not specified  Not specified  Not specified
         Current          0.500          0.498          0.998          0.001
         Low      Not specified  Not specified  Not specified  Not specified

   We observe that the gap pseudomotor did not reach the desired position of 1
   due to the left's positioning problem. Left's position write and
   read discrepancy of 0.002 causes that the gap reached only 0.998 and that
   the offset drifted to 0.001.

#. Move gap to 2

    .. sourcecode:: spock

        Door_lab_1 [4]: mv gap 2

   The calculation of the physical motors' positions gives us 1 for right
   and 1 for left (in accordance to the **last set** offset 0).

    .. sourcecode:: spock

        Door_lab_1 [5]: wm right left gap offset
                          right           left            gap         offset
        User
         High     Not specified  Not specified  Not specified  Not specified
         Current          1.000          0.998          1.998          0.001
         Low      Not specified  Not specified  Not specified  Not specified

   We observe that the gap pseudomotor did not reach the desired position of 2
   due to the left's positioning problem. Left's position write and
   read discrepancy of 0.002 causes that the gap reached only 1.998 and that
   the offset drifted again by 0.001 but thanks to the drift correction is
   maintained at this value.

#. Move gap to 3

    .. sourcecode:: spock

        Door_lab_1 [6]: mv gap 3

   The calculation of the physical motors' positions gives us 1.5 for right
   and 1.5 for left (in accordance to the **last set** offset of 0).

    .. sourcecode:: spock

        Door_lab_1 [7]: wm right left gap offset
                          right           left            gap         offset
        User
         High     Not specified  Not specified  Not specified  Not specified
         Current          1.500          1.498          2.998          0.001
         Low      Not specified  Not specified  Not specified  Not specified

   We observe that the gap pseudomotor did not reach the desired position of 3
   due to the left's positioning problem. Left's position write and
   read discrepancy of 0.002 causes that the gap reached only 2.998 and that
   the offset drifted again by 0.001 but thanks to the drift correction is
   maintained at this value.

.. figure:: /_static/drift_correction_enabled.png
  :align: center
  :width: 680

  This sketch demonstrates the above example where offset's drift was
  corrected.
