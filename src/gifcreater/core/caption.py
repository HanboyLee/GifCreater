"""表情包配文文字叠加模块 (Caption Text Overlay)

提供纯无头、高对比度黑边白字的表情包配文渲染能力。
支持零侵入回退、系统字体自动定位、字号自适应与上下位置对齐。
"""

import os
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont


# 常见 Windows 中文字体候选路径
_FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",     # 微软雅黑
    "C:/Windows/Fonts/msyhbd.ttc",   # 微软雅黑粗体
    "C:/Windows/Fonts/simhei.ttf",   # 黑体
    "C:/Windows/Fonts/simsun.ttc",   # 宋体
    "/System/Library/Fonts/PingFang.ttc",  # macOS 苹方
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
]


def _get_font(font_size: int) -> ImageFont.ImageFont:
    """获取可用字体，优先加载系统无衬线中文字体，失败时回退至 Pillow 默认字体。"""
    for font_path in _FONT_CANDIDATES:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, font_size)
            except Exception:
                continue
    try:
        return ImageFont.load_default(size=font_size)
    except Exception:
        return ImageFont.load_default()


def draw_caption(
    image: Image.Image,
    text: Optional[str],
    position: str = "bottom",
    font_size: Optional[int] = None,
    text_color: Tuple[int, int, int] = (255, 255, 255),
    stroke_color: Tuple[int, int, int] = (0, 0, 0),
    stroke_ratio: float = 0.08,
) -> Image.Image:
    """在单张图像上绘制高对比度黑边白字配文。

    Args:
        image: PIL 图像对象
        text: 配文字符串，若为空或纯空白则不修改直接返回
        position: 文字位置，'bottom' (底部居中) 或 'top' (顶部居中)
        font_size: 字体大小（像素），未指定时按画面短边 11% 自动计算
        text_color: 文字主体颜色，默认纯白 (255, 255, 255)
        stroke_color: 描边轮廓颜色，默认纯黑 (0, 0, 0)
        stroke_ratio: 描边宽度占字号的比例，默认 0.08 (约 8%)

    Returns:
        渲染配文后的 PIL Image 副本；若 text 为空则返回原 image
    """
    if not text or not text.strip():
        return image

    text = text.strip()
    w, h = image.size

    # 计算自适应字号
    if font_size is None or font_size <= 0:
        base_dim = min(w, h)
        font_size = max(14, min(72, int(base_dim * 0.11)))

    stroke_px = max(1, int(font_size * stroke_ratio))
    font = _get_font(font_size)

    # 复制并确保模式兼容
    out_img = image.copy()
    if out_img.mode not in ("RGB", "RGBA"):
        out_img = out_img.convert("RGBA" if "A" in image.mode else "RGB")

    draw = ImageDraw.Draw(out_img)

    # 计算文字边界框
    bbox = font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # 水平居中
    x = max(2, (w - text_w) // 2)

    # 垂直位置计算
    safe_margin = max(4, int(h * 0.04))
    if position == "top":
        y = safe_margin
    else:  # 默认 bottom
        y = max(2, h - text_h - safe_margin - bbox[1])

    # 渲染描边与文字
    draw.text(
        (x, y),
        text,
        font=font,
        fill=text_color,
        stroke_width=stroke_px,
        stroke_fill=stroke_color,
    )

    return out_img


def apply_caption_to_frames(
    frames: list[Image.Image],
    text: Optional[str],
    position: str = "bottom",
    font_size: Optional[int] = None,
) -> list[Image.Image]:
    """批量为帧序列叠加配文。

    Args:
        frames: PIL Image 列表
        text: 配文字符串，若为空则直接返回原序列
        position: 文字位置 ('bottom' 或 'top')
        font_size: 可选字号

    Returns:
        包含配文的新帧列表
    """
    if not text or not text.strip() or not frames:
        return frames

    return [draw_caption(frame, text, position=position, font_size=font_size) for frame in frames]
