#!/usr/bin/env python3
"""文档基线与路线图一致性自动校验工具 (Documentation Synchronization Guard)

用于核验 docs/roadmap.md (演进路线图) 与 docs/requirements.md (需求基线) 的版本状态是否严格对齐。
可作为本地提交自检、预发布核验或 CI/CD 质量门禁执行。
"""

import re
import sys
from pathlib import Path


def get_project_root() -> Path:
    """获取专案根目录绝对路径"""
    # 脚本位于 scripts/tools/check_doc_sync.py -> 往上两级为专案根目录
    return Path(__file__).resolve().parent.parent.parent


def parse_roadmap_baseline(roadmap_path: Path) -> str:
    """从 docs/roadmap.md 中提取当前基线版本号 (例如 'v3.4.3')"""
    if not roadmap_path.exists():
        raise FileNotFoundError(f"找不到路线图文档: {roadmap_path}")

    content = roadmap_path.read_text(encoding="utf-8")
    # 匹配模式：> **当前基线版本**：`v3.4.3 ...`
    match = re.search(r">\s*\*\*当前基线版本\*\*[：:]\s*`?([vV]?\d+\.\d+(?:\.\d+)?)", content)
    if not match:
        raise ValueError("未能从 docs/roadmap.md 中解析出 '> **当前基线版本**：`vX.Y.Z`' 字段！")

    return match.group(1).lower()


def parse_requirements_latest_version(requirements_path: Path) -> str:
    """从 docs/requirements.md 中提取最新已实现或变更记录中的最新版本号"""
    if not requirements_path.exists():
        raise FileNotFoundError(f"找不到需求文档: {requirements_path}")

    content = requirements_path.read_text(encoding="utf-8")

    # 1. 优先从 Changelog 的第一条记录中匹配最新版本号：
    # 格式示例：- **2026-09-18 (v3.4.3 官方品牌图标...)**：...
    changelog_match = re.search(r"-\s*\*\*\d{4}-\d{2}-\d{2}\s*\(([vV]?\d+\.\d+(?:\.\d+)?)[^)]*\)\*\*", content)
    if changelog_match:
        return changelog_match.group(1).lower()

    # 2. 回退策略：搜索最末尾标记为已实现的章节标题
    # 格式示例：## v3.4 交互细节与品牌视觉精细化规范 (已实现)
    implemented_sections = re.findall(r"##\s*([vV]?\d+\.\d+(?:\.\d+)?)[^\n]*\(已实现\)", content)
    if implemented_sections:
        return implemented_sections[-1].lower()

    raise ValueError("未能从 docs/requirements.md 中解析出有效的已完成版本标识！")


def check_docs_synchronization(root_dir: Path) -> bool:
    """执行双向文档同步校验，返回是否通过"""
    docs_dir = root_dir / "docs"
    roadmap_path = docs_dir / "roadmap.md"
    requirements_path = docs_dir / "requirements.md"

    try:
        roadmap_ver = parse_roadmap_baseline(roadmap_path)
        req_ver = parse_requirements_latest_version(requirements_path)
    except Exception as e:
        print(f"[ERROR] 解析文档失败: {e}", file=sys.stderr)
        return False

    print(f"[CHECK] docs/roadmap.md 当前基线版本:     {roadmap_ver}")
    print(f"[CHECK] docs/requirements.md 最新交付版本: {req_ver}")

    # 比较主版本与次版本前缀（允许 patch 微调对齐，如 v3.4 匹配 v3.4.3，或完全精确匹配）
    # 若 requirements 最新版本与 roadmap 版本一致，或处于同一语义版本族
    norm_roadmap = roadmap_ver.lstrip("v")
    norm_req = req_ver.lstrip("v")

    roadmap_parts = norm_roadmap.split(".")
    req_parts = norm_req.split(".")

    # 主版本号必须一致
    major_matches = roadmap_parts[0] == req_parts[0]
    # 次版本号必须一致
    minor_matches = len(roadmap_parts) > 1 and len(req_parts) > 1 and roadmap_parts[1] == req_parts[1]

    if not (major_matches and minor_matches):
        print("\n" + "=" * 70, file=sys.stderr)
        print("[FAIL] 架构文档脱节告警！", file=sys.stderr)
        print(f"  docs/roadmap.md 仍停留在基线 [{roadmap_ver}]，", file=sys.stderr)
        print(f"  而 docs/requirements.md 已推进至 [{req_ver}]！", file=sys.stderr)
        print("  【必须行动】：请按照 AGENTS.md 规范回写 docs/roadmap.md，提升基线版本！", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        return False

    # 若 patch 版本号也存在且不一致，发出友好提示，但不阻断
    if norm_roadmap != norm_req:
        print(f"[INFO] 版本族已对齐 ({roadmap_parts[0]}.{roadmap_parts[1]}.x)，细微 Patch 版本号为: {roadmap_ver} vs {req_ver}")
    else:
        print(f"[PASS] 版本号完全精确对齐: {roadmap_ver}")

    print("[SUCCESS] docs/roadmap.md 与 docs/requirements.md 状态对齐校验通过！")
    return True


def main():
    root = get_project_root()
    success = check_docs_synchronization(root)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
