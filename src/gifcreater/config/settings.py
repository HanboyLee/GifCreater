# -*- coding: utf-8 -*-
"""用户设置 JSON 持久化（主题等非机密）。"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional


PROVIDER_PRESETS = (
    ("openrouter", "OpenRouter", "https://openrouter.ai/api/v1"),
    ("openai", "OpenAI", "https://api.openai.com/v1"),
    ("deepseek", "DeepSeek", "https://api.deepseek.com/v1"),
    ("ollama", "Ollama", "http://127.0.0.1:11434/v1"),
    ("custom", "自定义", ""),
)


def preset_base_url(provider: str) -> str:
    for key, _label, url in PROVIDER_PRESETS:
        if key == provider:
            return url
    return ""


MODEL_CATALOG = {
    "openrouter": (
        "openai/gpt-4o-mini",
        "openai/gpt-4o",
        "openai/gpt-4.1-mini",
        "anthropic/claude-sonnet-4",
        "anthropic/claude-3.5-sonnet",
        "google/gemini-2.5-flash",
        "google/gemini-2.0-flash",
        "deepseek/deepseek-chat",
        "qwen/qwen-2.5-72b-instruct",
        "meta-llama/llama-3.3-70b-instruct",
    ),
    "openai": (
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4.1-mini",
        "gpt-4.1",
    ),
    "deepseek": (
        "deepseek-chat",
        "deepseek-reasoner",
    ),
    "ollama": (
        "llama3.2",
        "qwen2.5",
        "mistral",
    ),
    "custom": (),
}


def list_models(provider: str, query: str = "") -> list[str]:
    items = list(MODEL_CATALOG.get(provider, ()))
    q = (query or "").strip().lower()
    if q:
        items = [m for m in items if q in m.lower()]
    return items


@dataclass
class AppConfig:
    theme: str = "dark"
    provider: str = "openrouter"
    base_url: str = "https://openrouter.ai/api/v1"
    model_id: str = "openai/gpt-4o-mini"

    def normalized_theme(self) -> str:
        return "light" if self.theme == "light" else "dark"


class SettingsManager:
    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else default_settings_path()

    def load(self) -> AppConfig:
        if not self.path.exists():
            return AppConfig()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return AppConfig()
        cfg = AppConfig()
        if isinstance(raw, dict):
            if raw.get("theme") in ("dark", "light"):
                cfg.theme = raw["theme"]
            if isinstance(raw.get("provider"), str) and raw["provider"]:
                cfg.provider = raw["provider"]
            if isinstance(raw.get("base_url"), str):
                cfg.base_url = raw["base_url"]
            if isinstance(raw.get("model_id"), str) and raw["model_id"]:
                cfg.model_id = raw["model_id"]
        return cfg

    def save(self, cfg: AppConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(asdict(cfg), ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)


def default_settings_path() -> Path:
    from ..utils.paths import get_default_output_dir

    return Path(get_default_output_dir()) / "gifcreater-settings.json"
