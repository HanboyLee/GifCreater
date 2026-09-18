# -*- coding: utf-8 -*-
"""
tests/unit/test_presets.py
平台导出预设管理器单元测试
"""

from src.gifcreater.config.presets import (
    PRESETS,
    DEFAULT_PRESET_KEY,
    get_preset,
    list_preset_items,
    ExportPreset,
)


def test_presets_exist():
    """测试核心平台预设均已定义"""
    assert "wechat" in PRESETS
    assert "xiaohongshu" in PRESETS
    assert "hd_gif" in PRESETS
    assert "webp" in PRESETS


def test_wechat_preset_specs():
    """验证微信表情包严格遵守规范红线 (<=240px, <=500KB)"""
    preset = get_preset("wechat")
    assert preset.max_edge == 240
    assert preset.max_bytes == 500 * 1024
    assert preset.format == "GIF"
    assert preset.speed_factor >= 1.0


def test_get_preset_fallback():
    """测试未知预设 key 时的回退行为"""
    fallback = get_preset("non_existent_platform_key")
    assert fallback == PRESETS[DEFAULT_PRESET_KEY]


def test_list_preset_items():
    """测试 UI 选项数据生成函数"""
    items = list_preset_items()
    assert len(items) == len(PRESETS)
    for key, name, desc in items:
        assert isinstance(key, str) and len(key) > 0
        assert isinstance(name, str) and len(name) > 0
        assert isinstance(desc, str) and len(desc) > 0
