# -*- coding: utf-8 -*-
"""Prompt 收藏记录契约（无 GUI）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional
from uuid import uuid4

SCHEMA_VERSION = 1
GRID_MIN = 1
GRID_MAX = 20


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def format_grid(rows: int, cols: int) -> str:
    return f"{int(rows)}x{int(cols)}"


def parse_grid(value: str) -> tuple[int, int]:
    raw = (value or "").strip().lower().replace("×", "x")
    parts = raw.split("x")
    if len(parts) != 2:
        raise ValueError("grid 格式必须为 rowsxcols")
    rows, cols = int(parts[0]), int(parts[1])
    validate_grid(rows, cols)
    return rows, cols


def validate_grid(rows: int, cols: int) -> None:
    if not (GRID_MIN <= rows <= GRID_MAX and GRID_MIN <= cols <= GRID_MAX):
        raise ValueError(f"行列须在 {GRID_MIN}–{GRID_MAX}")


@dataclass
class PromptRecord:
    id: str
    title: str
    prompt: str
    grid: str
    negative: str = ""
    image_model: str = ""
    aspect: str = ""
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""
    schema_version: int = SCHEMA_VERSION

    @property
    def rows(self) -> int:
        return parse_grid(self.grid)[0]

    @property
    def cols(self) -> int:
        return parse_grid(self.grid)[1]

    def validate(self) -> None:
        if not self.id:
            raise ValueError("id 不能为空")
        parse_grid(self.grid)
        if self.schema_version < 1:
            raise ValueError("schema_version 无效")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "id": self.id,
            "title": self.title,
            "prompt": self.prompt,
            "negative": self.negative,
            "image_model": self.image_model,
            "aspect": self.aspect,
            "grid": self.grid,
            "tags": list(self.tags),
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PromptRecord":
        rec = cls(
            id=str(data.get("id") or ""),
            title=str(data.get("title") or ""),
            prompt=str(data.get("prompt") or ""),
            negative=str(data.get("negative") or ""),
            image_model=str(data.get("image_model") or ""),
            aspect=str(data.get("aspect") or ""),
            grid=str(data.get("grid") or ""),
            tags=[str(t) for t in (data.get("tags") or [])],
            notes=str(data.get("notes") or ""),
            created_at=str(data.get("created_at") or ""),
            updated_at=str(data.get("updated_at") or ""),
            schema_version=int(data.get("schema_version") or SCHEMA_VERSION),
        )
        rec.validate()
        return rec

    @classmethod
    def create(
        cls,
        *,
        title: str,
        prompt: str,
        rows: int,
        cols: int,
        negative: str = "",
        tags: Optional[List[str]] = None,
    ) -> "PromptRecord":
        validate_grid(rows, cols)
        now = utc_now_iso()
        return cls(
            id=str(uuid4()),
            title=title.strip() or (prompt.strip()[:24] or "未命名"),
            prompt=prompt,
            grid=format_grid(rows, cols),
            negative=negative,
            tags=list(tags or []),
            created_at=now,
            updated_at=now,
        )
