.. highlight:: python
   :linenothreshold: 5
   
.. currentmodule:: sardana.macroserver.macros.hooks


.. _sardana-macros-hooks:

===========
Macro Hooks
===========

A hook is an extra code that can be run at certain points of a macro execution.
These points are predefined for each hookable macro and passed via a "hints" mechanism.
The hint tells the macro how and when to run the attached hook.
Hooks allow the customization of already existing macros and can be added using
three different ways:

- General Hooks
- :ref:`Sequencer Hooks <sequencer_ui>`
- :ref:`Programmatic Hooks <sardana-macros-scanframework>`

All available macros can be used as a hook.
  
General Hooks
-------------

The general hooks were implemented in Sardana after the programmatic hooks.
The motivation for this implementation was to allow the customization
of the scan macros without having to redefine them.
The general hooks apply to all hookable macros and allow the definition
of new hints.
They can be controlled using dedicated macros: :class:`~sardana.macroserver.macros.env.lsgh`,
:class:`~sardana.macroserver.macros.env.defgh` and :class:`~sardana.macroserver.macros.env.udefgh`.
For each hook position, hint, several hooks can be run, they will be run in the
order they were added. The same hook can be run several times in the same position
if it's added several times.

Examples:

- Check motor limits in step scans (pre-scan)
- Prepare 2D detectors: create directories, set save directory, file name,
  file index (pre-scan)
- Set attenuators, set undulator, check shutter, check current (pre-scan)
- Restore changes (post-scan)
