# -*- coding: utf-8 -*-
from src.gifcreater.core.prompt_schema import (
    PromptRecord,
    format_grid,
    parse_grid,
    validate_grid,
)
import pytest


def test_format_and_parse_grid():
    assert format_grid(3, 3) == "3x3"
    assert parse_grid("4×4") == (4, 4)
    assert parse_grid("1x6") == (1, 6)


def test_grid_bounds():
    validate_grid(1, 20)
    with pytest.raises(ValueError):
        validate_grid(0, 3)
    with pytest.raises(ValueError):
        parse_grid("bad")


def test_record_roundtrip():
    rec = PromptRecord.create(title="挥手", prompt="a waving character", rows=3, cols=4)
    rec.validate()
    data = rec.to_dict()
    back = PromptRecord.from_dict(data)
    assert back.rows == 3
    assert back.cols == 4
    assert back.title == "挥手"


def test_schema_version_invalid():
    rec = PromptRecord.create(title="a", prompt="p", rows=2, cols=2)
    rec.schema_version = 0
    with pytest.raises(ValueError):
        rec.validate()


def test_missing_id_invalid():
    rec = PromptRecord.create(title="a", prompt="p", rows=2, cols=2)
    rec.id = ""
    with pytest.raises(ValueError):
        rec.validate()


def test_default_presets():
    from src.gifcreater.core.prompt_schema import DEFAULT_PROMPT_PRESETS, get_default_presets

    assert len(DEFAULT_PROMPT_PRESETS) == 7
    presets = get_default_presets()
    assert len(presets) == 7
    for p in presets:
        assert p["title"]
        assert p["prompt"].startswith("A single image")
        assert "Action:" in p["prompt"]
        assert "x" in p["grid"]
    grids = [p["grid"] for p in presets]
    assert "4x6" in grids
    assert "6x4" in grids


def test_layout_lock_bg_mode_and_anti_bleed():
    from src.gifcreater.core.prompt_schema import layout_lock_paragraph

    # 1. 纯色透明底 (transparent, 默认)
    t_text = layout_lock_paragraph(3, 3, bg_mode="transparent")
    assert "#FFFFFF" in t_text
    assert "Isolated character sticker style" in t_text
    assert "no ground shadows" in t_text
    assert "no environment" in t_text

    # 防越界穿模护城河约束
    assert "CRITICAL COMPACT SCALE" in t_text
    assert "60% to 70%" in t_text
    assert "at least 15% wide empty blank buffer margin" in t_text
    assert "ABSOLUTELY NO BLEED-OVER" in t_text

    # 2. 场景连贯环境 (scene)
    s_text = layout_lock_paragraph(4, 4, bg_mode="scene")
    assert "continuous, seamless scenic background environment" in s_text
    assert "scenery, props, and lighting must stay consistent" in s_text
    assert "#FFFFFF" not in s_text
    # 同样必须包含防越界穿模约束
    assert "60% to 70%" in s_text
    assert "ABSOLUTELY NO BLEED-OVER" in s_text

    # 3. 自由不限 (auto)
    a_text = layout_lock_paragraph(2, 2, bg_mode="auto")
    assert "seamless uniform background without borders" in a_text
    assert "ABSOLUTELY NO BLEED-OVER" in a_text
