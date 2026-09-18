# -*- coding: utf-8 -*-
"""
src/gifcreater/utils/paths.py
系统路径管理与权限防御降级 (零 GUI 依赖)
"""

import os
import sys
from typing import Optional


def get_base_dir() -> str:
    """
    获取应用程序基准根目录。
    兼容 PyInstaller 打包后的 sys.frozen 冻结环境。
    - 打包运行模式：返回可执行文件所在目录
    - 源码开发模式：从 src/gifcreater/utils/ 向上回溯 3 级定位工程根目录
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))

    cur_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(cur_dir, "..", "..", ".."))


def get_default_output_dir(subfolder: Optional[str] = None) -> str:
    """
    获取默认输出目录，内置只读权限安全降级机制：
    1. 优先尝试 base_dir/output；
    2. 创建临时测试文件验证写权限；
    3. 若无写权限 (如位于 C:\\Program Files)，自动静默降级至 %USERPROFILE%\\Pictures\\GifCreater\\output；
    4. 若指定 subfolder (如 'gifs' 或 'frames')，自动连接子目录并确保创建。
    """
    base = get_base_dir()
    candidate = os.path.join(base, "output")
    target_dir = candidate

    try:
        os.makedirs(candidate, exist_ok=True)
        test_file = os.path.join(candidate, ".perm_test")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("ok")
        if os.path.exists(test_file):
            os.remove(test_file)
        target_dir = candidate
    except Exception:
        fallback = os.path.join(os.path.expanduser("~"), "Pictures", "GifCreater", "output")
        os.makedirs(fallback, exist_ok=True)
        target_dir = fallback

    if subfolder:
        final_dir = os.path.join(target_dir, subfolder)
        os.makedirs(final_dir, exist_ok=True)
        return final_dir

    return target_dir


def get_gifs_output_dir() -> str:
    """获取动图输出归档目录 output/gifs/"""
    return get_default_output_dir("gifs")


def get_frames_output_dir(base_name: Optional[str] = None) -> str:
    """获取过程帧输出归档目录 output/frames/[base_name_frames/]"""
    sub = f"frames/{base_name}_frames" if base_name else "frames"
    return get_default_output_dir(sub)


def get_default_output_dirs():
    """获取 (gifs_dir, frames_dir) 的 Path 对象元组"""
    from pathlib import Path
    return Path(get_gifs_output_dir()), Path(get_frames_output_dir())

