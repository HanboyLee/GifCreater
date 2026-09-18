# -*- coding: utf-8 -*-
"""
tests/unit/test_slicer.py
单元测试: slicer.py (切片与网格计算引擎)
"""

from pathlib import Path
import pytest
from PIL import Image
from src.gifcreater.core.slicer import (
    GridConfig,
    calculate_default_grid,
    detect_dividers_universal,
    get_grid_divider_coords,
    slice_image,
    split_grid_image,
    get_aspect_ratio_info,
)
from tests.fixtures.mock_images import create_dummy_grid_image


def test_grid_config_dataclass():
    """验证 GridConfig 基础属性、双向别名与 cell 计算"""
    cfg = GridConfig(rows=3, cols=4, row_lines=[100, 200], col_lines=[50, 100, 150])
    assert cfg.rows == 3
    assert cfg.cols == 4
    assert cfg.total_cells() == 12
    assert cfg.crop_bounds is None

    # 别名测试
    assert cfg.h_lines == [100, 200]
    assert cfg.v_lines == [50, 100, 150]

    cfg.h_lines = [80, 160]
    assert cfg.row_lines == [80, 160]

    cfg.v_lines = [40, 80, 120]
    assert cfg.col_lines == [40, 80, 120]

    # repr and eq
    repr_str = repr(cfg)
    assert "GridConfig" in repr_str

    cfg2 = GridConfig(rows=3, cols=4, row_lines=[80, 160], col_lines=[40, 80, 120])
    assert cfg == cfg2
    assert cfg != "other"

    # h_lines/v_lines 构造入参测试
    cfg3 = GridConfig(rows=2, cols=2, h_lines=[50], v_lines=[60])
    assert cfg3.row_lines == [50]
    assert cfg3.col_lines == [60]


def test_calculate_default_grid_uniform():
    """验证无 bounds 时的均匀网格坐标推导"""
    cfg = calculate_default_grid(image_w=400, image_h=300, rows=3, cols=4)
    assert cfg.rows == 3
    assert cfg.cols == 4
    assert cfg.col_lines == [100, 200, 300]
    assert cfg.row_lines == [100, 200]

    # 位置参数调用
    cfg_pos = calculate_default_grid(400, 300, 3, 4)
    assert cfg_pos.col_lines == [100, 200, 300]
    assert cfg_pos.row_lines == [100, 200]


def test_calculate_default_grid_with_bounds():
    """验证提供主体包围盒 bounds 时的局部偏移网格计算"""
    bounds = (50, 50, 250, 250)
    cfg = calculate_default_grid(image_w=400, image_h=400, rows=2, cols=2, bounds=bounds)
    assert cfg.crop_bounds == bounds
    assert cfg.col_lines == [150]
    assert cfg.row_lines == [150]


def test_calculate_default_grid_edge_cases():
    """验证 rows=1 或 cols=1 或零/负尺寸的边界情况"""
    cfg = calculate_default_grid(image_w=200, image_h=200, rows=1, cols=1)
    assert cfg.row_lines == []
    assert cfg.col_lines == []
    assert cfg.total_cells() == 1

    cfg_zero = calculate_default_grid(width=0, height=0, rows=2, cols=2)
    assert cfg_zero.row_lines == []
    assert cfg_zero.col_lines == []


def test_detect_dividers_universal_v_and_h(dummy_grid_image_2x2):
    """验证垂直与水平特征分割线自动探测"""
    v_lines = detect_dividers_universal(dummy_grid_image_2x2, orientation="v", n_grid=2)
    h_lines = detect_dividers_universal(dummy_grid_image_2x2, orientation="h", n_grid=2)

    assert len(v_lines) == 1
    assert 190 <= v_lines[0] <= 210
    assert len(h_lines) == 1
    assert 190 <= h_lines[0] <= 210


def test_detect_dividers_universal_single_grid():
    """验证 n_grid <= 1 时快速返回空列表"""
    im = Image.new("RGB", (100, 100), (255, 255, 255))
    assert detect_dividers_universal(im, orientation="v", n_grid=1) == []
    assert detect_dividers_universal(im, orientation="h", n_grid=0) == []


def test_detect_dividers_universal_polymorphic(dummy_grid_image_2x2):
    """验证多态调用 detect_dividers_universal(im, rows, cols) -> (xs, ys)"""
    xs, ys = detect_dividers_universal(dummy_grid_image_2x2, 2, 2)
    assert len(xs) == 1
    assert len(ys) == 1
    assert 190 <= xs[0] <= 210
    assert 190 <= ys[0] <= 210


def test_get_grid_divider_coords_auto_and_uniform(dummy_grid_image_3x3):
    """验证 get_grid_divider_coords 在开启与关闭自动吸附时的行为"""
    xs_geom, ys_geom = get_grid_divider_coords(dummy_grid_image_3x3, rows=3, cols=3, auto_trim_borders=False)
    assert xs_geom == [100, 200]
    assert ys_geom == [100, 200]

    xs_auto, ys_auto = get_grid_divider_coords(dummy_grid_image_3x3, rows=3, cols=3, auto_trim_borders=True)
    assert len(xs_auto) == 2
    assert len(ys_auto) == 2

    # 带 bounds 的几何计算
    xs_b, ys_b = get_grid_divider_coords(
        dummy_grid_image_3x3, rows=2, cols=2, auto_trim_borders=False, bounds=(10, 10, 210, 210)
    )
    assert xs_b == [110]
    assert ys_b == [110]


def test_slice_image_in_memory():
    """验证纯内存切片产出 List[Image.Image] 且尺寸准确"""
    im = create_dummy_grid_image(width=200, height=200, rows=2, cols=2)
    cfg = GridConfig(rows=2, cols=2, row_lines=[100], col_lines=[100])

    frames = slice_image(im, grid_config=cfg, smart_crop=False)
    assert len(frames) == 4
    assert all(isinstance(f, Image.Image) for f in frames)
    assert frames[0].size == (100, 100)


def test_slice_image_smart_crop_and_resizing():
    """验证 smart_crop=True 去缝缩减及目标尺寸缩放"""
    im = create_dummy_grid_image(width=200, height=200, rows=2, cols=2)
    cfg = GridConfig(rows=2, cols=2, row_lines=[100], col_lines=[100])

    frames_resized = slice_image(im, grid_config=cfg, smart_crop=True, target_size=(60, 60))
    assert len(frames_resized) == 4
    assert frames_resized[0].size == (60, 60)

    frames_scaled = slice_image(im, grid_config=cfg, smart_crop=False, scale_factor=0.5)
    assert len(frames_scaled) == 4
    assert frames_scaled[0].size == (50, 50)


def test_slice_image_invalid_coordinates_protection():
    """验证异常混乱分割线时的安全跳过保护"""
    im = Image.new("RGB", (100, 100), (255, 255, 255))
    cfg = GridConfig(rows=2, cols=2, row_lines=[100], col_lines=[100])
    frames = slice_image(im, grid_config=cfg)
    assert len(frames) >= 1


def test_split_grid_image_disk_wrapper(tmp_path):
    """验证 split_grid_image 磁盘落盘包装函数"""
    img_path = tmp_path / "test_input.png"
    im = create_dummy_grid_image(width=200, height=200, rows=2, cols=2)
    im.save(img_path)

    out_dir = tmp_path / "output_frames"
    frames = split_grid_image(str(img_path), output_dir=str(out_dir), rows=2, cols=2)
    assert len(frames) == 4
    assert all(Path(f).exists() for f in frames)

    # 文件不存在时抛出 FileNotFoundError
    with pytest.raises(FileNotFoundError):
        split_grid_image("non_existent_img.png")


def test_get_aspect_ratio_info():
    """全量覆盖 13 类标准比例、异常输入、GCD 及浮点比"""
    # 异常输入
    assert get_aspect_ratio_info(0, 100) == ("--:--", "未知")
    assert get_aspect_ratio_info(-10, 50) == ("--:--", "未知")

    # 标准比例
    assert get_aspect_ratio_info(500, 500)[0] == "1:1"
    assert get_aspect_ratio_info(1920, 1080)[0] == "16:9"
    assert get_aspect_ratio_info(1080, 1920)[0] == "9:16"
    assert get_aspect_ratio_info(800, 600)[0] == "4:3"
    assert get_aspect_ratio_info(600, 800)[0] == "3:4"
    assert get_aspect_ratio_info(300, 200)[0] == "3:2"
    assert get_aspect_ratio_info(200, 300)[0] == "2:3"
    assert get_aspect_ratio_info(2100, 900)[0] == "21:9"
    assert get_aspect_ratio_info(900, 2100)[0] == "9:21"
    assert get_aspect_ratio_info(200, 400)[0] == "1:2"
    assert get_aspect_ratio_info(400, 200)[0] == "2:1"
    assert get_aspect_ratio_info(400, 500)[0] == "4:5"
    assert get_aspect_ratio_info(500, 400)[0] == "5:4"

    # 非标准整数比
    r_w, desc_w = get_aspect_ratio_info(19, 7)
    assert r_w == "19:7"
    assert "横向" in desc_w

    r_h, desc_h = get_aspect_ratio_info(7, 19)
    assert r_h == "7:19"
    assert "纵向" in desc_h

    # 浮点比
    r_f1, _ = get_aspect_ratio_info(137, 39)
    assert ":1" in r_f1
    r_f2, _ = get_aspect_ratio_info(39, 137)
    assert "1:" in r_f2


def test_detect_dividers_gutter_center_snapping():
    """验证宽缝隙 (Gutter) 场景下，分割线绝对吸附于物理缝隙正中央 (中位线)"""
    # 构造 200x200 画布，在 x=92..108 (宽度 16px) 放置一条纯白缝隙槽
    im = Image.new("RGB", (200, 200), (30, 30, 30))
    for x in range(92, 108):
        for y in range(200):
            im.putpixel((x, y), (255, 255, 255))

    v_lines = detect_dividers_universal(im, orientation="v", n_grid=2)
    assert len(v_lines) == 1
    # 缝隙区间为 [92, 107]，中点为 99~100
    assert 98 <= v_lines[0] <= 101


def test_detect_dividers_transparent_rgba():
    """验证 RGBA 透明背景拼图素材在透明留白缝隙处的中心吸附"""
    # 构造 200x200 透明画布，左右两侧有不透明色块，中间 x=80..120 为全透明
    im = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    # 左侧色块
    for x in range(0, 80):
        for y in range(200):
            im.putpixel((x, y), (200, 50, 50, 255))
    # 右侧色块
    for x in range(120, 200):
        for y in range(200):
            im.putpixel((x, y), (50, 200, 50, 255))

    v_lines = detect_dividers_universal(im, orientation="v", n_grid=2)
    assert len(v_lines) == 1
    # 透明缝隙 [80, 119]，中心为 99~100
    assert 98 <= v_lines[0] <= 102


def test_calculate_default_grid_auto_snap():
    """验证 calculate_default_grid 配合 auto_snap=True 自动执行波谷吸附"""
    im = Image.new("RGB", (200, 200), (40, 40, 40))
    # 在 x=94..106 绘制 12px 缝隙槽
    for x in range(94, 106):
        for y in range(200):
            im.putpixel((x, y), (255, 255, 255))

    # 1. 普通几何等分
    cfg_normal = calculate_default_grid(img=im, rows=2, cols=2, auto_snap=False)
    assert cfg_normal.col_lines == [100]

    # 2. 智能吸附
    cfg_snap = calculate_default_grid(img=im, rows=2, cols=2, auto_snap=True)
    assert len(cfg_snap.col_lines) == 1
    assert 98 <= cfg_snap.col_lines[0] <= 102

