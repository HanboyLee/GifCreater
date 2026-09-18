# -*- coding: utf-8 -*-
"""
tests/integration/test_pipeline.py
集成测试: 纯内存端到端全流程数据流集成测试 (E2E Memory Pipeline)
"""

import io
from PIL import Image, ImageSequence
from src.gifcreater.core.bounds import detect_bounds
from src.gifcreater.core.slicer import calculate_default_grid, slice_image
from src.gifcreater.core.compressor import compress_wechat_gif
from src.gifcreater.core.exporter import export_gif, export_webp
from tests.fixtures.mock_images import create_dummy_grid_image, create_border_probe_image


def test_e2e_memory_pipeline_all_modes():
    """
    【端到端全链路闭环测试】
    1. 生成包含黑边与 4x4 分割线的微型画布 (480x480)；
    2. 执行主体边界探测 (detect_bounds) 剔除留白；
    3. 基于探测包围盒推导 4x4 网格配置 (calculate_default_grid)；
    4. 执行纯内存切片 (slice_image)，产出 16 张单帧；
    5. 模拟用户在时间轴胶卷中剔除第 0 帧与第 5 帧，剩余 14 帧；
    6. 模式 A: 微信表情包压缩 -> 严格断言 <= 512,000 字节且最长边 <= 240px；
    7. 模式 B: Boomerang 乒乓往复导出 -> 验证帧数展开为 14 + 12 = 26 帧；
    8. 模式 C: 全彩 WebP 动图导出 -> 验证 RIFF/WEBP 头。
    """
    # 步骤 1: 内存合成 480x480 大图 (外围带 20px 纯黑边框，内部划分为 4x4 网格)
    canvas = create_border_probe_image(
        width=480,
        height=480,
        border_width=20,
        border_color=(0, 0, 0),
        fill_color=(230, 230, 230),
    )
    # 在主体内部绘制微型网格线
    grid_canvas = create_dummy_grid_image(
        width=440,
        height=440,
        rows=4,
        cols=4,
        line_color=(50, 50, 50),
        cell_patterns=True,
    )
    canvas.paste(grid_canvas, (20, 20))

    # 步骤 2: 智能边界探测
    bounds = detect_bounds(canvas, tolerance=15)
    left, top, right, bottom = bounds
    assert 18 <= left <= 22
    assert 18 <= top <= 22
    assert 458 <= right <= 462
    assert 458 <= bottom <= 462

    # 步骤 3: 基于包围盒计算 4x4 网格
    subj_w = right - left
    subj_h = bottom - top
    grid_cfg = calculate_default_grid(subj_w, subj_h, rows=4, cols=4, bounds=bounds)
    assert grid_cfg.total_cells() == 16
    assert len(grid_cfg.col_lines) == 3
    assert len(grid_cfg.row_lines) == 3

    # 步骤 4: 内存切片
    raw_frames = slice_image(canvas, grid_config=grid_cfg, smart_crop=True)
    assert len(raw_frames) == 16
    assert all(isinstance(f, Image.Image) for f in raw_frames)

    # 步骤 5: 胶卷废帧剔除联动 (剔除索引 0 和 5)
    excluded_indices = {0, 5}
    active_frames = [f for idx, f in enumerate(raw_frames) if idx not in excluded_indices]
    assert len(active_frames) == 14

    durations = [120] * len(active_frames)

    # 步骤 6 [模式 A]: 微信表情包 <=500KB & <=240px 验证
    wechat_bytes = compress_wechat_gif(active_frames, durations)
    assert isinstance(wechat_bytes, bytes)
    assert len(wechat_bytes) <= 500 * 1024, f"集成流水线微信表情包体积超标: {len(wechat_bytes)} 字节"
    with Image.open(io.BytesIO(wechat_bytes)) as im:
        assert max(im.size) <= 240
        assert im.format == "GIF"

    # 步骤 7 [模式 B]: Boomerang 往复循环导出
    boom_bytes = export_gif(active_frames, durations, boomerang=True)
    with Image.open(io.BytesIO(boom_bytes)) as im:
        expanded_frames = [f.copy() for f in ImageSequence.Iterator(im)]
        assert len(expanded_frames) == 26

    # 步骤 8 [模式 C]: 高保真 WebP 动图导出
    webp_bytes = export_webp(active_frames, durations)
    assert webp_bytes[:4] == b"RIFF"
    assert webp_bytes[8:12] == b"WEBP"
