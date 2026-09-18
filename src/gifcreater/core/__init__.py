# -*- coding: utf-8 -*-
"""
GifCreater 核心算法引擎 (Core Engine Layer)
===========================================

纯无头算法模块，零 GUI 依赖，接受纯内存图像计算：
- slicer: 网格切片计算、特征分割线探测、多格图像拆分
- bounds: 智能背景色采样与主体包围盒探测
- compressor: 微信表情包自适应阶梯调色板压缩 (<=500KB, <=240px)
- exporter: 原画 GIF / 全彩 WebP 封装与 Boomerang 往复序列展开
"""

__version__ = "3.0.0"

from .slicer import (
    GridConfig,
    calculate_default_grid,
    detect_dividers_universal,
    get_grid_divider_coords,
    get_aspect_ratio_info,
    slice_image,
    split_grid_image,
)
from .bounds import (
    detect_bounds,
)
from .compressor import (
    compress_wechat_gif,
)
from .exporter import (
    export_gif,
    export_webp,
    save_to_disk,
    create_animation,
    create_gif,
    process_image_to_gif,
    natural_sort_key,
)
from .caption import (
    CaptionConfig,
    draw_caption,
    apply_caption_to_frames,
)

__all__ = [
    "GridConfig",
    "CaptionConfig",
    "calculate_default_grid",
    "detect_dividers_universal",
    "get_grid_divider_coords",
    "get_aspect_ratio_info",
    "slice_image",
    "split_grid_image",
    "detect_bounds",
    "compress_wechat_gif",
    "export_gif",
    "export_webp",
    "save_to_disk",
    "create_animation",
    "create_gif",
    "process_image_to_gif",
    "natural_sort_key",
    "draw_caption",
    "apply_caption_to_frames",
]


