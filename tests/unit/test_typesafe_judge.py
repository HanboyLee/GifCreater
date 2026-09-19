# -*- coding: utf-8 -*-
"""scripts/tools/typesafe_judge.py 单元测试。"""

import importlib.util
from pathlib import Path
from unittest.mock import patch
import pytest

# 动态加载 scripts/tools/typesafe_judge.py
_script_path = Path(__file__).resolve().parents[2] / "scripts" / "tools" / "typesafe_judge.py"
_spec = importlib.util.spec_from_file_location("typesafe_judge", _script_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


def test_build_parser_choice_and_dry_run(capsys):
    parser = _mod.build_parser()
    args = parser.parse_args([
        "--state", "选择方案",
        "--choice-inst", "最符合直觉的方案",
        "-o", "opt_a", "方案A",
        "-o", "opt_b", "方案B",
        "--dry-run",
    ])
    assert args.state == "选择方案"
    assert args.choice_inst == "最符合直觉的方案"
    assert len(args.option) == 2
    assert args.dry_run is True


def test_main_dry_run_choice(capsys):
    test_args = [
        "typesafe_judge.py",
        "--state", "测试上下文",
        "--choice-inst", "请选择",
        "-o", "a", "选项A",
        "-o", "b", "选项B",
        "--dry-run",
    ]
    with patch("sys.argv", test_args):
        ret = _mod.main()
        assert ret == 0
    out = capsys.readouterr().out
    assert "[DRY-RUN]" in out
    assert "choice" in out
    assert "选项A" in out


def test_main_dry_run_noul(capsys):
    test_args = [
        "typesafe_judge.py",
        "--state", "测试上下文",
        "--noul", "是否为真？",
        "--dry-run",
    ]
    with patch("sys.argv", test_args):
        ret = _mod.main()
        assert ret == 0
    out = capsys.readouterr().out
    assert "[DRY-RUN]" in out
    assert "noul" in out
    assert "是否为真？" in out


def test_main_missing_questions(capsys):
    test_args = [
        "typesafe_judge.py",
        "--state", "无问题上下文",
    ]
    with patch("sys.argv", test_args):
        ret = _mod.main()
        assert ret == 1
    err = capsys.readouterr().err
    assert "错误" in err
