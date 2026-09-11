import os
import sys
import tempfile
import pytest
from PIL import Image, ImageDraw

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import gif_tool


def create_dummy_grid_image(width=400, height=400, rows=2, cols=2, line_color=(0, 0, 0)):
    """在内存中生成包含分割线的小尺寸测试图，避免外部大文件依赖"""
    im = Image.new("RGB", (width, height), color=(240, 240, 240))
    draw = ImageDraw.Draw(im)
    col_w = width // cols
    for c in range(1, cols):
        x = c * col_w
        draw.line([(x, 0), (x, height)], fill=line_color, width=2)
    row_h = height // rows
    for r in range(1, rows):
        y = r * row_h
        draw.line([(0, y), (width, y)], fill=line_color, width=2)
    return im


def test_natural_sort_key():
    keys = ["frame_10.png", "frame_2.png", "frame_1.png", "frame_20.png"]
    sorted_keys = sorted(keys, key=gif_tool.natural_sort_key)
    assert sorted_keys == ["frame_1.png", "frame_2.png", "frame_10.png", "frame_20.png"]


def test_get_aspect_ratio_info():
    # 边界情况
    assert gif_tool.get_aspect_ratio_info(0, 100) == ("--:--", "未知")
    assert gif_tool.get_aspect_ratio_info(100, 0) == ("--:--", "未知")

    # 常见标准比例
    assert gif_tool.get_aspect_ratio_info(500, 500)[0] == "1:1"
    assert gif_tool.get_aspect_ratio_info(1920, 1080)[0] == "16:9"
    assert gif_tool.get_aspect_ratio_info(1080, 1920)[0] == "9:16"
    assert gif_tool.get_aspect_ratio_info(800, 600)[0] == "4:3"
    assert gif_tool.get_aspect_ratio_info(600, 800)[0] == "3:4"
    assert gif_tool.get_aspect_ratio_info(300, 200)[0] == "3:2"
    assert gif_tool.get_aspect_ratio_info(200, 300)[0] == "2:3"
    assert gif_tool.get_aspect_ratio_info(2100, 900)[0] == "21:9"
    assert gif_tool.get_aspect_ratio_info(900, 2100)[0] == "9:21"
    assert gif_tool.get_aspect_ratio_info(200, 400)[0] == "1:2"
    assert gif_tool.get_aspect_ratio_info(400, 200)[0] == "2:1"
    assert gif_tool.get_aspect_ratio_info(400, 500)[0] == "4:5"
    assert gif_tool.get_aspect_ratio_info(500, 400)[0] == "5:4"

    # 非标准比例测试 (触发最简整数比逻辑)
    ratio_w, desc_w = gif_tool.get_aspect_ratio_info(19, 7)
    assert ratio_w == "19:7"
    assert "横向" in desc_w

    ratio_h, desc_h = gif_tool.get_aspect_ratio_info(7, 19)
    assert ratio_h == "7:19"
    assert "纵向" in desc_h

    # 极大不可化简比例 (触发浮点比逻辑)
    r_big_w, _ = gif_tool.get_aspect_ratio_info(137, 39)
    assert ":1" in r_big_w

    r_big_h, _ = gif_tool.get_aspect_ratio_info(39, 137)
    assert "1:" in r_big_h


def test_get_base_dir_and_default_output(monkeypatch, tmp_path):
    # 正常运行
    base_dir = gif_tool.get_base_dir()
    assert os.path.exists(base_dir)
    out_dir = gif_tool.get_default_output_dir()
    assert os.path.exists(out_dir)

    # 模拟打包 frozen 状态
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "app.exe"))
    frozen_base = gif_tool.get_base_dir()
    assert frozen_base == str(tmp_path)


def test_detect_dividers_universal():
    # 测试 n_grid <= 1
    im = create_dummy_grid_image(200, 200, rows=1, cols=1)
    assert gif_tool.detect_dividers_universal(im, orientation='v', n_grid=1) == []

    # 测试 2x2 检测
    im2 = create_dummy_grid_image(200, 200, rows=2, cols=2, line_color=(0, 0, 0))
    v_divs = gif_tool.detect_dividers_universal(im2, orientation='v', n_grid=2)
    h_divs = gif_tool.detect_dividers_universal(im2, orientation='h', n_grid=2)
    assert len(v_divs) == 1
    assert len(h_divs) == 1
    assert 90 <= v_divs[0] <= 110
    assert 90 <= h_divs[0] <= 110


def test_get_grid_divider_coords():
    im = create_dummy_grid_image(300, 300, rows=3, cols=3)
    # 自动吸附
    xs, ys = gif_tool.get_grid_divider_coords(im, rows=3, cols=3, auto_trim_borders=True)
    assert len(xs) == 2
    assert len(ys) == 2

    # 均匀等分
    xs_no_trim, ys_no_trim = gif_tool.get_grid_divider_coords(im, rows=3, cols=3, auto_trim_borders=False)
    assert xs_no_trim == [100, 200]
    assert ys_no_trim == [100, 200]


def test_split_grid_image_and_errors(tmp_path):
    with pytest.raises(FileNotFoundError):
        gif_tool.split_grid_image("non_existent_file.png")

    img_file = tmp_path / "test_grid.png"
    im = create_dummy_grid_image(200, 200, rows=2, cols=2)
    im.save(img_file)

    # 1. 默认 output_dir=None
    frames_default = gif_tool.split_grid_image(str(img_file), rows=2, cols=2)
    assert len(frames_default) == 4

    # 2. 自定义 output_dir
    frames = gif_tool.split_grid_image(str(img_file), output_dir=str(tmp_path / "frames"), rows=2, cols=2)
    assert len(frames) == 4
    for f in frames:
        assert os.path.exists(f)

    # 3. 自定义分割线与非等分裁切
    custom_frames = gif_tool.split_grid_image(
        str(img_file),
        output_dir=str(tmp_path / "custom_frames"),
        rows=2,
        cols=2,
        auto_trim_borders=False,
        custom_col_divs=[100],
        custom_row_divs=[100],
        target_size=(50, 50),
        scale_factor=0.5
    )
    assert len(custom_frames) == 4
    with Image.open(custom_frames[0]) as cell:
        assert cell.size == (50, 50)


def test_create_animation_types_and_errors(tmp_path):
    with pytest.raises(TypeError):
        gif_tool.create_animation(12345, str(tmp_path / "out.gif"))

    with pytest.raises(ValueError):
        gif_tool.create_animation(str(tmp_path / "not_dir"), str(tmp_path / "out.gif"))

    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    with pytest.raises(ValueError):
        gif_tool.create_animation(str(empty_dir), str(tmp_path / "out.gif"))

    with pytest.raises(ValueError):
        gif_tool.create_animation([], str(tmp_path / "out.gif"))

    # 生成 3 帧测试图片
    frame_paths = []
    for i in range(3):
        p = tmp_path / f"frame_{i}.png"
        Image.new("RGB", (100, 100), color=(i * 80, 50, 50)).save(p)
        frame_paths.append(str(p))

    # 1. 正常 GIF
    out_gif = tmp_path / "anim.gif"
    res = gif_tool.create_animation(frame_paths, str(out_gif), duration=200, last_frame_pause=1000)
    assert os.path.exists(res)

    # 2. 目录作为入参
    dir_gif = tmp_path / "from_dir.gif"
    res_dir = gif_tool.create_animation(str(tmp_path), str(dir_gif))
    assert os.path.exists(res_dir)

    # 3. Boomerang 往复乒乓
    boom_gif = tmp_path / "boomerang.gif"
    res_boom = gif_tool.create_animation(frame_paths, str(boom_gif), boomerang=True)
    assert os.path.exists(res_boom)

    # 4. WebP 格式
    webp_path = tmp_path / "anim.webp"
    res_webp = gif_tool.create_animation(frame_paths, str(webp_path), preset="webp")
    assert os.path.exists(res_webp)

    # 5. 微信表情包 preset (尺寸缩放 + 调色板自适应)
    wechat_gif = tmp_path / "wechat.gif"
    res_wechat = gif_tool.create_animation(frame_paths, str(wechat_gif), preset="wechat", duration=200)
    assert os.path.exists(res_wechat)

    # 6. 指定 resize
    resize_gif = tmp_path / "resized.gif"
    res_resize = gif_tool.create_animation(frame_paths, str(resize_gif), resize=(60, 60))
    assert os.path.exists(res_resize)

    # 7. create_gif 快捷函数
    cg_path = tmp_path / "cg.gif"
    res_cg = gif_tool.create_gif(frame_paths, str(cg_path))
    assert os.path.exists(res_cg)


def test_process_image_to_gif(tmp_path):
    img_file = tmp_path / "test_full_grid.png"
    im = create_dummy_grid_image(200, 200, rows=2, cols=2)
    im.save(img_file)

    # 1. 显式指定输出路径
    out_gif = tmp_path / "full_pipeline.gif"
    out_frames = tmp_path / "my_frames"
    frames, gif_res = gif_tool.process_image_to_gif(
        image_path=str(img_file),
        output_gif_path=str(out_gif),
        output_frames_dir=str(out_frames),
        rows=2,
        cols=2,
        preset="original",
        boomerang=False
    )
    assert len(frames) == 4
    assert os.path.exists(gif_res)

    # 2. 默认输出路径 (webp + boomerang 分支测试)
    frames_def, gif_def = gif_tool.process_image_to_gif(
        image_path=str(img_file),
        rows=2,
        cols=2,
        preset="webp",
        boomerang=True
    )
    assert len(frames_def) == 4
    assert os.path.exists(gif_def)


def test_main_cli_and_exceptions(monkeypatch, tmp_path):
    img_file = tmp_path / "cli_grid.png"
    im = create_dummy_grid_image(200, 200, rows=2, cols=2)
    im.save(img_file)

    out_gif = tmp_path / "cli_out.gif"
    out_dir = tmp_path / "cli_frames"

    # 正常 CLI 传参调用
    test_args = [
        "gif_tool.py",
        "-i", str(img_file),
        "-o", str(out_dir),
        "-g", str(out_gif),
        "-r", "2",
        "-c", "2",
        "-d", "100"
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    gif_tool.main()
    assert os.path.exists(out_gif)

    # 未提供 input 参数时退出
    monkeypatch.setattr(sys, "argv", ["gif_tool.py", "-r", "2"])
    with pytest.raises(SystemExit):
        gif_tool.main()
