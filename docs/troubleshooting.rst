Troubleshooting
===============

Java was not found
------------------

Install Java 17 or newer and verify it is visible to the same process that runs
Python:

.. code-block:: console

   java -version

On Windows, restart the terminal after changing ``PATH``.

Runner download fails
---------------------

Check access to GitHub Releases and write access to the user cache directory.
pyzxing will not use a partially downloaded file or a Runner whose SHA-256 does
not match the package configuration.

No files found
--------------

``decode()`` expands user paths and globs. Quote shell patterns so Python, rather
than the shell, receives the pattern:

.. code-block:: python

   reader.decode("images/*.png")

Binary QR text looks corrupted
------------------------------

Use ``result["byte_segments"]`` for arbitrary binary payloads. ``text`` is a
display string and cannot always be converted back to the original bytes.

NumPy decoding cannot import OpenCV
-----------------------------------

Install OpenCV in the environment that imports pyzxing:

.. code-block:: console

   python -m pip install opencv-python

Timeouts or large files
-----------------------

Construct ``BarCodeReader(timeout=...)`` to change the per-process timeout.
``DecodeTimeoutError`` and ``FileTooLargeError`` allow applications to handle
these cases separately from other ``DecodeError`` failures.
