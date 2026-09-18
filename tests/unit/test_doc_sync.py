"""tests/unit/test_doc_sync.py

文档一致性校验工具自动化单元测试。
"""

import sys
from pathlib import Path
import pytest

from scripts.tools.check_doc_sync import (
    get_project_root,
    parse_roadmap_baseline,
    parse_requirements_latest_version,
    check_docs_synchronization,
)


def test_get_project_root():
    root = get_project_root()
    assert (root / "docs").exists()
    assert (root / "src").exists()


def test_parse_real_documents():
    root = get_project_root()
    roadmap_path = root / "docs" / "roadmap.md"
    req_path = root / "docs" / "requirements.md"

    roadmap_ver = parse_roadmap_baseline(roadmap_path)
    req_ver = parse_requirements_latest_version(req_path)

    assert roadmap_ver.startswith("v3.4")
    assert req_ver.startswith("v3.4")
    assert check_docs_synchronization(root) is True


def test_parse_roadmap_errors(tmp_path):
    missing_file = tmp_path / "non_existent.md"
    with pytest.raises(FileNotFoundError):
        parse_roadmap_baseline(missing_file)

    invalid_content = tmp_path / "invalid.md"
    invalid_content.write_text("# Title without baseline", encoding="utf-8")
    with pytest.raises(ValueError):
        parse_roadmap_baseline(invalid_content)


def test_parse_requirements_errors(tmp_path):
    missing_file = tmp_path / "non_existent.md"
    with pytest.raises(FileNotFoundError):
        parse_requirements_latest_version(missing_file)

    invalid_content = tmp_path / "invalid.md"
    invalid_content.write_text("# Title without changelog or section", encoding="utf-8")
    with pytest.raises(ValueError):
        parse_requirements_latest_version(invalid_content)


def test_sync_mismatch_detected(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()

    roadmap = docs / "roadmap.md"
    roadmap.write_text("> **当前基线版本**：`v3.0.0`\n", encoding="utf-8")

    req = docs / "requirements.md"
    req.write_text(
        "## 需求变更与迭代记录 (Changelog)\n"
        "- **2026-09-18 (v3.4.3 官方品牌图标)**：内容\n",
        encoding="utf-8"
    )

    assert check_docs_synchronization(tmp_path) is False


def test_sync_fallback_to_implemented_section(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()

    roadmap = docs / "roadmap.md"
    roadmap.write_text("> **当前基线版本**：`v3.5.0`\n", encoding="utf-8")

    req = docs / "requirements.md"
    req.write_text(
        "## v3.5 某些特性规范 (已实现)\n"
        "- [x] 完成了某些特性\n",
        encoding="utf-8"
    )

    assert check_docs_synchronization(tmp_path) is True
