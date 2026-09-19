# -*- coding: utf-8 -*-
"""
tests/unit/test_compressor.py
单元测试: compressor.py (微信表情包自适应压缩引擎)
"""

import io
import pytest
from PIL import Image, ImageSequence
from src.gifcreater.core.compressor import compress_wechat_gif
from tests.fixtures.mock_images import create_synthetic_animated_frames, create_transparent_frame

MAX_WECHAT_BYTES = 500 * 1024  # 512,000 字节
MAX_WECHAT_SIDE = 240          # 240 像素


def test_compress_wechat_gif_hard_limits(animated_frames_8):
    """
    【硬性门禁测试】
    1. 字节大小严格 <= 512,000 字节；
    2. 图像最长边严格 <= 240 像素。
    """
    durations = [150] * len(animated_frames_8)
    gif_bytes = compress_wechat_gif(animated_frames_8, durations)

    assert isinstance(gif_bytes, bytes)
    assert len(gif_bytes) > 0
    assert len(gif_bytes) <= MAX_WECHAT_BYTES, f"微信表情包超出 500KB 硬指标: {len(gif_bytes)} 字节"

    with Image.open(io.BytesIO(gif_bytes)) as im:
        assert im.format == "GIF"
        w, h = im.size
        assert max(w, h) <= MAX_WECHAT_SIDE, f"微信表情包最长边超出 240px: {max(w, h)}"
        frames = [frame.copy() for frame in ImageSequence.Iterator(im)]
        assert len(frames) >= 2


def test_compress_wechat_gif_proportional_resize():
    """验证不同宽高比图像的长边等比缩放至 240px"""
    # 1. 横屏图 800x400 -> 期望 240x120
    wide_frames = [Image.new("RGB", (800, 400), (i * 20, 100, 100)) for i in range(4)]
    res_bytes = compress_wechat_gif(wide_frames, [100] * 4)
    with Image.open(io.BytesIO(res_bytes)) as im:
        assert im.size == (240, 120)

    # 2. 竖屏图 300x600 -> 期望 120x240
    tall_frames = [Image.new("RGB", (300, 600), (100, i * 20, 100)) for i in range(4)]
    res_tall = compress_wechat_gif(tall_frames, [100] * 4)
    with Image.open(io.BytesIO(res_tall)) as im:
        assert im.size == (120, 240)


def test_compress_wechat_gif_duration_fidelity():
    """验证微信模式下帧间隔保真、尾帧停顿与 GIF89a 10ms 量化规范"""
    frames = [Image.new("RGB", (100, 100), (i * 30, 50, 50)) for i in range(4)]

    # 1. 验证长延时与尾帧长停顿保真 (350ms, 1500ms 不再被强行截断为 120ms)
    durations = [350, 350, 350, 1500]
    gif_bytes = compress_wechat_gif(frames, durations)
    with Image.open(io.BytesIO(gif_bytes)) as im:
        frame_durations = [frame.info.get("duration", 0) for frame in ImageSequence.Iterator(im)]
        assert frame_durations == [350, 350, 350, 1500]

    # 2. 验证单一整数延时广播
    gif_single = compress_wechat_gif(frames, 400)
    with Image.open(io.BytesIO(gif_single)) as im:
        frame_durations = [frame.info.get("duration", 0) for frame in ImageSequence.Iterator(im)]
        assert frame_durations == [400, 400, 400, 400]

    # 3. 验证默认延时 (None -> 100ms)
    gif_default = compress_wechat_gif(frames, None)
    with Image.open(io.BytesIO(gif_default)) as im:
        frame_durations = [frame.info.get("duration", 0) for frame in ImageSequence.Iterator(im)]
        assert frame_durations == [100, 100, 100, 100]

    # 4. 验证 GIF89a 10ms 颗粒度量化与下限 20ms 保护
    gif_quant = compress_wechat_gif(frames, [35, 12, 504, 506])
    with Image.open(io.BytesIO(gif_quant)) as im:
        frame_durations = [frame.info.get("duration", 0) for frame in ImageSequence.Iterator(im)]
        assert frame_durations == [40, 20, 500, 510]


def test_compress_wechat_gif_extreme_entropy_stress(heavy_animated_frames_20):
    """
    【极端压力测试】
    20 帧 300x300 高噪点素材，普通 GIF 会达到 1~2MB。
    考验阶梯降级 (128->96->64->48->32) 及多级兜底能力，
    硬性断言：绝对不能超出 512,000 字节！
    """
    durations = [100] * len(heavy_animated_frames_20)
    gif_bytes = compress_wechat_gif(heavy_animated_frames_20, durations)

    assert len(gif_bytes) <= MAX_WECHAT_BYTES, f"极端素材压缩失败，超出体积上限: {len(gif_bytes)} 字节"
    with Image.open(io.BytesIO(gif_bytes)) as im:
        assert max(im.size) <= MAX_WECHAT_SIDE


def test_compress_wechat_gif_fallback_tiers():
    """
    测试极端严格体积限制 (如 10 字节)，
    全面触发 Tier 1 (隔帧抽取), Tier 2 (几何降采样), Tier 3 (深度调色板 16/8/4/2), Tier 4 (单帧保底) 及最终退出
    """
    frames = [Image.new("RGB", (10, 10), (i * 40, 50, 50)) for i in range(4)]
    res = compress_wechat_gif(frames, max_size_bytes=10)
    assert len(res) > 0
    with Image.open(io.BytesIO(res)) as im:
        assert im.format == "GIF"


def test_compress_wechat_gif_small_image_no_upscale():
    """验证原本尺寸小于 240px 的图片不被放大"""
    small_frames = [Image.new("RGB", (100, 80), (i * 20, 60, 60)) for i in range(3)]
    res = compress_wechat_gif(small_frames, 100)
    with Image.open(io.BytesIO(res)) as im:
        assert im.size == (100, 80)


def test_compress_wechat_gif_mode_conversions():
    """验证灰度 L 模式与调色板 P 模式转换"""
    gray_frames = [Image.new("L", (80, 80), 50 * i) for i in range(3)]
    res_l = compress_wechat_gif(gray_frames, 100)
    assert len(res_l) > 0

    p_frames = [im.convert("P") for im in gray_frames]
    res_p = compress_wechat_gif(p_frames, 100)
    assert len(res_p) > 0


def test_compress_wechat_gif_rgba_input():
    """验证 RGBA 带透明通道图片输入及透明通道保留"""
    rgba_frames = [
        create_transparent_frame(width=100, height=100, shape_color=(200, i * 40, 50, 255))
        for i in range(3)
    ]
    res = compress_wechat_gif(rgba_frames, 100)
    assert len(res) <= MAX_WECHAT_BYTES
    with Image.open(io.BytesIO(res)) as im:
        assert im.format == "GIF"
        # 验证透明度索引与背景透明保留
        assert im.info.get("transparency") is not None
        assert im.convert("RGBA").getpixel((0, 0))[3] == 0
        assert im.convert("RGBA").getpixel((50, 50))[3] == 255
        # 验证 disposal=2 帧刷新模式
        for f in ImageSequence.Iterator(im):
            assert f.disposal_method == 2


def test_compress_wechat_gif_durations_variants():
    """验证 durations 传入 None、int、过长/过短列表等分支"""
    frames = [Image.new("RGB", (80, 80), (i * 40, 50, 50)) for i in range(4)]

    # 1. durations is None
    res1 = compress_wechat_gif(frames, durations=None)
    assert len(res1) > 0

    # 2. durations is int
    res2 = compress_wechat_gif(frames, durations=200)
    assert len(res2) > 0

    # 3. durations 过长
    res3 = compress_wechat_gif(frames, durations=[100, 100, 100, 100, 100, 100])
    assert len(res3) > 0

    # 4. durations 过短
    res4 = compress_wechat_gif(frames, durations=[100])
    assert len(res4) > 0


def test_compress_wechat_gif_errors():
    """验证输入异常抛出 ValueError"""
    with pytest.raises(ValueError, match="frames list cannot be empty"):
        compress_wechat_gif([], [])

    frames = [Image.new("RGB", (50, 50))]
    with pytest.raises(ValueError, match="max_size_bytes must be positive"):
        compress_wechat_gif(frames, max_size_bytes=0)

    with pytest.raises(ValueError, match="max_side must be positive"):
        compress_wechat_gif(frames, max_side=-1)

    bad_dim_frames = [Image.new("RGB", (0, 50))]
    with pytest.raises(ValueError, match="Invalid frame dimensions"):
        compress_wechat_gif(bad_dim_frames)
