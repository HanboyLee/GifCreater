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


@pytest.fixture(scope="session")
def qapp():
    """提供单例 QApplication"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_canvas_and_player(qapp):
    """测试可交互画布与原地动图播放器"""
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
    """测试现代参数控制侧边栏"""
    sidebar = ControlSidebar()

    # 1. 默认预设
    assert sidebar.get_export_preset() == "gif"

    # 2. 切换至微信表情包
    sidebar.rb_exp_wechat.setChecked(True)
    assert sidebar.get_export_preset() == "wechat"

    # 3. 切换至 WebP
    sidebar.rb_exp_webp.setChecked(True)
    assert sidebar.get_export_preset() == "webp"

    # 4. 锁定与解锁处理状态
    sidebar.set_processing_state(True)
    assert sidebar.btn_process.isEnabled() is False
    sidebar.set_processing_state(False)
    assert sidebar.btn_process.isEnabled() is True


def test_main_window_headless(qapp, tmp_path):
    """测试主窗口生命周期与素材加载"""
    win = MainWindow()
    assert win.windowTitle().startswith("🎞️ GifCreater")

    # 创建测试图并载入
    img = create_dummy_grid_image(120, 120, rows=2, cols=2)
    img_path = tmp_path / "test_load.png"
    img.save(img_path)

    win.load_image_file(img_path)
    assert win.current_pil_image is not None
    assert win.current_grid is not None
    assert win.current_grid.rows == 4  # 侧边栏默认 4 行
