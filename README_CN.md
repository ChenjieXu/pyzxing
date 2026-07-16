# pyzxing

简体中文 | [English](README.md)

[![PyPI](https://img.shields.io/pypi/v/pyzxing)](https://pypi.org/project/pyzxing/)
[![Conda-forge](https://img.shields.io/conda/v/conda-forge/pyzxing)](https://anaconda.org/conda-forge/pyzxing)
![PyPI - Downloads](https://img.shields.io/pypi/dm/pyzxing)
![GitHub Repo stars](https://img.shields.io/github/stars/chenjiexu/pyzxing)

## 第一个正式版本

经历了一年的开发，pyzxing的第一个正式版本终于发布了。十分感谢各位开发者的建议和issue，这非常大程度上帮助了这个项目的开发。这个项目会继续保持开源并定时更新。

## 简介

Pyzxing是二维码识别[ZXing](https://github.com/zxing/zxing) JAVA库的Python
API。由于Zxing库相较于其他库二维码识别率最高，但使用起来十分繁琐，且python-zxing不能正常使用且已不再维护，所以我创建了这个库让使用Python的人可以花费最小的精力来使用Zxing库来进行二维码识别。

## 特性

- 十分容易上手
- 结构化输出
- 能够识别一张图中的多个二维码
- 以并行方式识别多张图片，提速77%

## 安装
推荐从[Github](https://github.com/ChenjieXu/pyzxing.git) 源安装:

```bash
git clone https://github.com/ChenjieXu/pyzxing.git
cd pyzxing
python -m pip install .
```

同时也支持使用pip从 [PyPI](https://pypi.org/project/pyzxing/) 安装:

```bash
pip install pyzxing
```

从[Anaconda](https://anaconda.org/ChenjieXu/pyzxing) 安装。现在可以从公开的channel——conda-forge中下载:

```bash
conda install -c conda-forge pyzxing # conda-forge频道
```

1.2 recipe 会把 checksum 固定的 canonical Runner 安装到
`$CONDA_PREFIX/share/pyzxing/runner`。`BarCodeReader()` 会先发现并校验这份
文件，再考虑联网下载；Release CI 会实际构建 conda 包，并在不传
`jar_path` 的情况下验证默认 reader 解码。

## Java Runner

PyZXing 1.2 使用由本项目维护、基于 ZXing 3.5.4 的可执行 Runner，要求
系统 `PATH` 中提供 Java 17 或更高版本。每个 GitHub Release 会同时发布
确定的 JAR 与 `.sha256` 文件；使用缓存或下载文件前都会校验 SHA-256。

从源码构建 Runner：

```bash
./mvnw -f java-runner/pom.xml clean verify
```

Windows 请使用 `mvnw.cmd`。也可以显式选择已经审核的本地 JAR：

```python
from pyzxing import BarCodeReader

reader = BarCodeReader(jar_path="/absolute/path/to/pyzxing-runner.jar")
```

## 快速上手

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

# glob 可以识别多个文件，仍然返回一层扁平结果列表。
results = reader.decode("/PATH/TO/FILES/*.png")
print(results)

# NumPy 数组需要先安装：pip install opencv-python
results = reader.decode_array(img)
```

Java 启动失败、无效图片和超时会抛出 `DecodeError` 的具体子类，
不再伪装成空的条码结果。

### 返回字段

1.2 采用增量兼容策略：保留原有 bytes 字段，同时增加无损二进制和方向字段。

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `filename` | `bytes` | Runner 原样返回的输入 URI。 |
| `format`, `type` | `bytes` | 兼容字段：ZXing 格式与解析结果类型。 |
| `raw`, `parsed` | `bytes` | `text`、`parsed_text` 的 UTF-8 兼容表示。 |
| `text`, `parsed_text` | `str` | 解码文本与 ZXing 的展示文本。 |
| `raw_bytes` | `bytes \| None` | ZXing 原始结果字节；对 QR 而言不一定等于原始 BYTE 段。 |
| `byte_segments` | `list[bytes]` | 按顺序保存的无损 BYTE 模式数据段。 |
| `num_bits` | `int \| None` | `raw_bytes` 中有效的位数。 |
| `points` | `list[tuple[float, float]]` | ZXing 返回的 `(x, y)` 定位点。 |
| `orientation` | `0 \| 90 \| 180 \| 270 \| None` | 相对正向的顺时针旋转角度。 |
| `orientation_source` | `str` | `metadata`、仅 QR 使用的 `derived`，或 `unavailable`。 |
| `metadata` | `dict` | 经过白名单约束的稳定元数据，包括可用的码制和纠错字段。 |

处理二进制 QR 时应直接使用 `byte_segments`，不要把 `text` 重新编码来恢复
原始数据。`raw_bytes` 与 `byte_segments` 对应 ZXing 中两个不同的概念。
未发现条码时，1.x 的兼容行为仍会返回只包含 `filename` 的占位结果。

方向必须结合 `orientation_source` 理解。顶层 `orientation` 统一表示图片相对
正向的顺时针旋转角度。对一维码，`metadata.orientation` 保留 ZXing 原始的
逆时针纠正角度，因此顺时针旋转 90 度的图片会得到顶层 `orientation=90`，
而原始 metadata 可能是 `270`。ZXing 不为 QR 提供方向元数据，因此
`derived` QR 值采用有序定位点的几何顺时针角度；定位点不足时返回 `None`，
不会猜测。ZXing 提供时，metadata 还可能包含整数类型的
`errors_corrected` 和 `erasures_corrected`。

Runner stdout 使用协议 schema version 1。错误码属于枚举式协议值：Java
新增、重命名或删除错误码时，必须同步 Python 校验和测试，并明确评估是否
需要升级 schema version；未知错误码会被拒绝，不会静默放行。

### 解码提示和格式范围

- `multi`：在一张图片中扫描多个条码。
- `try_harder`：启用 ZXing 更全面的扫描路径。
- `pure_barcode`：仅适用于没有周边内容、未旋转的纯单色条码图片。
- `character_set`：条码没有携带字符集时，可传入 `GB18030` 等提示。
- `possible_formats`：传入 ZXing 3.5.4 的 `BarcodeFormat` 名称以限制格式。

对 issue #34 已提交的无 ECI 样本，默认解码仍会在 `byte_segments` 中无损
保留 GB18030 字节，但无法自动推断文本编码；传入
`character_set="GB18030"` 后可得到预期中文。对 issue #38 的精确 192 个值，
记录中的 ZXing 3.5.4 Runner 在 default/try-harder/QR-only 模式识别 23/192，
使用 `pure_barcode=True` 时识别 192/192；ZXing 3.4.1 默认识别 19/192，
pure-barcode 同样是 192/192。因此不能把升级描述成通用检测修复；已提交报告
保留了该限制和经过验证的 hint。

PyZXing 只负责解码，不提供二维码生成；生成二维码可使用
[Segno](https://segno.readthedocs.io/)。issue #43 请求的六种 GS1 变体当前
状态如下：

| 请求的变体 | ZXing 3.5.4 候选入口 | 项目内已提交样本 | 1.2 状态 |
| --- | --- | --- | --- |
| GS1 DataBar Expanded | `RSS_EXPANDED` | 无 | 未验证 |
| GS1 DataBar Expanded Stacked | `RSS_EXPANDED` | 无 | 未验证 |
| GS1 DataBar OmniDirectional | `RSS_14` | 无 | 未验证 |
| GS1 DataBar Stacked | `RSS_14` | 无 | 未验证 |
| GS1 DataBar Stacked Omnidirectional | `RSS_14` | 无 | 未验证 |
| GS1 DataBar Truncated | `RSS_14` | 无 | 未验证 |

普通 QR 和 Code 128 样本不能证明这些 DataBar 变体。Runner 会在 ZXing
提供时暴露 `symbology_identifier`，但这不等于应用层 GS1 校验。在每个声称
支持的变体都有可再分发样本和预期 payload 断言前，issue #43 保持开启。

### PyInstaller

将对应 Release 的 Runner 打包，并显式传入解压后的路径：

```bash
# Linux 和 macOS；Windows 将 `:runner` 改为 `;runner`。
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

CI 会冻结并执行 `scripts/pyinstaller_smoke.py`，因此该路径由真实 one-file
程序验证，而不只是普通 Python 运行时示例。

### 摄像头演示

仓库提供了一个小型摄像头演示程序：使用 OpenCV 采集画面，并调用现有的
一次性 `decode_array()` 接口抽帧识别。它不需要持久 JVM，也不需要新增
流式 API：

```bash
pip install pyzxing opencv-python
python scripts/webcam_demo.py --camera 0 --interval 0.5
```

按 `q` 或 Esc 退出。可用 `--possible-formats QR_CODE,DATA_MATRIX` 限定格式。
每次抽帧识别仍会启动一个 JVM，因此 `--interval` 用来平衡响应速度与进程
开销；这是演示程序，不代表持久流式解码器的吞吐能力。

或者直接从命令行调用：

```bash
python scripts/scanner.py -f /PATH/TO/FILE
```

## 点赞趋势

[![Star History Chart](https://api.star-history.com/svg?repos=chenjiexu/pyzxing&type=Date)](https://www.star-history.com/#chenjiexu/pyzxing&Date)
