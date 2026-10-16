# Kids' LEGO Designer

[![CI](https://github.com/framegrabber/lego/actions/workflows/ci.yml/badge.svg)](https://github.com/framegrabber/lego/actions/workflows/ci.yml)

A kid describes a model; Claude designs it as a short Python program; deterministic checks prove
it can be built from real bricks; the kid follows step-by-step instructions in a browser.

Spec: [SPEC.md](SPEC.md) · Plan: [tasks/](tasks/) · Evals: [evals/prompts.md](evals/prompts.md)

## Setup

```sh
uv sync
uv run lego setup        # LDraw parts library (~150 MB) + headless Chromium, once
```

## Use

In Claude Code in this repository:

> Use the lego-designer skill to design a rocket on a launch pad.

The skill ([.claude/skills/lego-designer/SKILL.md](.claude/skills/lego-designer/SKILL.md))
writes `models/designs/<name>.py` and loops build → check → render until everything passes.

By hand:

```sh
uv run lego build models/examples/two_legs.py        # → out/two_legs.mpd (+ .json for the preview)
uv run lego check out/two_legs.mpd                   # B1–B7, exit 1 on failure; --json for Claude
uv run lego render out/two_legs.mpd -o out/two_legs  # front/side/top/iso PNGs; --step N
uv run lego preview out/two_legs.mpd                 # instructions in the browser
uv run lego live                                     # browser view of the newest build, auto-reloads
```

### Side by side: Claude left, live model right

1. Terminal 1: `uv run lego live` — opens the browser on the live view and keeps running.
2. Terminal 2: `omp` (or `claude`) in this folder; ask for a model with the lego-designer skill.
3. Tile the two windows: hover the green button of the terminal window and pick
   "Left" (macOS 15+: Window ▸ Move & Resize ▸ Left), then choose the browser for the right half.

Every `lego build` Claude runs shows up on the right within a second (the page starts at the
finished model; step back with ◀ or the arrow keys).

## Checks

| | Check |
|---|---|
| B1 | parts and colors exist in the LDraw library |
| B2 | no two parts overlap |
| B3 | every part is joined by studs |
| B4 | after every step the build is one piece (step 1 may lay out bottom plates) |
| B5 | nothing is wedged between earlier parts above and below |
| B6 | at most 6 items per step (a sub-assembly counts as one) |
| B7 | graded stability score; weak points in the finished model fail, while building they warn |

## Development

```sh
uv run pytest -q && uv run ruff check . && uv run basedpyright
```
