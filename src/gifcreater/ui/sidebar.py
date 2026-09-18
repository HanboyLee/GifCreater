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

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
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


class ControlSidebar(SingleDirectionScrollArea):
    """
    右侧现代参数控制面板 (基于 Fluent Design 与 UIUX-PRO-MAX 规范)
    """
    gridParamChanged = pyqtSignal(int, int, bool)   # (rows, cols, smart_crop)
    timingChanged = pyqtSignal(int, int, bool)      # (duration_ms, end_pause_ms, boomerang)
    captionChanged = pyqtSignal(str, str)           # (caption_text, caption_pos)
    startProcessRequested = pyqtSignal()            # 点击一键拆解合成
    openOutputRequested = pyqtSignal()              # 点击打开输出目录

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(310)
        self.setWidgetResizable(True)
        self.setStyleSheet(
            """
            ControlSidebar {
                background: transparent;
                border: none;
            }
            CardWidget {
                background-color: #272727;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
            }
            SubtitleLabel {
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
            }
            BodyLabel {
                color: #f0f0f0;
                font-size: 12px;
                font-weight: normal;
            }
            RadioButton {
                color: #f0f0f0;
                font-size: 12px;
            }
            RadioButton:hover {
                color: #ffffff;
            }
            SpinBox {
                background-color: #333333;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 2px 6px;
                font-weight: bold;
                font-size: 12px;
            }
            LineEdit {
                background-color: #333333;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 4px 8px;
                font-size: 12px;
            }
            """
        )

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)
        self.setWidget(container)

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

        layout.addWidget(card_grid)

        # ---------------- 卡片 2: 表情包配文增强 (所见即所得) ----------------
        card_caption = CardWidget(container)
        layout_caption = QVBoxLayout(card_caption)
        layout_caption.setSpacing(8)

        layout_caption.addWidget(SubtitleLabel("✍️ 表情包文字配文 (可选)"))

        layout_caption.addWidget(BodyLabel("配文内容 (留空则原画输出):"))
        self.edit_caption = LineEdit()
        self.edit_caption.setPlaceholderText("例如: 疯狂星期四 / 收到")
        self.edit_caption.setClearButtonEnabled(True)
        self.edit_caption.textChanged.connect(self._on_caption_changed)
        layout_caption.addWidget(self.edit_caption)

        # 配文位置单选
        layout_caption.addWidget(BodyLabel("文字位置:"))
        self.btn_group_pos = QButtonGroup(self)
        self.rb_pos_bottom = RadioButton("底部居中 (默认经典)")
        self.rb_pos_top = RadioButton("顶部横条 (Top)")
        self.rb_pos_bottom.setChecked(True)
        self.btn_group_pos.addButton(self.rb_pos_bottom)
        self.btn_group_pos.addButton(self.rb_pos_top)
        self.btn_group_pos.buttonToggled.connect(self._on_caption_changed)

        pos_box = QHBoxLayout()
        pos_box.addWidget(self.rb_pos_bottom)
        pos_box.addWidget(self.rb_pos_top)
        layout_caption.addLayout(pos_box)

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
        self.btn_process.clicked.connect(self.startProcessRequested.emit)
        layout.addWidget(self.btn_process)

        self.btn_open_output = PushButton("📂 打开成品归档目录")
        self.btn_open_output.clicked.connect(self.openOutputRequested.emit)
        layout.addWidget(self.btn_open_output)

        layout.addStretch()

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

    def _on_caption_changed(self):
        text = self.get_caption_text()
        pos = self.get_caption_position()
        self.captionChanged.emit(text, pos)

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
        return "top" if self.rb_pos_top.isChecked() else "bottom"

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

