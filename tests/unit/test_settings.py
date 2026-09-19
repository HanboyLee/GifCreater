# -*- coding: utf-8 -*-
from src.gifcreater.config.settings import AppConfig, SettingsManager, list_models


def test_settings_roundtrip(tmp_path):
    path = tmp_path / "gifcreater-settings.json"
    mgr = SettingsManager(path)
    assert mgr.load().theme == "dark"
    cfg = AppConfig(theme="light", provider="openai", base_url="https://api.openai.com/v1")
    mgr.save(cfg)
    loaded = mgr.load()
    assert loaded.theme == "light"
    assert loaded.provider == "openai"
    assert loaded.normalized_theme() == "light"


def test_list_models_filters():
    all_or = list_models("openrouter")
    assert "openai/gpt-4o-mini" in all_or
    found = list_models("openrouter", "claude")
    assert found
    assert all("claude" in m for m in found)


def test_settings_bad_json(tmp_path):
    path = tmp_path / "gifcreater-settings.json"
    path.write_text("{not json", encoding="utf-8")
    mgr = SettingsManager(path)
    assert mgr.load().theme == "dark"
