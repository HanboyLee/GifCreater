# -*- coding: utf-8 -*-
import json
from io import BytesIO
from urllib.error import HTTPError, URLError

import pytest

from src.gifcreater.core.agent_engine import (
    SYSTEM_PROMPT,
    AgentError,
    GenerationBrief,
    StoryboardPipeline,
    assemble_image_prompt,
    build_user_message,
    chat_completions,
    layout_lock_paragraph,
    sanitize_completion,
)


def test_system_prompt_forbids_mj_flags():
    assert "--ar" in SYSTEM_PROMPT
    assert "NEVER" in SYSTEM_PROMPT
    assert "tightly contained" in SYSTEM_PROMPT
    assert "cross cell borders" in SYSTEM_PROMPT
    assert "clean sticker cutout" in SYSTEM_PROMPT
    assert "solid plane" in SYSTEM_PROMPT


def test_layout_lock_is_sliceable_grid():
    text = layout_lock_paragraph(3, 3)
    assert "3 by 3" in text
    assert "sprite sheet" in text
    assert "do not draw any grid lines" in text
    assert "picture-frames" in text or "picture-frame" in text
    assert "CRITICAL COMPACT SCALE" in text


def test_assemble_image_prompt_keeps_code_layout():
    brief = GenerationBrief(inspiration="挥手", rows=2, cols=2, bg_mode="scene")
    out = assemble_image_prompt(brief, "just waving")
    assert out.startswith("A single image")
    assert "2 by 2" in out
    assert "just waving" in out
    assert "continuous, seamless scenic background environment" in out


def test_build_user_message_counts_panels():
    msg = build_user_message(GenerationBrief(inspiration="挥手", rows=3, cols=3, current_prompt="old", bg_mode="scene"))
    assert "3x3" in msg
    assert "9 panels" in msg
    assert "old" in msg
    assert "Continuous environmental scenic background" in msg

    msg_trans = build_user_message(GenerationBrief(inspiration="挥手", rows=2, cols=2, bg_mode="transparent"))
    assert "Transparent background" in msg_trans

    msg_solid = build_user_message(GenerationBrief(inspiration="跳跃", rows=2, cols=2, bg_mode="solid"))
    assert "Solid flat white background" in msg_solid


def test_sanitize_fences():
    assert sanitize_completion("```\nhi\n```") == "hi"


class _FakeResp:
    def __init__(self, payload: dict):
        self._data = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_chat_completions_ok():
    def opener(req, timeout=None):
        assert "Authorization" in dict(req.header_items())
        return _FakeResp({"choices": [{"message": {"content": "A single 2x2 storyboard sheet."}}]})

    text = chat_completions(
        base_url="https://openrouter.ai/api/v1",
        api_key="sk-test",
        model="openai/gpt-4o-mini",
        messages=[{"role": "user", "content": "ping"}],
        opener=opener,
    )
    assert "storyboard" in text


def test_chat_completions_http_429():
    def opener(req, timeout=None):
        raise HTTPError("https://x", 429, "no", hdrs=None, fp=BytesIO())

    with pytest.raises(AgentError, match="频繁"):
        chat_completions(base_url="https://x/v1", api_key="sk", model="m", messages=[], opener=opener)


def test_chat_missing_choices():
    def opener(req, timeout=None):
        return _FakeResp({"choices": []})

    with pytest.raises(AgentError, match="无法解析"):
        chat_completions(base_url="https://x/v1", api_key="sk", model="m", messages=[], opener=opener)


def test_chat_completions_http_401():
    def opener(req, timeout=None):
        raise HTTPError("https://x", 401, "no", hdrs=None, fp=BytesIO())

    with pytest.raises(AgentError, match="认证失败"):
        chat_completions(
            base_url="https://api.openai.com/v1",
            api_key="bad",
            model="m",
            messages=[],
            opener=opener,
        )


def test_chat_completions_no_key():
    with pytest.raises(AgentError, match="API Key"):
        chat_completions(base_url="https://x/v1", api_key="", model="m", messages=[])


def test_pipeline_uses_complete():
    def fake_complete(**kwargs):
        user = kwargs["messages"][1]["content"]
        assert "4x4" in user
        return "sixteen panel natural language prompt"

    result = StoryboardPipeline(complete=fake_complete).run(
        GenerationBrief(inspiration="跳", rows=4, cols=4),
        base_url="https://openrouter.ai/api/v1",
        api_key="sk",
        model="m",
    )
    assert "sixteen" in result.full_prompt
    assert "4 by 4" in result.full_prompt
    assert "sprite sheet" in result.full_prompt


def test_chat_empty_base():
    with pytest.raises(AgentError, match="Base URL"):
        chat_completions(base_url="  ", api_key="sk", model="m", messages=[])


def test_chat_bad_json():
    class Bad:
        def read(self):
            return b"not-json"

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def opener(req, timeout=None):
        return Bad()

    with pytest.raises(AgentError, match="无法解析"):
        chat_completions(base_url="https://x/v1", api_key="sk", model="m", messages=[], opener=opener)


def test_chat_empty_content():
    def opener(req, timeout=None):
        return _FakeResp({"choices": [{"message": {"content": "   "}}]})

    with pytest.raises(AgentError, match="为空"):
        chat_completions(base_url="https://x/v1", api_key="sk", model="m", messages=[], opener=opener)


def test_url_error():
    def opener(req, timeout=None):
        raise URLError("down")

    with pytest.raises(AgentError, match="网络"):
        chat_completions(
            base_url="https://x/v1",
            api_key="sk",
            model="m",
            messages=[],
            opener=opener,
        )


def test_fetch_remote_models_openai_format(monkeypatch):
    from src.gifcreater.core.agent_engine import fetch_remote_models

    payload = {
        "data": [
            {"id": "openai/gpt-4o"},
            {"id": "anthropic/claude-3.5-sonnet"},
            {"id": "deepseek/deepseek-r1"},
        ]
    }

    def fake_urlopen(req, timeout=None):
        assert "models" in req.full_url
        assert req.headers["Authorization"] == "Bearer sk-test"
        return _FakeResp(payload)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    models = fetch_remote_models("https://openrouter.ai/api/v1", api_key="sk-test")
    assert models == ["anthropic/claude-3.5-sonnet", "deepseek/deepseek-r1", "openai/gpt-4o"]


def test_fetch_remote_models_ollama_format(monkeypatch):
    from src.gifcreater.core.agent_engine import fetch_remote_models

    payload = {
        "models": [
            {"name": "llama3.2:latest"},
            {"name": "qwen2.5:latest"},
        ]
    }

    def fake_urlopen(req, timeout=None):
        return _FakeResp(payload)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    models = fetch_remote_models("http://localhost:11434/v1")
    assert models == ["llama3.2:latest", "qwen2.5:latest"]


def test_fetch_remote_models_errors(monkeypatch):
    from src.gifcreater.core.agent_engine import fetch_remote_models

    # 1. 未配置 base_url
    with pytest.raises(AgentError, match="未配置 Base URL"):
        fetch_remote_models("")

    # 2. HTTP 401
    def fake_401(req, timeout=None):
        raise HTTPError("https://x", 401, "unauthorized", hdrs=None, fp=BytesIO())

    monkeypatch.setattr("urllib.request.urlopen", fake_401)
    with pytest.raises(AgentError, match="认证失败"):
        fetch_remote_models("https://api.openai.com/v1", api_key="bad")

    # 3. 网络故障
    def fake_net_err(req, timeout=None):
        raise URLError("offline")

    monkeypatch.setattr("urllib.request.urlopen", fake_net_err)
    with pytest.raises(AgentError, match="网络连接失败"):
        fetch_remote_models("https://api.openai.com/v1")

    # 4. 超时
    def fake_timeout(req, timeout=None):
        raise TimeoutError("timed out")

    monkeypatch.setattr("urllib.request.urlopen", fake_timeout)
    with pytest.raises(AgentError, match="超时"):
        fetch_remote_models("https://api.openai.com/v1")

    # 5. 空列表
    def fake_empty(req, timeout=None):
        return _FakeResp({"data": []})

    monkeypatch.setattr("urllib.request.urlopen", fake_empty)
    with pytest.raises(AgentError, match="未获取到任何可用模型"):
        fetch_remote_models("https://api.openai.com/v1")
