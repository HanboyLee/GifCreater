# 🎞️ GifCreater Studio

<p align="center">
  <b>English</b> | <a href="README_zh.md"><b>简体中文</b></a>
</p>

<p align="center">
  <a href="https://github.com/HanboyLee/GifCreater/releases/tag/latest"><img src="https://img.shields.io/badge/Release-Latest_Continuous-brightgreen.svg" alt="Latest Continuous Release"></a>
  <img src="https://img.shields.io/badge/Platform-Windows%20x64-lightgrey.svg" alt="Platform: Windows x64">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/License-MIT-orange.svg" alt="License MIT">
</p>

An all-in-one, portable desktop studio designed for unpacking AI-generated multi-frame storyboards and creating smooth animated GIFs and WebPs. 

Easily turn multi-frame comic strips (such as 16-frame 4x4 grids, 6-frame vertical strips, 3x3 panels) into polished animations with smart divider snapping, in-app live preview, and one-click WeChat sticker export.

---

## 🖥️ Workspace & Production Flow

```text
+-----------------------------------------------------------------------------------------------+
| 🎞️ GifCreater Studio                                                          [-] [口] [X]   |
+-----------------------------------------------------------------------------------------------+
| 📥 Select Image: [ C:/AI_Art/comic_16frames.png                      ] [ 📁 Browse Image... ] |
+---------------------------------------------------------------+-------------------------------+
| 【 🖥️ Visual Canvas & In-App Player 】                        | 【 ⚙️ Slicing & Animation 】  |
|                                                               |                               |
|   +---------------------------------------------------------+ | 🔲 Grid Setup:                |
|   |         Canvas with Drag-to-Adjust Red Dashed Lines     | |   Grid: [ 4 ] Rows × [ 4 ] Cols|
|   |                            or                           | |   Mode: (o) ✨ Auto Trim      |
|   |              Live Animation Player Preview              | |         ( ) 📐 Uniform Grid   |
|   +---------------------------------------------------------+ | ----------------------------- |
|     [ ▶ Play / ⏸ Pause ] [⏮ First] [⏭ Next]  [05/16]        | ⏱️ Timing:                     |
|     Loop: (o) Normal Loop   ( ) 🔁 Boomerang Ping-Pong        | |   Frame Delay: [ 350 ] ms   |
|                                                               | |   Pause on Last: [ 1500 ] ms|
|                                                               | ----------------------------- |
|                                                               | 📦 Export Presets:            |
|                                                               |   (o) 🌟 High-Res GIF (Orig)  |
|                                                               |   ( ) 💬 WeChat Sticker (≤500K)|
|                                                               |   ( ) ⚡ High-Efficiency WebP |
|                                                               |                               |
|                                                               |   [ 🚀 One-Click Synthesize ] |
|                                                               |   [ 📂 Open Output Folder ]   |
+---------------------------------------------------------------+-------------------------------+
| 🎞️ Filmstrip Timeline (16 Frames | Click ❌ on any card to delete unwanted frame)           |
| [ #01 ]  [ #02 ]  [ #03 ]  [ #04 ]  [ ❌ Removed ]  [ #05 ] ... [ #16 ]  [ ↩ Restore Frame ]  |
+-----------------------------------------------------------------------------------------------+
```

The typical workflow takes just seconds:
$$\text{Drop Image} \longrightarrow \text{Smart Snap Dividers} \longrightarrow \text{In-App Player Preview} \longrightarrow \text{One-Click Export}$$

> **Note on UI Language**: The current desktop application interface displays in Chinese. English descriptions below include the original Chinese button text for easy navigation.

---

## 💡 Core Value

- **Say Goodbye to Manual Cropping**: AI image generators (ChatGPT, Midjourney) produce multiple frames packed into a single image. GifCreater automatically identifies dark, light, or gradient dividers and snaps cutlines to boundaries—with pixel-level drag-and-drop fine-tuning.
- **Eliminate Loop Jump Cuts**: Solves the awkward hitch in traditional single-direction loops by introducing the **Boomerang Ping-Pong** effect ($1 \rightarrow 2 \rightarrow 3 \rightarrow 2 \rightarrow 1$), making animations cycle seamlessly.
- **Solved WeChat Custom Sticker Constraints**: WeChat strictly enforces sticker limits ($\le 500\,\text{KB}$ and 240px long edge). The built-in adaptive multi-step color reduction engine optimizes output directly for WeChat sticker compliance.
- **Zero Configuration Friction**: Forget setting up output directories. Every split frame and rendered GIF is automatically archived into a clean `output/` folder next to the app, accessible via the one-click folder shortcut.

---

## ✨ Key Capabilities

### 1. 🧲 Smart Snap & Interactive Visual Adjustment
- **Multi-Divider Detection**: Automatically detects black lines, white borders, and color step transitions across non-uniform grid cells.
- **Direct Canvas Dragging**: Click and drag red dashed cutlines on the canvas to make instant pixel adjustments.
- **One-Click Re-Snap**: Instantly restore lines to algorithmically optimal coordinates using **`🔄 重新吸附` (Re-Snap)**.

### 2. 📐 Real-Time Resolution & Aspect Ratio HUD
- **Instant Ratio Recognition**: Calculates frame dimensions and standard aspect ratios dynamically (**1:1** Square, **16:9** Widescreen, **9:16** Vertical Video, **3:2** Classic Photo, **4:3** Standard, etc.).
- **Live Badge & Header Check**: Visible on the sidebar, canvas top-right HUD badge, and filmstrip header.

### 3. 🖥️ In-App Live Animation Player
- **Playhead Control**: Play, pause, step frame-by-frame, and drag the timeline scrubber in place.
- **Instant Speed Feedback**: Adjust frame delay (ms) with immediate real-time playback update.

### 4. 🔁 Boomerang Ping-Pong Loop
- Extends sequential frame playback forwards and backwards smoothly to eliminate unnatural loop jump cuts.

### 5. 💬 WeChat Sticker Preset (Targeting $\le 500\,\text{KB}$)
- Automatically scales the long edge to 240px and runs multi-stage adaptive color palette compression (down to 48 colors) to optimize for WeChat custom sticker upload requirements.

### 6. 🎞️ Filmstrip Frame Management
- Visual thumbnail strip of all extracted frames. Click **`❌`** on any frame to drop visual glitches or AI artifacts; the animation and export instantly adapt. Easily undo with **`↩ 恢复已删帧` (Restore Frame)**.

### 7. 📂 Structured Auto-Archiving
- Auto-saves all extracted assets into `output/frames/` and animations into `output/gifs/` without prompting for paths. Click **`📂 打开成品目录 (output)`** to view results.

---

## 🎯 Use Cases

- 🎨 **AI Content Creators**: Rapidly turn multi-panel comic strips generated by Midjourney, ChatGPT, or Stable Diffusion into animated story shorts.
- 💬 **Meme & Sticker Designers**: Slice continuous character expressions and export ready-to-use WeChat stickers in seconds.
- 🎬 **Animators & Storyboard Artists**: Inspect storyboard timing, delete flawed keyframes, and test pacing on the fly.
- 📱 **Social Media Curators**: Craft looping visual content tailored for Instagram (1:1), TikTok/Reels (9:16), or Xiaohongshu (3:4).

---

## 🚀 Download & Quick Start

### Option 1: Standalone Portable App (Windows x64) — Recommended
Get the latest pre-compiled green build directly from GitHub Releases:
- 📦 **[Download GifCreater-windows-x64.zip (Recommended)](https://github.com/HanboyLee/GifCreater/releases/download/latest/GifCreater-windows-x64.zip)**
- ⚡ **[Download GifCreater.exe (Standalone Executable)](https://github.com/HanboyLee/GifCreater/releases/download/latest/GifCreater.exe)**

> **No installation or Python setup required.** Extract and double-click `GifCreater.exe` to start creating immediately.

---

### Option 2: Run from Python Source (Cross-Platform)
Requires Python 3.10+ (tested on Python 3.11 & 3.13):

1. Clone the repository:
   ```bash
   git clone https://github.com/HanboyLee/GifCreater.git
   cd GifCreater
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the studio:
   ```bash
   python gui.py
   # Or double-click run_gui.bat on Windows
   ```

---

## 📄 License & Contributing

- Distributed under the [MIT License](LICENSE).
- *Developers & Contributors*: Please refer to [docs/](docs/) and [AGENTS.md](AGENTS.md) for architectural documentation and quality guidelines.
