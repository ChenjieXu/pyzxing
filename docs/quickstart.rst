Quick start
===========

Create a reader and decode one image:

.. code-block:: python

   from pyzxing import BarCodeReader

   reader = BarCodeReader()
   results = reader.decode("/path/to/qrcode.png")

   for result in results:
       print(result["format"], result["text"])

``decode()`` always returns a flat list. For backward compatibility, a file
containing no barcode contributes a dictionary containing only ``filename``;
a glob combines the per-file results from every matching file:

.. code-block:: python

   results = reader.decode("/path/to/images/*.png")

Limit decoding to selected formats when the input domain is known:

.. code-block:: python

   results = reader.decode(
       "/path/to/image.png",
       possible_formats=["QR_CODE", "DATA_MATRIX"],
   )

See :doc:`usage` for all hints and :doc:`results` for the returned fields.
