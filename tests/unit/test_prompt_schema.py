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
