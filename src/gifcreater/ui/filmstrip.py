# -*- coding: utf-8 -*-
"""
GifCreater 水平卡片式序列帧胶卷 (Filmstrip Widget)
=================================================

基于卡片流式布局的底部时间轴胶卷：
- 单帧缩略图与序号展示
- 单击选中、Ctrl/Shift 多选支持
- 按 Delete 键或点击 ✕ 快捷剔除废帧
- 废帧一键恢复机制
- 实时与原地动图播放器及导出引擎联动
"""

from typing import List, Set
from PIL import Image
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QKeyEvent, QMouseEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .canvas import pil_to_qpixmap


class FrameCard(QFrame):
    """
    单帧胶卷卡片控件
    """
    selectedChanged = pyqtSignal(int, bool)  # frame_idx, is_selected
    deleteToggled = pyqtSignal(int, bool)    # frame_idx, is_deleted

    def __init__(self, index: int, pil_img: Image.Image, parent=None):
        super().__init__(parent)
        self.index = index
        self.pil_img = pil_img
        self.is_selected = False
        self.is_deleted = False

        self.setFixedSize(96, 120)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # 顶栏：序号与删除按钮
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        self.label_num = QLabel(f"#{index + 1:02d}")
        self.label_num.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))

        self.btn_action = QPushButton("✕")
        self.btn_action.setFixedSize(18, 18)
        self.btn_action.setStyleSheet("QPushButton { border: none; font-size: 11px; color: #ff5555; } QPushButton:hover { background: #ffebeb; border-radius: 9px; }")
        self.btn_action.clicked.connect(self._toggle_delete)

        top_bar.addWidget(self.label_num)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_action)
        layout.addLayout(top_bar)

        # 缩略图
        self.label_thumb = QLabel()
        self.label_thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_thumb.setFixedSize(88, 88)
        self.label_thumb.setStyleSheet("background: #202020; border-radius: 4px;")
        
        # 等比缩放缩略图
        pixmap = pil_to_qpixmap(pil_img)
        scaled_pix = pixmap.scaled(84, 84, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.label_thumb.setPixmap(scaled_pix)
        layout.addWidget(self.label_thumb)

        self._update_style()

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self._update_style()

    def _toggle_delete(self):
        self.is_deleted = not self.is_deleted
        self._update_style()
        self.deleteToggled.emit(self.index, self.is_deleted)

    def set_deleted(self, deleted: bool):
        self.is_deleted = deleted
        self._update_style()
        self.deleteToggled.emit(self.index, self.is_deleted)

    def _update_style(self):
        if self.is_deleted:
            self.setStyleSheet("FrameCard { background: #3a1e1e; border: 1px solid #772222; border-radius: 6px; }")
            self.label_num.setStyleSheet("color: #aa6666; text-decoration: line-through;")
            self.btn_action.setText("↩")
            self.btn_action.setStyleSheet("QPushButton { border: none; font-size: 11px; color: #00cc88; }")
            self.label_thumb.setStyleSheet("background: #251010; opacity: 0.4; border-radius: 4px;")
        elif self.is_selected:
            self.setStyleSheet("FrameCard { background: #2b3b4f; border: 2px solid #0078d4; border-radius: 6px; }")
            self.label_num.setStyleSheet("color: #60cdff;")
            self.btn_action.setText("✕")
            self.btn_action.setStyleSheet("QPushButton { border: none; font-size: 11px; color: #ff5555; }")
            self.label_thumb.setStyleSheet("background: #111111; border-radius: 4px;")
        else:
            self.setStyleSheet("FrameCard { background: #282828; border: 1px solid #3d3d3d; border-radius: 6px; } FrameCard:hover { border-color: #555555; }")
            self.label_num.setStyleSheet("color: #cccccc;")
            self.btn_action.setText("✕")
            self.btn_action.setStyleSheet("QPushButton { border: none; font-size: 11px; color: #ff5555; }")
            self.label_thumb.setStyleSheet("background: #151515; border-radius: 4px;")

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.selectedChanged.emit(self.index, True)
        super().mousePressEvent(event)


class FilmstripWidget(QScrollArea):
    """
    序列帧胶卷流式容器：支持横向平滑滚动与批量剔除废帧
    """
    activeFramesChanged = pyqtSignal(list)  # 发射剩余有效 PIL 图像列表
    frameClicked = pyqtSignal(int)          # 点击单帧时发射索引

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(145)
        self.setWidgetResizable(True)
        self.setStyleSheet(
            "FilmstripWidget { background-color: #181818; border: 1px solid #333333; border-radius: 8px; }"
            "QScrollArea { background-color: #181818; border: 1px solid #333333; border-radius: 8px; }"
            "QWidget { background-color: #181818; }"
        )
        self.viewport().setStyleSheet("background-color: #181818; border: none;")

        self.container = QWidget()
        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setContentsMargins(8, 8, 8, 8)
        self.container_layout.setSpacing(8)

        # 空状态占位提示
        self.label_placeholder = QLabel("🎞️ 序列帧胶卷：切片拆解后的各帧将在此水平陈列，支持选中按 Delete 键一键剔除废帧")
        self.label_placeholder.setStyleSheet("color: #777777; font-size: 12px; font-weight: normal; background: transparent;")
        self.label_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.container_layout.addWidget(self.label_placeholder, 1)

        self.setWidget(self.container)

        self.cards: List[FrameCard] = []
        self.raw_frames: List[Image.Image] = []
        self.selected_indices: Set[int] = set()

    def set_frames(self, frames: List[Image.Image]):
        """载入切片生成的所有单帧"""
        self.clear()
        self.raw_frames = frames

        if frames:
            self.label_placeholder.setVisible(False)
        else:
            self.label_placeholder.setVisible(True)

        for i, frame in enumerate(frames):
            card = FrameCard(i, frame, self.container)
            card.selectedChanged.connect(self._on_card_selected)
            card.deleteToggled.connect(self._on_card_delete_toggled)
            self.container_layout.insertWidget(len(self.cards), card)
            self.cards.append(card)

        self.activeFramesChanged.emit(self.get_active_frames())

    def clear(self):
        """清空胶卷"""
        for card in self.cards:
            self.container_layout.removeWidget(card)
            card.deleteLater()
        self.cards.clear()
        self.raw_frames.clear()
        self.selected_indices.clear()
        self.label_placeholder.setVisible(True)

    def get_active_frames(self) -> List[Image.Image]:
        """获取所有未被剔除的有效帧"""
        return [card.pil_img for card in self.cards if not card.is_deleted]

    def _on_card_selected(self, index: int, is_selected: bool):
        # 默认单选切换
        for i, card in enumerate(self.cards):
            card.set_selected(i == index)
        self.selected_indices = {index}
        self.frameClicked.emit(index)

    def _on_card_delete_toggled(self, index: int, is_deleted: bool):
        self.activeFramesChanged.emit(self.get_active_frames())

    def keyPressEvent(self, event: QKeyEvent):
        # 响应 Delete 键快捷剔除废帧
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            if self.selected_indices:
                for idx in self.selected_indices:
                    if 0 <= idx < len(self.cards):
                        self.cards[idx].set_deleted(True)
                self.activeFramesChanged.emit(self.get_active_frames())
                event.accept()
                return
        super().keyPressEvent(event)
