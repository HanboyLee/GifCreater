# -*- coding: utf-8 -*-
"""
GifCreater 国际化多语言支持包 (Internationalization & Localization)
==================================================================

多语言本地化资源与翻译管理器：
- translator: 集中式多语言字典切换器 (Translator) 与快捷翻译函数 tr()
"""

__version__ = "3.0.0"

try:
    from .translator import Translator, tr

    __all__ = [
        "Translator",
        "tr",
    ]
except ImportError:
    # 待 Milestone R3 落地国际化字典后自动激活
    __all__ = []
