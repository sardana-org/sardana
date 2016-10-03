.. currentmodule:: sardana.pool.controller

.. _sardana-pseudocountercontroller-howto-basics:

========================================
How to write a pseudo counter controller
========================================

The basics
----------

An example of a X-ray beam position monitor (XBPM) pseudo counter controller
will be build incrementally from scratch to aid in the explanation. Its purpose
is to provide an easy feedback about the beam position in the vertical and
horizontal axes as well as the total intensity of the beam.

By now you should have read the general controller basics chapter. Let's start
from writing a :class:`~sardana.pool.controller.PseudoCounterController`
subclass with a proper constructor and the roles defined.

.. code-block:: python

    from sardana.pool.controller import PseudoCounterController

    class XBPMPseudoCounterController(PseudoCounterController):

        counter_roles = ('top', 'bottom', 'right', 'left')
        pseudo_counter_roles = ('vertical', 'horizontal', 'total')

        def __init__(self, inst, props, *args, **kwargs):
            super(XBPMPseudoCounterController, self).__init__(inst, props, *args, **kwargs)

The :obj:`~sardana.pool.controller.PseudoCounterController.counter_roles` and
:obj:`~sardana.pool.controller.PseudoCounterController.pseudo_counter_roles`
tuples contains names of the counter and pseudo counter roles respectively.
These names are used when creating the controller instance and their order is
important when writing the controller itself. Each controller will define its
own roles.

The constructor does nothing apart of calling the parent class constructor but
could be used to implement any necessary initialization.

The pseudo counter calculations are implemented in the
:meth:`~sardana.pool.controller.PseudoCounterController.calc` method:

.. code-block:: python

    def calc(self, index, counter_values):
        top, bottom, right, left = counter_values

        if index == 1: # vertical
            vertical = (top - bottom)/(top + bottom)
            return vertical
        elif index == 2: # horizontal
            horizontal = (right - left)/(right + left)
            return horizontal
        elif index == 3: # total
            total = (top + bottom + right + left) / 4
            return total

From the implementation we can conclude that the vertical pseudo counter will
give values from -1 to 1 depending on the beam position in the vertical
dimension. If the beam passes closer to the top sensor, the value will be more
positive. If the beam passes closer to the bottom sensor the value will be more
negative. The value close to the zero indicates the beam centered in the middle.
Similarly behaves the horizontal pseudo counter. The total pseudo counter is
the mean value of all the four sensors and indicates the beam intensity.

Including external variables in the calculation
-----------------------------------------------

The pseudo counter calculation may require an arbitrary variable which is not
a counter value. One can use Taurus_ or PyTango_ libraries in order to
read their attributes and use them in the calculation. It is even possible
to write pseudo counters not based at all on the counters. In this case it is
enough to define an empty
:obj:`~sardana.pool.controller.PseudoCounterController.counter_roles` tuple.

.. _sardana-motorcontroller-howto-axis-state:

.. _PyTango: http://packages.python.org/PyTango/
.. _Taurus: http://packages.python.org/taurus/
