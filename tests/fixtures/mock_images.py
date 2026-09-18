# -*- coding: utf-8 -*-
"""
tests/fixtures/mock_images.py
纯内存合成微型图像与测试固件生成器 (Zero-Disk-Media)
======================================================
所有测试图像在内存中动态生成，运行结束后自动被垃圾回收。
严格杜绝任何大体积媒体文件落盘或提交至 Git 仓库。
"""

import math
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw


def create_dummy_grid_image(
    width: int = 400,
    height: int = 400,
    rows: int = 2,
    cols: int = 2,
    line_color: Tuple[int, int, int] = (0, 0, 0),
    bg_color: Tuple[int, int, int] = (240, 240, 240),
    line_width: int = 2,
    cell_patterns: bool = False,
) -> Image.Image:
    """
    在内存中生成包含分割线的小尺寸网格测试图。
    :param width: 图像总宽度像素
    :param height: 图像总高度像素
    :param rows: 网格行数
    :param cols: 网格列数
    :param line_color: 分割线 RGB 颜色
    :param bg_color: 背景底色
    :param line_width: 分割线线宽 (像素)
    :param cell_patterns: 若为 True，为每个单元格绘制不同颜色的色块，便于切片后内容区分
    :return: PIL.Image.Image 对象 (模式 'RGB')
    """
    im = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(im)

    col_w = width // cols
    row_h = height // rows

    if cell_patterns:
        for r in range(rows):
            for c in range(cols):
                x1 = c * col_w + line_width
                y1 = r * row_h + line_width
                x2 = (c + 1) * col_w - line_width
                y2 = (r + 1) * row_h - line_width
                if x2 > x1 and y2 > y1:
                    cell_color = ((r * 60 + 50) % 256, (c * 80 + 70) % 256, 150)
                    draw.rectangle([x1, y1, x2, y2], fill=cell_color)

    # 绘制垂直分割线
    for c in range(1, cols):
        x = c * col_w
        draw.line([(x, 0), (x, height)], fill=line_color, width=line_width)

    # 绘制水平分割线
    for r in range(1, rows):
        y = r * row_h
        draw.line([(0, y), (width, y)], fill=line_color, width=line_width)

    return im


def create_border_probe_image(
    width: int = 200,
    height: int = 200,
    border_width: int = 10,
    border_color: Tuple[int, int, int] = (0, 0, 0),
    fill_color: Tuple[int, int, int] = (255, 100, 100),
    padding_asymmetric: Optional[Tuple[int, int, int, int]] = None,
) -> Image.Image:
    """
    在内存中生成包含外围黑边/白边留白的主体测试图。
    :param width: 图像总宽度
    :param height: 图像总高度
    :param border_width: 对称边框留白宽度
    :param border_color: 边框底色 (通常为 (0,0,0) 或 (255,255,255))
    :param fill_color: 内部主体高对比度颜色
    :param padding_asymmetric: 可选非对称留白 (left, top, right, bottom)
    :return: PIL.Image.Image 对象 (模式 'RGB')
    """
    im = Image.new("RGB", (width, height), color=border_color)
    draw = ImageDraw.Draw(im)

    if padding_asymmetric:
        pl, pt, pr, pb = padding_asymmetric
        inner_rect = [pl, pt, width - pr, height - pb]
    else:
        inner_rect = [border_width, border_width, width - border_width, height - border_width]

    draw.rectangle(inner_rect, fill=fill_color)
    return im


def create_synthetic_animated_frames(
    count: int = 8,
    size: Tuple[int, int] = (120, 120),
    complexity: str = "gradient",
) -> List[Image.Image]:
    """
    在内存中生成连续多帧动画序列，用于驱动压缩引擎与动图导出。
    :param count: 帧数量
    :param size: 单帧宽高 (w, h)
    :param complexity:
      - 'simple': 纯色阶变化
      - 'gradient': 渐变色伴随移动色块 (模拟真实逐帧动画)
      - 'high_entropy': 高噪点与高频颜色变换 (用于微信表情包极限抗压降级测试)
    :return: List[PIL.Image.Image]
    """
    w, h = size
    frames = []

    for i in range(count):
        if complexity == "simple":
            color = ((i * 35) % 256, (i * 20 + 80) % 256, (240 - i * 30) % 256)
            im = Image.new("RGB", size, color=color)

        elif complexity == "gradient":
            im = Image.new("RGB", size, color=(30, 30, 40))
            draw = ImageDraw.Draw(im)
            cx = int(w * 0.2 + (w * 0.6) * (i / max(1, count - 1)))
            cy = int(h * 0.5 + (h * 0.3) * math.sin(i * math.pi / 4))
            r = min(w, h) // 4
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, (i * 30) % 256, 50))
            draw.rectangle([10, 10, 30, 30], fill=((i * 40) % 256, 200, 220))

        elif complexity == "high_entropy":
            im = Image.new("RGB", size, color=(i * 10 % 256, 128, 128))
            draw = ImageDraw.Draw(im)
            step = 8
            for x in range(0, w, step):
                for y in range(0, h, step):
                    c = (
                        (x * 17 + y * 23 + i * 47) % 256,
                        (x * 31 + y * 13 + i * 29) % 256,
                        (x * 7 + y * 53 + i * 11) % 256,
                    )
                    draw.rectangle([x, y, x + step, y + step], fill=c)
        else:
            raise ValueError(f"未知的复杂度类型: {complexity}")

        frames.append(im)

    return frames


def create_transparent_frame(
    width: int = 100,
    height: int = 100,
    alpha_bg: int = 0,
    shape_color: Tuple[int, int, int, int] = (255, 0, 0, 255),
    shape_rect: Tuple[int, int, int, int] = (20, 20, 80, 80),
) -> Image.Image:
    """
    在内存中生成包含 Alpha 透明通道的 RGBA 单帧图像。
    :param width: 图像宽
    :param height: 图像高
    :param alpha_bg: 背景透明度 (0 表示全透明)
    :param shape_color: 主体 RGBA 颜色
    :param shape_rect: 主体包围盒 (x1, y1, x2, y2)
    :return: PIL.Image.Image (模式 'RGBA')
    """
    im = Image.new("RGBA", (width, height), color=(0, 0, 0, alpha_bg))
    draw = ImageDraw.Draw(im)
    draw.rectangle(shape_rect, fill=shape_color)
    return im
