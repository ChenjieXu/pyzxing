# pyzxing

简体中文 | [English](README.md)

[![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/chenjiexu/pyzxing?include_prereleases)](https://github.com/ChenjieXu/pyzxing/releases/latest)
[![PyPI](https://img.shields.io/pypi/v/pyzxing)](https://pypi.org/project/pyzxing/)
[![Conda](https://img.shields.io/conda/v/chenjiexu/pyzxing)](https://anaconda.org/ChenjieXu/pyzxing)

[![Travis (.org)](https://img.shields.io/travis/ChenjieXu/pyzxing)](https://travis-ci.org/github/ChenjieXu/pyzxing)
[![Codacy grade](https://img.shields.io/codacy/grade/353f276d2073445aab7af3e32b0d503a)](https://www.codacy.com/manual/ChenjieXu/pyzxing)

## 第一个正式版本

经历了一年的开发，pyzxing的第一个正式版本终于发布了。十分感谢各位开发者的建议和issue，这非常大程度上帮助了这个项目的开发。这个项目会继续保持开源并定时更新。

## 简介

Pyzxing是二维码识别[ZXing](https://github.com/zxing/zxing)JAVA库的Python
API。由于Zxing库相较于其他库二维码识别率最高，但使用起来十分繁琐，且python-zxing不能正常使用缺已不再维护，所以我创建了这个库让使用Python的人可以以最小的精力来使用Zxing库来进行二维码识别。

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
python setup.py install
```

同时也支持使用pip从 [PyPI](https://pypi.org/project/pyzxing/) 安装:

```bash
pip install pyzxing
```

从[Anaconda](https://anaconda.org/ChenjieXu/pyzxing) 安装:

```bash
conda install -c chenjiexu pyzxing
```

## 构建ZXing库

随版本提供了一个即用的jar文件，但我不能保证此文件将在您的电脑上正常工作。可以在构建ZXing之前运行测试脚本。Pyzxing将自动下载编译的Jar文件并调用单元测试。对于尚未安装Java的用户，强烈建议您安装openjdk8。

```bash
python -m unittest src.test_decode
```

如果单元测试未通过，使用以下代码构建ZXing库：

```bash
git submodule init
git submodule update
cd zxing
mvn install -DskipTests
cd javase
mvn -DskipTests package assembly:single
```

## 快速上手
```python
from pyzxing import BarCodeReader
reader = BarCodeReader()
results = reader.decode('/PATH/TO/FILE')
# 支持输入文件模式以检测多个文件
results = reader.decode('/PATH/TO/FILES/*.png')
print(results)
# 支持传入图片的向量
# 需要额外安装opencv，pip install opencv-python
results = reader.decode_array(img)
```

或者直接从命令行调用：

```bash
python scanner.py -f /PATH/TO/FILE
```

# 赞助

<p align="left">
  <a href="https://jb.gg/OpenSource"><img src="src/jetbrains-logo.svg" alt="Logo"></img></a>
  
  <br/>
  <sub><a href="https://www.jetbrains.com/community/opensource/">开源支持计划</a></sub>
</p>