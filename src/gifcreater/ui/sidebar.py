# -*- coding: utf-8 -*-
"""
GifCreater 现代参数控制面板 (Control Sidebar)
==============================================

基于 PyQt-Fluent-Widgets 构建的 Windows 11 Fluent 风格参数面板：
- 网格切片参数调节 (行列数、智能去黑边开关)
- 动画节奏与循环控制 (帧间隔、尾帧停留、Boomerang 乒乓循环)
- 导出目标预设单选组 (🌟 高清GIF, 💬 微信表情包 <=500KB, ⚡ WebP)
- 核心操作按钮 (一键拆解并合成、打开成品目录)
"""

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QButtonGroup,
    QColorDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ComboBox,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    RadioButton,
    SingleDirectionScrollArea,
    Slider,
    SpinBox,
    SubtitleLabel,
    SwitchButton,
)

from ..config.presets import PRESETS, list_preset_items
from ..config.theme_manager import ThemeManager
from ..core.caption import CaptionConfig


class ControlSidebar(SingleDirectionScrollArea):
    """
    右侧现代参数控制面板 (基于 Fluent Design 与 UIUX-PRO-MAX 规范)
    """
    gridParamChanged = pyqtSignal(int, int, bool)   # (rows, cols, smart_crop)
    realignRequested = pyqtSignal()                 # 请求智能波谷吸附对齐
    resetGridRequested = pyqtSignal()               # 请求几何均匀等分
    timingChanged = pyqtSignal(int, int, bool)      # (duration_ms, end_pause_ms, boomerang)
    captionChanged = pyqtSignal(str, str)           # (caption_text, caption_pos)
    captionConfigChanged = pyqtSignal(object)       # 发射 CaptionConfig 对象

    startProcessRequested = pyqtSignal()            # 点击一键拆解合成
    openOutputRequested = pyqtSignal()              # 点击打开输出目录

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(320)
        self.setMaximumWidth(480)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 配文与变换状态
        self.caption_pos_x_ratio: float = 0.50
        self.caption_pos_y_ratio: float = 0.88
        self.caption_rotation: float = 0.0
        self.text_color_rgb: tuple = (255, 255, 255)
        self.stroke_color_rgb: tuple = (0, 0, 0)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 18, 12)
        layout.setSpacing(12)
        self.setWidget(container)

        # 挂载全局主题管理器监听
        ThemeManager.get_instance().themeChanged.connect(self.apply_theme)

        # ---------------- 卡片 1: 网格切片配置 ----------------
        card_grid = CardWidget(container)
        layout_grid = QVBoxLayout(card_grid)
        layout_grid.setSpacing(8)

        layout_grid.addWidget(SubtitleLabel("🔲 网格切片与探测"))

        # 行列设置
        row_box = QHBoxLayout()
        row_box.addWidget(BodyLabel("行数 (Rows):"))
        self.spin_rows = SpinBox()
        self.spin_rows.setRange(1, 20)
        self.spin_rows.setValue(4)
        self.spin_rows.valueChanged.connect(self._on_grid_changed)
        row_box.addWidget(self.spin_rows)
        layout_grid.addLayout(row_box)

        col_box = QHBoxLayout()
        col_box.addWidget(BodyLabel("列数 (Cols):"))
        self.spin_cols = SpinBox()
        self.spin_cols.setRange(1, 20)
        self.spin_cols.setValue(4)
        self.spin_cols.valueChanged.connect(self._on_grid_changed)
        col_box.addWidget(self.spin_cols)
        layout_grid.addLayout(col_box)

        # 智能去黑边开关
        crop_box = QHBoxLayout()
        crop_box.addWidget(BodyLabel("✨ 智能去黑边/吸附:"))
        self.switch_crop = SwitchButton()
        self.switch_crop.setChecked(True)
        self.switch_crop.checkedChanged.connect(self._on_grid_changed)
        crop_box.addWidget(self.switch_crop)
        layout_grid.addLayout(crop_box)

        # 智能吸附与均匀等分快捷按钮组
        btn_grid_actions = QHBoxLayout()
        self.btn_auto_align = PushButton("⚡ 智能吸附参考线")
        self.btn_auto_align.setToolTip("基于投影波谷中位线自动识别分镜缝隙并居中吸附")
        self.btn_auto_align.clicked.connect(self.realignRequested.emit)
        btn_grid_actions.addWidget(self.btn_auto_align)

        self.btn_reset_grid = PushButton("↺ 均匀等分")
        self.btn_reset_grid.setToolTip("恢复几何均匀等分网格参考线")
        self.btn_reset_grid.clicked.connect(self.resetGridRequested.emit)
        btn_grid_actions.addWidget(self.btn_reset_grid)
        layout_grid.addLayout(btn_grid_actions)

        layout.addWidget(card_grid)

        # ---------------- 卡片 2: 表情包自由配文工作室 (所见即所得) ----------------
        card_caption = CardWidget(container)
        layout_caption = QVBoxLayout(card_caption)
        layout_caption.setSpacing(8)

        layout_caption.addWidget(SubtitleLabel("✍️ 表情包自由配文工作室"))

        layout_caption.addWidget(BodyLabel("配文内容 (留空则原画输出):"))
        self.edit_caption = LineEdit()
        self.edit_caption.setPlaceholderText("输入文字，在画布上可直接鼠标拖拽")
        self.edit_caption.setClearButtonEnabled(True)
        self.edit_caption.textChanged.connect(self._on_caption_changed)
        layout_caption.addWidget(self.edit_caption)

        # 旋转角度控制
        rot_header = QHBoxLayout()
        self.label_rotation = BodyLabel("旋转角度: 0°")
        rot_header.addWidget(self.label_rotation)
        rot_header.addStretch()
        layout_caption.addLayout(rot_header)

        # 常用角度快捷按钮
        rot_quick_box = QHBoxLayout()
        rot_quick_box.setSpacing(6)
        for deg in [-15, 0, 15, 45]:
            btn_deg = PushButton(f"{deg:+}°" if deg != 0 else "0°")
            btn_deg.setFixedHeight(24)
            btn_deg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn_deg.clicked.connect(lambda _, d=deg: self._set_rotation_angle(d))
            rot_quick_box.addWidget(btn_deg)
        layout_caption.addLayout(rot_quick_box)

        self.slider_rotation = Slider(Qt.Orientation.Horizontal)
        self.slider_rotation.setRange(-180, 180)
        self.slider_rotation.setValue(0)
        self.slider_rotation.valueChanged.connect(self._on_rotation_slider_changed)
        layout_caption.addWidget(self.slider_rotation)

        # 颜色与透明度选择区
        style_grid = QHBoxLayout()
        style_grid.setSpacing(8)

        # 文字颜色与透明度
        col_text_box = QVBoxLayout()
        col_text_box.setSpacing(4)
        self.btn_text_color = PushButton("文字颜色")
        self.btn_text_color.setFixedHeight(26)
        self.btn_text_color.clicked.connect(self._pick_text_color)
        col_text_box.addWidget(self.btn_text_color)

        self.label_text_opacity = BodyLabel("透明度: 100%")
        self.slider_text_opacity = Slider(Qt.Orientation.Horizontal)
        self.slider_text_opacity.setRange(10, 100)
        self.slider_text_opacity.setValue(100)
        self.slider_text_opacity.valueChanged.connect(self._on_text_opacity_changed)
        col_text_box.addWidget(self.label_text_opacity)
        col_text_box.addWidget(self.slider_text_opacity)
        style_grid.addLayout(col_text_box)

        # 描边颜色与粗细
        col_stroke_box = QVBoxLayout()
        col_stroke_box.setSpacing(4)
        self.btn_stroke_color = PushButton("描边颜色")
        self.btn_stroke_color.setFixedHeight(26)
        self.btn_stroke_color.clicked.connect(self._pick_stroke_color)
        col_stroke_box.addWidget(self.btn_stroke_color)

        self.label_stroke_width = BodyLabel("描边粗细: 2px")
        self.slider_stroke_width = Slider(Qt.Orientation.Horizontal)
        self.slider_stroke_width.setRange(0, 10)
        self.slider_stroke_width.setValue(2)
        self.slider_stroke_width.valueChanged.connect(self._on_stroke_width_changed)
        col_stroke_box.addWidget(self.label_stroke_width)
        col_stroke_box.addWidget(self.slider_stroke_width)
        style_grid.addLayout(col_stroke_box)

        layout_caption.addLayout(style_grid)

        # 九宫格快捷归位 (2x3 罗盘网格)
        layout_caption.addWidget(BodyLabel("九宫格快捷归位 (亦可直接在画布拖拽):"))
        grid_pos_layout = QGridLayout()
        grid_pos_layout.setSpacing(6)
        pos_buttons = [
            ("↖ 顶左", 0.20, 0.15, 0, 0),
            ("↑ 顶中", 0.50, 0.12, 0, 1),
            ("↗ 顶右", 0.80, 0.15, 0, 2),
            ("• 正中", 0.50, 0.50, 1, 0),
            ("↓ 底中", 0.50, 0.88, 1, 1),
            ("↘ 底右", 0.80, 0.88, 1, 2),
        ]
        for name, rx, ry, r, c in pos_buttons:
            b = PushButton(name)
            b.setFixedHeight(26)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            b.clicked.connect(lambda _, x=rx, y=ry: self._set_position_ratio(x, y))
            grid_pos_layout.addWidget(b, r, c)
        layout_caption.addLayout(grid_pos_layout)

        # 一键爆款风格模板 (2x2 网格)
        layout_caption.addWidget(BodyLabel("一键风格模板:"))
        template_grid = QGridLayout()
        template_grid.setSpacing(6)

        tpl_btn_classic = PushButton("🔥 经典黑白")
        tpl_btn_classic.setFixedHeight(28)
        tpl_btn_classic.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        tpl_btn_classic.clicked.connect(lambda: self._apply_style_template("classic"))
        template_grid.addWidget(tpl_btn_classic, 0, 0)

        tpl_btn_yellow = PushButton("⚡ 荧光亮黄")
        tpl_btn_yellow.setFixedHeight(28)
        tpl_btn_yellow.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        tpl_btn_yellow.clicked.connect(lambda: self._apply_style_template("yellow"))
        template_grid.addWidget(tpl_btn_yellow, 0, 1)

        tpl_btn_danger = PushButton("🚨 高能爆红")
        tpl_btn_danger.setFixedHeight(28)
        tpl_btn_danger.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        tpl_btn_danger.clicked.connect(lambda: self._apply_style_template("danger"))
        template_grid.addWidget(tpl_btn_danger, 1, 0)

        tpl_btn_wm = PushButton("👻 半透水印")
        tpl_btn_wm.setFixedHeight(28)
        tpl_btn_wm.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        tpl_btn_wm.clicked.connect(lambda: self._apply_style_template("watermark"))
        template_grid.addWidget(tpl_btn_wm, 1, 1)

        layout_caption.addLayout(template_grid)

        layout.addWidget(card_caption)

        # ---------------- 卡片 3: 动画节奏与循环 ----------------
        card_anim = CardWidget(container)
        layout_anim = QVBoxLayout(card_anim)
        layout_anim.setSpacing(8)


        layout_anim.addWidget(SubtitleLabel("⏱️ 动画节奏与循环"))

        # 帧间隔
        self.label_duration = BodyLabel("帧间隔: 350 ms")
        self.slider_duration = Slider(Qt.Orientation.Horizontal)
        self.slider_duration.setRange(40, 1500)
        self.slider_duration.setValue(350)
        self.slider_duration.valueChanged.connect(self._on_duration_changed)
        layout_anim.addWidget(self.label_duration)
        layout_anim.addWidget(self.slider_duration)

        # 尾帧停留
        self.label_pause = BodyLabel("尾帧停留: 1500 ms")
        self.slider_pause = Slider(Qt.Orientation.Horizontal)
        self.slider_pause.setRange(0, 3000)
        self.slider_pause.setValue(1500)
        self.slider_pause.valueChanged.connect(self._on_pause_changed)
        layout_anim.addWidget(self.label_pause)
        layout_anim.addWidget(self.slider_pause)

        # 循环模式单选组
        layout_anim.addWidget(BodyLabel("循环模式:"))
        self.btn_group_loop = QButtonGroup(self)
        self.rb_loop_normal = RadioButton("正常循环 (Normal Loop)")
        self.rb_loop_boomerang = RadioButton("🔁 乒乓往复 (Boomerang)")
        self.rb_loop_normal.setChecked(True)
        self.btn_group_loop.addButton(self.rb_loop_normal)
        self.btn_group_loop.addButton(self.rb_loop_boomerang)
        self.btn_group_loop.buttonToggled.connect(self._on_timing_changed)

        layout_anim.addWidget(self.rb_loop_normal)
        layout_anim.addWidget(self.rb_loop_boomerang)

        layout.addWidget(card_anim)

        # ---------------- 卡片 4: 导出目标预设 ----------------
        card_export = CardWidget(container)
        layout_export = QVBoxLayout(card_export)
        layout_export.setSpacing(8)

        layout_export.addWidget(SubtitleLabel("📦 导出平台预设"))

        self.combo_presets = ComboBox(self)
        self.preset_keys = []
        for key, name, desc in list_preset_items():
            self.preset_keys.append(key)
            self.combo_presets.addItem(f"{name} ({desc.split('，')[0]})")

        # 默认选中微信表情包 (index 0)
        self.combo_presets.setCurrentIndex(0)
        layout_export.addWidget(self.combo_presets)

        self.label_preset_hint = BodyLabel("说明: 最长边 ≤240px，体积严格 ≤500KB")
        self.label_preset_hint.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        self.combo_presets.currentIndexChanged.connect(self._on_preset_selected)
        layout_export.addWidget(self.label_preset_hint)

        layout.addWidget(card_export)

        # ---------------- 行动按钮区 ----------------
        self.btn_process = PrimaryPushButton("🚀 一键拆解并合成动图")
        self.btn_process.setFixedHeight(38)
        self.btn_process.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_process.clicked.connect(self.startProcessRequested.emit)
        layout.addWidget(self.btn_process)

        self.btn_open_output = PushButton("📂 打开成品归档目录")
        self.btn_open_output.setFixedHeight(32)
        self.btn_open_output.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_open_output.clicked.connect(self.openOutputRequested.emit)
        layout.addWidget(self.btn_open_output)

        layout.addStretch()
        self.apply_theme()

    def _on_grid_changed(self):
        self.gridParamChanged.emit(
            self.spin_rows.value(),
            self.spin_cols.value(),
            self.switch_crop.isChecked(),
        )

    def _on_duration_changed(self, val: int):
        self.label_duration.setText(f"帧间隔: {val} ms")
        self._on_timing_changed()

    def _on_pause_changed(self, val: int):
        self.label_pause.setText(f"尾帧停留: {val} ms")
        self._on_timing_changed()

    def _on_timing_changed(self):
        self.timingChanged.emit(
            self.slider_duration.value(),
            self.slider_pause.value(),
            self.rb_loop_boomerang.isChecked(),
        )

    def _on_rotation_slider_changed(self, val: int):
        self.caption_rotation = float(val)
        self.label_rotation.setText(f"旋转角度: {val:+d}°" if val != 0 else "旋转角度: 0°")
        self._on_caption_changed()

    def _set_rotation_angle(self, deg: int):
        self.slider_rotation.setValue(deg)

    def apply_theme(self, theme_name: Optional[str] = None):
        """动态加载并应用高对比度主题样式"""
        qss = ThemeManager.get_instance().get_theme_stylesheet()
        self.setStyleSheet(qss)
        self._update_color_buttons()

    def _update_color_buttons(self):
        """根据色彩相对感知亮度（ITU-R BT.601），动态设定文字/描边颜色挑选按钮的前景色"""
        tc = self.text_color_rgb
        lum_t = 0.299 * tc[0] + 0.587 * tc[1] + 0.114 * tc[2]
        fg_t = "#000000" if lum_t > 140 else "#ffffff"
        self.btn_text_color.setStyleSheet(
            f"background-color: rgb({tc[0]},{tc[1]},{tc[2]}); color: {fg_t}; font-weight: bold; border-radius: 5px;"
        )

        sc = self.stroke_color_rgb
        lum_s = 0.299 * sc[0] + 0.587 * sc[1] + 0.114 * sc[2]
        fg_s = "#000000" if lum_s > 140 else "#ffffff"
        self.btn_stroke_color.setStyleSheet(
            f"background-color: rgb({sc[0]},{sc[1]},{sc[2]}); color: {fg_s}; font-weight: bold; border-radius: 5px;"
        )

    def _pick_text_color(self):
        curr = QColor(*self.text_color_rgb)
        col = QColorDialog.getColor(curr, self, "选择文字颜色")
        if col.isValid():
            self.text_color_rgb = (col.red(), col.green(), col.blue())
            self._update_color_buttons()
            self._on_caption_changed()

    def _pick_stroke_color(self):
        curr = QColor(*self.stroke_color_rgb)
        col = QColorDialog.getColor(curr, self, "选择描边颜色")
        if col.isValid():
            self.stroke_color_rgb = (col.red(), col.green(), col.blue())
            self._update_color_buttons()
            self._on_caption_changed()

    def _on_text_opacity_changed(self, val: int):
        self.label_text_opacity.setText(f"透明度: {val}%")
        self._on_caption_changed()

    def _on_stroke_width_changed(self, val: int):
        self.label_stroke_width.setText(f"描边粗细: {val}px")
        self._on_caption_changed()

    def _set_position_ratio(self, x_ratio: float, y_ratio: float):
        self.caption_pos_x_ratio = x_ratio
        self.caption_pos_y_ratio = y_ratio
        self._on_caption_changed()

    def update_caption_position_ratio(self, x_ratio: float, y_ratio: float):
        """画布鼠标拖拽后回传更新相对坐标"""
        self.caption_pos_x_ratio = max(0.05, min(0.95, x_ratio))
        self.caption_pos_y_ratio = max(0.05, min(0.95, y_ratio))
        # 触发通知
        self._on_caption_changed()

    def _apply_style_template(self, name: str):
        if name == "classic":
            self.text_color_rgb = (255, 255, 255)
            self.stroke_color_rgb = (0, 0, 0)
            self.slider_text_opacity.setValue(100)
            self.slider_stroke_width.setValue(2)
        elif name == "yellow":
            self.text_color_rgb = (250, 204, 21)  # #FACC15
            self.stroke_color_rgb = (0, 0, 0)
            self.slider_text_opacity.setValue(100)
            self.slider_stroke_width.setValue(3)
        elif name == "danger":
            self.text_color_rgb = (239, 68, 68)   # #EF4444
            self.stroke_color_rgb = (255, 255, 255)
            self.slider_text_opacity.setValue(100)
            self.slider_stroke_width.setValue(2)
        elif name == "watermark":
            self.text_color_rgb = (255, 255, 255)
            self.stroke_color_rgb = (0, 0, 0)
            self.slider_text_opacity.setValue(35)
            self.slider_stroke_width.setValue(1)

        self._update_color_buttons()
        self._on_caption_changed()

    def _on_caption_changed(self):
        text = self.get_caption_text()
        pos = self.get_caption_position()
        self.captionChanged.emit(text, pos)
        cfg = self.get_caption_config()
        self.captionConfigChanged.emit(cfg)

    def _on_preset_selected(self, index: int):
        if 0 <= index < len(self.preset_keys):
            key = self.preset_keys[index]
            preset = PRESETS.get(key)
            if preset:
                self.label_preset_hint.setText(f"说明: {preset.description}")

    def get_caption_text(self) -> str:
        """获取当前表情包配文字符串"""
        return self.edit_caption.text().strip()

    def get_caption_position(self) -> str:
        """获取当前配文位置 ('bottom' 或 'top')"""
        return "top" if self.caption_pos_y_ratio < 0.3 else "bottom"

    def get_caption_config(self) -> CaptionConfig:
        """获取完整的表情包配文与变换配置对象"""
        text = self.get_caption_text()
        alpha_t = int(255 * (self.slider_text_opacity.value() / 100.0))
        rgba_text = (self.text_color_rgb[0], self.text_color_rgb[1], self.text_color_rgb[2], alpha_t)
        rgba_stroke = (self.stroke_color_rgb[0], self.stroke_color_rgb[1], self.stroke_color_rgb[2], alpha_t)

        return CaptionConfig(
            text=text,
            pos_x_ratio=getattr(self, "caption_pos_x_ratio", 0.5),
            pos_y_ratio=getattr(self, "caption_pos_y_ratio", 0.88),
            rotation_deg=getattr(self, "caption_rotation", 0.0),
            text_color=rgba_text,
            stroke_color=rgba_stroke,
            stroke_width=self.slider_stroke_width.value(),
        )

    def get_export_preset(self) -> str:
        """获取当前选中的导出预设 key ('wechat', 'xiaohongshu', 'hd_gif', 'webp')"""
        idx = self.combo_presets.currentIndex()
        if 0 <= idx < len(self.preset_keys):
            return self.preset_keys[idx]
        return "wechat"

    def set_processing_state(self, is_processing: bool):
        """进入/退出计算中防重入锁定状态"""
        self.btn_process.setEnabled(not is_processing)
        self.spin_rows.setEnabled(not is_processing)
        self.spin_cols.setEnabled(not is_processing)
        self.switch_crop.setEnabled(not is_processing)
        self.combo_presets.setEnabled(not is_processing)
        self.edit_caption.setEnabled(not is_processing)
        self.slider_rotation.setEnabled(not is_processing)
        self.btn_text_color.setEnabled(not is_processing)
        self.btn_stroke_color.setEnabled(not is_processing)
        self.slider_text_opacity.setEnabled(not is_processing)
        self.slider_stroke_width.setEnabled(not is_processing)


