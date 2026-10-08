# -*- coding: utf-8 -*-
"""tests/integration/test_video_integration.py
v3.6 视频静止帧与网格裁切/合并 GIF 端到端集成测试。
"""

from pathlib import Path
from PIL import Image
import pytest

from src.gifcreater.ui.main_window import MainWindow
from tests.fixtures.mock_video import make_color_video


@pytest.fixture()
def video_path(tmp_path):
    return make_color_video(tmp_path / "test_clip.mp4", n=12, size=(64, 48), fps=10)


def test_sidebar_presets(qapp):
    win = MainWindow()
    try:
        # 测试 3x3 胶囊
        win.sidebar.btn_preset_3x3.click()
        assert win.sidebar.spin_rows.value() == 3
        assert win.sidebar.spin_cols.value() == 3

        # 测试 4x6 胶囊
        win.sidebar.btn_preset_4x6.click()
        assert win.sidebar.spin_rows.value() == 4
        assert win.sidebar.spin_cols.value() == 6

        # 测试 6x4 胶囊
        win.sidebar.btn_preset_6x4.click()
        assert win.sidebar.spin_rows.value() == 6
        assert win.sidebar.spin_cols.value() == 4

        # 测试 4x4 胶囊
        win.sidebar.btn_preset_4x4.click()
        assert win.sidebar.spin_rows.value() == 4
        assert win.sidebar.spin_cols.value() == 4
    finally:
        win.close()


def test_load_pil_image_regression(qapp, tmp_path):
    win = MainWindow()
    try:
        img_path = tmp_path / "dummy.png"
        img = Image.new("RGB", (120, 120), (200, 100, 50))
        img.save(img_path)

        # 1. 传统 load_image_file 路径
        win.load_image_file(img_path)
        assert win.current_pil_image is not None
        assert win.current_grid is not None
        assert win.current_grid.rows == win.sidebar.spin_rows.value()

        # 2. 抽出的 load_pil_image 路径
        pil2 = Image.new("RGB", (90, 90), (50, 150, 200))
        win.load_pil_image(pil2, label_name="memory_img")
        assert win.current_pil_image is pil2
        assert win.current_grid.rows == win.sidebar.spin_rows.value()
    finally:
        win.close()


def test_mode_a_pipeline_end_to_end(qapp, video_path, monkeypatch):
    """端到端测试：模式 A (选定视频第 4 帧 -> 3x3 网格切片 -> 导出 GIF)。"""
    win = MainWindow()
    try:
        from src.gifcreater.ui.video_dialog import VideoStillDialog

        # Mock VideoStillDialog.exec() 返回 True，模拟用户选择第 4 帧与 3x3
        def mock_exec(dlg_self):
            dlg_self.result_mode = "still"
            dlg_self.current_index = 4
            dlg_self.still_image = dlg_self.reader.get_frame_by_index(4)
            dlg_self.selected_rows = 3
            dlg_self.selected_cols = 3
            return 1

        monkeypatch.setattr(VideoStillDialog, "exec", mock_exec)

        # 触发导入视频
        win.open_video_dialog(video_path)

        assert win.current_pil_image is not None
        assert win.sidebar.spin_rows.value() == 3
        assert win.sidebar.spin_cols.value() == 3
        assert win.current_grid.rows == 3
        assert win.current_grid.cols == 3

        # 启动一键切片并导出
        win._start_slice_and_export()

        # 等待切片工作线程完成
        if win.slice_worker:
            win.slice_worker.wait(3000)
        qapp.processEvents()

        # 等待导出工作线程完成
        if hasattr(win, "export_worker") and win.export_worker:
            win.export_worker.wait(3000)
        qapp.processEvents()

        assert win.active_frames is not None
        assert len(win.active_frames) == 9  # 3x3 = 9 帧切片
    finally:
        win.close()


def test_mode_b_pipeline_end_to_end(qapp, video_path, monkeypatch):
    """端到端测试：模式 B (从视频等距均匀抽帧 6 帧 -> 直接导出 GIF)。"""
    win = MainWindow()
    try:
        from src.gifcreater.ui.video_dialog import VideoStillDialog

        def mock_exec(dlg_self):
            dlg_self.result_mode = "sample"
            dlg_self.sampled_frames = dlg_self.reader.sample_evenly(6)
            dlg_self.selected_rows = 2
            dlg_self.selected_cols = 3
            return 1

        monkeypatch.setattr(VideoStillDialog, "exec", mock_exec)

        # 触发导入视频
        win.open_video_dialog(video_path)

        assert win.current_pil_image is None
        assert win.active_frames is not None
        assert len(win.active_frames) == 6
        assert len(win.filmstrip.cards) == 6

        # 模式 B 下直接导出
        win._start_slice_and_export()

        if hasattr(win, "export_worker") and win.export_worker:
            win.export_worker.wait(3000)
        qapp.processEvents()

        assert len(win.active_frames) == 6
    finally:
        win.close()
