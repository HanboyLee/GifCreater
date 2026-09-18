<p align="center">
  <img src="resources/icons/app_icon.png" width="120" height="120" alt="GifCreater Logo">
</p>

# 🎞️ GifCreater Studio (动图工坊)

<p align="center">
  <a href="README.md"><b>English</b></a> | <b>简体中文</b>
</p>

<p align="center">
  <a href="https://github.com/HanboyLee/GifCreater/releases/tag/latest"><img src="https://img.shields.io/badge/Release-v3.4.3_Latest-brightgreen.svg" alt="Latest Continuous Release"></a>
  <img src="https://img.shields.io/badge/Platform-Windows%20x64-lightgrey.svg" alt="Platform: Windows x64">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/UI-Fluent%20Design%20(PyQt6)-blueviolet.svg" alt="UI: Fluent Design">
  <img src="https://img.shields.io/badge/Tests-98%20Passed-success.svg" alt="Tests: 98 Passed">
  <img src="https://img.shields.io/badge/Coverage-95.8%25-brightgreen.svg" alt="Coverage: 95.8%">
  <img src="https://img.shields.io/badge/License-MIT-orange.svg" alt="License MIT">
</p>

专为 AI 多帧分镜生图与动图/表情包创作者打造的现代化、免安装桌面动图工坊（基于 PyQt6 与 Windows 11 Fluent 现代美学体系）。

一键将 Midjourney、Stable Diffusion、Flux、DALL-E 等生成的各类多帧拼图（如 2x2、4x4、3x3 或任意行列）智能切片，并通过**投影波谷中位线自动吸附**、**自由配文排版工作室**与**全平台导出预设矩阵**，秒速合成为高品质的 GIF 与 WebP 动图。

---

## ⚡ 极速创作工作流 (Workflow)

```text
📥 导入多格大图 ➔ ⚡ 投影波谷智能吸附 ➔ ✍️ 自由拖拽配文/旋转 ➔ 🎞️ 胶卷剔除废帧 ➔ 🚀 微信/小红书/WebP 一键导出
```

---

## ✨ 核心特性矩阵 (Key Features)

### 1. 🔲 智能网格切片与投影波谷吸附 (Projection Profile Valley Snapping)
- **缝隙中位线居中锁定**：基于全通道能量与灰度方差投影积分，自动在理论等分点窗口搜索分镜留白缝隙（Gutter），并将参考线绝对锁定在物理中位线，彻底解决 AI 拼图切在边缘或手脚的痛点。
- **全透明背景原生支持**：对 RGBA 透明背景拼图素材，优先感知透明留白缝隙。
- **一键快捷对齐**：支持画布鼠标自由拖拽红虚线微调，并提供「⚡ 智能吸附参考线」与「↺ 均匀等分」一键复位。

### 2. ✍️ 表情包自由配文工作室 (What-You-See-Is-What-You-Get)
- **画布鼠标自由排版**：支持在左侧画布上直接鼠标拖拽文字图元，任意设定配文位置。
- **全向双三次旋转**：支持 `-180° ~ 180°` 任意角度倾斜与动态旋转，带有角度快捷按钮（-45°、-15°、0°、+15°、+45°）。
- **RGBA 双色与透明度滑块**：文字主色与描边色独立自定义，自适应高清晰度描边与优雅字体回退。
- **2×2 风格模板网格**：一键套用「🔥 经典黑白」、「⚡ 荧光亮黄」、「🚨 高能爆红」、「👻 半透水印」。
- **2×3 罗盘快捷归位**：顶左、顶中、顶右、正中、底中、底右秒级定位。

### 3. 📦 全平台导出预设矩阵 (Multi-Platform Presets)
- **💬 微信表情包模式**：严格满足移动端三大硬指标（文件大小 $\le 500\,\text{KB}$、最长边 $\le 240\,\text{px}$、保留透明通道），内置自适应五阶调色板衰减与多级保底压缩算法，保证 100% 成功添加。
- **📕 小红书 3:4 社交动图**：自动等比缩放至社交平台推荐的 1080px 高清规格。
- **🌟 原画超清 GIF**：保留原图原始分辨率与色彩细节，满足高画质收藏与展示。
- **⚡ 高保真 WebP 动图**：全彩 1600 万色与原生 Alpha 通道支持，压缩率高且体积小巧。

### 4. ⏱️ 帧时序高保真与全平台 Boomerang
- **100% 尊重配置**：彻底废除硬编码截断，精准保真用户设定的帧间隔（毫秒）与尾帧停顿时间。
- **GIF89a 规范量化保护**：规范至 10ms 颗粒度且确保 $\ge 20\text{ms}$，杜绝播放器时序降级缺陷。
- **全平台 Boomerang 往复循环**：全预设统一支持乒乓往复展开（`[A, B, C, B]`），首尾顺滑衔接，彻底消除跳帧感。

### 5. 🎨 Windows 11 Fluent 美学与集中式主题管理
- **深浅双模热重载**：集中式 `ThemeManager` 与高对比度设计令牌，一键无缝热重载 QSS 样式表，深色模式高对比度保证绝不出现“黑底黑字”。
- **弹性工作区分割器**：左侧交互视窗与右侧控制台支持鼠标自由拖拽伸缩（带 320px~480px 弹性区间与安全避让区）。
- **原生独立品牌徽标**：采用「极简双态几何切片」官方品牌 Logo，注册 Windows 原生 `AppUserModelID`，任务栏与窗口展示专属徽标。

### 6. 🎞️ 时间轴卡片式序列帧胶卷
- 可视化展示所有切片单帧，点击红叉 `❌` 即可实时剔除 AI 生图瑕疵帧或冗余废帧，画布播放与导出同步响应，并支持一键撤销恢复。

---

## 🚀 极速上手与下载安装

### 选项 1：免安装绿色版 (Windows x64) — 强烈推荐
从 GitHub Releases 直接获取最新预编译单文件版本：
- 📦 **[下载完整便携包 GifCreater-windows-x64.zip (推荐)](https://github.com/HanboyLee/GifCreater/releases/download/latest/GifCreater-windows-x64.zip)**
- ⚡ **[下载可执行程序 GifCreater.exe (自带品牌图标)](https://github.com/HanboyLee/GifCreater/releases/download/latest/GifCreater.exe)**

> **无需配置 Python 或任何依赖**。解压后双击 `GifCreater.exe` 即可直接使用，生成的动图与切片帧会自动归档至同级目录下的 `output/` 文件夹。

---

### 选项 2：从源码运行 (跨平台开发者模式)
支持 Python 3.10+ (已在 Python 3.11 与 3.13 验证)：

```bash
# 1. 克隆代码仓库
git clone https://github.com/HanboyLee/GifCreater.git
cd GifCreater

# 2. 安装依赖库
pip install -r requirements.txt

# 3. 启动桌面端
python main.py
```

---

## 🏛️ 工程架构与技术规格索引

专案遵守严格的无头解耦架构与 90% 覆盖率质量门禁，详见核心文档：
- 🏛️ **[ARCHITECTURE.md](ARCHITECTURE.md)**：专案架构全景、纯文件夹层级规范与三层解耦体系
- 📖 **[docs/requirements.md](docs/requirements.md)**：PRD 产品业务需求与全生命周期版本基线
- 📐 **[docs/design.md](docs/design.md)**：底层详细技术设计、波谷吸附算法与主题令牌规范
- 🗺️ **[docs/roadmap.md](docs/roadmap.md)**：产品长期演进路线图 (v3.5 Prompt 收集器与 Agent 引擎)
- 🛡️ **[AGENTS.md](AGENTS.md)**：AI 代理协作准则与 TDD 90% 覆盖率质量门禁法典

---

## 📄 开源许可证 (License)

本项目基于 [MIT License](LICENSE) 协议开源。
