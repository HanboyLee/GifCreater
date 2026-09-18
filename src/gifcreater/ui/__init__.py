# -*- coding: utf-8 -*-
"""
GifCreater UI 表现层 (Presentation Layer)
=========================================

基于 PyQt6 与 PyQt-Fluent-Widgets 构建的 Windows 11 Fluent 风格交互系统：
- main_window: 主视窗 (FluentWindow, Mica/Acrylic 材质, 深浅色主题即时切换)
- canvas: 交互式视口画布 (鼠标锚点平滑缩放、空格平移、分割线磁吸拖拽)
- filmstrip: 水平卡片流式序列帧胶卷 (多选/Delete废帧剔除与播放器重排联动)
- sidebar: 参数控制侧边栏面板 (行列控制、节奏调节、导出预设)
- workers: 异步后台工作线程池 (SliceWorker, ExportWorker)
"""

__version__ = "3.0.0"

try:
    from .main_window import MainWindow
    from .canvas import InteractiveCanvas
    from .filmstrip import FilmstripWidget
    from .sidebar import ControlSidebar
    from .workers import SliceWorker, ExportWorker

    __all__ = [
        "MainWindow",
        "InteractiveCanvas",
        "FilmstripWidget",
        "ControlSidebar",
        "SliceWorker",
        "ExportWorker",
    ]
except ImportError:
    # 待 Milestone R3 (PyQt6 Fluent 表现层构建) 实现对应视窗组件后自动激活
    __all__ = []
