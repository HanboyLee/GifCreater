# 🛠️ GifCreater v3.0 重构落地执行计划方案 (Execution & Implementation Plan)

> **文档定位**：v3.0 现代桌面客户端重构落地的具体实施步骤、验证门禁与交付标准  
> **归档路径**：`spec/execution_plan.md`  
> **状态**：已全面落地并验证通过 (Delivered & Verified)  
> **前置方案**：[spec/v3_refactor_plan.md](file:///D:/gitfunFiles/GifCreater/spec/v3_refactor_plan.md) | [spec/detailed_design.md](file:///D:/gitfunFiles/GifCreater/spec/detailed_design.md)

---

## 一、 实施阶段总览与依赖拓扑

```text
[Step 1: 环境与依赖准备]
       │
       ▼
[Step 2: 规范文件夹层级骨架搭建]
       │
       ▼
[Step 3: 核心算法收拢与 90% 覆盖率门禁验证] ──── (质量安全门禁，不达标立即中止)
       │
       ▼
[Step 4: PyQt6 Fluent 表现层与异步调度构建]
       │
       ▼
[Step 5: 历史包袱清理 (移除旧 Tkinter 代码)]
       │
       ▼
[Step 6: PyInstaller 打包构建与端到端运行自检]
```

---

## 二、 详细实施步骤与可核验交付物

### Step 1: 环境与依赖准备 (Environment Setup)
* **执行动作**：
  1. 更新 `requirements.txt`：增加 `PyQt6>=6.5.0`、`PyQt-Fluent-Widgets>=1.5.0`、`Pillow>=10.0.0`；
  2. 更新 `requirements-dev.txt`：确保包含 `pytest`、`pytest-cov`、`pyinstaller`；
  3. 执行 `pip install -r requirements.txt` 完成本地环境安装。
* **可核验交付物**：
  * 控制台执行 `python -c "import PyQt6; import qfluentwidgets; print('Dependencies OK')"` 无报错。

---

### Step 2: 规范文件夹层级骨架搭建 (Folder Hierarchy Setup)
* **执行动作**：
  1. 创建面向未来的完整纯文件夹体系：
     - `src/gifcreater/core/`
     - `src/gifcreater/ui/components/`
     - `src/gifcreater/config/`
     - `src/gifcreater/i18n/`
     - `src/gifcreater/utils/`
     - `resources/icons/`、`resources/themes/`、`resources/presets/`
     - `tests/unit/`、`tests/integration/`、`tests/fixtures/`
     - `scripts/build/`、`scripts/tools/`
  2. 在各 Python 包目录下创建包含包版本定义的 `__init__.py`。
* **可核验交付物**：
  * 文件系统完整具备上述层级树，且无多余杂乱文件。

---

### Step 3: 核心算法收拢与 90% 覆盖率门禁验证 (Core Engine Migration)
* **执行动作**：
  1. 在 `src/gifcreater/utils/paths.py` 中实现安全的路径解析与权限防御降级机制；
  2. 将原 `gif_tool.py` 的算法无损迁移至 `src/gifcreater/core/`（拆分为 `slicer.py`、`bounds.py`、`compressor.py`、`exporter.py`）；
  3. 在专案根目录创建兼容垫片 `gif_tool.py`（内部转发导入 `src.gifcreater.core`），确保历史依赖 0 破坏；
  4. 同步更新 `tests/` 单元测试，测试固件完全在内存中生成微型图像，无外部大图依赖；
  5. 运行 pytest 质量门禁。
* **可核验交付物与核验命令**：
  ```bash
  pytest tests/ --cov=src/gifcreater/core --cov=gif_tool --cov-fail-under=90
  ```
  * 必须输出 **Coverage >= 90%** 且所有测试用例 100% Passed。未达标严禁进入下一阶段！

---

### Step 4: PyQt6 Fluent 表现层与异步调度构建 (UI & Workers Implementation)
* **执行动作**：
  1. **异步调度器**：编写 `src/gifcreater/ui/workers.py`（`SliceWorker` 与 `ExportWorker`），定义进度信号流；
  2. **可交互画布**：编写 `src/gifcreater/ui/canvas.py`（`InteractiveCanvas`，基于 `QGraphicsView` 实现缩放、平移与网格虚线拖拽）；
  3. **卡片胶卷**：编写 `src/gifcreater/ui/filmstrip.py`（`FilmstripWidget`，实现水平卡片流式滚动、多选与 Del 键删除）；
  4. **控制面板**：编写 `src/gifcreater/ui/sidebar.py`（`ControlSidebar`，集成 Fluent 参数微调滑块与导出目标单选）；
  5. **主窗口聚合**：编写 `src/gifcreater/ui/main_window.py`（`MainWindow(FluentWindow)`，聚合上述组件并绑定深浅色主题切换）；
  6. **主入口引导**：编写专案根目录 `main.py`（初始化高分屏 DPI 缩放、载入应用并拉起 Qt 视窗）。
* **可核验交付物**：
  * 执行 `python main.py`，成功弹出高颜值 Fluent 现代视窗，可正常加载图片并预览。

---

### Step 5: 历史包袱清理与启动脚本更新 (Legacy Cleanup)
* **执行动作**：
  1. 彻底删除原旧版 Tkinter 界面代码 `gui.py`；
  2. 更新根目录的 `run_gui.bat`，改为拉起 `python main.py`。
* **可核验交付物**：
  * 双击 `run_gui.bat` 直接拉起全新 v3.0 Fluent 界面。

---

### Step 6: PyInstaller 打包构建与端到端运行自检 (Packaging & Release Verification)
* **执行动作**：
  1. 更新 `GifCreater.spec`，适配新的入口 `main.py` 与 `PyQt6` / `qfluentwidgets` 资源挂载；
  2. 在本地执行 PyInstaller 构建，生成独立的绿色单文件 `dist/GifCreater.exe`；
  3. 验证构建产物运行状态：导入一张多帧素材测试拖拽分割、废帧剔除、微信表情包导出，验证文件体积是否严格 `<= 500KB`。
* **可核验交付物**：
  * 控制台输出可执行文件打包成功，且生成的 EXE 在离线环境下正常启动运行。

---

## 三、 应急回滚策略 (Rollback Plan)

* 本次重构依托 Git 分支/版本管理，在每完成一个 Step 后创建明确的本地提交；
* 若在 Step 4 或 Step 6 遇到不可克服的系统级兼容问题，可一键回滚代码并借助保留的兼容垫片快速恢复系统可用性。
