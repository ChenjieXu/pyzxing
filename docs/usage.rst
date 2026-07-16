Usage
=====

Files and globs
---------------

``BarCodeReader.decode()`` accepts a path or a glob pattern. Paths are expanded,
made absolute, sorted, and decoded without invoking a shell. Missing matches
raise ``FileNotFoundError``.

.. code-block:: python

   reader.decode("invoice.png")
   reader.decode("incoming/*.png")

Decode hints
------------

The keyword-only hints map to explicit ZXing behavior:

``multi``
   Search for multiple barcodes in each image. Defaults to ``True``.

``try_harder``
   Ask ZXing to spend more effort locating a barcode. Defaults to ``True``.

``pure_barcode``
   Treat the input as a clean monochrome barcode without surrounding content.

``character_set``
   Supply a character-set hint when the symbol does not declare one.

``possible_formats``
   Restrict decoding to ZXing ``BarcodeFormat`` names such as ``QR_CODE``,
   ``DATA_MATRIX``, ``PDF_417``, ``AZTEC``, ``CODE_128``, or ``EAN_13``.

.. code-block:: python

   results = reader.decode(
       "label.png",
       multi=False,
       try_harder=True,
       pure_barcode=False,
       character_set="UTF-8",
       possible_formats=["CODE_128", "QR_CODE"],
   )

NumPy arrays
------------

Install OpenCV to use ``decode_array()``:

.. code-block:: console

   python -m pip install opencv-python

The method accepts a grayscale array or an RGB array, writes a temporary PNG,
and delegates to the same decode path:

.. code-block:: python

   results = reader.decode_array(image)

The temporary file is removed whether decoding succeeds or fails.

Errors and timeouts
-------------------

``JavaNotFoundError`` is raised during reader construction when Java is not on
``PATH``. Runtime failures use ``DecodeError`` and preserve the Runner error
code in ``exception.code``. ``DecodeTimeoutError`` and ``FileTooLargeError``
identify timeout and size-limit failures explicitly.
