# Spec: Kids' LEGO Designer

Source of intent: [docs/intent/kids-lego-instructions.md](docs/intent/kids-lego-instructions.md).
Background research: [ai-lego-design-summary.md](ai-lego-design-summary.md).

## Objective

A kid (10+) describes a model in their own words. Claude designs it as a program, deterministic
checkers prove it is buildable, and the kid gets a 3D web preview plus step-by-step building
instructions they can follow with real bricks — without an adult fixing anything.

**Users.** Kids 10+ describe and build; an adult or facilitator runs the tool (home or workshop).

**User stories**

1. As a kid, I describe "a red racing car with a spoiler" and receive instructions I can build to
   the end without getting stuck.
2. As a kid, I see my model in 3D in a browser and can spin it before building.
3. As a kid, I ask for a change ("make the spoiler bigger") and get updated instructions.
4. As a facilitator, I run one command or Claude Code prompt per kid and hand over a link.

**Priority order:** buildability > likeness to description > everything else. Generation time is
not a constraint.

### Definition of "buildable" (hard gate)

A model is delivered only if B1–B6 pass and the B7 stability score is above the fail threshold.
Each check returns machine-readable JSON naming offending part indices and stud coordinates so
Claude can fix them.

| # | Check | Rule |
|---|---|---|
| B1 | Valid parts | Every part number exists in the LDraw library and in the supported vocabulary; every color is a valid LDraw color code. |
| B2 | No collisions | No two parts occupy the same volume (occupancy grid at 1 stud × 1 plate height). |
| B3 | Connected | The stud/anti-stud connection graph of the finished model is a single component. |
| B4 | Step-wise connected | After every step, all placed parts form one connected component. **Only exception: step 1 may leave several loose pieces if every step-1 part lies on the model's bottom layer** (plates laid out on the table, as in real instructions); from step 2 on, everything built so far is one piece. Free-standing models are supported; baseplate anchoring comes with baseplate support. |
| B5 | Step-wise insertable | No part is wedged: a part fails only if parts from earlier steps **touch** it both on top and underneath. A part with a gap above or below can be slid in sideways and pressed on (user decision 2026-10-13; misses the rare fully enclosed cavity). Parts of the same step never block each other: the kid sees the whole step and chooses the order. |
| B6 | Step size | Each step adds at most 6 items (configurable); an attached sub-assembly counts as one item. |
| B7 | Stable (graded) | Stability score per part and per step in [0, 1]; see below. |

B1–B6 are exact pass/fail for the v1 vocabulary. B7 is graded.

### Sub-assemblies (user decision 2026-10-13: before stability)

A sub-assembly is built separately with its own steps and coordinates, then attached in one main
step (one level deep; copies allowed). In LDraw it is a real MPD submodel referenced from the
main model, so the file stays usable in Studio/LDCad. Checks: B1–B3 and B7 run on the flattened
model; B4–B6 run on each sub-assembly's own steps; in the main model the attachment is one rigid
item that must join what is built (B4) and not be wedged (B5). The preview shows a sub-assembly's
steps on their own ("Build 2× the leg") right before the main step that attaches it.

### Stability score (B7)

Every part gets a score in [0, 1] (1 = no risk). The model score is the minimum over all parts and
all intermediate steps (a half-built model must not fall apart in a kid's hands either).

- **Heuristic v1:** for each part, find the weakest set of stud connections holding it (and
  everything it carries) to the ground, i.e. the minimum stud cut in the connection graph. Compare
  the clutch of that cut against the load it carries and its lever arm (overhang distance).
  Free-standing models also get a tipping term: centre of mass must lie inside the support
  footprint on the table.
- **v2 (later):** StableLego-style force analysis, plugged in behind the same score interface.

Two configurable thresholds turn the score into a verdict:

| Score | Verdict | Effect |
|---|---|---|
| ≥ `warn` (default 0.6) | ok | delivered |
| `fail` ≤ score < `warn` | fragile | delivered; Claude should try to improve it; flagged parts are highlighted in the preview as "hold carefully" |
| < `fail` (default 0.3) | unstable | not delivered; Claude must fix |

Default thresholds are placeholders, to be calibrated against physical builds.

### Likeness (soft gate)

Claude inspects renders (front / side / top / iso) against the description and either accepts or
revises. Not machine-checked; evaluated by humans on the eval set.

## Capability map

| Module id | Responsibility | Depends on |
|---|---|---|
| `parts` | Supported part vocabulary: LDraw id, footprint in studs, height in plates, stud/anti-stud positions; LDraw color table. | LDraw library |
| `dsl` | Python API in stud coordinates (`brick`, `plate`, `step`, `subassembly`, `attach`) that Claude writes; produces an in-memory model with flattened placements. | `parts` |
| `ldraw` | Serialize model → `.ldr` / `.mpd` with `0 STEP` and submodels; parse back for round-trips. | `dsl` |
| `check` | B1–B7 checks over the in-memory model; JSON report. | `parts`, `dsl` |
| `render` | Headless PNG renders of a model or a single step, produced by loading `preview` in headless Chromium (one renderer for Claude and kids). | `preview` |
| `preview` | Static web page (three.js `LDrawLoader`) showing the model with a step player; sub-assembly steps are shown on their own before the step that attaches them. | `ldraw` |
| `skill` | Claude Code skill: prompt → DSL program → build → check → render → fix loop → deliver. | all above |

Build order: `parts` → `dsl` → `ldraw` → `check` (B1–B3) → `preview` → `render` → `skill` (first
loop) → `check` (B4–B7).

### v1 part vocabulary

Axis-aligned parts, rotations in 90° steps:

- Bricks: 1×1 (3005), 1×2 (3004), 1×4 (3010), 2×2 (3003), 2×4 (3001)
- Plates: 1×1 (3024), 1×2 (3023), 1×4 (3710), 2×2 (3022), 2×4 (3020)
- Slopes 45°: 2×1 (3040), 2×2 (3039), 2×4 (3037); inverted 2×1 (3665), 2×2 (3660)
- Baseplate (optional): 32×32 (3811)

Every part declares its connection geometry as data in `parts`: footprint, height, stud positions
(slopes: back row only), anti-stud positions (inverted slopes: back row only), and occupancy.
Slopes use their full bounding box for collision — conservative, so it may reject a rare valid
placement in the empty space above a slope face but never accepts an invalid one. The DSL takes a
`facing` argument for slopes so Claude does not reason about rotation matrices.

Slopes are added after bricks and plates pass their checker tests (same plan, later task).

Extension (after v1 passes the eval set): tiles, round bricks, wheels, SNOT.

## Tech Stack

- Python 3.14, managed with `uv` (0.9.x); package `lego` in `src/lego/`
- Dev tooling: `basedpyright` (types), `ruff` (lint/format), `pytest`, `debugpy`
- LDraw parts library (`complete.zip`, ~80 MB) downloaded to `ldraw/` (gitignored)
- Renderer and preview: one static HTML page using three.js `LDrawLoader`. Kids open it in a
  browser; `lego render` screenshots it with headless Chromium via Playwright for Python
  (new runtime dependency, pending approval).

## Commands

Existing:

```sh
uv sync                     # install deps
uv run pytest               # tests
uv run ruff check .         # lint
uv run ruff format .        # format
uv run basedpyright         # type check
```

Planned CLI (names fixed here, implemented per plan):

```sh
uv run lego build models/car.py -o out/car.mpd    # DSL program → LDraw
uv run lego check out/car.mpd --json              # B1–B7 report, exit 1 on failure
uv run lego render out/car.mpd -o out/car/        # front/side/top/iso PNGs
uv run lego render out/car.mpd --step 5 -o out/   # single step
uv run lego preview out/car.mpd                   # serve web preview, print URL
uv run lego setup                                 # download LDraw library, install headless Chromium
```

## Project Structure

```
src/lego/           → package
  parts.py          → vocabulary + colors
  dsl.py            → model-building API
  ldraw.py          → .ldr/.mpd writer/reader
  check/            → one module per check family (collision, connectivity, steps, stability)
  render.py         → headless-Chromium screenshots of the preview
  cli.py            → `lego` command
web/                → static preview page
models/             → example DSL programs (incl. deliberately broken ones for tests)
evals/prompts.md    → fixed eval prompts
tests/              → pytest
.claude/skills/lego-designer/ → the Claude Code skill
docs/intent/        → confirmed intents
ldraw/, out/        → gitignored: parts library, generated output
```

## Code Style

The DSL is what Claude writes, so it must be short and unambiguous. Coordinates are integers in
studs (x, z) and plates (y, upward); `x, z` is the footprint's min corner and `y` its bottom level.
An unrotated `AxB` part covers B studs along x and A along z (LDraw orientation); `rot=90/270`
swaps them. The compiler converts to LDraw units (20 LDU per stud, 8 LDU per plate, −Y up).

```python
from lego.dsl import Model

m = Model("racing car")

with m.step():
    m.plate("2x4", x=0, z=0, y=0, color="black")
    m.plate("2x4", x=0, z=2, y=0, color="black")   # unrotated 2x4: 4 studs in x, 2 in z

with m.step():
    m.brick("2x4", x=0, z=1, y=1, color="red")     # covers z 1..3: bridges both plates

m.save("out/car.mpd")
```

Conventions: ruff defaults with line length 100; full type hints, basedpyright `standard` clean;
dataclasses for model data; checks are pure functions `model → Report`.

## Testing Strategy

- `pytest`, tests in `tests/`, deterministic, no network (LDraw library required for B1 tests;
  skip with a clear message if absent).
- **Checker tests are the core**: each check gets a passing model and a minimal failing model
  (floating brick, overlapping bricks, step that attaches to a future part, step blocked from
  above, single-1×1-stud cantilever). These encode the buildability contract.
- Round-trip tests: DSL → `.mpd` → parse → same parts/positions/steps.
- Render and preview are verified by running them (smoke), not by image-diff tests.
- **Eval set**: ~10 fixed prompts in `evals/prompts.md`; per run record pass/fail of B1–B6, the
  B7 score, part count, and a human likeness score (1–3).

## Boundaries

- **Always:** run `pytest`, `ruff check`, `basedpyright` before committing; keep checks
  deterministic; every check failure names parts and coordinates; never deliver a model that
  fails B1–B6 or scores below the B7 fail threshold.
- **Ask first:** adding runtime dependencies (e.g. pyldraw3, StableLego, Gurobi); expanding the
  part vocabulary; changing the B1–B7 definitions; anything that installs system software.
- **Never:** commit the LDraw library or generated output; weaken a check to make a model pass;
  require a commercial license (e.g. Gurobi) for the default path.

## Success Criteria

1. `lego check` correctly classifies every model in the test suite (all good models pass, every
   deliberately broken model fails with the right check and part index).
2. On the eval set, the skill delivers a model that passes B1–B6 with B7 ≥ `fail` for ≥ 8 of 10
   prompts, within any number of fix iterations; failures are reported, never silently delivered.
3. Delivered models are 50–400 parts.
4. The web preview shows the model and steps through it with a slider; it is the instruction
   format (no PDF).
5. **Physical test:** at least 3 delivered models are built from real bricks by someone following
   only the instructions, without getting stuck.

## Open Questions

1. **B7 thresholds:** defaults 0.3 / 0.6 are guesses; calibrate after the first physical builds.
2. **Playwright:** approve as runtime dependency (~150 MB Chromium download) for headless
   rendering.
