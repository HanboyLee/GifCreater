# 🗺️ GifCreater Studio 产品演进路线图 (Product Roadmap)

> **当前基线版本**：`v3.0.0 (Fluent & Headless Stable)`  
> **文档维护原则**：本文档定义 GifCreater 的长期技术演进、场景扩展与版本发布节奏，作为后续所有功能迭代与立项规格书（`spec/`）的顶层指南。

---

## 一、 产品长期愿景与定位 (Product Vision)

专为 **AI 多帧分镜创作者、连环画画师与表情包设计师** 打造的 **“100% 纯本地、零隐私泄露、轻量且高颜值的专业级动图工坊”**。

- **核心价值主张**：
  1. **极致隐私与离线**：绝不依赖云端，所有素材、切片和算法 100% 在用户本地设备安全运行；
  2. **端到端一气呵成**：从多帧大图拖入、智能吸附微调、原地动态预览、废帧剔除到一键导出微信合规表情包，全流程仅需数秒；
  3. **可扩展的工程底座**：严格恪守无头解耦（Headless Core）、90% 测试行覆盖率与自动化 CI/CD 绿色交付。

---

## 二、 版本演进全景里程碑 (Version Milestones)

```text
  【v3.0 基线】          【v3.1 吞吐提升】       【v3.2 表现力增强】       【v4.0 本地端侧AI】
  PyQt6 Fluent 重构   ──> 多图批量处理流水线 ──> 表情包字幕与贴纸叠加 ──> 纯本地离线智能抠图
  无头核心算法解耦         全平台预设管理器        视频/动图双向互转(MP4)    光流法智能运动补帧
  97% TDD 覆盖率门禁       帧反转与重映射滤镜      APNG 现代格式矩阵         跨平台适配 (macOS)
  (已完成交付)             (近景目标)              (中景目标)                (远景目标)
```

---

### 📍 v3.0 (Current Baseline - Stable) —— 架构现代化与工业级质量基线
- [x] **架构解耦**：彻底淘汰旧 Tkinter 单脚本（`gui.py`），无损拆分为纯无头核心算法（`src/gifcreater/core/`）；
- [x] **Fluent 现代化表现层**：引入 PyQt6 + PyQt-Fluent-Widgets，支持 Mica/Acrylic、深浅色模式与 WCAG 高对比度；
- [x] **交互式画布与胶卷**：滚轮以指针为锚点平滑缩放、红色分割线抓取拖拽与 8px 磁吸、流式胶卷按 `Delete` 剔除废帧；
- [x] **非阻塞异步调度**：切片与导出全部由 `QThread` 承载，主线程坚守 60 FPS，配合旋转环与 InfoBar 气泡；
- [x] **微信表情包硬约束**：严格确保文件体积 $\le 500\,\text{KB}$ 且最长边 $\le 240\,\text{px}$，五阶自适应调色板收敛；
- [x] **质量门禁达成**：全套 67 项纯内存 Mock 单测，代码行覆盖率达 **97.31%**；
- [x] **绿色免安装交付**：独立单文件 `dist/GifCreater.exe`，免 Python 环境离线秒开。

---

### 📍 v3.1 (Next Horizon) —— 批量处理吞吐与平台预设自由度
**目标**：解决“只能单张处理”的生产力瓶颈，实现流水线式高吞吐生产。

1. **批量拖拽与多任务切片队列 (Batch Processing Pipeline)**：
   - 支持一次性拖入 20+ 张多帧大图或整个文件夹；
   - 后台多线程队列自动按照预设切片并输出，支持任务进度总览与一键打开全部成品；
2. **用户自定义预设管理器 (Preset Configuration Engine)**：
   - 允许用户自由新建、保存、导出与导入平台规格预设（如：`小红书 3:4`、`抖音 9:16`、`Discord Emoji`、`B站动态`）；
   - 预设涵盖：切片网格（行×列）、目标尺寸、帧间隔时间、尾帧停留时长、循环模式与色彩精度；
3. **帧处理增强滤镜 (Frame Filter Utilities)**：
   - 支持单帧顺序反转（Reverse）；
   - 支持变速曲线（首尾慢速、中间加速等节奏重映射）；
4. **快捷键全域支持 (Pro Keyboard Shortcuts)**：
   - `Ctrl+O` 快速打开、`Ctrl+S` 快捷导出、`Space` 画布抓手平移、`Ctrl+Z` 恢复已删帧。

---

### 📍 v3.2 (Future Expansion) —— 动图编辑与动态表现力
**目标**：摆脱二次进 PS 的繁琐流程，在工坊内部完成表情包文字制作与视频格式互通。

1. **表情包字幕与花字图层 (Text & Caption Overlay)**：
   - 提供经典的“表情包黑边白字”、“顶部/底部配文横条”、“描边艺术字”；
   - 支持逐帧独立配文或全局统一文案，支持字体、大小、对齐与描边粗细实时调节；
2. **视频与动图双向互转 (MP4 / WebM $\longleftrightarrow$ GIF / WebP)**：
   - 纯本地视频解析：支持导入一段 MP4/WebM 短视频，拖动双滑块截取 3~5 秒片段，一键转为微信表情包；
   - 动图转视频：将合成的帧序列一键导出为高清 MP4 视频，方便直接发布至视频号、抖音等短视频平台；
3. **色彩与画质微调面板 (Color Grading)**：
   - 亮度、对比度、饱和度、锐化微调滑块；
   - 提供复古复写、黑白单色、赛博高对比度等风格滤镜。

---

### 📍 v4.0 (Long-term Evolution) —— 纯本地离线端侧 AI 赋能
**目标**：利用端侧轻量 AI 模型，在 100% 保护用户隐私的前提下提供断层式体验优势。

1. **纯本地离线智能抠图 (100% Offline AI Matting)**：
   - 内置轻量级端侧视觉分割模型（基于 ONNX Runtime，CPU 毫秒级推理，免显卡安装）；
   - 一键抠除多帧画面的杂乱背景，直接输出**纯透明背景高品质微信表情包**；
2. **智能运动平滑补帧 (Optical Flow Frame Interpolation)**：
   - 针对 4 帧或 6 帧动作跳跃的分镜，本地智能生成运动过渡帧，将 8 FPS 顿挫动图平滑提升至 24 FPS 丝滑流体效果；
3. **现代全格式矩阵 (Next-Gen Format Matrix)**：
   - 支持 **APNG**（高保真透明动图）、**AVIF**（超高压缩比新一代动图）与 **Lottie** 矢量动画导出；
4. **跨平台原生桌面支持 (Cross-Platform Architecture)**：
   - 依托 PyQt6 的跨平台特性，建立 macOS (Apple Silicon M系列) 与 Linux 原生安装包的 CI/CD 编译流水线。

---

## 三、 架构扩展性插槽设计 (Architecture Slots)

为了保证后续所有版本的演进**不需要重构主架构，且不破坏现有 97% 覆盖率**，底层已预留三类扩展插槽：

```text
1. 切片策略插槽 (Slicer Strategy)
   BaseSlicer ──┬──> GridSlicer (均匀网格)
                ├──> SmartDividerSlicer (边界/线条探测吸附)
                └──> [未来插槽] BatchFolderSlicer (批量自动化)

2. 帧滤镜流水线 (Frame Filter Pipeline)
   Raw Frames ──> [CropFilter] ──> [TextOverlayFilter] ──> [PaletteQuantizer] ──> Render

3. 导出器注册表 (Exporter Registry)
   ExporterFactory ──┬──> GifExporter (Pillow + 自适应调色板)
                     ├──> WebpExporter (Pillow WebP)
                     ├──> [未来插槽] ApngExporter
                     └──> [未来插槽] Mp4VideoExporter
```

---

## 四、 需求立项与迭代交付机制 (RFC & Sprint Cycle)

为保障后续开发高效、规范，任何新功能的引入均需按照以下流程推进：

1. **阶段 1：RFC 需求立项 (Request for Comments)**：
   - 在专案根目录 `spec/` 目录下创建 `spec/vX.Y_feature_name.md`，明确用户故事、UI 线框图、API 签名与性能约束；
   - 与团队/用户讨论达成共识；
2. **阶段 2：TDD 先行与内存测试驱动**：
   - 先在 `tests/unit/` 或 `tests/integration/` 中为新功能编写纯内存动态 Mock 单元测试；
   - 必须通过 `pytest --cov --cov-fail-under=90` 门禁；
3. **阶段 3：四件套强绑定交付**：
   - 在同一个 Commit 中，同步更新：
     - 代码实现；
     - 单元测试（绿灯且覆盖率 $\ge 90\%$）；
     - 根目录 `ARCHITECTURE.md`（如有架构演进）；
     - `docs/requirements.md`、`docs/design.md` 与 `README.md`。
