.. highlight:: python
   :linenothreshold: 5
   
.. currentmodule:: sardana.macroserver.macros.hooks


.. _sardana-macros-hooks:

===========
Macro Hooks
===========

A hook is an extra code that can be run at certain points of a macro execution.
These points, called *hook places* are predefined for each *hookable* macro.
The hook place tells the macro how and when to run the attached hook.
Hooks allow the customization of already existing macros and can be added
using three different ways:

- :ref:`General Hooks <sardana-macros-hooks-general>`
- :ref:`Sequencer Hooks <sequencer_ui>`
- :ref:`Programmatic Hooks <sardana-macro-adding-hooks-support>`

All available macros can be used as a hook.

.. _sardana-macros-hooks-general:

General Hooks
-------------

The general hooks were implemented in Sardana after the programmatic hooks.
The motivation for this implementation was to allow the customization
of the scan macros without having to redefine them. The general hooks apply
to all hookable macros.

They can be controlled using dedicated macros:
:class:`~sardana.macroserver.macros.env.lsgh`,
:class:`~sardana.macroserver.macros.env.defgh` and
:class:`~sardana.macroserver.macros.env.udefgh`.
For each hook place, several hooks can be attached, they will be run in the
order they were added. The same hook can be run several times in the same
place if it was added several times.


Examples:

- Check motor limits in step scans (pre-scan)
- Prepare 2D detectors: create directories, set save directory, file name,
  file index (pre-scan)
- Set attenuators, set undulator, check shutter, check current (pre-scan)
- Restore changes (post-scan)
