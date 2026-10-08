# -*- coding: utf-8 -*-
"""ui/video_dialog.py 单元测试：验证对话框生命周期、步进、网格切换与模式输出。"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
import pytest

from src.gifcreater.ui.video_dialog import (
    NeighborThumbnailCard,
    VideoStillDialog,
    format_seconds,
)
from tests.fixtures.mock_video import index_from_image, make_color_video


@pytest.fixture()
def video(tmp_path):
    return make_color_video(tmp_path / "clip.mp4", n=12, size=(64, 48), fps=10)


def test_format_seconds():
    assert format_seconds(0.0) == "00:00.00"
    assert format_seconds(65.4) == "01:05.40"


def test_neighbor_card_click(qapp):
    card = NeighborThumbnailCard(5, "第5帧")
    clicked_indices = []
    card.clicked.connect(lambda idx: clicked_indices.append(idx))
    # 模拟点击事件
    from PyQt6.QtCore import QPointF
    from PyQt6.QtGui import QMouseEvent

    evt = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(10, 10),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    card.mousePressEvent(evt)
    assert clicked_indices == [5]


def test_dialog_init_and_steps(qapp, video):
    dlg = VideoStillDialog(video)
    try:
        assert dlg.info.frame_count == 12
        assert dlg.slider.maximum() == 11
        assert dlg.current_index == 0

        # 单帧步进
        dlg._step_next_frame()
        assert dlg.current_index == 1
        dlg._step_prev_frame()
        assert dlg.current_index == 0

        # 秒步进 (fps=10，跳转 10 帧)
        dlg._step_forward_second()
        assert dlg.current_index == 10
        dlg._step_back_second()
        assert dlg.current_index == 0

        # 点击邻近卡片
        dlg._on_neighbor_clicked(3)
        assert dlg.current_index == 3
    finally:
        dlg.close()


def test_dialog_grid_presets(qapp, video):
    dlg = VideoStillDialog(video)
    try:
        # 3x3
        dlg._on_grid_preset_changed(0)
        assert (dlg.spin_rows.value(), dlg.spin_cols.value()) == (3, 3)
        assert not dlg.spin_rows.isEnabled()

        # 4x6
        dlg._on_grid_preset_changed(1)
        assert (dlg.spin_rows.value(), dlg.spin_cols.value()) == (4, 6)
        assert not dlg.spin_rows.isEnabled()

        # 6x4
        dlg._on_grid_preset_changed(2)
        assert (dlg.spin_rows.value(), dlg.spin_cols.value()) == (6, 4)
        assert not dlg.spin_rows.isEnabled()

        # 自定义
        dlg._on_grid_preset_changed(3)
        assert dlg.spin_rows.isEnabled()
        assert dlg.spin_cols.isEnabled()
    finally:
        dlg.close()


def test_dialog_mode_a_accept(qapp, video):
    dlg = VideoStillDialog(video)
    try:
        dlg.slider.setValue(4)
        dlg._on_mode_a_clicked()
        assert dlg.result_mode == "still"
        assert dlg.still_image is not None
        assert index_from_image(dlg.still_image) == 4
        assert dlg.selected_rows == 3
        assert dlg.selected_cols == 3
    finally:
        dlg.close()


def test_dialog_mode_b_sample(qapp, video):
    dlg = VideoStillDialog(video)
    try:
        # 启动模式 B
        dlg._on_mode_b_clicked()
        if dlg._sample_worker:
            dlg._sample_worker.wait(3000)
        qapp.processEvents()

        assert dlg.result_mode == "sample"
        assert dlg.sampled_frames is not None
        assert len(dlg.sampled_frames) == 9  # 3x3=9
    finally:
        dlg.close()


def test_dialog_key_navigation(qapp, video):
    dlg = VideoStillDialog(video)
    try:
        # 模拟按右键
        key_evt = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Right, Qt.KeyboardModifier.NoModifier)
        dlg.keyPressEvent(key_evt)
        assert dlg.current_index == 1

        # 模拟按左键
        key_evt = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Left, Qt.KeyboardModifier.NoModifier)
        dlg.keyPressEvent(key_evt)
        assert dlg.current_index == 0

        # 模拟 Shift + 右键
        key_evt = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Right, Qt.KeyboardModifier.ShiftModifier)
        dlg.keyPressEvent(key_evt)
        assert dlg.current_index == 10

        # 模拟 Shift + 左键
        key_evt = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Left, Qt.KeyboardModifier.ShiftModifier)
        dlg.keyPressEvent(key_evt)
        assert dlg.current_index == 0
    finally:
        dlg.close()
