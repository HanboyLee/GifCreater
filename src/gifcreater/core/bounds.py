# -*- coding: utf-8 -*-
"""
src/gifcreater/core/bounds.py
智能边界与主体探测引擎 (纯无头/零 GUI 依赖)
"""

from typing import Tuple
from PIL import Image, ImageChops

__all__ = ["detect_bounds"]


def detect_bounds(img: Image.Image, tolerance: int = 15) -> Tuple[int, int, int, int]:
    """
    智能背景色采样与主体包围盒探测算法。
    自动探测画面边缘留白（纯黑边、纯白边或单色背景），返回核心内容的外接矩形。

    :param img: PIL 图像对象
    :param tolerance: 颜色容差阈值 (默认 15)
    :return: (left, top, right, bottom) 主体包围盒元组；若无有效主体则回退为全图 (0, 0, w, h)
    """
    w, h = img.size
    if w <= 0 or h <= 0:
        return (0, 0, 0, 0)

    # 1. 透明度 Alpha 通道优先判定
    if img.mode == "RGBA":
        alpha = img.split()[-1]
        # 若存在显著透明区域 (最小 Alpha < 128)
        if alpha.getextrema()[0] < 128:
            alpha_bin = alpha.point(lambda p: 255 if p > tolerance else 0)
            alpha_bbox = alpha_bin.getbbox()
            if alpha_bbox is not None:
                left, top, right, bottom = alpha_bbox
                box_w = right - left
                box_h = bottom - top
                if box_w >= w * 0.10 and box_h >= h * 0.10:
                    return (left, top, right, bottom)

    # 2. 转换为 RGB 格式进行背景色采样
    im = img.convert("RGB")

    # 四角区域像素采样估计背景色 (取四角各 3x3 像素均值)
    patch_w = min(3, w)
    patch_h = min(3, h)
    corners = [
        (0, 0),                         # 左上
        (w - patch_w, 0),               # 右上
        (0, h - patch_h),               # 左下
        (w - patch_w, h - patch_h)      # 右下
    ]

    corner_samples = []
    for cx, cy in corners:
        for dx in range(patch_w):
            for dy in range(patch_h):
                corner_samples.append(im.getpixel((cx + dx, cy + dy)))

    bg_r = int(round(sum(p[0] for p in corner_samples) / len(corner_samples)))
    bg_g = int(round(sum(p[1] for p in corner_samples) / len(corner_samples)))
    bg_b = int(round(sum(p[2] for p in corner_samples) / len(corner_samples)))
    bg_color = (bg_r, bg_g, bg_b)

    # 3. 向量差分与阈值二值化
    bg_img = Image.new("RGB", (w, h), bg_color)
    diff = ImageChops.difference(im, bg_img)

    # 查表法加速通道二值化：若通道差值 > tolerance 则置为 255
    lut = [0 if val <= tolerance else 255 for val in range(256)]
    diff_bin = diff.point(lut * 3).convert("L")

    bbox = diff_bin.getbbox()

    # 4. 边界防崩溃与极小区域回退保护 (Fallback to full image)
    if bbox is None:
        # 纯单色画面，无反差主体，安全回退为全图
        return (0, 0, w, h)

    left, top, right, bottom = bbox
    box_w = right - left
    box_h = bottom - top

    # 若主体尺寸极小 (< 10%)，判定为噪点干扰，安全回退为全图
    if box_w < w * 0.10 or box_h < h * 0.10:
        return (0, 0, w, h)

    return (left, top, right, bottom)
