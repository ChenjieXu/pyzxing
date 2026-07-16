# pyzxing

[简体中文](README_CN.md) | [English](README.md)

[![CI](https://github.com/ChenjieXu/pyzxing/actions/workflows/ci-cd.yml/badge.svg?branch=master)](https://github.com/ChenjieXu/pyzxing/actions/workflows/ci-cd.yml)
[![Documentation](https://readthedocs.org/projects/pyzxing/badge/?version=latest)](https://pyzxing.readthedocs.io/en/latest/)
[![PyPI](https://img.shields.io/pypi/v/pyzxing)](https://pypi.org/project/pyzxing/)
[![Python](https://img.shields.io/pypi/pyversions/pyzxing)](https://pypi.org/project/pyzxing/)
[![Conda-forge](https://img.shields.io/conda/vn/conda-forge/pyzxing)](https://anaconda.org/conda-forge/pyzxing)
[![Coverage](https://codecov.io/gh/ChenjieXu/pyzxing/graph/badge.svg?branch=master)](https://codecov.io/gh/ChenjieXu/pyzxing)
[![Downloads](https://img.shields.io/pypi/dm/pyzxing)](https://pypistats.org/packages/pyzxing)
[![License](https://img.shields.io/github/license/ChenjieXu/pyzxing)](LICENSE)

[ZXing](https://github.com/zxing/zxing) 条码解码器的可靠 Python 封装。
pyzxing 提供稳定的 Python API，并通过版本固定、SHA-256 校验的 Java Runner
执行实际解码。

## 功能特点

- 以统一的结果列表解码单个文件或文件通配符。
- 支持 QR Code、Data Matrix、PDF417、Aztec 和常见一维码。
- 支持文件路径和 NumPy 数组。
- 保留二进制数据、字节段、定位点、元数据和方向信息。
- 显式控制格式、字符集、多码识别和 `try_harder` 等 ZXing 提示。
- 支持 Linux、macOS、Windows、Python 3.8–3.14 和 Java 17+。
- 自动安装经过校验的 Runner；conda-forge 环境会直接包含 Runner。

## 环境要求

| 组件 | 支持范围 |
| --- | --- |
| Python | 3.8–3.14 |
| Java | 17 或更高版本 |
| 操作系统 | Linux、macOS、Windows |
| ZXing 运行时 | pyzxing 1.2.x 使用 3.5.4 |

系统 `PATH` 中必须能够执行 `java`。PyPI 包会在首次使用时下载匹配的
Runner 并验证 SHA-256；conda-forge 包会将 Runner 安装到当前环境。

## 安装

从 PyPI 安装：

```bash
python -m pip install pyzxing
```

或从 conda-forge 安装：

```bash
conda install -c conda-forge pyzxing
```

## 快速上手

```python
from pyzxing import BarCodeReader

reader = BarCodeReader()
results = reader.decode("/path/to/qrcode.png")

for result in results:
    print(result["format"], result["text"])
```

文件通配符返回相同的一层 `list[dict]`：

```python
results = reader.decode("/path/to/images/*.png")
```

需要时可以显式传递解码提示：

```python
results = reader.decode(
    "/path/to/barcode.png",
    multi=True,
    try_harder=True,
    character_set="UTF-8",
    possible_formats=["QR_CODE", "DATA_MATRIX"],
)
```

## NumPy 数组

安装 OpenCV 后可传入 RGB 或灰度数组：

```bash
python -m pip install opencv-python
```

```python
results = reader.decode_array(image)
```

## 返回结果

每个条码对应一个字典，常用字段如下：

| 字段 | 类型 | 用途 |
| --- | --- | --- |
| `text` | `str` | 解码后的展示文本。 |
| `format` | `bytes` | ZXing 条码格式。 |
| `raw_bytes` | `bytes \| None` | ZXing 原始结果字节。 |
| `byte_segments` | `list[bytes]` | 无损 QR 字节模式数据段。 |
| `points` | `list[tuple[float, float]]` | ZXing 返回的定位点。 |
| `orientation` | `int \| None` | 图片的顺时针旋转角度。 |
| `metadata` | `dict` | 稳定的 ZXing 结果元数据。 |

为保持向后兼容，字节类型的 `raw` 和 `parsed` 字段仍然保留。处理二进制
QR 数据时应使用 `byte_segments`，不要对文本重新编码。

## 文档

完整英文文档托管在
[Read the Docs](https://pyzxing.readthedocs.io/en/latest/)：

- [安装与运行环境](https://pyzxing.readthedocs.io/en/latest/installation.html)
- [用法与解码提示](https://pyzxing.readthedocs.io/en/latest/usage.html)
- [结果结构](https://pyzxing.readthedocs.io/en/latest/results.html)
- [API 参考](https://pyzxing.readthedocs.io/en/latest/api.html)
- [PyInstaller 与部署](https://pyzxing.readthedocs.io/en/latest/deployment.html)
- [故障排查](https://pyzxing.readthedocs.io/en/latest/troubleshooting.html)

## 命令行示例

扫描文件：

```bash
python scripts/scanner.py -f /path/to/barcode.png
```

定期采样摄像头画面：

```bash
python -m pip install opencv-python
python scripts/webcam_demo.py --camera 0 --interval 0.5
```

摄像头示例使用现有的一次性 `decode_array()` API，不会保持长期运行的
Java 进程。

## 开发

```bash
python -m pip install -e '.[dev]'
./mvnw -f java-runner/pom.xml clean verify
python -m pytest tests/
```

Windows 使用 `mvnw.cmd` 代替 `./mvnw`。文档构建和发布检查请参阅
[开发指南](https://pyzxing.readthedocs.io/en/latest/development.html)。

## 项目链接

- [文档](https://pyzxing.readthedocs.io/)
- [更新日志](CHANGELOG.md)
- [发布版本](https://github.com/ChenjieXu/pyzxing/releases)
- [问题反馈](https://github.com/ChenjieXu/pyzxing/issues)
- [许可证](LICENSE)
