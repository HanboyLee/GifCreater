# -*- coding: utf-8 -*-
"""
GifCreater 交互式视口画布 (Interactive Canvas)
==============================================

基于 QGraphicsView 实现的高性能图形工作台：
- 支持高清像素图像渲染
- 鼠标滚轮平滑缩放与空格键/中键拖拽平移
- 交互式红色网格分割线（悬停高亮、抓取拖拽微调、坐标双向映射）
- 原地动图播放器（FPS 自适应，常规循环 / 乒乓往复 Boomerang）
"""

from typing import List, Optional
from PIL import Image
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import (
    QColor,
    QCursor,
    QFont,
    QImage,
    QPainter,
    QPen,
    QPixmap,
    QWheelEvent,
    QMouseEvent,
    QKeyEvent,
)
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QStyle,
)

from ..core import GridConfig
from ..core.caption import draw_caption, CaptionConfig




def pil_to_qpixmap(pil_img: Image.Image) -> QPixmap:
    """将 PIL 图像转换为 QPixmap"""
    if pil_img.mode != "RGBA":
        pil_img = pil_img.convert("RGBA")
    data = pil_img.tobytes("raw", "RGBA")
    qimg = QImage(data, pil_img.width, pil_img.height, QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(qimg)


class DraggableLineItem(QGraphicsLineItem):
    """
    可拖拽网格分割参考线：支持鼠标抓取平移微调
    """
    def __init__(self, orientation: str, coord: float, min_val: float, max_val: float, length: float, parent_canvas):
        super().__init__()
        self.orientation = orientation  # "H" (水平线，调整Y) 或 "V" (垂直线，调整X)
        self.coord = coord
        self.min_val = min_val
        self.max_val = max_val
        self.length = length
        self.parent_canvas = parent_canvas
        self.is_dragging = False

        self.setAcceptHoverEvents(True)
        self.update_geometry()
        self.set_normal_style()

    def update_geometry(self):
        if self.orientation == "H":
            self.setLine(0, self.coord, self.length, self.coord)
        else:
            self.setLine(self.coord, 0, self.coord, self.length)

    def set_normal_style(self):
        pen = QPen(QColor(235, 50, 50, 200), 2, Qt.PenStyle.DashLine)
        pen.setCosmetic(True)  # 缩放时线条粗细不变
        self.setPen(pen)

    def set_hover_style(self):
        pen = QPen(QColor(255, 230, 0, 255), 3, Qt.PenStyle.SolidLine)
        pen.setCosmetic(True)
        self.setPen(pen)

    def hoverEnterEvent(self, event):
        self.set_hover_style()
        if self.orientation == "H":
            self.setCursor(QCursor(Qt.CursorShape.SplitVCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.SplitHCursor))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if not self.is_dragging:
            self.set_normal_style()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.set_hover_style()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            scene_pos = event.scenePos()
            if self.orientation == "H":
                new_y = max(self.min_val + 5, min(self.max_val - 5, scene_pos.y()))
                self.coord = new_y
            else:
                new_x = max(self.min_val + 5, min(self.max_val - 5, scene_pos.x()))
                self.coord = new_x
            self.update_geometry()
            self.parent_canvas.on_line_moved()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.set_normal_style()
            self.parent_canvas.on_line_drag_finished()
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class DraggableCaptionItem(QGraphicsItem):
    """
    可直接在画布上鼠标抓取平移微调的表情包配文交互图元
    """
    def __init__(self, parent_canvas):
        super().__init__()
        self.parent_canvas = parent_canvas
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self.is_dragging = False
        self.rect = QRectF(-70, -22, 140, 44)
        self.setZValue(100)

    def boundingRect(self) -> QRectF:
        return self.rect

    def paint(self, painter: QPainter, option, widget=None):
        if self.is_dragging or option.state & QStyle.StateFlag.State_MouseOver:
            pen = QPen(QColor(34, 211, 238, 220), 1.5, Qt.PenStyle.DashLine)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(QColor(34, 211, 238, 30))
            painter.drawRoundedRect(self.rect, 6, 6)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            self.update()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            scene_pos = event.scenePos()
            self.setPos(scene_pos)
            self.parent_canvas.on_caption_item_moving(scene_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            self.update()
            self.parent_canvas.on_caption_item_drag_finished(self.scenePos())
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class InteractiveCanvas(QGraphicsView):
    """
    可交互画布：整合大图预览、网格线拖拽微调及动图原地播放器
    """
    gridModified = pyqtSignal(object)  # 发射 GridConfig
    frameChanged = pyqtSignal(int, int)  # 当前帧索引, 总帧数
    captionPositionMoved = pyqtSignal(float, float)  # (x_ratio, y_ratio)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # 视口属性配置
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(QColor("#181818"))
        self.setStyleSheet("InteractiveCanvas { background-color: #181818; border: 1px solid #333333; border-radius: 8px; }")

        # 数据状态
        self.current_pil_image: Optional[Image.Image] = None
        self.pixmap_item: Optional[QGraphicsPixmapItem] = None
        self.grid_lines: List[DraggableLineItem] = []
        self.grid_config: Optional[GridConfig] = None
        self.caption_item: Optional[DraggableCaptionItem] = None
        self.caption_config: Optional[CaptionConfig] = None
        self.placeholder_item = None

        self._show_placeholder()


        # 播放器状态与配文
        self.frames: List[Image.Image] = []
        self.frame_pixmaps: List[QPixmap] = []
        self.play_indices: List[int] = []
        self.current_play_idx = 0
        self.is_playing = False
        self.duration_ms = 350
        self.end_pause_ms = 1500
        self.boomerang = False
        self.caption_text = ""
        self.caption_pos = "bottom"

        self.play_timer = QTimer(self)
        self.play_timer.timeout.connect(self._on_play_tick)


        # 拖拽平移辅助
        self.space_pressed = False
        self.middle_mouse_pressed = False
        self.last_mouse_pos = None

    def _show_placeholder(self):
        """在画布中央展示友好的深色空状态提示"""
        self.scene.clear()
        self.pixmap_item = None
        self.scene.setSceneRect(0, 0, 640, 440)
        text_item = self.scene.addText("📥  请将多帧拼图图片拖拽至此，或点击左上角选择素材")
        text_item.setDefaultTextColor(QColor("#888888"))
        text_item.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        br = text_item.boundingRect()
        text_item.setPos((640 - br.width()) / 2, (440 - br.height()) / 2)
        self.placeholder_item = text_item

    def set_source_image(self, pil_img: Image.Image, grid: Optional[GridConfig] = None):
        """载入原图素材"""
        self.placeholder_item = None
        self.stop_playback()
        self.frames.clear()
        self.frame_pixmaps.clear()
        self.current_pil_image = pil_img
        self.grid_config = grid

        self.scene.clear()
        self.grid_lines.clear()

        # 渲染原图 Pixmap
        pixmap = pil_to_qpixmap(pil_img)
        self.pixmap_item = self.scene.addPixmap(pixmap)
        self.scene.setSceneRect(0, 0, pil_img.width, pil_img.height)

        # 渲染可拖拽参考线
        if grid:
            self._render_grid_lines(grid, pil_img.width, pil_img.height)

        self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def update_grid(self, grid: GridConfig):
        """更新网格配置并重绘参考线"""
        self.grid_config = grid
        if not self.current_pil_image:
            return

        for line in self.grid_lines:
            self.scene.removeItem(line)
        self.grid_lines.clear()

        self._render_grid_lines(grid, self.current_pil_image.width, self.current_pil_image.height)

    def _render_grid_lines(self, grid: GridConfig, w: int, h: int):
        # 边界偏移
        offset_x, offset_y = 0, 0
        if grid.crop_bounds:
            offset_x, offset_y = grid.crop_bounds[0], grid.crop_bounds[1]

        # 垂直参考线
        col_coords = [c + offset_x for c in grid.col_lines]
        for i, cx in enumerate(col_coords):
            min_x = col_coords[i-1] if i > 0 else 0
            max_x = col_coords[i+1] if i < len(col_coords)-1 else w
            line = DraggableLineItem("V", float(cx), float(min_x), float(max_x), float(h), self)
            self.scene.addItem(line)
            self.grid_lines.append(line)

        # 水平参考线
        row_coords = [r + offset_y for r in grid.row_lines]
        for i, ry in enumerate(row_coords):
            min_y = row_coords[i-1] if i > 0 else 0
            max_y = row_coords[i+1] if i < len(row_coords)-1 else h
            line = DraggableLineItem("H", float(ry), float(min_y), float(max_y), float(w), self)
            self.scene.addItem(line)
            self.grid_lines.append(line)

    def on_line_moved(self):
        """单线拖拽中的回调"""
        pass

    def on_line_drag_finished(self):
        """拖拽完成，同步回 GridConfig 并发射信号"""
        if not self.grid_config:
            return

        offset_x = self.grid_config.crop_bounds[0] if self.grid_config.crop_bounds else 0
        offset_y = self.grid_config.crop_bounds[1] if self.grid_config.crop_bounds else 0

        v_lines = sorted([round(line.coord - offset_x) for line in self.grid_lines if line.orientation == "V"])
        h_lines = sorted([round(line.coord - offset_y) for line in self.grid_lines if line.orientation == "H"])

        self.grid_config.col_lines = v_lines
        self.grid_config.row_lines = h_lines
        self.gridModified.emit(self.grid_config)

    # ---------------- 动图原地播放器与配文控制 ----------------

    def _generate_frame_pixmap(self, frame: Image.Image) -> QPixmap:
        """根据当前配文配置动态生成帧 Pixmap (所见即所得)"""
        if self.caption_config and self.caption_config.text:
            rendered = draw_caption(frame, self.caption_config)
            return pil_to_qpixmap(rendered)
        elif self.caption_text:
            rendered = draw_caption(frame, self.caption_text, position=self.caption_pos)
            return pil_to_qpixmap(rendered)
        return pil_to_qpixmap(frame)

    def set_caption_config(self, cfg: CaptionConfig):
        """实时更新表情包配文与变换配置并刷新呈现 (WYSIWYG)"""
        self.caption_config = cfg
        self.caption_text = cfg.text.strip() if cfg and cfg.text else ""

        w = max(100.0, self.scene.sceneRect().width())
        h = max(100.0, self.scene.sceneRect().height())

        if self.caption_text:
            if not self.caption_item:
                self.caption_item = DraggableCaptionItem(self)
                self.scene.addItem(self.caption_item)

            pos_x = w * cfg.pos_x_ratio
            pos_y = h * cfg.pos_y_ratio
            self.caption_item.setPos(pos_x, pos_y)
            self.caption_item.setRotation(-cfg.rotation_deg)
            self.caption_item.setVisible(True)
        else:
            if self.caption_item:
                self.caption_item.setVisible(False)

        if self.frames:
            self.frame_pixmaps = [self._generate_frame_pixmap(f) for f in self.frames]
            self._display_current_frame()
        elif self.current_pil_image and self.pixmap_item:
            if self.caption_text:
                rendered = draw_caption(self.current_pil_image, cfg)
                self.pixmap_item.setPixmap(pil_to_qpixmap(rendered))
            else:
                self.pixmap_item.setPixmap(pil_to_qpixmap(self.current_pil_image))

    def set_caption(self, text: str, position: str = "bottom"):
        """兼容旧版纯文本设置"""
        cfg = CaptionConfig(
            text=text,
            pos_y_ratio=0.12 if position == "top" else 0.88,
        )
        self.set_caption_config(cfg)

    def on_caption_item_moving(self, scene_pos: QPointF):
        """拖拽中回调"""
        pass

    def on_caption_item_drag_finished(self, scene_pos: QPointF):
        """拖拽释放后，计算相对坐标并通知侧边栏"""
        w = self.scene.sceneRect().width()
        h = self.scene.sceneRect().height()
        if w > 10 and h > 10:
            rx = max(0.05, min(0.95, scene_pos.x() / w))
            ry = max(0.05, min(0.95, scene_pos.y() / h))
            if self.caption_config:
                self.caption_config.pos_x_ratio = rx
                self.caption_config.pos_y_ratio = ry
            self.captionPositionMoved.emit(rx, ry)
            if self.frames:
                self.frame_pixmaps = [self._generate_frame_pixmap(f) for f in self.frames]
                self._display_current_frame()


    def set_animation_frames(self, frames: List[Image.Image], boomerang: bool = False):
        """载入切片动图帧并准备播放"""
        self.stop_playback()
        self.frames = frames
        self.boomerang = boomerang
        self.frame_pixmaps = [self._generate_frame_pixmap(f) for f in frames]


        if not frames:
            return

        # 构建播放索引序列
        n = len(frames)
        if boomerang and n > 2:
            self.play_indices = list(range(n)) + list(range(n - 2, 0, -1))
        else:
            self.play_indices = list(range(n))

        # 清除参考线并显示首帧
        for line in self.grid_lines:
            self.scene.removeItem(line)
        self.grid_lines.clear()

        self.current_play_idx = 0
        self._display_current_frame()
        self.start_playback()

    def set_durations(self, duration_ms: int, end_pause_ms: int, boomerang: bool = False):
        """更新播放节奏"""
        self.duration_ms = duration_ms
        self.end_pause_ms = end_pause_ms
        self.boomerang = boomerang
        if self.frames:
            n = len(self.frames)
            if boomerang and n > 2:
                self.play_indices = list(range(n)) + list(range(n - 2, 0, -1))
            else:
                self.play_indices = list(range(n))

    def start_playback(self):
        if not self.frame_pixmaps:
            return
        self.is_playing = True
        self._schedule_next_frame()

    def stop_playback(self):
        self.is_playing = False
        self.play_timer.stop()

    def seek_frame(self, index: int):
        if not self.frames:
            return
        self.current_play_idx = max(0, min(len(self.play_indices) - 1, index))
        self._display_current_frame()

    def _display_current_frame(self):
        if not self.frame_pixmaps:
            return
        actual_frame_idx = self.play_indices[self.current_play_idx]
        pixmap = self.frame_pixmaps[actual_frame_idx]

        if not self.pixmap_item:
            self.pixmap_item = self.scene.addPixmap(pixmap)
        else:
            self.pixmap_item.setPixmap(pixmap)

        self.scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())
        self.frameChanged.emit(actual_frame_idx, len(self.frames))

    def _on_play_tick(self):
        if not self.is_playing or not self.play_indices:
            return

        self.current_play_idx = (self.current_play_idx + 1) % len(self.play_indices)
        self._display_current_frame()
        self._schedule_next_frame()

    def _schedule_next_frame(self):
        actual_frame_idx = self.play_indices[self.current_play_idx]
        # 尾帧停留判断
        if actual_frame_idx == len(self.frames) - 1 and self.end_pause_ms > 0:
            delay = self.end_pause_ms
        else:
            delay = self.duration_ms
        self.play_timer.start(max(10, delay))

    # ---------------- 鼠标滚轮缩放与平移 ----------------

    def wheelEvent(self, event: QWheelEvent):
        # 滚轮平滑缩放
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)
        event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Space:
            self.space_pressed = True
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            event.accept()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Space:
            self.space_pressed = False
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            event.accept()
        else:
            super().keyReleaseEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if (self.space_pressed and event.button() == Qt.MouseButton.LeftButton) or event.button() == Qt.MouseButton.MiddleButton:
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            self.last_mouse_pos = event.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.last_mouse_pos is not None:
            delta = event.pos() - self.last_mouse_pos
            self.last_mouse_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.last_mouse_pos is not None:
            self.last_mouse_pos = None
            if self.space_pressed:
                self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            else:
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            event.accept()
        else:
            super().mouseReleaseEvent(event)
