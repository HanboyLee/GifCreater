# -*- coding: utf-8 -*-
"""
GifCreater 配置与偏好管理包 (Configuration & Preferences)
========================================================

运行时配置管理与偏好持久化模块：
- settings: 本地 JSON 配置文件存取管理器 (SettingsManager) 与配置实体 (AppConfig)
"""

__version__ = "3.0.0"

try:
    from .settings import SettingsManager, AppConfig

    __all__ = [
        "SettingsManager",
        "AppConfig",
    ]
except ImportError:
    # 待 Milestone R3 落地偏好配置管理逻辑后自动激活
    __all__ = []
