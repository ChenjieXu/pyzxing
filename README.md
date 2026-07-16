# pyzxing

English | [简体中文](README_CN.md)

[![PyPI](https://img.shields.io/pypi/v/pyzxing)](https://pypi.org/project/pyzxing/)
[![Conda-forge](https://img.shields.io/conda/v/conda-forge/pyzxing)](https://anaconda.org/conda-forge/pyzxing)
![PyPI - Downloads](https://img.shields.io/pypi/dm/pyzxing)
![GitHub Repo stars](https://img.shields.io/github/stars/chenjiexu/pyzxing)

Python bindings for the [ZXing](https://github.com/zxing/zxing) barcode decoder.
PyZXing supports single and multiple barcodes, file globs, NumPy arrays, decode
hints, binary payloads, result points, and orientation metadata.

## Requirements

- Python 3.8 or newer
- Java 17 or newer on `PATH`

PyZXing downloads and verifies its matching Java Runner automatically. The
conda-forge package includes the Runner in the environment.

## Installation

```bash
pip install pyzxing
```

or:

```bash
conda install -c conda-forge pyzxing
```

To install the current source tree:

```bash
git clone https://github.com/ChenjieXu/pyzxing.git
cd pyzxing
python -m pip install .
```

## Quick start

```python
from pyzxing import BarCodeReader

reader = BarCodeReader()

results = reader.decode("/path/to/barcode.png")
print(results)

# Decode all matching images and return one flat result list.
results = reader.decode("/path/to/images/*.png")
```

Restrict formats or tune decoding with keyword arguments:

```python
results = reader.decode(
    "/path/to/barcode.png",
    multi=True,
    try_harder=True,
    pure_barcode=False,
    character_set=None,
    possible_formats=["QR_CODE", "DATA_MATRIX"],
)
```

- `multi`: scan for multiple barcodes in one image.
- `try_harder`: use ZXing's more exhaustive decode path.
- `pure_barcode`: decode a clean, unrotated monochrome symbol.
- `character_set`: provide a charset hint when the symbol does not carry one.
- `possible_formats`: limit decoding to ZXing `BarcodeFormat` names.

## Results

Each result is a dictionary. Common fields are:

| Field | Type | Meaning |
| --- | --- | --- |
| `filename` | `bytes` | Input file URI. |
| `format`, `type` | `bytes` | Barcode format and parsed-result type. |
| `raw`, `parsed` | `bytes` | Backward-compatible text fields. |
| `text`, `parsed_text` | `str` | Decoded and parsed display text. |
| `raw_bytes` | `bytes \| None` | ZXing raw result bytes. |
| `byte_segments` | `list[bytes]` | Lossless byte-mode payload segments. |
| `points` | `list[tuple[float, float]]` | Result points as `(x, y)` pairs. |
| `orientation` | `0 \| 90 \| 180 \| 270 \| None` | Clockwise image rotation. |
| `orientation_source` | `str` | `metadata`, `derived`, or `unavailable`. |
| `metadata` | `dict` | Stable ZXing metadata when available. |

For binary QR data, use `byte_segments` instead of re-encoding `text`.
Decode and runtime failures raise `DecodeError` subclasses.

## NumPy arrays

Install OpenCV and pass an RGB or grayscale array:

```bash
pip install opencv-python
```

```python
results = reader.decode_array(image)
```

## Webcam demo

The example periodically samples frames from an OpenCV camera:

```bash
pip install pyzxing opencv-python
python scripts/webcam_demo.py --camera 0 --interval 0.5
```

Press `q` or Esc to quit. Run `python scripts/webcam_demo.py --help` for all
options.

## Command line

```bash
python scripts/scanner.py -f /path/to/barcode.png
```

## PyInstaller

Bundle a Runner JAR and pass its extracted path to `BarCodeReader`:

```bash
# Use `;runner` instead of `:runner` on Windows.
pyinstaller --add-data "/path/to/pyzxing-runner.jar:runner" app.py
```

```python
import sys
from pathlib import Path

from pyzxing import BarCodeReader

bundle_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
runner_jar = next((bundle_dir / "runner").glob("*.jar"))
reader = BarCodeReader(jar_path=runner_jar)
```

## Development

```bash
./mvnw -f java-runner/pom.xml clean verify
python -m pytest tests/
```

Windows users can run `mvnw.cmd` instead of `./mvnw`.
