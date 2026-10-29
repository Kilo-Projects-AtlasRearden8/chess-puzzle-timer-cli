"""Tests for the chess puzzle timer package."""

from __future__ import annotations

import os
import tempfile
import time
import unittest

from chess_puzzle_timer.models import Puzzle, Attempt
from chess_puzzle_timer.timer import PuzzleTimer
from chess_puzzle_timer.scoring import (
    compute_accuracy,
    compute_streak,
    ReviewScheduler,
    StreakRecord,
    AccuracyStats,
)
from chess_puzzle_timer.storage import PuzzleStore
from chess_puzzle_timer.quiz import QuizSession


class TestTimer(unittest.TestCase):
    def test_initial_state(self):
        t = PuzzleTimer()
        self.assertFalse(t.running)
        self.assertEqual(t.elapsed, 0.0)
        self.assertFalse(t.result().completed)

    def test_start_stop(self):
        t = PuzzleTimer()
        t.start()
        self.assertTrue(t.running)
        time.sleep(0.05)
        duration = t.stop()
        self.assertFalse(t.running)
        self.assertGreaterEqual(duration, 0.04)
        res = t.result()
        self.assertTrue(res.completed)
        self.assertIsNotNone(res.duration_seconds)
        self.assertGreaterEqual(res.duration_seconds, 0.04)

    def test_stop_without_start_raises(self):
        t = PuzzleTimer()
        with self.assertRaises(RuntimeError):
            t.stop()

    def test_double_start_raises(self):
        t = PuzzleTimer()
        t.start()
        with self.assertRaises(RuntimeError):
            t.start()

    def test_reset(self):
        t = PuzzleTimer()
        t.start()
        time.sleep(0.02)
        t.reset()
        self.assertFalse(t.running)
        self.assertEqual(t.elapsed, 0.0)
        # Can start again after reset.
        t.start()
        self.assertTrue(t.running)
        t.stop()


class TestScoring(unittest.TestCase):
    def test_streak_record(self):
        r = StreakRecord()
        r = r.apply(True)
        self.assertEqual((r.current, r.best), (1, 1))
        r = r.apply(True)
        self.assertEqual((r.current, r.best), (2, 2))
        r = r.apply(False)
        self.assertEqual((r.current, r.best), (0, 2))
        r = r.apply(True)
        self.assertEqual((r.current, r.best), (1, 2))

    def test_accuracy_stats(self):
        s = AccuracyStats()
        self.assertEqual(s.accuracy, 0.0)
        s = s.apply(True).apply(False).apply(True)
        self.assertEqual((s.total, s.correct), (3, 2))
        self.assertAlmostEqual(s.accuracy, 2 / 3)

    def test_compute_accuracy_empty(self):
        self.assertEqual(compute_accuracy([]).accuracy, 0.0)

    def test_compute_accuracy_attempts(self):
        attempts = [
            Attempt("a1", "p1", 0.0, 1.0, 1.0, True, 0, 1),
            Attempt("a2", "p1", 1.0, 2.0, 1.0, False, 1, 0),
            Attempt("a3", "p1", 2.0, 3.0, 1.0, True, 0, 1),
        ]
        stats = compute_accuracy(attempts)
        self.assertEqual((stats.total, stats.correct), (3, 2))
        self.assertAlmostEqual(stats.accuracy, 2 / 3)

    def test_compute_streak(self):
        attempts = [
            Attempt("a1", "p1", 0.0, 1.0, 1.0, True, 0, 1),
            Attempt("a2", "p1", 1.0, 2.0, 1.0, True, 1, 2),
            Attempt("a3", "p1", 2.0, 3.0, 1.0, False, 2, 0),
            Attempt("a4", "p1", 3.0, 4.0, 1.0, True, 0, 1),
        ]
        streak = compute_streak(attempts)
        self.assertEqual((streak.current, streak.best), (1, 2))

    def test_compute_streak_all_wrong(self):
        attempts = [
            Attempt("a1", "p1", 0.0, 1.0, 1.0, False, 0, 0),
            Attempt("a2", "p1", 1.0, 2.0, 1.0, False, 0, 0),
        ]
        self.assertEqual((compute_streak(attempts).current, compute_streak(attempts).best), (0, 0))

    def test_scheduler_correct_doubles_interval(self):
        sched = ReviewScheduler(now=1_000_000.0)
        interval, nxt = sched.next_review(1, True, now=1_000_000.0)
        self.assertEqual(interval, 2)
        # next review is two days after today-start anchor; just check it's ahead.
        self.assertGreater(nxt, 1_000_000.0)
        self.assertTrue(sched.is_due(nxt, now=1_000_000.0 + 172800))

    def test_scheduler_wrong_resets(self):
        sched = ReviewScheduler(now=1_000_000.0)
        interval, nxt = sched.next_review(30, False, now=1_000_000.0)
        self.assertEqual(interval, 1)

    def test_scheduler_cap(self):
        sched = ReviewScheduler(now=1_000_000.0)
        interval, _ = sched.next_review(365, True, now=1_000_000.0)
        self.assertEqual(interval, ReviewScheduler.MAX_INTERVAL_DAYS)


class TestStorage(unittest.TestCase):
    def _tmp_path(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        return path

    def test_add_and_list_puzzle(self):
        path = self._tmp_path()
        try:
            store = PuzzleStore(path)
            puzzle = Puzzle.create("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                                   source_url="https://example.com/puzzle",
                                   title="Opening trap",
                                   tags=["tactic"])
            store.add_puzzle(puzzle)

            all_puzzles = store.list_puzzles()
            self.assertEqual(len(all_puzzles), 1)
            got = store.get_puzzle(puzzle.id)
            self.assertIsNotNone(got)
            self.assertEqual(got.fen, puzzle.fen)
            self.assertEqual(got.source_url, "https://example.com/puzzle")
            self.assertEqual(got.tags, ["tactic"])
            # New puzzle is due immediately.
            self.assertTrue(store.list_puzzles(due_only=True))
        finally:
            os.unlink(path)

    def test_persistence_round_trip(self):
        path = self._tmp_path()
        try:
            store = PuzzleStore(path)
            puzzle = Puzzle.create("8/8/8/8/8/8/8/8 w - - 0 1")
            store.add_puzzle(puzzle)

            store2 = PuzzleStore(path)
            puzzles = store2.list_puzzles()
            self.assertEqual(len(puzzles), 1)
            self.assertEqual(puzzles[0].id, puzzle.id)
        finally:
            os.unlink(path)

    def test_attempt_schedules_review(self):
        path = self._tmp_path()
        try:
            store = PuzzleStore(path)
            puzzle = Puzzle.create("8/8/8/8/8/8/8/8 w - - 0 1")
            store.add_puzzle(puzzle)

            before = store.get_puzzle(puzzle.id)
            attempt = Attempt(
                "x1", puzzle.id, 100.0, 120.0, 20.0, True, 0, 1,
            )
            store.add_attempt(attempt)

            after = store.get_puzzle(puzzle.id)
            self.assertEqual(after.interval, 2)
            attempts = store.attempts_for_puzzle(puzzle.id)
            self.assertEqual(len(attempts), 1)
            self.assertTrue(attempts[0].correct)

            # Wrong answer resets interval to 1.
            attempt2 = Attempt("x2", puzzle.id, 130.0, 140.0, 10.0, False, 1, 0)
            store.add_attempt(attempt2)
            again = store.get_puzzle(puzzle.id)
            self.assertEqual(again.interval, 1)
        finally:
            os.unlink(path)

    def test_delete_puzzle(self):
        path = self._tmp_path()
        try:
            store = PuzzleStore(path)
            puzzle = Puzzle.create("8/8/8/8/8/8/8/8 w - - 0 1")
            store.add_puzzle(puzzle)
            attempt = Attempt("a1", puzzle.id, 0.0, 1.0, 1.0, True, 0, 1)
            store.add_attempt(attempt)

            self.assertTrue(store.delete_puzzle(puzzle.id))
            self.assertIsNone(store.get_puzzle(puzzle.id))
            self.assertEqual(store.attempts_for_puzzle(puzzle.id), [])
            self.assertFalse(store.delete_puzzle(puzzle.id))
        finally:
            os.unlink(path)


class TestQuiz(unittest.TestCase):
    def test_quiz_streak_tracking(self):
        path = tempfile.mktemp(suffix=".json")
        try:
            store = PuzzleStore(path)
            puzzle = Puzzle.create("8/8/8/8/8/8/8/8 w - - 0 1")
            store.add_puzzle(puzzle)

            session = QuizSession(store)
            session.start_puzzle(puzzle)
            time.sleep(0.02)
            attempt = session.finish_puzzle(True)
            self.assertTrue(attempt.correct)
            self.assertEqual(attempt.streak_before, 0)
            self.assertEqual(attempt.streak_after, 1)
            self.assertGreaterEqual(attempt.duration_seconds, 0.02)
            self.assertIsNone(session._active_puzzle)

            # Second attempt breaks the streak when incorrect.
            puzzle2 = Puzzle.create("8/8/8/8/4K3/8/8/4k3 w - - 0 1")
            store.add_puzzle(puzzle2)
            session.start_puzzle(puzzle2)
            attempt2 = session.finish_puzzle(False)
            self.assertFalse(attempt2.correct)
            self.assertEqual(attempt2.streak_before, 1)
            self.assertEqual(attempt2.streak_after, 0)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_cancel(self):
        session = QuizSession(PuzzleStore(tempfile.mktemp(suffix=".json")))
        session.timer.start()
        session.cancel()
        self.assertFalse(session.timer.running)
        self.assertIsNone(session._active_puzzle)


if __name__ == "__main__":
    unittest.main()
