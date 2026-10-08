# -*- coding: utf-8 -*-
"""动态生成微型测试视频（不依赖、也不提交任何真实视频素材）。

约定：第 i 帧整幅涂成 ``color_for_index(i)``，解码后用 ``index_from_image`` 反推帧号，
即可断言「取到的就是第 i 帧」，而不是近似帧。
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import av
from PIL import Image

_STEP = 20  # 相邻帧红色通道间隔，足以抵抗有损编码误差


def color_for_index(i: int) -> Tuple[int, int, int]:
    return (min(255, _STEP * i), max(0, 255 - _STEP * i), 128)


def index_from_image(img: Image.Image) -> int:
    """由整幅图的平均红色通道反推帧号。"""
    r = img.convert("RGB").resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))[0]
    return int(round(r / _STEP))


def make_color_video(
    path,
    n: int = 12,
    size: Tuple[int, int] = (64, 48),
    fps: int = 10,
    codec: str = "mpeg4",
    pts_list: Optional[Sequence[int]] = None,
    gop: int = 4,
    bframes: int = 2,
) -> Path:
    """编码一个 n 帧的彩色序列视频并返回路径。

    pts_list 不为空时用于构造变帧率（VFR）视频，长度即帧数。
    """
    path = Path(path)
    pts: List[int] = list(pts_list) if pts_list is not None else list(range(n))
    out = av.open(str(path), "w")
    try:
        stream = out.add_stream(codec, rate=fps)
        stream.width, stream.height = size
        stream.pix_fmt = "yuv420p"
        stream.codec_context.gop_size = gop
        if codec == "mpeg4":
            stream.codec_context.max_b_frames = bframes
        for i, p in enumerate(pts):
            frame = av.VideoFrame.from_image(Image.new("RGB", size, color_for_index(i)))
            frame.pts = p
            for packet in stream.encode(frame):
                out.mux(packet)
        for packet in stream.encode():
            out.mux(packet)
    finally:
        out.close()
    return path
