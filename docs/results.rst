Result schema
=============

Each decoded barcode is a dictionary. Text, bytes, geometry, and metadata are
kept separate so callers do not need to reconstruct binary information from a
display string.

Core fields
-----------

``filename`` (``bytes``)
   Absolute input file URI encoded as UTF-8 bytes.

``format`` (``bytes``)
   ZXing barcode format, for example ``b"QR_CODE"``.

``type`` (``bytes``)
   Parsed-result type reported by ZXing.

``text`` and ``parsed_text`` (``str``)
   Decoded text and parsed display text.

``raw`` and ``parsed`` (``bytes``)
   Backward-compatible UTF-8 byte fields.

Binary fields
-------------

``raw_bytes`` (``bytes | None``)
   Raw result bytes exposed by ZXing.

``byte_segments`` (``list[bytes]``)
   Lossless QR byte-mode segments. Use these values for arbitrary binary QR
   payloads instead of encoding ``text`` again.

Geometry and metadata
---------------------

``points`` (``list[tuple[float, float]]``)
   Result points in image coordinates.

``orientation`` (``0 | 90 | 180 | 270 | None``)
   Normalized clockwise image rotation when a reliable value is available.

``orientation_source`` (``str``)
   ``metadata``, ``derived``, or ``unavailable``.

``metadata`` (``dict``)
   Stable ZXing metadata. A raw ZXing orientation value is preserved here even
   when the public orientation field uses normalized image-rotation semantics.

Example
-------

.. code-block:: python

   result = reader.decode("payload.png")[0]
   print(result["text"])
   for segment in result["byte_segments"]:
       consume_binary_payload(segment)
