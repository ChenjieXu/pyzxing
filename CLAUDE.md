# CLAUDE.md
commit以及任何信息里面不要有claude信息
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 ZXing 库的 Python 包装器，用于条形码和二维码识别。项目通过 Java 子模块和预编译 JAR 文件提供 ZXing 功能的 Python 接口。

## 常用命令

### 构建和安装
```bash
# 安装依赖
pip install -r requirements.txt

# 安装包
python setup.py install

# 自动化 JAR 构建（推荐）
./scripts/build_jar.sh          # Linux/macOS
./scripts/build_jar.bat         # Windows
./scripts/build_and_release.sh  # 完整发布流程

# 手动构建 ZXing Java 库
git submodule init
git submodule update
cd zxing
mvn install -DskipTests -Dmaven.javadoc.skip=true
cd javase
mvn package -DskipTests -Dmaven.javadoc.skip=true assembly:single
```

### 测试
```bash
# 运行所有测试
python -m pytest tests/ -v --cov=pyzxing --cov-report=term-missing

# 运行特定测试
python -m pytest tests/test_decode.py -v

# 运行性能测试
python -m pytest tests/test_performance.py -v

# 运行边缘情况测试
python -m pytest tests/test_edge_cases.py -v
```

### 命令行工具
```bash
# 使用命令行扫描器
python scripts/scanner.py -f /PATH/TO/FILE

# 测试 JAR 功能
java -jar releases/javase-*.jar --help
```

## 核心架构

### 主要组件
1. **BarCodeReader** (`pyzxing/reader.py`): 核心条码读取器类
   - 三级 JAR 文件查找策略：本地构建 → 缓存目录 → 下载
   - 支持单文件和多文件并行处理（使用 joblib）
   - 支持 numpy 数组输入（需要 opencv-python）
   - 智能并行处理阈值（Config.PARALLEL_THRESHOLD = 3）

2. **Config** (`pyzxing/config.py`): 中央化配置管理
   - 版本控制和 ZXing 版本管理
   - 性能设置和路径配置
   - JAR URL 生成和缓存目录管理

3. **PlatformUtils** (`pyzxing/platform_utils.py`): 跨平台兼容性
   - 平台特定的路径规范化
   - Java 命令和环境变量设置
   - 编码处理（Windows 支持中文编码）

4. **Utils** (`pyzxing/utils.py`): 工具函数
   - 文件下载和进度显示
   - 缓存目录管理

### 依赖管理
- 核心依赖：`setuptools`, `joblib`, `numpy`, `pytest`, `psutil`
- 可选依赖：`opencv-python`（用于 `decode_array()` 方法）

### ZXing JAR 文件策略
项目采用三级查找策略：
1. 检查本地构建目录 `zxing/javase/target/`
2. 检查平台特定缓存目录（`~/.local/pyzxing` 或 `%LOCALAPPDATA%/pyzxing`）
3. 从 GitHub releases 下载预编译 JAR 文件

### 自动化构建系统
- **build_jar.sh/bat**: 跨平台 JAR 构建脚本
- **build_and_release.sh**: 完整发布准备脚本
- **GitHub Actions**: 自动化 CI/CD 管道，支持多平台测试和自动发布

### 测试架构
- `test_decode.py`: 基本解码功能测试
- `test_edge_cases.py`: 边缘情况和错误处理测试
- `test_performance.py`: 性能和并发测试
- `test_create_reader.py`: 读取器初始化测试

## 开发注意事项

- **版本同步**: 修改 ZXing 版本时需同时更新 `config.py` 和子模块
- **跨平台兼容**: 使用 `PlatformUtils` 处理平台差异
- **编码处理**: Windows 环境需要特殊处理中文编码
- **并行处理**: 文件数量少于 3 个时自动使用顺序处理
- **错误处理**: 所有子进程调用都包含返回码检查和错误日志
- **缓存管理**: JAR 文件自动缓存到用户目录，避免重复下载
- **条码格式支持**: QR Code, Code 128, Code 39, PDF417, Codabar 等

## CI/CD 流程

项目使用 GitHub Actions 实现完整的自动化流程：
- 多平台测试（Linux, Windows, macOS）
- 多 Python 版本测试（3.7-3.11）
- 自动 JAR 构建
- PyPI 和 Conda 发布
- 代码覆盖率报告