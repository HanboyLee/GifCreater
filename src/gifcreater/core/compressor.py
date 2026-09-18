# -*- coding: utf-8 -*-
"""
src/gifcreater/core/compressor.py
微信表情包自适应压缩引擎 (WeChat Sticker Compressor)
=============================================================

遵循微信表情包技术规范：
1. 几何尺寸约束：最长边严格 <= 240px (等比缩放，小图不放大)；
2. 体积硬性门禁：输出体积严格 <= 500KB (512,000 bytes)；
3. 调色板自适应阶梯：128 -> 96 -> 64 -> 48 -> 32 色试探；
4. 极端场景兜底：延时归一化、隔帧抽取、延时累加与几何降采样；
5. 纯内存 Headless 设计，输入 PIL 图像列表，输出 GIF89a 二进制 bytes。
"""

import io
from typing import List, Optional, Union
from PIL import Image

__all__ = ["compress_wechat_gif"]


def compress_wechat_gif(
    frames: List[Image.Image],
    durations: Optional[Union[List[int], int]] = None,
    max_size_bytes: int = 512000,
    max_side: int = 240,
    loop: int = 0,
) -> bytes:
    """
    自适应微信表情包压缩核心算法。

    :param frames: PIL Image 对象列表
    :param durations: 帧停留时间（毫秒），可传入单值 int、列表 List[int] 或 None
    :param max_size_bytes: 最大字节数限制 (默认 512,000 字节 = 500KB)
    :param max_side: 最长边最大像素限制 (默认 240 像素)
    :param loop: 循环播放次数 (默认 0 表示无限循环)
    :return: 编码完成的 GIF 二进制数据 (bytes)
    :raises ValueError: 当 frames 为空、尺寸非法或 max_size_bytes <= 0 时抛出
    """
    if not frames:
        raise ValueError("frames list cannot be empty")
    if max_size_bytes <= 0:
        raise ValueError("max_size_bytes must be positive")
    if max_side <= 0:
        raise ValueError("max_side must be positive")

    # 1. 颜色模式统一归一化 (兼容 RGBA, RGB, L, P, 1, CMYK)
    norm_frames: List[Image.Image] = []
    for im in frames:
        if im.mode not in ("RGB", "RGBA"):
            norm_frames.append(im.convert("RGB"))
        else:
            norm_frames.append(im)

    # 2. 几何等比缩放推导 (最长边 <= max_side, 小图不放大)
    w0, h0 = norm_frames[0].size
    if w0 <= 0 or h0 <= 0:
        raise ValueError(f"Invalid frame dimensions: {w0}x{h0}")

    scale = min(max_side / w0, max_side / h0, 1.0)
    target_w = max(1, min(max_side, int(round(w0 * scale))))
    target_h = max(1, min(max_side, int(round(h0 * scale))))

    # 统一将所有帧缩放到标准目标尺寸 (规避异构多帧尺寸问题)
    resized_frames = [
        im.resize((target_w, target_h), Image.Resampling.LANCZOS)
        if im.size != (target_w, target_h)
        else im
        for im in norm_frames
    ]

    num_frames = len(resized_frames)

    # 3. 帧延时量化保护 (遵循 GIF89a 10ms 颗粒度标准，保证 >= 20ms，四舍五入到 10ms 整数倍)
    def _quantize_duration(d: int) -> int:
        return max(20, int(round(d / 10.0) * 10))

    if durations is None:
        norm_durs = [100] * num_frames
    elif isinstance(durations, int):
        norm_durs = [_quantize_duration(durations)] * num_frames
    else:
        norm_durs = [_quantize_duration(d) for d in durations]
        if len(norm_durs) < num_frames:
            norm_durs.extend([100] * (num_frames - len(norm_durs)))
        elif len(norm_durs) > num_frames:
            norm_durs = norm_durs[:num_frames]

    curr_frames = resized_frames
    curr_durs = norm_durs
    palette_ladder = [128, 96, 64, 48, 32]
    data = b""

    # 4. 自适应调色板阶梯试探与极端场景多级降级循环
    while True:
        # 阶梯试探
        for colors in palette_ladder:
            p_frames = [
                im.convert("P", palette=Image.Palette.ADAPTIVE, colors=colors)
                for im in curr_frames
            ]
            buf = io.BytesIO()
            p_frames[0].save(
                buf,
                format="GIF",
                save_all=True,
                append_images=p_frames[1:],
                duration=curr_durs,
                loop=loop,
                optimize=True,
            )
            data = buf.getvalue()
            if len(data) <= max_size_bytes:
                return data

        # Tier 1: 隔帧抽取降采样 (当帧数 > 2 时)
        if len(curr_frames) > 2:
            sub_frames = curr_frames[::2]
            sub_durs = [
                curr_durs[i] + (curr_durs[i + 1] if i + 1 < len(curr_durs) else 0)
                for i in range(0, len(curr_durs), 2)
            ]
            curr_frames = sub_frames
            curr_durs = sub_durs
            # 重置阶梯，给抽取后的帧提供最佳画质机会
            palette_ladder = [128, 96, 64, 48, 32]
            continue

        # Tier 2: 几何尺寸按 0.75 递减
        new_w = max(1, int(curr_frames[0].width * 0.75))
        new_h = max(1, int(curr_frames[0].height * 0.75))
        if (new_w, new_h) != (curr_frames[0].width, curr_frames[0].height):
            curr_frames = [
                im.resize((new_w, new_h), Image.Resampling.LANCZOS)
                for im in curr_frames
            ]
            palette_ladder = [128, 96, 64, 48, 32]
            continue

        # Tier 3: 深度色阶降维
        if palette_ladder != [16, 8, 4, 2]:
            palette_ladder = [16, 8, 4, 2]
            continue

        # Tier 4: 单帧极限兜底
        if len(curr_frames) > 1:
            curr_frames = [curr_frames[0]]
            curr_durs = [curr_durs[0]]
            continue

        return data
