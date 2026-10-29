"""Stopwatch-style timing for puzzle solving attempts."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class TimingResult:
    """Result of a timed solving session."""

    started_at: float
    finished_at: Optional[float]
    duration_seconds: Optional[float]
    completed: bool


class PuzzleTimer:
    """A simple stopwatch for timing how long a puzzle takes to solve."""

    def __init__(self) -> None:
        self._started_at: Optional[float] = None
        self._finished_at: Optional[float] = None

    @property
    def running(self) -> bool:
        return self._started_at is not None and self._finished_at is None

    @property
    def elapsed(self) -> float:
        if self._started_at is None:
            return 0.0
        end = self._finished_at if self._finished_at is not None else time.time()
        return max(0.0, end - self._started_at)

    def start(self) -> float:
        """Start the timer. Returns the start timestamp."""
        if self.running:
            raise RuntimeError("Timer is already running")
        self._started_at = time.time()
        self._finished_at = None
        return self._started_at

    def stop(self) -> float:
        """Stop the timer. Returns the elapsed duration in seconds."""
        if not self.running:
            raise RuntimeError("Timer is not running")
        self._finished_at = time.time()
        return self.elapsed

    def result(self) -> TimingResult:
        return TimingResult(
            started_at=self._started_at or 0.0,
            finished_at=self._finished_at,
            duration_seconds=self.elapsed if self._finished_at is not None else None,
            completed=self._finished_at is not None,
        )

    def reset(self) -> None:
        self._started_at = None
        self._finished_at = None
