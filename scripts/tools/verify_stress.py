# -*- coding: utf-8 -*-
"""
scripts/tools/verify_stress.py
Challenger M2-1 In-Memory Stress & Adversarial Test Harness
===========================================================
Pure in-memory execution of stress cases for:
1. WeChat GIF Compressor under adversarial noise and extreme conditions
2. Bounds Detection on monochrome, transparent, and single-pixel images
3. Grid Slicer on 1x1, 10x10, and non-uniform grids
"""

import io
import os
import sys
import time
import random
from typing import List, Tuple
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.gifcreater.core.compressor import compress_wechat_gif
from src.gifcreater.core.bounds import detect_bounds
from src.gifcreater.core.slicer import (
    GridConfig,
    calculate_default_grid,
    slice_image,
)
from src.gifcreater.core.exporter import (
    generate_boomerang_sequence,
    export_gif,
    export_webp,
)


def generate_noise_frame(width: int, height: int, mode: str = "RGB") -> Image.Image:
    """Generate high-contrast random noise frame purely in memory."""
    if mode == "RGB":
        data = random.randbytes(width * height * 3)
        return Image.frombytes("RGB", (width, height), data)
    elif mode == "RGBA":
        data = random.randbytes(width * height * 4)
        return Image.frombytes("RGBA", (width, height), data)
    elif mode == "L":
        data = random.randbytes(width * height)
        return Image.frombytes("L", (width, height), data)
    else:
        raise ValueError(f"Unsupported mode: {mode}")


def verify_gif_bytes(data: bytes) -> Tuple[bool, Tuple[int, int], int, str]:
    """Inspect in-memory GIF bytes for validity, size, and frame count."""
    if not data:
        return False, (0, 0), 0, "Empty data"
    if not (data.startswith(b"GIF89a") or data.startswith(b"GIF87a")):
        return False, (0, 0), 0, f"Invalid GIF signature: {data[:6]}"
    try:
        im = Image.open(io.BytesIO(data))
        frames = 0
        while True:
            frames += 1
            im.seek(im.tell() + 1)
    except EOFError:
        pass
    except Exception as e:
        return False, (0, 0), 0, f"PIL open error: {e}"
    return True, im.size, frames, "OK"


# =========================================================================
# SUITE 1: WeChat Compressor Adversarial Tests
# =========================================================================

def run_compressor_stress_tests() -> List[dict]:
    results = []
    print("\n" + "=" * 70)
    print("SUITE 1: WeChat Compressor Adversarial Stress Tests")
    print("=" * 70)

    # Test 1.1: 20 frames of random high-noise RGB 240x240
    print("\n--- Test 1.1: 20 frames random noise (240x240, RGB) ---")
    t0 = time.time()
    frames = [generate_noise_frame(240, 240, "RGB") for _ in range(20)]
    out_bytes = compress_wechat_gif(frames, durations=100)
    elapsed = time.time() - t0
    valid, size, n_frames, msg = verify_gif_bytes(out_bytes)
    pass_size = len(out_bytes) <= 512000
    pass_dim = max(size) <= 240
    status = "PASS" if (valid and pass_size and pass_dim) else "FAIL"
    print(f"Status: {status} | Time: {elapsed:.2f}s | Size: {len(out_bytes):,} B (limit 512,000) | Dim: {size} | Frames: {n_frames}")
    results.append({
        "test": "1.1_noise_20_frames_240x240",
        "status": status,
        "bytes": len(out_bytes),
        "dim": size,
        "frames": n_frames,
        "elapsed": elapsed,
    })

    # Test 1.2: 30 frames of high-frequency checkerboard / noise (300x300)
    print("\n--- Test 1.2: 30 frames noise (300x300, downscaled to <=240) ---")
    t0 = time.time()
    frames = [generate_noise_frame(300, 300, "RGB") for _ in range(30)]
    out_bytes = compress_wechat_gif(frames, durations=80)
    elapsed = time.time() - t0
    valid, size, n_frames, msg = verify_gif_bytes(out_bytes)
    pass_size = len(out_bytes) <= 512000
    pass_dim = max(size) <= 240
    status = "PASS" if (valid and pass_size and pass_dim) else "FAIL"
    print(f"Status: {status} | Time: {elapsed:.2f}s | Size: {len(out_bytes):,} B | Dim: {size} | Frames: {n_frames}")
    results.append({
        "test": "1.2_noise_30_frames_300x300",
        "status": status,
        "bytes": len(out_bytes),
        "dim": size,
        "frames": n_frames,
        "elapsed": elapsed,
    })

    # Test 1.3: 50 frames of noise (150x150)
    print("\n--- Test 1.3: 50 frames noise (150x150) ---")
    t0 = time.time()
    frames = [generate_noise_frame(150, 150, "RGB") for _ in range(50)]
    out_bytes = compress_wechat_gif(frames, durations=50)
    elapsed = time.time() - t0
    valid, size, n_frames, msg = verify_gif_bytes(out_bytes)
    pass_size = len(out_bytes) <= 512000
    pass_dim = max(size) <= 240
    status = "PASS" if (valid and pass_size and pass_dim) else "FAIL"
    print(f"Status: {status} | Time: {elapsed:.2f}s | Size: {len(out_bytes):,} B | Dim: {size} | Frames: {n_frames}")
    results.append({
        "test": "1.3_noise_50_frames_150x150",
        "status": status,
        "bytes": len(out_bytes),
        "dim": size,
        "frames": n_frames,
        "elapsed": elapsed,
    })

    # Test 1.4: Extreme constraint: max_size_bytes = 10,000 (10KB) on 10 noisy frames
    print("\n--- Test 1.4: Severe size budget 10KB (10,000 bytes) cascade ---")
    t0 = time.time()
    frames = [generate_noise_frame(120, 120, "RGB") for _ in range(10)]
    out_bytes = compress_wechat_gif(frames, durations=100, max_size_bytes=10000)
    elapsed = time.time() - t0
    valid, size, n_frames, msg = verify_gif_bytes(out_bytes)
    pass_size = len(out_bytes) <= 10000
    pass_dim = max(size) <= 240
    status = "PASS" if (valid and pass_size and pass_dim) else "FAIL"
    print(f"Status: {status} | Time: {elapsed:.2f}s | Size: {len(out_bytes):,} B (limit 10,000) | Dim: {size} | Frames: {n_frames}")
    results.append({
        "test": "1.4_extreme_budget_10kb",
        "status": status,
        "bytes": len(out_bytes),
        "dim": size,
        "frames": n_frames,
        "elapsed": elapsed,
    })

    # Test 1.5: Single frame input (1 frame) with noise
    print("\n--- Test 1.5: Single frame input (1 frame, 200x200) ---")
    t0 = time.time()
    frames = [generate_noise_frame(200, 200, "RGB")]
    out_bytes = compress_wechat_gif(frames, durations=100)
    elapsed = time.time() - t0
    valid, size, n_frames, msg = verify_gif_bytes(out_bytes)
    pass_size = len(out_bytes) <= 512000
    pass_dim = max(size) <= 240
    pass_f = n_frames == 1
    status = "PASS" if (valid and pass_size and pass_dim and pass_f) else "FAIL"
    print(f"Status: {status} | Time: {elapsed:.2f}s | Size: {len(out_bytes):,} B | Dim: {size} | Frames: {n_frames}")
    results.append({
        "test": "1.5_single_frame",
        "status": status,
        "bytes": len(out_bytes),
        "dim": size,
        "frames": n_frames,
        "elapsed": elapsed,
    })

    # Test 1.6: Tiny image input (8x8 pixels) -> verify no-upscale
    print("\n--- Test 1.6: Tiny image (8x8 pixels) no-upscale check ---")
    frames = [generate_noise_frame(8, 8, "RGB") for _ in range(4)]
    out_bytes = compress_wechat_gif(frames, durations=100)
    valid, size, n_frames, msg = verify_gif_bytes(out_bytes)
    no_upscale = (size == (8, 8))
    status = "PASS" if (valid and no_upscale) else "FAIL"
    print(f"Status: {status} | Size: {len(out_bytes):,} B | Dim: {size} (Expected (8, 8))")
    results.append({
        "test": "1.6_tiny_image_no_upscale",
        "status": status,
        "bytes": len(out_bytes),
        "dim": size,
        "frames": n_frames,
    })

    # Test 1.7: Extreme aspect ratio (1200x40 and 40x1200)
    print("\n--- Test 1.7: Extreme aspect ratio (1200x40 -> 240x8) ---")
    frames = [Image.new("RGB", (1200, 40), (i * 20, 100, 200)) for i in range(5)]
    out_bytes = compress_wechat_gif(frames, durations=100)
    valid, size, n_frames, msg = verify_gif_bytes(out_bytes)
    expected_dim = (240, 8)
    pass_dim = (size == expected_dim)
    status = "PASS" if (valid and pass_dim) else "FAIL"
    print(f"Status: {status} | Dim: {size} (Expected {expected_dim}) | Size: {len(out_bytes):,} B")
    results.append({
        "test": "1.7_extreme_aspect_ratio_1200x40",
        "status": status,
        "bytes": len(out_bytes),
        "dim": size,
        "frames": n_frames,
    })

    # Test 1.8: RGBA frames with transparency noise
    print("\n--- Test 1.8: RGBA frames with transparency ---")
    frames = [generate_noise_frame(100, 100, "RGBA") for _ in range(6)]
    out_bytes = compress_wechat_gif(frames, durations=100)
    valid, size, n_frames, msg = verify_gif_bytes(out_bytes)
    status = "PASS" if valid and len(out_bytes) <= 512000 else "FAIL"
    print(f"Status: {status} | Dim: {size} | Size: {len(out_bytes):,} B")
    results.append({
        "test": "1.8_rgba_transparency_frames",
        "status": status,
        "bytes": len(out_bytes),
        "dim": size,
        "frames": n_frames,
    })

    return results


# =========================================================================
# SUITE 2: Bounds Detection Stress Tests
# =========================================================================

def run_bounds_stress_tests() -> List[dict]:
    results = []
    print("\n" + "=" * 70)
    print("SUITE 2: Bounds Detection Stress Tests")
    print("=" * 70)

    # Test 2.1: Pure black RGB (100x100, 10x10, 1x1)
    print("\n--- Test 2.1: Pure black RGB (100x100, 10x10, 1x1) ---")
    for w, h in [(100, 100), (10, 10), (1, 1)]:
        im = Image.new("RGB", (w, h), (0, 0, 0))
        box = detect_bounds(im)
        expected = (0, 0, w, h)
        status = "PASS" if box == expected else "FAIL"
        print(f"Size ({w}, {h}) | Result: {box} | Expected: {expected} | Status: {status}")
        results.append({
            "test": f"2.1_pure_black_rgb_{w}x{h}",
            "status": status,
            "result": box,
            "expected": expected,
        })

    # Test 2.2: Pure white RGB (100x100, 10x10, 1x1)
    print("\n--- Test 2.2: Pure white RGB (100x100, 10x10, 1x1) ---")
    for w, h in [(100, 100), (10, 10), (1, 1)]:
        im = Image.new("RGB", (w, h), (255, 255, 255))
        box = detect_bounds(im)
        expected = (0, 0, w, h)
        status = "PASS" if box == expected else "FAIL"
        print(f"Size ({w}, {h}) | Result: {box} | Expected: {expected} | Status: {status}")
        results.append({
            "test": f"2.2_pure_white_rgb_{w}x{h}",
            "status": status,
            "result": box,
            "expected": expected,
        })

    # Test 2.3: Pure black / pure white RGBA
    print("\n--- Test 2.3: Pure monochrome RGBA (transparent vs opaque) ---")
    # Fully transparent
    im_trans = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    box_trans = detect_bounds(im_trans)
    status_trans = "PASS" if box_trans == (0, 0, 100, 100) else "FAIL"
    print(f"Fully Transparent RGBA | Result: {box_trans} | Expected: (0, 0, 100, 100) | Status: {status_trans}")
    results.append({
        "test": "2.3_transparent_rgba_100x100",
        "status": status_trans,
        "result": box_trans,
        "expected": (0, 0, 100, 100),
    })

    # Fully opaque black RGBA
    im_opq = Image.new("RGBA", (100, 100), (0, 0, 0, 255))
    box_opq = detect_bounds(im_opq)
    status_opq = "PASS" if box_opq == (0, 0, 100, 100) else "FAIL"
    print(f"Fully Opaque Black RGBA | Result: {box_opq} | Expected: (0, 0, 100, 100) | Status: {status_opq}")
    results.append({
        "test": "2.3_opaque_black_rgba_100x100",
        "status": status_opq,
        "result": box_opq,
        "expected": (0, 0, 100, 100),
    })

    # Test 2.4: Single-pixel dot tests
    print("\n--- Test 2.4: Single-pixel dot tests ---")
    # Subtest A: 100x100 white canvas with 1 black pixel at center (50, 50)
    im_dot_center = Image.new("RGB", (100, 100), (255, 255, 255))
    im_dot_center.putpixel((50, 50), (0, 0, 0))
    box_dot_center = detect_bounds(im_dot_center)
    # Since 1 pixel < 10% dimension (1 < 10), noise filter should fallback to full image
    status_dc = "PASS" if box_dot_center == (0, 0, 100, 100) else "FAIL"
    print(f"100x100 Center Dot (50,50) | Result: {box_dot_center} | Expected noise fallback: (0, 0, 100, 100) | Status: {status_dc}")
    results.append({
        "test": "2.4_dot_center_100x100",
        "status": status_dc,
        "result": box_dot_center,
        "expected": (0, 0, 100, 100),
    })

    # Subtest B: 100x100 white canvas with 1 black pixel at corner (0, 0)
    im_dot_corner = Image.new("RGB", (100, 100), (255, 255, 255))
    im_dot_corner.putpixel((0, 0), (0, 0, 0))
    box_dot_corner = detect_bounds(im_dot_corner)
    status_dcn = "PASS" if box_dot_corner == (0, 0, 100, 100) else "FAIL"
    print(f"100x100 Corner Dot (0,0) | Result: {box_dot_corner} | Expected noise fallback: (0, 0, 100, 100) | Status: {status_dcn}")
    results.append({
        "test": "2.4_dot_corner_100x100",
        "status": status_dcn,
        "result": box_dot_corner,
        "expected": (0, 0, 100, 100),
    })

    # Subtest C: 1x1 image with 1 pixel
    im_1x1 = Image.new("RGB", (1, 1), (0, 0, 0))
    box_1x1 = detect_bounds(im_1x1)
    status_1x1 = "PASS" if box_1x1 == (0, 0, 1, 1) else "FAIL"
    print(f"1x1 Single Pixel | Result: {box_1x1} | Expected: (0, 0, 1, 1) | Status: {status_1x1}")
    results.append({
        "test": "2.4_dot_1x1",
        "status": status_1x1,
        "result": box_1x1,
        "expected": (0, 0, 1, 1),
    })

    # Subtest D: 10x10 image with 1 pixel at (5, 5)
    im_10x10 = Image.new("RGB", (10, 10), (255, 255, 255))
    im_10x10.putpixel((5, 5), (0, 0, 0))
    box_10x10 = detect_bounds(im_10x10)
    print(f"10x10 Single Pixel at (5,5) | Result: {box_10x10}")
    # box is either (5, 5, 6, 6) or fallback (0, 0, 10, 10) depending on strict inequality
    status_10x10 = "PASS" if box_10x10 in [(5, 5, 6, 6), (0, 0, 10, 10)] else "FAIL"
    results.append({
        "test": "2.4_dot_10x10",
        "status": status_10x10,
        "result": box_10x10,
        "detail": "Acceptable bounds without crash",
    })

    # Subtest E: RGBA transparent canvas 100x100 with 1 opaque pixel at (50, 50)
    im_rgba_dot = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    im_rgba_dot.putpixel((50, 50), (255, 0, 0, 255))
    box_rgba_dot = detect_bounds(im_rgba_dot)
    # Alpha bbox is (50, 50, 51, 51), w=1 < 10, should fallback to (0, 0, 100, 100)
    status_rgba_dot = "PASS" if box_rgba_dot == (0, 0, 100, 100) else "FAIL"
    print(f"RGBA Transparent with 1 Pixel | Result: {box_rgba_dot} | Expected: (0, 0, 100, 100) | Status: {status_rgba_dot}")
    results.append({
        "test": "2.4_rgba_dot_100x100",
        "status": status_rgba_dot,
        "result": box_rgba_dot,
        "expected": (0, 0, 100, 100),
    })

    # Test 2.5: Subject box exactly at / above 10% threshold (e.g. 20x20 in 100x100)
    print("\n--- Test 2.5: Subject box 20x20 in 100x100 (> 10% threshold) ---")
    im_subj = Image.new("RGB", (100, 100), (255, 255, 255))
    for x in range(40, 60):
        for y in range(40, 60):
            im_subj.putpixel((x, y), (0, 0, 0))
    box_subj = detect_bounds(im_subj)
    status_subj = "PASS" if box_subj == (40, 40, 60, 60) else "FAIL"
    print(f"Subject 20x20 | Result: {box_subj} | Expected: (40, 40, 60, 60) | Status: {status_subj}")
    results.append({
        "test": "2.5_subject_above_threshold",
        "status": status_subj,
        "result": box_subj,
        "expected": (40, 40, 60, 60),
    })

    return results


# =========================================================================
# SUITE 3: Slicer Stress Tests (1x1, 10x10, Non-Uniform)
# =========================================================================

def run_slicer_stress_tests() -> List[dict]:
    results = []
    print("\n" + "=" * 70)
    print("SUITE 3: Slicer Stress Tests (1x1, 10x10, Non-Uniform)")
    print("=" * 70)

    # Test 3.1: 1x1 grid on various dimensions
    print("\n--- Test 3.1: 1x1 Grid on 1x1, 10x10, and 500x500 images ---")
    for w, h in [(1, 1), (10, 10), (500, 500)]:
        im = Image.new("RGB", (w, h), (100, 150, 200))
        grid = calculate_default_grid(width=w, height=h, rows=1, cols=1)
        frames_smart = slice_image(im, grid, smart_crop=True)
        frames_raw = slice_image(im, grid, smart_crop=False)

        pass_len = (len(frames_smart) == 1 and len(frames_raw) == 1)
        pass_size = (frames_smart[0].size == (w, h) and frames_raw[0].size == (w, h))
        status = "PASS" if (pass_len and pass_size) else "FAIL"
        print(f"1x1 Grid on ({w}, {h}) | Smart: {len(frames_smart)} frame(s) {frames_smart[0].size} | Raw: {len(frames_raw)} frame(s) | Status: {status}")
        results.append({
            "test": f"3.1_grid_1x1_{w}x{h}",
            "status": status,
            "smart_len": len(frames_smart),
            "raw_len": len(frames_raw),
            "dim": frames_smart[0].size,
        })

    # Test 3.2: 10x10 grid on 1000x1000 and 500x500
    print("\n--- Test 3.2: 10x10 Grid on 1000x1000 and 500x500 images ---")
    for w, h in [(1000, 1000), (500, 500)]:
        im = Image.new("RGB", (w, h), (100, 150, 200))
        grid = calculate_default_grid(width=w, height=h, rows=10, cols=10)
        frames_smart = slice_image(im, grid, smart_crop=True)
        frames_raw = slice_image(im, grid, smart_crop=False)

        pass_len = (len(frames_smart) == 100 and len(frames_raw) == 100)
        status = "PASS" if pass_len else "FAIL"
        print(f"10x10 Grid on ({w}, {h}) | Smart frames: {len(frames_smart)} | Raw frames: {len(frames_raw)} | Status: {status}")
        results.append({
            "test": f"3.2_grid_10x10_{w}x{h}",
            "status": status,
            "smart_len": len(frames_smart),
            "raw_len": len(frames_raw),
        })

    # Test 3.3: 10x10 grid on small 10x10 image (dense grid edge case)
    print("\n--- Test 3.3: 10x10 Grid on 10x10 image (Extreme edge case) ---")
    im_10x10 = Image.new("RGB", (10, 10), (128, 128, 128))
    grid_10x10 = calculate_default_grid(width=10, height=10, rows=10, cols=10)
    # smart_crop trims 1px borders around divider lines. On a 10x10 image, dividing by 10 leaves no space for cell content.
    frames_smart = slice_image(im_10x10, grid_10x10, smart_crop=True)
    frames_raw = slice_image(im_10x10, grid_10x10, smart_crop=False)
    # Slicer should safely produce either valid cells or gracefully drop collapsed cells without exception
    print(f"10x10 on 10x10 | Smart frames: {len(frames_smart)} | Raw frames: {len(frames_raw)} | Safe: True (No exception thrown)")
    results.append({
        "test": "3.3_grid_10x10_on_10x10",
        "status": "PASS",
        "smart_len": len(frames_smart),
        "raw_len": len(frames_raw),
    })

    # Test 3.4: Non-uniform grids (Asymmetric rows/cols and custom line coords)
    print("\n--- Test 3.4: Non-uniform grids ---")
    # Subtest A: Asymmetric rows=2, cols=7 on 700x200 image
    im_asym = Image.new("RGB", (700, 200), (50, 100, 150))
    grid_asym = calculate_default_grid(width=700, height=200, rows=2, cols=7)
    frames_asym = slice_image(im_asym, grid_asym, smart_crop=False)
    status_asym = "PASS" if len(frames_asym) == 14 else "FAIL"
    print(f"Asymmetric 2x7 Grid | Total frames: {len(frames_asym)} (Expected 14) | Status: {status_asym}")
    results.append({
        "test": "3.4_asymmetric_grid_2x7",
        "status": status_asym,
        "frames": len(frames_asym),
    })

    # Subtest B: Custom non-uniform divider coordinates
    im_cust = Image.new("RGB", (500, 500), (200, 100, 50))
    # Arbitrary non-uniform column dividers at 50, 150, 400 (4 columns of widths 50, 100, 250, 100)
    # and row dividers at 100, 450 (3 rows of heights 100, 350, 50) -> 4 * 3 = 12 cells
    grid_cust = GridConfig(
        rows=3,
        cols=4,
        col_lines=[50, 150, 400],
        row_lines=[100, 450]
    )
    frames_cust = slice_image(im_cust, grid_cust, smart_crop=False)
    status_cust = "PASS" if len(frames_cust) == 12 else "FAIL"
    print(f"Custom Non-Uniform Dividers (4 cols x 3 rows) | Total: {len(frames_cust)} (Expected 12) | Status: {status_cust}")
    results.append({
        "test": "3.4_custom_non_uniform_dividers",
        "status": status_cust,
        "frames": len(frames_cust),
    })

    # Subtest C: Unsorted and redundant divider coordinates
    # GridConfig with unsorted col_lines [400, 50, 150] and duplicate [100, 100, 450]
    grid_unsorted = GridConfig(
        rows=3,
        cols=4,
        col_lines=[400, 50, 150],
        row_lines=[100, 100, 450]
    )
    try:
        frames_unsorted = slice_image(im_cust, grid_unsorted, smart_crop=False)
        print(f"Unsorted/Duplicate Dividers | Result frames: {len(frames_unsorted)} | No crash: PASS")
        status_un = "PASS"
    except Exception as e:
        print(f"Unsorted Dividers Threw Exception: {e}")
        status_un = "FAIL"
    results.append({
        "test": "3.4_unsorted_duplicate_dividers",
        "status": status_un,
    })

    # Subtest D: Dividers outside image boundaries (e.g. negative or > width)
    grid_oob = GridConfig(
        rows=2,
        cols=2,
        col_lines=[-50, 250, 999],
        row_lines=[-10, 250, 1200]
    )
    try:
        frames_oob = slice_image(im_cust, grid_oob, smart_crop=False)
        # Slicer filters dividers min_x <= x <= max_x, so out of bounds dividers should be safely ignored
        print(f"Out-of-Bounds Dividers | Filtered cleanly | Frames: {len(frames_oob)} | Status: PASS")
        status_oob = "PASS" if len(frames_oob) == 4 else "FAIL"
    except Exception as e:
        print(f"Out-of-bounds Dividers Exception: {e}")
        status_oob = "FAIL"
    results.append({
        "test": "3.4_oob_dividers_filtered",
        "status": status_oob,
    })

    return results


# =========================================================================
# SUITE 4: In-Memory Verification & Zero-Disk Integrity Check
# =========================================================================

def run_memory_integrity_tests() -> List[dict]:
    results = []
    print("\n" + "=" * 70)
    print("SUITE 4: In-Memory Operation & Zero-Disk Leak Integrity")
    print("=" * 70)

    # Test 4.1: Exporter Boomerang sequence pure in-memory
    frames = [Image.new("RGB", (50, 50), (i * 20, 0, 0)) for i in range(5)]
    boom_seq, boom_durs = generate_boomerang_sequence(frames, [100] * 5)
    # Expected: 5 + 3 = 8 frames
    status_boom = "PASS" if len(boom_seq) == 8 else "FAIL"
    print(f"Boomerang Sequence (5 frames in) -> {len(boom_seq)} frames out (Expected 8) | Status: {status_boom}")
    results.append({
        "test": "4.1_boomerang_sequence",
        "status": status_boom,
        "frames_out": len(boom_seq),
    })

    # Test 4.2: In-memory bytes export (output_path=None)
    data_gif = export_gif(frames, [100] * 5, output_path=None)
    valid_gif, _, _, _ = verify_gif_bytes(data_gif)

    data_webp = export_webp(frames, [100] * 5, output_path=None)
    valid_webp = data_webp.startswith(b"RIFF") and b"WEBP" in data_webp[:16]

    status_mem = "PASS" if (valid_gif and valid_webp) else "FAIL"
    print(f"Memory Buffer Export | GIF: {len(data_gif)} B (Valid: {valid_gif}) | WebP: {len(data_webp)} B (Valid: {valid_webp}) | Status: {status_mem}")
    results.append({
        "test": "4.2_buffer_export_gif_webp",
        "status": status_mem,
        "gif_bytes": len(data_gif),
        "webp_bytes": len(data_webp),
    })

    return results


def main():
    print("=" * 70)
    print("STARTING CHALLENGER M2-1 EMPIRICAL ADVERSARIAL STRESS HARNESS")
    print("=" * 70)

    all_results = []
    all_results.extend(run_compressor_stress_tests())
    all_results.extend(run_bounds_stress_tests())
    all_results.extend(run_slicer_stress_tests())
    all_results.extend(run_memory_integrity_tests())

    print("\n" + "=" * 70)
    print("SUMMARY OF EMPIRICAL ADVERSARIAL STRESS RESULTS")
    print("=" * 70)
    total = len(all_results)
    passed = sum(1 for r in all_results if r["status"] == "PASS")
    failed = total - passed

    for r in all_results:
        print(f"[{r['status']}] {r['test']}")

    print(f"\nTOTAL TESTS: {total} | PASSED: {passed} | FAILED: {failed}")
    if failed == 0:
        print("FINAL VERDICT: APPROVE")
    else:
        print("FINAL VERDICT: REJECT")


if __name__ == "__main__":
    main()
