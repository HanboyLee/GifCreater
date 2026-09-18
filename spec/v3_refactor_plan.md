# 📋 GifCreater v3.0 现代桌面客户端重构整体规划方案 (Specification & Plan)

> **文档状态**：已对齐并确立 (Confirmed via `/grill-me`)  
> **制定时间**：2026-09-17  
> **归档位置**：`spec/v3_refactor_plan.md`  
> **关联文档**：[ARCHITECTURE.md](file:///D:/gitfunFiles/GifCreater/ARCHITECTURE.md) | [docs/requirements.md](file:///D:/gitfunFiles/GifCreater/docs/requirements.md) | [docs/design.md](file:///D:/gitfunFiles/GifCreater/docs/design.md)

---

## 一、 重构背景与核心动因

当前客户端基于 Python 原生 Tkinter 开发，虽已具备 16 帧切片、去黑边探测与微信表情包（≤500KB）自适应调色板压缩等核心能力，但在 UI 展示层存在显著瓶颈：
1. **视觉表现力不足**：控件外观停留在早期系统原生灰底风格，缺乏现代阴影、圆角、层次材质（如 Windows 11 Mica/Acrylic）与动效；
2. **交互体验局限**：切片分割线无法流畅拖拽微调与磁吸对齐，序列帧缺乏时间轴卡片式浏览与多选剔除能力；
3. **主线程偶尔阻塞**：计算密集型任务（如调色板试探循环）缺乏系统性异步线程隔离，可能导致界面短暂未响应。

为彻底解决上述痛点，决定在**坚守“纯本地离线单机桌面应用”**的前提下，对 UI 展示层与专案工程目录进行体系化重构。

---

## 二、 核心架构原则与设计哲学

1. **100% 本地算力与绝对隐私安全 (Local-First & Zero Leakage)**：
   - 杜绝传统 Web 上传到云端服务器的架构形态。所有图像切片、像素运算、微信调色板试探与动图导出，**100% 运行在用户本地 CPU/内存**；
   - 零云端带宽与算力成本，绝对保护创作者素材隐私。
2. **三层分工解耦模型 (Three-Tier Decoupling)**：
   - **表现层 (Presentation Layer)**：基于 PyQt6 + PyQt-Fluent-Widgets，构建现代 Windows 11 Fluent 风格交互界面；
   - **调度与状态层 (Coordination Layer)**：通过 `QThread` 与 Qt 信号槽实现全异步任务管理与状态分发，彻底消除界面卡顿；
   - **核心算法引擎层 (Core Engine Layer)**：继承 `gif_tool.py` 算法，严格保证纯 Python/C 运算，零 GUI 依赖，接受 ≥90% 覆盖率门禁保护。

---

## 三、 `/grill-me` 深度访谈确认的核心决策基线

| 决策分支 | 裁定结论 | 实施准则 |
| :--- | :--- | :--- |
| **1. 迁移过渡策略** | **平滑桥接过渡** | 核心算法收拢至 `src/gifcreater/core/`；根目录保留 `gif_tool.py` 转发垫片，保障旧脚本与测试零破坏。 |
| **2. 底层 Qt 选型** | **PyQt6 + PyQt-Fluent-Widgets** | 官方适配度最佳，原生支持亚克力/云母毛玻璃材质、自适应深浅色主题与平滑微动效。 |
| **3. 旧 UI 处理方案** | **彻底淘汰原 Tkinter 代码** | 彻底移除原 `gui.py`，不保留历史包袱，专案轻装前行。 |
| **4. 扩展模块落地节奏** | **渐进式交付** | 本轮优先攻克高颜值 Fluent 交互界面与主题系统；同步预留 `config/`、`i18n/`、`resources/` 规范文件夹层级骨架。 |

---

## 四、 面向全生命周期的纯文件夹层级规范 (Directory Hierarchy)

本规范聚焦高内聚、低耦合的**文件夹层级（Directory Level）**划分，全面涵盖当前及未来规划所需的所有工程目录：

```text
GifCreater/
│
├── .github/                      # 🤖 自动化工作流与云端质量门禁
│   └── workflows/                #    GitHub Actions 自动化 CI/CD 流水线配置
│
├── spec/                         # 📋 专案整体规划方案、技术规格书与设计对齐规范 (本目录)
│
├── docs/                         # 📚 统一文档中心 (唯一法定文档根目录)
│   ├── prd/                      #    产品需求说明书 (PRD)、功能特性演进与基线规划
│   ├── architecture/             #    架构设计、技术决策记录 (ADR)、性能/安全规范
│   └── manuals/                  #    用户使用手册、开发者指南、版本更新说明
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

## 五、 核心交互与视觉设计规格

### 1. 现代化界面视窗 (Fluent Window)
* 采用 `FluentWindow` 作为顶级窗口，自动挂载 Windows 11 Mica/Acrylic 特效材质；
* 右上角提供深色模式 / 浅色模式 / 跟随系统的一键切换按钮；
* 高分屏 (High DPI / 4K / 2K) 自动缩放，图标与文字矢量化渲染，彻底消除模糊。

### 2. 交互式缩放画布 (QGraphicsView Canvas)
* 支持鼠标滚轮平滑缩放，支持按住空格键或鼠标中键平移素材；
* 红色网格分割线具备悬停高亮、鼠标直接抓取平移拖拽，并提供边缘磁吸辅助；
* 原地动图播放器，支持循环模式（正序 / 乒乓往复 Boomerang）流畅播放。

### 3. 时间轴卡片式序列帧胶卷 (Filmstrip)
* 底部采用横向滚动的卡片流式布局；
* 每帧带有序号标号，鼠标悬浮显示删除图标；
* 支持单击选中、Ctrl/Shift 多选、按键盘 `Delete` 键一键批量剔除废帧；
* 剔除后实时联动原地播放器与导出引擎。

### 4. 异步多线程调度与反馈系统
* 切片拆解与动图导出封装为后台 `QThread` 任务；
* 界面显示 Fluent `ProgressRing` 旋转环与实时状态文本，杜绝界面假死；
* 操作完成使用轻量级 `InfoBar` 气泡通知提示成果与文件体积（如“微信表情包已成功压缩至 468KB”）。

---

## 六、 实施路线图与质量门禁

### 阶段一：文件夹骨架初始化与核心引擎收拢
1. 创建 `src/gifcreater/{core,ui,config,i18n,utils}`、`resources/`、`scripts/` 等规范文件夹；
2. 将 `gif_tool.py` 算法模块重构至 `src/gifcreater/core/`，根目录保留 `gif_tool.py` 转发别名；
3. 运行 `pytest tests/ --cov=src/gifcreater/core --cov-fail-under=90`，确保 90% 覆盖率门禁立即通过。

### 阶段二：PyQt6 Fluent 表现层构建
1. 安装并配置 `PyQt6` 与 `PyQt-Fluent-Widgets` 依赖；
2. 构建 `main_window.py`、`canvas.py`、`filmstrip.py`、`sidebar.py` 与异步 `workers.py`；
3. 实现主入口 `main.py` 并清理旧版 `gui.py`。

### 阶段三：构建适配与交付自检
1. 更新 `GifCreater.spec`，验证 PyInstaller 打包单文件 EXE 的兼容性；
2. 执行全流程功能自检与覆盖率报告验证。

---

## 七、 持续维护铁律契约

> 凡后续开发、功能迭代或架构变更，**必须同步更新专案根目录的 `ARCHITECTURE.md`、`spec/v3_refactor_plan.md` 及 `docs/` 下的对应 PRD 与设计文档**，确保代码实现与文档规范始终保持 100% 强对齐。
