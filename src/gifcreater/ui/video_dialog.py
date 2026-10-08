# -*- coding: utf-8 -*-
"""GifCreater 视频静止帧与网格裁切处理对话框 (VideoStillDialog)

基于 Windows 11 Fluent Design (PyQt6 + qfluentwidgets) 构建。
提供交互式视频时间轴定位、逐帧微调、邻近帧胶卷预览、网格预设选择与模式分流。
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from PIL import Image
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QKeyEvent, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    ComboBox,
    FluentIcon,
    IconWidget,
    PrimaryPushButton,
    PushButton,
    Slider,
    SpinBox,
    StrongBodyLabel,
)

from ..core.video_source import VideoError, VideoInfo, VideoReader, grid_frame_count
from .workers import VideoFrameWorker, VideoSampleWorker


def pil_to_qpixmap(pil_img: Image.Image) -> QPixmap:
    """将 PIL 图像转换为 Qt QPixmap。"""
    img = pil_img.convert("RGBA")
    data = img.tobytes("raw", "RGBA")
    qimg = QImage(data, img.width, img.height, img.width * 4, QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(qimg)


def format_seconds(s: float) -> str:
    """格式化秒数为 mm:ss.ms 字符串。"""
    minutes = int(s // 60)
    secs = s % 60
    return f"{minutes:02d}:{secs:05.2f}"


class NeighborThumbnailCard(CardWidget):
    """邻近帧缩略图小卡片，支持悬停和点击快速跳转。"""

    clicked = pyqtSignal(int)

    def __init__(self, frame_index: int, label_text: str, parent=None):
        super().__init__(parent)
        self.frame_index = frame_index
        self.setFixedSize(96, 84)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        self.lbl_img = QLabel(self)
        self.lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_img.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.lbl_img.setStyleSheet("background: transparent; border-radius: 4px;")
        layout.addWidget(self.lbl_img)

        self.lbl_tag = CaptionLabel(label_text, self)
        self.lbl_tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_tag)

    def set_thumbnail(self, pixmap: QPixmap, is_current: bool = False):
        scaled = pixmap.scaled(
            88, 54, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.lbl_img.setPixmap(scaled)
        if is_current:
            self.setStyleSheet("NeighborThumbnailCard { border: 2px solid #0078d4; }")
            self.lbl_tag.setText("● 当前")
        else:
            self.setStyleSheet("")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.frame_index)
        super().mousePressEvent(event)


class VideoStillDialog(QDialog):
    """视频静止帧与网格裁切对话框。"""

    def __init__(self, video_path: Union[str, Path], parent=None):
        super().__init__(parent)
        self.video_path = Path(video_path)
        self.setWindowTitle("🎬 视频静止帧与网格处理")
        self.resize(960, 720)
        self.setMinimumSize(840, 620)

        # 结果载荷
        self.result_mode: Optional[str] = None  # "still" or "sample"
        self.still_image: Optional[Image.Image] = None
        self.sampled_frames: Optional[List[Image.Image]] = None
        self.selected_rows: int = 3
        self.selected_cols: int = 3

        # 初始化视频读取器
        try:
            self.reader = VideoReader(self.video_path)
            self.info: VideoInfo = self.reader.info
        except Exception as e:
            raise VideoError(f"无法读取视频: {e}") from e

        self.current_index: int = 0
        self._current_pixmap: Optional[QPixmap] = None
        self._active_worker: Optional[VideoFrameWorker] = None
        self._sample_worker: Optional[VideoSampleWorker] = None

        # 防抖定时器 (80ms)
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(80)
        self._debounce_timer.timeout.connect(self._fetch_current_frame_async)

        self._init_ui()
        self._update_time_labels(0)
        self._trigger_frame_update(0)

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 16, 20, 16)
        root_layout.setSpacing(12)

        # 1. 顶部信息栏
        top_bar = QHBoxLayout()
        icon = IconWidget(FluentIcon.VIDEO, self)
        icon.setFixedSize(24, 24)
        top_bar.addWidget(icon)

        title_lbl = StrongBodyLabel(self.video_path.name, self)
        top_bar.addWidget(title_lbl)

        meta_text = (
            f"{self.info.width}×{self.info.height} · "
            f"{self.info.fps:.1f} fps · "
            f"{format_seconds(self.info.duration_s)} · "
            f"共 {self.info.frame_count} 帧"
        )
        if self.info.rotation != 0:
            meta_text += f" (旋转 {self.info.rotation}°)"

        meta_lbl = CaptionLabel(meta_text, self)
        meta_lbl.setStyleSheet("color: #888888;")
        top_bar.addWidget(meta_lbl)
        top_bar.addStretch()

        root_layout.addLayout(top_bar)

        # 2. 中部大预览画布 (CardWidget)
        self.preview_card = CardWidget(self)
        self.preview_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        preview_layout = QVBoxLayout(self.preview_card)
        preview_layout.setContentsMargins(6, 6, 6, 6)

        self.preview_label = QLabel(self.preview_card)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background: transparent;")
        preview_layout.addWidget(self.preview_label)

        root_layout.addWidget(self.preview_card, stretch=1)

        # 3. 时间轴与逐帧控制栏
        timeline_layout = QVBoxLayout()
        timeline_layout.setSpacing(6)

        # 时间与帧数标签
        time_info_bar = QHBoxLayout()
        self.lbl_curr_time = BodyLabel("00:00.00 / 00:00.00", self)
        self.lbl_frame_no = CaptionLabel("第 0 帧 / 共 0 帧", self)
        time_info_bar.addWidget(self.lbl_curr_time)
        time_info_bar.addStretch()
        time_info_bar.addWidget(self.lbl_frame_no)
        timeline_layout.addLayout(time_info_bar)

        # 滑动条与步进按钮
        slider_bar = QHBoxLayout()
        slider_bar.setSpacing(8)

        self.btn_step_prev_sec = PushButton("-1s", self)
        self.btn_step_prev_sec.setToolTip("向后跳转 1 秒 (Shift+←)")
        self.btn_step_prev_sec.clicked.connect(self._step_back_second)
        slider_bar.addWidget(self.btn_step_prev_sec)

        self.btn_step_prev_frame = PushButton("◀ -1帧", self)
        self.btn_step_prev_frame.setToolTip("上一帧 (←)")
        self.btn_step_prev_frame.clicked.connect(self._step_prev_frame)
        slider_bar.addWidget(self.btn_step_prev_frame)

        self.slider = Slider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(0, max(0, self.info.frame_count - 1))
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self._on_slider_changed)
        slider_bar.addWidget(self.slider, stretch=1)

        self.btn_step_next_frame = PushButton("+1帧 ▶", self)
        self.btn_step_next_frame.setToolTip("下一帧 (→)")
        self.btn_step_next_frame.clicked.connect(self._step_next_frame)
        slider_bar.addWidget(self.btn_step_next_frame)

        self.btn_step_next_sec = PushButton("+1s", self)
        self.btn_step_next_sec.setToolTip("向前跳转 1 秒 (Shift+→)")
        self.btn_step_next_sec.clicked.connect(self._step_forward_second)
        slider_bar.addWidget(self.btn_step_next_sec)

        timeline_layout.addLayout(slider_bar)
        root_layout.addLayout(timeline_layout)

        # 4. 邻近帧胶卷预览条 (前後各 2 帧，共 5 帧)
        neighbors_box = QHBoxLayout()
        neighbors_box.setSpacing(8)
        self.neighbor_cards: List[NeighborThumbnailCard] = []
        for i in range(5):
            card = NeighborThumbnailCard(0, "", self)
            card.clicked.connect(self._on_neighbor_clicked)
            self.neighbor_cards.append(card)
            neighbors_box.addWidget(card)
        neighbors_box.addStretch()
        root_layout.addLayout(neighbors_box)

        # 5. 网格参数与操作模式栏
        action_card = CardWidget(self)
        action_layout = QHBoxLayout(action_card)
        action_layout.setContentsMargins(12, 10, 12, 10)
        action_layout.setSpacing(12)

        # 网格选择
        action_layout.addWidget(BodyLabel("切片网格:", self))
        self.combo_grid = ComboBox(self)
        self.combo_grid.addItems(["3 × 3 (9格)", "4 × 6 (24格)", "6 × 4 (24格)", "自定义"])
        self.combo_grid.currentIndexChanged.connect(self._on_grid_preset_changed)
        action_layout.addWidget(self.combo_grid)

        self.spin_rows = SpinBox(self)
        self.spin_rows.setRange(1, 20)
        self.spin_rows.setValue(3)
        self.spin_rows.setPrefix("行: ")
        self.spin_rows.setEnabled(False)
        self.spin_rows.valueChanged.connect(self._on_custom_grid_changed)
        action_layout.addWidget(self.spin_rows)

        self.spin_cols = SpinBox(self)
        self.spin_cols.setRange(1, 20)
        self.spin_cols.setValue(3)
        self.spin_cols.setPrefix("列: ")
        self.spin_cols.setEnabled(False)
        self.spin_cols.valueChanged.connect(self._on_custom_grid_changed)
        action_layout.addWidget(self.spin_cols)

        action_layout.addStretch()

        # 采样进度条 (初始隐藏)
        self.sample_progress = QProgressBar(self)
        self.sample_progress.setFixedSize(120, 16)
        self.sample_progress.setVisible(False)
        action_layout.addWidget(self.sample_progress)

        # 模式 B: 抽帧
        self.btn_sample = PushButton("🎞️ 等距抽帧生成 GIF", self)
        self.btn_sample.setToolTip("按所选网格格数从视频均匀提取帧，并直接合并为 GIF")
        self.btn_sample.clicked.connect(self._on_mode_b_clicked)
        action_layout.addWidget(self.btn_sample)

        # 模式 A: 设为静止帧 (主要推荐)
        self.btn_accept_still = PrimaryPushButton("🎯 设为静止帧进入裁切", self)
        self.btn_accept_still.setToolTip("使用当前帧作为高清源图载入工坊，开始 3×3/4×6 网格裁切")
        self.btn_accept_still.clicked.connect(self._on_mode_a_clicked)
        action_layout.addWidget(self.btn_accept_still)

        self.btn_cancel = PushButton("取消", self)
        self.btn_cancel.clicked.connect(self.reject)
        action_layout.addWidget(self.btn_cancel)

        root_layout.addWidget(action_card)

    def _on_slider_changed(self, val: int):
        self.current_index = val
        self._update_time_labels(val)
        self._debounce_timer.start()

    def _update_time_labels(self, index: int):
        t_curr = self.reader.time_of_index(index)
        t_total = self.info.duration_s
        self.lbl_curr_time.setText(f"{format_seconds(t_curr)} / {format_seconds(t_total)}")
        self.lbl_frame_no.setText(f"第 {index + 1} 帧 / 共 {self.info.frame_count} 帧")

    def _trigger_frame_update(self, index: int):
        self.current_index = index
        self._update_time_labels(index)
        self._fetch_current_frame_async()

    def _fetch_current_frame_async(self):
        """启动后台线程读取当前预览帧 (限制大预览尺寸 960 以保障流畅)。"""
        if self._active_worker and self._active_worker.isRunning():
            self._active_worker.requestInterruption()

        worker = VideoFrameWorker(self.reader, self.current_index, max_edge=960, parent=self)
        worker.frameReady.connect(self._on_frame_ready)
        self._active_worker = worker
        worker.start()

        # 同步刷新邻近缩略图
        self._update_neighbor_strip(self.current_index)

    def _on_frame_ready(self, idx: int, img: Image.Image):
        if idx != self.current_index:
            return
        pix = pil_to_qpixmap(img)
        self._current_pixmap = pix
        self._render_preview()

    def _render_preview(self):
        if self._current_pixmap is None:
            return
        target_size = self.preview_label.size()
        if target_size.width() <= 10 or target_size.height() <= 10:
            return
        scaled = self._current_pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._render_preview()

    def _update_neighbor_strip(self, index: int):
        """加载当前帧前后各 2 帧的小缩略图。"""
        # 读取 [-2, -1, 0, 1, 2] 相对索引
        targets = [index - 2, index - 1, index, index + 1, index + 2]
        for card, tgt in zip(self.neighbor_cards, targets):
            clamped = self.reader.index_by_clamp(tgt)
            card.frame_index = clamped
            is_curr = clamped == index
            diff = clamped - index
            tag = "● 当前" if is_curr else (f"{diff:+d}帧" if diff != 0 else "当前")
            card.lbl_tag.setText(tag)

            # 读取缩略图
            try:
                thumb = self.reader.get_frame_by_index(clamped)
                if max(thumb.size) > 96:
                    thumb = thumb.copy()
                    thumb.thumbnail((96, 96), Image.Resampling.LANCZOS)
                card.set_thumbnail(pil_to_qpixmap(thumb), is_current=is_curr)
            except Exception:
                pass

    def _on_neighbor_clicked(self, frame_index: int):
        self.slider.setValue(frame_index)

    def _step_prev_frame(self):
        self.slider.setValue(max(0, self.current_index - 1))

    def _step_next_frame(self):
        self.slider.setValue(min(self.info.frame_count - 1, self.current_index + 1))

    def _step_back_second(self):
        fps = max(1.0, self.info.fps)
        delta = int(round(fps))
        self.slider.setValue(max(0, self.current_index - delta))

    def _step_forward_second(self):
        fps = max(1.0, self.info.fps)
        delta = int(round(fps))
        self.slider.setValue(min(self.info.frame_count - 1, self.current_index + delta))

    def _on_grid_preset_changed(self, idx: int):
        if idx == 0:  # 3x3
            self.spin_rows.setValue(3)
            self.spin_cols.setValue(3)
            self.spin_rows.setEnabled(False)
            self.spin_cols.setEnabled(False)
        elif idx == 1:  # 4x6
            self.spin_rows.setValue(4)
            self.spin_cols.setValue(6)
            self.spin_rows.setEnabled(False)
            self.spin_cols.setEnabled(False)
        elif idx == 2:  # 6x4
            self.spin_rows.setValue(6)
            self.spin_cols.setValue(4)
            self.spin_rows.setEnabled(False)
            self.spin_cols.setEnabled(False)
        else:  # 自定义
            self.spin_rows.setEnabled(True)
            self.spin_cols.setEnabled(True)

    def _on_custom_grid_changed(self):
        pass

    def _on_mode_a_clicked(self):
        """模式 A：选定当前静止帧，提取全分辨率原图，关闭对话框。"""
        try:
            self.still_image = self.reader.get_frame_by_index(self.current_index)
            self.selected_rows = self.spin_rows.value()
            self.selected_cols = self.spin_cols.value()
            self.result_mode = "still"
            self.accept()
        except Exception as e:
            from qfluentwidgets import InfoBar, InfoBarPosition

            InfoBar.error(
                title="提取静止帧失败",
                content=str(e),
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000,
            )

    def _on_mode_b_clicked(self):
        """模式 B：等距采样指定帧数并合并为 GIF。"""
        rows = self.spin_rows.value()
        cols = self.spin_cols.value()
        count = grid_frame_count(rows, cols)

        self.btn_sample.setEnabled(False)
        self.btn_accept_still.setEnabled(False)
        self.sample_progress.setVisible(True)
        self.sample_progress.setValue(0)
        self.sample_progress.setMaximum(count)

        self._sample_worker = VideoSampleWorker(
            self.reader,
            count=count,
            t_start=0.0,
            t_end=self.info.duration_s,
            parent=self,
        )
        self._sample_worker.progressChanged.connect(
            lambda done, tot: self.sample_progress.setValue(done)
        )
        self._sample_worker.samplingFinished.connect(self._on_sample_finished)
        self._sample_worker.samplingFailed.connect(self._on_sample_failed)
        self._sample_worker.start()

    def _on_sample_finished(self, frames: List[Image.Image]):
        self.sampled_frames = frames
        self.selected_rows = self.spin_rows.value()
        self.selected_cols = self.spin_cols.value()
        self.result_mode = "sample"
        self.accept()

    def _on_sample_failed(self, err_msg: str):
        from qfluentwidgets import InfoBar, InfoBarPosition

        self.btn_sample.setEnabled(True)
        self.btn_accept_still.setEnabled(True)
        self.sample_progress.setVisible(False)
        InfoBar.error(
            title="抽帧失败",
            content=err_msg,
            parent=self,
            position=InfoBarPosition.TOP,
            duration=3500,
        )

    def keyPressEvent(self, event: QKeyEvent):
        """支持方向键微调与快捷键。"""
        modifiers = event.modifiers()
        key = event.key()

        if key == Qt.Key.Key_Left:
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                self._step_back_second()
            else:
                self._step_prev_frame()
            event.accept()
            return
        elif key == Qt.Key.Key_Right:
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                self._step_forward_second()
            else:
                self._step_next_frame()
            event.accept()
            return
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._on_mode_a_clicked()
            event.accept()
            return

        super().keyPressEvent(event)

    def closeEvent(self, event):
        """安全释放后台线程与视频读取器句柄。"""
        if self._active_worker and self._active_worker.isRunning():
            self._active_worker.requestInterruption()
            self._active_worker.wait(200)
        if self._sample_worker and self._sample_worker.isRunning():
            self._sample_worker.cancel()
            self._sample_worker.wait(200)
        self.reader.close()
        super().closeEvent(event)
