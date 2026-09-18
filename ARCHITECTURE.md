# 🏛️ GifCreater 专案架构全景与目录规范 (ARCHITECTURE.md)

本文件是专案根目录下的**架构速查与工程规范入口**，用于指导开发者与 AI 代理快速理解专案的分层解耦模型、纯文件夹层级规范及各模块职责边界。

详细的产品需求说明请参阅 [docs/requirements.md](docs/requirements.md)；详细的底层技术设计请参阅 [docs/design.md](docs/design.md)；中长期功能演进全景请参阅 [docs/roadmap.md](docs/roadmap.md)。

> 📌 **持续维护契约（Mandatory Sync Protocol）**：
> 凡日后专案发生任何架构分层、目录调整、技术选型演进或重大功能变更，**必须且只能无条件同步更新此 `ARCHITECTURE.md` 文件及 `docs/` 下的对应文档**，杜绝任何代码与文档脱节行为。

---

## 一、 核心架构定位与设计哲学

1. **100% 本机算力与本地隐私安全**：
   - 坚持纯单机桌面客户端架构（Native Desktop Application），所有图像拆解、自适应调色板试探计算及动图编码完全在用户本机 CPU 运行，零外部网络依赖，彻底消除云端服务器开销与用户素材外泄风险。
2. **三层分工解耦模型 (Three-Tier Decoupling)**：
   - **表现层 (Presentation Layer)**：基于 PyQt6 + Fluent UI，负责现代 Windows 11 风格的视觉渲染、可交互缩放画布与时间轴胶卷；
   - **调度与状态层 (Coordination Layer)**：基于 `QThread` 异步任务与 Qt 信号槽机制，彻底杜绝耗时计算导致的界面未响应；
   - **核心算法引擎层 (Core Engine Layer)**：纯无头运算（Headless），零 GUI 依赖，接受严格的单测门禁保护。

---

## 二、 专案文件夹层级全景规范 (Directory Hierarchy)

为支撑全生命周期的演进与功能扩展，专案采用标准的分层文件夹体系：

```text
GifCreater/
│
├── .github/                      # 🤖 自动化工作流与云端质量门禁
│   └── workflows/                #    GitHub Actions 自动化 CI/CD 流水线配置
│
├── spec/                         # 📋 专案整体规划方案、技术规格书与设计对齐规范
│   ├── v3_refactor_plan.md       #    v3.0 现代桌面客户端重构整体规划方案
│   ├── detailed_design.md        #    v3.0 底层类图、交互信号与核心算法详细设计方案
│   ├── execution_plan.md         #    v3.0 重构落地执行计划与阶段质量验收方案
│   └── tdd_and_verification_plan.md # v3.0 测试驱动开发 (TDD) 与系统验收方案
│
├── docs/                         # 📚 统一文档中心 (集中管理需求、设计与演进路线)
│   ├── requirements.md           #    产品业务需求基线说明书
│   ├── design.md                 #    底层详细技术设计与架构实现方案
│   ├── roadmap.md                #    🗺️ 产品演进路线图与中长期演进全景书 (v3.1 ~ v4.0)
│   └── ui_prototype.md           #    🎨 界面原型图底稿与 UI/UX 演进审查规范
│
├── .agent/                       # 🤖 模块化 AI 协作工程规则库
│   └── rules/                    #    架构边界、TDD 门禁、文档生命周期等 5 大法典
│
├── src/                          # 📦 生产源代码主目录
│   └── gifcreater/               #    专案主包根命名空间
│       ├── core/                 #    ⚙️ 核心算法引擎 (纯无头计算：切片/去黑边/压缩/编码)
│       ├── ui/                   #    🖥️ 现代桌面图形界面 (基于 PyQt6 Fluent 视窗系统)
│       │   └── components/       #       可复用的通用 UI 基础组件与微卡片
│       ├── config/               #    ⚙️ 运行时配置、用户偏好持久化与预设策略管理
│       ├── i18n/                 #    🌐 国际化与多语言本地化资源包 (中文/英文等)
│       └── utils/                #    🛠️ 通用辅助工具库 (跨平台路径安全、文件 I/O 辅助)
│
├── resources/                    # 🎨 静态资产与视觉资源目录 (UI 运行时静态挂载)
│   ├── icons/                    #    应用图标、托盘图标、工具栏矢量/PNG 图标
│   ├── themes/                   #    界面主题样式、Fluent 调色板与 QSS 样式表
│   └── presets/                  #    微信表情包、小红书、Discord 等预设模板配置
│
├── tests/                        # 🧪 质量门禁自动化测试套件 (严格保护 ≥90% 覆盖率)
│   ├── unit/                     #    单元测试 (覆盖 core 引擎与基础算法)
│   ├── integration/              #    集成测试 (端到端切图与动图导出链路验证)
│   └── fixtures/                 #    测试固件与内存微型图生成器 (杜绝外部大图依赖)
│
├── scripts/                      # 🔨 工程化与发布辅助脚本目录
│   ├── build/                    #    PyInstaller 本地单文件打包与构建辅助脚本
│   └── tools/                    #    资源编译、图标转换、环境自检脚本
│
└── output/                       # 📂 [本地运行时产物，Git 严格忽略] 本地自动归档目录
    ├── gifs/                     #    动图成品导出归档
    └── frames/                   #    切片过程帧文件归档
```

---

## 三、 各核心文件夹职责与约束准则

### 1. 业务算法引擎 (`src/gifcreater/core/`)
* **准则**：纯 Python/C 原生计算，**严禁引入任何 GUI 模块**（如禁止直接或间接 `import PyQt6` 或 `import tkinter`）。
* **职责**：
  * 多帧拼图切片与边缘探测算法 (`slicer.py`)；
  * 微信表情包 ≤500KB 调色板自适应搜索与试探压缩 (`compressor.py`)；
  * GIF / WebP 动图合成与帧延时编码 (`exporter.py`)；
  * 表情包黑边白字文字叠加无头渲染引擎 (`caption.py`，零侵入、自适应描边与字体优雅回退)；
  * (v3.5+) 提示词结构化数据契约与 Agent 规范生成引擎 (`prompt_schema.py` / `agent_engine.py`)。

### 2. 交互表现层 (`src/gifcreater/ui/`)
* **准则**：专注于视图呈现与用户输入，**严禁在主线程执行耗时计算**。遵守 `UIUX-PRO-MAX` 规范。
* **职责**：
  * 现代 Fluent 窗口框架、自适应深浅色主题渲染；
  * QGraphicsView 交互画布（支持滚轮缩放、平移与网格虚线拖拽，实时配文所见即所得图层）；
  * 时间轴卡片式序列帧胶卷（支持多选、快捷键剔除废帧）；
  * 表情包配文与导出预设面板（统一下拉选择器，无缝切换微信 1:1、小红书 3:4、原画超清与 WebP）；
  * 异步 Worker 线程调度与进度信号（ProgressRing / InfoBar）联动。

### 3. 配置与国际化 (`src/gifcreater/config/` & `src/gifcreater/i18n/`)
* **职责**：
  * 负责用户偏好（如常用行列数、导出格式、默认帧率）的本地持久化读取与写入；
  * 平台导出预设规格定义 (`presets.py`)；
  * 集中管理多语言文本键值对，预留中英双语扩展能力。

### 4. 静态资产管理 (`resources/`)
* **准则**：严禁将图片、图标硬编码在代码或散落在根目录。
* **职责**：统一存放矢量 SVG、PNG 图标、应用 `.ico` 徽标、QSS 样式表与开箱即用的预设模板 JSON。

### 5. 质量保证与测试套件 (`tests/`)
* **准则**：
  * 必须使用内存微型动态图片生成器（见 `tests/fixtures/`），**严禁向仓库提交外部大体积图片素材**；
  * 核心算法与业务逻辑必须维持 **代码行覆盖率（Line Coverage）≥ 90%** 的硬性红线。

### 6. 本地输出与资产归档 (`output/`)
* **准则**：
  * 导出文件统一收拢于 `output/gifs/` 与 `output/frames/`，严禁到处散落生成；
  * 必须在 `.gitignore` 中强制忽略，绝不提交至版本库。

---

## 四、 深入文档索引导航

* 📋 **[v3.0 现代桌面客户端重构整体规划方案](file:///D:/gitfunFiles/GifCreater/spec/v3_refactor_plan.md)**：包含 `/grill-me` 深度对齐后的核心决策、纯文件夹层级规范、实施路线图与质量门禁。
* 📐 **[v3.0 详细设计方案说明书](file:///D:/gitfunFiles/GifCreater/spec/detailed_design.md)**：包含三层解耦类设计、交互时序与信号拓扑图、异步 Worker 架构与路径防御降级。
* 🛠️ **[v3.0 重构落地执行计划方案](file:///D:/gitfunFiles/GifCreater/spec/execution_plan.md)**：包含六阶段任务拆解、各 Step 可核验交付物标准、覆盖率质量门禁与回滚预案。
* 🧪 **[v3.0 测试驱动开发 (TDD) 与系统验证方案](file:///D:/gitfunFiles/GifCreater/spec/tdd_and_verification_plan.md)**：包含内存动态测试固件设计、90% 覆盖率单测矩阵、TC-01~TC-10 端到端交互验收用例与微信过审级验证。
* 📖 **[PRD 产品需求与演进基线说明书](file:///D:/gitfunFiles/GifCreater/docs/requirements.md)**：包含 v2.0、v2.1 规范及 v3.0 现代桌面客户端重构的详细业务需求。
* 📐 **[系统技术设计与规格说明书](file:///D:/gitfunFiles/GifCreater/docs/design.md)**：包含系统宏观技术拓扑、UI Wireframe、异步线程模型与 CI/CD 自动化构建发布架构。
* 🛡️ **[AI 代理协作准则与操作边界](file:///D:/gitfunFiles/GifCreater/AGENTS.md)**：包含质量门禁、Git 干净度红线与功能研发分级协作流程。
