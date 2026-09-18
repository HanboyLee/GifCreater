# 01 - 架构分层与工程边界规范 (Architecture & Boundaries)

本文档是 GifCreater 项目的法定架构边界规范，所有接手本项目的 AI 代理必须严格遵循。

---

## 1. 核心架构分层标准 (Layering Standard)

本项目采用严格的 **无头核心解耦架构 (Headless Decoupled Architecture)**，分为四层：

1. **核心算法层 (`src/gifcreater/core/`)**：
   - **绝对无头原则**：严禁导入任何图形库（禁止 `import PyQt6`、`import tkinter`）。
   - **单一职责**：
     - `slicer.py`：网格坐标切片与通用分割线探测算法；
     - `bounds.py`：高精度黑边、白边、透明背景边界探测；
     - `compressor.py`：自适应调色板阶梯衰减算法（微信表情包压缩核心）；
     - `exporter.py`：GIF / WebP 动图合成、Boomerang 往复帧序列重排与保存。
   - **外部独立性**：所有核心算法必须能够脱离 GUI 在纯命令行（CLI）或单元测试中直接独立调用。
2. **表现与交互层 (`src/gifcreater/ui/`)**：
   - 基于 PyQt6 + PyQt-Fluent-Widgets 构建，只负责视图渲染、用户交互、事件响应与异步线程调度。
   - 严禁在 UI 类中嵌入重型图像处理算法，所有图像处理必须调用 `core` 模块。
3. **基础设施与工具层 (`src/gifcreater/utils/`, `src/gifcreater/config/`, `src/gifcreater/i18n/`)**：
   - `paths.py`：跨平台安全输出路径处理，支持受限只读目录优雅降级回退；
   - 提供纯粹的基础工具函数，不产生逆向业务依赖。
4. **根目录轻量入口层**：
   - `main.py`：桌面客户端正式启动引导入口（仅包含 DPI 初始化与 MainWindow 调起）；
   - `gif_tool.py`：向后兼容转发代理（Shim），将历史命令行调用透明代理至 `core`。

---

## 2. 根目录极简白名单红线 (Root Directory Whitelist)

为保持专案整洁与工程标准，专案根目录下**严禁随意创建散落的脚本、草稿或临时文档**。

### 根目录法定允许文件列表：
- **可执行/入口**：`main.py`、`gif_tool.py`、`run_gui.bat`
- **打包配置**：`GifCreater.spec`
- **依赖声明**：`requirements.txt`、`requirements-dev.txt`
- **测试配置**：`pytest.ini`
- **Git 规则**：`.gitignore`
- **开源协议**：`LICENSE`
- **产品说明**：`README.md`、`README_zh.md`
- **架构与规则总纲**：`ARCHITECTURE.md`、`AGENTS.md`
- **法定子目录**：`src/`、`resources/`、`scripts/`、`tests/`、`docs/`、`spec/`、`.agent/`、`.github/`、`dist/`、`output/`

---

## 3. 依赖与计算边界 (Dependencies & Zero Cloud)

1. **100% 纯本地离线计算**：
   - 严禁引入任何需要外部云端 API、远程网络请求或服务端依赖的代码；
   - 保护用户隐私，所有图像切片与合成运算均在本地设备完成。
2. **轻量依赖控制**：
   - 严禁擅自引入未经验证的重型第三方依赖（生产运行时严格控制在 `Pillow`, `PyQt6`, `PyQt6-Fluent-Widgets` 三大核心依赖）。
