# -*- coding: utf-8 -*-
"""
Image Grid Splitter & GIF Creator (多帧拆解与 GIF 合成工具)
核心逻辑与底层引擎
"""

import os
import sys
import glob
import re
import argparse
import math
from typing import List, Tuple, Optional
from PIL import Image

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def natural_sort_key(s: str):
    """自然数排序键，确保 'frame_2.png' 排在 'frame_10.png' 前面"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]


def get_aspect_ratio_info(w: int, h: int) -> Tuple[str, str]:
    """
    计算像素分辨率的长宽比例与语义说明。
    :param w: 单帧宽度像素
    :param h: 单帧高度像素
    :return: (ratio_str, desc_str) 例如 ("16:9", "横屏宽屏"), ("1:1", "正方形·经典表情包")
    """
    if w <= 0 or h <= 0:
        return "--:--", "未知"

    r = float(w) / float(h)

    # 常见标准比例数据库 (比例值, 显示标识, 语义标签, 容差)
    standards = [
        (1.0, "1:1", "正方形 · 经典表情包/头像", 0.035),
        (16.0 / 9.0, "16:9", "横屏宽屏 · 视频/壁纸", 0.04),
        (9.0 / 16.0, "9:16", "竖屏满屏 · 手机短视频", 0.04),
        (4.0 / 3.0, "4:3", "标准横屏 · 经典画幅", 0.035),
        (3.0 / 4.0, "3:4", "经典竖屏 · 小红书/海报", 0.035),
        (3.0 / 2.0, "3:2", "相机横幅 · 单反胶片", 0.03),
        (2.0 / 3.0, "2:3", "相机竖幅 · 写真画幅", 0.03),
        (21.0 / 9.0, "21:9", "超宽带鱼屏 · 电影宽荧幕", 0.05),
        (9.0 / 21.0, "9:21", "超长竖屏 · 移动长条", 0.05),
        (1.0 / 2.0, "1:2", "长竖图 · 双倍高", 0.04),
        (2.0 / 1.0, "2:1", "宽全景 · 双倍宽", 0.04),
        (4.0 / 5.0, "4:5", "社交媒体推荐竖图", 0.03),
        (5.0 / 4.0, "5:4", "大画幅传统相片", 0.03),
    ]

    for std_r, ratio_text, desc, tol in standards:
        if abs(r - std_r) <= tol:
            return ratio_text, desc

    # 若不在标准库，尝试计算最简整数比
    g = math.gcd(int(round(w)), int(round(h)))
    simp_w = int(round(w)) // g
    simp_h = int(round(h)) // g
    if simp_w <= 32 and simp_h <= 32:
        ratio_text = f"{simp_w}:{simp_h}"
    else:
        ratio_text = f"{r:.2f}:1" if r >= 1 else f"1:{(1.0 / r):.2f}"

    desc = "横向构图" if w > h else ("纵向长图" if h > w else "正方形")
    return ratio_text, desc


def get_base_dir() -> str:
    """获取程序根目录（处理 PyInstaller 冻结打包情况）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def get_default_output_dir() -> str:
    """获取默认 output 目录，包含只读权限安全降级"""
    base = get_base_dir()
    candidate = os.path.join(base, "output")
    try:
        os.makedirs(candidate, exist_ok=True)
        test_file = os.path.join(candidate, ".perm_test")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        return candidate
    except Exception:
        fallback = os.path.join(os.path.expanduser("~"), "Pictures", "GifCreater", "output")
        os.makedirs(fallback, exist_ok=True)
        return fallback


def detect_dividers_universal(im: Image.Image, orientation: str = 'v', n_grid: int = 4) -> List[int]:
    """
    全能分割线检测算法：同时支持黑线、白线、细色线以及画面对比度突变分界。
    :param orientation: 'v' 表示垂直分割线(返回x坐标)，'h' 表示水平分割线(返回y坐标)
    :param n_grid: 格子数（如 6 行则有 5 条分割线）
    :return: 各分割线中心像素坐标列表
    """
    w, h = im.size
    dim = w if orientation == 'v' else h
    other_dim = h if orientation == 'v' else w
    n_divs = n_grid - 1
    if n_divs <= 0:
        return []

    # 1. 快速采样统计各行/列的颜色均值、方差及与相邻行/列的颜色阶跃突变
    step = max(1, other_dim // 60)
    line_vars = []
    line_means = []
    for p in range(dim):
        if orientation == 'v':
            samples = [im.getpixel((p, y)) for y in range(0, other_dim, step)]
        else:
            samples = [im.getpixel((x, p)) for x in range(0, other_dim, step)]
        grays = [(r + g + b) / 3.0 for r, g, b in samples[:3]]
        m = sum(grays) / len(grays)
        v = sum((g - m) ** 2 for g in grays) / len(grays)
        line_vars.append(v)
        line_means.append(m)

    line_diffs = [0.0]
    for p in range(1, dim):
        if orientation == 'v':
            diff = sum(abs(im.getpixel((p, y))[0] - im.getpixel((p - 1, y))[0]) for y in range(0, other_dim, step)) / len(samples)
        else:
            diff = sum(abs(im.getpixel((x, p))[0] - im.getpixel((x, p - 1))[0]) for x in range(0, other_dim, step)) / len(samples)
        line_diffs.append(diff)

    cell_len = dim / float(n_grid)
    search_w = int(cell_len * 0.35)  # 允许最大 35% 的非等高/非等宽偏离

    dividers = []
    for k in range(n_divs):
        nom = int(round((k + 1) * cell_len))
        start_p = max(0, nom - search_w)
        end_p = min(dim - 1, nom + search_w)

        best_p = nom
        best_score = -1.0

        for p in range(start_p, end_p + 1):
            v = line_vars[p]
            m = line_means[p]
            diff = line_diffs[p]

            score = diff * 2.0
            if v < 120:  # 整行/整列颜色均匀（说明是人工画的分割线）
                score += (120 - v) * 3.0
                if m < 85 or m > 180:  # 典型黑线（<85）或典型白线（>180）
                    score += 250.0

            if score > best_score:
                best_score = score
                best_p = p

        dividers.append(best_p)

    return dividers


def get_grid_divider_coords(img: Image.Image, rows: int = 4, cols: int = 4, auto_trim_borders: bool = True) -> Tuple[List[int], List[int]]:
    """
    获取网格分割线在图中的像素位置列表 (xs, ys)，用于界面绘制与交互拖拽参考
    """
    w, h = img.size
    if auto_trim_borders:
        xs = detect_dividers_universal(img, orientation='v', n_grid=cols)
        ys = detect_dividers_universal(img, orientation='h', n_grid=rows)
    else:
        cw = w / float(cols)
        xs = [int(round(i * cw)) for i in range(1, cols)]
        rh = h / float(rows)
        ys = [int(round(i * rh)) for i in range(1, rows)]

    return xs, ys


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
    prefix: str = "frame"
) -> List[str]:
    """
    拆解网格图片为单帧独立图片（支持自定义分割线精确裁切）。
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"找不到指定图片文件: {image_path}")

    base_name = os.path.splitext(os.path.basename(image_path))[0]
    if not output_dir:
        output_dir = os.path.join(get_default_output_dir(), "frames", f"{base_name}_frames")

    os.makedirs(output_dir, exist_ok=True)

    img = Image.open(image_path).convert('RGB')
    w, h = img.size

    # 获取/使用列分割线
    if custom_col_divs is not None and len(custom_col_divs) == cols - 1:
        v_lines = sorted(custom_col_divs)
    else:
        v_lines = detect_dividers_universal(img, orientation='v', n_grid=cols) if auto_trim_borders else [int(round(i * w / cols)) for i in range(1, cols)]

    # 获取/使用行分割线
    if custom_row_divs is not None and len(custom_row_divs) == rows - 1:
        h_lines = sorted(custom_row_divs)
    else:
        h_lines = detect_dividers_universal(img, orientation='h', n_grid=rows) if auto_trim_borders else [int(round(i * h / rows)) for i in range(1, rows)]

    # 构建列范围 (x1, x2)
    col_bounds = []
    curr_x = 0
    trim_px = 1 if auto_trim_borders else 0
    for vx in v_lines:
        col_bounds.append((curr_x, max(curr_x, vx - trim_px)))
        curr_x = min(w, vx + 1 + trim_px)
    col_bounds.append((curr_x, w))

    # 构建行范围 (y1, y2)
    row_bounds = []
    curr_y = 0
    for hy in h_lines:
        row_bounds.append((curr_y, max(curr_y, hy - trim_px)))
        curr_y = min(h, hy + 1 + trim_px)
    row_bounds.append((curr_y, h))

    # 计算目标尺寸
    if target_size is None:
        avg_w = int(round(sum(x2 - x1 for x1, x2 in col_bounds) / len(col_bounds) * scale_factor))
        avg_h = int(round(sum(y2 - y1 for y1, y2 in row_bounds) / len(row_bounds) * scale_factor))
        target_size = (avg_w, avg_h)

    frame_files = []
    idx = 1
    for r_idx, (y1, y2) in enumerate(row_bounds):
        for c_idx, (x1, x2) in enumerate(col_bounds):
            if x2 <= x1 or y2 <= y1:
                continue
            cell = img.crop((x1, y1, x2, y2))
            if target_size:
                cell = cell.resize(target_size, Image.Resampling.LANCZOS)

            frame_filename = f"{prefix}_{idx:02d}.png"
            frame_path = os.path.join(output_dir, frame_filename)
            cell.save(frame_path, format="PNG")
            frame_files.append(frame_path)
            idx += 1

    return frame_files


def create_animation(
    frame_paths_or_dir: any,
    output_path: str,
    duration: int = 350,
    last_frame_pause: int = 1500,
    loop: int = 0,
    preset: str = "original",
    boomerang: bool = False,
    resize: Optional[Tuple[int, int]] = None
) -> str:
    """
    通用动图合成（支持 原画GIF、微信表情包标准、WebP、乒乓往复循环）。
    """
    if isinstance(frame_paths_or_dir, str):
        if os.path.isdir(frame_paths_or_dir):
            patterns = ["*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp", "*.PNG", "*.JPG", "*.JPEG", "*.WEBP", "*.BMP"]
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
        frame_paths = sorted(frame_paths_or_dir, key=natural_sort_key)
    else:
        raise TypeError("frame_paths_or_dir 必须为路径列表或目录字符串")

    if not frame_paths:
        raise ValueError("单帧图片列表为空，无法合成动图")

    if boomerang and len(frame_paths) > 2:
        expanded_paths = list(frame_paths) + list(reversed(frame_paths[1:-1]))
    else:
        expanded_paths = list(frame_paths)

    images = [Image.open(p).convert('RGBA' if preset == 'webp' else 'RGB') for p in expanded_paths]

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
    elif resize:
        images = [im.resize(resize, Image.Resampling.LANCZOS) for im in images]
    else:
        first_size = images[0].size
        images = [im.resize(first_size, Image.Resampling.LANCZOS) if im.size != first_size else im for im in images]

    num_frames = len(images)
    durations = [duration] * num_frames
    if not boomerang and last_frame_pause > 0 and num_frames > 0:
        durations[-1] = last_frame_pause

    output_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(output_dir, exist_ok=True)

    if preset == "webp" or output_path.lower().endswith(".webp"):
        images[0].save(
            output_path,
            format="WEBP",
            save_all=True,
            append_images=images[1:],
            duration=durations,
            loop=loop,
            quality=85,
            method=6
        )
        return os.path.abspath(output_path)

    if preset == "wechat":
        for colors in [128, 96, 64, 48]:
            p_images = [im.convert('P', palette=Image.Palette.ADAPTIVE, colors=colors) for im in images]
            p_images[0].save(
                output_path,
                save_all=True,
                append_images=p_images[1:],
                duration=durations,
                loop=loop,
                optimize=True
            )
            file_size = os.path.getsize(output_path)
            if file_size <= 500 * 1024:
                break
    else:
        images[0].save(
            output_path,
            save_all=True,
            append_images=images[1:],
            duration=durations,
            loop=loop,
            optimize=False
        )

    return os.path.abspath(output_path)


def create_gif(frame_paths_or_dir, output_gif_path, duration=350, last_frame_pause=1500, loop=0, resize=None):
    return create_animation(
        frame_paths_or_dir=frame_paths_or_dir,
        output_path=output_gif_path,
        duration=duration,
        last_frame_pause=last_frame_pause,
        loop=loop,
        preset="original",
        boomerang=False,
        resize=resize
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
    boomerang: bool = False
) -> Tuple[List[str], str]:
    """
    一键拆解并合成动图
    """
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
        scale_factor=scale_factor
    )

    result_path = create_animation(
        frame_paths_or_dir=frames,
        output_path=output_gif_path,
        duration=duration,
        last_frame_pause=last_frame_pause,
        preset=preset,
        boomerang=boomerang
    )

    return frames, result_path


def main():
    parser = argparse.ArgumentParser(description="多帧图片拆解与 GIF 动图合成工具")
    parser.add_argument("-i", "--input", help="输入的网格拼图文件路径（如 16 帧大图）")
    parser.add_argument("-o", "--output-dir", help="保存拆解后单帧图片的目录")
    parser.add_argument("-g", "--gif", help="导出的 GIF 动图路径")
    parser.add_argument("-r", "--rows", type=int, default=4, help="网格行数（默认 4）")
    parser.add_argument("-c", "--cols", type=int, default=4, help="网格列数（默认 4）")
    parser.add_argument("-d", "--duration", type=int, default=350, help="常规帧播放时长毫秒（默认 350ms）")
    parser.add_argument("-p", "--last-pause", type=int, default=1500, help="最后一帧停留时长毫秒（默认 1500ms）")
    parser.add_argument("--scale", type=float, default=1.0, help="输出帧的缩放倍率（默认 1.0 原寸）")
    parser.add_argument("--preset", choices=["original", "wechat", "webp"], default="original", help="导出预设目标")
    parser.add_argument("--boomerang", action="store_true", help="启用乒乓往复循环")
    parser.add_argument("--no-trim", action="store_true", help="关闭智能去除黑边/分界线")
    parser.add_argument("--gui", action="store_true", help="启动图形化界面")

    args = parser.parse_args()

    if args.gui or len(sys.argv) == 1:
        try:
            import gui
            gui.launch_gui(args.input)
        except Exception as e:
            print(f"启动图形化界面异常: {e}")
            if not args.input:
                parser.print_help()
        return

    if not args.input:
        print("提示: 请使用 -i 参数指定输入图片路径，或运行 --gui 打开图形界面。")
        parser.print_help()
        sys.exit(1)

    print(f"正在处理图片: {args.input}")
    frames, out_path = process_image_to_gif(
        image_path=args.input,
        output_gif_path=args.gif,
        output_frames_dir=args.output_dir,
        rows=args.rows,
        cols=args.cols,
        duration=args.duration,
        last_frame_pause=args.last_pause,
        auto_trim_borders=not args.no_trim,
        scale_factor=args.scale,
        preset=args.preset,
        boomerang=args.boomerang
    )

    print(f"成功拆解 {len(frames)} 帧图片，保存至: {os.path.dirname(frames[0])}")
    print(f"成功合成动图，保存至: {out_path}")


if __name__ == "__main__":
    main()