# 🎞️ GifCreater Studio (动画工坊)

<p align="center">
  <b>English</b> | <a href="README_zh.md"><b>简体中文</b></a>
</p>

<p align="center">
  <a href="https://github.com/HanboyLee/GifCreater/actions/workflows/release.yml"><img src="https://github.com/HanboyLee/GifCreater/actions/workflows/release.yml/badge.svg" alt="CI/CD Release Pipeline"></a>
  <a href="https://github.com/HanboyLee/GifCreater/releases/tag/latest"><img src="https://img.shields.io/badge/Release-Latest_Continuous-brightgreen.svg" alt="Latest Continuous Release"></a>
  <img src="https://img.shields.io/badge/Platform-Windows%20x64-lightgrey.svg" alt="Platform: Windows x64">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Coverage-%E2%89%A590%25-success.svg" alt="Coverage >= 90%">
  <img src="https://img.shields.io/badge/License-MIT-orange.svg" alt="License MIT">
</p>

A lightweight, portable standalone desktop studio for splitting multi-frame grid images and crafting smooth animated GIFs and WebPs. Easily unpack multi-frame storyboards (such as 16-frame 4x4, 6-frame vertical strips, 3x3 comics) and synthesize animations with one click.

> **Note on UI Language**: The current graphical interface displays in Chinese. English descriptions below include the corresponding Chinese button labels for easy reference.

---

## 🌟 Key Features

1. 🧲 **Smart Boundary Snapping & Interactive Drag Adjustment**:
   - **Intelligent Detection**: Automatically detects dark/light dividers, margins, and non-uniform grid cells.
   - **WYSIWYG Dragging**: Interactively drag red dashed divider lines directly on the canvas for pixel-level fine-tuning.
   - **One-Click Re-Snap**: Instantly reset divider lines to detected snap positions via the **`🔄 重新吸附` (Re-Snap)** button.
2. 📐 **Real-Time Cell Resolution & Aspect Ratio HUD (16:9 / 1:1 / 3:2 / 9:16, etc.)**:
   - **Dynamic Ratio Calculation**: Both the sidebar and the canvas top-right HUD badge calculate and display pixel dimensions and standard ratios in real time (e.g. `1:1 Square/Sticker`, `16:9 Widescreen`, `9:16 Vertical Video`, `3:2 Classic Photo`, `4:3 Standard`).
   - **Post-Split Inspection**: The filmstrip header immediately confirms the actual split resolution and aspect ratio.
3. 🖥️ **In-App Real-Time Animation Player**:
   - Preview animations in place with play/pause controls (**`▶ 播放动效` / `⏸ 暂停`**), frame-by-frame stepping, time slider scrubber, and instant playback speed adjustments.
4. 🔁 **Boomerang Ping-Pong Loop**:
   - Transforms sequential frames into a seamless back-and-forth loop (1→2→3→2→1), eliminating jump cuts between loop cycles.
5. 💬 **WeChat Sticker Optimization (Targeting ≤500KB)**:
   - Scales the long edge to 240px and applies adaptive color palette reduction (down to 48 colors) to optimize file sizes toward WeChat sticker requirements (≤500KB). *(Note: For extremely long frame sequences, consider trimming frames or adjusting frame rates if size limits are reached).*
6. 🎞️ **Visual Filmstrip Frame Management**:
   - Inspect all split frames on the bottom timeline. Click **`❌`** on any thumbnail to drop unwanted or glitchy frames with instant animation reconstruction and undo support via **`↩ 恢复已删帧` (Restore Frame)**.
7. 📂 **Zero-Config Automatic Archiving**:
   - Drag & drop any image without configuring paths. All sliced frames and exported animations are automatically organized into the `output/` directory with a convenient **`📂 打开成品目录 (output)`** button.

---

## 🚀 Download & Quick Start

### Option 1: Standalone Portable App (Windows x64) — Recommended
Download the latest pre-compiled build directly from GitHub Releases:
- 📦 **[Download GifCreater-windows-x64.zip (Recommended)](https://github.com/HanboyLee/GifCreater/releases/download/latest/GifCreater-windows-x64.zip)**
- ⚡ **[Download GifCreater.exe (Standalone Executable)](https://github.com/HanboyLee/GifCreater/releases/download/latest/GifCreater.exe)**
- **No Python installation required!** Extract and double-click `GifCreater.exe` to run immediately on 64-bit Windows.

---

### Option 2: Run from Python Source (Cross-Platform)
Requires Python 3.10+ (tested on 3.11 and 3.13; CI uses 3.11):

1. Clone the repository:
   ```bash
   git clone https://github.com/HanboyLee/GifCreater.git
   cd GifCreater
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python gui.py
   # Or double-click run_gui.bat on Windows
   ```

---

## 🛠️ Quality Assurance & CI/CD

This repository enforces strict engineering quality standards defined in [AGENTS.md](AGENTS.md) (guidelines for developers and AI agents):
- **TDD Quality Gate**: All core image splitting and animation logic is backed by automated unit tests requiring a line coverage of **≥90%** (validated in CI).
- **Automated Continuous Deployment**: Every push to `main` that passes the test gate automatically compiles and updates the Windows executable on the `latest` Release.

```bash
# Run tests and verify the ≥90% coverage gate locally:
pip install -r requirements-dev.txt
pytest tests/ --cov=gif_tool --cov-report=term-missing --cov-fail-under=90
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
