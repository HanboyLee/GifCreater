# -*- coding: utf-8 -*-
"""
GifCreater 配置与偏好管理包 (Configuration & Preferences)
========================================================

运行时配置管理与偏好持久化模块：
- settings: 本地 JSON 配置文件存取管理器 (SettingsManager) 与配置实体 (AppConfig)
"""

from .presets import ExportPreset, PRESETS, DEFAULT_PRESET_KEY, get_preset, list_preset_items

__all__ = [
    "ExportPreset",
    "PRESETS",
    "DEFAULT_PRESET_KEY",
    "get_preset",
    "list_preset_items",
]

try:
    from .settings import SettingsManager, AppConfig
    __all__.extend(["SettingsManager", "AppConfig"])
except ImportError:
    pass

