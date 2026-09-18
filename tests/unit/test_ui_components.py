# -*- coding: utf-8 -*-
"""
tests/unit/test_ui_components.py
PyQt6 Fluent 表现层交互与组件单元测试
"""

import sys
import pytest
from PIL import Image
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from src.gifcreater.core import calculate_default_grid
from src.gifcreater.ui.canvas import InteractiveCanvas, pil_to_qpixmap
from src.gifcreater.ui.filmstrip import FilmstripWidget
from src.gifcreater.ui.sidebar import ControlSidebar
from src.gifcreater.ui.main_window import MainWindow
from tests.fixtures.mock_images import create_dummy_grid_image


def test_canvas_and_player(qapp):
    """测试可交互画布与原地动图播放器及配文联动"""
    canvas = InteractiveCanvas()
    pil_img = create_dummy_grid_image(120, 120, rows=2, cols=2)
    grid = calculate_default_grid(120, 120, 2, 2)

    # 1. 载入原图
    canvas.set_source_image(pil_img, grid)
    assert canvas.current_pil_image is not None
    assert len(canvas.grid_lines) > 0

    # 2. 模拟参考线拖拽完成
    canvas.on_line_drag_finished()

    # 3. 载入切片帧并启动播放
    frames = [pil_img.crop((0, 0, 60, 60)), pil_img.crop((60, 0, 120, 60))]
    canvas.set_animation_frames(frames, boomerang=True)
    assert canvas.is_playing is True
    assert len(canvas.play_indices) == 2  # 2 帧普通循环

    # 4. 定时器滴答
    canvas._on_play_tick()
    assert canvas.current_play_idx == 1

    # 5. 暂停播放与寻帧
    canvas.stop_playback()
    assert canvas.is_playing is False
    canvas.seek_frame(0)
    assert canvas.current_play_idx == 0

    # 6. 配文所见即所得测试
    canvas.set_caption("测试表情包配文", "bottom")
    assert canvas.caption_text == "测试表情包配文"
    assert canvas.caption_pos == "bottom"


def test_filmstrip_widget(qapp):
    """测试卡片流式序列帧胶卷与废帧剔除"""
    filmstrip = FilmstripWidget()
    pil_img = create_dummy_grid_image(60, 60)
    frames = [pil_img.copy() for _ in range(4)]

    # 1. 载入 4 帧
    filmstrip.set_frames(frames)
    assert len(filmstrip.cards) == 4
    assert len(filmstrip.get_active_frames()) == 4

    # 2. 选中第一帧
    filmstrip._on_card_selected(0, True)
    assert 0 in filmstrip.selected_indices

    # 3. 剔除第二帧
    filmstrip.cards[1].set_deleted(True)
    active = filmstrip.get_active_frames()
    assert len(active) == 3

    # 4. 恢复第二帧
    filmstrip.cards[1].set_deleted(False)
    assert len(filmstrip.get_active_frames()) == 4

    # 5. 清空
    filmstrip.clear()
    assert len(filmstrip.cards) == 0


def test_control_sidebar(qapp):
    """测试现代参数控制侧边栏与配文变换控件"""
    from PyQt6.QtCore import Qt

    sidebar = ControlSidebar()

    # 验证自适应尺寸限制与横向滚动条策略
    assert sidebar.minimumWidth() == 320
    assert sidebar.maximumWidth() == 480
    assert sidebar.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff

    # 1. 默认预设 (微信表情包)
    assert sidebar.get_export_preset() == "wechat"

    # 2. 切换下拉预设
    sidebar.combo_presets.setCurrentIndex(1)
    assert sidebar.get_export_preset() == "xiaohongshu"
    sidebar.combo_presets.setCurrentIndex(2)
    assert sidebar.get_export_preset() == "hd_gif"
    sidebar.combo_presets.setCurrentIndex(3)
    assert sidebar.get_export_preset() == "webp"

    # 3. 配文输入、旋转与配置获取
    cfg_captured = []
    sidebar.captionConfigChanged.connect(lambda cfg: cfg_captured.append(cfg))

    sidebar.edit_caption.setText("大吉大利")
    assert sidebar.get_caption_text() == "大吉大利"
    assert len(cfg_captured) > 0
    assert cfg_captured[-1].text == "大吉大利"

    # 旋转角度滑块与快捷键
    sidebar._set_rotation_angle(-15)
    assert sidebar.caption_rotation == -15.0
    assert cfg_captured[-1].rotation_deg == -15.0

    # 九宫格快捷对齐
    sidebar._set_position_ratio(0.5, 0.12)
    assert sidebar.caption_pos_y_ratio == 0.12
    assert sidebar.get_caption_position() == "top"

    # 一键模板
    sidebar._apply_style_template("yellow")
    assert sidebar.text_color_rgb == (250, 204, 21)
    sidebar._apply_style_template("danger")
    assert sidebar.text_color_rgb == (239, 68, 68)
    sidebar._apply_style_template("watermark")
    assert sidebar.slider_text_opacity.value() == 35

    # 4. 锁定与解锁处理状态
    sidebar.set_processing_state(True)
    assert sidebar.btn_process.isEnabled() is False
    assert sidebar.edit_caption.isEnabled() is False
    assert sidebar.combo_presets.isEnabled() is False
    sidebar.set_processing_state(False)
    assert sidebar.btn_process.isEnabled() is True
    assert sidebar.edit_caption.isEnabled() is True
    assert sidebar.combo_presets.isEnabled() is True


def test_canvas_caption_drag_interaction(qapp):
    """测试画布配文图元拖拽与位置同步"""
    from PyQt6.QtCore import QPointF
    from src.gifcreater.core.caption import CaptionConfig

    canvas = InteractiveCanvas()
    pil_img = create_dummy_grid_image(200, 200)
    grid = calculate_default_grid(200, 200, 2, 2)
    canvas.set_source_image(pil_img, grid)

    # 载入带角度与透明度的配置
    cfg = CaptionConfig(text="可拖拽文字", pos_x_ratio=0.5, pos_y_ratio=0.88, rotation_deg=15.0)
    canvas.set_caption_config(cfg)
    assert canvas.caption_item is not None
    assert canvas.caption_item.isVisible() is True

    # 模拟鼠标拖拽释放至 (120, 80)
    moved_signals = []
    canvas.captionPositionMoved.connect(lambda x, y: moved_signals.append((x, y)))
    canvas.on_caption_item_drag_finished(QPointF(120, 80))

    assert len(moved_signals) > 0
    assert canvas.caption_config.pos_x_ratio == pytest.approx(120 / 200, rel=1e-2)
    assert canvas.caption_config.pos_y_ratio == pytest.approx(80 / 200, rel=1e-2)




def test_main_window_headless(qapp, tmp_path):
    """测试主窗口生命周期与素材加载"""
    win = MainWindow()
    assert win.windowTitle().startswith("🎞️ GifCreater")

    # 验证工作区 QSplitter 自适应
    assert win.work_splitter is not None
    assert win.work_splitter.count() == 2
    assert win.work_splitter.widget(1) == win.sidebar
    assert win.work_splitter.sizes()[1] > 0

    # 创建测试图并载入
    img = create_dummy_grid_image(120, 120, rows=2, cols=2)
    img_path = tmp_path / "test_load.png"
    img.save(img_path)

    win.load_image_file(img_path)
    assert win.current_pil_image is not None
    assert win.current_grid is not None
    assert win.current_grid.rows == 4  # 侧边栏默认 4 行
