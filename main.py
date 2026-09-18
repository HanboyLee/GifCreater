# -*- coding: utf-8 -*-
"""
GifCreater 动图工坊 v3.0 主应用入口
==================================

- 初始化系统级 High DPI 高分屏适配
- 启动 PyQt6 现代化 Fluent UI 视窗事件循环
"""

import sys
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

# 注册 Windows 原生 AppUserModelID 以确保任务栏显示独立应用图标
if sys.platform == "win32":
    import ctypes
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("HanboyLee.GifCreater.App.3.4")
    except Exception:
        pass

from src.gifcreater.ui.main_window import MainWindow
from src.gifcreater.utils.paths import get_base_dir


def main():
    # 启用高分屏支持与 DPI 缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("GifCreater")
    app.setOrganizationName("HanboyLee")

    # 挂载官方品牌图标
    icon_path = Path(get_base_dir()) / "resources" / "icons" / "app_icon.ico"
    if not icon_path.exists():
        icon_path = Path(get_base_dir()) / "resources" / "icons" / "app_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    from src.gifcreater.config.theme_manager import ThemeManager, ThemeMode

    # 默认启用深色质感主题 (支持界面一键切换)
    ThemeManager.get_instance().set_theme(ThemeMode.DARK)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
