# -*- coding: utf-8 -*-
"""
tests/unit/test_exporter.py
单元测试: exporter.py (动图封装与序列展开引擎)
"""

import io
from pathlib import Path
import pytest
from PIL import Image, ImageSequence
from src.gifcreater.core.exporter import (
    export_gif,
    export_webp,
    save_to_disk,
    create_animation,
    create_gif,
    natural_sort_key,
    generate_boomerang_sequence,
)
from tests.fixtures.mock_images import create_synthetic_animated_frames, create_transparent_frame


def test_natural_sort_key():
    """验证自然数语义排序逻辑"""
    items = ["frame_10.png", "frame_2.png", "frame_1.png", "frame_20.png"]
    sorted_items = sorted(items, key=natural_sort_key)
    assert sorted_items == ["frame_1.png", "frame_2.png", "frame_10.png", "frame_20.png"]


def test_generate_boomerang_sequence_none_durations():
    """验证 generate_boomerang_sequence durations 为 None 分支"""
    frames = [Image.new("RGB", (30, 30)) for _ in range(4)]
    exp_f, exp_d = generate_boomerang_sequence(frames, None)
    assert len(exp_f) == 6
    assert len(exp_d) == 6
    assert exp_d == [100] * 6


def test_export_gif_normal_and_magic_bytes(animated_frames_8):
    """验证标准 GIF 导出与 GIF89a/GIF87a 文件头魔数"""
    durations = [100] * len(animated_frames_8)
    data = export_gif(animated_frames_8, durations, loop=0, boomerang=False)

    assert isinstance(data, bytes)
    assert data.startswith(b"GIF89a") or data.startswith(b"GIF87a")

    with Image.open(io.BytesIO(data)) as im:
        frames = [f.copy() for f in ImageSequence.Iterator(im)]
        assert len(frames) == len(animated_frames_8)

    # 验证 output_path 传入 int (loop 容错)
    data_int = export_gif(animated_frames_8, durations, 0)
    assert isinstance(data_int, bytes)


def test_export_gif_disk_path(tmp_path, animated_frames_8):
    """验证 export_gif 传入 output_path 写出文件"""
    out_file = tmp_path / "subdir" / "test.gif"
    res = export_gif(animated_frames_8, [100] * len(animated_frames_8), output_path=str(out_file))
    assert Path(res).exists()


def test_export_gif_boomerang_expansion():
    """验证 Boomerang 乒乓往复展开序列 (A, B, C, D -> A, B, C, D, C, B)"""
    frames = [Image.new("RGB", (50, 50), (i * 50, 0, 0)) for i in range(4)]
    durations = [100] * 4

    # 1. 帧数 > 2 触发展开 (4 -> 6)
    data_boom = export_gif(frames, durations, boomerang=True)
    with Image.open(io.BytesIO(data_boom)) as im:
        frames_boom = [f.copy() for f in ImageSequence.Iterator(im)]
        assert len(frames_boom) == 6

    # 2. 帧数 <= 2 不触发展开
    short_frames = frames[:2]
    data_short = export_gif(short_frames, [100, 100], boomerang=True)
    with Image.open(io.BytesIO(data_short)) as im:
        frames_short = [f.copy() for f in ImageSequence.Iterator(im)]
        assert len(frames_short) == 2


def test_export_gif_transparent_background():
    """验证 export_gif 对透明 RGBA 帧的透明度保留与半透明边缘净化"""
    frames = [
        create_transparent_frame(width=60, height=60, shape_color=(200, i * 50, 0, 255))
        for i in range(3)
    ]
    # 在第 1 帧边缘添加半透明微弱杂色
    frames[0].putpixel((10, 10), (200, 0, 0, 40))  # 应当被二值化清洗为透明
    frames[0].putpixel((20, 20), (200, 0, 0, 180)) # 应当被保留为不透明

    data = export_gif(frames, [100] * 3)
    with Image.open(io.BytesIO(data)) as im:
        assert im.info.get("transparency") is not None
        # 验证背景透明
        rgba_f0 = im.convert("RGBA")
        assert rgba_f0.getpixel((0, 0))[3] == 0
        # 验证微弱半透明 (alpha=40) 被二值化为透明，消除杂色黑圈
        assert rgba_f0.getpixel((10, 10))[3] == 0
        # 验证主体 (alpha=180) 保留为不透明
        assert rgba_f0.getpixel((20, 20))[3] == 255
        # 验证 disposal=2 属性
        for f in ImageSequence.Iterator(im):
            assert f.disposal_method == 2


def test_export_webp_magic_bytes_and_alpha(tmp_path):
    """验证 WebP 动图导出、RIFF 文件头魔数及透明度保留"""
    frames = [create_transparent_frame(width=60, height=60, shape_color=(200, i * 50, 0, 255)) for i in range(3)]
    durations = [120] * 3

    # 内存导出
    webp_data = export_webp(frames, durations, boomerang=False)
    assert isinstance(webp_data, bytes)
    assert webp_data[:4] == b"RIFF"
    assert webp_data[8:12] == b"WEBP"

    # 文件导出
    out_file = tmp_path / "test.webp"
    res = export_webp(frames, durations, output_path=str(out_file))
    assert Path(res).exists()

    # loop 容错与 boomerang 分支
    webp_boom = export_webp(frames, durations, 0, boomerang=True)
    assert isinstance(webp_boom, bytes)


def test_save_to_disk(tmp_path):
    """验证 save_to_disk 自动创建多级目录与写入数据"""
    target = tmp_path / "deep" / "nested" / "anim.gif"
    sample_data = b"GIF89a_fake_data"
    saved_path = save_to_disk(sample_data, target)

    assert Path(saved_path).exists()
    assert Path(saved_path).read_bytes() == sample_data


def test_create_animation_wrapper_types_and_presets(tmp_path):
    """验证 create_animation 对文件列表、目录输入及各种预设的支持"""
    frame_paths = []
    for i in range(3):
        p = tmp_path / f"frame_{i:02d}.png"
        Image.new("RGB", (60, 60), (i * 70, 50, 50)).save(p)
        frame_paths.append(str(p))

    # 1. 列表传入导出 GIF
    out_gif = tmp_path / "out.gif"
    res1 = create_animation(frame_paths, str(out_gif), preset="original")
    assert Path(res1).exists()

    # 2. 目录传入导出 WebP
    out_webp = tmp_path / "out.webp"
    res2 = create_animation(str(tmp_path), str(out_webp), preset="webp")
    assert Path(res2).exists()

    # 3. 微信预设 + boomerang
    out_wc = tmp_path / "wechat.gif"
    res3 = create_animation(frame_paths, str(out_wc), preset="wechat", boomerang=True, last_frame_pause=1500)
    assert Path(res3).exists()

    # 4. create_gif 快捷函数 (含 wechat_mode)
    out_cg = tmp_path / "cg.gif"
    res4 = create_gif(frame_paths, str(out_cg), wechat_mode=True)
    assert Path(res4).exists()

    # 5. Image.Image 列表传入
    img_objs = [Image.open(p) for p in frame_paths]
    out_mem = tmp_path / "mem.gif"
    res5 = create_animation(img_objs, str(out_mem))
    assert Path(res5).exists()


def test_create_animation_errors(tmp_path):
    """验证参数类型异常与空数据异常"""
    with pytest.raises(TypeError):
        create_animation(12345, str(tmp_path / "out.gif"))

    with pytest.raises(ValueError):
        create_animation([], str(tmp_path / "out.gif"))

    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    with pytest.raises(ValueError):
        create_animation(str(empty_dir), str(tmp_path / "out.gif"))


def test_export_empty_frames_errors():
    """验证空帧列表导出抛出 ValueError"""
    with pytest.raises(ValueError, match="帧列表为空"):
        export_gif([], [100])

    with pytest.raises(ValueError, match="帧列表为空"):
        export_webp([], [100])


def test_export_gif_with_caption():
    """验证 export_gif 叠加表情包文字"""
    frames = [Image.new("RGB", (80, 80), (100, 100, 100)) for _ in range(3)]
    durations = [100] * 3
    data = export_gif(frames, durations, caption_text="测试表情包配文", caption_pos="bottom")
    assert isinstance(data, bytes)
    assert data.startswith(b"GIF89a") or data.startswith(b"GIF87a")


def test_export_webp_with_caption():
    """验证 export_webp 叠加顶部文字"""
    frames = [Image.new("RGBA", (100, 100), (0, 0, 0, 255)) for _ in range(2)]
    durations = [150, 150]
    data = export_webp(frames, durations, caption_text="顶部配文", caption_pos="top")
    assert isinstance(data, bytes)
    assert data[:4] == b"RIFF"


def test_create_animation_xiaohongshu_and_caption(tmp_path):
    """验证 xiaohongshu 预设与配文一体化导出"""
    frames = [Image.new("RGB", (1200, 1600), (50, 100, 150)) for _ in range(2)]
    out_file = tmp_path / "xhs.gif"
    res = create_animation(
        frames,
        str(out_file),
        preset="xiaohongshu",
        caption_text="小红书爆款动图",
        caption_pos="bottom",
    )
    assert Path(res).exists()
    with Image.open(res) as im:
        # 尺寸应被限缩到 1080px 最长边
        assert max(im.size) <= 1080

