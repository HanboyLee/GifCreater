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


def layout_lock_paragraph(rows: int, cols: int) -> str:
    """切片引擎需要的几何约束，由代码写入，不交给模型发挥。"""
    validate_grid(rows, cols)
    cells = rows * cols
    return (
        f"A single image that is a perfect {rows} by {cols} animation sprite sheet for automatic cropping. "
        f"Exactly {cells} rectangular cells in a regular matrix: {rows} rows and {cols} columns. "
        "Every cell is the same width and the same height. "
        "The grid fills the entire image edge to edge. "
        "CRITICAL: do not draw any grid lines, gutters, borders, boxes, or picture-frames between or around cells. "
        "No black lines, no white lines, no panel outlines. Cells share one seamless uniform background. "
        "Separate poses only by equal spacing of the character; the background is continuous. "
        "Keep each pose centered in its imaginary cell with empty background padding so nothing touches a cell edge. "
        "No overlapping, no comic layout, no collage, no extra empty cells. "
        "Read left to right, then top to bottom."
    )


DEFAULT_PROMPT_PRESETS: List[dict[str, Any]] = [
    {
        "title": "Q版角色眨眼微笑 (2×2)",
        "rows": 2,
        "cols": 2,
        "tags": ["表情包", "二次元", "2x2"],
        "action": "A cute chibi cat-eared character. Panel 1: Standing facing forward with bright open eyes and gentle smile. Panel 2: Eyes half closed in a relaxed blink. Panel 3: Eyes completely closed with a happy arc smile and tiny blush. Panel 4: Eyes opening back up to bright neutral expression.",
    },
    {
        "title": "黄色卫衣少年挥手打招呼 (3×3)",
        "rows": 3,
        "cols": 3,
        "tags": ["问候", "打招呼", "3x3"],
        "action": "A cheerful boy in a bright yellow hoodie waving hand. Panel 1: Neutral standing pose looking forward. Panel 2: Raising right arm slightly. Panel 3: Right hand raised near head level, open palm. Panel 4: Hand waving slightly to the left. Panel 5: Hand waving back to the right. Panel 6: Hand waving left again with a wide joyful smile. Panel 7: Beginning to lower right arm. Panel 8: Arm halfway down. Panel 9: Returned to original relaxed standing pose.",
    },
    {
        "title": "贪吃小仓鼠啃葵花籽 (1×6)",
        "rows": 1,
        "cols": 6,
        "tags": ["萌宠", "动物", "1x6"],
        "action": "A chubby fluffy hamster eating a sunflower seed. Panel 1: Sitting upright holding a sunflower seed with both paws. Panel 2: Bringing the seed up to mouth. Panel 3: Nibbling rapidly with puffed cheeks. Panel 4: Chewing happily with closed eyes. Panel 5: Swallowing the seed with cheeks deflating. Panel 6: Satisfied smile, paws resting on round tummy.",
    },
    {
        "title": "卡通小恐龙侧面循环快走 (4×4)",
        "rows": 4,
        "cols": 4,
        "tags": ["连环画", "步态", "4x4"],
        "action": "A friendly green cartoon dinosaur walking in a side view walk-cycle. 16 continuous sequential frames of smooth walking: left foot forward contact, recoil dip, passing position, high point extension, right foot contact, recoil, passing, high point, repeating seamlessly with tail bobbing gently up and down.",
    },
    {
        "title": "职场打工人抱头崩溃抓狂 (2×3)",
        "rows": 2,
        "cols": 3,
        "tags": ["搞怪", "职场", "2x3"],
        "action": "A comical tired office worker at a desk experiencing funny despair. Panel 1: Staring at laptop screen with flat expression. Panel 2: Eyes suddenly widening in shock. Panel 3: Raising both hands to grab sides of head. Panel 4: Frantically shaking head with comical sweat drops flying. Panel 5: Mouth wide open in exaggerated silent scream. Panel 6: Softly resting forehead flat on the desk in funny defeat.",
    },
]


def get_default_presets() -> List[dict[str, Any]]:
    presets = []
    for item in DEFAULT_PROMPT_PRESETS:
        r, c = int(item["rows"]), int(item["cols"])
        full_prompt = f"{layout_lock_paragraph(r, c)}\n\nAction: {item['action']}"
        presets.append(
            {
                "title": item["title"],
                "prompt": full_prompt,
                "grid": format_grid(r, c),
                "tags": list(item["tags"]),
                "negative": "",
                "notes": "官方推荐经典分镜范例",
            }
        )
    return presets


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
