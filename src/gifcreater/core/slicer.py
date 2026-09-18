# -*- coding: utf-8 -*-
"""
src/gifcreater/core/slicer.py
切片与网格计算引擎 (纯无头/零 GUI 依赖)
"""

import math
import os
from typing import List, Tuple, Optional, Union
from PIL import Image

__all__ = [
    "GridConfig",
    "calculate_default_grid",
    "detect_dividers_universal",
    "get_grid_divider_coords",
    "get_aspect_ratio_info",
    "slice_image",
    "split_grid_image",
]


class GridConfig:
    """
    网格切片配置类
    支持 row_lines/h_lines 与 col_lines/v_lines 双向别名访问
    """

    def __init__(
        self,
        rows: int = 4,
        cols: int = 4,
        row_lines: Optional[List[int]] = None,
        col_lines: Optional[List[int]] = None,
        crop_bounds: Optional[Tuple[int, int, int, int]] = None,
        h_lines: Optional[List[int]] = None,
        v_lines: Optional[List[int]] = None,
    ):
        self.rows = max(1, rows)
        self.cols = max(1, cols)

        if row_lines is not None:
            self._row_lines = list(row_lines)
        elif h_lines is not None:
            self._row_lines = list(h_lines)
        else:
            self._row_lines = []

        if col_lines is not None:
            self._col_lines = list(col_lines)
        elif v_lines is not None:
            self._col_lines = list(v_lines)
        else:
            self._col_lines = []

        self.crop_bounds = crop_bounds

    @property
    def row_lines(self) -> List[int]:
        return self._row_lines

    @row_lines.setter
    def row_lines(self, val: List[int]):
        self._row_lines = list(val)

    @property
    def col_lines(self) -> List[int]:
        return self._col_lines

    @col_lines.setter
    def col_lines(self, val: List[int]):
        self._col_lines = list(val)

    @property
    def h_lines(self) -> List[int]:
        return self._row_lines

    @h_lines.setter
    def h_lines(self, val: List[int]):
        self._row_lines = list(val)

    @property
    def v_lines(self) -> List[int]:
        return self._col_lines

    @v_lines.setter
    def v_lines(self, val: List[int]):
        self._col_lines = list(val)

    def total_cells(self) -> int:
        return max(0, self.rows * self.cols)

    def __repr__(self) -> str:
        return (
            f"GridConfig(rows={self.rows}, cols={self.cols}, "
            f"row_lines={self._row_lines}, col_lines={self._col_lines}, "
            f"crop_bounds={self.crop_bounds})"
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, GridConfig):
            return False
        return (
            self.rows == other.rows
            and self.cols == other.cols
            and self._row_lines == other._row_lines
            and self._col_lines == other._col_lines
            and self.crop_bounds == other.crop_bounds
        )


def calculate_default_grid(
    width: Optional[int] = None,
    height: Optional[int] = None,
    rows: int = 4,
    cols: int = 4,
    bounds: Optional[Tuple[int, int, int, int]] = None,
    *,
    image_w: Optional[int] = None,
    image_h: Optional[int] = None,
    img: Optional[Image.Image] = None,
    auto_snap: bool = False,
) -> GridConfig:
    """
    根据图像宽高与行列数初始化分割线坐标。
    支持多态入参名 (width/height 或 image_w/image_h)。
    - 若 auto_snap=True 且传入 img，则调用投影波谷中位线算法自动吸附分镜缝隙；
    - 否则采用标准几何等分（若提供 bounds 则在 bounds 内部等分）。
    """
    if img is not None:
        w, h = img.size
    else:
        w = image_w if image_w is not None else (width if width is not None else 0)
        h = image_h if image_h is not None else (height if height is not None else 0)

    rows = max(1, rows)
    cols = max(1, cols)

    if w <= 0 or h <= 0:
        return GridConfig(rows=rows, cols=cols, row_lines=[], col_lines=[], crop_bounds=bounds)

    if auto_snap and img is not None:
        v_lines = _detect_single_axis(img, orientation="v", n_grid=cols, bounds=bounds)
        h_lines = _detect_single_axis(img, orientation="h", n_grid=rows, bounds=bounds)
    elif bounds is not None:
        left, top, right, bottom = bounds
        bw = max(0, right - left)
        bh = max(0, bottom - top)
        v_lines = [left + int(round(i * bw / cols)) for i in range(1, cols)]
        h_lines = [top + int(round(i * bh / rows)) for i in range(1, rows)]
    else:
        cw = w / float(cols)
        v_lines = [int(round(i * cw)) for i in range(1, cols)]
        rh = h / float(rows)
        h_lines = [int(round(i * rh)) for i in range(1, rows)]

    return GridConfig(
        rows=rows,
        cols=cols,
        row_lines=h_lines,
        col_lines=v_lines,
        crop_bounds=bounds,
    )


def _detect_single_axis(
    im: Image.Image,
    orientation: str = "v",
    n_grid: int = 4,
    bounds: Optional[Tuple[int, int, int, int]] = None,
) -> List[int]:
    """
    单轴特征线与缝隙波谷中位线探测算法 (Projection Profile Valley Detection)
    - 支持 RGB、RGBA 及单通道灰度图的原生探测
    - 计算单轴投影能量/方差剖面，提取连续低能量波谷带
    - 自动定位缝隙带的物理中位线 (Centerline)，彻底消除边缘吸附偏差
    """
    w, h = im.size
    if bounds:
        min_x, min_y, max_x, max_y = bounds
    else:
        min_x, min_y, max_x, max_y = 0, 0, w, h

    min_x = max(0, min(w, min_x))
    max_x = max(min_x, min(w, max_x))
    min_y = max(0, min(h, min_y))
    max_y = max(min_y, min(h, max_y))

    dim_start = min_x if orientation == "v" else min_y
    dim_end = max_x if orientation == "v" else max_y
    dim_len = max(0, dim_end - dim_start)

    other_start = min_y if orientation == "v" else min_x
    other_end = max_y if orientation == "v" else max_x
    other_len = max(0, other_end - other_start)

    n_divs = n_grid - 1
    if n_divs <= 0 or dim_len <= 0 or other_len <= 0:
        return []

    is_rgba = (im.mode == "RGBA")
    sample_img = im if is_rgba else im.convert("RGB")
    px = sample_img.load()

    step = max(1, other_len // 120)
    sample_coords = list(range(other_start, other_end, step))
    n_samples = len(sample_coords)
    if n_samples == 0:
        return []

    # 1. 沿主轴计算每条采样切线的能量值 (方差 + 透明度)
    energies = []
    for p in range(dim_start, dim_end):
        if orientation == "v":
            pts = [px[p, y] for y in sample_coords]
        else:
            pts = [px[x, p] for x in sample_coords]

        if is_rgba:
            transparent_count = sum(1 for pt in pts if pt[3] < 64)
            trans_ratio = transparent_count / float(n_samples)
            if trans_ratio > 0.4:
                e = (1.0 - trans_ratio) * 10.0
                energies.append(e)
                continue

        grays = [(pt[0] * 299 + pt[1] * 587 + pt[2] * 114) / 1000.0 for pt in pts]
        mean_g = sum(grays) / float(n_samples)
        var_g = sum((g - mean_g) ** 2 for g in grays) / float(n_samples)
        energies.append(var_g)

    cell_len = dim_len / float(n_grid)
    search_w = max(3, int(cell_len * 0.28))

    dividers = []
    for k in range(n_divs):
        nom_offset = int(round((k + 1) * cell_len))
        start_idx = max(0, nom_offset - search_w)
        end_idx = min(dim_len - 1, nom_offset + search_w)

        if start_idx >= end_idx:
            dividers.append(dim_start + nom_offset)
            continue

        window_energies = energies[start_idx : end_idx + 1]
        min_e = min(window_energies)

        # 动态波谷阈值：容许一定范围内的低能量平坦带
        valley_threshold = max(min_e * 1.35 + 15.0, min_e + 25.0)

        # 寻找波谷点
        valley_indices = [
            i for i, e in enumerate(window_energies) if e <= valley_threshold
        ]

        if not valley_indices:
            dividers.append(dim_start + nom_offset)
            continue

        # 将波谷点划分为连续区间
        segments = []
        cur_seg = [valley_indices[0]]
        for idx in valley_indices[1:]:
            if idx == cur_seg[-1] + 1:
                cur_seg.append(idx)
            else:
                segments.append(cur_seg)
                cur_seg = [idx]
        segments.append(cur_seg)

        # 选择最靠近理论等分点 nom_offset 的连续波谷区间
        target_local_idx = nom_offset - start_idx
        best_seg = min(
            segments,
            key=lambda seg: abs((seg[0] + seg[-1]) / 2.0 - target_local_idx),
        )

        # 取波谷区间物理中位线 (Centerline)
        gutter_center_local = int(round((best_seg[0] + best_seg[-1]) / 2.0))
        best_p = dim_start + start_idx + gutter_center_local

        # 边界安全性检查
        best_p = max(dim_start + 1, min(dim_end - 1, best_p))
        dividers.append(best_p)

    return dividers


def detect_dividers_universal(
    im: Image.Image,
    orientation: Union[str, int] = "v",
    n_grid: int = 4,
    bounds: Optional[Tuple[int, int, int, int]] = None,
) -> Union[List[int], Tuple[List[int], List[int]]]:
    """
    全能分割线检测算法：同时支持黑线、白线、细色线以及对比度边缘。
    多态重载：
    - 若 orientation 为 int: detect_dividers_universal(im, rows, cols, bounds) -> (xs, ys)
    - 若 orientation 为 str ('v' 或 'h'): 返回对应轴向的一维分割线列表
    """
    if isinstance(orientation, int):
        rows = orientation
        cols = n_grid
        xs = _detect_single_axis(im, orientation="v", n_grid=cols, bounds=bounds)
        ys = _detect_single_axis(im, orientation="h", n_grid=rows, bounds=bounds)
        return xs, ys

    return _detect_single_axis(im, orientation=orientation, n_grid=n_grid, bounds=bounds)


def get_grid_divider_coords(
    img: Image.Image,
    rows: int = 4,
    cols: int = 4,
    auto_trim_borders: bool = True,
    bounds: Optional[Tuple[int, int, int, int]] = None,
) -> Tuple[List[int], List[int]]:
    """
    获取网格分割线在图中的像素位置 (xs, ys)。
    auto_trim_borders: True 启用自适应特征线探测吸附；False 采用绝对几何等分。
    """
    w, h = img.size
    if auto_trim_borders:
        xs = _detect_single_axis(img, orientation="v", n_grid=cols, bounds=bounds)
        ys = _detect_single_axis(img, orientation="h", n_grid=rows, bounds=bounds)
    else:
        if bounds:
            left, top, right, bottom = bounds
            cw = (right - left) / float(cols)
            xs = [left + int(round(i * cw)) for i in range(1, cols)]
            rh = (bottom - top) / float(rows)
            ys = [top + int(round(i * rh)) for i in range(1, rows)]
        else:
            cw = w / float(cols)
            xs = [int(round(i * cw)) for i in range(1, cols)]
            rh = h / float(rows)
            ys = [int(round(i * rh)) for i in range(1, rows)]

    return xs, ys


def slice_image(
    img: Image.Image,
    grid_config: GridConfig,
    smart_crop: bool = True,
    bounds: Optional[Tuple[int, int, int, int]] = None,
    target_size: Optional[Tuple[int, int]] = None,
    scale_factor: float = 1.0,
) -> List[Image.Image]:
    """
    纯内存网格切片函数：
    接收 PIL Image，根据 grid_config 裁切，返回 List[Image.Image]。
    绝不进行磁盘文件写入。
    """
    w, h = img.size
    effective_bounds = bounds or grid_config.crop_bounds
    if effective_bounds:
        min_x, min_y, max_x, max_y = effective_bounds
        min_x = max(0, min(w, min_x))
        max_x = max(min_x, min(w, max_x))
        min_y = max(0, min(h, min_y))
        max_y = max(min_y, min(h, max_y))
    else:
        min_x, min_y, max_x, max_y = 0, 0, w, h

    v_lines = sorted([x for x in grid_config.col_lines if min_x <= x <= max_x])
    h_lines = sorted([y for y in grid_config.row_lines if min_y <= y <= max_y])

    trim_px = 1 if smart_crop else 0

    # 构建列切片范围
    col_bounds = []
    curr_x = min_x
    for vx in v_lines:
        col_bounds.append((curr_x, max(curr_x, vx - trim_px)))
        curr_x = min(max_x, vx + 1 + trim_px)
    col_bounds.append((curr_x, max_x))

    # 构建行切片范围
    row_bounds = []
    curr_y = min_y
    for hy in h_lines:
        row_bounds.append((curr_y, max(curr_y, hy - trim_px)))
        curr_y = min(max_y, hy + 1 + trim_px)
    row_bounds.append((curr_y, max_y))

    # 计算目标尺寸
    if target_size is None and scale_factor != 1.0:
        valid_cols = [x2 - x1 for x1, x2 in col_bounds if x2 > x1]
        valid_rows = [y2 - y1 for y1, y2 in row_bounds if y2 > y1]
        if valid_cols and valid_rows:
            avg_w = int(round(sum(valid_cols) / len(valid_cols) * scale_factor))
            avg_h = int(round(sum(valid_rows) / len(valid_rows) * scale_factor))
            target_size = (max(1, avg_w), max(1, avg_h))

    frames = []
    for y1, y2 in row_bounds:
        for x1, x2 in col_bounds:
            if x2 <= x1 or y2 <= y1:
                continue
            cell = img.crop((x1, y1, x2, y2))
            if target_size:
                cell = cell.resize(target_size, Image.Resampling.LANCZOS)
            frames.append(cell)

    return frames


def split_grid_image(
    image_path: str,
    output_dir: Optional[str] = None,
    rows: int = 4,
    cols: int = 4,
    auto_trim_borders: bool = True,
    custom_col_divs: Optional[List[int]] = None,
    custom_row_divs: Optional[List[int]] = None,
    target_size: Optional[Tuple[int, int]] = None,
    scale_factor: float = 1.0,
    prefix: str = "frame",
) -> List[str]:
    """
    向后兼容辅助函数：拆解网格图片为单帧文件并存盘，返回文件路径列表 List[str]。
    内部调用 slice_image 实现内存裁切。
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"找不到指定图片文件: {image_path}")

    from ..utils.paths import get_default_output_dir

    base_name = os.path.splitext(os.path.basename(image_path))[0]
    if not output_dir:
        output_dir = os.path.join(get_default_output_dir(), "frames", f"{base_name}_frames")

    os.makedirs(output_dir, exist_ok=True)

    img = Image.open(image_path).convert("RGB")
    w, h = img.size

    if custom_col_divs is not None and len(custom_col_divs) == cols - 1:
        v_lines = sorted(custom_col_divs)
    else:
        v_lines = (
            _detect_single_axis(img, orientation="v", n_grid=cols)
            if auto_trim_borders
            else [int(round(i * w / cols)) for i in range(1, cols)]
        )

    if custom_row_divs is not None and len(custom_row_divs) == rows - 1:
        h_lines = sorted(custom_row_divs)
    else:
        h_lines = (
            _detect_single_axis(img, orientation="h", n_grid=rows)
            if auto_trim_borders
            else [int(round(i * h / rows)) for i in range(1, rows)]
        )

    grid = GridConfig(rows=rows, cols=cols, row_lines=h_lines, col_lines=v_lines)
    cells = slice_image(
        img,
        grid,
        smart_crop=auto_trim_borders,
        target_size=target_size,
        scale_factor=scale_factor,
    )

    frame_files = []
    for idx, cell in enumerate(cells, start=1):
        frame_filename = f"{prefix}_{idx:02d}.png"
        frame_path = os.path.join(output_dir, frame_filename)
        cell.save(frame_path, format="PNG")
        frame_files.append(frame_path)

    return frame_files


def get_aspect_ratio_info(width: int, height: int) -> Tuple[str, str]:
    """
    根据给定的宽和高，推算标准画幅比例及构图语义说明。
    """
    if width <= 0 or height <= 0:
        return "--:--", "未知"

    aspect = width / height

    ratios = [
        (1.0, "1:1", "正方形 (头像/表情包)"),
        (16 / 9, "16:9", "横向宽屏 (影视/横版动图)"),
        (9 / 16, "9:16", "竖屏全屏 (短视频/故事)"),
        (4 / 3, "4:3", "经典横屏 (传统视讯)"),
        (3 / 4, "3:4", "经典竖屏 (社媒图文)"),
        (3 / 2, "3:2", "单反横构图 (35mm胶片)"),
        (2 / 3, "2:3", "单反竖构图"),
        (21 / 9, "21:9", "超宽电影宽幅"),
        (9 / 21, "9:21", "超长竖向长图"),
        (1 / 2, "1:2", "双倍高竖图"),
        (2 / 1, "2:1", "双倍宽横图"),
        (4 / 5, "4:5", "社媒肖像黄金比"),
        (5 / 4, "5:4", "大幅相机画幅"),
    ]

    for r_val, name, desc in ratios:
        if abs(aspect - r_val) < 0.02:
            return name, desc

    g = math.gcd(width, height)
    sw, sh = width // g, height // g
    if sw <= 32 and sh <= 32:
        tag = "横向" if sw > sh else ("纵向" if sh > sw else "正方形")
        return f"{sw}:{sh}", f"非标比例 ({tag})"

    if aspect >= 1:
        return f"{aspect:.2f}:1", "自定义横向画幅"
    else:
        return f"1:{1/aspect:.2f}", "自定义纵向画幅"
