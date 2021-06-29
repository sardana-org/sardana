
.. _sardana-installing:

==========
Installing
==========

Installing with pip (platform-independent)
------------------------------------------

Sardana can be installed using pip. The following command will
automatically download and install the latest release of Sardana (see
pip3 --help for options)::

       pip3 install sardana

You can test the installation by running::

       python3 -c "import sardana; print(sardana.Release.version)"

Note: Installing sardana with pip3 on Linux requires building PyTango (one of
the sardana's dependencies). You could use :ref:`sardana-getting-started-installing-in-conda`
to avoid this. If you decide to continue with pip3, please refer to
`PyTango's installation guide <https://pytango.readthedocs.io/en/stable/start.html#pypi>`_.
On Debian this should work to prepare the build environment::

        apt-get install pkg-config libboost-python-dev libtango-dev

Linux (Debian-based)
--------------------

Sardana is part of the official repositories of Debian (and Ubuntu
and other Debian-based distros). You can install it and all its dependencies by
doing (as root)::

       apt-get install python3-sardana

Note: `python3-sardana` package is available starting from the Debian 11
(Bullseye) release. For previous releases you can use `python-sardana`
(compatible with Python 2 only).

.. _sardana-getting-started-installing-in-conda:

Installing in a conda environment (platform-independent)
--------------------------------------------------------

In a conda environment (we recommend creating one specifically for sardana)::

    conda install -c conda-forge sardana

Note: for Windows, until PyTango is available on conda-forge, you may need to use
`pip3 install pytango` for installing it.

Working from Git source directly (in develop mode)
--------------------------------------------------
 
If you intend to do changes to Sardana itself, or want to try the latest
developments, it is convenient to work directly from the git source in
"develop" (aka "editable") mode, so that you do not need to re-install
on each change::

    # optional: if using a conda environment, pre-install dependencies with:
    conda install --only-deps -c conda-forge sardana

    # install sardana in develop mode
    git clone https://github.com/sardana-org/sardana.git
    pip3 install -e ./sardana  # <-- Note the -e !!

.. _dependencies:

============
Dependencies
============

Sardana depends on PyTango_, Taurus_, lxml_, itango_ and click_.
However some Sardana features require additional dependencies. For example:

- Using the Sardana Qt_ widgets, requires either PyQt_ (v4 or v5)
  or PySide_ (v1 or v2).

- The macro plotting feature requires matplotlib_

- The showscan online widget requires pyqtgraph_

- The showscan offline widget requires PyMca5_.

- The HDF5 NeXus recorder requires h5py_

- The sardana editor widget requires spyder_.


.. _PyTango: http://pytango.readthedocs.io/
.. _Taurus: http://www.taurus-scada.org/
.. _lxml: http://lxml.de
.. _itango: https://pytango.readthedocs.io/en/stable/itango.html
.. _click: https://pypi.org/project/click/
.. _Qt: http://qt.nokia.com/products/
.. _PyQt: http://www.riverbankcomputing.co.uk/software/pyqt/
.. _PySide: https://wiki.qt.io/Qt_for_Python/
.. _matplotlib: https://matplotlib.org/
.. _pyqtgraph: http://www.pyqtgraph.org/
.. _PyMca5: http://pymca.sourceforge.net/
.. _h5py: https://www.h5py.org/
.. _spyder: http://pythonhosted.org/spyder/