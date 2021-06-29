.. _pctv:

PoolChannelTV User’s Interface
------------------------------

Sardana provides a widget to display and operate any Sardana channel.
As all Taurus widget it needs at least a model, but several can be given
to this widget. The widget exports the Sardana channel models as Taurus attributes.

The :class:`~sardana.taurus.qt.qtgui.extra_pool.poolchannel.PoolChannelTV`
allows:

    - Start :ref:`experimental channel acquisition<sardana-acquisition-expchannel>`
      after prior setting of integration time
    - Stop the acquisition
    - Monitor the channel's value while acquiring or after the acquisition

.. image:: /_static/pctv.png
    :align: center

Moreover, this widget allows you to access to the channel's configuration via a
context menu (right-click over the channel name) - see the image bellow.

.. image:: /_static/pctv_attr_editor.png
    :align: center







