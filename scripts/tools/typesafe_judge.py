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

# Windows 控制台编码保护 (防止 cp950/cp936 等非 UTF-8 终端崩溃)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="TypeSafe Jev 结构化决策辅助工具 (极速 CLI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
使用示例 (Examples):
  # 1. 快捷单行 Choice 多选裁决 (推荐，无需手拼 JSON):
  python scripts/tools/typesafe_judge.py --state "用户需要选择背景" \\
    --choice-inst "最合理的背景模式方案" \\
    -o transparent "透明免抠背景" \\
    -o solid "纯色实心背景" \\
    -o scene "连续场景背景"

  # 2. 快捷单行 Noul 是/否条件判定:
  python scripts/tools/typesafe_judge.py --state "本次修改纯粹是文档调整" \\
    --noul "本次改动是否包含业务逻辑代码变更？"

  # 3. 预检请求结构 (Dry-Run, 不发网):
  python scripts/tools/typesafe_judge.py --state "测试" --noul "测试" --dry-run
""",
    )
    parser.add_argument("--state", required=True, help="待评估的状态上下文文本 (State)")

    # 快捷 Choice
    parser.add_argument("--choice-name", default="decision", help="Choice 问题名称 (默认: decision)")
    parser.add_argument("--choice-inst", help="Choice 判定指令 (Instructions)")
    parser.add_argument(
        "-o",
        "--option",
        action="append",
        nargs=2,
        metavar=("KEY", "DESC"),
        help="Choice 选项键名与描述，可多次指定，如: -o opt_a '方案A描述'",
    )

    # 快捷 Noul
    parser.add_argument("--noul-name", default="quick_noul", help="Noul 问题名称 (默认: quick_noul)")
    parser.add_argument("--noul", help="快捷发起单个 Noul 是/否判定指令，例如: --noul '是否属于压缩任务？'")

    # 高级原生 JSON
    parser.add_argument(
        "--questions-json",
        help="JSON 格式的问题定义字典（包含复合 Choice / Noul / Score，用于高级场景）",
    )

    # 通用控制
    parser.add_argument("--model", default="jev-latest", help="调用的模型版本（默认 jev-latest）")
    parser.add_argument(
        "--format",
        choices=["pretty", "json"],
        default="pretty",
        help="输出格式: pretty (友好排版摘要+原始JSON) 或 json (纯JSON)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只校验并打印构造的 Request Payload，不向网络发起请求",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    questions: Dict[str, Any] = {}

    # 1. 解析高级 JSON
    if args.questions_json:
        try:
            questions = json.loads(args.questions_json)
        except json.JSONDecodeError as e:
            print(f"JSON 解析失败: {e}", file=sys.stderr)
            return 1

    # 2. 解析快捷 Choice
    if args.choice_inst:
        if not args.option or len(args.option) < 2:
            print("错误: --choice-inst 必须搭配至少 2 个 -o/--option KEY DESC 选项", file=sys.stderr)
            return 1
        criteria = {k: desc for k, desc in args.option}
        questions[args.choice_name] = {
            "type": "choice",
            "instructions": args.choice_inst,
            "criteria": criteria,
        }

    # 3. 解析快捷 Noul
    if args.noul:
        questions[args.noul_name] = {
            "type": "noul",
            "instructions": args.noul,
        }

    if not questions:
        print("错误: 必须指定 --choice-inst (-o ...), --noul 或 --questions-json", file=sys.stderr)
        return 1

    # Dry-run 模式
    if args.dry_run:
        payload = {"state": args.state, "model": args.model, "questions": questions}
        print("[DRY-RUN] Request payload valid:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    try:
        result = evaluate(args.state, questions, model=args.model)

        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("\n=== TypeSafe Jev 结构化决策分析结果 ===")
            answers = result.get("answers", {})
            for qid, ans in answers.items():
                val = ans.get("value")
                conf = ans.get("confidence")
                prob = ans.get("probability")
                dist = ans.get("distribution")
                if dist is not None:
                    conf_str = f"{conf * 100:.1f}%" if conf is not None else "N/A"
                    print(f"[{qid}] -> 裁决结果: 【{val}】 (置信度: {conf_str})")
                    print(f"       概率分布: {dist}")
                elif prob is not None:
                    verdict = "YES (成立)" if prob >= 0.5 else "NO (不成立)"
                    print(f"[{qid}] -> Noul 判定: 【{verdict}】 (概率: {prob * 100:.1f}%)")
            print("\n--- 原始 JSON 响应 ---")
            print(json.dumps(result, ensure_ascii=False, indent=2))

        return 0
    except Exception as e:
        print(f"执行失败: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
