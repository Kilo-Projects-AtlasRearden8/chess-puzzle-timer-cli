"""Local JSON storage for puzzles and attempts."""

from __future__ import annotations

import json
import os
import time
from typing import Optional

from .models import Puzzle, Attempt
from .scoring import ReviewScheduler


class PuzzleStore:
    """JSON-backed store of puzzles and solving attempts."""

    def __init__(self, path: str) -> None:
        self.path = path
        self._puzzles: dict[str, Puzzle] = {}
        self._attempts: list[Attempt] = []
        self.scheduler = ReviewScheduler()
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        self._puzzles = {}
        self._attempts = []
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as fh:
                    contents = fh.read().strip()
            except OSError:
                contents = ""
            if contents:
                try:
                    data = json.loads(contents)
                except json.JSONDecodeError:
                    data = {}
            else:
                data = {}
            for p in data.get("puzzles", []):
                puzzle = Puzzle.from_dict(p)
                self._puzzles[puzzle.id] = puzzle
            for a in data.get("attempts", []):
                self._attempts.append(Attempt.from_dict(a))
        self._loaded = True

    def _save(self) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.path)) or ".", exist_ok=True)
        data = {
            "puzzles": [p.to_dict() for p in self._puzzles.values()],
            "attempts": [a.to_dict() for a in self._attempts],
        }
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
        os.replace(tmp, self.path)

    # --- puzzles -----------------------------------------------------

    def add_puzzle(self, puzzle: Puzzle) -> Puzzle:
        self._load()
        self._puzzles[puzzle.id] = puzzle
        self._save()
        return puzzle

    def get_puzzle(self, puzzle_id: str) -> Optional[Puzzle]:
        self._load()
        return self._puzzles.get(puzzle_id)

    def list_puzzles(self, due_only: bool = False) -> list[Puzzle]:
        self._load()
        puzzles = sorted(self._puzzles.values(), key=lambda p: p.created_at)
        if due_only:
            now = time.time()
            return [p for p in puzzles if self.scheduler.is_due(p.next_review, now)]
        return puzzles

    def delete_puzzle(self, puzzle_id: str) -> bool:
        self._load()
        if puzzle_id not in self._puzzles:
            return False
        del self._puzzles[puzzle_id]
        self._attempts = [a for a in self._attempts if a.puzzle_id != puzzle_id]
        self._save()
        return True

    # --- attempts ----------------------------------------------------

    def add_attempt(self, attempt: Attempt) -> Attempt:
        self._load()
        puzzle = self._puzzles.get(attempt.puzzle_id)
        interval, next_review = self.scheduler.next_review(
            puzzle.interval if puzzle else 1, attempt.correct
        )
        if puzzle:
            puzzle.interval = interval
            puzzle.next_review = next_review
            self._puzzles[attempt.puzzle_id] = puzzle
        self._attempts.append(attempt)
        self._save()
        return attempt

    def attempts_for_puzzle(self, puzzle_id: str) -> list[Attempt]:
        self._load()
        return [a for a in self._attempts if a.puzzle_id == puzzle_id]

    def recent_attempts(self, limit: int = 50) -> list[Attempt]:
        self._load()
        return sorted(self._attempts, key=lambda a: a.started_at)[-limit:]

    # --- stats -------------------------------------------------------

    def all_attempts(self) -> list[Attempt]:
        self._load()
        return list(self._attempts)

    def clear(self) -> None:
        self._load()
        self._puzzles = {}
        self._attempts = []
        self._save()
