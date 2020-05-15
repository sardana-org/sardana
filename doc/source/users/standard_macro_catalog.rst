
.. _sardana-standard-macro-catalog:

======================
Standard macro catalog
======================

motion related macros
---------------------

.. hlist::
    :columns: 5

    * :class:`~sardana.macroserver.macros.standard.wa`
    * :class:`~sardana.macroserver.macros.standard.wm`
    * :class:`~sardana.macroserver.macros.standard.pwa`
    * :class:`~sardana.macroserver.macros.standard.pwm`
    * :class:`~sardana.macroserver.macros.standard.set_lim`
    * :class:`~sardana.macroserver.macros.standard.set_lm`
    * :class:`~sardana.macroserver.macros.standard.set_pos`
    * :class:`~sardana.macroserver.macros.standard.mv`
    * :class:`~sardana.macroserver.macros.standard.umv`
    * :class:`~sardana.macroserver.macros.standard.mvr`
    * :class:`~sardana.macroserver.macros.standard.umvr`
    * :class:`~sardana.macroserver.macros.standard.tw`
    * :class:`~sardana.macroserver.macros.lists.lsm`
    * :class:`~sardana.macroserver.macros.lists.lspm`

counting macros
---------------

.. hlist::
    :columns: 5
    
    * :class:`~sardana.macroserver.macros.standard.ct`
    * :class:`~sardana.macroserver.macros.standard.uct`
    * :class:`~sardana.macroserver.macros.standard.settimer`
    * :class:`~sardana.macroserver.macros.lists.lsexp`
    * :class:`~sardana.macroserver.macros.lists.lsmeas`
    * :class:`~sardana.macroserver.macros.lists.lsct`
    * :class:`~sardana.macroserver.macros.lists.ls0d`
    * :class:`~sardana.macroserver.macros.lists.ls1d`
    * :class:`~sardana.macroserver.macros.lists.ls2d`
    * :class:`~sardana.macroserver.macros.lists.lspc`

diffractometer related macros
-----------------------------
.. _sardana-diffractometer-macros:

.. hlist::
    :columns: 5

    * :class:`~sardana.macroserver.macros.hkl.addreflection`
    * :class:`~sardana.macroserver.macros.hkl.affine`
    * :class:`~sardana.macroserver.macros.hkl.br`
    * :class:`~sardana.macroserver.macros.hkl.ca`
    * :class:`~sardana.macroserver.macros.hkl.caa`
    * :class:`~sardana.macroserver.macros.hkl.ci`
    * :class:`~sardana.macroserver.macros.hkl.computeub`
    * :class:`~sardana.macroserver.macros.hkl.freeze`
    * :class:`~sardana.macroserver.macros.hkl.getmode`
    * :class:`~sardana.macroserver.macros.hkl.hklscan`
    * :class:`~sardana.macroserver.macros.hkl.hscan`
    * :class:`~sardana.macroserver.macros.hkl.kscan`
    * :class:`~sardana.macroserver.macros.hkl.latticecal`
    * :class:`~sardana.macroserver.macros.hkl.loadcrystal`
    * :class:`~sardana.macroserver.macros.hkl.lscan`
    * :class:`~sardana.macroserver.macros.hkl.newcrystal`
    * :class:`~sardana.macroserver.macros.hkl.or0`
    * :class:`~sardana.macroserver.macros.hkl.or1`
    * :class:`~sardana.macroserver.macros.hkl.orswap`
    * :class:`~sardana.macroserver.macros.hkl.pa`
    * :class:`~sardana.macroserver.macros.hkl.savecrystal`
    * :class:`~sardana.macroserver.macros.hkl.setaz`
    * :class:`~sardana.macroserver.macros.hkl.setlat`
    * :class:`~sardana.macroserver.macros.hkl.setmode`
    * :class:`~sardana.macroserver.macros.hkl.setor0`
    * :class:`~sardana.macroserver.macros.hkl.setor1`
    * :class:`~sardana.macroserver.macros.hkl.setorn`
    * :class:`~sardana.macroserver.macros.hkl.th2th`
    * :class:`~sardana.macroserver.macros.hkl.ubr`
    * :class:`~sardana.macroserver.macros.hkl.wh`

environment related macros
--------------------------

.. hlist::
    :columns: 5
    
    * :class:`~sardana.macroserver.macros.env.lsenv`
    * :class:`~sardana.macroserver.macros.env.senv`
    * :class:`~sardana.macroserver.macros.env.usenv`
    * :class:`~sardana.macroserver.macros.env.dumpenv`

list related macros
-------------------

.. hlist::
    :columns: 5

    * :class:`~sardana.macroserver.macros.env.lsenv`
    * :class:`~sardana.macroserver.macros.lists.lsa`
    * :class:`~sardana.macroserver.macros.lists.lsm`
    * :class:`~sardana.macroserver.macros.lists.lspm`
    * :class:`~sardana.macroserver.macros.lists.lsexp`
    * :class:`~sardana.macroserver.macros.lists.lsior`
    * :class:`~sardana.macroserver.macros.lists.lsmeas`
    * :class:`~sardana.macroserver.macros.lists.lsct`
    * :class:`~sardana.macroserver.macros.lists.ls0d`
    * :class:`~sardana.macroserver.macros.lists.ls1d`
    * :class:`~sardana.macroserver.macros.lists.ls2d`
    * :class:`~sardana.macroserver.macros.lists.lspc`
    * :class:`~sardana.macroserver.macros.lists.lsctrl`
    * :class:`~sardana.macroserver.macros.lists.lsi`
    * :class:`~sardana.macroserver.macros.lists.lsctrllib`
    * :class:`~sardana.macroserver.macros.lists.lsa`
    * :class:`~sardana.macroserver.macros.lists.lsmac`
    * :class:`~sardana.macroserver.macros.lists.lsmaclib`
    * :class:`~sardana.macroserver.macros.env.lsgh`
    * :class:`~sardana.macroserver.macros.env.lssnap`

experiment configuration macros
--------------------------------

.. hlist::
    :columns: 5

    * :class:`~sardana.macroserver.macros.expert.defmeas`
    * :class:`~sardana.macroserver.macros.expert.udefmeas`
    * :class:`~sardana.macroserver.macros.expconf.set_meas`
    * :class:`~sardana.macroserver.macros.expconf.get_meas`
    * :class:`~sardana.macroserver.macros.expconf.set_meas_conf`
    * :class:`~sardana.macroserver.macros.expconf.get_meas_conf`
    * :class:`~sardana.macroserver.macros.expconf.defsnap`
    * :class:`~sardana.macroserver.macros.expconf.udefsnap`
    * :class:`~sardana.macroserver.macros.expconf.lssnap`

general hooks macros
--------------------

.. hlist::
    :columns: 5

    * :class:`~sardana.macroserver.macros.env.lsgh`
    * :class:`~sardana.macroserver.macros.env.defgh`
    * :class:`~sardana.macroserver.macros.env.udefgh`

advanced element manipulation macros
------------------------------------

.. hlist::
    :columns: 5

    * :class:`~sardana.macroserver.macros.expert.defelem`
    * :class:`~sardana.macroserver.macros.expert.udefelem`
    * :class:`~sardana.macroserver.macros.expert.renameelem`
    * :class:`~sardana.macroserver.macros.expert.defctrl`
    * :class:`~sardana.macroserver.macros.expert.udefctrl`
    * :class:`~sardana.macroserver.macros.expert.prdef`

reload code macros
------------------

.. hlist::
    :columns: 5

    * :class:`~sardana.macroserver.macros.expert.relmac`
    * :class:`~sardana.macroserver.macros.expert.relmaclib`
    * :class:`~sardana.macroserver.macros.expert.addmaclib`
    * :class:`~sardana.macroserver.macros.expert.rellib`
    * :class:`~sardana.macroserver.macros.expert.relctrlcls`
    * :class:`~sardana.macroserver.macros.expert.relctrllib`
    * :class:`~sardana.macroserver.macros.expert.addctrllib`

scan macros
-----------

.. hlist::
    :columns: 5

    * :class:`~sardana.macroserver.macros.scan.ascan`
    * :class:`~sardana.macroserver.macros.scan.a2scan`
    * :class:`~sardana.macroserver.macros.scan.a3scan`
    * :class:`~sardana.macroserver.macros.scan.a4scan`
    * :class:`~sardana.macroserver.macros.scan.amultiscan`
    * :class:`~sardana.macroserver.macros.scan.dscan`
    * :class:`~sardana.macroserver.macros.scan.d2scan`
    * :class:`~sardana.macroserver.macros.scan.d3scan`
    * :class:`~sardana.macroserver.macros.scan.d4scan`
    * :class:`~sardana.macroserver.macros.scan.dmultiscan`
    * :class:`~sardana.macroserver.macros.scan.mesh`
    * :class:`~sardana.macroserver.macros.scan.fscan`
    * :class:`~sardana.macroserver.macros.scan.scanhist`

    * :class:`~sardana.macroserver.macros.scan.ascanc`
    * :class:`~sardana.macroserver.macros.scan.a2scanc`
    * :class:`~sardana.macroserver.macros.scan.a3scanc`
    * :class:`~sardana.macroserver.macros.scan.a4scanc`
    * :class:`~sardana.macroserver.macros.scan.dscanc`
    * :class:`~sardana.macroserver.macros.scan.d2scanc`
    * :class:`~sardana.macroserver.macros.scan.d3scanc`
    * :class:`~sardana.macroserver.macros.scan.d4scanc`
    * :class:`~sardana.macroserver.macros.scan.meshc`

    * :class:`~sardana.macroserver.macros.scan.ascanct`
    * :class:`~sardana.macroserver.macros.scan.a2scanct`
    * :class:`~sardana.macroserver.macros.scan.a3scanct`
    * :class:`~sardana.macroserver.macros.scan.a4scanct`
    * :class:`~sardana.macroserver.macros.scan.dscanct`
    * :class:`~sardana.macroserver.macros.scan.d2scanct`
    * :class:`~sardana.macroserver.macros.scan.d3scanct`
    * :class:`~sardana.macroserver.macros.scan.d4scanct`

scan related macros
-------------------

.. hlist::
    :columns: 5

    * :class:`~sardana.macroserver.macros.standard.newfile`
