# -*- coding: utf-8 -*-
"""Prompt SQLite 收藏库（无 GUI）。"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from .prompt_schema import PromptRecord, utc_now_iso

_SCHEMA = """
CREATE TABLE IF NOT EXISTS prompts (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT '',
    prompt TEXT NOT NULL DEFAULT '',
    negative TEXT NOT NULL DEFAULT '',
    image_model TEXT NOT NULL DEFAULT '',
    aspect TEXT NOT NULL DEFAULT '',
    grid TEXT NOT NULL,
    tags_json TEXT NOT NULL DEFAULT '[]',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    schema_version INTEGER NOT NULL DEFAULT 1
);
"""


class PromptStoreError(Exception):
    pass


class PromptStore:
    def __init__(self, db_path: Path, auto_seed: bool = False):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.auto_seed = auto_seed
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        try:
            with self._connect() as conn:
                conn.executescript(_SCHEMA)
                if self.auto_seed:
                    count = conn.execute("SELECT COUNT(*) FROM prompts").fetchone()[0]
                    if count == 0:
                        self.seed_defaults(conn)
        except sqlite3.DatabaseError as exc:
            self._backup_corrupt()
            raise PromptStoreError("收藏库损坏，已备份为 .bak") from exc

    def seed_defaults(self, conn: Optional[sqlite3.Connection] = None) -> int:
        """植入内置精选分镜范例。返回成功插入的记录数。"""
        from .prompt_schema import get_default_presets

        presets = get_default_presets()
        now = utc_now_iso()

        def _do_insert(c: sqlite3.Connection) -> int:
            inserted = 0
            for item in presets:
                pid = str(uuid4())
                c.execute(
                    """
                    INSERT INTO prompts (id, title, prompt, negative, image_model, aspect, grid, tags_json, notes, created_at, updated_at, schema_version)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                    (
                        pid,
                        item["title"],
                        item["prompt"],
                        item.get("negative", ""),
                        "",
                        "",
                        item["grid"],
                        json.dumps(item.get("tags", []), ensure_ascii=False),
                        item.get("notes", ""),
                        now,
                        now,
                    ),
                )
                inserted += 1
            return inserted

        if conn is not None:
            return _do_insert(conn)
        with self._connect() as c:
            return _do_insert(c)

    def _backup_corrupt(self) -> None:
        if self.db_path.exists():
            bak = self.db_path.with_suffix(self.db_path.suffix + ".bak")
            bak.write_bytes(self.db_path.read_bytes())

    def _row_to_record(self, row: sqlite3.Row) -> PromptRecord:
        tags = json.loads(row["tags_json"] or "[]")
        return PromptRecord.from_dict({**dict(row), "tags": tags})

    def list(self, query: Optional[str] = None) -> List[PromptRecord]:
        sql = "SELECT * FROM prompts ORDER BY updated_at DESC"
        params: tuple = ()
        if query and query.strip():
            q = f"%{query.strip()}%"
            sql = (
                "SELECT * FROM prompts WHERE title LIKE ? OR prompt LIKE ? "
                "ORDER BY updated_at DESC"
            )
            params = (q, q)
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_record(r) for r in rows]

    def get(self, record_id: str) -> Optional[PromptRecord]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM prompts WHERE id = ?", (record_id,)).fetchone()
        return self._row_to_record(row) if row else None

    def save(self, record: PromptRecord) -> PromptRecord:
        record.validate()
        record.updated_at = utc_now_iso()
        if not record.created_at:
            record.created_at = record.updated_at
        payload = record.to_dict()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO prompts (
                    id, title, prompt, negative, image_model, aspect, grid,
                    tags_json, notes, created_at, updated_at, schema_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    prompt=excluded.prompt,
                    negative=excluded.negative,
                    image_model=excluded.image_model,
                    aspect=excluded.aspect,
                    grid=excluded.grid,
                    tags_json=excluded.tags_json,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at,
                    schema_version=excluded.schema_version
                """,
                (
                    payload["id"],
                    payload["title"],
                    payload["prompt"],
                    payload["negative"],
                    payload["image_model"],
                    payload["aspect"],
                    payload["grid"],
                    json.dumps(payload["tags"], ensure_ascii=False),
                    payload["notes"],
                    payload["created_at"],
                    payload["updated_at"],
                    payload["schema_version"],
                ),
            )
        return record

    def create(self, *, title: str, prompt: str, rows: int, cols: int) -> PromptRecord:
        rec = PromptRecord.create(title=title, prompt=prompt, rows=rows, cols=cols)
        return self.save(rec)

    def delete(self, record_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM prompts WHERE id = ?", (record_id,))
            return cur.rowcount > 0

    def duplicate(self, record_id: str) -> Optional[PromptRecord]:
        src = self.get(record_id)
        if src is None:
            return None
        now = utc_now_iso()
        copy = PromptRecord.from_dict(
            {
                **src.to_dict(),
                "id": str(uuid4()),
                "title": f"{src.title} 副本" if src.title else "副本",
                "created_at": now,
                "updated_at": now,
            }
        )
        return self.save(copy)

    def export_json(self, path: Path) -> None:
        items = [r.to_dict() for r in self.list()]
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"schema_version": 1, "items": items}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def import_json(self, path: Path) -> int:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        items = data.get("items", data if isinstance(data, list) else [])
        count = 0
        for raw in items:
            incoming = PromptRecord.from_dict(raw)
            existing = self.get(incoming.id)
            if existing is None or incoming.updated_at >= existing.updated_at:
                self.save(incoming)
                count += 1
        return count

    def export_markdown(self, path: Path) -> None:
        lines = ["# Prompt 收藏\n"]
        for rec in self.list():
            lines.append(f"## {rec.title or rec.id}\n")
            lines.append(f"- 网格: {rec.grid}\n")
            lines.append(f"\n{rec.prompt}\n")
        Path(path).write_text("\n".join(lines), encoding="utf-8")


def default_library_path() -> Path:
    from ..utils.paths import get_default_output_dir

    return Path(get_default_output_dir("prompts")) / "library.sqlite"
