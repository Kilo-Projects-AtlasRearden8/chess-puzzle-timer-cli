"""Command-line interface for the chess puzzle timer."""

from __future__ import annotations

import argparse
import sys
import time
import uuid
from typing import Optional, Sequence

from .models import Puzzle, Attempt
from .storage import PuzzleStore
from .timer import PuzzleTimer
from .quiz import QuizSession
from .scoring import compute_accuracy, compute_streak


DEFAULT_STORAGE = "chess_puzzle_data.json"


def _store() -> PuzzleStore:
    return PuzzleStore(DEFAULT_STORAGE)


def cmd_add(args: argparse.Namespace) -> int:
    store = _store()
    puzzle = Puzzle.create(
        fen=args.fen,
        source_url=args.url or None,
        title=args.title or "",
        tags=args.tag or [],
    )
    store.add_puzzle(puzzle)
    print(f"Added puzzle {puzzle.id[:8]}")
    print(f"  FEN:    {puzzle.fen}")
    if puzzle.source_url:
        print(f"  Source: {puzzle.source_url}")
    if puzzle.title:
        print(f"  Title:  {puzzle.title}")
    if puzzle.tags:
        print(f"  Tags:   {', '.join(puzzle.tags)}")
    return 0


def _format_puzzle(puzzle: Puzzle, show_next: bool = False) -> str:
    due = ""
    if show_next:
        marker = "DUE" if time.time() >= puzzle.next_review else "ok"
        due = f" [{marker}]"
    line = f"{puzzle.id[:8]}  {puzzle.fen}{due}"
    if puzzle.title:
        line += f"  - {puzzle.title}"
    if puzzle.source_url:
        line += f"  (source: {puzzle.source_url})"
    return line


def cmd_list(args: argparse.Namespace) -> int:
    store = _store()
    puzzles = store.list_puzzles(due_only=args.due)
    if not puzzles:
        print("No puzzles stored.")
        return 0
    for p in puzzles:
        print(_format_puzzle(p, show_next=True))
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    store = _store()
    due = store.list_puzzles(due_only=True)
    if not due:
        print("No puzzles due for review.")
        return 0
    print(f"{len(due)} puzzle(s) due for review:")
    for p in due:
        print(_format_puzzle(p, show_next=True))
    return 0


def _prompt_bool(prompt: str) -> bool:
    while True:
        answer = input(f"{prompt} [y/n]: ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no", ""):
            return False
        print("Please answer y or n.")


def _record_attempt(store: PuzzleStore, puzzle: Puzzle, duration: float, correct: bool) -> Attempt:
    attempts = store.all_attempts()
    streak = compute_streak(attempts)
    streak_before = streak.current
    streak_after = streak_before + 1 if correct else 0
    attempt = Attempt(
        id=uuid.uuid4().hex,
        puzzle_id=puzzle.id,
        started_at=time.time() - duration,
        finished_at=time.time(),
        duration_seconds=duration,
        correct=correct,
        streak_before=streak_before,
        streak_after=streak_after,
    )
    store.add_attempt(attempt)
    return attempt


def cmd_solve(args: argparse.Namespace) -> int:
    store = _store()
    puzzle = store.get_puzzle(args.id)
    if puzzle is None:
        print(f"Puzzle {args.id} not found.")
        return 1

    print(f"Puzzle {puzzle.id[:8]}")
    print(f"FEN: {puzzle.fen}")
    if puzzle.source_url:
        print(f"Source: {puzzle.source_url}")
    print("Press Enter to start the timer, then Enter again when you solve it.")
    input("> ")
    timer = PuzzleTimer()
    timer.start()
    print("Timer running... press Enter to stop.")
    input("> ")
    duration = timer.stop()
    print(f"Time: {duration:.2f} seconds")
    correct = _prompt_bool("Did you solve it correctly?")
    attempt = _record_attempt(store, puzzle, duration, correct)
    print(f"Streak: {attempt.streak_before} -> {attempt.streak_after}")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    store = _store()
    attempts = store.all_attempts()
    stats = compute_accuracy(attempts)
    streak = compute_streak(attempts)
    print(f"Attempts:  {stats.total}")
    print(f"Correct:   {stats.correct}")
    print(f"Accuracy:  {stats.accuracy * 100:.1f}%")
    print(f"Streak:    {streak.current} (best {streak.best})")
    puzzles = store.list_puzzles()
    print(f"Puzzles:   {len(puzzles)}")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    store = _store()
    if store.delete_puzzle(args.id):
        print(f"Puzzle {args.id} removed.")
        return 0
    print(f"Puzzle {args.id} not found.")
    return 1


def cmd_quiz(args: argparse.Namespace) -> int:
    store = _store()
    due = store.list_puzzles(due_only=True)
    if not due:
        print("No puzzles due for review. Add puzzles with `add`; new puzzles are due immediately.")
        return 0
    session = QuizSession(store)
    for puzzle in list(due):
        print("\n" + "=" * 40)
        print(f"Puzzle {puzzle.id[:8]}")
        print(f"FEN: {puzzle.fen}")
        if puzzle.source_url:
            print(f"Source: {puzzle.source_url}")
        input("Press Enter to start the timer...")
        session.start_puzzle(puzzle)
        print("Timer running... press Enter when done.")
        input("> ")
        correct = _prompt_bool("Correct?")
        attempt = session.finish_puzzle(correct)
        print(f"Time: {attempt.duration_seconds:.2f}s  Streak: {attempt.streak_before} -> {attempt.streak_after}")
    print("\nQuiz complete.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chess-puzzle-timer",
        description="Time chess puzzle solving, track accuracy and streaks, log puzzle sources.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add a puzzle (FEN + optional source URL)")
    p_add.add_argument("fen", help="FEN position of the puzzle")
    p_add.add_argument("--url", help="Source URL of the puzzle")
    p_add.add_argument("--title", help="Optional title")
    p_add.add_argument("--tag", action="append", default=[], help="Tag (repeatable)")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="List stored puzzles")
    p_list.add_argument("--due", action="store_true", help="Show only puzzles due for review")
    p_list.set_defaults(func=cmd_list)

    sub.add_parser("review", help="Show puzzles due for review").set_defaults(func=cmd_review)

    p_solve = sub.add_parser("solve", help="Time one stored puzzle")
    p_solve.add_argument("id", help="Puzzle ID (prefix OK)")
    p_solve.set_defaults(func=cmd_solve)

    sub.add_parser("quiz", help="Quiz mode: work through due puzzles").set_defaults(func=cmd_quiz)

    sub.add_parser("stats", help="Show accuracy and streak stats").set_defaults(func=cmd_stats)

    p_rm = sub.add_parser("remove", help="Remove a puzzle")
    p_rm.add_argument("id", help="Puzzle ID (prefix OK)")
    p_rm.set_defaults(func=cmd_remove)

    return parser


def resolve_id(store: PuzzleStore, prefix: str) -> Optional[str]:
    """Resolve a short ID prefix to a full puzzle ID."""
    for puzzle in store.list_puzzles():
        if puzzle.id.startswith(prefix):
            return puzzle.id
    return None


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in ("solve", "remove"):
        store = _store()
        full = resolve_id(store, args.id)
        if full is None:
            print(f"Puzzle {args.id} not found.")
            return 1
        args.id = full

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
