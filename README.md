# pyzxing

English | [简体中文](README_CN.md)

[![PyPI](https://img.shields.io/pypi/v/pyzxing)](https://pypi.org/project/pyzxing/)
[![Conda-forge](https://img.shields.io/conda/v/conda-forge/pyzxing)](https://anaconda.org/conda-forge/pyzxing)
![PyPI - Downloads](https://img.shields.io/pypi/dm/pyzxing)
![GitHub Repo stars](https://img.shields.io/github/stars/chenjiexu/pyzxing)


## First GA

After a year of development, the first General Availability of pyzxing is finally released. I would like to express my
gratitude to all the developers for their suggestions and issue, which helped the development of this project to a great
extent. This project will continue to be open source and updated regularly.

## Introduction

A Python wrapper of [ZXing library](https://github.com/zxing/zxing). python-zxing does not work properly and is out of
maintenance. So I decide to create this repository so that Pythoneers can take advantage of ZXing library with minimum
effort.

## Features

- Super easy to get hands on decoding qrcode with Python
- Structured outputs
- Scan multiple barcodes in one picture
- Scan multiple pictures in parallel, which speeds up 77%

## Installation

Installing from [Github source](https://github.com/ChenjieXu/pyzxing.git) is recommended :

```bash
git clone https://github.com/ChenjieXu/pyzxing.git
cd pyzxing
python -m pip install .
```

It is also possible to install from [PyPI](https://pypi.org/project/pyzxing/):

```bash
pip install pyzxing
```

Install from [Anaconda](https://anaconda.org/ChenjieXu/pyzxing). Now available on the public channel, conda-forge:

```bash
conda install -c conda-forge pyzxing # conda-forge channel
```

The 1.2 recipe packages the checksum-pinned canonical Runner under
`$CONDA_PREFIX/share/pyzxing/runner`. `BarCodeReader()` discovers and verifies
that copy before considering a network download; release CI builds the conda
package and proves a default-reader decode without passing `jar_path`.

## Java Runner

PyZXing 1.2 uses a pyzxing-owned executable Runner built with ZXing 3.5.4 and
requires Java 17 or newer on `PATH`. The exact JAR and its `.sha256` file are
published with each GitHub Release. PyZXing verifies the checksum before using
a cached or downloaded JAR.

To build the Runner from source:

```bash
./mvnw -f java-runner/pom.xml clean verify
```

On Windows, use `mvnw.cmd` instead. You can bypass downloading and select a
reviewed local build explicitly:

```python
from pyzxing import BarCodeReader

reader = BarCodeReader(jar_path="/absolute/path/to/pyzxing-runner.jar")
```

## Quick Start

```python
from pyzxing import BarCodeReader, DecodeError

reader = BarCodeReader()
results = reader.decode(
    "/PATH/TO/FILE",
    multi=True,
    try_harder=True,
    pure_barcode=False,
    character_set=None,
    possible_formats=["QR_CODE", "DATA_MATRIX"],
)

# A glob decodes multiple files and still returns one flat result list.
results = reader.decode("/PATH/TO/FILES/*.png")
print(results)

# NumPy arrays require: pip install opencv-python
results = reader.decode_array(img)
```

Java startup failures, invalid images, and timeouts raise `DecodeError` subclasses
instead of being reported as an empty barcode result.

### Result schema

The 1.2 result is additive: the legacy byte-valued fields remain available,
while the machine-readable Runner adds lossless binary and orientation fields.

| Field | Type | Meaning |
| --- | --- | --- |
| `filename` | `bytes` | Exact input URI echoed by the Runner. |
| `format`, `type` | `bytes` | Legacy ZXing format and parsed-result type. |
| `raw`, `parsed` | `bytes` | Legacy UTF-8 encodings of `text` and `parsed_text`. |
| `text`, `parsed_text` | `str` | Decoded text and ZXing's parsed display text. |
| `raw_bytes` | `bytes \| None` | ZXing raw result bytes; for QR this is not necessarily the original byte-mode payload. |
| `byte_segments` | `list[bytes]` | Lossless BYTE-mode payload segments, in order. |
| `num_bits` | `int \| None` | Valid bit count in `raw_bytes`. |
| `points` | `list[tuple[float, float]]` | ZXing result points as `(x, y)` pairs. |
| `orientation` | `0 \| 90 \| 180 \| 270 \| None` | Clockwise rotation from upright. |
| `orientation_source` | `str` | `metadata`, QR-only `derived`, or `unavailable`. |
| `metadata` | `dict` | Stable allow-listed metadata, including symbology/error-correction fields when available. |

For binary QR data, use `byte_segments`; do not recover bytes by re-encoding
`text`. `raw_bytes` and `byte_segments` intentionally expose different ZXing
concepts. A no-barcode image retains the 1.x compatibility placeholder
containing only `filename`.

`orientation_source` is part of the meaning. The top-level `orientation` is
always normalized to the image's clockwise rotation from upright. For 1D
formats, `metadata.orientation` preserves ZXing's raw counter-clockwise
correction value, so a clockwise-90 image has top-level `orientation=90` while
raw metadata may be `270`. ZXing does not supply QR orientation metadata, so
`derived` QR values use the geometric clockwise angle of ordered finder points.
If that geometry is insufficient, the value is `None` rather than a guess.
Metadata may also include integer
`errors_corrected` and `erasures_corrected` values when ZXing provides them.

Runner stdout is protocol schema version 1. Error codes are enum-like protocol
values: adding, renaming, or removing a Java error code requires matching Python
validation/tests and an explicit schema-version compatibility review. Unknown
codes are rejected instead of being silently accepted.

### Decode hints and format scope

- `multi` scans for more than one barcode in an image.
- `try_harder` enables ZXing's more exhaustive path.
- `pure_barcode` is for an unrotated, monochrome barcode image without surrounding content.
- `character_set` supplies a charset hint such as `GB18030` when the symbol does not carry one.
- `possible_formats` accepts ZXing 3.5.4 `BarcodeFormat` names and restricts decoding to those formats.

For issue #34's committed no-ECI fixture, the default decoder preserves the
exact GB18030 bytes in `byte_segments` but cannot infer the intended text
encoding; `character_set="GB18030"` returns the expected Chinese text. For
issue #38's exact 192-value corpus, the recorded ZXing 3.5.4 Runner decodes
23/192 in default/try-harder/QR-only modes and 192/192 with
`pure_barcode=True`. ZXing 3.4.1 decoded 19/192 by default and also 192/192 in
pure-barcode mode. The upgrade is therefore not presented as a general detector
fix; the committed reports preserve the limitation and the proven hint.

PyZXing is a decoder, not a QR generator; use a library such as
[Segno](https://segno.readthedocs.io/) for generation. The exact status of the
six GS1 variants requested in issue #43 is:

| Requested variant | Candidate ZXing 3.5.4 route | Committed project fixture | 1.2 status |
| --- | --- | --- | --- |
| GS1 DataBar Expanded | `RSS_EXPANDED` | None | Unverified |
| GS1 DataBar Expanded Stacked | `RSS_EXPANDED` | None | Unverified |
| GS1 DataBar OmniDirectional | `RSS_14` | None | Unverified |
| GS1 DataBar Stacked | `RSS_14` | None | Unverified |
| GS1 DataBar Stacked Omnidirectional | `RSS_14` | None | Unverified |
| GS1 DataBar Truncated | `RSS_14` | None | Unverified |

Generic QR and Code 128 fixtures do not prove these DataBar variants. The
Runner exposes ZXing's `symbology_identifier` metadata when present, but that is
not application-level GS1 validation. Issue #43 stays open until each claimed
variant has a redistributable fixture and an asserted payload result.

### PyInstaller

Bundle the exact release Runner and pass its unpacked path explicitly:

```bash
# Linux and macOS; use `;runner` instead of `:runner` on Windows.
pyinstaller --add-data "/absolute/path/to/pyzxing-runner.jar:runner" app.py
```

```python
import sys
from pathlib import Path

from pyzxing import BarCodeReader

bundle_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
runner_jar = next((bundle_dir / "runner").glob("*.jar"))
reader = BarCodeReader(jar_path=runner_jar)
```

CI freezes and executes `scripts/pyinstaller_smoke.py`, so this path is tested
from an actual one-file bundle rather than only from normal Python.

### Camera use

The repository includes a small webcam demonstration that combines OpenCV
camera capture with the existing one-shot `decode_array()` API. It does not
require a persistent JVM or a new streaming API:

```bash
pip install pyzxing opencv-python
python scripts/webcam_demo.py --camera 0 --interval 0.5
```

Press `q` or Esc to quit. Use `--possible-formats QR_CODE,DATA_MATRIX` to limit
formats. Each sampled frame still starts one JVM, so `--interval` controls the
trade-off between responsiveness and process overhead; this is a demonstration
program, not a throughput claim about a persistent streaming decoder.

Or you may simply call it from command line

```bash
python scripts/scanner.py -f /PATH/TO/FILE
```

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=chenjiexu/pyzxing&type=Date)](https://www.star-history.com/#chenjiexu/pyzxing&Date)
