# -*- coding: utf-8 -*-
"""TypeSafe Jev 决策模型辅助执行工具（供 Agent CLI 在开发/规划/验收时调用）。

本工具遵循 Zero Cloud 边界，仅在开发与验收阶段由开发人员或 Agent CLI 独立运行，
不作为 GifCreater 运行时的依赖包。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Dict


def get_api_key() -> str:
    """获取 TypeSafe API Key，支持进程环境变量与 Windows 用户注册表回退。"""
    key = os.environ.get("TYPESAFE_API_KEY")
    if key:
        return key.strip()

    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as reg_key:
                val, _ = winreg.QueryValueEx(reg_key, "TYPESAFE_API_KEY")
                if val:
                    return str(val).strip()
        except OSError:
            pass

    raise RuntimeError(
        "未检测到 TYPESAFE_API_KEY。请配置环境变量或在 Windows 用户变量中设置 TYPESAFE_API_KEY。"
    )


def evaluate(
    state: str,
    questions: Dict[str, Any],
    model: str = "jev-latest",
    timeout: float = 15.0,
) -> Dict[str, Any]:
    """向 TypeSafe System One 端点发起结构化评估。"""
    api_key = get_api_key()
    payload = {
        "state": state,
        "model": model,
        "questions": questions,
    }

    req = urllib.request.Request(
        "https://api.typesafe.ai/v1/systemone",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"TypeSafe API 请求失败 (HTTP {e.code}): {body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"网络连接异常: {e.reason}") from e


def main() -> int:
    parser = argparse.ArgumentParser(description="TypeSafe Jev 结构化决策辅助工具")
    parser.add_argument("--state", required=True, help="待评估的状态或上下文文本")
    parser.add_argument(
        "--questions-json",
        help="JSON 格式的问题定义字典（包含 Choice / Noul / Score）",
    )
    parser.add_argument(
        "--noul",
        help="快捷发起单个 Noul 是/否问题，例如：--noul '是否属于压缩任务？'",
    )
    parser.add_argument(
        "--model",
        default="jev-latest",
        help="调用的模型版本（默认 jev-latest）",
    )

    args = parser.parse_args()

    questions = {}
    if args.questions_json:
        try:
            questions = json.loads(args.questions_json)
        except json.JSONDecodeError as e:
            print(f"JSON 解析失败: {e}", file=sys.stderr)
            return 1
    elif args.noul:
        questions["quick_noul"] = {
            "type": "noul",
            "instructions": args.noul,
        }
    else:
        print("错误: 必须指定 --questions-json 或 --noul", file=sys.stderr)
        return 1

    try:
        result = evaluate(args.state, questions, model=args.model)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(f"执行失败: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
