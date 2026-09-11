# 🎞️ GifCreater Studio (动画工坊)

<p align="center">
  <strong>[English](README.md) | 简体中文</strong>
</p>

<p align="center">
  <a href="https://github.com/HanboyLee/GifCreater/actions/workflows/release.yml"><img src="https://github.com/HanboyLee/GifCreater/actions/workflows/release.yml/badge.svg" alt="CI/CD Release Pipeline"></a>
  <a href="https://github.com/HanboyLee/GifCreater/releases/tag/latest"><img src="https://img.shields.io/badge/Release-Latest_Continuous-brightgreen.svg" alt="Latest Continuous Release"></a>
  <img src="https://img.shields.io/badge/Platform-Windows%20x64-lightgrey.svg" alt="Platform: Windows x64">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Coverage-%E2%89%A590%25-success.svg" alt="Coverage >= 90%">
  <img src="https://img.shields.io/badge/License-MIT-orange.svg" alt="License MIT">
</p>

一个轻量、高效、免安装的多帧拼图拆解与动图精修桌面工坊。支持将多帧故事图（如 16 帧 4x4、6 帧竖向长图条、3x3 连环画等）一键拆解并合成为流畅的 GIF 或 WebP 动图。

---

## 🌟 核心特色功能

1. 🧲 **全能智能吸附 + 交互式拖拽微调**：
   - **智能识别**：自动探测黑边、白边、浅色分界线及非等高/非等宽格子的真实分割边界；
   - **所见即所得拖拽**：在画布上直接使用鼠标**按住红色虚线左右/上下拖拽**，精确像素级微调；
   - **一键重新吸附**：点击「🔄 重新吸附」按钮可瞬间还原为算法最优吸附位置。
2. 📐 **实时单格切片尺寸与比例标记 (16:9 / 1:1 / 3:2 / 9:16 等)**：
   - **智能比例计算**：侧边栏与画布右上角 HUD 徽章都会**实时计算并清晰标明单格的像素尺寸与画面长宽比**（如 `1:1 正方形·表情包`、`16:9 横屏宽屏`、`9:16 竖屏短视频`、`3:2 相机经典`、`4:3 标准画幅` 等）；
   - **切片后精确核验**：底部胶卷标题栏同步展示切片后的实际单帧分辨率与画面比例。
3. 🖥️ **原地动图实时播放器**：
   - 拆解完成后在界面中央原地实时流畅播放，支持单帧步进、拖动时间轴定位、调速即改即播。
4. 🔁 **乒乓往复循环 (Boomerang)**：
   - 支持 1→2→3→2→1 往复平滑动效，消除传统单向循环首尾不连贯的跳跃感。
5. 💬 **微信自定义表情自适应优化 (目标 ≤500KB)**：
   - 画面长边等比缩放至 240px，内置多阶自适应调色板试探压缩算法（至 48 色），尽量压缩至微信表情规范（≤500KB）。*(注：极端超长帧序列建议在胶卷中适当删减冗余帧或调整帧率)*。
6. 🎞️ **胶卷式可视删帧**：
   - 底部胶卷缩略图展示所有帧，点击单帧红叉「❌」即可移除废帧或穿帮帧，动图与导出实时重构，支持「↩ 恢复已删帧」。
7. 📂 **零配置自动归档**：
   - 单文件直接拖入或选择，无需配置路径，所有拆解单帧与导出成品自动规整归档至 `output/` 目录；顶部提供「📂 打开成品目录 (output)」一键直达。

---

## 🚀 下载与使用

### 方式 1：最推荐（下载最新绿色免安装版，Windows x64）
直接从 GitHub 自动构建的最新发布页下载，开箱即用：
- 📦 **[下载最新 GifCreater-windows-x64.zip 绿色压缩包 (推荐)](https://github.com/HanboyLee/GifCreater/releases/download/latest/GifCreater-windows-x64.zip)**
- ⚡ **[下载最新 GifCreater.exe 单文件版](https://github.com/HanboyLee/GifCreater/releases/download/latest/GifCreater.exe)**
- **无需安装 Python 或任何环境**，在 64 位 Windows 系统上解压后双击即可直接使用！

---

### 方式 2：Python 源码运行（支持跨平台）
需安装 Python 3.10+（已在 3.11 与 3.13 验证，CI 使用 3.11）：

1. 克隆代码仓库：
   ```bash
   git clone https://github.com/HanboyLee/GifCreater.git
   cd GifCreater
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 启动应用：
   ```bash
   python gui.py
   # 或在 Windows 上双击 run_gui.bat
   ```

---

## 🛠️ 工程质量与 CI/CD 规范

本项目严格遵守 [AGENTS.md](AGENTS.md)（开发者与 AI 协作规范）约定的质量红线：
- **TDD 自动化测试门禁**：所有核心切片与合成算法均经过严格的单元测试，代码覆盖率门禁保持在 **≥90%**。
- **全自动化持续部署**：每次代码合入 `main` 分支并通过质量门禁后，GitHub Actions 自动构建最新的 Windows 绿色包并滚动更新至 `latest` Release。

```bash
# 本地执行测试与覆盖率门禁验证
pip install -r requirements-dev.txt
pytest tests/ --cov=gif_tool --cov-report=term-missing --cov-fail-under=90
```

---

## 📄 开源许可证

本项目采用 [MIT License](LICENSE) 开源协议。
