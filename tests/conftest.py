# -*- coding: utf-8 -*-
"""
tests/conftest.py
全局 pytest 夹具与环境 Mock 模拟器
"""

import sys
from pathlib import Path
from typing import Generator
import pytest

# 确保 src 目录与项目根目录优先在 sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tests.fixtures.mock_images import (
    create_dummy_grid_image,
    create_border_probe_image,
    create_synthetic_animated_frames,
    create_transparent_frame,
)


@pytest.fixture(scope="session")
def qapp():
    """提供全局单例 QApplication"""
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def dummy_grid_image_2x2():
    """标准 400x400 2x2 包含中心分割线的 RGB 测试图"""
    return create_dummy_grid_image(width=400, height=400, rows=2, cols=2, line_color=(0, 0, 0))


@pytest.fixture
def dummy_grid_image_3x3():
    """标准 300x300 3x3 RGB 测试图"""
    return create_dummy_grid_image(width=300, height=300, rows=3, cols=3, line_color=(0, 0, 0))


@pytest.fixture
def border_black_image():
    """外圈带 10px 纯黑边框的主体图 (200x200)"""
    return create_border_probe_image(
        width=200,
        height=200,
        border_width=10,
        border_color=(0, 0, 0),
        fill_color=(255, 100, 100),
    )


@pytest.fixture
def border_white_image():
    """外圈带 15px 纯白边框的主体图 (200x200)"""
    return create_border_probe_image(
        width=200,
        height=200,
        border_width=15,
        border_color=(255, 255, 255),
        fill_color=(50, 150, 250),
    )


@pytest.fixture
def uniform_color_image():
    """纯色图像 (无主体反差，边界探测保护边缘测试)"""
    return create_border_probe_image(
        width=100,
        height=100,
        border_width=0,
        border_color=(128, 128, 128),
        fill_color=(128, 128, 128),
    )


@pytest.fixture
def animated_frames_8():
    """8 帧常规动画序列 (100x100 RGB 渐变模式)"""
    return create_synthetic_animated_frames(count=8, size=(100, 100), complexity="gradient")


@pytest.fixture
def heavy_animated_frames_20():
    """20 帧高熵复杂噪点图像 (300x300)，用于考验微信压缩自适应收敛"""
    return create_synthetic_animated_frames(count=20, size=(300, 300), complexity="high_entropy")


@pytest.fixture
def transparent_frame_rgba():
    """100x100 带 Alpha 通道的透明图"""
    return create_transparent_frame(width=100, height=100, alpha_bg=0)


@pytest.fixture
def mock_readonly_fs(monkeypatch) -> Generator[None, None, None]:
    """
    Mock 只读文件系统环境：
    精准拦截对 output/.perm_test 的写操作，模拟 PermissionError，
    验证 paths.py 的安全静默降级机制。
    """
    real_open = open

    def guarded_open(file, *args, **kwargs):
        file_str = str(file)
        if ".perm_test" in file_str:
            raise PermissionError("Mock Read-Only Filesystem: Permission denied")
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)
    yield
