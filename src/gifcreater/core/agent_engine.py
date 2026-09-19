# -*- coding: utf-8 -*-
"""自然语言分镜 Prompt 完善（OpenAI 兼容 HTTP，无 GUI）。"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, List, Optional

from .prompt_schema import layout_lock_paragraph, validate_grid

SYSTEM_PROMPT = """You write the ACTION part of an animation sprite-sheet prompt.
A program will prepend a locked grid-layout paragraph. You must NOT invent layout.
Rules:
- Output only natural-language action: who the character is, and what happens in each cell in order.
- Cell count MUST equal rows*cols. Same character, clothes, hair, body in every cell.
- Sequential motion, left-to-right then top-to-bottom.
- Keep all actions, poses, and effects tightly contained within the character's local space. Do not describe oversized projectile trails, sprawling horizontal leaps, or wide effects that cross cell borders.
- If background is transparent, DO NOT describe any background, environment, floors, or cast shadows. Focus exclusively on character actions for a clean sticker cutout.
- If background is solid, describe only the character action on a flat solid plane, no scenery.
- If background is scenic, keep environmental scenery coherent and stationary across all panels.
- Do not mention comic pages, frames, gutters, grid lines, stamps, or collages.
- Do not mention extra empty cells or irregular panel sizes.
- Natural language only. NEVER use Midjourney/Flux/SD flags such as --ar, --v, --stylize, --grid, (word:1.3).
- Do not name commercial image products.
- No markdown fences, no JSON, no commentary.
"""


def assemble_image_prompt(brief: GenerationBrief, action_text: str) -> str:
    action = sanitize_completion(action_text)
    bg_mode = getattr(brief, "bg_mode", "transparent")
    return f"{layout_lock_paragraph(brief.rows, brief.cols, bg_mode=bg_mode)}\n\nAction: {action}"


class AgentError(Exception):
    pass


@dataclass
class GenerationBrief:
    inspiration: str
    rows: int
    cols: int
    current_prompt: str = ""
    bg_mode: str = "transparent"


@dataclass
class GenerationResult:
    full_prompt: str


def build_user_message(brief: GenerationBrief) -> str:
    validate_grid(brief.rows, brief.cols)
    cells = brief.rows * brief.cols
    bg_mode = (getattr(brief, "bg_mode", None) or "transparent").lower()
    bg_desc = {
        "transparent": "Transparent background (isolated sticker, zero background/environment)",
        "solid": "Solid flat white background (clean solid color, no scenery)",
        "scene": "Continuous environmental scenic background across panels",
        "auto": "Natural background",
    }.get(bg_mode, "Transparent background (isolated sticker, zero background/environment)")

    parts = [
        f"Grid: {brief.rows}x{brief.cols} ({cells} panels).",
        f"Background style: {bg_desc}.",
        f"Idea: {brief.inspiration.strip() or 'expressive character animation'}",
    ]
    if brief.current_prompt.strip():
        parts.append("Revise this existing prompt:\n" + brief.current_prompt.strip())
    return "\n".join(parts)


def sanitize_completion(text: str) -> str:
    raw = (text or "").strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    return raw


def chat_completions(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: List[dict[str, str]],
    timeout: float = 45.0,
    opener: Optional[Callable[..., Any]] = None,
) -> str:
    root = (base_url or "").strip().rstrip("/")
    if not root:
        raise AgentError("未填写 Base URL")
    if not api_key.strip():
        raise AgentError("未配置 API Key")
    url = root + "/chat/completions"
    body = json.dumps(
        {"model": model, "messages": messages, "temperature": 0.7},
        ensure_ascii=False,
    ).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_key.strip(),
        "HTTP-Referer": "https://gifcreater.local",
        "X-Title": "GifCreater",
    }
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    do_open = opener or urllib.request.urlopen
    try:
        with do_open(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise AgentError(_http_message(exc.code)) from None
    except urllib.error.URLError:
        raise AgentError("网络连接失败") from None
    except TimeoutError:
        raise AgentError("请求超时") from None
    except json.JSONDecodeError:
        raise AgentError("模型返回无法解析") from None
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise AgentError("模型返回无法解析") from None
    text = sanitize_completion(str(content))
    if not text:
        raise AgentError("模型返回为空")
    return text


def _http_message(code: int) -> str:
    if code in (401, 403):
        return "认证失败"
    if code == 429:
        return "请求过于频繁"
    return f"服务返回错误 ({code})"


class StoryboardPipeline:
    def __init__(self, complete: Optional[Callable[..., str]] = None):
        self._complete = complete or chat_completions

    def run(
        self,
        brief: GenerationBrief,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 45.0,
    ) -> GenerationResult:
        validate_grid(brief.rows, brief.cols)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_message(brief)},
        ]
        text = self._complete(
            base_url=base_url,
            api_key=api_key,
            model=model,
            messages=messages,
            timeout=timeout,
        )
        return GenerationResult(full_prompt=assemble_image_prompt(brief, text))


def fetch_remote_models(base_url: str, api_key: str = "", timeout: float = 10.0) -> List[str]:
    """从 Provider 的 /models 端点获取模型列表。"""
    url = (base_url or "").strip().rstrip("/")
    if not url:
        raise AgentError("未配置 Base URL")
    endpoint = f"{url}/models"
    headers = {
        "User-Agent": "GifCreater/3.5 (Desktop)",
        "Accept": "application/json",
    }
    if api_key and api_key.strip():
        headers["Authorization"] = f"Bearer {api_key.strip()}"

    req = urllib.request.Request(endpoint, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise AgentError(_http_message(exc.code)) from None
    except urllib.error.URLError:
        raise AgentError("网络连接失败，请检查 Base URL 或网络设置") from None
    except TimeoutError:
        raise AgentError("获取模型列表超时") from None
    except json.JSONDecodeError:
        raise AgentError("服务返回数据非有效 JSON") from None

    raw_list: list[Any] = []
    if isinstance(data, dict):
        if "data" in data and isinstance(data["data"], list):
            raw_list = data["data"]
        elif "models" in data and isinstance(data["models"], list):
            raw_list = data["models"]
    elif isinstance(data, list):
        raw_list = data

    model_ids = set()
    for item in raw_list:
        if isinstance(item, dict):
            mid = item.get("id") or item.get("name")
            if mid and isinstance(mid, str):
                model_ids.add(mid.strip())
        elif isinstance(item, str) and item.strip():
            model_ids.add(item.strip())

    result = sorted(model_ids)
    if not result:
        raise AgentError("未获取到任何可用模型")
    return result
