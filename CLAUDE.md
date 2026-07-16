# CLAUDE.md
commit以及任何信息里面不要有claude信息
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 ZXing 库的 Python 包装器，用于条形码和二维码识别。项目通过自有 JSONL Java Runner 和经过 SHA-256 校验的 Release JAR 提供稳定的 Python 接口。

## 常用命令

### 构建和安装
```bash
# 安装依赖
python -m pip install -e '.[dev]'

# 安装包
python -m pip install .

# 构建并测试基于 ZXing 3.5.4 的 Java Runner
./mvnw -f java-runner/pom.xml clean verify
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

# 测试指定 JAR
PYZXING_TEST_JAR=/absolute/path/to/pyzxing-runner.jar python -m pytest tests/test_decode.py -v
```

## 核心架构

### 主要组件
1. **BarCodeReader** (`pyzxing/reader.py`): 核心条码读取器类
   - 三级 JAR 文件查找策略：显式 `jar_path` → 本地 Runner → 已校验缓存/安全下载
   - 支持单文件和多文件并行处理（使用 joblib）
   - 支持 numpy 数组输入（需要 opencv-python）
   - 智能并行处理阈值（Config.PARALLEL_THRESHOLD = 3）

2. **PyzxingRunner** (`java-runner/`): ZXing 3.5.4 JSONL 边界
   - stdout 每行一个 `schema_version=1` JSON 对象，诊断只写 stderr
   - 二进制统一使用 Base64，同时导出 raw codewords 与 BYTE segments
   - 一维码方向原样导出 ZXing 元数据；仅对 QR 有序定位点推导几何方向

3. **Config** (`pyzxing/config.py`): 中央化配置管理
   - 版本控制和 ZXing 版本管理
   - canonical Runner 文件名、Release、SHA-256 和源提交
   - 性能设置、路径配置和缓存目录管理

4. **PlatformUtils** (`pyzxing/platform_utils.py`): 跨平台兼容性
   - 平台特定的路径规范化
   - Java 命令和环境变量设置
   - 编码处理（Windows 支持中文编码）

5. **Utils** (`pyzxing/utils.py`): 工具函数
   - 文件下载和进度显示
   - 缓存目录管理

### 依赖管理
- 核心依赖：`joblib`, `numpy`
- 开发依赖：`pytest`, `pytest-cov`, `psutil`, `ruff`
- 可选依赖：`opencv-python`（用于 `decode_array()` 方法）

### ZXing JAR 文件策略
项目采用三级查找策略：
1. 使用显式传入的 `jar_path`
2. 检查本地构建目录 `java-runner/target/`
3. 检查平台特定缓存或从 GitHub Release 原子下载，并验证固定 SHA-256

### 自动化构建系统
- **GitHub Actions**: 多平台测试、单次构建、PyPI Trusted Publishing 和 GitHub Release
- **prepare-runner.yml**: 从冻结提交构建两次并提升 canonical Runner 到草稿 Release
- **ci-cd.yml**: 普通 CI 使用构建产物；Release CI 只使用已提升的 canonical JAR
- **conda recipe/feedstock**: recipe 安装 canonical JAR 到 `$CONDA_PREFIX/share/pyzxing/runner`，Release CI 用默认 reader 做真实解码；正式发布仍由独立 feedstock 完成
- **RELEASING.md**: 两阶段 JAR、版本发布和 conda-forge 更新步骤

### 测试架构
- `test_decode.py`: 基本解码功能测试
- `test_edge_cases.py`: 边缘情况和错误处理测试
- `test_performance.py`: 性能和并发测试
- `test_create_reader.py`: 读取器初始化测试

## 开发注意事项

- **版本同步**: 修改 Runner/ZXing 版本时需同步 Maven、`config.py`、版本文件和 Release 资产
- **跨平台兼容**: 使用 `PlatformUtils` 处理平台差异
- **编码处理**: JSONL 固定 UTF-8；二进制不得通过文本重新编码，使用 `byte_segments`
- **并行处理**: 文件数量少于 3 个时自动使用顺序处理
- **错误处理**: Java 启动、失败和超时通过 `DecodeError` 子类明确报告
- **协议版本**: Java 错误码是 schema 的枚举式组成；新增、改名或删除错误码时必须同步 Python allow-list/测试，并评估 schema version 升级
- **方向语义**: 顶层 `orientation` 是归一化的图片顺时针角度；`metadata.orientation` 保留 ZXing 原始纠正角度
- **缓存管理**: JAR 文件自动缓存到用户目录，避免重复下载
- **范围**: 1.2.0 处理正确性和发布基础设施；持久 JVM 摄像头模式属于 1.3.0

## CI/CD 流程

项目使用 GitHub Actions 实现完整的自动化流程：
- 多平台测试（Linux, Windows, macOS）
- 多 Python 版本测试（3.8-3.14）
- Java Runner 的 JUnit、JSONL smoke 和 canonical 资产校验
- 版本/资产名同步校验与真实 PyInstaller one-file 解码 smoke
- `publish-release.yml` 在严格校验 final Config、canonical 草稿资产、冻结 Java tree 和持久 issue 证据后自动发布草稿 Release
- GitHub Release 资产完成后才执行 PyPI OIDC 发布
- Conda 由 conda-forge feedstock 独立发布
- 代码覆盖率报告
