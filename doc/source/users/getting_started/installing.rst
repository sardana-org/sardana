
.. _sardana-installing:

==========
Installing
==========

Installing with pip [1]_ (platform-independent)
--------------------------------------------------------

Sardana can be installed using pip. The following command will
automatically download and install the latest release of Sardana (see
pip3 --help for options)::

       pip3 install sardana

You can test the installation by running::

       python3 -c "import sardana; print(sardana.Release.version)"

If you want macro server environment based on redis you also need::

       pip3 install sardana[redis]


Installing from PyPI manually [2]_ (platform-independent)
---------------------------------------------------------

You may alternatively install from a downloaded release package:

#. Download the latest release of Sardana from http://pypi.python.org/pypi/sardana
#. Extract the downloaded source into a temporary directory and change to it
#. run::

       python3 setup.py install

You can test the installation by running::

       python3 -c "import sardana; print(sardana.Release.version)"

Linux (Debian-based)
--------------------

Since v1.4, Sardana is part of the official repositories of Debian (and Ubuntu
and other Debian-based distros). You can install it and all its dependencies by
doing (as root)::

       aptitude install python-sardana

You can test the installation by running::

       python3 -c "import sardana; print(sardana.Release.version)"

(see more detailed instructions in `this step-by-step howto
<https://sourceforge.net/p/sardana/wiki/Howto-Sardana-on-Debian8/>`__)


Windows
-------

#. Download the latest windows binary from https://github.com/sardana-org/sardana/releases
#. Run the installation executable
#. test the installation::

       C:\Python35\python3 -c "import sardana; print(sardana.Release.version)"

Windows installation shortcut
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This chapter provides a quick shortcut to all windows packages which are
necessary to run Sardana on your windows machine

#. Install all dependencies:

	#. Download and install latest `PyTango`_ from `PyTango downdoad page <http://pypi.python.org/pypi/PyTango>`_
	#. Download and install latest `Taurus`_ from `Taurus downdoad page <http://pypi.python.org/pypi/taurus>`_
	#. Download and install latest `lxml`_ from `lxml downdoad page <http://pypi.python.org/pypi/lxml>`_
	#. Download and install latest itango from `itango download page <http://pypi.python.org/pypi/itango>`_

#. Finally download and install latest Sardana from `Sardana downdoad page <http://pypi.python.org/pypi/sardana>`_

=========================
Working directly from Git
=========================
 
If you intend to do changes to Sardana itself, or want to try the latest
developments, it is convenient to work directly from the git source in
"develop" (aka "editable") mode, so that you do not need to re-install
on each change.

You can clone sardana from the main git repository::

    git clone https://github.com/sardana-org/sardana.git sardana

Then, to work in editable mode, just do::

    pip3 install -e ./sardana

Note that you can also fork the git repository in github to get your own
github-hosted clone of the sardana repository to which you will have full
access. This will create a new git repository associated to your personal account in
github, so that your changes can be easily shared and eventually merged
into the official repository.


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

.. [1] This command requires super user previledges on linux systems. If your
       user has them you can usually prefix the command with *sudo*:
       ``sudo pip3 -U sardana``. Alternatively, if you don't have
       administrator previledges, you can install locally in your user
       directory with: ``pip3 --user sardana``
       In this case the executables are located at <HOME_DIR>/.local/bin. Make
       sure the PATH is pointing there or you execute from there.

.. [2] *setup.py install* requires user previledges on linux systems. If your
       user has them you can usually prefix the command with *sudo*: 
       ``sudo python3 setup.py install``. Alternatively, if you don't have
       administrator previledges, you can install locally in your user directory
       with: ``python3 setup.py install --user``
       In this case the executables are located at <HOME_DIR>/.local/bin. Make
       sure the PATH is pointing there or you execute from there.

.. [3] PyTango < 9 is compatible with itango >= 0.0.1 and < 0.1.0,
       while higher versions with itango >= 0.1.6.

.. _lxml: http://lxml.de
.. _SardanaPypi: http://pypi.python.org/pypi/sardana/
.. _Tango: http://www.tango-controls.org/
.. _PyTango: http://pytango.readthedocs.io/
.. _Taurus: http://www.taurus-scada.org/
