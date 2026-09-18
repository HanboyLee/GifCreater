# 🧪 GifCreater v3.0 测试驱动开发 (TDD) 与系统验证方案说明书

> **文档定位**：全流程质量门禁体系、TDD 单元测试设计、90% 覆盖率达标策略与端到端功能核验用例库  
> **归档路径**：`spec/tdd_and_verification_plan.md`  
> **状态**：已全量验证通过 (All 67 Tests Passed, Coverage 97.31%)  
> **关联文档**：[spec/detailed_design.md](file:///D:/gitfunFiles/GifCreater/spec/detailed_design.md) | [spec/execution_plan.md](file:///D:/gitfunFiles/GifCreater/spec/execution_plan.md) | [ARCHITECTURE.md](file:///D:/gitfunFiles/GifCreater/ARCHITECTURE.md)

---

## 一、 TDD (测试驱动开发) 核心策略与实施矩阵

本项目严格遵照 `AGENTS.md` 法定质量门禁要求，执行“测试先行、内存动态数据、覆盖率 ≥ 90% 熔断”三大原则：

### 1. 内存动态微型图像固件设计 (`tests/fixtures/`)
* **核心红线**：严禁在 Git 仓库提交本地大体积图片文件。
* **实现方案**：在 `tests/conftest.py` 与 `tests/fixtures/` 中，通过程序在内存中即时生成带特定数学特征的测试图：
  * **网格拼图测试固件**：内存生成纯色/渐变色交替的 4×4、3×3 矩阵微型图像（如 120×120 像素，每个色块 30×30 像素）；
  * **黑边探测测试固件**：在图像外圈绘制 5px 黑色/白色 Padding，内圈填充高对比度主体矩形，用于精确验证边界探测；
  * **微信体积压缩测试固件**：生成色彩丰富的多帧动画序列，用于精准校验自适应调色板（256/128/64/32 色）降级与体积上限。

### 2. 核心模块 TDD 单测矩阵 (Unit Test Matrix)

| 目标测试模块 | 对应测试文件 | 核心断言与验证场景 |
| :--- | :--- | :--- |
| **切片引擎** (`slicer.py`) | `tests/unit/test_slicer.py` | 1. 默认网格均匀行列坐标计算正确性；<br>2. 拖拽自定义网格线后的非均匀切割验证；<br>3. 切割产出帧数量与预期完全一致（如 4×4 产出 16 帧）。 |
| **黑边探测** (`bounds.py`) | `tests/unit/test_bounds.py` | 1. 纯黑边、纯白边背景探测准确度（容差范围内无残留）；<br>2. 无黑边图片自动保留全图完整包围盒；<br>3. 复杂边缘抗噪能力。 |
| **微信压缩引擎** (`compressor.py`) | `tests/unit/test_compressor.py` | 1. 输出文件字节数**严格 `<= 500 * 1024` 字节 (硬性断言)**；<br>2. 图像尺寸最长边**严格 `<= 240px`**；<br>3. 调色板自适应阶梯式降级收敛性测试。 |
| **动图导出** (`exporter.py`) | `tests/unit/test_exporter.py` | 1. 常规循环帧序列索引验证 (`0, 1, ..., N-1`)；<br>2. 乒乓往复 Boomerang 展开验证 (`0, 1, ..., N-1, N-2, ..., 1`)；<br>3. GIF / WebP 文件头有效魔数（Magic Number）验证。 |
| **路径与权限** (`paths.py`) | `tests/unit/test_paths.py` | 1. 正常环境自动创建并返回 `output/gifs/` 与 `output/frames/`；<br>2. Mock 只读权限时，成功安全降级至 `%USERPROFILE%/Pictures/GifCreater/output`，绝不抛出异常。 |

### 3. 覆盖率硬性门禁执行命令 (Quality Gate Command)
```bash
pytest tests/ --cov=src/gifcreater/core --cov=gif_tool --cov-report=term-missing --cov-fail-under=90
```
* **熔断规则**：若代码行覆盖率（Line Coverage）低于 90%，或有任何一个断言失败，CI/CD 流水线与本地构建立即终止。

---

## 二、 系统端到端功能与交互验证用例库 (Verification Test Cases)

在代码实施完毕后，必须逐项执行以下**可复现、可核验的黑盒/白盒验收用例**：

### 1. 界面与视觉体验验收 (UI/UX Verification)
* **TC-01: Windows 11 Fluent 视觉与材质验证**
  * **操作**：启动 `python main.py`。
  * **预期**：主窗口渲染高品质云母 (Mica) / 亚克力 (Acrylic) 材质底色，控件具备圆角与微阴影，非系统原始灰白底。
* **TC-02: 深浅色模式自适应切换**
  * **操作**：点击右上角主题切换按钮。
  * **预期**：界面即时在暗黑 (Dark Mode) 与明亮 (Light Mode) 之间平滑无缝切换，文字和图标对比度清晰，无样式残缺。
* **TC-03: 高分屏 (High DPI) 矢量渲染验证**
  * **操作**：在 2K/4K 屏幕（125%、150% 缩放比例下）启动。
  * **预期**：字体边缘平滑锐利，图标与分割线无发虚、重影或排版错位。

### 2. 交互式画布与参考线验收 (Canvas Verification)
* **TC-04: 平滑缩放与拖拽平移**
  * **操作**：鼠标在画布上滚动滚轮；按住空格键或鼠标中键拖拽。
  * **预期**：图像以鼠标指针为锚点平滑缩放放大/缩小；平移跟随鼠标移动，无卡顿闪烁。
* **TC-05: 分割参考线拖动与坐标映射**
  * **操作**：鼠标靠近红色分割线，光标变为调整箭头，按住左键左右/上下拖动。
  * **预期**：参考线平滑位移，并实时反映至右侧切片参数；坐标转换在缩放状态下依然保持 100% 像素精准度。

### 3. 时间轴卡片胶卷与废帧管理 (Filmstrip Verification)
* **TC-06: 序列帧卡片横向流式浏览**
  * **操作**：拆解完成后，鼠标滚轮在底部胶卷上滚动。
  * **预期**：单帧卡片带编号清晰陈列，支持水平平滑滚动。
* **TC-07: 废帧剔除与原地播放器动态联动**
  * **操作**：单击选中第 3 帧，按键盘 `Delete` 键剔除（或点击卡片右上角 ❌ 按钮）。
  * **预期**：第 3 帧标记为剔除状态，原地循环播放器立刻重新编排剩余帧序列，不再播放已剔除帧。

### 4. 异步非阻塞防假死验证 (Worker Non-blocking Verification)
* **TC-08: 重型计算期间 UI 响应性**
  * **操作**：载入 16 帧高清图，选择【微信表情包 (≤500KB)】，点击【一键拆解并合成动图】。
  * **预期**：
    1. 右下角显示 Fluent `ProgressRing` 旋转环；
    2. 主窗口可自由拖动，窗口标题不出现“（未响应）”字样，界面始终保持 60 FPS 响应；
    3. 完成后弹出 Fluent `InfoBar` 成功提示气泡，标明真实导出的文件大小（如 468KB）。

### 5. 微信真实过审级验收 (WeChat Compliance Verification)
* **TC-09: 导出的动图真实性与微信添加测试**
  * **操作**：检查 `output/gifs/` 下生成的表情包动图。
  * **预期**：
    1. 右键属性查看文件大小：**严格小于等于 500 KB (512,000 bytes)**；
    2. 图像长宽比例正常，长边不超过 240 像素；
    3. 将该 GIF 发送至微信聊天框，长按选择“添加单个表情”，能够 100% 成功添加，无“图片过大”报错。

---

## 三、 打包构建与兼容性验证 (Packaging Verification)

* **TC-10: PyInstaller 独立单文件 EXE 构建**
  * **执行**：运行打包脚本或命令 `pyinstaller GifCreater.spec`。
  * **预期**：
    1. 构建过程无 Qt 插件缺失警告；
    2. 产物 `dist/GifCreater.exe` 可以在无 Python 环境的纯净 Windows 10/11 电脑上双击秒开运行；
    3. 运行后功能与源码调试模式完全一致。
