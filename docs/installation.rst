Installation
============

Requirements
------------

pyzxing supports Python 3.8 through 3.14 on Linux, macOS, and Windows. Java 17
or newer must be available as ``java`` on ``PATH``.

PyPI
----

Install the Python package with pip:

.. code-block:: console

   python -m pip install pyzxing

On first use, pyzxing downloads the Runner that matches the package version.
The download is accepted only when its SHA-256 checksum matches the value
shipped in the Python package.

conda-forge
-----------

The conda-forge package installs Python, Java, and the matching Runner into the
same environment:

.. code-block:: console

   conda install -c conda-forge pyzxing

Installing from source
----------------------

.. code-block:: console

   git clone https://github.com/ChenjieXu/pyzxing.git
   cd pyzxing
   python -m pip install .

Installing the source tree does not build the Java Runner automatically.
Normal development builds use the Maven wrapper described in
:doc:`development`.
