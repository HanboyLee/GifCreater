#!/usr/bin/env python3
"""Documentation Synchronization Guard (CI Doc Guard)

Verifies that docs/roadmap.md (Product Roadmap) and docs/requirements.md (Requirements Baseline)
are strictly synchronized in terms of version milestones.
Compatible with all platforms and encoding environments (UTF-8, CP1252, ASCII).
"""

import re
import sys
from pathlib import Path

# Ensure stdout/stderr handles UTF-8 safely across any terminal runner
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def get_project_root() -> Path:
    """Returns absolute path to the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


def parse_roadmap_baseline(roadmap_path: Path) -> str:
    """Extract current baseline version token (e.g. 'v3.4.3') from docs/roadmap.md."""
    if not roadmap_path.exists():
        raise FileNotFoundError(f"Roadmap document not found at: {roadmap_path}")

    content = roadmap_path.read_text(encoding="utf-8")
    # Matches: > **当前基线版本**：`v3.4.3 ...`
    match = re.search(r">\s*\*\*当前基线版本\*\*[：:]\s*`?([vV]?\d+\.\d+(?:\.\d+)?)", content)
    if not match:
        raise ValueError("Failed to locate '> **当前基线版本**：`vX.Y.Z`' token in docs/roadmap.md")

    return match.group(1).lower()


def parse_requirements_latest_version(requirements_path: Path) -> str:
    """Extract latest delivered version token from docs/requirements.md."""
    if not requirements_path.exists():
        raise FileNotFoundError(f"Requirements document not found at: {requirements_path}")

    content = requirements_path.read_text(encoding="utf-8")

    # 1. First priority: changelog entry format: - **2026-09-18 (v3.4.3 ...)**:
    changelog_match = re.search(r"-\s*\*\*\d{4}-\d{2}-\d{2}\s*\(([vV]?\d+\.\d+(?:\.\d+)?)[^)]*\)\*\*", content)
    if changelog_match:
        return changelog_match.group(1).lower()

    # 2. Fallback: last section marked as implemented
    implemented_sections = re.findall(r"##\s*([vV]?\d+\.\d+(?:\.\d+)?)[^\n]*\(已实现\)", content)
    if implemented_sections:
        return implemented_sections[-1].lower()

    raise ValueError("Failed to extract completed milestone version from docs/requirements.md")


def check_docs_synchronization(root_dir: Path) -> bool:
    """Validates baseline synchronization between roadmap and requirements."""
    docs_dir = root_dir / "docs"
    roadmap_path = docs_dir / "roadmap.md"
    requirements_path = docs_dir / "requirements.md"

    try:
        roadmap_ver = parse_roadmap_baseline(roadmap_path)
        req_ver = parse_requirements_latest_version(requirements_path)
    except Exception as e:
        print(f"[ERROR] Failed to parse documents: {e}", file=sys.stderr)
        return False

    print(f"[CHECK] docs/roadmap.md baseline:     {roadmap_ver}")
    print(f"[CHECK] docs/requirements.md latest: {req_ver}")

    norm_roadmap = roadmap_ver.lstrip("v")
    norm_req = req_ver.lstrip("v")

    roadmap_parts = norm_roadmap.split(".")
    req_parts = norm_req.split(".")

    major_matches = roadmap_parts[0] == req_parts[0]
    minor_matches = len(roadmap_parts) > 1 and len(req_parts) > 1 and roadmap_parts[1] == req_parts[1]

    if not (major_matches and minor_matches):
        print("\n" + "=" * 70, file=sys.stderr)
        print("[FAIL] Documentation Baseline Mismatch Warning!", file=sys.stderr)
        print(f"  docs/roadmap.md is at [{roadmap_ver}], but docs/requirements.md is at [{req_ver}].", file=sys.stderr)
        print("  Action Required: Update docs/roadmap.md baseline version according to AGENTS.md!", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        return False

    if norm_roadmap != norm_req:
        print(f"[INFO] Version families aligned ({roadmap_parts[0]}.{roadmap_parts[1]}.x), patch difference: {roadmap_ver} vs {req_ver}")
    else:
        print(f"[PASS] Versions exactly aligned: {roadmap_ver}")

    print("[SUCCESS] docs/roadmap.md and docs/requirements.md are synchronized!")
    return True


def main():
    root = get_project_root()
    success = check_docs_synchronization(root)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
