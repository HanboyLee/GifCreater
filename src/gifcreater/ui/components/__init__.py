# -*- coding: utf-8 -*-
"""
GifCreater UI 基础与通用微组件包 (Reusable UI Components)
=========================================================

可复用的通用微组件库：
- frame_card: 序列帧胶卷单帧微卡片控件 (缩略图、标号、删除悬浮动效)
- hud_badge: 画布左上角半透明 Fluent 悬浮尺寸与画幅比例徽章
"""

__version__ = "3.0.0"

try:
    from .frame_card import FrameCard
    from .hud_badge import HudBadge

    __all__ = [
        "FrameCard",
        "HudBadge",
    ]
except ImportError:
    # 待 Milestone R3 落地基础控件实现后自动激活
    __all__ = []
