"""Data models for the chess puzzle timer."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional
import uuid
import time


def _now() -> float:
    return time.time()


def _new_id() -> str:
    return uuid.uuid4().hex


@dataclass
class Puzzle:
    """A single chess puzzle with a FEN position and optional source URL."""

    id: str
    fen: str
    source_url: Optional[str] = None
    title: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=_now)
    next_review: float = field(default_factory=_now)
    interval: int = 1  # days until next review

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Puzzle":
        return Puzzle(
            id=d["id"],
            fen=d["fen"],
            source_url=d.get("source_url"),
            title=d.get("title", ""),
            tags=d.get("tags", []),
            created_at=d.get("created_at", _now()),
            next_review=d.get("next_review", _now()),
            interval=d.get("interval", 1),
        )

    @classmethod
    def create(cls, fen: str, source_url: Optional[str] = None,
               title: str = "", tags: list[str] | None = None) -> "Puzzle":
        return cls(
            id=_new_id(),
            fen=fen,
            source_url=source_url,
            title=title,
            tags=tags or [],
        )


@dataclass
class Attempt:
    """One timed attempt at solving a puzzle."""

    id: str
    puzzle_id: str
    started_at: float
    finished_at: float
    duration_seconds: float
    correct: bool
    streak_before: int
    streak_after: int

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Attempt":
        return Attempt(
            id=d["id"],
            puzzle_id=d["puzzle_id"],
            started_at=d["started_at"],
            finished_at=d["finished_at"],
            duration_seconds=d["duration_seconds"],
            correct=d["correct"],
            streak_before=d["streak_before"],
            streak_after=d["streak_after"],
        )
