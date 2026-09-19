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
- Do not mention comic pages, frames, gutters, grid lines, stamps, or collages.
- Do not mention extra empty cells or irregular panel sizes.
- Natural language only. NEVER use Midjourney/Flux/SD flags such as --ar, --v, --stylize, --grid, (word:1.3).
- Do not name commercial image products.
- No markdown fences, no JSON, no commentary.
"""


def assemble_image_prompt(brief: GenerationBrief, action_text: str) -> str:
    action = sanitize_completion(action_text)
    return f"{layout_lock_paragraph(brief.rows, brief.cols)}\n\nAction: {action}"


class AgentError(Exception):
    pass


@dataclass
class GenerationBrief:
    inspiration: str
    rows: int
    cols: int
    current_prompt: str = ""


@dataclass
class GenerationResult:
    full_prompt: str


def build_user_message(brief: GenerationBrief) -> str:
    validate_grid(brief.rows, brief.cols)
    cells = brief.rows * brief.cols
    parts = [
        f"Grid: {brief.rows}x{brief.cols} ({cells} panels).",
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
