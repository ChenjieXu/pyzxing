Deployment
==========

Runner cache
------------

The PyPI package downloads its versioned Runner on first use and stores it in a
platform-appropriate user cache. Concurrent writers use a lock and the final
file is accepted only after checksum verification.

For deterministic deployments, download the Runner from the matching GitHub
Release and pass its path explicitly:

.. code-block:: python

   reader = BarCodeReader(jar_path="/opt/pyzxing/pyzxing-runner.jar")

PyInstaller
-----------

Bundle the Runner as data and locate it through ``sys._MEIPASS`` at runtime:

.. code-block:: console

   pyinstaller --add-data "/path/to/pyzxing-runner.jar:runner" app.py

Use ``;runner`` instead of ``:runner`` on Windows.

.. code-block:: python

   import sys
   from pathlib import Path

   from pyzxing import BarCodeReader

   bundle_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
   runner_jar = next((bundle_dir / "runner").glob("*.jar"))
   reader = BarCodeReader(jar_path=runner_jar)

Containers
----------

Install a Java 17 runtime in the image and warm the Runner cache during the
image build, or copy a verified Runner into the image and use ``jar_path``.
Applications should keep the cache directory writable when relying on automatic
download.

Webcam example
--------------

``scripts/webcam_demo.py`` periodically samples frames and calls
``decode_array()``. It is a demonstration of the one-shot API, not a persistent
streaming JVM service.
