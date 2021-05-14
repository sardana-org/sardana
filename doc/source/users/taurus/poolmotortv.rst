.. _pmtv:

PoolMotorTV User’s Interface
-----------------------------

Sardana provides a widget to display and operate any Sardana moveables.
As all Taurus widget it needs at least a model, but several can be given
to this widget,
The widget exports the Sardana moveable models as Taurus attributes.

The :class:`~sardana.taurus.qt.qtgui.extra_pool.poolmotor.PoolMotorTV`
allows:

    - Move relative/absolute any moveable to a set point
    - Abort a movement
    - or simply monitor the moveables

.. image:: /_static/pmtv.png
    :align: center

Moreover, this widget allows you to access to the moveable configuration via a
context menu (right-click over the moveable name) See the image bellow. Also you
can enable the ``expert mode`` option in the same context menu. This option
add new buttons under the line edit of the setting point. These buttons allows
you to move the moveable to their limits (with just one click) or move it
in a direction when the button is pressed but **only** if limits have
been configured.

.. image:: /_static/pmtv_attr_editor.png
    :align: center







