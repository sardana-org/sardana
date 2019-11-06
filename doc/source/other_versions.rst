
===============================
Docs for other Sardana versions
===============================

The `main Sardana docs <http://sardana-controls.org>`_ are generated for the
most recent development version.

You can still generate the docs for other versions of Sardana. In order to do that
you first need to clone the `Sardana repository <https://github.com/sardana-org/sardana>`_,
checkout the necessary version and simply build the docs.

In continuation you can find an example of how to do it for version ``2.8.3``:

.. code-block:: console

    git clone -b 2.8.3 https://github.com/sardana-org/sardana
    cd sardana
    python setup.py build_sphinx
    firefox build/sphinx/html/index.html

.. note::
   Sardana versions >= 3 work only with Python 3. Then you will need to build
   the documentation with ``python3`` instead of ``python``.
