# pyzxing

[English](README.md) | [简体中文](README_CN.md)

[![CI](https://github.com/ChenjieXu/pyzxing/actions/workflows/ci-cd.yml/badge.svg?branch=master)](https://github.com/ChenjieXu/pyzxing/actions/workflows/ci-cd.yml)
[![Documentation](https://readthedocs.org/projects/pyzxing/badge/?version=latest)](https://pyzxing.readthedocs.io/en/latest/)
[![PyPI](https://img.shields.io/pypi/v/pyzxing)](https://pypi.org/project/pyzxing/)
[![Python](https://img.shields.io/pypi/pyversions/pyzxing)](https://pypi.org/project/pyzxing/)
[![Conda-forge](https://img.shields.io/conda/vn/conda-forge/pyzxing)](https://anaconda.org/conda-forge/pyzxing)
[![Coverage](https://codecov.io/gh/ChenjieXu/pyzxing/graph/badge.svg?branch=master)](https://codecov.io/gh/ChenjieXu/pyzxing)
[![Downloads](https://img.shields.io/pypi/dm/pyzxing)](https://pypistats.org/packages/pyzxing)
[![License](https://img.shields.io/github/license/ChenjieXu/pyzxing)](LICENSE)

Reliable Python bindings for the [ZXing](https://github.com/zxing/zxing)
barcode decoder. pyzxing exposes a stable Python API while delegating decoding
to a versioned, checksum-verified Java Runner.

## Features

- Decode one image or a glob of images into one consistent result list.
- Read QR Code, Data Matrix, PDF417, Aztec, and common one-dimensional formats.
- Accept file paths and NumPy arrays.
- Preserve binary payloads, byte segments, result points, metadata, and orientation.
- Control ZXing with explicit format, charset, multi-code, and effort hints.
- Run on Linux, macOS, and Windows with Python 3.8–3.14 and Java 17+.
- Install a pinned Runner automatically, or receive it directly from conda-forge.

## Requirements

| Component | Supported versions |
| --- | --- |
| Python | 3.8–3.14 |
| Java | 17 or newer |
| Operating systems | Linux, macOS, Windows |
| ZXing runtime | 3.5.4 in pyzxing 1.2.x |

Java must be available as `java` on `PATH`. The Python package downloads the
matching Runner on first use and verifies its SHA-256 checksum. The conda-forge
package installs that Runner inside the environment.

## Installation

Install from PyPI:

```bash
python -m pip install pyzxing
```

Or install from conda-forge:

```bash
conda install -c conda-forge pyzxing
```

## Quick start

```python
from pyzxing import BarCodeReader

reader = BarCodeReader()
results = reader.decode("/path/to/qrcode.png")

for result in results:
    print(result["format"], result["text"])
```

Globs return the same flat `list[dict]` shape:

```python
results = reader.decode("/path/to/images/*.png")
```

Pass decode hints explicitly when needed:

```python
results = reader.decode(
    "/path/to/barcode.png",
    multi=True,
    try_harder=True,
    character_set="UTF-8",
    possible_formats=["QR_CODE", "DATA_MATRIX"],
)
```

## NumPy arrays

Install OpenCV and pass an RGB or grayscale array:

```bash
python -m pip install opencv-python
```

```python
results = reader.decode_array(image)
```

## Results

Every decoded barcode is represented by a dictionary. The most commonly used
fields are:

| Field | Type | Purpose |
| --- | --- | --- |
| `text` | `str` | Decoded display text. |
| `format` | `bytes` | ZXing barcode format. |
| `raw_bytes` | `bytes \| None` | Raw ZXing result bytes. |
| `byte_segments` | `list[bytes]` | Lossless QR byte-mode segments. |
| `points` | `list[tuple[float, float]]` | Result points reported by ZXing. |
| `orientation` | `int \| None` | Clockwise image rotation. |
| `metadata` | `dict` | Stable ZXing result metadata. |

The legacy byte-valued `raw` and `parsed` fields remain available for backward
compatibility. Use `byte_segments` for binary QR payloads instead of re-encoding
text.

## Documentation

The complete guide is available on
[Read the Docs](https://pyzxing.readthedocs.io/en/latest/):

- [Installation and runtime requirements](https://pyzxing.readthedocs.io/en/latest/installation.html)
- [Usage and decode hints](https://pyzxing.readthedocs.io/en/latest/usage.html)
- [Result schema](https://pyzxing.readthedocs.io/en/latest/results.html)
- [API reference](https://pyzxing.readthedocs.io/en/latest/api.html)
- [PyInstaller and deployment](https://pyzxing.readthedocs.io/en/latest/deployment.html)
- [Troubleshooting](https://pyzxing.readthedocs.io/en/latest/troubleshooting.html)

## Command-line examples

Scan a file:

```bash
python scripts/scanner.py -f /path/to/barcode.png
```

Sample frames from a webcam:

```bash
python -m pip install opencv-python
python scripts/webcam_demo.py --camera 0 --interval 0.5
```

The webcam example uses the existing one-shot `decode_array()` API. It does not
keep a persistent Java process running.

## Development

```bash
python -m pip install -e '.[dev]'
./mvnw -f java-runner/pom.xml clean verify
python -m pytest tests/
```

Use `mvnw.cmd` instead of `./mvnw` on Windows. See
[the development guide](https://pyzxing.readthedocs.io/en/latest/development.html)
for documentation builds and release checks.

## Project links

- [Documentation](https://pyzxing.readthedocs.io/)
- [Changelog](CHANGELOG.md)
- [Releases](https://github.com/ChenjieXu/pyzxing/releases)
- [Issue tracker](https://github.com/ChenjieXu/pyzxing/issues)
- [License](LICENSE)
