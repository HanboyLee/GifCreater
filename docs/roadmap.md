# 🗺️ GifCreater Studio 产品演进路线图 (Product Roadmap)

> **当前基线版本**：`v3.5.0 (Windows Native Stable)`  
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
  【v3.0~v3.5 基线】        【v3.6 吞吐互转】       【v4.0 本地端侧AI】
  Fluent重构/无头解耦   ──> 多图批量处理流水线 ──> 纯本地离线智能抠图
  配文旋转/平台预设         视频/动图双向互转(MP4)    光流法智能运动补帧
  Prompt工作台/Jev门禁      帧反转与重映射滤镜      APNG/现代格式矩阵
  (已完成全量交付)          (中景目标)              (远景目标)
```

---

### 📍 v3.0 ~ v3.5 (Current Baseline - Stable) —— 现代表现层、核心算法、Prompt 工作台与交付体验闭环 (已完成交付)

- [x] **v3.0 现代桌面客户端体验升级 (Fluent UI & Headless Core)**：
  - [x] 彻底淘汰旧 Tkinter 单脚本，解耦为纯无头核心算法模块；
  - [x] 引入 PyQt6 + PyQt-Fluent-Widgets，支持亚克力/云母、深浅色模式与高对比度令牌；
  - [x] 交互式流式画布与时间轴胶卷，滚轮平滑缩放、参考线磁吸微调、`Delete` 键废帧剔除；
  - [x] 全面采用 `QThread` 异步非阻塞调度，界面保持 60 FPS，气泡通知取代弹窗；
  - [x] 严格微信表情包物理红线约束（最长边 $\le 240\text{px}$、体积严格 $\le 500\text{KB}$、五阶自适应调色板）；
  - [x] 建立 90% 行覆盖率测试门禁（达成 97.31%）与 GitHub Actions 全自动发布流水线。
- [x] **v3.1 平台预设管理器与表情包配文增强 (Text Overlay & Presets)**：
  - [x] 统一 Fluent 下拉预设选择器（微信表情包 1:1、小红书竖版 3:4、原画超清 GIF、高保真 WebP）；
  - [x] 零侵入文字叠加引擎：画布直接鼠标抓取拖拽、3×3 九宫格相对比例快捷对齐；
  - [x] 任意角度旋转（-180° ~ +180°）、双三次插值抗锯齿；
  - [x] 颜色拾取、0~100% 透明度调节、0~10px 描边轮廓定制及 4 款经典风格模板。
- [x] **v3.4 交互细节与品牌视觉精细化规范 (Fidelity & Visual Identity)**：
  - [x] **v3.4.1 帧间隔保真与微信往复修复**：消除微信 120ms 截断与尾帧抹平，支持 GIF89a 10ms 量化对齐，全预设支持 Boomerang 往复；
  - [x] **v3.4.2 智能网格线投影波谷吸附**：投影能量积分波谷中位线（Centerline）智能识别分镜缝隙，自动居中对齐；
  - [x] **v3.4.3 官方品牌图标与 Windows 桌面原生挂载**：「极简双态几何切片」官方 Logo，16~256px 全尺寸 ICO，任务栏独立进程与 PyInstaller 内嵌徽标。
- [x] **v3.5 Prompt 工作台与自然语言分镜 Agent (Prompt Workbench & Jev Semantic Gate)**：
  - [x] **v3.5.0 本地离线工作台与收藏库**：左侧三页导航（工坊 / Prompt / 设置）、SQLite3 主存、网格快捷+自定义行列（1~20）、横排主题持久化与 JSON/MD 导出；
  - [x] **v3.5.1 设置 API 与分镜完善 Agent**：OpenRouter 兼容自然语言分镜完善、Windows DPAPI 独立密钥存储、TypeSafe Jev 语义决策与验车门禁。

---

### 📍 v3.6 (Next Horizon) —— 批量处理吞吐与视频格式互通 (中景目标)
**目标**：解决大批量素材处理的生产力瓶颈，实现流水线式高吞吐生产与视频互通。

1. **批量拖拽与多任务切片队列 (Batch Processing Pipeline)**：
   - 支持一次性拖入 20+ 张多帧大图或整个文件夹；
   - 后台多线程队列自动按照预设切片并输出，支持任务进度总览与一键打开全部成品；
2. **视频与动图双向互转 (MP4 / WebM $\longleftrightarrow$ GIF / WebP)**：
   - 纯本地视频解析：支持导入一段 MP4/WebM 短视频，拖动双滑块截取 3~5 秒片段，一键转为微信表情包；
   - 动图转视频：将合成的帧序列一键导出为高清 MP4 视频，方便直接发布至视频号、抖音等短视频平台；
3. **帧处理增强滤镜与快捷键全域支持 (Pro Utilities)**：
   - 支持单帧顺序反转（Reverse）与节奏变速曲线；
   - `Ctrl+O` 快速打开、`Ctrl+S` 快捷导出、`Space` 画布抓手平移、`Ctrl+Z` 恢复已删帧；
4. **色彩与画质微调面板 (Color Grading)**：
   - 亮度、对比度、饱和度、锐化微调滑块与风格色彩滤镜。

---

### 📍 v4.0 (Long-term Evolution) —— 纯本地离线端侧 AI 赋能 (远景目标)
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

为了保证后续所有版本的演进**不需要重构主架构，且不破坏现有 90%+ 覆盖率**，底层已预留四类扩展插槽：

```text
1. 切片策略插槽 (Slicer Strategy)
   BaseSlicer ──┬──> GridSlicer (均匀网格)
                ├──> SmartDividerSlicer (边界/线条探测吸附)
                └──> [v3.6 插槽] BatchFolderSlicer (批量自动化)

2. 帧滤镜流水线 (Frame Filter Pipeline)
   Raw Frames ──> [CropFilter] ──> [TextOverlayFilter] ──> [PaletteQuantizer] ──> Render
                                  └──> [v3.6 插槽] ReverseFilter / CurveFilter

3. 导出器注册表 (Exporter Registry)
   ExporterFactory ──┬──> GifExporter (Pillow + 自适应调色板)
                     ├──> WebpExporter (Pillow WebP)
                     ├──> [未来插槽] ApngExporter
                     └──> [v3.6 插槽] Mp4VideoExporter

4. 提示词与 Agent 扩展插槽 (Prompt & Agent Slots)
   AgentEngine ──┬──> OpenAICompatibleAgent (DeepSeek / OpenAI / 本地 Ollama)
                 └──> ClaudeAgent / GeminiAgent
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
3. **阶段 3：文档与代码强绑定原子交付 (Atomic Delivery)**：
   - 在同一个 Commit 中，同步推进：
     - 代码实现与单元测试（通过且覆盖率 $\ge 90\%$）；
     - `docs/requirements.md`（将完成项由 `- [ ]` 推进为 `- [x]`，并追加 Changelog）；
     - `docs/design.md`（追加增量设计）与 `ARCHITECTURE.md`（如有架构变动）；
4. **阶段 4：大版本里程碑结项回写 (Milestone Promotion)**：
   - 当某个里程碑的所有需求已全部落地并发布后，同步回写 `docs/roadmap.md`，提升当前基线版本号并校准未来路线。
