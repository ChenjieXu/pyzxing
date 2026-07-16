# pyzxing

简体中文 | [English](README.md)

[![PyPI](https://img.shields.io/pypi/v/pyzxing)](https://pypi.org/project/pyzxing/)
[![Conda-forge](https://img.shields.io/conda/v/conda-forge/pyzxing)](https://anaconda.org/conda-forge/pyzxing)
![PyPI - Downloads](https://img.shields.io/pypi/dm/pyzxing)
![GitHub Repo stars](https://img.shields.io/github/stars/chenjiexu/pyzxing)

[ZXing](https://github.com/zxing/zxing) 条码解码器的 Python 封装。PyZXing
支持单码和多码识别、文件通配符、NumPy 数组、解码提示、二进制数据、定位点
和方向元数据。

## 环境要求

- Python 3.8 或更高版本
- 系统 `PATH` 中提供 Java 17 或更高版本

PyZXing 会自动下载并校验匹配的 Java Runner；conda-forge 包会将 Runner
直接安装到环境中。

## 安装

```bash
pip install pyzxing
```

或者：

```bash
conda install -c conda-forge pyzxing
```

安装当前源码：

```bash
git clone https://github.com/ChenjieXu/pyzxing.git
cd pyzxing
python -m pip install .
```

## 快速上手

```python
from pyzxing import BarCodeReader

reader = BarCodeReader()

results = reader.decode("/path/to/barcode.png")
print(results)

# 识别所有匹配图片，并返回一层结果列表。
results = reader.decode("/path/to/images/*.png")
```

可通过参数限制格式或调整解码方式：

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

- `multi`：识别一张图片中的多个条码。
- `try_harder`：启用 ZXing 更全面的解码路径。
- `pure_barcode`：解码干净、未旋转的纯单色条码。
- `character_set`：条码未携带字符集时提供字符集提示。
- `possible_formats`：限制为指定的 ZXing `BarcodeFormat` 名称。

## 返回结果

每个结果都是一个字典，常用字段如下：

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `filename` | `bytes` | 输入文件 URI。 |
| `format`, `type` | `bytes` | 条码格式和解析结果类型。 |
| `raw`, `parsed` | `bytes` | 向后兼容的文本字段。 |
| `text`, `parsed_text` | `str` | 解码文本和解析后的展示文本。 |
| `raw_bytes` | `bytes \| None` | ZXing 原始结果字节。 |
| `byte_segments` | `list[bytes]` | 无损字节模式数据段。 |
| `points` | `list[tuple[float, float]]` | `(x, y)` 定位点。 |
| `orientation` | `0 \| 90 \| 180 \| 270 \| None` | 图片的顺时针旋转角度。 |
| `orientation_source` | `str` | `metadata`、`derived` 或 `unavailable`。 |
| `metadata` | `dict` | ZXing 提供的稳定元数据。 |

处理二进制 QR 数据时应使用 `byte_segments`，不要重新编码 `text`。
解码和运行时失败会抛出 `DecodeError` 的具体子类。

## NumPy 数组

安装 OpenCV，然后传入 RGB 或灰度数组：

```bash
pip install opencv-python
```

```python
results = reader.decode_array(image)
```

## 摄像头演示

示例程序会定期抽取 OpenCV 摄像头画面进行识别：

```bash
pip install pyzxing opencv-python
python scripts/webcam_demo.py --camera 0 --interval 0.5
```

按 `q` 或 Esc 退出。运行 `python scripts/webcam_demo.py --help` 查看全部参数。

## 命令行

```bash
python scripts/scanner.py -f /path/to/barcode.png
```

## PyInstaller

将 Runner JAR 打包，并把解压后的路径传给 `BarCodeReader`：

```bash
# Windows 使用 `;runner`，不要使用 `:runner`。
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

## 开发

```bash
./mvnw -f java-runner/pom.xml clean verify
python -m pytest tests/
```

Windows 用户使用 `mvnw.cmd` 代替 `./mvnw`。
