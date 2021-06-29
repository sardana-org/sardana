###########
What's new?
###########

Below you will find the most relevant news that brings the Sardana releases.
For a complete list of changes consult the Sardana `CHANGELOG.md \
<https://github.com/sardana-org/sardana/blob/develop/CHANGELOG.md>`_ file.

****************************
What's new in Sardana 3.1.1?
****************************

Date: 2021-06-11

Type: hotfix release

Fixed
=====

- Correctly handle stop/abort of macros e.g. ``Ctrl+c`` in Spock in case
  the macro was executing another hooked macros e.g. a scan executing a general
  hook.

**************************
What's new in Sardana 3.1?
**************************

Date: 2021-05-17 (*Jan21* milestone)

Type: biannual stable release

It is backwards compatible and comes with new features, changes and bug fixes.

.. note::

    This release, in comparison to the previous ones, brings significant
    user experience improvements when used on Windows.

Added
=====

- *HDF5 write session*, in order to avoid the file locking problems and to introduce
  the SWMR mode support. It enables safe introspection e.g.: using data
  analysis tools like PyMCA or silx, custom scripts, etc. of the scan data files
  written in the `HDF5 data format <https://www.hdfgroup.org/solutions/hdf5/>`_
  while scanning.
  You can control the session using e.g.:
  `~sardana.macroserver.macros.h5storage.h5_start_session` and
  `~sardana.macroserver.macros.h5storage.h5_end_session` macros
  or the `~sardana.macroserver.macros.h5storage.h5_write_session`
  context manager.
  More information in the :ref:`NXscanH5_FileRecorder documentation \
  <sardana-users-scan-data-storage-nxscanh5_filerecorder>`
- *scan information* and *scan point* forms to the *showscan online* widget.
  See example in the :ref:`showscan online screenshot \
  <showscan-online-infopanels-figure>`.
- Handle `pre-move` and `post-move` hooks by: `mv`, `mvr`, `umv`, `umvr`,
  `br` and `ubr` macros.
  You may use `~sardana.sardanacustomsettings.PRE_POST_MOVE_HOOK_IN_MV`
  for disabling these hooks.
- Include trigger/gate (synchronizer) elements in the per-measurement preparation.
  This enables possible dead time optimization in hardware synchronized step scans.
  More information in the :ref:`How to write a trigger/gate controller documentation \
  <sardana-TriggerGateController-howto-prepare>`.
- :ref:`scanuser` environment variable.
- Support to `PosFormat` :ref:`ViewOption <sardana-spock-viewoptions>` in `umv` macro.
- Avoid double printing of user units in :ref:`pmtv`: read widget and
  units widget.
- Print of allowed :ref:`sardana-macros-hooks` when :ref:`sardana-spock-gettinghelp`
  on macros in Spock.
- Documentation:

    - :ref:`sardana-1dcontroller-howto` and :ref:`sardana-2dcontroller-howto`
    - :ref:`sardana-countertimercontroller` now contains the `SEP18 \
      <http://www.sardana-controls.org/sep/?SEP18.md>`_ concepts.
    - Properly :ref:`sardana-macro-exception-handling` in macros in order
      to not interfere with macro stopping/aborting
    - :ref:`faq_how_to_access_tango_from_macros_and_controllers`
    - Update :ref:`Installation instructions <sardana-installing>`

Changed
=======

- Experimental channel's shape is now considered as a result of the configuration
  e.g. RoI, binning, etc. and not part of the measurement group configuration:

  - Added :ref:`shape controller axis parameter (plugin) <sardana-2dcontroller-general-guide-shape>`,
    `shape` experimental channel attribute (kernel)
    and `Shape` Tango attribute to the experimental channels
  - **Removed** the *shape* column from the measurement group's configuration panel
    in :ref:`expconf_ui`.

Fixed
=====

- Sardana server (standalone) startup is more robust.
- Storing string values in *datasets*, *pre-scan snapshot* and *custom data*
  in :ref:`sardana-users-scan-data-storage-nxscanh5_filerecorder`.
- Stopping/aborting grouped movement when backlash correction would be applied.
- Randomly swapping target positions in grouped motion when moveables proceed
  from various Device Pool's.
- Enables possible dead time optimization in `mesh` scan macro by executing
  :ref:`per measurement preparation <sardana-macros-scanframework-determscan>`.
- Continuously read experimental channel's value references in hardware
  synchronized acquisition instead of reading only once at the end.
- Problems when :ref:`sardana-controller-howto-change-default-interface` of standard attributes
  in controllers e.g. shape of the pseudo counter's Value attribute.
- :ref:`sequencer_ui` related bugs:

    * Fill Macro's `parent_macro` in case of executing XML hooks in sequencer
    * Problems with macro id's when executing sequences loaded from *plain text* files with spock syntax
    * Loading of sequences using macro functions from *plain text* files with spock syntax
- Apply position formatting (configured with `PosFormat`
  :ref:`ViewOption <sardana-spock-viewoptions>`) to the limits in the `wm` macro.
