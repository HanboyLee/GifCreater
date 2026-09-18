# -*- coding: utf-8 -*-
"""
tests/unit/test_caption.py
表情包文字叠加渲染模块单元测试 (TDD 质量门禁)
"""

import pytest
from PIL import Image
from src.gifcreater.core.caption import (
    draw_caption,
    apply_caption_to_frames,
    _get_font,
)


def _create_test_image(mode="RGBA", size=(200, 200), color=(128, 128, 128, 255)) -> Image.Image:
    """生成微型内存测试图片，杜绝外部图片文件依赖"""
    return Image.new(mode, size, color)


def test_draw_caption_empty_or_none():
    """测试当文本为空或纯空白时，零侵入直接返回原图引用"""
    img = _create_test_image()
    assert draw_caption(img, None) is img
    assert draw_caption(img, "") is img
    assert draw_caption(img, "   \n\t  ") is img


def test_draw_caption_bottom_default():
    """测试默认底部居中绘制配文"""
    img = _create_test_image(mode="RGBA", size=(200, 200), color=(50, 50, 50, 255))
    result = draw_caption(img, "测试配文", position="bottom")

    assert result is not img
    assert result.size == img.size
    # 像素变化校验：配文绘制后字节数据必然发生改变
    assert result.tobytes() != img.tobytes()


def test_draw_caption_top():
    """测试顶部居中绘制配文"""
    img = _create_test_image(mode="RGB", size=(150, 150), color=(200, 200, 200))
    result = draw_caption(img, "顶部标题", position="top", font_size=16)

    assert result.size == (150, 150)
    assert result.tobytes() != img.tobytes()



def test_draw_caption_palette_mode_conversion():
    """测试 P 模式或非 RGBA/RGB 模式自动转换"""
    img = Image.new("P", (100, 100))
    result = draw_caption(img, "调色板图")
    assert result.mode in ("RGB", "RGBA")
    assert result.size == (100, 100)


def test_draw_caption_custom_colors_and_size():
    """测试自定义字号、颜色和描边宽度比例"""
    img = _create_test_image(mode="RGB", size=(300, 300), color=(0, 0, 0))
    result = draw_caption(
        img,
        "自定义高对比",
        position="bottom",
        font_size=28,
        text_color=(255, 255, 0),
        stroke_color=(255, 0, 0),
        stroke_ratio=0.1,
    )
    assert result.size == (300, 300)


def test_apply_caption_to_frames():
    """测试批量帧叠加配文"""
    frames = [_create_test_image(size=(100, 100)) for _ in range(3)]
    captioned = apply_caption_to_frames(frames, "帧序列配文", position="bottom")

    assert len(captioned) == 3
    for f in captioned:
        assert f.size == (100, 100)


def test_apply_caption_to_frames_empty():
    """测试空帧或空文本时的批量函数短路行为"""
    assert apply_caption_to_frames([], "测试") == []
    frames = [_create_test_image()]
    assert apply_caption_to_frames(frames, "") is frames
    assert apply_caption_to_frames(frames, None) is frames


def test_get_font_fallback():
    """测试字体获取机制与边界回退"""
    font = _get_font(20)
    assert font is not None


def test_caption_config_full_transform():
    """测试 CaptionConfig 任意坐标、旋转、透明度与边框定制"""
    from src.gifcreater.core.caption import CaptionConfig

    img = _create_test_image(mode="RGBA", size=(200, 200), color=(30, 30, 30, 255))
    cfg = CaptionConfig(
        text="倾斜动感配文",
        pos_x_ratio=0.4,
        pos_y_ratio=0.6,
        rotation_deg=-15.0,
        font_size=20,
        text_color=(255, 255, 0, 180),   # 半透明黄色
        stroke_color=(0, 0, 0, 255),
        stroke_width=3,
    )
    result = draw_caption(img, cfg)

    assert result.size == (200, 200)
    assert result.tobytes() != img.tobytes()


def test_caption_config_no_stroke():
    """测试 stroke_width=0 无边框纯文字模式"""
    from src.gifcreater.core.caption import CaptionConfig

    img = _create_test_image(mode="RGB", size=(160, 160), color=(0, 0, 0))
    cfg = CaptionConfig(
        text="纯无边框文字",
        pos_x_ratio=0.5,
        pos_y_ratio=0.5,
        rotation_deg=45.0,
        stroke_width=0,
    )
    result = draw_caption(img, cfg)
    assert result.size == (160, 160)
    assert result.tobytes() != img.tobytes()


def test_apply_caption_to_frames_with_config():
    """测试批量帧应用 CaptionConfig"""
    from src.gifcreater.core.caption import CaptionConfig

    frames = [_create_test_image(size=(100, 100)) for _ in range(2)]
    cfg = CaptionConfig(text="批量帧配文", rotation_deg=10.0)
    out = apply_caption_to_frames(frames, cfg)
    assert len(out) == 2

    # 空配置短路
    empty_cfg = CaptionConfig(text="")
    assert apply_caption_to_frames(frames, empty_cfg) is frames


def test_get_font_fallback_when_no_system_fonts(monkeypatch):
    """测试当系统字体均不存在时的默认字体加载与异常回退"""
    import os
    monkeypatch.setattr(os.path, "exists", lambda p: False)
    font = _get_font(24)
    assert font is not None


