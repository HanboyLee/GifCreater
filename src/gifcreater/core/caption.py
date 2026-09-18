"""表情包配文文字叠加模块 (Caption Text Overlay & Transform)

提供纯无头、高对比度、支持自由坐标、任意角度旋转、全透明度与边框定制的表情包配文引擎。
支持零侵入回退、系统字体自动定位、字号自适应与双三次插值抗锯齿旋转。
"""

import os
from dataclasses import dataclass
from typing import Optional, Tuple, Union
from PIL import Image, ImageDraw, ImageFont


# 常见 Windows/跨平台中文字体候选路径
_FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",     # 微软雅黑
    "C:/Windows/Fonts/msyhbd.ttc",   # 微软雅黑粗体
    "C:/Windows/Fonts/simhei.ttf",   # 黑体
    "C:/Windows/Fonts/simsun.ttc",   # 宋体
    "/System/Library/Fonts/PingFang.ttc",  # macOS 苹方
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
]


@dataclass
class CaptionConfig:
    """表情包配文与变换配置数据类"""
    text: str = ""
    pos_x_ratio: float = 0.5       # 相对水平中心 (0.0~1.0, 0.5 为正居中)
    pos_y_ratio: float = 0.88      # 相对垂直中心 (0.0~1.0, 0.88 为底部偏下, 0.12 为顶部)
    rotation_deg: float = 0.0      # 旋转度数 (-180.0 ~ 180.0)
    font_size: Optional[int] = None
    text_color: Tuple[int, ...] = (255, 255, 255, 255)      # RGBA (0~255)
    stroke_color: Tuple[int, ...] = (0, 0, 0, 255)          # RGBA (0~255)
    stroke_width: int = 2                                   # 描边粗细 (px, 0 为不描边)


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


def _ensure_rgba_tuple(c: Tuple[int, ...], default_alpha: int = 255) -> Tuple[int, int, int, int]:
    """确保颜色为 (R, G, B, A) 4 元组"""
    if len(c) >= 4:
        return (c[0], c[1], c[2], c[3])
    elif len(c) == 3:
        return (c[0], c[1], c[2], default_alpha)
    return (255, 255, 255, default_alpha)


def draw_caption(
    image: Image.Image,
    config_or_text: Union[CaptionConfig, str, None],
    position: str = "bottom",
    font_size: Optional[int] = None,
    text_color: Tuple[int, ...] = (255, 255, 255, 255),
    stroke_color: Tuple[int, ...] = (0, 0, 0, 255),
    stroke_width: Optional[int] = None,
    stroke_ratio: float = 0.08,
    rotation_deg: float = 0.0,
    pos_x_ratio: Optional[float] = None,
    pos_y_ratio: Optional[float] = None,
) -> Image.Image:
    """在单张图像上绘制支持自由坐标、旋转与透明度的表情包配文。

    Args:
        image: PIL 图像对象
        config_or_text: CaptionConfig 对象或纯文本字符串。为空则直接返回原图引用。
        position: 快捷位置 ('bottom' 或 'top')，仅在 config_or_text 为字符串且未提供 ratio 时生效
        font_size: 字体大小（像素），未指定时按画面短边 11% 自动计算
        text_color: 文字主体颜色 (RGBA)
        stroke_color: 描边轮廓颜色 (RGBA)
        stroke_width: 描边粗细 (px)，为 0 则不描边
        stroke_ratio: 描边占字号比例 (用于缺省计算)
        rotation_deg: 旋转角度 (-180° ~ 180°)
        pos_x_ratio: 相对水平中心 (0.0~1.0)
        pos_y_ratio: 相对垂直中心 (0.0~1.0)

    Returns:
        渲染配文后的 PIL Image 副本；若文字为空则直接返回原 image 引用
    """
    if config_or_text is None:
        return image

    if isinstance(config_or_text, CaptionConfig):
        cfg = config_or_text
    else:
        text_str = str(config_or_text)
        if not text_str.strip():
            return image
        
        # 解析默认 y 坐标
        if pos_y_ratio is None:
            default_y = 0.12 if position == "top" else 0.88
        else:
            default_y = pos_y_ratio

        default_x = 0.5 if pos_x_ratio is None else pos_x_ratio

        cfg = CaptionConfig(
            text=text_str,
            pos_x_ratio=default_x,
            pos_y_ratio=default_y,
            rotation_deg=rotation_deg,
            font_size=font_size,
            text_color=text_color,
            stroke_color=stroke_color,
            stroke_width=2 if stroke_width is None else stroke_width,
        )

    text = cfg.text.strip() if cfg.text else ""
    if not text:
        return image

    w, h = image.size

    # 计算自适应字号
    curr_font_size = cfg.font_size
    if curr_font_size is None or curr_font_size <= 0:
        base_dim = min(w, h)
        curr_font_size = max(14, min(72, int(base_dim * 0.11)))

    # 计算描边像素
    if cfg.stroke_width is not None and cfg.stroke_width >= 0:
        stroke_px = cfg.stroke_width
    else:
        stroke_px = max(1, int(curr_font_size * stroke_ratio))

    font = _get_font(curr_font_size)
    rgba_text = _ensure_rgba_tuple(cfg.text_color)
    rgba_stroke = _ensure_rgba_tuple(cfg.stroke_color)

    # 计算文本边界框
    bbox = font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # 在独立的透明图层上绘制单行文本（预留描边与抗锯齿边距）
    pad = stroke_px + 8
    layer_w = max(1, text_w + pad * 2)
    layer_h = max(1, text_h + pad * 2)

    text_layer = Image.new("RGBA", (layer_w, layer_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)

    draw_x = pad - bbox[0]
    draw_y = pad - bbox[1]

    draw.text(
        (draw_x, draw_y),
        text,
        font=font,
        fill=rgba_text,
        stroke_width=stroke_px,
        stroke_fill=rgba_stroke if stroke_px > 0 else None,
    )

    # 双三次插值旋转
    if abs(cfg.rotation_deg) > 0.01:
        # Pillow rotate 以逆时针为正，符合直觉
        rotated_layer = text_layer.rotate(
            cfg.rotation_deg,
            resample=Image.Resampling.BICUBIC,
            expand=True,
        )
    else:
        rotated_layer = text_layer

    # 计算目标中心点与粘贴左上角
    target_cx = int(w * cfg.pos_x_ratio)
    target_cy = int(h * cfg.pos_y_ratio)

    paste_x = target_cx - rotated_layer.width // 2
    paste_y = target_cy - rotated_layer.height // 2

    # 构建全画幅透明图层进行 Alpha 复合
    full_overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    full_overlay.paste(rotated_layer, (paste_x, paste_y), mask=rotated_layer)

    # 准备基础图像
    orig_mode = image.mode
    base_rgba = image.convert("RGBA") if orig_mode != "RGBA" else image.copy()
    composited = Image.alpha_composite(base_rgba, full_overlay)

    # 模式回退处理：若是 RGB/RGBA 则保持原模式；若是 P 模式或其它受限模式则提升至 RGB/RGBA
    if orig_mode in ("RGB", "RGBA"):
        return composited.convert(orig_mode)
    return composited.convert("RGBA" if "A" in orig_mode else "RGB")



def apply_caption_to_frames(
    frames: list[Image.Image],
    config_or_text: Union[CaptionConfig, str, None],
    position: str = "bottom",
    font_size: Optional[int] = None,
) -> list[Image.Image]:
    """批量为帧序列叠加配文。

    Args:
        frames: PIL Image 列表
        config_or_text: CaptionConfig 对象或配文字符串
        position: 兼容模式文字位置 ('bottom' 或 'top')
        font_size: 可选字号

    Returns:
        包含配文的新帧列表；若未指定有效配文则返回原列表
    """
    if not frames or config_or_text is None:
        return frames

    if isinstance(config_or_text, str) and not config_or_text.strip():
        return frames

    if isinstance(config_or_text, CaptionConfig) and (not config_or_text.text or not config_or_text.text.strip()):
        return frames

    return [
        draw_caption(
            frame,
            config_or_text,
            position=position,
            font_size=font_size,
        )
        for frame in frames
    ]
