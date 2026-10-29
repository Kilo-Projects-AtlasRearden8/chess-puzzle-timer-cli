"""Scoring logic: accuracy, streaks, and review scheduling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import time


@dataclass
class StreakRecord:
    """Current streak state for a puzzle or overall."""

    current: int = 0
    best: int = 0

    def apply(self, correct: bool) -> "StreakRecord":
        """Return a new record updated with one attempt result."""
        if correct:
            return StreakRecord(current=self.current + 1, best=max(self.best, self.current + 1))
        return StreakRecord(current=0, best=self.best)


@dataclass
class AccuracyStats:
    """Accuracy statistics over a set of attempts."""

    total: int = 0
    correct: int = 0

    @property
    def accuracy(self) -> float:
        if self.total == 0:
            return 0.0
        return self.correct / self.total

    def apply(self, correct: bool) -> "AccuracyStats":
        return AccuracyStats(total=self.total + 1, correct=self.correct + (1 if correct else 0))


def compute_streak(attempts: list, correct_field: str = "correct") -> StreakRecord:
    """Compute current and best streak from a list of attempts (chronological)."""
    record = StreakRecord()
    for attempt in attempts:
        record = record.apply(bool(getattr(attempt, correct_field, attempt.get(correct_field)) if hasattr(attempt, "get") else getattr(attempt, correct_field)))
    return record


def compute_accuracy(attempts: list) -> AccuracyStats:
    """Compute accuracy stats from a list of attempts."""
    stats = AccuracyStats()
    for attempt in attempts:
        correct = attempt.correct if hasattr(attempt, "correct") else attempt.get("correct", False)
        stats = stats.apply(bool(correct))
    return stats


class ReviewScheduler:
    """Simple spaced-repetition scheduler for puzzle reviews.

    Rules:
      - Correct answer: interval doubles (capped at 365 days), next review
        moves forward by the new interval.
      - Wrong answer: interval resets to 1 day, next review is tomorrow.
    """

    MAX_INTERVAL_DAYS = 365

    def __init__(self, now: Optional[float] = None) -> None:
        self._now = now or time.time

    def next_review(self, puzzle_interval: int, correct: bool, now: Optional[float] = None) -> tuple[int, float]:
        """Return (new_interval, next_review_timestamp) for a puzzle.

        Args:
            puzzle_interval: current interval in days.
            correct: whether the latest attempt was correct.
            now: reference timestamp (defaults to now).
        """
        import datetime

        ref = now if now is not None else self._now()
        today_start = datetime.datetime.combine(
            datetime.date.fromtimestamp(ref), datetime.time.min
        ).timestamp()
        day = 86400.0

        if correct:
            new_interval = min(max(puzzle_interval, 1) * 2, self.MAX_INTERVAL_DAYS)
        else:
            new_interval = 1

        next_review = today_start + new_interval * day
        return new_interval, next_review

    def is_due(self, next_review: float, now: Optional[float] = None) -> bool:
        ref = now if now is not None else self._now()
        return ref >= next_review
