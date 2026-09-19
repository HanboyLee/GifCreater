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


def test_list_models_filters(tmp_path):
    all_or = list_models("openrouter", cache_path=tmp_path / "none.json")
    assert "openai/gpt-4o-mini" in all_or
    found = list_models("openrouter", "claude", cache_path=tmp_path / "none.json")
    assert found
    assert all("claude" in m for m in found)


def test_settings_bad_json(tmp_path):
    path = tmp_path / "gifcreater-settings.json"
    path.write_text("{not json", encoding="utf-8")
    mgr = SettingsManager(path)
    assert mgr.load().theme == "dark"


def test_models_cache_persistence(tmp_path):
    from src.gifcreater.config.settings import load_cached_models, save_cached_models

    cache_file = tmp_path / "models_cache.json"
    # 空缓存
    assert load_cached_models("openrouter", path=cache_file) == []

    # 写入缓存
    models = ["openai/gpt-4o", "anthropic/claude-3.5-sonnet", "google/gemini-2.0-flash"]
    save_cached_models("openrouter", models, path=cache_file)

    loaded = load_cached_models("openrouter", path=cache_file)
    assert loaded == models

    # 缓存优先过滤
    found = list_models("openrouter", "gemini", cache_path=cache_file)
    assert found == ["google/gemini-2.0-flash"]
