# -*- coding: utf-8 -*-
"""
主题系统与设计令牌单元测试 (Unit Tests for Theme System)
"""

import pytest
from src.gifcreater.config.theme_manager import (
    ThemeManager,
    ThemeMode,
    ThemeTokens,
    DARK_TOKENS,
    LIGHT_TOKENS,
)


def test_theme_tokens_contrast():
    """验证深浅色设计令牌文本与背景对比度规范"""
    # 深色模式：白字深底
    assert DARK_TOKENS.text_primary.lower() == "#ffffff"
    assert DARK_TOKENS.btn_secondary_text.lower() == "#ffffff"
    assert DARK_TOKENS.card_bg.startswith("#2")

    # 浅色模式：黑字浅底
    assert LIGHT_TOKENS.text_primary.lower() == "#09090b"
    assert LIGHT_TOKENS.btn_secondary_text.lower() == "#18181b"
    assert LIGHT_TOKENS.card_bg.lower() == "#ffffff"


def test_theme_manager_singleton_and_toggle(qapp):
    """测试 ThemeManager 单例与双模切换"""
    mgr1 = ThemeManager.get_instance()
    mgr2 = ThemeManager.get_instance()
    assert mgr1 is mgr2

    # 设置深色
    mgr1.set_theme(ThemeMode.DARK)
    assert mgr1.is_dark() is True
    assert mgr1.current_mode == ThemeMode.DARK
    assert mgr1.tokens == DARK_TOKENS

    # 切换为浅色
    switched = []
    mgr1.themeChanged.connect(lambda mode: switched.append(mode))
    new_mode = mgr1.toggle_theme()
    assert new_mode == ThemeMode.LIGHT
    assert mgr1.is_dark() is False
    assert mgr1.current_mode == ThemeMode.LIGHT
    assert mgr1.tokens == LIGHT_TOKENS
    assert "light" in switched

    # 恢复深色
    mgr1.set_theme(ThemeMode.DARK)
    assert mgr1.is_dark() is True


def test_theme_manager_stylesheets_disk_loading(qapp):
    """测试读取磁盘 dark.qss 和 light.qss 文件"""
    mgr = ThemeManager.get_instance()
    qss_dark = mgr.get_theme_stylesheet(ThemeMode.DARK)
    assert "background-color: #18181b" in qss_dark
    assert "color: #ffffff" in qss_dark

    qss_light = mgr.get_theme_stylesheet(ThemeMode.LIGHT)
    assert "background-color: #f4f4f5" in qss_light
    assert "color: #09090b" in qss_light
