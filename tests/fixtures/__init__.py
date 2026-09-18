# -*- coding: utf-8 -*-
"""
tests/fixtures
测试固件与微型动态图像构造包 (Zero-Disk-Media)
"""

from .mock_images import (
    create_dummy_grid_image,
    create_border_probe_image,
    create_synthetic_animated_frames,
    create_transparent_frame,
)

__all__ = [
    "create_dummy_grid_image",
    "create_border_probe_image",
    "create_synthetic_animated_frames",
    "create_transparent_frame",
]
