# -*- coding: utf-8 -*-
"""
GifCreater 通用系统工具包 (Utilities)
====================================

跨平台文件 I/O 与安全路径解析工具：
- paths: 安全路径推导、PyInstaller 打包冻结适配与只读目录安全降级
"""

__version__ = "3.0.0"

from .paths import (
    get_base_dir,
    get_default_output_dir,
    get_gifs_output_dir,
    get_frames_output_dir,
)

__all__ = [
    "get_base_dir",
    "get_default_output_dir",
    "get_gifs_output_dir",
    "get_frames_output_dir",
]
