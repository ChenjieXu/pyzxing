# GB18030 byte-mode QR fixture

`gb18030-byte-no-eci.png` is a committed interoperability fixture for a QR
code whose payload is encoded as GB18030 bytes in a single BYTE segment and
does not contain an ECI designator. It is intentionally independent of ZXing:
the image was generated with Segno 1.6.6 under CPython 3.12.11.

Payload text: `生产许可证号：测试-123`

Payload bytes (hex):
`c9fab2fad0edbfc9d6a4bac5a3bab2e2cad42d313233`

Generation parameters:

- QR version 2
- error correction M
- mask 5
- BYTE mode
- encoding GB18030
- ECI disabled
- scale 8 and border 4

Equivalent generator call:

```python
encoded = "生产许可证号：测试-123".encode("gb18030")
qr = segno.make(
    encoded,
    error="M",
    mode="byte",
    encoding="gb18030",
    eci=False,
    micro=False,
    boost_error=False,
)
qr.save(
    "gb18030-byte-no-eci.png",
    kind="png",
    scale=8,
    border=4,
    dark="#000",
    light="#fff",
)
```

The fixture SHA256 is
`ee4aa39fbfabbcbce4e41f9d6d7f3c1cc59af89c4ba09a9e43719fc34d828398`.
The machine-readable copy of this provenance is in `metadata.json`.
