# Chess Puzzle Timer CLI

A small, friendly command-line tool to time your chess puzzle solving,
track your accuracy and streaks, log where each puzzle came from (FEN or
URL), and schedule reviews so you don't forget what you've learned.

Everything stays on your computer in a single JSON file. No accounts, no
network calls, no subscriptions, no secrets.

This is a fan project from **Asdale Dynamics, LLC**, made in the same
beginner-friendly spirit as Dylan Asdale's books and the hub site
dylanasdale.github.io: plain English, step by step, never condescending.
Dylan is a registered nurse turned AI author and founder of Asdale
Dynamics, LLC (Indiana, formed October 2026).

## What it does

- **Time your solves** — press Enter to start and stop a stopwatch for each
  puzzle; the elapsed time is saved with your answer.
- **Track accuracy and streaks** — see how many puzzles you've gotten right,
  your overall accuracy percentage, and your current and best solving streak.
- **Log puzzle sources** — store each puzzle's FEN position plus an optional
  source URL and title, so you can always find it again.
- **Review scheduler** — get a puzzle right and it comes back for review
  later (the interval doubles, up to a year). Get it wrong and it comes back
  sooner. Use this to keep your skills sharp without cramming.
- **Quiz mode** — work through every puzzle that's due for review, one timed
  solve at a time.

## Install

```bash
git clone <this-repo>
cd chess-puzzle-timer-cli
pip install -e .
```

No internet access is needed after installation. If `pip install` is blocked
by your system, you can run the tool directly:

```bash
python3 -m chess_puzzle_timer.cli --help
```

## Usage

Add a puzzle by its FEN position (you can get a FEN from any chess site or
app):

```bash
chess-puzzle-timer add "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1" \
  --url "https://example.com/puzzle" --title "Spanish opening trap" --tag tactic
```

See your puzzles (new ones are due for review right away):

```bash
chess-puzzle-timer list
chess-puzzle-timer list --due
```

Time one puzzle:

```bash
chess-puzzle-timer solve <puzzle-id>
```

You'll press Enter to start the timer and Enter again when you've solved it,
then answer whether you got it right.

Quiz through everything due for review:

```bash
chess-puzzle-timer quiz
```

Check your stats:

```bash
chess-puzzle-timer stats
```

Remove a puzzle:

```bash
chess-puzzle-timer remove <puzzle-id>
```

## Commands at a glance

| Command | What it does |
|---------|--------------|
| `add <FEN>` | Store a new puzzle (`--url`, `--title`, `--tag` optional) |
| `list [--due]` | List puzzles; `--due` shows only those ready for review |
| `review` | Show puzzles due for review |
| `solve <id>` | Time one stored puzzle and record the result |
| `quiz` | Work through all due puzzles, one timed solve at a time |
| `stats` | Show attempts, accuracy, and current/best streak |
| `remove <id>` | Delete a puzzle and its attempts |

## How scoring works

- **Accuracy:** correct solves ÷ total attempts.
- **Streak:** how many correct solves in a row. An incorrect answer resets it
  to zero; your best streak is remembered.
- **Review interval:** after a correct answer, the wait until next review
  doubles (capped at 365 days). After a wrong answer, it resets to one day.

## Data

All your puzzles and attempts live in `chess_puzzle_data.json` in the folder
where you run the program. It's plain JSON, so you can back it up, move it,
or open it in a text editor anytime. No cloud, no lock-in.

## Testing

```bash
python3 -m unittest discover -v tests
```

There are no game assets and no external dependencies beyond the Python
standard library.

## License

MIT. Copyright (c) 2026 Asdale Dynamics, LLC.

Credit: This fan project is created by Asdale Dynamics, LLC (Dylan Asdale,
Indiana). It is not affiliated with any chess organization, publisher, or
platform.
