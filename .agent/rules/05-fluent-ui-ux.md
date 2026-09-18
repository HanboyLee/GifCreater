# 05 - Fluent UI 美学与非阻塞交互规范 (UI/UX Standards)

GifCreater 基于 Windows 11 Fluent Design（PyQt6 + PyQt-Fluent-Widgets）构建。界面不仅要现代化高颜值，更要保证高帧率流畅度。

---

## 1. 现代化视觉美学标准 (Fluent Design & Contrast)

1. **深浅色模式与 Windows 11 材质**：
   - 必须支持深色（Dark）与浅色（Light）模式无缝切换；
   - 窗口启用系统级 Mica 或 Acrylic 半透明微光材质。
2. **WCAG 深色模式高对比度硬规范**：
   - 严禁出现“白底白字”或“深底深字”的低对比度残缺；
   - **深色标准调色板**：
     - 画布与胶卷工作区底色：`#181818`；
     - 控制卡片背景色 (`CardWidget`)：`#272727`；
     - 卡片边框线 (`Border`)：`1px solid #3d3d3d`；
     - 主文字颜色 (`Primary Text`)：`#f0f0f0` 或 `#ffffff`；
     - 次要提示文字 (`Secondary Text`)：`#a0a0a0`；
     - 主题强调色 (`Accent Color`)：Windows 11 Fluent 经典蓝或品牌色。

---

## 2. 异步调度与防假死标准 (Non-blocking UI & 60 FPS)

1. **重型计算强制异步化**：
   - 所有预估耗时 $> 50\,\text{ms}$ 的计算（如切片探测、调色板试探、GIF/WebP 编码保存），**必须由 `QThread` 异步工作线程承载 (`workers.py`)**；
   - **绝对禁止在 Qt 主 GUI 线程中执行耗时的文件 I/O、PIL 图像变换或量化运算**。
2. **用户交互反馈体验**：
   - 异步任务执行期间，主界面必须保持 60 FPS 流畅响应（窗口可自由拖拽、缩放，绝无 Windows 标题栏“(未响应)”假死现象）；
   - 底部或侧边栏必须展示流畅转动的 `ProgressRing`；
   - 任务完成后必须弹出轻量级 Fluent `InfoBar` 气泡通知，并在右下角提供“打开目录”快捷动作。

---

## 3. 画布与胶卷交互标准 (Canvas & Filmstrip)

1. **交互画布 (`InteractiveCanvas` 基于 `QGraphicsView`)**：
   - **鼠标锚点平滑缩放**：支持滚轮缩放，且必须以当前鼠标指针所在的图像坐标为锚点进行缩放（缩放范围 0.1x ~ 10x）；
   - **空格拖拽平移**：按住空格键或鼠标中键可平移画布；
   - **可交互网格分割线**：红色虚线分割线支持鼠标抓取左右/上下微调，悬停时指针自动变为 `SplitHCursor` / `SplitVCursor`，并支持 8px 边缘磁吸。
2. **序列帧胶卷 (`FilmstripWidget`)**：
   - 采用流式卡片水平平滑滚动；
   - 支持单选与多选废帧，按键盘 `Delete` 键可即时剔除瑕疵帧；
   - 剔除废帧后，画布原地动图播放器与导出序列必须**即时同步重排生效**。

---

## 4. 原型图生命周期与迭代审查流程 (UI Prototype Lifecycle)

为避免界面频繁改动与认知偏差，确立严格的原型前置生命周期：

1. **改界面必先改 HTML 原型与设计规范**：
   - 任何涉及控件增减、布局重排、弹窗或右侧卡片变动，**必须先在 `docs/prototype.html` 实现可交互的动态高保真原型，并在 `docs/ui_prototype.md` 中同步线框图与交互规格**；
2. **审查清单与用户拍板**：
   - AI 必须在原型文档末尾提供包含结构、交互、对比度等维度的显式 Review Checklist，交由用户在浏览器直接点击体验并审核；
   - **未获得用户明确确认之前，严禁直接修改 `src/gifcreater/ui/` 下的代码**；
3. **像素级代码实施**：
   - 用户确认后，严格依据原型图编写 PyQt6 控件，确保界面最终渲染效果与原型图 100% 对应。

---

## 5. UIUX-PRO-MAX 强制调用与设计智能规范 (Mandatory UIUX-PRO-MAX Skill)

**法定规则铁律**：所有在进行**原型设计（HTML/CSS/JS）**或在**产品 UI 表现层撰写代码（`src/gifcreater/ui/`、PyQt6 控件、QSS 样式表）**时，**必须强制调用并严格遵循 `UIUX-PRO-MAX` 这个 Skill**。

### 执行规范：
1. **原型与界面生成前**：
   - 必须通过 `python C:\Users\Administrator\.agents\skills\ui-ux-pro-max\scripts\search.py` 检索设计智能数据库；
   - 检索领域涵盖：
     - `--domain style`（极简、暗黑模式、玻璃态等高阶视觉风格）；
     - `--domain color`（严格提取符合 WCAG 对比度、具备品牌一致性的色彩微调搭配）；
     - `--domain typography`（现代高质量字体配对）；
     - `--domain ux`（按钮点击反馈、防呆设计、防抖、微动效与边缘防溢出）；
2. **严禁随性拼凑 UI**：
   - 严禁未经 `UIUX-PRO-MAX` 调色板与规范校验擅自使用通用色（如纯白、纯黑、杂乱蓝）；
   - 所有间距、圆角、悬停态、聚焦态必须符合设计智能数据库的最佳实践。
