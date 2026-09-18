# -*- coding: utf-8 -*-
"""
src/gifcreater/core/exporter.py
动图封装、序列展开与全格式导出引擎 (纯无头/零 GUI 依赖)
"""

import glob
import io
import os
import re
from typing import List, Tuple, Optional, Union
from PIL import Image

from .caption import apply_caption_to_frames

__all__ = [
    "natural_sort_key",
    "generate_boomerang_sequence",
    "export_gif",
    "export_webp",
    "save_to_disk",
    "create_animation",
    "create_gif",
    "process_image_to_gif",
]


def natural_sort_key(s: str) -> List[Union[int, str]]:
    """
    自然数语义排序键，确保 'frame_2.png' 排在 'frame_10.png' 前面
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", str(s))]


def generate_boomerang_sequence(
    frames: List[Image.Image],
    durations: Optional[List[int]] = None,
) -> Tuple[List[Image.Image], List[int]]:
    """
    生成 Boomerang 往复序列：
    若帧数 > 2，序列镜像展开为 [A, B, C, D, C, B]，首尾不重复拼接。
    """
    n = len(frames)
    if n <= 2:
        durs = list(durations) if durations else [100] * n
        return list(frames), durs

    expanded_frames = list(frames) + list(reversed(frames[1:-1]))
    if durations:
        expanded_durations = list(durations) + list(reversed(durations[1:-1]))
    else:
        expanded_durations = [100] * len(expanded_frames)

    return expanded_frames, expanded_durations


def export_gif(
    frames: List[Image.Image],
    durations: List[int],
    output_path: Optional[str] = None,
    loop: int = 0,
    boomerang: bool = False,
    optimize: bool = False,
    caption_text: Optional[str] = None,
    caption_pos: str = "bottom",
) -> Union[bytes, str]:
    """
    封装高质量 GIF 动图
    - 若 output_path 为 None，纯内存运行返回 bytes
    - 若 output_path 为字符串，写出文件并返回绝对路径 str
    - 支持可选的表情包配文叠加 (caption_text, caption_pos)
    """
    if not frames:
        raise ValueError("帧列表为空，无法导出 GIF")

    # 参数容错：若第 3 个位置参数传入了 int，自动将其视为 loop
    if isinstance(output_path, int):
        loop = output_path
        output_path = None

    if caption_text:
        frames = apply_caption_to_frames(frames, caption_text, position=caption_pos)

    if boomerang:
        exp_frames, exp_durs = generate_boomerang_sequence(frames, durations)
    else:
        exp_frames, exp_durs = list(frames), list(durations)

    first_size = exp_frames[0].size
    processed = [
        im.resize(first_size, Image.Resampling.LANCZOS) if im.size != first_size else im
        for im in exp_frames
    ]
    converted = [im.convert("RGB") if im.mode not in ("RGB", "P") else im for im in processed]

    buf = io.BytesIO()
    converted[0].save(
        buf,
        format="GIF",
        save_all=True,
        append_images=converted[1:],
        duration=exp_durs,
        loop=loop,
        optimize=optimize,
    )
    data = buf.getvalue()

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(data)
        return os.path.abspath(output_path)

    return data


def export_webp(
    frames: List[Image.Image],
    durations: List[int],
    output_path: Optional[str] = None,
    loop: int = 0,
    boomerang: bool = False,
    quality: int = 85,
    method: int = 6,
    caption_text: Optional[str] = None,
    caption_pos: str = "bottom",
) -> Union[bytes, str]:
    """
    封装高保真 WebP 动图 (全彩 1600 万色 + Alpha 通道)
    - 若 output_path 为 None，返回 bytes
    - 若 output_path 为字符串，写出文件并返回绝对路径 str
    - 支持可选的表情包配文叠加 (caption_text, caption_pos)
    """
    if not frames:
        raise ValueError("帧列表为空，无法导出 WebP")

    if isinstance(output_path, int):
        loop = output_path
        output_path = None

    if caption_text:
        frames = apply_caption_to_frames(frames, caption_text, position=caption_pos)

    if boomerang:
        exp_frames, exp_durs = generate_boomerang_sequence(frames, durations)
    else:
        exp_frames, exp_durs = list(frames), list(durations)


    first_size = exp_frames[0].size
    processed = [
        im.resize(first_size, Image.Resampling.LANCZOS) if im.size != first_size else im
        for im in exp_frames
    ]
    converted = [im.convert("RGBA") if im.mode != "RGBA" else im for im in processed]

    buf = io.BytesIO()
    converted[0].save(
        buf,
        format="WEBP",
        save_all=True,
        append_images=converted[1:],
        duration=exp_durs,
        loop=loop,
        quality=quality,
        method=method,
    )
    data = buf.getvalue()

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(data)
        return os.path.abspath(output_path)

    return data


def save_to_disk(data: bytes, file_path: Union[str, os.PathLike]) -> str:
    """安全保存二进制数据至磁盘，自动递归创建父目录"""
    abs_path = os.path.abspath(str(file_path))
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "wb") as f:
        f.write(data)
    return abs_path


def create_animation(
    frame_paths_or_dir: any,
    output_path: str,
    duration: int = 350,
    last_frame_pause: int = 1500,
    loop: int = 0,
    preset: str = "original",
    boomerang: bool = False,
    resize: Optional[Tuple[int, int]] = None,
    wechat_mode: bool = False,
    caption_text: Optional[str] = None,
    caption_pos: str = "bottom",
) -> str:
    """
    通用动图合成接口（支持原画 GIF、微信表情包标准、WebP、乒乓往复循环、表情包配文）。
    100% 兼容历史调用入参与文件/目录解析行为。
    """
    if wechat_mode:
        preset = "wechat"

    # 1. 载入图片路径或对象
    if isinstance(frame_paths_or_dir, str):
        if os.path.isdir(frame_paths_or_dir):
            patterns = [
                "*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp",
                "*.PNG", "*.JPG", "*.JPEG", "*.WEBP", "*.BMP",
            ]
            found = []
            for pat in patterns:
                found.extend(glob.glob(os.path.join(frame_paths_or_dir, pat)))
            files = list(set(found))
            files.sort(key=natural_sort_key)
            if not files:
                raise ValueError(f"目录中未找到有效图片文件: {frame_paths_or_dir}")
            frame_paths = files
        else:
            raise ValueError(f"输入路径非有效目录: {frame_paths_or_dir}")
    elif isinstance(frame_paths_or_dir, list):
        if not frame_paths_or_dir:
            raise ValueError("单帧图片列表为空，无法合成动图")
        if isinstance(frame_paths_or_dir[0], Image.Image):
            images = list(frame_paths_or_dir)
            frame_paths = None
        else:
            frame_paths = sorted(frame_paths_or_dir, key=natural_sort_key)
            images = None
    else:
        raise TypeError("frame_paths_or_dir 必须为路径列表或目录字符串")

    if frame_paths is not None:
        images = [Image.open(p) for p in frame_paths]

    # 2. 预设特化与尺寸时延处理
    if preset == "wechat":
        max_edge = 240
        w0, h0 = images[0].size
        scale = min(max_edge / w0, max_edge / h0, 1.0)
        target_w = max(1, int(round(w0 * scale)))
        target_h = max(1, int(round(h0 * scale)))
        images = [im.resize((target_w, target_h), Image.Resampling.LANCZOS) for im in images]
        if duration > 160:
            duration = 120
        if boomerang or last_frame_pause > 500:
            last_frame_pause = 0
    elif preset == "xiaohongshu":
        max_edge = 1080
        w0, h0 = images[0].size
        if max(w0, h0) > max_edge:
            scale = max_edge / max(w0, h0)
            target_w = max(1, int(round(w0 * scale)))
            target_h = max(1, int(round(h0 * scale)))
            images = [im.resize((target_w, target_h), Image.Resampling.LANCZOS) for im in images]
    elif resize:
        images = [im.resize(resize, Image.Resampling.LANCZOS) for im in images]
    else:
        first_size = images[0].size
        images = [
            im.resize(first_size, Image.Resampling.LANCZOS) if im.size != first_size else im
            for im in images
        ]

    # 叠加表情包文字配文 (若指定)
    if caption_text:
        images = apply_caption_to_frames(images, caption_text, position=caption_pos)

    num_frames = len(images)
    durations = [duration] * num_frames
    if not boomerang and last_frame_pause > 0 and num_frames > 0:
        durations[-1] = last_frame_pause

    if boomerang:
        images, durations = generate_boomerang_sequence(images, durations)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # 3. 格式写出
    if preset == "webp" or output_path.lower().endswith(".webp"):
        export_webp(images, durations, output_path=output_path, loop=loop)
        return os.path.abspath(output_path)

    if preset == "wechat":
        from .compressor import compress_wechat_gif

        data = compress_wechat_gif(images, durations, max_size_bytes=500 * 1024, max_side=240)
        with open(output_path, "wb") as f:
            f.write(data)
        return os.path.abspath(output_path)

    export_gif(images, durations, output_path=output_path, loop=loop, optimize=False)
    return os.path.abspath(output_path)


def create_gif(
    frame_paths_or_dir: any,
    output_gif_path: str,
    duration: int = 350,
    last_frame_pause: int = 1500,
    loop: int = 0,
    resize: Optional[Tuple[int, int]] = None,
    boomerang: bool = False,
    wechat_mode: bool = False,
    caption_text: Optional[str] = None,
    caption_pos: str = "bottom",
) -> str:
    """历史 create_gif 快捷函数"""
    return create_animation(
        frame_paths_or_dir=frame_paths_or_dir,
        output_path=output_gif_path,
        duration=duration,
        last_frame_pause=last_frame_pause,
        loop=loop,
        preset="wechat" if wechat_mode else "original",
        boomerang=boomerang,
        resize=resize,
        wechat_mode=wechat_mode,
        caption_text=caption_text,
        caption_pos=caption_pos,
    )


def process_image_to_gif(
    image_path: str,
    output_gif_path: Optional[str] = None,
    output_frames_dir: Optional[str] = None,
    rows: int = 4,
    cols: int = 4,
    duration: int = 350,
    last_frame_pause: int = 1500,
    auto_trim_borders: bool = True,
    custom_col_divs: Optional[List[int]] = None,
    custom_row_divs: Optional[List[int]] = None,
    scale_factor: float = 1.0,
    preset: str = "original",
    boomerang: bool = False,
    caption_text: Optional[str] = None,
    caption_pos: str = "bottom",
) -> Tuple[List[str], str]:
    """一键拆解网格图并合成动图全流程"""
    from .slicer import split_grid_image
    from ..utils.paths import get_default_output_dir

    base_name = os.path.splitext(os.path.basename(image_path))[0]
    out_root = get_default_output_dir()

    if not output_frames_dir:
        output_frames_dir = os.path.join(out_root, "frames", f"{base_name}_frames")

    ext = ".webp" if preset == "webp" else ".gif"
    suffix = "_wechat" if preset == "wechat" else ("_boomerang" if boomerang else "")
    if not output_gif_path:
        output_gif_path = os.path.join(out_root, "gifs", f"{base_name}{suffix}{ext}")

    frames = split_grid_image(
        image_path=image_path,
        output_dir=output_frames_dir,
        rows=rows,
        cols=cols,
        auto_trim_borders=auto_trim_borders,
        custom_col_divs=custom_col_divs,
        custom_row_divs=custom_row_divs,
        scale_factor=scale_factor,
    )

    result_path = create_animation(
        frame_paths_or_dir=frames,
        output_path=output_gif_path,
        duration=duration,
        last_frame_pause=last_frame_pause,
        preset=preset,
        boomerang=boomerang,
        caption_text=caption_text,
        caption_pos=caption_pos,
    )

    return frames, result_path

