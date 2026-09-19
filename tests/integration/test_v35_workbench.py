# -*- coding: utf-8 -*-
"""v3.5 工作台进程内 E2E：导航 + Mock 完善（不打真网）。"""

from PyQt6.QtWidgets import QApplication

from src.gifcreater.config.secrets import FakeProtector, SecretStore
from src.gifcreater.config.settings import SettingsManager
from src.gifcreater.core.prompt_store import PromptStore
from src.gifcreater.ui.main_window import MainWindow
from src.gifcreater.ui.prompt_page import PromptPage


def test_main_window_has_three_pages(qapp, tmp_path):
    settings = SettingsManager(tmp_path / "gifcreater-settings.json")
    secrets = SecretStore(tmp_path / "gifcreater-secrets.bin", protector=FakeProtector())
    win = MainWindow(settings_manager=settings, secret_store=secrets)
    assert "v3.5" in win.windowTitle()
    assert win.prompt_page is not None
    assert win.settings_page is not None
    assert win.stackedWidget.count() >= 3
    win.switchTo(win.prompt_page)
    assert win.stackedWidget.currentWidget() is win.prompt_page
    win.switchTo(win.settings_page)
    assert win.settings_page.radio_dark is not None
    assert win.settings_page.combo_provider is not None


def test_refine_without_key_does_not_start_worker(qapp, tmp_path):
    store = PromptStore(tmp_path / "lib.sqlite")
    settings = SettingsManager(tmp_path / "gifcreater-settings.json")
    secrets = SecretStore(tmp_path / "gifcreater-secrets.bin", protector=FakeProtector())
    page = PromptPage(store=store, settings=settings, secrets=secrets)
    page._on_refine()
    assert page._refine_worker is None


def test_refine_with_mock_writes_prompt(qapp, tmp_path, monkeypatch):
    def fake_complete(**kwargs):
        return "A single 3x3 storyboard sheet, nine equal panels, same character waving."

    monkeypatch.setattr("src.gifcreater.core.agent_engine.chat_completions", fake_complete)

    store = PromptStore(tmp_path / "lib.sqlite")
    settings = SettingsManager(tmp_path / "gifcreater-settings.json")
    secrets = SecretStore(tmp_path / "gifcreater-secrets.bin", protector=FakeProtector())
    secrets.save_key("sk-test")
    page = PromptPage(store=store, settings=settings, secrets=secrets)
    page.spin_rows.setValue(3)
    page.spin_cols.setValue(3)
    page.edit_hint.setText("黄帽衫小人挥手")
    page._on_refine()
    assert page._refine_worker is not None
    page._refine_worker.wait(15000)
    QApplication.processEvents()
    text = page.edit_prompt.toPlainText()
    assert "storyboard" in text.lower() or "panel" in text.lower()
    assert "--ar" not in text
    assert "--grid" not in text
