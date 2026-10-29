# STATUS

## What was built

A local-first Python CLI for timing chess puzzle solving, called
`chess-puzzle-timer`. It lets you:

- Add puzzles by FEN with an optional source URL, title, and tags
- Time each solve with a stopwatch (Enter to start/stop)
- Record whether each attempt was correct
- Track accuracy and current/best streak
- Schedule reviews with a simple spaced-repetition scheduler
  (correct doubles the interval up to 365 days; wrong resets to 1 day)
- Quiz mode: work through all due puzzles in sequence
- View stats (attempts, correct, accuracy, streak, puzzle count)
- List and remove puzzles

All data is stored in a single local JSON file (`chess_puzzle_data.json`).
No network calls, no accounts, no secrets. Pure Python standard library,
no game assets.

## Project structure

```
chess-puzzle-timer-cli/
├── pyproject.toml         # package metadata + console script entry point
├── LICENSE                # MIT, Copyright (c) 2026 Asdale Dynamics, LLC
├── README.md              # usage guide, credits Asdale Dynamics, LLC
├── STATUS.md              # this file
├── chess_puzzle_timer/
│   ├── __init__.py        # version
│   ├── models.py          # Puzzle, Attempt dataclasses
│   ├── timer.py           # PuzzleTimer stopwatch
│   ├── scoring.py         # accuracy, streaks, ReviewScheduler
│   ├── storage.py         # PuzzleStore (JSON persistence)
│   ├── quiz.py            # QuizSession
│   └── cli.py             # argparse CLI (main entry point)
└── tests/
    └── test_chess_puzzle_timer.py   # 20 tests (timing, scoring, storage, quiz)
```

## How to run it

Install:

```bash
pip install -e .
```

Or run without installing:

```bash
python3 -m chess_puzzle_timer.cli --help
```

Example commands:

```bash
chess-puzzle-timer add "<FEN>" --url "..." --title "..." --tag tactic
chess-puzzle-timer list --due
chess-puzzle-timer solve <puzzle-id>
chess-puzzle-timer quiz
chess-puzzle-timer stats
```

Run tests:

```bash
python3 -m unittest discover -v tests
```

## Verification results

- Package builds and installs cleanly with `pip install -e .`
- `python3 -m chess_puzzle_timer.cli --help` works
- All 20 tests pass: `OK` (timing, scoring/accuracy/streaks, scheduler,
  storage round-trip/persistence/delete, quiz streak tracking)
- Smoke-tested CLI commands end-to-end with piped input: add, list,
  review, solve, quiz, stats all behave correctly
  - solve records attempt, updates streak, accuracy
  - after a correct answer, puzzle is not immediately due again
  - quiz runs through due puzzles, updating stats/streak across the session
- LICENSE copyright line is exactly `Copyright (c) 2026 Asdale Dynamics, LLC`
- README credits Asdale Dynamics, LLC
- No `.github/workflows` directory present
- No API keys, secrets, or personal data in any file

## Known gaps

- `solve` and `quiz` are interactive (require Enter input); fine for a CLI,
  but not scriptable without piping input.
- Streak/accuracy stats are computed across all puzzles globally (consistent
  with `stats`); there is no per-puzzle streak view.
- Review interval is capped at 365 days and uses calendar-day boundaries;
  no finer-grained (e.g., hours/minutes) scheduling.
- No data migration/versioning for the JSON storage file if the schema
  changes in the future.
- No configuration file; storage path is fixed to `chess_puzzle_data.json`
  in the current working directory.
- No packaging to PyPI (intentionally; this is a local fan project, not
  published).
