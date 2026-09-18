# -*- coding: utf-8 -*-
"""
tests/unit/test_paths.py
单元测试: paths.py (跨平台安全路径与权限降级)
"""

import os
import sys
from src.gifcreater.utils.paths import (
    get_base_dir,
    get_default_output_dir,
    get_gifs_output_dir,
    get_frames_output_dir,
)


def test_get_base_dir_normal_and_frozen(monkeypatch, tmp_path):
    """验证正常路径与 PyInstaller 冻结态路径"""
    base = get_base_dir()
    assert os.path.exists(base)

    # 模拟 sys.frozen
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "bin" / "app.exe"))
    frozen_base = get_base_dir()
    assert frozen_base == str(tmp_path / "bin")


def test_get_default_output_dir_normal():
    """验证正常环境下 output 目录推导与创建"""
    out_dir = get_default_output_dir()
    assert os.path.exists(out_dir)


def test_get_default_output_dir_readonly_fallback(mock_readonly_fs):
    """
    【关键安全测试】
    模拟只读环境（如运行在 C:\\Program Files\\），
    验证安全静默降级至 %USERPROFILE%\\Pictures\\GifCreater\\output，
    绝不向用户抛出 PermissionError！
    """
    fallback_dir = get_default_output_dir()
    assert fallback_dir is not None
    expected_part = os.path.join("Pictures", "GifCreater", "output")
    assert expected_part.lower() in fallback_dir.lower()
    assert os.path.exists(fallback_dir)


def test_get_sub_output_dirs():
    """验证 gifs 与 frames 子归档目录生成"""
    gifs_dir = get_gifs_output_dir()
    assert os.path.exists(gifs_dir)
    assert gifs_dir.endswith("gifs")

    frames_dir = get_frames_output_dir("test_subject")
    assert os.path.exists(frames_dir)
    assert "test_subject_frames" in frames_dir

    frames_dir_default = get_frames_output_dir()
    assert os.path.exists(frames_dir_default)
    assert frames_dir_default.endswith("frames")
