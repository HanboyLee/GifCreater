# -*- coding: utf-8 -*-
"""
GifCreater 主题与设计令牌系统 (Theme & Design Tokens System)
============================================================

管理全局视觉主题（暗黑/明亮）、设计令牌 (Tokens) 与 QSS 样式表装载，
保证所有组件符合 WCAG 高对比度与 Windows 11 Fluent 美学规范。
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
from qfluentwidgets import Theme, setTheme


class ThemeMode(str, Enum):
    DARK = "dark"
    LIGHT = "light"


@dataclass(frozen=True)
class ThemeTokens:
    surface_bg: str
    card_bg: str
    card_border: str
    text_primary: str
    text_secondary: str
    btn_secondary_bg: str
    btn_secondary_text: str
    btn_hover_bg: str
    btn_hover_border: str
    accent: str


DARK_TOKENS = ThemeTokens(
    surface_bg="#18181b",
    card_bg="#27272a",
    card_border="#3f3f46",
    text_primary="#ffffff",
    text_secondary="#a1a1aa",
    btn_secondary_bg="#38383e",
    btn_secondary_text="#ffffff",
    btn_hover_bg="#44444c",
    btn_hover_border="#00bcd4",
    accent="#00bcd4",
)

LIGHT_TOKENS = ThemeTokens(
    surface_bg="#f4f4f5",
    card_bg="#ffffff",
    card_border="#e4e4e7",
    text_primary="#09090b",
    text_secondary="#71717a",
    btn_secondary_bg="#f4f4f5",
    btn_secondary_text="#18181b",
    btn_hover_bg="#e4e4e7",
    btn_hover_border="#0097a7",
    accent="#00bcd4",
)


class ThemeManager(QObject):
    """
    统一主题管理器单例
    """
    themeChanged = pyqtSignal(str)  # 发送新主题名称 ("dark" 或 "light")

    _instance: Optional["ThemeManager"] = None

    def __init__(self):
        super().__init__()
        self._current_mode: ThemeMode = ThemeMode.DARK

    @classmethod
    def get_instance(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance

    @property
    def current_mode(self) -> ThemeMode:
        return self._current_mode

    @property
    def tokens(self) -> ThemeTokens:
        return DARK_TOKENS if self._current_mode == ThemeMode.DARK else LIGHT_TOKENS

    def is_dark(self) -> bool:
        return self._current_mode == ThemeMode.DARK

    def set_theme(self, mode: ThemeMode) -> None:
        self._current_mode = mode
        # 同步 QFluentWidgets 全局主题
        if mode == ThemeMode.DARK:
            setTheme(Theme.DARK)
        else:
            setTheme(Theme.LIGHT)
        self.themeChanged.emit(mode.value)

    def toggle_theme(self) -> ThemeMode:
        new_mode = ThemeMode.LIGHT if self._current_mode == ThemeMode.DARK else ThemeMode.DARK
        self.set_theme(new_mode)
        return new_mode

    def get_theme_stylesheet(self, mode: Optional[ThemeMode] = None) -> str:
        """读取 resources/themes/{mode}.qss 样式表内容，兼容源码与 PyInstaller 冻结环境"""
        import sys
        target = mode or self._current_mode
        search_dirs = []
        if getattr(sys, "_MEIPASS", None):
            search_dirs.append(Path(sys._MEIPASS))
        if getattr(sys, "frozen", False):
            search_dirs.append(Path(sys.executable).parent)
        search_dirs.append(Path(__file__).resolve().parent.parent.parent.parent)

        for base in search_dirs:
            theme_file = base / "resources" / "themes" / f"{target.value}.qss"
            if theme_file.exists():
                return theme_file.read_text(encoding="utf-8")

        # 降级备选内联样式
        tokens = DARK_TOKENS if target == ThemeMode.DARK else LIGHT_TOKENS
        return f"""
        #workshopInterface, #promptInterface, #settingsInterface {{ background-color: {tokens.surface_bg}; }}
        ListWidget, QListWidget {{ background-color: {tokens.card_bg}; color: {tokens.text_primary}; border: 1px solid {tokens.card_border}; border-radius: 6px; }}
        ListWidget::item, QListWidget::item {{ color: {tokens.text_primary}; background: transparent; }}
        ListWidget::item:selected, QListWidget::item:selected {{ background-color: {tokens.btn_secondary_bg}; color: {tokens.text_primary}; }}
        CardWidget {{ background-color: {tokens.card_bg}; border: 1px solid {tokens.card_border}; border-radius: 8px; }}
        SubtitleLabel {{ color: {tokens.text_primary}; font-size: 13px; font-weight: bold; }}
        BodyLabel {{ color: {tokens.text_primary}; font-size: 12px; }}
        PushButton {{ background-color: {tokens.btn_secondary_bg}; color: {tokens.btn_secondary_text}; border: 1px solid {tokens.card_border}; border-radius: 5px; }}
        PushButton:hover {{ border-color: {tokens.btn_hover_border}; color: {tokens.text_primary}; }}
        """
