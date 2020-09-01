# pyzxing
[![Travis (.org)](https://img.shields.io/travis/ChenjieXu/pyzxing)](https://travis-ci.org/github/ChenjieXu/pyzxing)
[![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/chenjiexu/pyzxing?include_prereleases)](https://github.com/ChenjieXu/selective_search/releases/latest)
[![PyPI](https://img.shields.io/pypi/v/pyzxing)]((https://pypi.org/project/pyzxing/))
[![Codacy grade](https://img.shields.io/codacy/grade/353f276d2073445aab7af3e32b0d503a)](https://www.codacy.com/manual/ChenjieXu/pyzxing)

A Python wrapper of [ZXing library](https://github.com/zxing/zxing). python-zxing does not work properly and is out of maintenance. So I decide to create this repository so that Pythoneers can take advantage of ZXing library with minimum effort.

## Features

- Super easy to get hands on ZXing with Python
- Structured outputs
- Scan multiple barcodes in one picture
- Scan multiple pictures in parallel, which speeds up 77%.

## Installation
Installing from [Github source](https://github.com/ChenjieXu/pyzxing.git) is recommended :

```bash
git clone https://github.com/ChenjieXu/pyzxing.git
cd pyzxing
python setup.py install
```

It is also possible to install from [PyPI](https://pypi.org/project/pyzxing/):

```bash
pip install pyzxing
```

## Build ZXing Library

A ready-to-go jar file is available with release, but I can not guarantee that this file will work properly on your PC. You may run test script before building ZXing. Pyzxing will download compiled Jar file automatically and call unit test. For those who haven't installed Java, I strongly recommend you to install openjdk8.

```bash
python -m unittest src.test_barcode
```

If failed, build ZXing using following commands.

```bash
git submodule init
git submodule update
cd zxing
mvn install -DskipTests
cd javase
mvn -DskipTests package assembly:single
```

## Quick Start

```python
from pyzxing import BarCodeReader
reader = BarCodeReader()
results = reader.decode('/PATH/TO/FILE')
# Or file pattern for multiple files
results = reader.decode('/PATH/TO/FILES/*.png')
print(results)
```

Or you may simply call it from command line

```bash
python scanner.py -f /PATH/TO/FILE
```
