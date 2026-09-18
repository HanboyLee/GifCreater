# -*- coding: utf-8 -*-
"""
tests/unit/test_bounds.py
单元测试: bounds.py (智能边界探测引擎)
"""

from PIL import Image
from src.gifcreater.core.bounds import detect_bounds
from tests.fixtures.mock_images import create_border_probe_image, create_transparent_frame


def test_detect_bounds_black_border(border_black_image):
    """验证纯黑边框主体包围盒探测"""
    left, top, right, bottom = detect_bounds(border_black_image, tolerance=15)
    assert 8 <= left <= 11
    assert 8 <= top <= 11
    assert 189 <= right <= 192
    assert 189 <= bottom <= 192


def test_detect_bounds_white_border(border_white_image):
    """验证纯白边框主体包围盒探测"""
    left, top, right, bottom = detect_bounds(border_white_image, tolerance=15)
    assert 13 <= left <= 16
    assert 13 <= top <= 16
    assert 184 <= right <= 187
    assert 184 <= bottom <= 187


def test_detect_bounds_asymmetric_padding():
    """验证非对称 Padding 边框探测"""
    im = create_border_probe_image(
        width=200,
        height=200,
        padding_asymmetric=(5, 20, 15, 30),
        border_color=(0, 0, 0),
        fill_color=(200, 50, 50),
    )
    left, top, right, bottom = detect_bounds(im, tolerance=15)
    assert 4 <= left <= 6
    assert 19 <= top <= 21
    assert 184 <= right <= 186
    assert 169 <= bottom <= 171


def test_detect_bounds_uniform_color_fallback(uniform_color_image):
    """验证纯色无主体图像回退至全图完整尺寸 (0, 0, w, h)"""
    w, h = uniform_color_image.size
    left, top, right, bottom = detect_bounds(uniform_color_image, tolerance=15)
    assert (left, top, right, bottom) == (0, 0, w, h)


def test_detect_bounds_tolerance_noise():
    """验证容差参数抗噪性"""
    im = create_border_probe_image(
        width=100,
        height=100,
        border_width=10,
        border_color=(20, 20, 20),
        fill_color=(100, 100, 100),
    )
    left, top, right, bottom = detect_bounds(im, tolerance=25)
    assert 9 <= left <= 11
    assert 9 <= top <= 11


def test_detect_bounds_rgba_transparent():
    """验证带透明通道 RGBA 图像的包围盒探测"""
    im = create_transparent_frame(width=100, height=100, alpha_bg=0, shape_rect=(20, 20, 80, 80))
    left, top, right, bottom = detect_bounds(im, tolerance=15)
    assert 18 <= left <= 21
    assert 18 <= top <= 21
    assert 79 <= right <= 82
    assert 79 <= bottom <= 82


def test_detect_bounds_empty_dimensions():
    """验证零尺寸或极小尺寸安全防御"""
    im_empty = Image.new("RGB", (0, 0))
    assert detect_bounds(im_empty) == (0, 0, 0, 0)


def test_detect_bounds_tiny_subject_noise_fallback():
    """验证极小噪点 (<10% 面积) 回退为全图"""
    # 200x200 图像，主体只有 4x4 像素 (< 10%)
    im = Image.new("RGB", (200, 200), (0, 0, 0))
    im.putpixel((100, 100), (255, 255, 255))
    im.putpixel((101, 100), (255, 255, 255))
    im.putpixel((100, 101), (255, 255, 255))
    im.putpixel((101, 101), (255, 255, 255))
    assert detect_bounds(im) == (0, 0, 200, 200)
