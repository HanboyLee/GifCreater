# -*- coding: utf-8 -*-
import json
from pathlib import Path

import pytest

from src.gifcreater.core.prompt_schema import PromptRecord
from src.gifcreater.core.prompt_store import PromptStore, PromptStoreError


def test_crud_and_query(tmp_path):
    store = PromptStore(tmp_path / "library.sqlite")
    a = store.create(title="挥手", prompt="wave hello", rows=3, cols=3)
    store.create(title="连跳", prompt="jump loop", rows=4, cols=4)
    assert len(store.list()) == 2
    assert store.get(a.id).title == "挥手"
    found = store.list(query="wave")
    assert len(found) == 1
    a.prompt = "wave hello updated"
    store.save(a)
    assert store.get(a.id).prompt.endswith("updated")
    a.created_at = ""
    store.save(a)
    assert store.get(a.id).created_at
    assert store.delete(a.id) is True
    assert store.get(a.id) is None


def test_duplicate_and_export_import(tmp_path):
    store = PromptStore(tmp_path / "library.sqlite")
    rec = store.create(title="眨眼", prompt="blink", rows=2, cols=2)
    copy = store.duplicate(rec.id)
    assert copy is not None
    assert copy.id != rec.id
    assert len(store.list()) == 2

    js = tmp_path / "out.json"
    store.export_json(js)
    md = tmp_path / "out.md"
    store.export_markdown(md)
    assert "眨眼" in md.read_text(encoding="utf-8")

    other = PromptStore(tmp_path / "other.sqlite")
    n = other.import_json(js)
    assert n == 2
    assert len(other.list()) == 2


def test_import_merge_newer_wins(tmp_path):
    store = PromptStore(tmp_path / "library.sqlite")
    rec = store.create(title="旧", prompt="old", rows=2, cols=2)
    incoming = rec.to_dict()
    incoming["title"] = "新"
    incoming["updated_at"] = "2099-01-01T00:00:00+00:00"
    payload = tmp_path / "in.json"
    payload.write_text(json.dumps({"items": [incoming]}), encoding="utf-8")
    store.import_json(payload)
    assert store.get(rec.id).title == "新"


def test_duplicate_missing(tmp_path):
    store = PromptStore(tmp_path / "library.sqlite")
    assert store.duplicate("no-such") is None


def test_corrupt_db_backup(tmp_path):
    db = tmp_path / "library.sqlite"
    db.write_text("not a database", encoding="utf-8")
    with pytest.raises(PromptStoreError):
        PromptStore(db)
    assert (tmp_path / "library.sqlite.bak").exists()


def test_auto_seed_default_presets(tmp_path):
    db = tmp_path / "seeded.sqlite"
    store = PromptStore(db, auto_seed=True)
    items = store.list()
    assert len(items) == 7
    titles = [it.title for it in items]
    assert any("2×2" in t for t in titles)
    assert any("3×3" in t for t in titles)
    assert any("1×6" in t for t in titles)
    assert any("4×4" in t for t in titles)
    assert any("2×3" in t for t in titles)
    assert any("4×6" in t for t in titles)
    assert any("6×4" in t for t in titles)

    # Reopening should not re-seed duplicate records
    store2 = PromptStore(db, auto_seed=True)
    assert len(store2.list()) == 7

    # Manual seeding into empty db
    manual_db = tmp_path / "manual.sqlite"
    manual_store = PromptStore(manual_db, auto_seed=False)
    assert len(manual_store.list()) == 0
    count = manual_store.seed_defaults()
    assert count == 7
    assert len(manual_store.list()) == 7
