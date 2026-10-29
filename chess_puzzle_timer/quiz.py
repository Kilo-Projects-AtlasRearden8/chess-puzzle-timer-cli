"""Quiz mode: present puzzles, time the solve, record the attempt."""

from __future__ import annotations

import uuid
from typing import Optional

from .models import Puzzle, Attempt
from .timer import PuzzleTimer
from .storage import PuzzleStore


class QuizSession:
    """A quiz session: walk through puzzles, time each, record results."""

    def __init__(self, store: PuzzleStore) -> None:
        self.store = store
        self.timer = PuzzleTimer()
        self._active_puzzle: Optional[Puzzle] = None

    def start_puzzle(self, puzzle: Puzzle) -> Puzzle:
        """Begin timing a puzzle. Returns the puzzle."""
        if self.timer.running:
            self.timer.stop()
        self._active_puzzle = puzzle
        self.timer.start()
        return puzzle

    def finish_puzzle(self, correct: bool) -> Attempt:
        """Stop timing, record the attempt, and return it.

        Requires start_puzzle to have been called first.
        """
        if self._active_puzzle is None:
            raise RuntimeError("No puzzle is currently being solved")
        if not self.timer.running:
            raise RuntimeError("Timer is not running")

        puzzle = self._active_puzzle
        streak_before = self._current_streak(self.store.all_attempts())

        duration = self.timer.stop()
        streak_after = streak_before + 1 if correct else 0

        attempt = Attempt(
            id=uuid.uuid4().hex,
            puzzle_id=puzzle.id,
            started_at=self.timer.result().started_at,
            finished_at=self.timer.result().finished_at or self.timer.result().started_at,
            duration_seconds=duration,
            correct=correct,
            streak_before=streak_before,
            streak_after=streak_after,
        )
        self.store.add_attempt(attempt)
        self._active_puzzle = None
        return attempt

    def cancel(self) -> None:
        """Cancel the in-progress puzzle without recording an attempt."""
        if self.timer.running:
            self.timer.stop()
        self._active_puzzle = None

    @property
    def elapsed(self) -> float:
        return self.timer.elapsed

    @staticmethod
    def _current_streak(attempts: list[Attempt]) -> int:
        streak = 0
        for attempt in reversed(sorted(attempts, key=lambda a: a.started_at)):
            if attempt.correct:
                streak += 1
            else:
                break
        return streak
