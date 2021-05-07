
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
the sardana's dependencies). You could use :ref:`sardana-getting-started-installing-in-conda`_
to avoid this. If you decide ton continue with pip3, please refer to
`PyTango's installation guide <https://pytango.readthedocs.io/en/stable/start.html#pypi>`_.
On Debian this should work to prepare the build environment::

        apt-get install pkg-config libboost-python-dev libtango-dev

Linux (Debian-based)
--------------------

Sardana is part of the official repositories of Debian (and Ubuntu
and other Debian-based distros). You can install it and all its dependencies by
doing (as root)::

       apt-get install python3-sardana

You can test the installation by running::

       python3 -c "import sardana; print(sardana.Release.version)"


Note: `python3-sardana` package is available starting from the Debian 11
(Bullseye) release. For previous releases you can use `python-sardana`
(compatible with Python 2 only).

.. _sardana-getting-started-installing-in-conda:

Installing in a conda environment (platform-independent)
--------------------------------------------------------

In a conda environment (we recommend creating one specifically for sardana)::

    conda install -c conda-forge -c sardana

Note: for Windows, until PyTango is available on conda-forge, you may need to use
`pip install pytango` for installing it.

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

Sardana has dependencies on some python libraries:

- Sardana uses Tango as the middleware so you need PyTango_ 9.2.5 or later
  installed. You can check it by doing::

    python3 -c 'import tango; print(tango.__version__)'

- Sardana clients are developed with Taurus so you need Taurus_ 4.5.4 or later
  installed. You can check it by doing::

      python3 -c 'import taurus; print(taurus.Release.version)'

- Sardana operate some data in the XML format and requires lxml_ library 2.3 or
  later. You can check it by doing::

      python3 -c 'import lxml.etree; print(lxml.etree.LXML_VERSION)'

- spock (Sardana CLI) requires itango 0.1.6 or later [3]_.


.. rubric:: Footnotes

.. [3] PyTango < 9 is compatible with itango >= 0.0.1 and < 0.1.0,
       while higher versions with itango >= 0.1.6.

.. _lxml: http://lxml.de
.. _SardanaPypi: http://pypi.python.org/pypi/sardana/
.. _Tango: http://www.tango-controls.org/
.. _PyTango: http://pytango.readthedocs.io/
.. _Taurus: http://www.taurus-scada.org/
