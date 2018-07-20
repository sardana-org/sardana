.. _sardana-configuration:

*********************
Sardana configuration
*********************

There are many configuration points in Sardana and unfortunately there is
no single configuration application neither interface to access all of them.
This guide goes step-by-step through the Sardana system configuration
process and lists all of the configuration points linking to documents with
more detailed explanation. It starts from configuration of the
:ref:`sardana-spock` client, going through the
:ref:`MacroServer<sardana-macroserver-overview>` and finally ending on the
:ref:`Device Pool <sardana-pool-overview>`.

This chapter will not document itself all the different configuration
possibilities and will just link you to other documents explaining them in
details.


.. note::
    At the time of writing, Sardana system can :ref:`run
    only as Tango device server <sardana-getting-started-running-server>`
    and most of the configurations are accessible via the Tango device
    properties. One can easily change them with the Jive client application.

.. toctree::
    :maxdepth: 2

    Spock configuration <spock>
    MacroServer configuration <macroserver>
    Device Pool configuration <pool>
    Sardana Custom Settings <sardanacustomsettings>
