# -*- coding: utf-8 -*-
"""
GifCreater 动图工坊 v3.0 主应用入口
==================================

- 初始化系统级 High DPI 高分屏适配
- 启动 PyQt6 现代化 Fluent UI 视窗事件循环
"""

import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from qfluentwidgets import Theme, setTheme

from src.gifcreater.ui.main_window import MainWindow


def main():
    # 启用高分屏支持与 DPI 缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("GifCreater")
    app.setOrganizationName("HanboyLee")

    from src.gifcreater.config.theme_manager import ThemeManager, ThemeMode

    # 默认启用深色质感主题 (支持界面一键切换)
    ThemeManager.get_instance().set_theme(ThemeMode.DARK)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
