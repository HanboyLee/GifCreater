# -*- coding: utf-8 -*-
"""
GifCreater 主视窗系统 (Main Window Presentation)
================================================

基于 PyQt6 与 PyQt-Fluent-Widgets 构建的现代化动图工坊主窗口：
- 支持系统级 Mica / Acrylic 材质与暗黑/明亮主题平滑切换
- 支持全局文件拖拽放入素材
- 整合交互画布 (Canvas)、时间轴胶卷 (Filmstrip) 与参数面板 (Sidebar)
- 基于 QThread 异步调度切片与调色板自适应压缩
- 采用 Fluent InfoBar 现代轻量气泡通知与 ProgressRing 状态反馈
"""

import os
import sys
from pathlib import Path
from typing import List, Optional
from PIL import Image
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QDragEnterEvent, QDropEvent, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    FluentIcon as FIF,
    InfoBar,
    InfoBarPosition,
    MSFluentWindow,
    ProgressRing,
    PushButton,
    SubtitleLabel,
    Theme,
    setTheme,
    toggleTheme,
)

from ..config.presets import PRESETS
from ..config.theme_manager import ThemeManager
from ..core import (
    GridConfig,
    calculate_default_grid,
    detect_bounds,
)
from ..utils.paths import get_default_output_dirs, get_base_dir
from .canvas import InteractiveCanvas
from .filmstrip import FilmstripWidget
from .sidebar import ControlSidebar
from .workers import ExportWorker, SliceWorker


class MainWindow(MSFluentWindow):
    """
    动图工坊主窗口
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎞️ GifCreater 动画工坊 v3.0")
        self.resize(1180, 780)
        self.setMinimumSize(980, 680)

        # 挂载官方品牌图标
        icon_path = Path(get_base_dir()) / "resources" / "icons" / "app_icon.ico"
        if not icon_path.exists():
            icon_path = Path(get_base_dir()) / "resources" / "icons" / "app_icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # 核心数据状态
        self.current_file_path: Optional[Path] = None
        self.current_pil_image: Optional[Image.Image] = None
        self.current_grid: Optional[GridConfig] = None
        self.active_frames: List[Image.Image] = []

        # 异步线程引用
        self.slice_worker: Optional[SliceWorker] = None
        self.export_worker: Optional[ExportWorker] = None

        # 初始化主界面容器
        self._init_ui()
        self.setAcceptDrops(True)

    def _init_ui(self):
        # 创建中央主微件
        self.central_widget = QWidget(self)
        self.central_widget.setObjectName("workshopInterface")
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(16, 12, 16, 12)
        self.main_layout.setSpacing(10)

        # 1. 顶部操作栏 (素材载入与主题切换)
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        self.btn_open_file = PushButton(FIF.FOLDER, "📁 选择拼图素材...")
        self.btn_open_file.clicked.connect(self._select_image_file)
        top_bar.addWidget(self.btn_open_file)

        self.label_filepath = QLabel("📥 拖拽拼图图片至此，或点击左侧浏览选择素材")
        self.label_filepath.setStyleSheet("color: #e0e0e0; font-size: 12px; font-weight: normal;")
        top_bar.addWidget(self.label_filepath, 1)

        # 深浅色主题切换按钮
        self.btn_theme = PushButton(FIF.BRUSH, "切换主题")
        self.btn_theme.clicked.connect(self._toggle_app_theme)
        top_bar.addWidget(self.btn_theme)

        self.main_layout.addLayout(top_bar)

        # 2. 中间工作区分割布局 (左侧：画布+胶卷，右侧：控制面板，采用可拖拽 QSplitter)
        self.work_splitter = QSplitter(Qt.Orientation.Horizontal, self.central_widget)
        self.work_splitter.setHandleWidth(8)
        self.work_splitter.setChildrenCollapsible(False)
        self.work_splitter.setStyleSheet(
            """
            QSplitter::handle {
                background-color: #272727;
                border: 1px solid #383838;
                border-radius: 3px;
                margin: 0px 2px;
            }
            QSplitter::handle:hover {
                background-color: #00bcd4;
            }
            """
        )

        # 左侧区域
        left_widget = QWidget(self.work_splitter)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # 交互画布与原地播放器
        self.canvas = InteractiveCanvas(left_widget)
        self.canvas.gridModified.connect(self._on_canvas_grid_modified)
        self.canvas.frameChanged.connect(self._on_player_frame_changed)
        left_layout.addWidget(self.canvas, 1)

        # 动图播放器简单控制栏
        player_bar = QHBoxLayout()
        self.btn_play_pause = PushButton(FIF.PLAY, "播放")
        self.btn_play_pause.clicked.connect(self._toggle_playback)
        player_bar.addWidget(self.btn_play_pause)

        self.label_frame_info = QLabel("帧进度: 00/00")
        self.label_frame_info.setStyleSheet("color: #e0e0e0; font-weight: bold; font-size: 12px;")
        player_bar.addWidget(self.label_frame_info)
        player_bar.addStretch()
        left_layout.addLayout(player_bar)

        # 底部卡片胶卷
        self.filmstrip = FilmstripWidget(left_widget)
        self.filmstrip.activeFramesChanged.connect(self._on_active_frames_changed)
        left_layout.addWidget(self.filmstrip)

        self.work_splitter.addWidget(left_widget)

        # 右侧控制面板
        self.sidebar = ControlSidebar(self.work_splitter)
        self.sidebar.gridParamChanged.connect(self._on_grid_param_changed)
        self.sidebar.realignRequested.connect(self._realign_grid)
        self.sidebar.resetGridRequested.connect(self._reset_grid_uniform)
        self.sidebar.timingChanged.connect(self._on_timing_changed)
        self.sidebar.captionChanged.connect(self.canvas.set_caption)
        self.sidebar.captionConfigChanged.connect(self.canvas.set_caption_config)
        self.canvas.captionPositionMoved.connect(self.sidebar.update_caption_position_ratio)
        self.sidebar.startProcessRequested.connect(self._start_slice_and_export)
        self.sidebar.openOutputRequested.connect(self._open_output_dir)
        self.work_splitter.addWidget(self.sidebar)

        # 分配伸缩权重与初始尺寸 (左侧画布为主拉伸 3，右侧面板 1)
        self.work_splitter.setStretchFactor(0, 3)
        self.work_splitter.setStretchFactor(1, 1)
        self.work_splitter.setSizes([840, 360])

        self.main_layout.addWidget(self.work_splitter, 1)

        # 3. 底部状态栏
        status_bar = QHBoxLayout()
        self.label_status = QLabel("就绪 | 请载入拼图素材")
        self.label_status.setStyleSheet("color: #b8b8b8; font-size: 12px;")
        status_bar.addWidget(self.label_status, 1)

        # 进度旋转环 (计算中显示)
        self.progress_ring = ProgressRing(self)
        self.progress_ring.setFixedSize(20, 20)
        self.progress_ring.setVisible(False)
        status_bar.addWidget(self.progress_ring)

        self.main_layout.addLayout(status_bar)

        # 注册中央工作区到 Fluent 主窗口
        self.addSubInterface(self.central_widget, FIF.PHOTO, "动图工坊")

        # 挂载全局主题状态监听并应用初始高对比度样式
        ThemeManager.get_instance().themeChanged.connect(self._on_theme_changed)
        self._on_theme_changed()

    # ---------------- 素材载入与拖拽处理 ----------------

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = Path(urls[0].toLocalFile())
            if file_path.is_file() and file_path.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp", ".webp"):
                self.load_image_file(file_path)
                event.acceptProposedAction()
                return
        super().dropEvent(event)

    def _select_image_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择多帧拼图素材",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp);;All Files (*.*)",
        )
        if file_path:
            self.load_image_file(Path(file_path))

    def load_image_file(self, file_path: Path):
        """载入图像文件并初始化网格参考线"""
        try:
            pil_img = Image.open(file_path)
            self.current_file_path = file_path
            self.current_pil_image = pil_img
            self.label_filepath.setText(f"📄 素材: {file_path.name} ({pil_img.width} × {pil_img.height} px)")
            self.label_status.setText(f"已载入素材: {file_path.name}")

            # 初始化默认网格配置 (若开启智能裁剪则自动执行投影波谷吸附)
            rows = self.sidebar.spin_rows.value()
            cols = self.sidebar.spin_cols.value()
            smart_crop = self.sidebar.switch_crop.isChecked()

            bounds = None
            if smart_crop:
                bounds = detect_bounds(pil_img)

            self.current_grid = calculate_default_grid(
                pil_img.width,
                pil_img.height,
                rows,
                cols,
                bounds=bounds,
                img=pil_img,
                auto_snap=smart_crop,
            )
            self.canvas.set_source_image(pil_img, self.current_grid)
            self.filmstrip.clear()
            self.btn_play_pause.setText("播放")
            self.label_frame_info.setText("帧进度: 00/00")

            InfoBar.success("素材载入成功", f"图像尺寸: {pil_img.width}×{pil_img.height}", parent=self, position=InfoBarPosition.TOP_RIGHT, duration=2500)
        except Exception as e:
            InfoBar.error("载入失败", str(e), parent=self, position=InfoBarPosition.TOP_RIGHT)

    # ---------------- 交互联动回调 ----------------

    def _on_grid_param_changed(self, rows: int, cols: int, smart_crop: bool):
        if not self.current_pil_image:
            return
        bounds = None
        if smart_crop:
            bounds = detect_bounds(self.current_pil_image)
        self.current_grid = calculate_default_grid(
            self.current_pil_image.width,
            self.current_pil_image.height,
            rows,
            cols,
            bounds=bounds,
            img=self.current_pil_image,
            auto_snap=smart_crop,
        )
        self.canvas.update_grid(self.current_grid)

    def _realign_grid(self):
        """用户主动请求智能波谷居中吸附对齐"""
        if not self.current_pil_image:
            InfoBar.warning("未载入素材", "请先载入多格图像素材", parent=self, position=InfoBarPosition.TOP_RIGHT, duration=2000)
            return
        rows = self.sidebar.spin_rows.value()
        cols = self.sidebar.spin_cols.value()
        bounds = detect_bounds(self.current_pil_image)
        self.current_grid = calculate_default_grid(
            self.current_pil_image.width,
            self.current_pil_image.height,
            rows,
            cols,
            bounds=bounds,
            img=self.current_pil_image,
            auto_snap=True,
        )
        self.canvas.update_grid(self.current_grid)
        self.label_status.setText("已智能吸附分镜缝隙中位线")
        InfoBar.success("智能吸附对齐完成", "已自动识别分镜留白缝隙并居中定位", parent=self, position=InfoBarPosition.TOP_RIGHT, duration=2000)

    def _reset_grid_uniform(self):
        """用户请求恢复纯几何均匀等分"""
        if not self.current_pil_image:
            return
        rows = self.sidebar.spin_rows.value()
        cols = self.sidebar.spin_cols.value()
        self.current_grid = calculate_default_grid(
            self.current_pil_image.width,
            self.current_pil_image.height,
            rows,
            cols,
            bounds=None,
            auto_snap=False,
        )
        self.canvas.update_grid(self.current_grid)
        self.label_status.setText("已恢复几何均匀等分")
        InfoBar.info("已重置网格", "已恢复为纯几何等距离均匀划分", parent=self, position=InfoBarPosition.TOP_RIGHT, duration=2000)

    def _on_canvas_grid_modified(self, new_grid: GridConfig):
        self.current_grid = new_grid
        self.label_status.setText("网格参考线已手动微调")

    def _on_timing_changed(self, duration: int, end_pause: int, boomerang: bool):
        self.canvas.set_durations(duration, end_pause, boomerang)

    def _toggle_playback(self):
        if self.canvas.is_playing:
            self.canvas.stop_playback()
            self.btn_play_pause.setText("播放")
        else:
            self.canvas.start_playback()
            self.btn_play_pause.setText("暂停")

    def _on_player_frame_changed(self, current_idx: int, total_frames: int):
        self.label_frame_info.setText(f"帧进度: {current_idx + 1:02d}/{total_frames:02d}")

    def _on_active_frames_changed(self, active_frames: List[Image.Image]):
        self.active_frames = active_frames
        boomerang = self.sidebar.rb_loop_boomerang.isChecked()
        self.canvas.set_animation_frames(active_frames, boomerang=boomerang)
        self.label_status.setText(f"当前有效序列帧: {len(active_frames)} 帧")

    # ---------------- 异步切片与导出流水线 ----------------

    def _start_slice_and_export(self):
        if not self.current_pil_image or not self.current_grid:
            InfoBar.warning("提示", "请先载入一张拼图素材！", parent=self, position=InfoBarPosition.TOP_RIGHT)
            return

        # 锁定界面，进入计算中
        self.sidebar.set_processing_state(True)
        self.progress_ring.setVisible(True)
        self.label_status.setText("正在执行切片拆解...")

        # 启动 SliceWorker
        smart_crop = self.sidebar.switch_crop.isChecked()
        self.slice_worker = SliceWorker(self.current_pil_image, self.current_grid, smart_crop=smart_crop, parent=self)
        self.slice_worker.stageChanged.connect(self.label_status.setText)
        self.slice_worker.sliceFinished.connect(self._on_slice_finished)
        self.slice_worker.sliceFailed.connect(self._on_worker_failed)
        self.slice_worker.start()

    def _on_slice_finished(self, frames: List[Image.Image], grid: GridConfig):
        self.active_frames = frames
        self.filmstrip.set_frames(frames)

        # 切片完成，紧接着启动 ExportWorker
        preset = self.sidebar.get_export_preset()
        duration = self.sidebar.slider_duration.value()
        end_pause = self.sidebar.slider_pause.value()
        boomerang = self.sidebar.rb_loop_boomerang.isChecked()
        base_name = self.current_file_path.stem if self.current_file_path else "animation"
        caption_text = self.sidebar.get_caption_text()
        caption_pos = self.sidebar.get_caption_position()
        caption_cfg = self.sidebar.get_caption_config()

        self.export_worker = ExportWorker(
            frames=frames,
            preset=preset,
            duration=duration,
            end_pause=end_pause,
            boomerang=boomerang,
            base_name=base_name,
            caption_text=caption_text,
            caption_pos=caption_pos,
            caption_config=caption_cfg,
            parent=self,
        )
        self.export_worker.stageChanged.connect(self.label_status.setText)

        self.export_worker.exportFinished.connect(self._on_export_finished)
        self.export_worker.exportFailed.connect(self._on_worker_failed)
        self.export_worker.start()


    def _on_export_finished(self, output_path: str, size_bytes: int):
        self.sidebar.set_processing_state(False)
        self.progress_ring.setVisible(False)
        size_kb = size_bytes / 1024
        msg = f"已成功导出！体积: {size_kb:.1f} KB\n路径: {output_path}"
        self.label_status.setText(f"导出完成: {Path(output_path).name} ({size_kb:.1f} KB)")
        InfoBar.success("动图导出完成", msg, parent=self, position=InfoBarPosition.TOP_RIGHT, duration=4500)

    def _on_worker_failed(self, error_msg: str):
        self.sidebar.set_processing_state(False)
        self.progress_ring.setVisible(False)
        self.label_status.setText(f"操作失败: {error_msg}")
        InfoBar.error("处理出错", error_msg, parent=self, position=InfoBarPosition.TOP_RIGHT, duration=5000)

    def _open_output_dir(self):
        gifs_dir, _ = get_default_output_dirs()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(gifs_dir)))

    def _toggle_app_theme(self):
        ThemeManager.get_instance().toggle_theme()

    def _on_theme_changed(self, theme_name: Optional[str] = None):
        mgr = ThemeManager.get_instance()
        qss = mgr.get_theme_stylesheet()
        self.central_widget.setStyleSheet(qss)
        is_dark = mgr.is_dark()
        self.btn_theme.setText("切换浅色" if is_dark else "切换深色")
        self.label_filepath.setStyleSheet(f"color: {mgr.tokens.text_secondary}; font-size: 12px;")
        self.label_frame_info.setStyleSheet(f"color: {mgr.tokens.text_primary}; font-weight: bold; font-size: 12px;")
        self.label_status.setStyleSheet(f"color: {mgr.tokens.text_secondary}; font-size: 12px;")
